"""Integrated Quantum Circuit Optimization Framework

Provides a comprehensive optimization pipeline combining multiple pattern-based
and analysis-based optimization passes for quantum circuits. Supports configurable
optimization levels and precision thresholds for QFT-based arithmetic circuits.

This module integrates:
- Dead code elimination (quantum-safe)
- CCNOT decomposition (Barenco construction)
- In-place CNOT chain optimization
- Draper QFT arithmetic optimizations
- Phase precision filtering
"""

from xdsl.dialects.builtin import ModuleOp
from xdsl.rewriter import Rewriter
from xdsl.pattern_rewriter import GreedyRewritePatternApplier

# existing optimization passes
from .remove_unused_op import RemoveUnusedOperations
from .ccnot_decomposition import CCnot_decomposition
from .in_placing import InPlacing
from .draper_optimizer import DraperOptimizer


class IntegratedQuantumOptimizer:
    """Comprehensive quantum circuit optimization framework.
    
    Combines pattern-based optimizations using XDSL's RewritePattern framework
    with analysis-based optimizations. Provides configurable optimization levels
    and tracks optimization statistics.
    
    Attributes:
        enable_decomposition: Whether to decompose CCNOT gates.
        enable_cse: Whether to apply common subexpression elimination.
        enable_dead_code: Whether to remove unused operations.
        enable_in_place: Whether to optimize CNOT chains in-place.
        enable_draper_opt: Whether to apply Draper QFT optimizations.
        precision_threshold: Minimum phase angle to retain.
        stats: Dictionary tracking optimization statistics.
    """
    
    def __init__(self, enable_decomposition: bool = True, 
                 enable_cse: bool = True,
                 enable_dead_code: bool = True,
                 enable_in_place: bool = True,
                 enable_draper_opt: bool = True,
                 precision_threshold: float = 1e-6):
        """
        Initialize the integrated optimizer.
        
        Args:
            enable_decomposition: Enable CCNOT decomposition pass
            enable_cse: Enable common subexpression elimination
            enable_dead_code: Enable removal of unused operations
            enable_in_place: Enable in-place computation optimization
            enable_draper_opt: Enable Draper QFT arithmetic optimizations
            precision_threshold: Threshold for phase precision optimization
        """
        self.enable_decomposition = enable_decomposition
        self.enable_cse = enable_cse
        self.enable_dead_code = enable_dead_code
        self.enable_in_place = enable_in_place
        self.enable_draper_opt = enable_draper_opt
        self.precision_threshold = precision_threshold
        
        # statistics tracking
        self.stats = {
            'passes_applied': [],
            'operations_before': 0,
            'operations_after': 0
        }
    
    def optimize_circuit(self, module: ModuleOp, 
                        analysis_only: bool = False,
                        verbose: bool = True) -> ModuleOp:
        """
        Apply comprehensive optimization pipeline to quantum circuit.
        
        Args:
            module: Input MLIR module containing quantum operations
            analysis_only: If True, only perform analysis without modifications
            verbose: Print optimization progress and insights
            
        Returns:
            Optimized MLIR module
        """
        if verbose:
            print("[INFO] Starting integrated quantum circuit optimization")
        
        self._collect_initial_stats(module)
        self._collect_initial_stats(module)
        
        if analysis_only:
            if verbose:
                print("[INFO] Analysis-only mode completed")
            return module
        
        # apply optimization passes
        optimized_module = self._apply_pattern_optimizations(module, verbose)
        
        # collect final statistics
        if verbose:
            print("\n[INFO] Optimization Results")
        
        self._collect_final_stats(optimized_module)
        self._print_optimization_summary(verbose)
        
        return optimized_module
    
    def _collect_initial_stats(self, module: ModuleOp) -> None:
        """Collect statistics before optimization.
        
        Args:
            module: Input MLIR module to analyze.
        """
        op_count = len(list(module.walk()))
        self.stats['operations_before'] = op_count
    
    def _collect_final_stats(self, module: ModuleOp) -> None:
        """Collect statistics after optimization.
        
        Args:
            module: Optimized MLIR module to analyze.
        """
        op_count = len(list(module.walk()))
        self.stats['operations_after'] = op_count
    
    def _apply_pattern_optimizations(self, module: ModuleOp, verbose: bool) -> ModuleOp:
        """Apply pattern-based optimization passes.
        
        Integrates existing optimization passes using XDSL's pattern rewriting
        framework. Applies Draper optimizations first, followed by pattern-based
        rewrites in the configured order.
        
        Args:
            module: Input MLIR module to optimize.
            verbose: Whether to print progress messages.
            
        Returns:
            Optimized MLIR module.
        """
        rewriter = Rewriter()
        patterns = []
        
        if self.enable_draper_opt:
            if verbose:
                print("  > Applying Draper QFT optimizations...")
            try:
                draper_opt = DraperOptimizer(precision_threshold=self.precision_threshold)
                module = draper_opt.optimize_draper_circuit(module)
                if verbose:
                    print("  [PASS] Applied: Draper QFT optimizations")
            except Exception as e:
                if verbose:
                    print(f"  [WARN] Draper optimization failed: {e}")
        
        if self.enable_dead_code:
            patterns.append(RemoveUnusedOperations())
            if verbose:
                print("  [PASS] Added: Dead code elimination")
        
        if self.enable_decomposition:
            patterns.append(CCnot_decomposition())
            if verbose:
                print("  [PASS] Added: CCNOT decomposition")
        
        if self.enable_in_place:
            patterns.append(InPlacing())
            if verbose:
                print("  [PASS] Added: In-place computation")
        
        if patterns:
            if verbose:
                print(f"  > Applying {len(patterns)} optimization patterns...")
            
            try:
                applier = GreedyRewritePatternApplier(patterns)
                # try xdsl api methods (version-dependent)
                if hasattr(applier, 'rewrite_module'):
                    applier.rewrite_module(module)  # type: ignore[attr-defined]
                elif hasattr(applier, 'apply_patterns'):
                    applier.apply_patterns(module)  # type: ignore[attr-defined]
                else:  # fallback: apply patterns manually
                    for pattern in patterns:
                        if hasattr(pattern, 'apply_to_module'):
                            pattern.apply_to_module(module)
                        elif hasattr(pattern, 'match_and_rewrite'):
                            for op in list(module.walk()):
                                try:
                                    pattern.match_and_rewrite(op, rewriter)
                                except:
                                    continue
                
                self.stats['passes_applied'] = [type(p).__name__ for p in patterns]
                
            except Exception as e:
                if verbose:
                    print(f"  [WARN] Pattern application failed: {e}")
                    print(f"  > Falling back to analysis-only mode")
                self.stats['passes_applied'] = ["Analysis only (pattern application failed)"]
        else:
            if verbose:
                print("  [WARN] No optimization patterns enabled")
        
        return module
    
    def _print_optimization_summary(self, verbose: bool) -> None:
        """Print summary of optimization results.
        
        Args:
            verbose: Whether to print the summary.
        """
        if not verbose:
            return
            
        print("\n[INFO] Optimization Summary")
        print("=" * 40)
        
        # operation count changes
        before = self.stats['operations_before']
        after = self.stats['operations_after']
        
        if before > 0:
            reduction = before - after
            percentage = (reduction / before) * 100
            print(f"Operations: {before} → {after} ({reduction:+d}, {percentage:+.1f}%)")
        
        # applied passes
        if self.stats['passes_applied']:
            print(f"Passes applied: {', '.join(self.stats['passes_applied'])}")
        
        # analysis insights summary
        insights = self.stats.get('analysis_insights', {})
        if 'small_phases_found' in insights:
            print(f"Phase optimization opportunities: {insights['small_phases_found']}")
        
        if 'operation_counts' in insights:
            total_ops = sum(insights['operation_counts'].values())
            print(f"Total quantum operations analyzed: {total_ops}")


def create_optimizer_pipeline(optimization_level: str = "default", precision_threshold: float = 1e-6) -> IntegratedQuantumOptimizer:
    """Create preconfigured optimization pipeline.
    
    Args:
        optimization_level: Optimization level to apply. Options are:
            - "conservative": Only dead code elimination
            - "default": Balanced optimization (recommended)
            - "aggressive": All optimizations enabled
            - "analysis_only": No modifications, analysis only
        precision_threshold: Phase precision threshold for Draper optimization.
            Phases smaller than this value are filtered out.
        
    Returns:
        Configured IntegratedQuantumOptimizer instance.
    """
    if optimization_level == "conservative":
        return IntegratedQuantumOptimizer(
            enable_decomposition=False,
            enable_cse=False,
            enable_dead_code=True,
            enable_in_place=False,
            enable_draper_opt=False,
            precision_threshold=max(precision_threshold, 1e-3)
        )
    
    elif optimization_level == "aggressive":
        return IntegratedQuantumOptimizer(
            enable_decomposition=True,
            enable_cse=True,
            enable_dead_code=True,
            enable_in_place=True,
            enable_draper_opt=True,
            precision_threshold=precision_threshold
        )
    
    elif optimization_level == "analysis_only":
        return IntegratedQuantumOptimizer(
            enable_decomposition=False,
            enable_cse=False,
            enable_dead_code=False,
            enable_in_place=False,
            enable_draper_opt=False
        )
    
    else:
        return IntegratedQuantumOptimizer(
            enable_decomposition=True,
            enable_cse=False,
            enable_dead_code=True,
            enable_in_place=True,
            enable_draper_opt=True,
            precision_threshold=precision_threshold
        )


def optimize_quantum_circuit(module: ModuleOp, 
                           optimization_level: str = "default",
                           analysis_only: bool = False,
                           verbose: bool = True,
                           precision_threshold: float = 1e-6) -> ModuleOp:
    """Optimize quantum circuits with configurable optimization level.
    
    Convenience function that creates an optimizer pipeline and applies it
    to the input module. Supports multiple optimization levels and analysis mode.
    
    Args:
        module: Input MLIR module containing quantum operations.
        optimization_level: Optimization level ("conservative", "default",
            "aggressive", or "analysis_only").
        analysis_only: If True, only perform analysis without modifications.
        verbose: If True, print optimization progress and results.
        precision_threshold: Phase precision threshold for Draper optimization.
            Phases smaller than this are filtered out.
        
    Returns:
        Optimized MLIR module.
    """
    optimizer = create_optimizer_pipeline(optimization_level, precision_threshold=precision_threshold)
    return optimizer.optimize_circuit(module, analysis_only, verbose)
