# Dynamic Dispatch

![Build status](https://img.shields.io/github/workflow/status/XevoInc/dynamic_dispatch/Push%20CI/master)
[![PyPI](https://img.shields.io/pypi/v/dynamic-dispatch)](https://pypi.org/project/dynamic-dispatch/)
![PyPI - License](https://img.shields.io/pypi/l/dynamic-dispatch)

A lightweight, dynamic dispatch implementation for classes and functions. This allows a class or function to delegate
its implementation conditioned on the value of its first argument. This is similar to `functools.singledispatch`,
however this library dispatches over value while the other dispatches over type.

## Install

You may install this via the [`dynamic-dispatch`](https://pypi.org/project/dynamic-dispatch/) package on [PyPi](https://pypi.org):

```bash
pip3 install dynamic-dispatch
```

## Usage


## Development

When developing, it is recommended to use Pipenv. To create your development environment:

```bash
pipenv install --dev
```

### Testing

This library uses the `unittest` framework. Tests may be run with the following:

```bash
python3 -m unittest
```