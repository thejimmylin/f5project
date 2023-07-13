#!.venv/bin/python
"""Set up GitHub secrets with local config

Install it as a Git pre-push hook by:
`chmod 755 scripts/setup_github_secrets.py && ln -s ../../scripts/setup_github_secrets.py .git/hooks/pre-push`

Notes:
1. When you `git push`, it will be triggered.
2. It uses `.venv/bin/python` as interpreter, so make sure you have created a virtual environment.
3. Uninstall it by `rm .git/hooks/pre-push`.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    sys.path.insert(0, str(BASE_DIR))
    from main import project

    project.setup_github_secrets()
