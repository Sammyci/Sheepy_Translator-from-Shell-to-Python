#!/bin/bash

file="example.txt"
if test -r $file
then
    echo "$file is readable"
else
    echo "$file is not readable"
fi
