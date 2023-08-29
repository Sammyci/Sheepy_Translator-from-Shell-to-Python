#!/bin/bash

file="example.txt"
if test -e $file
then
    echo "$file exists"
else
    echo "$file does not exist"
fi
