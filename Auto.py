from pathlib import Path
from collections import defaultdict
import pandas as pd
import re


# ============================================================
# CONFIGURATION
# ============================================================

# Base directory of the repository.
# GitPath from Excel will be relative to this directory.
BASE_REPO = Path(
    "/root/amiyanshu/ubuntu_test/FunctionTest"
).resolve()

# Excel containing GitPath, TestParamID and CaseID
EXCEL_FILE = Path(
    "/root/amiyanshu/case_ids.xlsx"
).resolve()

# Excel column names
COL_GIT_PATH = "GitPath"
COL_PARAM_ID = "TestParamID"
COL_CASE_ID = "CaseID"

# True  -> only show what would be changed
# False -> actually modify the C++ files
DRY_RUN = True


# ============================================================
# REGEX
# ============================================================

# Matches ONLY the CM10 TestRail ID line.
#
# Examples:
#
# * CM10 TestRail ID:
# * CM10 TestRail ID: C123, C456
# * CM10 TestRail Case ID - C123
#
# CM7, CM9 etc. will NOT match.
CM10_PATTERN = re.compile(
    r"(?im)^"
    r"(?P<prefix>\s*\*?\s*CM10\s+TestRail\s+(?:Case\s+)?ID\s*[:\-])"
    r"[^\r\n]*"
)


# Finds parameter definitions:
#
# [0] = {
# [1]={
# [11] = {
#
PARAM_START_PATTERN = re.compile(
    r"(?m)^\s*\[(\d+)\]\s*="
)


# Matches a TestRail Case ID comment:
#
# /*C3256386*/
# /* C3256386 */
#
CASE_COMMENT_PATTERN = re.compile(
    r"/\*\s*C\d+\s*\*/",
    re.IGNORECASE
)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_git_path(value):
    """
    Normalize GitPath from Excel.

    Examples:

    CommonTP\\nvme\\abc
        ->
    CommonTP/nvme/abc

    /CommonTP/nvme/abc
        ->
    CommonTP/nvme/abc

    FunctionTest/CommonTP/nvme/abc
        ->
    CommonTP/nvme/abc
    """

    value = str(value).strip()

    # Convert Windows path separators
    value = value.replace("\\", "/")

    # Remove duplicate slashes
    value = re.sub(r"/+", "/", value)

    # We need a path relative to BASE_REPO
    value = value.lstrip("/")

    # If Excel accidentally includes FunctionTest/
    # remove it because BASE_REPO already points there.
    if value.lower().startswith("functiontest/"):
        value = value[len("FunctionTest/"):]

    return Path(value)


def normalize_case_id(value):
    """
    Normalize Case ID.

    Examples:

        C3256386 -> C3256386
        c3256386 -> C3256386
        3256386  -> C3256386

    Also handles Excel numeric values like:
        3256386.0
    """

    value = str(value).strip()

    if value.endswith(".0"):
        value = value[:-2]

    value = value.upper()

    if not value.startswith("C"):
        value = "C" + value

    if not re.fullmatch(r"C\d+", value):
        raise ValueError(
            f"Invalid Case ID: {value}"
        )

    return value


def normalize_param_id(value):
    """
    Normalize TestParamID.

    Supports:
        0
        1
        2.0
        "3"
    """

    return int(float(value))


# ============================================================
# RESOLVE C++ FILE
# ============================================================

def resolve_cpp_file(git_path):
    """
    Resolve GitPath relative to BASE_REPO.

    Excel:

    CommonTP/nvme/.../FW_Transition_Common

    becomes:

    /root/.../FunctionTest/
        CommonTP/nvme/.../FW_Transition_Common.cpp
    """

    relative_path = normalize_git_path(git_path)

    # Add .cpp if Excel doesn't already contain it
    if relative_path.suffix.lower() != ".cpp":
        relative_path = relative_path.with_suffix(".cpp")

    cpp_file = (BASE_REPO / relative_path).resolve()

    # Safety check:
    # Don't allow Excel paths such as ../../something
    # to modify files outside the repository.
    try:
        cpp_file.relative_to(BASE_REPO)
    except ValueError:
        raise ValueError(
            f"GitPath points outside BASE_REPO:\n"
            f"  {git_path}"
        )

    return cpp_file


# ============================================================
# LOAD EXCEL
# ============================================================

def load_excel_mapping():
    """
    Build:

    {
        GitPath1: {
            0: Cxxxx,
            1: Cxxxx,
            2: Cxxxx
        },

        GitPath2: {
            0: Cxxxx,
            1: Cxxxx
        }
    }

    Excel rows do NOT need to be contiguous.
    """

    df = pd.read_excel(EXCEL_FILE)

    required_columns = {
        COL_GIT_PATH,
        COL_PARAM_ID,
        COL_CASE_ID
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Missing required Excel columns: "
            + ", ".join(sorted(missing_columns))
        )

    mapping = defaultdict(dict)

    for index, row in df.iterrows():

        # Skip incomplete rows
        if pd.isna(row[COL_GIT_PATH]):
            continue

        if pd.isna(row[COL_PARAM_ID]):
            continue

        if pd.isna(row[COL_CASE_ID]):
            continue

        git_path = normalize_git_path(
            row[COL_GIT_PATH]
        )

        param_id = normalize_param_id(
            row[COL_PARAM_ID]
        )

        case_id = normalize_case_id(
            row[COL_CASE_ID]
        )

        # --------------------------------------------
        # Check for conflicting duplicates
        # --------------------------------------------

        if param_id in mapping[git_path]:

            previous_case = mapping[git_path][param_id]

            if previous_case != case_id:

                raise ValueError(
                    "\nConflicting Excel mapping found:\n"
                    f"GitPath   : {git_path}\n"
                    f"Param ID  : {param_id}\n"
                    f"Old Case  : {previous_case}\n"
                    f"New Case  : {case_id}\n"
                    f"Excel Row : {index + 2}"
                )

        mapping[git_path][param_id] = case_id

    return mapping


# ============================================================
# GET ORDERED CASE IDs
# ============================================================

def get_ordered_case_ids(param_mapping):
    """
    Return Case IDs ordered by TestParamID.

    Duplicate Case IDs are included only once in CM10.

    Example:

    0 -> C100
    1 -> C101
    2 -> C100
    3 -> C103

    CM10 becomes:

    C100, C101, C103
    """

    case_ids = []

    for param_id in sorted(param_mapping):

        case_id = param_mapping[param_id]

        if case_id not in case_ids:
            case_ids.append(case_id)

    return case_ids


# ============================================================
# UPDATE CM10
# ============================================================

def update_cm10(content, param_mapping):
    """
    Update ONLY CM10.

    Existing:
        * CM10 TestRail ID: C111, C222

    becomes:
        * CM10 TestRail ID: C100, C101, C102

    CM7, CM9, etc. are untouched.

    If CM10 doesn't exist, it is inserted into the
    first header comment.
    """

    case_ids = get_ordered_case_ids(
        param_mapping
    )

    case_string = ", ".join(case_ids)

    match = CM10_PATTERN.search(content)

    # --------------------------------------------
    # CM10 already exists
    # --------------------------------------------

    if match:

        replacement = (
            match.group("prefix")
            + " "
            + case_string
        )

        content = (
            content[:match.start()]
            + replacement
            + content[match.end():]
        )

        return content, "UPDATED"

    # --------------------------------------------
    # CM10 does NOT exist
    # --------------------------------------------

    comment_start = content.find("/*")

    if comment_start == -1:

        return (
            content,
            "NOT ADDED - header comment not found"
        )

    comment_end = content.find(
        "*/",
        comment_start
    )

    if comment_end == -1:

        return (
            content,
            "NOT ADDED - malformed header comment"
        )

    # Determine the comment style.
    #
    # Usually your header is:
    #
    # *
    # * CM9 ...
    # *
    # */

    insertion = (
        f"* CM10 TestRail ID: {case_string}\n"
    )

    # Make sure it starts on a new line
    before = content[:comment_end]

    if before and not before.endswith("\n"):
        insertion = "\n" + insertion

    content = (
        before
        + insertion
        + content[comment_end:]
    )

    return content, "ADDED"


# ============================================================
# UPDATE TEST PARAMETER CASE IDS
# ============================================================

def update_parameter_case_ids(
    content,
    param_mapping
):
    """
    For:

    [0]={...},
    /* description */ /*C111*/

    and Excel:

    TestParamID = 0
    CaseID      = C3256386

    update ONLY:

    /*C111*/

    to:

    /*C3256386*/

    The parameter definition and description comment
    are untouched.
    """

    matches = list(
        PARAM_START_PATTERN.finditer(content)
    )

    updated = 0
    already_correct = 0

    missing_comments = []
    missing_excel_mapping = []

    # --------------------------------------------
    # Work backwards.
    #
    # This means changing text won't invalidate
    # positions for parameter blocks above it.
    # --------------------------------------------

    for index in range(
        len(matches) - 1,
        -1,
        -1
    ):

        match = matches[index]

        param_id = int(
            match.group(1)
        )

        # ----------------------------------------
        # Parameter exists in C++ but Excel
        # doesn't contain mapping for it.
        #
        # DO NOT modify it.
        # ----------------------------------------

        if param_id not in param_mapping:

            missing_excel_mapping.append(
                param_id
            )

            continue

        expected_case_id = (
            param_mapping[param_id]
        )

        block_start = match.start()

        # ----------------------------------------
        # Parameter block ends when next
        # [TestParamID] begins.
        # ----------------------------------------

        if index + 1 < len(matches):

            block_end = (
                matches[index + 1].start()
            )

        else:

            # Last parameter.
            #
            # Limit search to avoid accidentally
            # finding Case IDs much later in file.
            block_end = min(
                len(content),
                match.start() + 1500
            )

        block = content[
            block_start:block_end
        ]

        case_matches = list(
            CASE_COMMENT_PATTERN.finditer(
                block
            )
        )

        # ----------------------------------------
        # No /*Cxxxx*/ found for this parameter
        # ----------------------------------------

        if not case_matches:

            missing_comments.append(
                param_id
            )

            continue

        # Normally the TestRail ID is the last
        # /*Cxxxx*/ comment belonging to the
        # parameter.
        case_match = case_matches[-1]

        old_comment = (
            case_match.group(0)
        )

        new_comment = (
            f"/*{expected_case_id}*/"
        )

        # Already correct
        if old_comment.replace(" ", "").upper() == \
                new_comment.upper():

            already_correct += 1
            continue

        absolute_start = (
            block_start
            + case_match.start()
        )

        absolute_end = (
            block_start
            + case_match.end()
        )

        content = (
            content[:absolute_start]
            + new_comment
            + content[absolute_end:]
        )

        updated += 1

    return {
        "content": content,
        "updated": updated,
        "already_correct": already_correct,
        "missing_comments": sorted(
            missing_comments
        ),
        "missing_excel": sorted(
            missing_excel_mapping
        )
    }


# ============================================================
# VALIDATE EXCEL PARAM IDS AGAINST C++
# ============================================================

def validate_parameter_ids(
    content,
    param_mapping
):
    """
    Check whether every TestParamID from Excel
    actually exists in the C++ file.
    """

    cpp_param_ids = {
        int(value)
        for value
        in PARAM_START_PATTERN.findall(content)
    }

    excel_param_ids = set(
        param_mapping.keys()
    )

    missing_in_cpp = (
        excel_param_ids
        - cpp_param_ids
    )

    return sorted(missing_in_cpp)


# ============================================================
# PROCESS ONE CPP FILE
# ============================================================

def process_file(
    git_path,
    param_mapping
):

    cpp_file = resolve_cpp_file(
        git_path
    )

    print()
    print("=" * 80)
    print(f"GitPath : {git_path}")
    print(f"C++ File: {cpp_file}")
    print("=" * 80)

    # --------------------------------------------
    # File existence
    # --------------------------------------------

    if not cpp_file.exists():

        print(
            "[ERROR] C++ file does not exist."
        )

        return False

    # --------------------------------------------
    # Read
    # --------------------------------------------

    try:

        original_content = (
            cpp_file.read_text(
                encoding="utf-8"
            )
        )

    except UnicodeDecodeError:

        print(
            "[ERROR] Could not read file "
            "as UTF-8."
        )

        return False

    content = original_content

    # --------------------------------------------
    # Show Excel mappings
    # --------------------------------------------

    print(
        f"Excel mappings: "
        f"{len(param_mapping)}"
    )

    for param_id in sorted(
        param_mapping
    ):

        print(
            f"  TestParamID {param_id:>3}"
            f" -> "
            f"{param_mapping[param_id]}"
        )

    # --------------------------------------------
    # Validate
    # --------------------------------------------

    missing_in_cpp = (
        validate_parameter_ids(
            content,
            param_mapping
        )
    )

    if missing_in_cpp:

        print()
        print(
            "[WARNING] These TestParamIDs "
            "exist in Excel but NOT in C++:"
        )

        print(
            f"  {missing_in_cpp}"
        )

    # --------------------------------------------
    # Update CM10
    # --------------------------------------------

    content, cm10_status = (
        update_cm10(
            content,
            param_mapping
        )
    )

    print()
    print(
        f"CM10 status: {cm10_status}"
    )

    # --------------------------------------------
    # Update individual parameter Case IDs
    # --------------------------------------------

    result = (
        update_parameter_case_ids(
            content,
            param_mapping
        )
    )

    content = result["content"]

    print(
        "Parameter Case IDs updated : "
        f"{result['updated']}"
    )

    print(
        "Already correct            : "
        f"{result['already_correct']}"
    )

    # --------------------------------------------
    # Warnings
    # --------------------------------------------

    if result["missing_comments"]:

        print()
        print(
            "[WARNING] No /*Cxxxx*/ "
            "comment found for:"
        )

        print(
            "  TestParamID:",
            result["missing_comments"]
        )

    if result["missing_excel"]:

        print()
        print(
            "[INFO] These C++ TestParamIDs "
            "have no Excel mapping and "
            "were left untouched:"
        )

        print(
            " ",
            result["missing_excel"]
        )

    # --------------------------------------------
    # Nothing changed
    # --------------------------------------------

    if content == original_content:

        print()
        print(
            "[NO CHANGE] File already correct."
        )

        return True

    # --------------------------------------------
    # Dry run
    # --------------------------------------------

    if DRY_RUN:

        print()
        print(
            "[DRY RUN] Changes found, "
            "but file was NOT modified."
        )

        return True

    # --------------------------------------------
    # Write changes
    # --------------------------------------------

    cpp_file.write_text(
        content,
        encoding="utf-8"
    )

    print()
    print(
        "[UPDATED] File successfully modified."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("TestRail Case ID Updater")
    print("=" * 80)

    print(
        f"Base repo : {BASE_REPO}"
    )

    print(
        f"Excel     : {EXCEL_FILE}"
    )

    print(
        f"Dry run   : {DRY_RUN}"
    )

    # --------------------------------------------
    # Validate configuration
    # --------------------------------------------

    if not BASE_REPO.exists():

        raise FileNotFoundError(
            f"BASE_REPO does not exist:\n"
            f"{BASE_REPO}"
        )

    if not EXCEL_FILE.exists():

        raise FileNotFoundError(
            f"Excel file does not exist:\n"
            f"{EXCEL_FILE}"
        )

    # --------------------------------------------
    # Load Excel
    # --------------------------------------------

    mapping = load_excel_mapping()

    print()
    print(
        "Unique GitPaths found in Excel: "
        f"{len(mapping)}"
    )

    # --------------------------------------------
    # Process each unique C++ file
    # --------------------------------------------

    successful = 0
    failed = 0

    for git_path, param_mapping \
            in mapping.items():

        try:

            result = process_file(
                git_path,
                param_mapping
            )

            if result:
                successful += 1
            else:
                failed += 1

        except Exception as error:

            failed += 1

            print()
            print(
                f"[ERROR] {git_path}"
            )

            print(
                f"        {error}"
            )

    # --------------------------------------------
    # Final summary
    # --------------------------------------------

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        f"Files processed successfully : "
        f"{successful}"
    )

    print(
        f"Files failed                 : "
        f"{failed}"
    )

    print(
        f"Dry run                      : "
        f"{DRY_RUN}"
    )

    if DRY_RUN:

        print()
        print(
            "No files were modified."
        )

        print(
            "After verifying the output, "
            "set DRY_RUN = False."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
