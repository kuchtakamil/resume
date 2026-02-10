# Makefile for LaTeX resume

MAIN = resume
LATEX = pdflatex
LATEXFLAGS = -interaction=nonstopmode -halt-on-error

.PHONY: all clean watch tailored

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	$(LATEX) $(LATEXFLAGS) $(MAIN).tex
	$(LATEX) $(LATEXFLAGS) $(MAIN).tex

clean:
	rm -f *.aux *.log *.out *.toc *.fls *.fdb_latexmk *.synctex.gz *.bbl *.blg

tailored:
	python tailor.py $(OFFER)

watch:
	@echo "Watching for changes..."
	@while true; do \
		inotifywait -q -e modify $(MAIN).tex; \
		make all; \
	done