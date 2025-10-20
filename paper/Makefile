# Makefile for compiling LaTeX paper
# Compatible with macOS and standard LaTeX distributions

# Main document name (without .tex extension)
MAIN = main

# LaTeX compiler
LATEX = pdflatex

# BibTeX compiler
BIBTEX = bibtex

# PDF viewer (macOS)
VIEWER = open

# Output directory
OUTDIR = build

# Flags
LATEX_FLAGS = -output-directory=$(OUTDIR) -interaction=nonstopmode

.PHONY: all clean view help setup

# Default target: compile the paper
all: setup $(MAIN).pdf

# Create output directory
setup:
	@mkdir -p $(OUTDIR)

# Compile the paper (full build with bibliography)
$(MAIN).pdf: $(MAIN).tex
	@echo "Compiling LaTeX document (first pass)..."
	@$(LATEX) $(LATEX_FLAGS) $(MAIN).tex
	@echo "Running BibTeX..."
	@cd $(OUTDIR) && $(BIBTEX) $(MAIN) || true
	@echo "Compiling LaTeX document (second pass)..."
	@$(LATEX) $(LATEX_FLAGS) $(MAIN).tex
	@echo "Compiling LaTeX document (third pass)..."
	@$(LATEX) $(LATEX_FLAGS) $(MAIN).tex
	@cp $(OUTDIR)/$(MAIN).pdf .
	@echo "PDF generated successfully: $(MAIN).pdf"

# Quick compile (single pass, no bibliography)
quick: setup
	@echo "Quick compile (single pass)..."
	@$(LATEX) $(LATEX_FLAGS) $(MAIN).tex
	@cp $(OUTDIR)/$(MAIN).pdf .
	@echo "PDF generated: $(MAIN).pdf"

# View the PDF
view: $(MAIN).pdf
	@$(VIEWER) $(MAIN).pdf

# Clean auxiliary files
clean:
	@echo "Cleaning auxiliary files..."
	@rm -rf $(OUTDIR)
	@rm -f $(MAIN).pdf
	@rm -f *.aux *.log *.bbl *.blg *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz
	@echo "Clean complete."

# Clean and rebuild
rebuild: clean all

# Help message
help:
	@echo "LaTeX Paper Makefile"
	@echo "===================="
	@echo "Available targets:"
	@echo "  all     - Compile the paper with bibliography (default)"
	@echo "  quick   - Quick compile (single pass, no bibliography)"
	@echo "  view    - Open the PDF in the default viewer"
	@echo "  clean   - Remove all generated files"
	@echo "  rebuild - Clean and rebuild from scratch"
	@echo "  help    - Show this help message"
	@echo ""
	@echo "Usage examples:"
	@echo "  make          # Compile the paper"
	@echo "  make quick    # Quick compile for drafts"
	@echo "  make view     # View the PDF"
	@echo "  make clean    # Clean up files"
