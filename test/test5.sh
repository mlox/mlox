#!/bin/bash

PROG=`cat .prog`
TEST=test5

echo ; echo "$TEST - various"
if ! mkdir $TEST.tmp ; then
    echo "Error creating test dir: $TEST.tmp"
    exit 1
fi
cp mlox.msg $TEST.tmp
cd $TEST.tmp
echo "$TEST Setup"
for f in ../$TEST.data/*.es[mp] ; do
    f2="${f##*/}"
    touch -r "$f" "$f2"
done
cp ../$TEST.data/*.txt .
echo "$TEST Running $PROG ..."
$PROG -u > mlox.out
if [ $? -ne 0 ] ; then echo "FAILED $TEST: Program Error" ; exit 1 ; fi
echo "$TEST Finished"

echo "$TEST checking correct output"
if diff out0.txt mlox.out ; then
    echo "PASSED $TEST"
    exit 0
else
    echo "FAILED $TEST, expected output does not match new output"
    exit 1
fi
