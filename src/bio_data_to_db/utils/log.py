import logging
import os
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

logger = logging.getLogger(__name__)

console = Console(
    theme=Theme(
        {
            "logging.level.error": "bold red blink",
            "logging.level.critical": "red blink",
            "logging.level.warning": "yellow",
        }
    )
)


def setup_logging(
    console_level: int | str = logging.INFO,
    output_files: list[str] | None = None,
    file_levels: list[int | str] | None = None,
):
    """
    Setup logging with RichHandler and FileHandler.

    You should call this function at the beginning of your script.

    Args:
        console_level: Logging level for console. Defaults to INFO or env var PPMI_LOG_LEVEL.
        output_files: List of output file paths, relative to LOG_DIR. If None, use default.
        file_levels: List of logging levels for each output file. If None, use default.
    """
    if output_files is None:
        output_files = []
    if file_levels is None:
        file_levels = []

    assert len(output_files) == len(
        file_levels
    ), "output_files and file_levels must have the same length"

    # NOTE: Initialise with NOTSET level and null device, and add stream handler separately.
    # This way, the root logging level is NOTSET (log all), and we can customise each handler's behaviour.
    # If we set the level during the initialisation, it will affect to ALL streams,
    # so the file stream cannot be more verbose (lower level) than the console stream.
    logging.basicConfig(
        format="",
        level=logging.NOTSET,
        stream=open(os.devnull, "w"),  # noqa: SIM115
    )

    # If you want to suppress logs from other modules, set their level to WARNING or higher
    # logging.getLogger("slowfast.utils.checkpoint").setLevel(logging.WARNING)

    console_handler = RichHandler(
        level=console_level,
        show_time=True,
        show_level=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        console=console,
    )
    console_format = logging.Formatter(
        fmt="%(name)s - %(message)s",
        datefmt="%m/%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)

    f_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s: %(lineno)4d - %(levelname)s - %(message)s",
        datefmt="%y/%m/%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)

    log_paths = []
    for output_file, file_level in zip(output_files, file_levels, strict=True):
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        f_handler = logging.FileHandler(output_file)
        f_handler.setLevel(file_level)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        root_logger.addHandler(f_handler)

    for log_path in log_paths:
        logger.info(f"Logging to {log_path}")


def main():
    logger.info("Hello, world!")
    raise Exception("Test exception")


if __name__ == "__main__":
    try:
        setup_logging()
        main()
    except Exception:
        logger.exception("Exception occurred")
