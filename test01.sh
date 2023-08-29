#!/bin/bash

directory="/tmp"
if test -d $directory
then
    echo "$directory is a directory"
else
    echo "$directory is not a directory"
fi
