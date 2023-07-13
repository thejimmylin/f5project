from pathlib import Path
import sys

__all__ = ["create_f5project"]


def create_f5project(dst: Path | str = '.') -> None:
    """Create a project with templates."""

    if len(sys.argv) == 2:
        dst = sys.argv[1]

    if isinstance(dst, str):
        dst = Path(dst).resolve()

    dst.resolve().parent.mkdir(parents=True, exist_ok=True)

    src = Path(__file__).parent / "templates"

    all_src_files = src.glob("**/*")
    src_files = [f for f in all_src_files if "__pycache__" not in f.parts]
    for src_file in src_files:
        if src_file.is_file():
            dst_file = dst / src_file.relative_to(src)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_text(src_file.read_text())
