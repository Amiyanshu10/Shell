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
    .astype(str
