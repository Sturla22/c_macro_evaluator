import argparse
import re
import sys
from typing import Dict, List


class MacroEvaluator:
    """."""

    MACRO_REGEX = re.compile(r"^\s*#\s*(\w+)\s*(\w*)\s*([^\\|^\n]*)(\\*)$")
    MULTILINE_REGEX = re.compile(r"^\s*([^\\|^\n]*)(\\*)$")
    LITERAL_SUFFIX_REGEX = re.compile(r"((?:0[xXoO])?\d*)([uUlL]+)")
    INCLUDE_REGEX = re.compile(r"[\"<](.*)[\">]")

    def __init__(self, lines: List[str] = [], file_name: str = ""):
        if lines:
            self.lines = lines
        elif file_name:
            self.lines = self.read_lines(file_name)
        self.symbols: Dict[str, str] = {}
        self.inactive_level = 0
        self.parse_lines()

    def read_lines(self, file_name: str) -> List[str]:
        lines: List[str]
        with open(file_name, "r") as f:
            lines = f.readlines()
        return lines

    def handle_multiline(self, line, parsed_lines) -> bool:
        m = self.MULTILINE_REGEX.match(line)
        multiline = True
        if m:
            line_groups = m.groups()
            # Append to the line that was just parsed.
            parsed_lines[-1][-2] += line_groups[0].strip()
            multiline = bool(line_groups[1])
        return multiline

    def handle_inactive(self, line, command):
        if command == "error":
            if line[2]:
                raise UserWarning(line[2])
            else:
                raise UserWarning("Error directive hit")
        elif command == "include":
            # TODO(stla): Detect circular dependency.
            if line[2]:
                file_name = self.INCLUDE_REGEX.sub(r"\1", line[2])
                e = MacroEvaluator(file_name=file_name)
                self.symbols.update(e.symbols)
            else:
                raise UserWarning("Include without filename")

    def handle_directives(self, line):
        command = line[0].lower()
        if line[1]:
            symbol = line[1]
            if command == "ifdef":
                if symbol not in self.symbols or self.inactive_level:
                    self.inactive_level += 1
            elif command == "ifndef":
                if symbol in self.symbols:
                    self.inactive_level += 1
            elif command == "if":
                if not self.evaluate_macro(symbol):
                    self.inactive_level += 1
            elif not self.inactive_level:
                if command == "pragma":
                    print(f"pragma {symbol}")
                elif command == "undef":
                    del self.symbols[symbol]
                elif command == "define":
                    if line[2]:
                        self.symbols[symbol] = line[2]
                    else:
                        self.symbols[symbol] = None
        elif not self.inactive_level:
            self.handle_inactive(line, command)
        elif command == "endif":
            self.inactive_level -= 1

    def parse_lines(self) -> List[List[str]]:
        parsed_lines: List[List[str]] = []
        multiline = False
        # TODO(stla): Detect unmatched if statements.
        self.inactive_level = 0
        for line in self.lines:
            if multiline:
                multiline = self.handle_multiline(line, parsed_lines)
            m = self.MACRO_REGEX.match(line)
            if m:
                line_groups = list(m.groups())
                if len(line_groups) > 3 and line_groups[3]:
                    multiline = True
                parsed_lines.append(line_groups)
        for parsed_line in parsed_lines:
            self.handle_directives(parsed_line)

        return parsed_lines

    def evaluate_macro(self, macro_name):
        """Evaluate the parsed macros."""
        # TODO(stla): Handle ctypes and casts.
        macro = self.symbols[macro_name]
        for symbol in self.symbols.keys():
            # TODO(stla): Detect circular dependency.
            if symbol in macro:
                result = self.evaluate_macro(symbol)
                macro = macro.replace(symbol, str(result))
            macro = self.LITERAL_SUFFIX_REGEX.sub(r"\1", macro)
        return eval(macro)


def parse_options(args):
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-f", "--file", help="A C/C++ file to evaluate with preprocessor."
    )
    group.add_argument("-r", "--raw", help="Define a macro to evaluate directly.")

    parser.add_argument("-m", "--macro", help="The macro to be evaluated.")
    parser.add_argument(
        "-I",
        "--include_path",
        action="append",
        dest="include_paths",
        help="Include path, works like gcc's -I",
    )
    options = parser.parse_args(args)
    if options.file is None and options.raw is None:
        parser.print_help()

    return options


def main(args):
    """
    main function defined to allow for testing and calling the entire functionality
    as a python module.
    """
    options = parse_options(args)

    if options.file:
        e = MacroEvaluator(file_name=options.file)
    elif options.raw:
        e = MacroEvaluator(lines=options.raw.split("\n"))
    else:
        raise UserWarning()

    if options.macro:
        result = e.evaluate_macro(options.macro)
        print(result)


if __name__ == "__main__":
    main(sys.argv)
