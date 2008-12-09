# Makefile for mlox project

.PHONY: all stats update-version mlox-dist data-dist test-dist

README    := mlox/mlox_readme.txt
VERSION   := $(shell cat VERSION)
MLOXARC   := mlox-$(VERSION).7z
ARCDATE   := $(shell date "+%Y-%m-%d")
RELDATE   := $(shell date "+%Y-%m-%d %T")
DATAARC   := mlox-data_$(ARCDATE).7z

all: mlox-dist data-dist test-dist

mlox-dist: dist/$(MLOXARC)

update-version:
	@echo "Updating mlox with latest Version number: $(VERSION)"
	@perl -p -i -e "s/^Version: (?:\d+\.\d+)/Version: $(VERSION)/" mlox/mlox_readme.txt
	@perl -p -i -e "s/^Version = \"(?:\d+\.\d+)\"/Version = \"$(VERSION)\"/" mlox/mlox.py

dist/$(MLOXARC): dist/mlox
	@rsync -uvaC mlox/ dist/mlox/ > /dev/null 2>&1
	@cp License.txt dist/mlox
	@echo "Adding DOS line endings to .bat and .txt files in staging directory"
	@for i in dist/mlox/*.bat dist/mlox/*.txt ; do perl -p -i -e "s/\015?$$/\015/" $$i ; done
	@echo "Creating distibution archive for mlox: $@"
	@(cd dist && 7z a $(MLOXARC) mlox) > /dev/null 2>&1

data-dist: dist dist/$(DATAARC) stats

dist/$(DATAARC): data/mlox_base.txt
	@echo "Updating Release date in: $<"
	@perl -p -i -e "s/^# Release Date: .*/# Release Date: $(RELDATE)/" $<
	@echo "Creating distibution archive for mlox rule-base: $@"
	@(cd data ; 7z a ../$@ $(<F)) > /dev/null 2>&1

dist/mlox:
	@echo "Creating $@"
	@mkdir -p $@

stats:
	@echo "Rule-base stats ($(RELDATE))"
	@grep '^\[' data/mlox_base.txt |wc -l|xargs echo "rules:		"
	@grep '^[^\[ #]' data/mlox_base.txt|sed 's/ [ ]*#.*//'|sort|uniq|wc -l|xargs echo "plugins:	"
	@grep '^# @' data/mlox_base.txt |wc -l|xargs echo "sections:	"

