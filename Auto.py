import re
from pathlib import Path

import pandas as pd


# =========================
# CONFIGURATION
# =========================

EXCEL_FILE = "cid_mapping.xlsx"
SCRIPT_FOLDER = "/home/Amiyanshu_pyATE/cm10_Throttling/ubuntu_test"


# =========================
# READ EXCEL
# =========================

# Your Excel has no header:
# Column A = CID
# Column B = test name
df = pd.read_excel(
    EXCEL_FILE,
    header=None,
    usecols="A:B",
    names=["cid", "test_name"]
)

# Clean the Excel values
df["cid"] = df["cid"].astype(str).str.strip().str.lower()
df["test_name"] = df["test_name"].astype(str).str.strip()


# =========================
# UPDATE TEST FILES
# =========================

script_folder = Path(SCRIPT_FOLDER)

for _, row in df.iterrows():

    new_cid = row["cid"]
    test_name = row["test_name"]

    print(f"\nProcessing: {test_name}")
    print(f"Expected CID: {new_cid}")

    found = False

    # Search all Python files
    for py_file in script_folder.rglob("*.py"):

        content = py_file.read_text(encoding="utf-8")

        # Find:
        # def test_thermal_throttling_0506_c1234567(
        #
        # based on:
        # test_thermal_throttling_0506

        function_pattern = (
            rf"(def\s+{re.escape(test_name)}_)"
            rf"c\d+"
            rf"(\s*\()"
        )

        if not re.search(function_pattern, content, re.IGNORECASE):
            continue

        found = True

        # -----------------------------------
        # 1. Update CID in function name
        # -----------------------------------

        updated_content = re.sub(
            function_pattern,
            rf"\g<1>{new_cid}\g<2>",
            content,
            count=1,
            flags=re.IGNORECASE
        )

        # -----------------------------------
        # 2. Update @testcaseId
        # -----------------------------------

        testcase_pattern = (
            r"(@testcaseId\s*:\s*)"
            r"c\d+"
        )

        updated_content = re.sub(
            testcase_pattern,
            rf"\g<1>{new_cid}",
            updated_content,
            count=1,
            flags=re.IGNORECASE
        )

        # -----------------------------------
        # SAVE
        # -----------------------------------

        if updated_content != content:
            py_file.write_text(
                updated_content,
                encoding="utf-8"
            )

            print(f"UPDATED: {py_file}")
        else:
            print(f"No change required: {py_file}")

        break

    if not found:
        print(f"WARNING: Test not found: {test_name}")


print("\nCID update completed.")
