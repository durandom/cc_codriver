.PHONY: all out_janne out_bollinger cc_bollinger

all: out_janne out_bollinger
	@echo "Done"

cc_bollinger:
	./codriver.py --codriver bollinger --map-to-cc build/copilot_bollinger
	@echo "Done"

out_janne:
	./codriver.py --codriver janne-v2 --map-to-cc-csv > out/janne-v2-cc.csv
	./codriver.py --codriver janne-v2 --rbr-list-csv > out/janne-v2-rbr.csv
	@echo "Done"

out_bollinger:
	./codriver.py --codriver bollinger --map-to-cc-csv > out/bollinger-cc.csv
	./codriver.py --codriver bollinger --rbr-list-csv > out/bollinger-rbr.csv
	@echo "Done"
