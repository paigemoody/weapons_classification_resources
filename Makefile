QUESTIONS    = content/questions.csv
OPTIONS      = content/classifications.csv
CLASSIFICATIONS = content/classifications.csv
STRUCTURE    = taxonomy-structure.mmd
MMD          = weapons-classification-flowchart.mmd
CLICKTHROUGH = classification-guide.html
HYPOTHESIS   = classification-guide-hypothesis-filtering.html

.PHONY: all clean

all: $(CLICKTHROUGH) $(HYPOTHESIS)

# Intermediate enriched Mermaid (needed only for click-through)
$(MMD): $(STRUCTURE) $(QUESTIONS) content/options.csv $(CLASSIFICATIONS)
	python3 src/build_content_mmd.py \
		--structure $(STRUCTURE) \
		--questions $(QUESTIONS) \
		--options content/options.csv \
		--classifications $(CLASSIFICATIONS) \
		--output $(MMD)

$(CLICKTHROUGH): $(MMD)
	python3 src/mermaid_to_clickthrough.py \
		--input-mmd $(MMD) \
		--output-html $(CLICKTHROUGH) \
		--app-name "[DEMO] Weapons Classification Guide"

$(HYPOTHESIS): $(QUESTIONS) content/options.csv $(CLASSIFICATIONS)
	python3 src/csv_to_hypothesis_filtering.py \
		--questions $(QUESTIONS) \
		--options content/options.csv \
		--classifications $(CLASSIFICATIONS) \
		--output $(HYPOTHESIS) \
		--app-name "[DEMO] Weapons Classification Guide (Hypothesis Filtering)"

clean:
	rm -f $(MMD) $(CLICKTHROUGH) $(HYPOTHESIS)
