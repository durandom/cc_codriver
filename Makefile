.PHONY: all janne bollinger german-tts cc_bollinger roadbooks roadbooks-v3

all: janne-v2 janne-v3 bollinger german-tts
	@echo "Done"

roadbooks-default:
	./codriver.py --roadbook-csv-default --roadbook-name '/.*default.*/' > out/roadbooks-default.csv
	@echo "Done"

roadbooks-v2:
	./codriver.py --roadbook-csv-v2 --roadbook-name '/.*/' > out/roadbooks-luppis-v2.csv
	@echo "Done"

roadbooks-v3:
	./codriver.py --roadbook-csv-v3 --roadbook-name '/.*/' > out/roadbooks-luppis-v3.csv
	@echo "Done"

codriver_bollinger:
	./codriver.py --codriver bollinger --codriver-fallback-to-base --create-codriver "build/codriver_David Bollinger"
	@echo "Done"

codriver_german_tts:
	./codriver.py --codriver german-tts --codriver-fallback-to-base --create-codriver "build/codriver_Hans Juchard"
	@echo "Done"

janne-v2:
	./codriver.py --codriver janne-v2 --map-to-cc-csv > out/janne-v2-cc.csv
	./codriver.py --codriver janne-v2 --rbr-list-csv > out/janne-v2-rbr.csv
	@echo "Done"

janne-v3:
	./codriver.py --codriver janne-v3 --map-to-cc-csv > out/janne-v3-cc.csv
	./codriver.py --codriver janne-v3 --rbr-list-csv > out/janne-v3-rbr.csv
	@echo "Done"

bollinger:
	./codriver.py --codriver bollinger --codriver-fallback-to-base --map-to-cc-csv > out/bollinger-cc.csv
	./codriver.py --codriver bollinger --rbr-list-csv > out/bollinger-rbr.csv
	@echo "Done"

german-tts:
	./codriver.py --codriver german-tts --codriver-fallback-to-base --map-to-cc-csv > out/german-tts-cc.csv
	./codriver.py --codriver german-tts --rbr-list-csv > out/german-tts-rbr.csv
	@echo "Done"