# 🚀 Quick Build Guide

## How to Build Your Paper

You're in the `paper/` directory. The build script is ready to use!

### **Simplest Way** (Just Build It!)

```bash
./build.sh --no-figures
```

This will:
- ✅ Check LaTeX is installed
- ✅ Compile your paper
- ✅ Open the PDF automatically

### **Common Commands**

```bash
# Quick build (fast, for editing)
./build.sh --quick --no-figures

# Full build (with bibliography - slower but complete)
./build.sh --no-figures

# Just compile, don't open PDF
./build.sh --quick --no-figures --no-open

# Clean everything and start fresh
./build.sh --clean

# View help
./build.sh --help
```

### **Why `--no-figures`?**

The figure generation needs qiskit installed in your Python environment. Since you're just writing the paper, you can skip figure generation for now with `--no-figures`.

To enable figures later:
```bash
# In your Python virtual environment
pip install qiskit matplotlib
```

## **Current Status**

✅ LaTeX is installed (BasicTeX)  
✅ Your paper compiles successfully  
✅ PDF is generated: `main.pdf`  
⚠️ Bibliography has minor issues (doesn't affect PDF generation)

## **File Locations**

- **Source**: `main.tex`
- **Output**: `main.pdf` (this is what you submit!)
- **Build files**: `build/` directory (can be deleted anytime)
- **Bibliography**: `references.bib`

## **Typical Workflow While Writing**

```bash
# 1. Edit main.tex in VS Code
# 2. Save the file
# 3. Build it:
./build.sh --quick --no-figures

# Paper opens automatically in Preview!
```

## **Before Final Submission**

```bash
# Clean build with bibliography
./build.sh --clean
./build.sh --no-figures

# Your final PDF is ready: main.pdf
```

## **Troubleshooting**

### "LaTeX not found"
Make sure TeX is in your PATH:
```bash
export PATH="/Library/TeX/texbin:$PATH"
```

### Build fails
Clean and try again:
```bash
./build.sh --clean
./build.sh --quick --no-figures
```

### PDF won't open
Open it manually:
```bash
open main.pdf
```

---

**That's it! Happy writing! 📝**

**Quick command**: `./build.sh --quick --no-figures`
