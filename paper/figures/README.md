# Figures Directory

This directory contains figures and diagrams for the C2Q paper.

## Guidelines

### File Formats
- **Preferred**: PDF (vector graphics)
- **Alternative**: PNG (high resolution, 300+ DPI)
- **Avoid**: JPG for diagrams/plots (lossy compression)

### Naming Convention
Use descriptive names with underscores:
- `compiler_architecture.pdf`
- `qft_circuit_diagram.pdf`
- `optimization_results.pdf`
- `gate_count_comparison.png`

### Size Recommendations
- Single-column width: ~3.5 inches (88.9mm)
- Double-column width: ~7 inches (177.8mm)
- Keep aspect ratios reasonable for readability

## Adding Figures to Paper

### Single-column figure
```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\columnwidth]{figures/your_figure.pdf}
    \caption{Your caption describing the figure}
    \label{fig:your_label}
\end{figure}
```

### Double-column figure
```latex
\begin{figure*}[t]
    \centering
    \includegraphics[width=\textwidth]{figures/your_figure.pdf}
    \caption{Your caption describing the figure}
    \label{fig:your_label}
\end{figure*}
```

### Subfigures
```latex
\begin{figure}[t]
    \centering
    \begin{subfigure}[b]{0.45\columnwidth}
        \includegraphics[width=\textwidth]{figures/fig_a.pdf}
        \caption{First subfigure}
        \label{fig:sub_a}
    \end{subfigure}
    \hfill
    \begin{subfigure}[b]{0.45\columnwidth}
        \includegraphics[width=\textwidth]{figures/fig_b.pdf}
        \caption{Second subfigure}
        \label{fig:sub_b}
    \end{subfigure}
    \caption{Overall caption for both subfigures}
    \label{fig:combined}
\end{figure}
```

## Suggested Figures

Based on the C2Q project, consider creating:

1. **System Architecture Diagram**
   - Frontend → Middle-end → Backend flow
   - Show lexer, parser, IR generator, optimizer, circuit generator

2. **QFT Circuit Example**
   - Visual representation of quantum addition circuit
   - Show before/after optimization

3. **Optimization Results Chart**
   - Bar charts comparing gate count, depth, qubits
   - Before/after optimization metrics

4. **Compilation Pipeline**
   - Flow diagram from C code to quantum circuit
   - Intermediate representations at each stage

5. **Gate Distribution Pie Chart**
   - Show percentage of different gate types
   - Highlight phase rotation density

6. **Example Circuit Diagram**
   - Simple arithmetic operation (3+5)
   - Annotated quantum circuit

## Tools for Creating Figures

### Diagrams
- **Draw.io**: Free online diagram tool
- **TikZ**: LaTeX package for programmatic diagrams
- **Inkscape**: Free vector graphics editor
- **Adobe Illustrator**: Professional vector graphics

### Plots/Charts
- **Matplotlib**: Python plotting library (already in project)
- **pgfplots**: LaTeX package for plots
- **Excel/Numbers**: Export to PDF

### Circuit Diagrams
- **Qiskit**: Use `circuit_drawer` to export circuits
- **Quantikz**: LaTeX package for quantum circuits

## Example: Generating Circuit from Qiskit

```python
from qiskit import QuantumCircuit
from qiskit.visualization import circuit_drawer

# Create your circuit
circuit = create_circuit(...)

# Save as PDF
circuit_drawer(circuit, output='latex_source', 
               filename='figures/circuit_diagram.pdf')
```

## Current Figures
(List your figures here as you add them)

- None yet - add your figures and document them here

## Notes
- Keep source files (.svg, .drawio, .py scripts) in a `sources/` subdirectory
- Only commit final PDF/PNG versions to keep repository size manageable
- Ensure all figures are referenced in the paper text
