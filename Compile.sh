#!/bin/bash

# Get absolute path of the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Define your project directories here
DIRECTORIES=(
    "/path/to/project1"
    "/path/to/project2"
    "/path/to/project3"
)

for TARGET_DIR in "${DIRECTORIES[@]}"
do
    echo "-----------------------------------------"
    echo "Processing: $TARGET_DIR"

    # Check directory exists
    if [ ! -d "$TARGET_DIR" ]; then
        echo "Directory not found: $TARGET_DIR"
        continue
    fi

    # Log file stored in script directory
    LOG_FILE="$SCRIPT_DIR/$(basename "$TARGET_DIR")_build.log"

    echo "Saving log to: $LOG_FILE"

    # Run build
    make -C "$TARGET_DIR" clean > "$LOG_FILE" 2>&1
    make -C "$TARGET_DIR" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "Build successful for $TARGET_DIR"
    else
        echo "Build failed for $TARGET_DIR (Check log)"
    fi

    # Remove nvmetst if exists
    if [ -f "$TARGET_DIR/nvmetst" ]; then
        rm -f "$TARGET_DIR/nvmetst"
        echo "Removed nvmetst"
    fi

    # Remove object files
    rm -f "$TARGET_DIR"/*.o 2>/dev/null

    echo "Done with $TARGET_DIR"
done

echo "All builds completed."
