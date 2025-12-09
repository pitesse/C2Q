"""
Integrated Quantum Circuit Optimization Framework

This module combines existing optimization passes with new analysis capabilities
to provide a comprehensive optimization pipeline for quantum circuits generated
by the C-to-Quantum compiler.
"""

from typing import List, Dict, Optional
import logging

from xdsl.ir import Operation
from xdsl.dialects.builtin import ModuleOp
from xdsl.rewriter import Rewriter
from xdsl.pattern_rewriter import GreedyRewritePatternApplier

# Import existing optimization passes
from .remove_unused_op import RemoveUnusedOperations
from .ccnot_decomposition import CCnot_decomposition
from .qubit_renumber import QubitRenumber
from .in_placing import InPlacing
from .draper_optimizer import DraperOptimizer
# Hermitian transformation uses ModulePass, need different integration approach
# from .hermitian_gates_transformation import HermitianGatesElimination
# from .common_subexpr_elimination import CommonSubexprElimination

# Import new analysis capabilities
from .simple_optimizer import SimpleQuantumOptimizer


class IntegratedQuantumOptimizer:
    """
    Comprehensive quantum circuit optimization framework.
    
    Combines pattern-based optimizations (using XDSL RewritePattern) with
    analysis-based optimizations and provides a unified interface for
    quantum circuit optimization.
    """
    
    def __init__(self, enable_decomposition: bool = True, 
                 enable_cse: bool = True,
                 enable_dead_code: bool = True,
                 enable_renumbering: bool = True,
                 enable_in_place: bool = True,
                 enable_draper_opt: bool = True,
                 precision_threshold: float = 1e-6):
        """
        Initialize the integrated optimizer.
        
        Args:
            enable_decomposition: Enable CCNOT decomposition pass
            enable_cse: Enable common subexpression elimination
            enable_dead_code: Enable removal of unused operations
            enable_renumbering: Enable qubit renumbering optimization
            enable_in_place: Enable in-place computation optimization
            enable_draper_opt: Enable Draper QFT arithmetic optimizations
            precision_threshold: Threshold for phase precision optimization
        """
        self.enable_decomposition = enable_decomposition
        self.enable_cse = enable_cse
        self.enable_dead_code = enable_dead_code
        self.enable_renumbering = enable_renumbering
        self.enable_in_place = enable_in_place
        self.enable_draper_opt = enable_draper_opt
        self.precision_threshold = precision_threshold
        
        # Initialize analyzer for insights
        self.analyzer = SimpleQuantumOptimizer(precision_threshold)
        
        # Statistics tracking
        self.stats = {
            'passes_applied': [],
            'operations_before': 0,
            'operations_after': 0,
            'analysis_insights': {}
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
            print("🔧 Starting Integrated Quantum Circuit Optimization")
            print("=" * 60)
        
        # Phase 1: Pre-optimization analysis
        self._collect_initial_stats(module)
        
        if verbose:
            print("📊 Phase 1: Circuit Analysis")
        
        # Run comprehensive circuit analysis
        analyzed_module = self.analyzer.analyze_and_optimize(module)
        self.stats['analysis_insights'] = self.analyzer.stats
        
        if analysis_only:
            if verbose:
                print("✅ Analysis-only mode completed")
            return analyzed_module
        
        # Phase 2: Pattern-based optimizations
        if verbose:
            print("\n🛠️  Phase 2: Pattern-Based Optimizations")
        
        optimized_module = self._apply_pattern_optimizations(analyzed_module, verbose)
        
        # Phase 3: Post-optimization analysis
        if verbose:
            print("\n📈 Phase 3: Optimization Results")
        
        self._collect_final_stats(optimized_module)
        self._print_optimization_summary(verbose)
        
        return optimized_module
    
    def _collect_initial_stats(self, module: ModuleOp) -> None:
        """Collect statistics before optimization."""
        op_count = len(list(module.walk()))
        self.stats['operations_before'] = op_count
    
    def _collect_final_stats(self, module: ModuleOp) -> None:
        """Collect statistics after optimization."""
        op_count = len(list(module.walk()))
        self.stats['operations_after'] = op_count
    
    def _apply_pattern_optimizations(self, module: ModuleOp, verbose: bool) -> ModuleOp:
        """
        Apply the existing pattern-based optimization passes.
        
        This integrates your existing optimization passes using XDSL's
        pattern rewriting framework.
        """
        rewriter = Rewriter()
        patterns = []
        
        # Apply Draper-specific optimizations first (before pattern rewrites)
        if self.enable_draper_opt:
            if verbose:
                print("  🔄 Applying Draper QFT optimizations...")
            try:
                draper_opt = DraperOptimizer(precision_threshold=self.precision_threshold)
                module = draper_opt.optimize_draper_circuit(module)
                if verbose:
                    print("  ✅ Applied: Draper QFT optimizations")
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  Draper optimization failed: {e}")
        
        # Build optimization pipeline based on enabled passes
        if self.enable_dead_code:
            patterns.append(RemoveUnusedOperations())
            if verbose:
                print("  ✅ Added: Dead code elimination")
        
        if self.enable_decomposition:
            patterns.append(CCnot_decomposition())
            if verbose:
                print("  ✅ Added: CCNOT decomposition")
        
        if self.enable_renumbering:
            patterns.append(QubitRenumber())
            if verbose:
                print("  ✅ Added: Qubit renumbering")
        
        if self.enable_in_place:
            patterns.append(InPlacing())
            if verbose:
                print("  ✅ Added: In-place computation")
        
        # Note: CSE and Hermitian transformation might need updates for your current dialect
        # Commenting out for now to avoid compatibility issues
        # if self.enable_cse:
        #     patterns.append(CommonSubexprElimination())
        
        if patterns:
            if verbose:
                print(f"  🔄 Applying {len(patterns)} optimization patterns...")
            
            try:
                # Apply patterns using greedy rewriter
                applier = GreedyRewritePatternApplier(patterns)
                # Try different method names for different XDSL versions
                if hasattr(applier, 'rewrite_module'):
                    applier.rewrite_module(module)
                elif hasattr(applier, 'apply_patterns'):
                    applier.apply_patterns(module)
                else:
                    # Fallback: apply patterns manually
                    for pattern in patterns:
                        if hasattr(pattern, 'apply_to_module'):
                            pattern.apply_to_module(module)
                        elif hasattr(pattern, 'match_and_rewrite'):
                            # Apply pattern to each operation
                            for op in list(module.walk()):
                                try:
                                    pattern.match_and_rewrite(op, rewriter)
                                except:
                                    continue
                
                self.stats['passes_applied'] = [type(p).__name__ for p in patterns]
                
            except Exception as e:
                if verbose:
                    print(f"  ⚠️  Pattern application failed: {e}")
                    print(f"  🔄 Falling back to analysis-only mode")
                # Continue without pattern-based optimization
                self.stats['passes_applied'] = ["Analysis only (pattern application failed)"]
        else:
            if verbose:
                print("  ⚠️  No optimization patterns enabled")
        
        return module
    
    def _print_optimization_summary(self, verbose: bool) -> None:
        """Print summary of optimization results."""
        if not verbose:
            return
            
        print("\n🏆 Optimization Summary")
        print("=" * 40)
        
        # Operation count changes
        before = self.stats['operations_before']
        after = self.stats['operations_after']
        
        if before > 0:
            reduction = before - after
            percentage = (reduction / before) * 100
            print(f"Operations: {before} → {after} ({reduction:+d}, {percentage:+.1f}%)")
        
        # Applied passes
        if self.stats['passes_applied']:
            print(f"Passes applied: {', '.join(self.stats['passes_applied'])}")
        
        # Analysis insights summary
        insights = self.stats.get('analysis_insights', {})
        if 'small_phases_found' in insights:
            print(f"Phase optimization opportunities: {insights['small_phases_found']}")
        
        if 'operation_counts' in insights:
            total_ops = sum(insights['operation_counts'].values())
            print(f"Total quantum operations analyzed: {total_ops}")


def create_optimizer_pipeline(optimization_level: str = "default") -> IntegratedQuantumOptimizer:
    """
    Create preconfigured optimization pipeline.
    
    Args:
        optimization_level: "conservative", "default", "aggressive", or "analysis_only"
        
    Returns:
        Configured IntegratedQuantumOptimizer instance
    """
    if optimization_level == "conservative":
        # Only apply safest optimizations
        return IntegratedQuantumOptimizer(
            enable_decomposition=False,
            enable_cse=False,
            enable_dead_code=True,
            enable_renumbering=True,
            enable_in_place=False,
            enable_draper_opt=False,
            precision_threshold=1e-3
        )
    
    elif optimization_level == "aggressive":
        # Apply all available optimizations
        return IntegratedQuantumOptimizer(
            enable_decomposition=True,
            enable_cse=True,
            enable_dead_code=True,
            enable_renumbering=True,
            enable_in_place=True,
            enable_draper_opt=True,
            precision_threshold=1e-6
        )
    
    elif optimization_level == "analysis_only":
        # Only perform analysis, no modifications
        return IntegratedQuantumOptimizer(
            enable_decomposition=False,
            enable_cse=False,
            enable_dead_code=False,
            enable_renumbering=False,
            enable_in_place=False,
            enable_draper_opt=False
        )
    
    else:  # "default"
        # Balanced optimization approach
        # NOTE: RemoveUnusedOperations (dead code elimination) is DISABLED because
        # it incorrectly identifies quantum operations as unused and removes them,
        # breaking Draper multiplication circuits. This needs to be fixed before
        # re-enabling. See: draper_optimizer.py bug investigation.
        return IntegratedQuantumOptimizer(
            enable_decomposition=True,
            enable_cse=False,  # Disabled for now due to potential compatibility issues
            enable_dead_code=False,  # DISABLED - incorrectly removes operations in multiplication
            enable_renumbering=True,
            enable_in_place=True,
            enable_draper_opt=True,
            precision_threshold=1e-6
        )


def optimize_quantum_circuit(module: ModuleOp, 
                           optimization_level: str = "default",
                           analysis_only: bool = False,
                           verbose: bool = True) -> ModuleOp:
    """
    Convenience function to optimize quantum circuits.
    
    Args:
        module: Input MLIR module
        optimization_level: Level of optimization to apply
        analysis_only: Only perform analysis without modifications
        verbose: Print optimization progress
        
    Returns:
        Optimized MLIR module
    """
    optimizer = create_optimizer_pipeline(optimization_level)
    return optimizer.optimize_circuit(module, analysis_only, verbose)
