# Makefile for mlox project

.PHONY: all stats version mlox-dist data-dist test-dist upload upload-mlox upload-data upload-exe

README    := mlox/mlox_readme.txt
PROGRAM   := mlox/mlox.py
RULES     := data/mlox_base.txt
VERSION   := $(shell cat VERSION)
MLOXARC   := mlox-$(VERSION).7z
EXEARC    := mlox-exe-$(VERSION).7z
ARCDATE   := $(shell date --utc "+%Y-%m-%d")
RELDATE   := $(shell date --utc "+%Y-%m-%d %T (UTC)")
DATAARC   := mlox-data_$(ARCDATE).7z
UPLOAD    := googlecode_upload.py -u john.moonsugar -p mlox

all: mlox-dist data-dist test-dist

upload: upload-mlox upload-exe upload-data

upload-mlox:
	$(UPLOAD) -s "[mlox $(VERSION)] - requires Python25 and wxPython" dist/$(MLOXARC)

upload-data:
	$(UPLOAD) -s "[mlox-data $(RELDATE)] - install mlox_base.txt into your mlox directory" dist/$(DATAARC)

upload-exe:
	$(UPLOAD) -s "[mlox-exe $(VERSION)] - standalone executable for Windows" dist/$(EXEARC)

# update the version strings in mlox_readme.txt, mlox.py
version: $(README) $(PROGRAM)

$(README): VERSION
	@echo "Updating $@ with latest Version number: $(VERSION)"
	@perl -p -i -e "s/^Version: (?:\d+\.\d+)/Version: $(VERSION)/" $@

$(PROGRAM): VERSION
	@echo "Updating $@ with latest Version number: $(VERSION)"
	@perl -p -i -e "s/^Version = \"(?:\d+\.\d+)\"/Version = \"$(VERSION)\"/" $@

mlox-dist: dist/$(MLOXARC)

dist/$(MLOXARC): version dist/mlox $(wildcard mlox/*)
	@rsync -uvaC mlox/ dist/mlox/ > /dev/null 2>&1
	@cp License.txt dist/mlox
	@echo "Adding DOS line endings to .bat and .txt files in staging directory"
	@for i in dist/mlox/*.bat dist/mlox/*.txt ; do perl -p -i -e "s/\015?$$/\015/" $$i ; done
	@(cd dist && 7z a $(MLOXARC) mlox) > /dev/null 2>&1
	@echo "CREATED distibution archive for mlox: $@"

data-dist: dist dist/$(DATAARC) stats

dist/$(DATAARC): $(RULES)
	@echo "Updating $< with latest Version date: $(RELDATE)"
	@perl -p -i -e "s/^\[Version\s+[^\]]+\]/[Version $(RELDATE)]/" $<
	@(cd data ; 7z a ../$@ $(<F)) > /dev/null 2>&1
	@echo "CREATED distibution archive for mlox rule-base: $@"

dist/mlox:
	@echo "Creating $@"
	@mkdir -p $@

stats:
	@echo "Rule-base stats ($(RELDATE))"
	@grep '^;; @' data/mlox_base.txt |wc -l|xargs echo "sections:	"
	@egrep -i '^\[(order|nearstart|nearend|note|conflict|patch|requires)( |\])' data/mlox_base.txt |wc -l|xargs echo "rules:		"

