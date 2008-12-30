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
TES3LINTFILES  := $(wildcard util/tes3lint util/tes3lint*.bat util/tes3lint*.txt)
TES3LINTVER    := $(shell svn log -l 1 -q util/tes3lint | grep ^r | cut -f 1 -d " ")
TES3LINTARC    := tes3lint-$(TES3LINTVER).7z

all: mlox-dist data-dist test-dist tes3lint-dist

upload: upload-mlox upload-exe upload-data upload-tes3lint

upload-mlox:
	@echo "Uploading dist/$(MLOXARC)"
	$(UPLOAD) -s "[mlox $(VERSION)] - requires Python25 and wxPython" dist/$(MLOXARC)

upload-data:
	@echo "Uploading `cat dist/DATAARC`"
	$(UPLOAD) -s "[mlox-data $(RELDATE)] - install mlox_base.txt into your mlox directory" `cat dist/DATAARC`

upload-exe:
	@echo "Uploading dist/$(EXEARC)"
	$(UPLOAD) -s "[mlox-exe $(VERSION)] - standalone executable for Windows" dist/$(EXEARC)

upload-tes3lint:
	@echo "Uploading dist/$(TES3LINTARC)"
	$(UPLOAD) -s "[tes3lint $(TES3LINTVER)]" dist/$(TES3LINTARC)


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

tes3lint-dist: dist/$(TES3LINTARC)

dist/$(TES3LINTARC): dist/tes3lint $(TES3LINTFILES)
	@rsync -uvaC $(TES3LINTFILES) dist/tes3lint/ > /dev/null 2>&1
	@cp License.txt dist/tes3lint
	@echo "Adding DOS line endings to .bat and .txt files in staging directory"
	@for i in dist/tes3lint/*.bat dist/tes3lint/*.txt ; do perl -p -i -e "s/\015?$$/\015/" $$i ; done
	@(cd dist && 7z a $(TES3LINTARC) tes3lint) > /dev/null 2>&1
	@rm -rf dist/tes3lint/
	@echo "CREATED distibution archive for tes3lint: $@"

dist/tes3lint:
	@echo "Creating $@"
	@mkdir -p $@

stats:
	@echo "Rule-base stats ($(RELDATE))"
	@grep '^;; @' data/mlox_base.txt |wc -l|xargs echo "sections:	"
	@egrep -i '^\[(order|nearstart|nearend|note|conflict|patch|requires)( |\])' data/mlox_base.txt |wc -l|xargs echo "rules:		"

