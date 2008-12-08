#!/bin/bash

PROG="`cat .prog` -u"
TEST=testa

echo ; echo "$TEST - check HUGE load order (this may take some time)"
if ! mkdir $TEST.tmp ; then
    echo "Error creating test dir: $TEST.tmp"
    exit 1
fi
cp mlox.msg $TEST.tmp
cd $TEST.tmp
echo "$TEST Setup"

echo "# generated mlox_base.txt file" > mlox_base.txt
echo "[Order]" >> mlox_base.txt
echo "Morrowind.esm" >> mlox_base.txt
echo "plugin-00.esm" >> mlox_base.txt

# generate data files
prev=""
for i in 0 1 2 3 4 5 6 7 8 9 ; do
    echo >> mlox_base.txt
    echo "[Order]" >> mlox_base.txt
    if [ -n "$p" ] ; then echo $prev >> mlox_base.txt ; fi
    for j in 0 1 2 3 4 5 6 7 8 9 ; do
	p="plugin-$i$j.esm"
	touch $p
	echo $p >> mlox_base.txt
    done
    prev=$p
done
# generate data files
for i in 0 1 2 3 4 5 6 7 8 9 ; do
    for j in 0 1 2 3 4 5 6 7 8 9 ; do
	echo >> mlox_base.txt
	echo "[Order]" >> mlox_base.txt
	if [ -n "$p" ] ; then echo $prev >> mlox_base.txt ; fi
	for k in 0 1 2 3 4 5 6 7 8 9 ; do
	    for l in 1 2 3 4 5 6 7 8 9 0 ; do
		p="plugin-$i$j$k$l.esp"
		echo $p >> mlox_base.txt
	    done
	    touch $p
	done
	prev=$p
    done
done

cp ../$TEST.data/*.txt .
cp ../$TEST.data/*.es[mp] .
cp ../$TEST.data/lo0 .		# expected load order
echo "$TEST Running $PROG ..."
$PROG > mlox.out
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
