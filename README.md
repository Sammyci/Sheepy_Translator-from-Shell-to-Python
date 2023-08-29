# Sheepy_Translator-from-Shell-to-Python
Translator from Shell to Python
Your task in this assignment is to write a POSIX Shell Transpiler.
Generally, compilers take a high-level language as input and output assembler, which can then can be directly executed.
A Transpiler (or Source-to-Source Compiler) takes a high-level language as input and outputs a different high-level language.
Your transpiler will take Shell scripts as input and output Python.
Such a translation is useful because programmers sometimes convert Shell scripts to Python.
Most commonly this is done because extra functionality is needed, e.g. a GUI.
And this functionality is much easier to implement in Python.
Your task in this assignment is to automate this conversion.
You must write a Python program that takes as input a Shell script and outputs an equivalent Python program.

The translation of some POSIX Shell code to Python is straightforward.
The translation of other Shell code is difficult or infeasible.
So your program will not be able to translate all Shell code to Python.
But a tool that performs only a partial translation of shell to Python could still be very useful.

You should assume the Python code output by your program will be subsequently read and modified by humans.
In other words, you have to output readable Python code.
For example, you should aim to preserve variable names and comments.
