#!/bin/bash
row=1
TARGET="11111111111"

# While loop with condition using `!=`
while test $row != $TARGET
do
    echo $row
    row="1$row"
done
