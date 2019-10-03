import re
import string


class Macro:
    #     def __init__(self, name, toplevel=True, args=None):
    #         self.name = name
    #         self.is_toplevel = toplevel
    #         self.args = args or []
    def __init__(self, name, position):
        self.name = name
        # Line and column (Zero-indexed for now, TODO)
        line_index, column_index = position
        # The first char of a file is at (1, 1)--according to vim at least
        self.position = (line_index + 1, column_index + 1)
        self.raw_args = []
        # Whitespace cleaned up
        self.args = []

    def _clean_args(self):
        # Strip leading whitespace of all args
        for raw_arg in self.raw_args:
            self.args.append(raw_arg.lstrip())

    def __repr__(self):
        if self.args:
            suffix = f"({','.join(self.args)})"
        else:
            suffix = ""
        return f"<Macro {self.name}{suffix} at {self.position}>"


def parse_configure_file(filename):
    with open(filename, "r") as f:
        file_buffer = f.readlines()

    macro_calls = parse_macro_call(file_buffer, (0, 0))

    VALID_MACRO_PREFIXES = re.compile("^(AC_|AS_|AM_|_)")
    # Remove "invalid" macros
    valid_macro_calls = [
        macro for macro in macro_calls if VALID_MACRO_PREFIXES.match(macro.name)
    ]
    return valid_macro_calls


def parse_macro_call(line_buffer, origin):
    VALID_MACRO_CHARS = set(string.ascii_uppercase)
    VALID_MACRO_CHARS.add("_")

    macros = []
    macro_call_start_pos = None
    macro_name_buffer = []
    for line_no, line in enumerate(line_buffer):
        # Ignore line comments
        if line.startswith("#") or line.startswith("dnl"):
            continue
        for col_no, char in enumerate(line):
            if char in VALID_MACRO_CHARS:
                # The first character of the macro is its origin
                if not macro_name_buffer:
                    macro_call_start_pos = (origin[0] + line_no, origin[1] + col_no)
                macro_name_buffer.append(char)
            elif char in "(":
                # Now, parse the arguments.
                assert macro_call_start_pos is not None
                macro = Macro("".join(macro_name_buffer), macro_call_start_pos)

                # Reset for next macro.
                macro_call_start_pos = None
                macro_name_buffer.clear()

                position = (origin[0] + line_no, origin[1] + col_no)
                # Prevent the open paren from going into args
                # sub_line_buffer = line_buffer[position[0]][position[1]+1:]
                sub_line_buffer = list(line_buffer[position[0]][position[1] + 1 :])
                # Rest of the lines
                sub_line_buffer.extend(line_buffer[position[0] + 1 :])
                parse_macro_args(macro, sub_line_buffer, position)
                macros.append(macro)
            # NOT a valid macro name char and NOT a valid M4 identifier
            elif macro_name_buffer:
                if char not in string.ascii_lowercase:
                    # Empty macro call
                    assert macro_call_start_pos is not None
                    macro = Macro("".join(macro_name_buffer), macro_call_start_pos)

                    # Reset for next macro.
                    macro_call_start_pos = None
                    macro_name_buffer.clear()

                    macros.append(macro)
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
                # Ignore parens inside quotes
                elif quote_level > 0:
                    arg_chars_buffer.append(char)
                    continue

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

    macro._clean_args()
