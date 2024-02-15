.PHONY: all out_janne out_bollinger

all: out_janne out_bollinger
	@echo "Done"

out_janne:
	./codriver.py --config config-janne-v2.json --map-to-cc-csv > out/janne-cc.csv
	./codriver.py --config config-janne-v2.json --rbr-list-csv > out/janne-rbr.csv
	@echo "Done"

out_bollinger:
	./codriver.py --config config-bollinger.json --map-to-cc-csv > out/bollinger-cc.csv
	./codriver.py --config config-bollinger.json --rbr-list-csv > out/bollinger-rbr.csv
	@echo "Done"
