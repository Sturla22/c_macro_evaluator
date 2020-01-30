import pytest

import c_macro_evaluator.c_macro_evaluator as dut

macro_str = "#define TEST"
not_macro_str = "define TEST2"
multiline_macro = r"""#define MACRO 1+2\
        +4+5\
        *3
"""
recursive_macro = "#define RECURSIVE MACRO+1"
circular_macro = "#define CIRCULAR CIRCULAR*2"
conditional_macro = r"""
#define COND1
#ifdef COND1
#define COND2 0O1
#if COND2
#define COND3 0x0U
#if COND3
#define COND4 "Should not get here!"
#error
#endif // COND3
#endif // COND2
#endif // COND1
#undef COND1
#ifdef COND1
#define COND4 "Not here either!"
#error
#endif
#ifndef COND5
#ifndef COND3
#define TMP
#endif
#define COND5 0b1
#endif
#pragma some_pragma
"""


error = "#error"
error_msg = '#error "hey, don\'t go here!"'

not_a_macro = r"""
main() {
    printf("hello, world!\n");
}
"""


def test_macro_regex():
    assert dut.MacroEvaluator.MACRO_REGEX.match(macro_str)
    assert not dut.MacroEvaluator.MACRO_REGEX.match(not_macro_str)


def test_symbol_finding():
    e = dut.MacroEvaluator([macro_str, *multiline_macro.split("\n"), not_macro_str])
    assert "TEST" in e.symbols.keys()
    assert "TEST2" not in e.symbols.keys()
    assert "MACRO" in e.symbols.keys()
    assert "1+2+4+5*3" in e.symbols["MACRO"]
    assert len(e.symbols.keys()) == 2


def test_include_no_filename():
    with pytest.raises(UserWarning):
        dut.MacroEvaluator(["#include"])


def test_evaluate():
    e = dut.MacroEvaluator(
        [*multiline_macro.split("\n"), recursive_macro, circular_macro]
    )
    assert e.evaluate_macro("MACRO") == 22
    assert e.evaluate_macro("RECURSIVE") == 23


def test_errors():
    with pytest.raises(UserWarning):
        dut.MacroEvaluator([error])

    with pytest.raises(UserWarning):
        dut.MacroEvaluator([error_msg])


def test_conditional():
    e = dut.MacroEvaluator(conditional_macro.split("\n"))
    # COND1 gets removed by undef
    assert "COND1" not in e.symbols.keys()
    assert "COND2" in e.symbols.keys()
    assert "COND3" in e.symbols.keys()
    assert "COND4" not in e.symbols.keys()


def test_file():
    e = dut.MacroEvaluator(file_name="test/test_c_macro_evaluator.py")
    assert "COND2" in e.symbols.keys()


def test_include():
    e = dut.MacroEvaluator(
        r"""#include "test/test_c_macro_evaluator.py"
    """.split(
            "\n"
        )
    )
    assert "COND2" in e.symbols.keys()


def test_argparse():
    dut.parse_options(["-f", "file", "-m", "COND1", "-I", "."])
    dut.parse_options(["-r" "#define COND1 0x1", "-m", "COND1", "-I", "."])


def test_main():
    with pytest.raises(UserWarning):
        dut.main([])

    dut.main(["-f", "test/test_c_macro_evaluator.py", "-m", "COND2"])
    dut.main(["-r", "#define 1+2"])
