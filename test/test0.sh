#!/bin/bash

PROG=`cat .prog`
TEST=test0

echo ; echo "$TEST - no input files"
if ! mkdir $TEST.tmp ; then
    echo "Error creating test dir: test0.tmp"
    exit 1
fi
cp mlox.msg $TEST.tmp
cd $TEST.tmp
echo "$TEST Setup"
#cp ../$TEST.data/*.txt .
echo "$TEST Running $PROG ... (CTRL-C to interrupt if hung)"
$PROG -u > mlox.out
echo "PASSED $TEST"
