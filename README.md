# C Macro Evaluator

An evaluator for C Macros. Implements the C/C++ preprocessor and enables testing of macros.

## Usage

To evaluate a macro called `HELLO` defined in the header file `hello_world.h` or any of its dependencies in the folder `include`:

`c_macro_evaluator.py -f hello_world.h -I include -m HELLO`

## Development Setup
```sh
# Install dependencies
pipenv install --dev

# Setup pre-commit and pre-push hooks
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Credits
This package was created with Cookiecutter and the [sourceryai/python-best-practices-cookiecutter](https://github.com/sourceryai/python-best-practices-cookiecutter) project template.
