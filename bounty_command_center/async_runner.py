import asyncio
import os
import signal
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List

import psutil

from .logging_setup import get_logger
from .monitoring_config import monitoring_config


@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    return_code: int | None
    timed_out: bool = False
    aborted: bool = False
    peak_cpu: float = 0.0
    peak_mem: float = 0.0
    avg_cpu: float = 0.0
    avg_mem: float = 0.0
    time_to_abort: float | None = None
    samples_collected: int = 0
    abort_reason: str | None = None


class AsyncToolRunner:
    """
    A class to run multiple shell commands asynchronously with timeouts and advanced resource monitoring.
    """

    def __init__(self):
        self.log = get_logger(self.__class__.__name__)
        self.monitor_log = get_logger("resource_monitor")

    async def _terminate_process_group(self, pid: int, run_id: str) -> None:
        """
        Safely terminates a process group with a grace period.
        Sends SIGTERM, waits, then sends SIGKILL if the process is still alive.
        """
        if monitoring_config.abort_dry_run:
            self.monitor_log.warning("DRY RUN: Would terminate process group", pid=pid, run_id=run_id)
            return

        try:
            pgid = os.getpgid(pid)
            self.monitor_log.warning("Sending SIGTERM to process group", pgid=pgid, run_id=run_id)
            os.killpg(pgid, signal.SIGTERM)

            await asyncio.sleep(monitoring_config.kill_grace_seconds)

            # Check if the process is still alive
            p = psutil.Process(pid)
            if p.is_running():
                self.monitor_log.warning("Process group did not exit gracefully, sending SIGKILL", pgid=pgid, run_id=run_id)
                os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            # Process already finished, which is fine
            self.monitor_log.info("Process group already exited", pgid=getattr(self, 'pgid', 'N/A'), run_id=run_id)
        except Exception as e:
            self.log.error("Error during process termination", error=str(e), pgid=getattr(self, 'pgid', 'N/A'), run_id=run_id)

    async def _monitor_resources(self, proc: asyncio.subprocess.Process, command_str: str) -> Dict[str, Any]:
        """
        Monitors process resources, applying EMA smoothing and breach window logic before aborting.
        """
        run_id = f"{proc.pid}-{time.time_ns()}"
        metrics = {
            "peak_cpu": 0.0, "peak_mem": 0.0, "avg_cpu": 0.0, "avg_mem": 0.0,
            "time_to_abort": None, "samples_collected": 0, "aborted": False, "abort_reason": None,
        }

        if not monitoring_config.abort_enable:
            return metrics

        try:
            p = psutil.Process(proc.pid)
            p.cpu_percent(interval=None)  # Initialize
            total_ram = psutil.virtual_memory().total

            ema_cpu = None
            ema_mem = None
            over_limit_start_time = None
            all_cpu_samples: List[float] = []
            all_mem_samples: List[float] = []

            while proc.returncode is None:
                await asyncio.sleep(monitoring_config.poll_interval_seconds)
                if proc.returncode is not None: break

                try:
                    if not p.is_running(): break

                    cpu_percent = p.cpu_percent(interval=None) / 100.0
                    mem_percent = p.memory_info().rss / total_ram
                    metrics["samples_collected"] += 1
                    all_cpu_samples.append(cpu_percent)
                    all_mem_samples.append(mem_percent)
                    metrics["peak_cpu"] = max(metrics["peak_cpu"], cpu_percent)
                    metrics["peak_mem"] = max(metrics["peak_mem"], mem_percent)

                    alpha = monitoring_config.smoothing_alpha
                    ema_cpu = cpu_percent if ema_cpu is None else alpha * cpu_percent + (1 - alpha) * ema_cpu
                    ema_mem = mem_percent if ema_mem is None else alpha * mem_percent + (1 - alpha) * ema_mem

                    self.monitor_log.info("sample", run_id=run_id, tool=command_str.split()[0], pid=proc.pid,
                                          cpu=cpu_percent, mem=mem_percent, ema_cpu=ema_cpu, ema_mem=ema_mem,
                                          threshold_cpu=monitoring_config.cpu_limit, threshold_mem=monitoring_config.mem_limit)

                    is_over_limit = ema_cpu >= monitoring_config.cpu_limit or ema_mem >= monitoring_config.mem_limit
                    now = time.time()

                    if is_over_limit:
                        if over_limit_start_time is None:
                            over_limit_start_time = now
                            self.monitor_log.warning("threshold_breach_start", run_id=run_id, over_metric="cpu" if ema_cpu > monitoring_config.cpu_limit else "mem",
                                                     over_value=max(ema_cpu, ema_mem))
                    else:
                        over_limit_start_time = None

                    if over_limit_start_time and (now - over_limit_start_time) >= monitoring_config.breach_window_seconds:
                        metrics["aborted"] = True
                        metrics["abort_reason"] = "resource_limit"
                        metrics["time_to_abort"] = now - over_limit_start_time
                        self.monitor_log.critical("threshold_breach_sustained", run_id=run_id, duration=metrics["time_to_abort"])
                        await self._terminate_process_group(proc.pid, run_id)
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
        except (psutil.NoSuchProcess, asyncio.CancelledError):
            pass
        except Exception as e:
            self.log.error("Error in resource monitor", error=str(e), run_id=run_id)

        if all_cpu_samples: metrics["avg_cpu"] = sum(all_cpu_samples) / len(all_cpu_samples)
        if all_mem_samples: metrics["avg_mem"] = sum(all_mem_samples) / len(all_mem_samples)
        return metrics

    async def _run_single_command(self, command: list[str], timeout: int) -> CommandResult:
        cmd_str = " ".join(command)
        log = self.log.bind(command=cmd_str, timeout=timeout)
        log.info("Starting command")

        proc = None
        monitor_task = None
        monitor_metrics: Dict[str, Any] = {}

        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid  # Create a new process session
            )

            monitor_task = asyncio.create_task(self._monitor_resources(proc, cmd_str))

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            finally:
                # Always ensure the monitor task is awaited to get its final metrics,
                # especially in the case of an abort where it finishes after killing the process.
                if not monitor_task.done():
                    monitor_task.cancel()
                try:
                    monitor_metrics = await monitor_task
                except asyncio.CancelledError:
                    # This is expected if the main process finished normally.
                    if not monitor_metrics:
                        monitor_metrics = {}

            stdout = stdout_bytes.decode('utf-8', errors='ignore').strip()
            stderr = stderr_bytes.decode('utf-8', errors='ignore').strip()

            aborted = monitor_metrics.get("aborted", False)
            if proc.returncode != 0 and aborted:
                log.warning("Command was aborted due to excessive resource usage", **monitor_metrics)
                stderr = f"Command aborted after exceeding resource limits. Reason: {monitor_metrics.get('abort_reason')}."
            elif proc.returncode == 0:
                log.info("Command finished successfully", return_code=proc.returncode)
            else:
                log.warning("Command finished with an error", return_code=proc.returncode, stderr=stderr)

            return CommandResult(
                command=cmd_str, stdout=stdout, stderr=stderr, return_code=proc.returncode,
                **monitor_metrics
            )

        except asyncio.TimeoutError:
            log.error("Command timed out")
            if proc and proc.returncode is None:
                await self._terminate_process_group(proc.pid, f"timeout-{proc.pid}")
            return CommandResult(command=cmd_str, stdout="", stderr=f"Timeout occurred after {timeout} seconds.",
                                 return_code=None, timed_out=True)
        except FileNotFoundError:
            log.error("Command not found", command=command[0])
            return CommandResult(command=cmd_str, stdout="", stderr=f"Command not found: {command[0]}", return_code=None)
        except Exception as e:
            log.exception("An unexpected error occurred while running command")
            return CommandResult(command=cmd_str, stdout="", stderr=str(e), return_code=None)
        finally:
            if monitor_task and not monitor_task.done():
                monitor_task.cancel()

    async def run_commands(self, commands: list[list[str]], timeout: int) -> list[CommandResult]:
        if not commands: return []
        self.log.info("Starting a batch of commands", command_count=len(commands), timeout=timeout)
        tasks = [self._run_single_command(cmd, timeout) for cmd in commands]
        results = await asyncio.gather(*tasks)
        self.log.info("Finished running batch of commands.")
        return results
