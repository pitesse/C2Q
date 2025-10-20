#!/bin/bash
# Quick setup and build script for C2Q paper

set -e  # Exit on error

# Add TeX to PATH
export PATH="/Library/TeX/texbin:$PATH"

PAPER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PAPER_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if LaTeX is installed
check_latex() {
    print_status "Checking for LaTeX installation..."
    
    if command -v pdflatex &> /dev/null; then
        LATEX_VERSION=$(pdflatex --version | head -n 1)
        print_success "Found: $LATEX_VERSION"
        return 0
    else
        print_error "LaTeX not found!"
        echo ""
        echo "Please install LaTeX:"
        echo "  macOS:   brew install --cask mactex"
        echo "  Ubuntu:  sudo apt-get install texlive-full"
        echo ""
        return 1
    fi
}

# Generate figures
generate_figures() {
    print_status "Generating figures from quantum circuits..."
    
    if [ -f "generate_figures.py" ]; then
        python3 generate_figures.py
        if [ $? -eq 0 ]; then
            print_success "Figures generated successfully"
        else
            print_warning "Figure generation had errors (you can continue without figures)"
        fi
    else
        print_warning "generate_figures.py not found, skipping figure generation"
    fi
}

# Compile paper
compile_paper() {
    print_status "Compiling LaTeX document..."
    
    if make all > /dev/null 2>&1; then
        print_success "Paper compiled successfully!"
        return 0
    else
        print_error "Compilation failed. Running verbose compilation..."
        make all
        return 1
    fi
}

# Open PDF
open_pdf() {
    print_status "Opening PDF..."
    
    if [ -f "main.pdf" ]; then
        if command -v open &> /dev/null; then
            open main.pdf
            print_success "PDF opened in default viewer"
        elif command -v xdg-open &> /dev/null; then
            xdg-open main.pdf
            print_success "PDF opened in default viewer"
        else
            print_warning "Could not open PDF automatically. File: main.pdf"
        fi
    else
        print_error "main.pdf not found!"
        return 1
    fi
}

# Show usage
show_usage() {
    cat << EOF
C2Q Paper Build Script
=====================

Usage: $0 [OPTIONS]

Options:
    -h, --help          Show this help message
    -f, --figures       Generate figures only
    -c, --compile       Compile paper only
    -q, --quick         Quick compile (single pass)
    --clean             Clean all generated files
    --rebuild           Clean and rebuild
    --no-figures        Skip figure generation
    --no-open           Don't open PDF after compilation

Default behavior (no options): 
    Check LaTeX → Generate figures → Compile paper → Open PDF

Examples:
    $0                  # Full build and open
    $0 --quick          # Quick draft compilation
    $0 --no-figures     # Compile without regenerating figures
    $0 --clean          # Clean all generated files

EOF
}

# Parse command line arguments
GENERATE_FIGURES=true
COMPILE=true
OPEN_PDF=true
QUICK=false
CLEAN=false
REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -f|--figures)
            COMPILE=false
            OPEN_PDF=false
            shift
            ;;
        -c|--compile)
            GENERATE_FIGURES=false
            shift
            ;;
        -q|--quick)
            QUICK=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --no-figures)
            GENERATE_FIGURES=false
            shift
            ;;
        --no-open)
            OPEN_PDF=false
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
echo ""
echo "════════════════════════════════════════════════"
echo "     C2Q Paper Build Script"
echo "════════════════════════════════════════════════"
echo ""

# Handle clean
if [ "$CLEAN" = true ]; then
    print_status "Cleaning generated files..."
    make clean
    print_success "Clean complete"
    exit 0
fi

# Handle rebuild
if [ "$REBUILD" = true ]; then
    print_status "Rebuilding from scratch..."
    make rebuild
    if [ $? -eq 0 ]; then
        print_success "Rebuild complete!"
        if [ "$OPEN_PDF" = true ]; then
            open_pdf
        fi
    else
        print_error "Rebuild failed"
        exit 1
    fi
    exit 0
fi

# Check LaTeX installation
if ! check_latex; then
    exit 1
fi
echo ""

# Generate figures
if [ "$GENERATE_FIGURES" = true ]; then
    generate_figures
    echo ""
fi

# Compile paper
if [ "$COMPILE" = true ]; then
    if [ "$QUICK" = true ]; then
        print_status "Quick compilation (single pass)..."
        make quick
    else
        compile_paper
    fi
    echo ""
fi

# Open PDF
if [ "$OPEN_PDF" = true ] && [ "$COMPILE" = true ]; then
    open_pdf
fi

echo ""
echo "════════════════════════════════════════════════"
print_success "All done!"
echo ""
echo "Paper location: $PAPER_DIR/main.pdf"
echo ""
echo "Next steps:"
echo "  • Review the PDF and make any necessary edits"
echo "  • Add your figures to the figures/ directory"
echo "  • Update author information in main.tex"
echo "  • Add more references to references.bib as needed"
echo ""
echo "════════════════════════════════════════════════"
