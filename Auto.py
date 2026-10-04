import os
from pathlib import Path

import openpyxl


# ============================================================
# CONFIGURATION
# ============================================================

REPO_PATH = r"/path/to/Pyate22"
EXCEL_PATH = r"/path/to/input.xlsx"

SHEET_NAME = "Sheet1"
SCRIPT_COLUMN = "automation_script"

# Name of the new column
OUTPUT_COLUMN = "GitPath"


# ============================================================
# FUNCTIONS
# ============================================================

def build_repo_index(repo_path):
    """
    Scan repository once.

    If duplicate script names exist, only the FIRST one found
    will be stored.
    """

    index = {}

    for root, dirs, files in os.walk(repo_path):

        # Store directories
        for directory in dirs:
            name = directory.lower()

            # Keep only first match
            if name not in index:
                index[name] = os.path.join(root, directory)

        # Store files
        for file in files:
            name = file.lower()

            # Keep only first match
            if name not in index:
                index[name] = os.path.join(root, file)

    return index


def get_relative_path(full_path, repo_path):
    """
    Example:

    /home/.../Pyate22/tests/abc/test_set_get_0505.py

    becomes:

    Pyate22/tests/abc/
    """

    repo = Path(repo_path)
    full = Path(full_path)

    relative = full.relative_to(repo.parent)

    # If match is a .py file, use its parent directory
    if full.is_file():
        relative = relative.parent

    return relative.as_posix().rstrip("/") + "/"


def find_script(script_name, repo_index, repo_path):

    if script_name is None:
        return None

    script_name = str(script_name).strip()

    if not script_name:
        return None

    # First try exact name
    candidates = [script_name.lower()]

    # Also support Excel values without .py
    if not script_name.lower().endswith(".py"):
        candidates.append((script_name + ".py").lower())

    for candidate in candidates:

        if candidate in repo_index:

            full_path = repo_index[candidate]

            git_path = get_relative_path(
                full_path,
                repo_path
            )

            # Required Excel format
            return f"TestParamID : NA, GitPath : {git_path}"

    return None


def find_column(ws, column_name):

    for cell in ws[1]:

        if (
            cell.value
            and str(cell.value).strip() == column_name
        ):
            return cell.column

    raise ValueError(
        f"Column '{column_name}' not found in Excel."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("Scanning repository...")

    repo_index = build_repo_index(REPO_PATH)

    print(
        f"Repository indexed: "
        f"{len(repo_index)} unique names\n"
    )

    # Open SAME Excel
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb[SHEET_NAME]

    script_col = find_column(
        ws,
        SCRIPT_COLUMN
    )

    # --------------------------------------------------------
    # Find existing output column or create a new one
    # --------------------------------------------------------

    try:
        output_col = find_column(
            ws,
            OUTPUT_COLUMN
        )

    except ValueError:
        output_col = ws.max_column + 1

        ws.cell(
            row=1,
            column=output_col
        ).value = OUTPUT_COLUMN

    found = 0
    not_found = 0

    # --------------------------------------------------------
    # Process Excel
    # --------------------------------------------------------

    for row in range(2, ws.max_row + 1):

        script_name = ws.cell(
            row=row,
            column=script_col
        ).value

        if not script_name:
            continue

        result = find_script(
            script_name,
            repo_index,
            REPO_PATH
        )

        if result:

            ws.cell(
                row=row,
                column=output_col
            ).value = result

            print(
                f"[FOUND] {script_name} -> {result}"
            )

            found += 1

        else:

            # Keep Excel blank
            ws.cell(
                row=row,
                column=output_col
            ).value = None

            print(
                f"[SCRIPT NOT FOUND] {script_name}"
            )

            not_found += 1

    # --------------------------------------------------------
    # SAVE BACK TO SAME EXCEL
    # --------------------------------------------------------

    wb.save(EXCEL_PATH)

    print("\n====================================")
    print("Completed")
    print("====================================")
    print(f"Found            : {found}")
    print(f"Script not found : {not_found}")
    print(f"Excel updated    : {EXCEL_PATH}")


if __name__ == "__main__":
    main()
