#!/bin/bash

grep '^;; @' mlox_base.txt |wc -l|xargs echo "sections:	"
egrep -i '^\[(order|nearstart|nearend|note|conflict|patch|requires)( |\])' mlox_base.txt |wc -l|xargs echo "rules:		"
