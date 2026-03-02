#!/bin/bash

# ---- DEFINE DIRECTORIES HERE ----
DIRECTORIES=(
    "/path/to/project1"
    "/path/to/project2"
    "/path/to/project3"
)

# ---- LOOP THROUGH DIRECTORIES ----
for TARGET_DIR in "${DIRECTORIES[@]}"
do
    echo "---------------------------------------------"
    echo "Processing directory: $TARGET_DIR"

    # Check if directory exists
    if [ ! -d "$TARGET_DIR" ]; then
        echo "Directory not found: $TARGET_DIR"
        continue
    fi

    cd "$TARGET_DIR" || continue

    LOG_FILE="build_$(basename "$TARGET_DIR").log"

    echo "Log file: $LOG_FILE"

    # Run make clean and make
    make clean > "$LOG_FILE" 2>&1
    make >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        echo "Build successful for $TARGET_DIR"
    else
        echo "Build failed for $TARGET_DIR (Check $LOG_FILE)"
    fi

    # Remove nvmetst if exists
    if [ -f "./nvmetst" ]; then
        echo "Removing nvmetst..."
        rm -f ./nvmetst
    fi

    # Remove object files if exist
    if ls *.o 1> /dev/null 2>&1; then
        echo "Removing object files..."
        rm -f *.o
    fi

    echo "Finished processing $TARGET_DIR"
done

echo "============================================="
echo "All directories processed."
