import contextlib
import logging
import os
import sys


@contextlib.contextmanager
def noprint():
    old_stdout = sys.stdout
    with open(os.devnull, "w") as blackhole:
        sys.stdout = blackhole
        yield
    sys.stdout = old_stdout


def config_basic_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(pathname)s:%(lineno)d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
