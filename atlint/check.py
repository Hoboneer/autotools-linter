# Checking api
import re

def warn_file(filename, message):
    print(f"{filename}: {message}")


def warn_position(filename, line, column, message):
    print(f"{filename}:{line}:{column}: {message}")


def unquote(s):
    return s.lstrip("[").rstrip("]")

class Warn:
    def __init__(self):
        pass


def check_macro_arg(macro, arg_index, ctx):
    try:
        arg = macro.args[arg_index]
    except IndexError:
        line, col = macro.position
        msg = f"Missing argument {arg_index + 1}."
        warn_position(ctx["configure_file"], line, col, msg)
        return False
    return True

# Warns about missing args as well
def get_macro_arg(macro, arg_index, ctx):
    if not check_macro_arg(macro, arg_index, ctx):
        return None
    return macro.args[arg_index]

def checker(targets_re):
    def decorator(func):
        func.targets_re = re.compile('|'.join(targets_re))
        return func
    return decorator
