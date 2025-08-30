import asyncio
from dataclasses import dataclass, asdict
from .logging_setup import get_logger

# A simple data class to structure the results of each command
@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    return_code: int | None
    timed_out: bool = False

class AsyncToolRunner:
    """
    A class to run multiple shell commands asynchronously with timeouts.
    """
    def __init__(self):
        self.log = get_logger(self.__class__.__name__)

    async def _run_single_command(self, command: list[str], timeout: int) -> CommandResult:
        """
        Runs a single command asynchronously with a specified timeout.
        """
        cmd_str = " ".join(command)
        log = self.log.bind(command=cmd_str, timeout=timeout)
        log.info("Starting command")

        try:
            # Create the subprocess
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for the process to complete with a timeout
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            # Decode stdout and stderr
            stdout = stdout_bytes.decode('utf-8', errors='ignore').strip()
            stderr = stderr_bytes.decode('utf-8', errors='ignore').strip()

            if proc.returncode == 0:
                log.info("Command finished successfully", stdout=stdout, stderr=stderr, return_code=proc.returncode)
            else:
                log.warning("Command finished with an error", stdout=stdout, stderr=stderr, return_code=proc.returncode)

            return CommandResult(
                command=cmd_str,
                stdout=stdout,
                stderr=stderr,
                return_code=proc.returncode
            )

        except asyncio.TimeoutError:
            log.error("Command timed out")
            # Attempt to clean up the process
            if 'proc' in locals() and proc.returncode is None:
                try:
                    proc.kill()
                    await proc.wait()
                except ProcessLookupError:
                    # Process might have finished just as timeout occurred
                    pass
            return CommandResult(
                command=cmd_str,
                stdout="",
                stderr="Timeout occurred after {} seconds.".format(timeout),
                return_code=None,
                timed_out=True
            )
        except FileNotFoundError:
            log.error("Command not found", command=command[0])
            return CommandResult(
                command=cmd_str,
                stdout="",
                stderr=f"Command not found: {command[0]}",
                return_code=None,
                timed_out=False
            )
        except Exception as e:
            log.exception("An unexpected error occurred while running command")
            return CommandResult(
                command=cmd_str,
                stdout="",
                stderr=str(e),
                return_code=None,
                timed_out=False
            )

    async def run_commands(self, commands: list[list[str]], timeout: int) -> list[CommandResult]:
        """
        Runs a list of commands in parallel and returns their results.
        """
        if not commands:
            return []

        self.log.info("Starting a batch of commands", command_count=len(commands), timeout=timeout)

        # Create a list of tasks to run concurrently
        tasks = [self._run_single_command(cmd, timeout) for cmd in commands]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        self.log.info("Finished running batch of commands.")
        return results
