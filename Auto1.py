import os
import subprocess
import sys


BASE_REPO_PATH = "/home/user/repo"

# Complete absolute path from root (/)
SEARCH_PATH = "/home/user/repo/automation/test/suites"


def get_python_files(search_path):
    """Recursively find all Python files from the absolute search path."""

    if not os.path.isdir(search_path):
        print(f"ERROR: Search directory not found: {search_path}")
        return []

    python_files = []

    for root, _, files in os.walk(search_path):
        for filename in files:
            if filename.endswith(".py"):
                python_files.append(os.path.join(root, filename))

    return python_files


def run_pylint(file_path):
    """Run pylint for one file, with command executed from base repo path."""

    print("\n" + "=" * 80)
    print(f"File: {file_path}")
    print("=" * 80)

    result = subprocess.run(
        [sys.executable, "-m", "pylint", file_path],
        cwd=BASE_REPO_PATH,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    return result.returncode


def main():

    python_files = get_python_files(SEARCH_PATH)

    print(f"\nFound {len(python_files)} Python files.")

    failed_files = []

    for file_path in python_files:
        return_code = run_pylint(file_path)

        if return_code != 0:
            failed_files.append(file_path)

    print("\n" + "=" * 80)
    print("PYLINT SUMMARY")
    print("=" * 80)

    print(f"Total files: {len(python_files)}")
    print(f"Files with pylint findings: {len(failed_files)}")

    for file_path in failed_files:
        print(file_path)


if __name__ == "__main__":
    main()
