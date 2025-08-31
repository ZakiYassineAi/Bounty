import asyncio
from dataclasses import dataclass, asdict
from .logging_setup import get_logger
import psutil
import time

# A simple data class to structure the results of each command
@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    return_code: int | None
    timed_out: bool = False
    aborted: bool = False

class AsyncToolRunner:
    """
    A class to run multiple shell commands asynchronously with timeouts and resource monitoring.
    """
    def __init__(self):
        self.log = get_logger(self.__class__.__name__)

    async def _monitor_resources(self, proc: asyncio.subprocess.Process, command_str: str) -> bool:
        """
        Monitors the resource usage of a process. If usage is too high for too long,
        it kills the process.
        Returns True if the process was aborted, False otherwise.
        """
        try:
            p = psutil.Process(proc.pid)
            # First call is to initialize, subsequent calls will have a meaningful value
            p.cpu_percent(interval=None)

            high_usage_start_time = None
            CPU_THRESHOLD = 80.0
            MEM_THRESHOLD = 75.0
            TIME_LIMIT_SECONDS = 30

            while proc.returncode is None:
                await asyncio.sleep(1) # Check every second

                if proc.returncode is not None:
                    break

                try:
                    if not p.is_running():
                        break

                    cpu_percent = p.cpu_percent(interval=None)
                    mem_percent = p.memory_percent()

                    if cpu_percent > CPU_THRESHOLD or mem_percent > MEM_THRESHOLD:
                        if high_usage_start_time is None:
                            high_usage_start_time = time.time()
                        elif time.time() - high_usage_start_time > TIME_LIMIT_SECONDS:
                            self.log.warning(
                                "Aborting command due to excessive resource usage",
                                command=command_str,
                                cpu_percent=cpu_percent,
                                memory_percent=mem_percent,
                            )
                            p.kill()
                            return True  # Aborted
                    else:
                        high_usage_start_time = None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break # Process ended before we could check it
        except psutil.NoSuchProcess:
            pass # Process finished before monitoring could start
        except asyncio.CancelledError:
            pass # Monitoring was cancelled, which is expected
        except Exception as e:
            self.log.error("An unexpected error occurred in resource monitor", error=str(e), command=command_str)

        return False # Not aborted

    async def _run_single_command(self, command: list[str], timeout: int) -> CommandResult:
        """
        Runs a single command asynchronously with a specified timeout and resource monitoring.
        """
        cmd_str = " ".join(command)
        log = self.log.bind(command=cmd_str, timeout=timeout)
        log.info("Starting command")

        proc = None
        monitor_task = None
        aborted = False

        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            monitor_task = asyncio.create_task(self._monitor_resources(proc, cmd_str))

            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            if monitor_task.done():
                aborted = await monitor_task
            else:
                monitor_task.cancel()

            stdout = stdout_bytes.decode('utf-8', errors='ignore').strip()
            stderr = stderr_bytes.decode('utf-8', errors='ignore').strip()

            if proc.returncode != 0 and aborted:
                log.warning("Command was aborted due to excessive resource usage", stdout=stdout, stderr=stderr, return_code=proc.returncode)
                stderr = f"Command aborted after exceeding resource limits (CPU > 80% or Memory > 75% for 30s)."
            elif proc.returncode == 0:
                log.info("Command finished successfully", stdout=stdout, stderr=stderr, return_code=proc.returncode)
            else:
                log.warning("Command finished with an error", stdout=stdout, stderr=stderr, return_code=proc.returncode)

            return CommandResult(
                command=cmd_str,
                stdout=stdout,
                stderr=stderr,
                return_code=proc.returncode,
                aborted=aborted,
            )

        except asyncio.TimeoutError:
            log.error("Command timed out")
            if proc and proc.returncode is None:
                try:
                    proc.kill()
                    await proc.wait()
                except ProcessLookupError:
                    pass
            return CommandResult(
                command=cmd_str,
                stdout="",
                stderr="Timeout occurred after {} seconds.".format(timeout),
                return_code=None,
                timed_out=True,
                aborted=False,
            )
        except FileNotFoundError:
            log.error("Command not found", command=command[0])
            return CommandResult(
                command=cmd_str,
                stdout="",
                stderr=f"Command not found: {command[0]}",
                return_code=None,
                aborted=False
            )
        except Exception as e:
            log.exception("An unexpected error occurred while running command")
            return CommandResult(
                command=cmd_str,
                stdout="",
                stderr=str(e),
                return_code=None,
                aborted=False,
            )
        finally:
            if monitor_task and not monitor_task.done():
                monitor_task.cancel()

    async def run_commands(self, commands: list[list[str]], timeout: int) -> list[CommandResult]:
        """
        Runs a list of commands in parallel and returns their results.
        """
        if not commands:
            return []

        self.log.info("Starting a batch of commands", command_count=len(commands), timeout=timeout)
        tasks = [self._run_single_command(cmd, timeout) for cmd in commands]
        results = await asyncio.gather(*tasks)
        self.log.info("Finished running batch of commands.")
        return results
