import os
from pathlib import Path

import openpyxl


# ============================================================
# CONFIGURATION
# ============================================================

# Root of Pyate22 repository
REPO_PATH = r"/path/to/Pyate22"

# Path under which CaseIDs should be searched.
# Keep this as REPO_PATH to search the complete repository.
# You can also give a smaller path for faster searching.
SEARCH_PATH = REPO_PATH

# Excel file containing CaseID
EXCEL_PATH = r"/path/to/input.xlsx"

# Excel sheet name
SHEET_NAME = "Remaining shyam san"

# Input column
CASE_ID_COLUMN = "CaseID"

# Output columns
OUTPUT_COLUMN = "AutomationSuites"
SCRIPT_OUTPUT_COLUMN = "automation_script"


# ============================================================
# CREATE GIT PATH
# ============================================================

def get_git_path(file_path):
    """
    Convert actual file path:

    /home/user/Pyate22/tests/test_external_generic/
    test_mctp_outband/.../test_format_ocp_2_7_dif_1_0201.py

    Into:

    Pyate22/tests/test_external_generic/
    test_mctp_outband/.../test_format_ocp_2_7_dif_1_0201/
    """

    file_path = Path(file_path)
    repo_path = Path(REPO_PATH)

    # Get path relative to Pyate22
    relative = file_path.relative_to(repo_path)

    # Remove .py and treat script name as final folder
    script_name = file_path.stem

    relative_path = relative.parent / script_name

    git_path = (
        repo_path.name
        + "/"
        + relative_path.as_posix()
        + "/"
    )

    return git_path


# ============================================================
# LOAD ALL PYTHON FILES
# ============================================================

def load_python_files():
    """
    Read all .py files under SEARCH_PATH only once.

    We store:
        full file path
        file content

    Content is converted to lowercase so CaseID search
    becomes case-insensitive.
    """

    python_files = []

    print("========================================")
    print("Scanning Python files...")
    print("========================================")

    for root, _, files in os.walk(SEARCH_PATH):

        for filename in files:

            if not filename.lower().endswith(".py"):
                continue

            full_path = os.path.join(
                root,
                filename
            )

            try:

                with open(
                    full_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as file:

                    content = file.read().lower()

                python_files.append(
                    (full_path, content)
                )

            except Exception as error:

                print(
                    f"[READ ERROR] "
                    f"{full_path}: {error}"
                )

    print(
        f"Loaded {len(python_files)} Python files."
    )

    print()

    return python_files


# ============================================================
# FIND CASE ID
# ============================================================

def find_case_id(case_id, python_files):
    """
    Search CaseID inside every Python file.

    Example CaseID:
        C3119818

    It will find all of these:

        _c3119818

        @TestCaseId: C3119818

        def test_xxx_c3119818(...):

        case_id = "C3119818"

    because search is case-insensitive.

    Returns:
        git_path, script_name

    If not found:
        None, None
    """

    if case_id is None:
        return None, None

    case_id = str(case_id).strip().lower()

    if not case_id:
        return None, None

    for file_path, content in python_files:

        if case_id in content:

            git_path = get_git_path(
                file_path
            )

            script_name = Path(
                file_path
            ).name

            return git_path, script_name

    return None, None


# ============================================================
# FIND EXCEL COLUMN
# ============================================================

def find_column(ws, column_name):
    """
    Find column number using column header.

    Header comparison is case-insensitive.
    """

    for cell in ws[1]:

        if not cell.value:
            continue

        current_header = str(
            cell.value
        ).strip().lower()

        if current_header == column_name.lower():
            return cell.column

    raise ValueError(
        f"Column '{column_name}' not found."
    )


# ============================================================
# GET OR CREATE COLUMN
# ============================================================

def get_or_create_column(ws, column_name):
    """
    Return existing column if present.

    Otherwise create a new column at the end.
    """

    try:

        return find_column(
            ws,
            column_name
        )

    except ValueError:

        new_column = ws.max_column + 1

        ws.cell(
            row=1,
            column=new_column
        ).value = column_name

        return new_column


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # STEP 1
    # Load all Python files once
    # --------------------------------------------------------

    python_files = load_python_files()

    if not python_files:

        print(
            "[ERROR] No Python files found "
            f"under: {SEARCH_PATH}"
        )

        return

    # --------------------------------------------------------
    # STEP 2
    # Open Excel
    # --------------------------------------------------------

    print(
        f"Opening Excel: {EXCEL_PATH}"
    )

    wb = openpyxl.load_workbook(
        EXCEL_PATH
    )

    # Check sheet
    if SHEET_NAME not in wb.sheetnames:

        print(
            f"[ERROR] Sheet '{SHEET_NAME}' "
            "does not exist."
        )

        print(
            "Available sheets:"
        )

        for sheet in wb.sheetnames:
            print(f"  - {sheet}")

        return

    ws = wb[SHEET_NAME]

    # --------------------------------------------------------
    # STEP 3
    # Find CaseID column
    # --------------------------------------------------------

    try:

        case_id_col = find_column(
            ws,
            CASE_ID_COLUMN
        )

    except ValueError as error:

        print(f"[ERROR] {error}")

        return

    # --------------------------------------------------------
    # STEP 4
    # Create/find output columns
    # --------------------------------------------------------

    automation_suites_col = (
        get_or_create_column(
            ws,
            OUTPUT_COLUMN
        )
    )

    automation_script_col = (
        get_or_create_column(
            ws,
            SCRIPT_OUTPUT_COLUMN
        )
    )

    print()
    print(
        f"CaseID column            : "
        f"{case_id_col}"
    )

    print(
        f"AutomationSuites column  : "
        f"{automation_suites_col}"
    )

    print(
        f"automation_script column : "
        f"{automation_script_col}"
    )

    print()

    # --------------------------------------------------------
    # STEP 5
    # Search CaseIDs
    # --------------------------------------------------------

    found_count = 0
    not_found_count = 0

    for row in range(
        2,
        ws.max_row + 1
    ):

        case_id = ws.cell(
            row=row,
            column=case_id_col
        ).value

        # Ignore completely empty CaseID rows
        if case_id is None:
            continue

        case_id = str(
            case_id
        ).strip()

        if not case_id:
            continue

        # ----------------------------------------------------
        # Search repository
        # ----------------------------------------------------

        git_path, script_name = (
            find_case_id(
                case_id,
                python_files
            )
        )

        # ----------------------------------------------------
        # FOUND
        # ----------------------------------------------------

        if git_path:

            automation_suite = (
                "TestParamID : NA, "
                f"GitPath : {git_path}"
            )

            # Write AutomationSuites
            ws.cell(
                row=row,
                column=automation_suites_col
            ).value = automation_suite

            # Write actual .py filename
            ws.cell(
                row=row,
                column=automation_script_col
            ).value = script_name

            print(
                f"[FOUND] {case_id}"
            )

            print(
                f"        Script : "
                f"{script_name}"
            )

            print(
                f"        Path   : "
                f"{git_path}"
            )

            found_count += 1

        # ----------------------------------------------------
        # NOT FOUND
        # ----------------------------------------------------

        else:

            # Keep AutomationSuites blank
            ws.cell(
                row=row,
                column=automation_suites_col
            ).value = None

            # Keep automation_script blank
            ws.cell(
                row=row,
                column=automation_script_col
            ).value = None

            print(
                f"[CASE ID NOT FOUND] "
                f"{case_id}"
            )

            not_found_count += 1

    # --------------------------------------------------------
    # STEP 6
    # Save SAME Excel
    # --------------------------------------------------------

    try:

        wb.save(
            EXCEL_PATH
        )

    except PermissionError:

        print()
        print(
            "[ERROR] Unable to save Excel."
        )

        print(
            "Please close the Excel file if it "
            "is currently open and run the script again."
        )

        return

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("========================================")
    print("COMPLETED")
    print("========================================")

    print(
        f"Found              : "
        f"{found_count}"
    )

    print(
        f"Case IDs not found : "
        f"{not_found_count}"
    )

    print(
        f"Excel updated      : "
        f"{EXCEL_PATH}"
    )

    print("========================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
