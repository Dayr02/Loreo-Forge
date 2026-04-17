"""PR validation helpers used by GitHub Actions."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


COMMIT_PATTERN = re.compile(
    r"^(feat|fix|refactor|test|docs|chore|style)\((phase-\d+|bridge|forge|godot|db|ai|ui|build)\): .+"
)
FORBIDDEN_PREFIXES = ("data/bridge/", "data/stories/")
SOURCE_EXTENSIONS = {".py", ".gd"}


def _run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def validate_commits() -> int:
    try:
        messages = _run_git("log", "--format=%s", "origin/develop..HEAD").splitlines()
    except subprocess.CalledProcessError:
        messages = _run_git("log", "--format=%s", "-n", "20").splitlines()

    invalid = [message for message in messages if message and not COMMIT_PATTERN.match(message)]
    for message in invalid:
        print(f"Invalid commit message: {message}")
    return 1 if invalid else 0


def validate_files() -> int:
    try:
        changed = _run_git("diff", "--name-only", "origin/develop...HEAD").splitlines()
    except subprocess.CalledProcessError:
        changed = _run_git("diff", "--name-only", "HEAD~1", "HEAD").splitlines()

    forbidden = [path for path in changed if path.startswith(FORBIDDEN_PREFIXES)]
    for path in forbidden:
        print(f"Forbidden committed runtime data: {path}")
    if forbidden:
        return 1

    added_sources = [Path(path) for path in changed if Path(path).suffix in SOURCE_EXTENSIONS]
    changed_tests = [path for path in changed if path.startswith("tests/")]
    if added_sources and not changed_tests:
        print("Source files changed without corresponding tests under tests/.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices={"commits", "files"}, required=True)
    args = parser.parse_args()
    return validate_commits() if args.mode == "commits" else validate_files()


if __name__ == "__main__":
    sys.exit(main())
