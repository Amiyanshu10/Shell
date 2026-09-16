import re


def update_param_case_ids(content, param_mapping):
    """
    param_mapping example:
    {
        0: "C3256611",
        1: "C3256612",
        ...
    }

    TestParamID is treated as the zero-based position of an
    initializer entry inside an array.
    """

    # Generic array declaration:
    # anything like:
    #
    #   some_type some_name[] = {
    #
    # We do NOT care about the type or variable name.
    array_pattern = re.compile(
        r'^[ \t]*[\w:<>,\s*&]+\s+\w+\s*\[\s*\]\s*=\s*\{',
        re.MULTILINE
    )

    for array_match in array_pattern.finditer(content):

        array_start = array_match.end()

        # ---------------------------------------------------------
        # Find matching closing brace of this array.
        # ---------------------------------------------------------
        depth = 1
        i = array_start

        while i < len(content) and depth > 0:

            # Skip // comments
            if content.startswith("//", i):
                newline = content.find("\n", i)

                if newline == -1:
                    i = len(content)
                    break

                i = newline + 1
                continue

            # Skip /* ... */ comments
            if content.startswith("/*", i):
                comment_end = content.find("*/", i + 2)

                if comment_end == -1:
                    break

                i = comment_end + 2
                continue

            if content[i] == "{":
                depth += 1

            elif content[i] == "}":
                depth -= 1

                if depth == 0:
                    array_end = i
                    break

            i += 1

        else:
            continue

        block = content[array_start:array_end]

        # ---------------------------------------------------------
        # Find top-level {...} entries inside this array.
        #
        # Example:
        #
        # {
        #     {HP3PAR_SED, ..., 1, 0},
        #     /* description */ /*C123*/
        #
        #     {HP3PAR_FIPS, ..., 1, 0},
        #     /* description */ /*C456*/
        # }
        #
        # ---------------------------------------------------------

        entries = []

        depth = 0
        entry_start = None
        i = 0

        while i < len(block):

            # Skip comments while looking for initializer braces
            if block.startswith("//", i):
                newline = block.find("\n", i)

                if newline == -1:
                    break

                i = newline + 1
                continue

            if block.startswith("/*", i):
                comment_end = block.find("*/", i + 2)

                if comment_end == -1:
                    break

                i = comment_end + 2
                continue

            if block[i] == "{":

                if depth == 0:
                    entry_start = i

                depth += 1

            elif block[i] == "}":

                if depth > 0:
                    depth -= 1

                    if depth == 0 and entry_start is not None:

                        # initializer itself ends here
                        initializer_end = i + 1

                        # Include text after initializer up until
                        # the beginning of the next initializer.
                        entries.append(
                            [entry_start, initializer_end]
                        )

                        entry_start = None

            i += 1

        if not entries:
            continue

        # ---------------------------------------------------------
        # Extend every entry to the beginning of the next entry.
        #
        # This includes:
        #
        # /*HP3PAR...*/ /*C3256386*/
        #
        # belonging to that parameter.
        # ---------------------------------------------------------

        full_entries = []

        for index, entry in enumerate(entries):

            start = entry[0]

            if index + 1 < len(entries):
                end = entries[index + 1][0]
            else:
                end = len(block)

            full_entries.append((start, end))

        # Check whether this looks like the correct array.
        # We want an array having enough entries for the Excel IDs.
        if not param_mapping:
            continue

        max_param_id = max(param_mapping.keys())

        if max_param_id >= len(full_entries):
            continue

        print(
            f"Found candidate parameter array "
            f"with {len(full_entries)} entries"
        )

        # ---------------------------------------------------------
        # Replace backwards so offsets don't change.
        # ---------------------------------------------------------

        for param_id in sorted(param_mapping.keys(), reverse=True):

            case_id = param_mapping[param_id]

            start, end = full_entries[param_id]

            entry_text = block[start:end]

            # Find TestRail Case ID comment such as:
            #
            # /*C3256386*/
            #
            case_pattern = re.compile(
                r'/\*\s*C\d+\s*\*/'
            )

            matches = list(case_pattern.finditer(entry_text))

            if not matches:
                print(
                    f"[WARNING] No existing CaseID found for "
                    f"TestParamID {param_id}"
                )
                continue

            # Normally the Case ID is the last /*Cxxxx*/ in the entry.
            case_match = matches[-1]

            new_entry = (
                entry_text[:case_match.start()]
                + f"/*{case_id}*/"
                + entry_text[case_match.end():]
            )

            block = (
                block[:start]
                + new_entry
                + block[end:]
            )

            print(
                f"  TestParamID {param_id} -> {case_id}"
            )

        # Put modified array back into complete source
        content = (
            content[:array_start]
            + block
            + content[array_end:]
        )

        # We found and processed the matching parameter array.
        return content

    print("[WARNING] No suitable parameter array found.")
    return content
