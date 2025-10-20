# C2Q Paper - Complete Setup Guide

## 📄 What You Have

A complete LaTeX paper setup for documenting your C-to-Quantum compiler project, configured with:

- **IEEE Conference template** (compatible with Politecnico di Milano standards)
- **Two-column layout** as requested
- **Fully structured paper** with all sections pre-written based on your project
- **Build automation** with Makefile and shell scripts
- **Figure generation** scripts to create diagrams from your quantum circuits
- **Bibliography management** with BibTeX

## 📁 File Structure

```
paper/
├── main.tex              # Main LaTeX document (YOUR PAPER)
├── references.bib        # Bibliography database
├── Makefile             # Automated compilation
├── build.sh             # Interactive build script
├── generate_figures.py  # Generate figures from circuits
├── README.md            # Detailed documentation
├── .gitignore          # Git ignore rules
└── figures/            # Directory for figures
    └── README.md       # Figure guidelines
```

## 🚀 Quick Start

### Step 1: Install LaTeX (One-time setup)

Since LaTeX is not installed on your system, you need to install it first:

**macOS (recommended - BasicTeX for smaller install):**
```bash
# Option 1: BasicTeX (smaller, faster install ~100MB)
brew install --cask basictex

# After installation, update package manager
sudo tlmgr update --self

# Install required packages
sudo tlmgr install collection-fontsrecommended
sudo tlmgr install collection-latexextra
sudo tlmgr install ieeetran
sudo tlmgr install algorithms algorithmicx
```

**macOS (alternative - Full MacTeX ~4GB):**
```bash
# Option 2: Full MacTeX (includes everything)
brew install --cask mactex
```

**After installation, restart your terminal or run:**
```bash
eval "$(/usr/libexec/path_helper)"
```

### Step 2: Build Your Paper

Once LaTeX is installed, use the automated build script:

```bash
cd /Users/pitesse/Desktop/code/C_to_Quantum/paper

# Full build (generates figures + compiles paper)
./build.sh

# Or use Make directly
make
```

The script will:
1. ✅ Check LaTeX installation
2. 📊 Generate figures from your quantum circuits
3. 📄 Compile the paper with bibliography
4. 📖 Open the PDF automatically

### Step 3: Customize

Edit `main.tex` to add your information:

1. **Author details** (lines 45-54)
2. **Abstract** (line 59)
3. **Content** (throughout the document)
4. **References** (add to `references.bib`)

## 📋 Build Options

### Using the build script (easiest):
```bash
./build.sh              # Full build with figures
./build.sh --quick      # Fast draft (no bib, single pass)
./build.sh --no-figures # Skip figure generation
./build.sh --clean      # Clean all generated files
./build.sh --rebuild    # Clean and rebuild from scratch
./build.sh --help       # See all options
```

### Using Make:
```bash
make           # Full compilation with bibliography
make quick     # Quick draft compilation
make view      # Open the PDF
make clean     # Remove generated files
make rebuild   # Clean and rebuild
```

### Manual compilation:
```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## 🎨 Adding Your Content

### 1. Update Author Information

In `main.tex`, find the `\author` section and update:

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

### 2. Add Figures

Generate figures from your circuits:
```bash
# Generate all figures automatically
python3 generate_figures.py

# Or create your own figures and place them in figures/
```

Then reference in the paper:
```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/your_figure.pdf}
    \caption{Description of your figure}
    \label{fig:your_label}
\end{figure}
```

### 3. Add References

Edit `references.bib` to add new references:
```bibtex
@article{author2024,
  title={Title of the Paper},
  author={Author, First and Author, Second},
  journal={Journal Name},
  year={2024}
}
```

Then cite in text: `\cite{author2024}`

### 4. Modify Content

The paper is already filled with content based on your project. You can:
- Modify existing sections
- Add new sections with `\section{Title}`
- Add subsections with `\subsection{Title}`
- Add equations, tables, code listings, etc.

## 📊 Paper Structure (Already Included)

1. **Abstract** - Project overview and key results
2. **Introduction** - Motivation and contributions
3. **Background and Related Work** - Quantum computing fundamentals
4. **System Architecture** - Frontend, middle-end, backend
5. **Optimization Framework** - Detailed optimization strategies
6. **Implementation Details** - Technology stack
7. **Evaluation** - Test results and metrics
8. **Discussion** - Strengths, limitations, future work
9. **Conclusion** - Summary
10. **References** - Bibliography

## 🔧 Troubleshooting

### LaTeX not found after installation
```bash
# Refresh your PATH
eval "$(/usr/libexec/path_helper)"

# Or restart your terminal
```

### Missing LaTeX packages
```bash
# Install specific package
sudo tlmgr install package-name

# Update all packages
sudo tlmgr update --all
```

### Bibliography not showing
```bash
# Make sure you run the full compilation sequence
make clean && make
```

### Figures not generating
```bash
# Check if Python dependencies are installed
pip install qiskit matplotlib

# Generate figures manually
python3 generate_figures.py
```

### Permission denied on scripts
```bash
chmod +x build.sh generate_figures.py
```

## 📝 Writing Tips

### Code Examples
```latex
\begin{lstlisting}[language=C,caption={Your caption}]
int main() {
    int a = 3;
    return 0;
}
\end{lstlisting}
```

### Equations
```latex
% Inline: $E = mc^2$
% Display:
\begin{equation}
    c = \sqrt{a^2 + b^2}
    \label{eq:pythagorean}
\end{equation}
```

### Tables
```latex
\begin{table}[h]
\centering
\caption{Your caption}
\begin{tabular}{@{}lrr@{}}
\toprule
Header 1 & Header 2 & Header 3 \\ \midrule
Data 1 & Data 2 & Data 3 \\
\bottomrule
\end{tabular}
\label{tab:your_label}
\end{table}
```

### Cross-references
```latex
% Define: \label{sec:intro}
% Reference: Section~\ref{sec:intro}
% Figure: Figure~\ref{fig:circuit}
% Table: Table~\ref{tab:results}
```

## 🎯 Next Steps

1. **Install LaTeX** (if not done yet)
   ```bash
   brew install --cask basictex
   ```

2. **Build the paper**
   ```bash
   ./build.sh
   ```

3. **Review the output** (main.pdf will open automatically)

4. **Customize** the content in main.tex

5. **Add your figures** using generate_figures.py or manually

6. **Update author info** with your details

7. **Add more references** if needed

## 📚 Resources

- **LaTeX Help**: [Overleaf Tutorial](https://www.overleaf.com/learn)
- **IEEEtran**: Run `texdoc IEEEtran` after installation
- **BibTeX**: [Bibliography Management](https://www.overleaf.com/learn/latex/Bibliography_management_with_bibtex)
- **LaTeX Stack Exchange**: [tex.stackexchange.com](https://tex.stackexchange.com)

## 🎓 For Politecnico di Milano

This template uses the IEEE Conference format, which is:
- ✅ Suitable for conference papers
- ✅ Suitable for technical reports
- ✅ Good for research documentation
- ✅ Two-column format as requested

For **official thesis submissions**, you may need to use the Politecnico di Milano thesis template. However, this paper format is excellent for:
- Publishing your work
- Internal documentation
- Preliminary thesis chapters
- Research reports

## ⚡ Quick Reference Card

```bash
# First time setup
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install collection-fontsrecommended collection-latexextra ieeetran

# Build paper
./build.sh              # Full build
./build.sh --quick      # Quick draft

# View paper
make view

# Clean up
make clean

# Generate figures
python3 generate_figures.py
```

## 💡 Tips for Success

1. **Compile frequently** - Build after every major change to catch errors early
2. **Use version control** - Commit your changes regularly
3. **Write in drafts** - Use `--quick` flag while writing to save time
4. **Add figures early** - Placeholder figures help visualize layout
5. **Get feedback** - Share PDFs with advisors/colleagues regularly

---

**You're all set!** Once LaTeX is installed, just run `./build.sh` and your paper will be ready.

For questions or issues, refer to the README files in the paper/ and figures/ directories.
