.PHONY: all janne bollinger german-tts cc_bollinger roadbooks

all: janne bollinger german-tts
	@echo "Done"

roadbooks:
	./codriver.py --roadbook-csv --roadbook-name '/.*/' > out/roadbooks-luppis-v2.csv
	@echo "Done"

cc_bollinger:
	./codriver.py --codriver bollinger --codriver-fallback-to-base --create-codriver "build/codriver_David Bollinger"
	@echo "Done"

janne:
	./codriver.py --codriver janne-v2 --map-to-cc-csv > out/janne-v2-cc.csv
	./codriver.py --codriver janne-v2 --rbr-list-csv > out/janne-v2-rbr.csv
	@echo "Done"

bollinger:
	./codriver.py --codriver bollinger --codriver-fallback-to-base --map-to-cc-csv > out/bollinger-cc.csv
	./codriver.py --codriver bollinger --rbr-list-csv > out/bollinger-rbr.csv
	@echo "Done"

german-tts:
	./codriver.py --codriver german-tts --rbr-list-csv > out/german-tts-rbr.csv
	@echo "Done"