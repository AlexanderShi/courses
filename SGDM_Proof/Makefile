# Build the report (and optionally regenerate the figures).
#   make          -> report/main.pdf, copied to SGDM_Convergence_Report.pdf
#   make figures  -> rerun all numerical experiments (about 2-3 minutes)
#   make clean    -> remove LaTeX build files

PDF := SGDM_Convergence_Report.pdf

all: $(PDF)

$(PDF): report/main.tex report/sections/*.tex report/figures/*.pdf
	cd report && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
	cp report/main.pdf $(PDF)

figures:
	cd experiments && python3 run_all.py

clean:
	cd report && latexmk -C main.tex

.PHONY: all figures clean
