from pathlib import Path
import re

ROOT_DIR = Path(
    "FunctionTest/CommonTP/nvme/Customization/Dell/Dell_Common"
)

# Captures whatever object/variable name is being used.
PATTERN = re.compile(
    r"\bPowRelay\s*&\s*([A-Za-z_]\w*)\s*=\s*pow_relay\s*\(\s*\)\s*;"
)


def update_power_relay(root_dir, dry_run=True):
    modified_files = 0
    total_replacements = 0

    for cpp_file in root_dir.rglob("*.cpp"):
        content = cpp_file.read_text(encoding="utf-8")

        # \1 = original object name
        new_content, count = PATTERN.subn(
            r"PowerSupplyControllable &\1 = power_supply_controller();",
            content
        )

        if count == 0:
            continue

        print(f"\n{'[WOULD UPDATE]' if dry_run else '[UPDATED]'} {cpp_file}")
        print(f"  Replacements: {count}")

        if not dry_run:
            cpp_file.write_text(new_content, encoding="utf-8")

        modified_files += 1
        total_replacements += count

    print("\n========== SUMMARY ==========")
    print(f"Files found       : {modified_files}")
    print(f"Total replacements: {total_replacements}")
    print(f"Dry run           : {dry_run}")
    print("=============================")


if __name__ == "__main__":
    # First run safely without modifying anything
    update_power_relay(ROOT_DIR, dry_run=True)

    # After checking the output, change to:
    # update_power_relay(ROOT_DIR, dry_run=False)
