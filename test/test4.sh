#!/bin/bash

PROG=`cat .prog`
TEST=test4

echo ; echo "$TEST - check load order"
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
cp ../$TEST.data/lo0 .		# expected load order
echo "$TEST Running $PROG ..."
$PROG -u > mlox.out
if [ $? -ne 0 ] ; then echo "FAILED $TEST: Program Error" ; exit 1 ; fi
echo "$TEST Finished"
../lo > lo1			# new load order

echo "$TEST checking correct load order"
if diff lo0 lo1 ; then
    echo "PASSED $TEST"
    exit 0
else
    echo "FAILED $TEST, expected load order (lo0) does not match new load order (lo1)"
    exit 1
fi
