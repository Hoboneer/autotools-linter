#!/usr/bin/env python3
# A program to lint autotools projects

import argparse
import os

PROGRAM_NAME = "atlint"


def warn_file(filename, message):
    print(f"{filename}: {message}")


def warn_general(message):
    print(f"{PROGRAM_NAME}: {message}")


def warn_position(filename, line, column, message):
    print(f"{filename}:{line}:{column}: {message}")


class Macro:
    #     def __init__(self, name, toplevel=True, args=None):
    #         self.name = name
    #         self.is_toplevel = toplevel
    #         self.args = args or []
    def __init__(self, name):
        self.name = name
        self.raw_args = []

    def __repr__(self):
        if self.raw_args:
            suffix = f"({','.join(self.raw_args)})"
        else:
            suffix = ""
        return f"<Macro {self.name}{suffix}>"


def parse_configure_file(filename):
    with open(filename, "r") as f:
        file_buffer = f.readlines()

    macro_calls = parse_macro_call(file_buffer, (0, 0))
    import re
    VALID_MACRO_PREFIXES = re.compile('^(AC_|AS_|AM_|_)')
    # Remove "invalid" macros
    valid_macro_calls = [macro for macro in macro_calls if VALID_MACRO_PREFIXES.match(macro.name)]
    for macro in valid_macro_calls:
        print(macro)


#         for line_no, line in enumerate(f):
#             for col_no, char in enumerate(line):
#                 if char in VALID_MACRO_CHARS:
#                     macro_name_buffer.append(char)
#                 elif char in '(':
#                     _parse_macro_args
#                 else:
#                     if

# Only does the bare minimum of work to allow the caller to decide how much to parse
# def parse_macro_call(line_buffer, origin):
#     import string
#
#     VALID_MACRO_CHARS = set(string.ascii_uppercase)
#
#     macro_name_buffer = []
#     arg_chars_buffer = []
#     paren_stack = []
#     quote_stack = []
#
#     CALL_MODE = 0
#     ARGS_MODE = 1
#     parse_mode = CALL_MODE
#     for line_no, line in enumerate(line_buffer):
#         for col_no, char in enumerate(line):
#             if parse_mode == CALL_MODE:
#                 if char in VALID_MACRO_CHARS:
#                     macro_name_buffer.append(char)
#                 elif char in "(":
#                     # Now, parse the arguments.
#                     paren_stack.append('(')
#                     macro = Macro("".join(macro_name_buffer))
#                     parse_mode = ARGS_MODE
#                 # NOT a valid macro name char
#                 elif macro_name_buffer:
#                     # Empty macro call
#                     macro = Macro("".join(macro_name_buffer))
#                     break
#                 else:
#                     # This shouldn't have been reached
#                     raise RuntimeError("Invalid macro call text (TODO)")
#             elif parse_mode == ARGS_MODE:
#                 # Next argument if comma is not protected by quote
#                 if char == ',' and not quote_stack:
#                     position = (origin[0] + line_no, origin[1] + col_no)
#                     macro.raw_args.append(''.join(arg_chars_buffer))
#                     arg_chars_buffer.clear()
#                 # Complete macro call
#                 elif char == ')' and len(paren_stack) == 0 and paren_stack[0] == '(':
#                     paren_stack.append(char)
#                     macro.raw_args.append(''.join(arg_chars_buffer))
#                     arg_chars_buffer.clear()
#                 elif char == '(':
#                     paren_stack.append(char)
#                 elif char == ')':
#                     if not paren_stack:


def parse_macro_call(line_buffer, origin):
    import string

    VALID_MACRO_CHARS = set(string.ascii_uppercase)
    VALID_MACRO_CHARS.add("_")

    macros = []
    macro_name_buffer = []
    for line_no, line in enumerate(line_buffer):
        # Ignore line comments
        if line.startswith("#") or line.startswith("dnl"):
            continue
        for col_no, char in enumerate(line):
            if char in VALID_MACRO_CHARS:
                macro_name_buffer.append(char)
            elif char in "(":
                # Now, parse the arguments.
                macro = Macro("".join(macro_name_buffer))
                macro_name_buffer.clear()

                position = (origin[0] + line_no, origin[1] + col_no)
                # Prevent the open paren from going into args
                # sub_line_buffer = line_buffer[position[0]][position[1]+1:]
                sub_line_buffer = list(line_buffer[position[0]][position[1] + 1 :])
                # Rest of the lines
                sub_line_buffer.extend(line_buffer[position[0] + 1:])
                parse_macro_args(macro, sub_line_buffer, position)
                macros.append(macro)
            # NOT a valid macro name char and NOT a valid M4 identifier
            elif macro_name_buffer:
                if char not in string.ascii_lowercase:
                    # Empty macro call
                    macro = Macro("".join(macro_name_buffer))
                    macros.append(macro)
                    macro_name_buffer.clear()
                    break
                else:
                    # Not a macro call
                    macro_name_buffer.clear()
            # Not parsing a macro call yet
            elif not macro_name_buffer:
                continue
            else:
                # This shouldn't have been reached
                raise RuntimeError("Invalid macro call text (TODO)")
    return macros


def parse_macro_args(macro, line_buffer, origin):
    quote_stack = []
    # Starts from an open macro call
    paren_stack = ["("]
    arg_chars_buffer = []

    no_more_args = False
    quote_level = 0
    for line_no, line in enumerate(line_buffer):
        # Exit if no more arguments
        if no_more_args:
            break
        for col_no, char in enumerate(line):
            if char == "[":
                quote_level += 1
                arg_chars_buffer.append(char)
                continue
            elif char == "]":
                quote_level -= 1
                arg_chars_buffer.append(char)
                continue

            if char == "(":
                # Balanced parens only matter when outside of quotes
                if quote_level == 0:
                    paren_stack.append(char)
                arg_chars_buffer.append(char)
            elif char == ")":
                # Only deal with balanced parens outside of quotes
                # Empty stack means unbalanced parens
                if quote_level == 0 and not paren_stack:
                    raise NotImplementedError("TODO: Handle unbalanced parens")
                other_paren = paren_stack.pop()
                # Non-matching pair
                if other_paren != "(":
                    raise NotImplementedError("TODO: Handle unmatched parens")
                # Macro call finished
                if len(paren_stack) == 0:
                    macro.raw_args.append("".join(arg_chars_buffer))
                    no_more_args = True
                    break
                else:
                    # Continue adding chars to buffer
                    arg_chars_buffer.append(char)

            # Next argument if comma is not protected by quote or inside inner parens
            elif quote_level == 0 and len(paren_stack) == 1 and char == ",":
                macro.raw_args.append("".join(arg_chars_buffer))
                arg_chars_buffer.clear()
            else:
                arg_chars_buffer.append(char)

    if paren_stack:
        raise NotImplementedError("TODO: Handle unfinished macro call args")


# def _parse_macro_args(


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
    # Makefile.am checks
    # configure.ac + Makefile.am checks (cross-file knowledge)


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
