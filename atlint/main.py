#!/usr/bin/env python3
# A program to lint autotools projects

import argparse
import os
import re
import string

from .parse import parse_configure_file
from .check import warn_file, warn_position
from .checks import CHECKERS

PROGRAM_NAME = "atlint"


def warn_general(message):
    print(f"{PROGRAM_NAME}: {message}")


def main(argv=None):
    parser = argparse.ArgumentParser("atlint", description="Autotools project linter")
    parser.add_argument("test", nargs="?")
    args = parser.parse_args(argv)

    # Project-wide checks (for file existence)
    # 'configure.ac' is a required file
    if os.path.exists("configure.ac"):
        configure_file = "configure.ac"
    elif os.path.exists("configure.in"):
        configure_file = "configure.in"
        warn_general(
            "Files named 'configure.in' are deprecated. Consider renaming to 'configure.ac'"
        )
    else:
        warn_general("Cannot find 'configure.ac' or 'configure.in'")
        # TODO: Use proper exit code
        return 1

    # configure.ac checks
    macro_calls = parse_configure_file(configure_file)
    context = {"configure_file": configure_file}
    # Checking arguments of macros
    for checker in CHECKERS:
        matching_macros = [
            macro for macro in macro_calls if checker.targets_re.match(macro.name)
        ]
        checker(matching_macros, context)

    # # Checking existence of macros
    # required_macro_calls = [
    #     ("AC_CONFIG_AUX_DIR", ["[build-aux]"]),
    #     ("AC_CONFIG_MACRO_DIR", ["[m4]"]),
    # ]
    # # Membership testing with sets is clearer (and usually faster) than nested for-loops.
    # present_calls = {macro.name for macro in macro_calls}
    # for exact_name, args in required_macro_calls:
    #     if exact_name not in present_calls:
    #         call_text = f"{exact_name}({', '.join(args)})"
    #         warn_file(configure_file, f"Call to {call_text} should be present.")

    # Check for whitespace between macro name and opening paren
    empty_macros = {macro for macro in macro_calls if not macro.args}
    with open(configure_file, "r") as f:
        file_buffer = f.readlines()

    for macro in empty_macros:
        line, col = macro.position
        line_index, col_index = line - 1, col - 1
        # End of macro name
        col_end_index = col_index + len(macro.name) - 1
        expected_open_paren_index = col_end_index + 1
        # Find first paren to the right of macro name
        cur_line = file_buffer[line_index]
        paren_index = cur_line.find("(", col_end_index)
        if paren_index != -1:
            # The line up to (excluding) the paren is only whitespace
            if set(cur_line[expected_open_paren_index:paren_index]) <= set(
                string.whitespace
            ):
                warn_position(
                    configure_file,
                    line,
                    col,
                    f"Whitespace before opening parenthesis for a macro call produces undesired behaviour. Use {macro.name}(args...) instead.",
                )

    # Makefile.am checks
    # configure.ac + Makefile.am checks (cross-file knowledge)


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
