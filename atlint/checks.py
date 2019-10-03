import re

from .check import get_macro_arg, warn_position, checker

CHECKERS = []
def _public_checker(checker):
    CHECKERS.append(checker)

@_public_checker
@checker(['.*'])
def trailing_whitespace(macros, ctx):
    for macro in macros:
        for i, arg in enumerate(macro.args, start=1):
            if arg.rstrip() != arg:
                line, col = macro.position
                msg = f"Argument {i} has trailing whitespace. Trailing whitespace is preserved in M4."
                warn_position(ctx["configure_file"], line, col, msg)


@_public_checker
@checker(['.*'])
def unquoted_args(macros, ctx):
    quoted_arg_re = re.compile(r"\[.*\]", flags=re.MULTILINE)
    for macro in macros:
        for i, arg in enumerate(macro.args, start=1):
            # `rstrip` so that more macros with trailing whitespace but
            # incorrect quoting are warned about
            if not quoted_arg_re.match(arg.rstrip()):
                line, col = macro.position
                msg = f"Argument {i} is unquoted. Consider quoting to prevent errors."
                warn_position(ctx["configure_file"], line, col, msg)


@_public_checker
@checker([r'^AC_CONFIG_AUX_DIR$'])
def bad_aux_dir(macros, ctx):
    # There should only be one macro here
    for macro in macros:
        line, col = macro.position
        # try:
        #     first = macro.args[0]
        # except IndexError: #     msg = "Missing first argument."
        #     warn_position(ctx["configure_file"], line, col, msg)
        #     continue
        arg = get_macro_arg(macro, 0, ctx)
        if not arg:
            continue

        if unquote(arg) != "build-aux":
            msg = "Argument 1 should be [build-aux]."
            warn_position(ctx["configure_file"], line, col, msg)

@_public_checker
@checker([r'^AC_CONFIG_MACRO_DIR$'])
def bad_macro_dir(macros, ctx):
    # There should only be one macro here
    for macro in macros:
        line, col = macro.position
        # try:
        #     first = macro.args[0]
        # except IndexError:
        #     msg = "Missing first argument. Requires at least 1 argument."
        #     warn_position(ctx["configure_file"], line, col, msg)
        #     continue
        arg = get_macro_arg(macro, 0, ctx)
        if not arg:
            continue

        if unquote(arg) != "m4":
            msg = "Argument 1 should be [m4]."
            warn_position(ctx["configure_file"], line, col, msg)
