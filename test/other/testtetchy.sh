#!/bin/bash

PROG=`cat .prog`
TEST=testtetchy

echo ; echo "$TEST - tetchy"
if ! mkdir $TEST.tmp ; then
    echo "Error creating test dir: $TEST.tmp"
    exit 1
fi
cd $TEST.tmp
echo "$TEST Setup"
for f in ../$TEST.data/*.es[mp] ; do
    f2="${f##*/}"
    touch -r "$f" "$f2"
done
cp ../$TEST.data/*.txt .
cp ../$TEST.data/*.out .
echo "$TEST Running $PROG ..."
$PROG > mlox.out
if [ $? -ne 0 ] ; then echo "FAILED $TEST: Program Error" ; exit 1 ; fi
echo "$TEST Finished"

echo "$TEST checking correct output"
if diff load_order.out mlox_loadorder.out ; then
    echo "PASSED $TEST"
    exit 0
else
    echo "FAILED $TEST, expected output does not match new output"
    exit 1
fi
