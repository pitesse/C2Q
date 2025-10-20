# C2Q Paper - LaTeX Documentation

This directory contains the LaTeX source for the academic paper documenting the C2Q compiler project.

## Paper Information

- **Title**: C2Q: A Compiler Framework for Translating Classical C Programs to Quantum Circuits
- **Template**: IEEE Conference (IEEEtran) - suitable for Politecnico di Milano submissions
- **Format**: Two-column layout
- **Main File**: `main.tex`

## Prerequisites

### macOS
```bash
# Install MacTeX (full distribution)
brew install --cask mactex

# Or install BasicTeX (minimal distribution)
brew install --cask basictex

# If using BasicTeX, install additional packages:
sudo tlmgr update --self
sudo tlmgr install collection-fontsrecommended
sudo tlmgr install collection-latexextra
sudo tlmgr install ieeetran
sudo tlmgr install algorithms algorithmicx
```

### Linux
```bash
# Ubuntu/Debian
sudo apt-get install texlive-full

# Or minimal installation:
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-publishers
```

### Windows
Download and install MiKTeX or TeX Live from their respective websites.

## Compilation

### Using Make (Recommended)
```bash
# Full compilation with bibliography
make

# Quick draft compilation (faster, single pass)
make quick

# View the generated PDF
make view

# Clean all generated files
make clean

# Rebuild from scratch
make rebuild
```

### Manual Compilation
```bash
# Full compilation sequence
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# The PDF will be generated as main.pdf
```

## Document Structure

The paper follows this organization:

1. **Abstract**: Overview of the C2Q compiler and key results
2. **Introduction**: Motivation and contributions
3. **Background**: Quantum computing fundamentals and related work
4. **System Architecture**: Frontend, middle-end, backend design
5. **Optimization Framework**: Detailed optimization strategies
6. **Implementation**: Technology stack and code organization
7. **Evaluation**: Test results and performance metrics
8. **Discussion**: Strengths, limitations, and future work
9. **Conclusion**: Summary of achievements
10. **References**: Bibliography in IEEE format

## Customization

### Author Information
Edit the `\author` block in `main.tex`:
```latex
\author{
    \IEEEauthorblockN{Your Name}
    \IEEEauthorblockA{
        \textit{Department of Electronics, Information and Bioengineering}\\
        \textit{Politecnico di Milano}\\
        Milan, Italy\\
        your.email@polimi.it
    }
}
```

### Adding Figures
Place figure files in the `paper/figures/` directory and reference them:
```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/your_figure.pdf}
    \caption{Your caption here}
    \label{fig:your_label}
\end{figure}
```

### Adding Tables
Use the booktabs package for professional tables:
```latex
\begin{table}[h]
\centering
\caption{Your table caption}
\label{tab:your_label}
\begin{tabular}{@{}lrr@{}}
\toprule
Column 1 & Column 2 & Column 3 \\ \midrule
Data 1 & Data 2 & Data 3 \\
\bottomrule
\end{tabular}
\end{table}
```

### Code Listings
The paper uses the `listings` package for code:
```latex
\begin{lstlisting}[language=C,caption={Your caption}]
int main() {
    // Your code here
    return 0;
}
\end{lstlisting}
```

## Style Guidelines

- **Two-column format**: Content automatically flows between columns
- **Section numbering**: Automatic
- **References**: Use `\cite{key}` for citations
- **Equations**: Use `\begin{equation}...\end{equation}` for numbered equations
- **Figures/Tables**: Use `[h]` for here, `[t]` for top, `[b]` for bottom placement

## Common Issues

### Missing Packages
If compilation fails due to missing packages:
```bash
# macOS
sudo tlmgr install <package-name>

# Linux (Ubuntu/Debian)
sudo apt-get install texlive-<package-collection>
```

### Bibliography Not Showing
Ensure you run the full compilation sequence:
```bash
make clean && make
```

### PDF Not Updating
Clear auxiliary files and rebuild:
```bash
make rebuild
```

## File Organization

```
paper/
├── main.tex          # Main LaTeX document
├── Makefile          # Compilation automation
├── README.md         # This file
├── figures/          # Directory for figures (create as needed)
└── build/            # Generated during compilation (ignored by git)
```

## LaTeX Tips

### Equation Formatting
```latex
% Inline math
The equation $E = mc^2$ shows...

% Display math
\begin{equation}
    c = \sqrt{a^2 + b^2}
\end{equation}
```

### Cross-References
```latex
% Define label
\section{Introduction}
\label{sec:intro}

% Reference
As discussed in Section~\ref{sec:intro}...
```

### Special Characters
- Use `\texttt{}` for monospace/code
- Use `\textbf{}` for bold
- Use `\textit{}` for italics
- Use `\%` for percent sign
- Use `\&` for ampersand
- Use `\$` for dollar sign

## Politecnico di Milano Guidelines

The IEEE Conference template is widely accepted for:
- Conference papers
- Technical reports
- Master's thesis documentation (supplementary)

For official Politecnico di Milano thesis submissions, you may need to use the official PoliMi thesis template. This paper template is suitable for:
- Research papers
- Conference submissions
- Technical documentation
- Preliminary thesis work

## Export for Submission

For conference/journal submission:
```bash
# Generate the final PDF
make clean && make

# The paper is in: main.pdf
# Submit this PDF file along with source files if required
```

## Version Control

The `.gitignore` should exclude:
```
*.aux
*.log
*.bbl
*.blg
*.out
*.toc
*.pdf
build/
```

Keep in version control:
- `main.tex`
- `Makefile`
- `README.md`
- Any custom `.sty` or `.bib` files
- Figures (source files)

## Need Help?

- **LaTeX Help**: [Overleaf Documentation](https://www.overleaf.com/learn)
- **IEEEtran Help**: `texdoc IEEEtran` or [CTAN](https://ctan.org/pkg/ieeetran)
- **LaTeX Stack Exchange**: [tex.stackexchange.com](https://tex.stackexchange.com)

## License

The paper content is subject to academic integrity policies.
The LaTeX source structure follows standard academic templates.
