from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

EXCEL_FILE = "case_update.xlsx"

# Root folder containing PyATE test scripts
SCRIPT_FOLDER = (
    "/home/Amiyanshu_pyATE/cm10_Throttling/ubuntu_test/"
    "FunctionTest/Pyate22/tests"
)


# ============================================================
# READ EXCEL
# ============================================================

df = pd.read_excel(
    EXCEL_FILE,
    usecols="A:C",
)

# Expected Excel columns:
# previous | tobe | scriptname

required_columns = {"previous", "tobe", "scriptname"}

if not required_columns.issubset(df.columns):
    raise ValueError(
        "Excel must contain columns: previous, tobe, scriptname"
    )


# Remove completely empty rows
df = df.dropna(
    subset=["previous", "tobe", "scriptname"]
)


# Convert everything to clean strings
df["previous"] = (
    df["previous"]
    .astype(str)
    .str.strip()
)

df["tobe"] = (
    df["tobe"]
    .astype(str)
    .str.strip()
)

df["scriptname"] = (
    df["scriptname"]
    .astype(str)
    .str.strip()
)


# ============================================================
# PREPARE SCRIPT DIRECTORY
# ============================================================

script_folder = Path(SCRIPT_FOLDER)

if not script_folder.exists():
    raise FileNotFoundError(
        f"Script folder does not exist: {script_folder}"
    )


# ============================================================
# UPDATE TEST FILES
# ============================================================

for _, row in df.iterrows():

    old_cid = row["previous"]
    new_cid = row["tobe"]
    test_name = row["scriptname"]

    print("\n" + "=" * 70)
    print(f"Processing script : {test_name}")
    print(f"Previous CID      : {old_cid}")
    print(f"New CID           : {new_cid}")

    script_found = False
    cid_found = False

    # --------------------------------------------------------
    # Search recursively for Python script
    # --------------------------------------------------------

    for py_file in script_folder.rglob("*.py"):

        # Compare filename without .py
        #
        # Example:
        # Excel:
        # test_thermal_throttling_0507
        #
        # File:
        # test_thermal_throttling_0507.py

        if py_file.stem != test_name:
            continue

        script_found = True

        print(f"Found script      : {py_file}")

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        content = py_file.read_text(
            encoding="utf-8"
        )

        # ----------------------------------------------------
        # Check old CID
        # ----------------------------------------------------

        occurrence_count = content.count(old_cid)

        if occurrence_count == 0:
            print(
                f"CID {old_cid} not found in this script."
            )
            continue

        cid_found = True

        print(
            f"Found {occurrence_count} occurrence(s) "
            f"of {old_cid}"
        )

        # ----------------------------------------------------
        # Replace ALL occurrences
        # ----------------------------------------------------

        updated_content = content.replace(
            old_cid,
            new_cid,
        )

        # ----------------------------------------------------
        # Write updated file
        # ----------------------------------------------------

        py_file.write_text(
            updated_content,
            encoding="utf-8",
        )

        print(
            f"UPDATED: {old_cid} -> {new_cid}"
        )

    # --------------------------------------------------------
    # Result for this Excel row
    # --------------------------------------------------------

    if not script_found:
        print(
            f"WARNING: Script '{test_name}' was not found."
        )

    elif not cid_found:
        print(
            f"WARNING: CID '{old_cid}' was not found "
            f"in '{test_name}'."
        )


# ============================================================
# FINISHED
# ============================================================

print("\n" + "=" * 70)
print("CID update completed.")
print("=" * 70)
