"""
Build the C cycle finder extension.

Usage:
    python build_cycle_finder.py

Produces _cycle_finder.cpython-*.so in the current directory.
"""
from setuptools import setup, Extension
import sys

ext = Extension(
    "_cycle_finder",
    sources=["_cycle_finder.c"],
    extra_compile_args=["-O3", "-Wall"] if sys.platform != "win32" else ["/O2"],
)

setup(
    name="cycle_finder",
    ext_modules=[ext],
    script_args=["build_ext", "--inplace"],
)
