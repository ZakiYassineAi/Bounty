from bounty_command_center.logging_setup import setup_logging

# It's good practice to set up your application's logging
# when the worker starts.
setup_logging(log_to_file=True)
