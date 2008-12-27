# Makefile for mlox project

.PHONY: all stats version mlox-dist data-dist test-dist upload upload-mlox upload-data upload-exe

README    := mlox/mlox_readme.txt
PROGRAM   := mlox/mlox.py
RULES     := data/mlox_base.txt
VERSION   := $(shell cat VERSION)
MLOXARC   := mlox-$(VERSION).7z
EXEARC    := mlox-exe-$(VERSION).7z
RELDATE   := $(shell date --utc "+%Y-%m-%d %T (UTC)")
DATAARC   := $(shell data/arcname)
UPLOAD    := googlecode_upload.py -u john.moonsugar -p mlox
ESPLINTFILES  := $(wildcard util/esplint util/esplint*.bat util/esplint*.txt)
ESPLINTVER    := $(shell svn log -l 1 -q util/esplint | grep ^r | cut -f 1 -d " ")
ESPLINTARC    := esplint-$(ESPLINTVER).7z

all: mlox-dist data-dist test-dist esplint-dist

upload: upload-mlox upload-exe upload-data

upload-mlox:
	@echo "Uploading dist/$(MLOXARC)"
	$(UPLOAD) -s "[mlox $(VERSION)] - requires Python25 and wxPython" dist/$(MLOXARC)

upload-data:
	@echo "Uploading `cat dist/DATAARC`"
	$(UPLOAD) -s "[mlox-data $(RELDATE)] - install mlox_base.txt into your mlox directory" `cat dist/DATAARC`

upload-exe:
	@echo "Uploading dist/$(EXEARC)"
	$(UPLOAD) -s "[mlox-exe $(VERSION)] - standalone executable for Windows" dist/$(EXEARC)

upload-esplint:
	@echo "Uploading dist/$(ESPLINTARC)"
	$(UPLOAD) -s "[esplint $(ESPLINTVER)]" dist/$(ESPLINTARC)


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
	@(cd dist && rm -f $(MLOXARC) && 7z a $(MLOXARC) mlox) > /dev/null 2>&1
	@rm -rf dist/mlox/
	@echo "CREATED distibution archive for mlox: $@"

data-dist: dist dist/$(DATAARC) stats

dist/$(DATAARC): $(RULES)
	@echo "Updating $< with latest Version date: $(RELDATE)"
	@perl -p -i -e "s/^\[Version\s+[^\]]+\]/[Version $(RELDATE)]/" $<
	@(cd data ; 7z a ../$@ $(<F)) > /dev/null 2>&1
	@echo "CREATED distibution archive for mlox rule-base: $@"
	@echo "$@" > dist/DATAARC

dist/mlox:
	@echo "Creating $@"
	@mkdir -p $@

esplint-dist: dist/$(ESPLINTARC)

dist/$(ESPLINTARC): dist/esplint $(ESPLINTFILES)
	@rsync -uvaC $(ESPLINTFILES) dist/esplint/ > /dev/null 2>&1
	@cp License.txt dist/esplint
	@echo "Adding DOS line endings to .bat and .txt files in staging directory"
	@for i in dist/esplint/*.bat dist/esplint/*.txt ; do perl -p -i -e "s/\015?$$/\015/" $$i ; done
	@(cd dist && 7z a $(ESPLINTARC) esplint) > /dev/null 2>&1
	@rm -rf dist/esplint/
	@echo "CREATED distibution archive for esplint: $@"

dist/esplint:
	@echo "Creating $@"
	@mkdir -p $@

stats:
	@echo "Rule-base stats ($(RELDATE))"
	@grep '^;; @' data/mlox_base.txt |wc -l|xargs echo "sections:	"
	@egrep -i '^\[(order|nearstart|nearend|note|conflict|patch|requires)( |\])' data/mlox_base.txt |wc -l|xargs echo "rules:		"

