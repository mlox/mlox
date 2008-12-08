#!/bin/bash

PROG="`cat .prog` -u"
TEST=testc
N=100

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
echo "$TEST Running $PROG $N times ..."

for i in 0 1 2 3 4 ; do
    dots=""
    for j in 0 1 2 3 4 5 6 7 8 9 ; do
	for k in 0 1 2 3 4 5 6 7 8 9 ; do
	    if [ "$k" = "0" ] ; then echo -n "$dots${j}0" ; fi
	    ../scrambledates
	    $PROG > mlox.out
	    if [ $? -ne 0 ] ; then echo "FAILED $TEST: Program Error" ; exit 1 ; fi
	    ../lo > lo1
	    if ! diff lo0 lo1 ; then
		echo "FAILED $TEST, expected load order (lo0) does not match new load order (mlox_loadorder.out)"
		exit 1
	    fi
	    N=$(( $N - 1 ))
	    if [ "$N" = "0" ] ; then
		echo "..100"
		echo "PASSED $TEST"
		exit 0
	    fi
	done
	dots=".."
    done
    echo "..100"
done
echo "PASSED $TEST"
