# C2Q Compiler - Development Roadmap

**Priority Order**: Critical fix → AST optimizations (highest impact) → Quantum optimizations → Validation/Testing → Future enhancements

---

## 🔴 WEEK 1: Fix Core Functionality

### 1. Fix Quantum Multiplication Algorithm
**Status**: 🔴 CRITICAL - Blocking everything else

**Problem**: 
- Current implementation uses simplified controlled operations
- Ignores control bits (always adds all shifted values)
- Doubly-controlled gates simplified to singly-controlled
- Produces incorrect results

**Solution**:
- Implement proper Toffoli gates (CCNOT) for doubly-controlled additions
- Use conditional quantum addition based on multiplier bits
- Consider algorithms:
  - Proper controlled QFT-based multiplication (Draper)
  - Ruiz-Perez algorithm for efficient multiplication
  - Classical multiplication with quantum adders

**References**: Draper's original paper, Vedral et al. quantum arithmetic circuits

**Timeline**: Week 1 | **Effort**: High | **Impact**: ✅ Correctness

---

## 🔥 WEEK 2: Quick Wins (Easy High-Impact Optimizations)

These optimizations happen **before** quantum gate generation, avoiding unnecessary circuits entirely.

### 2. Constant Folding & Propagation
**Status**: 🔥 Easiest, biggest impact

**Problem**: `int c = 3 + 5;` generates 130+ quantum gates when result is known at compile time

**Solution**:
- Add constant evaluation pass in AST
- Track constant values through symbol table  
- Replace compile-time expressions with results

**Impact**: **90% gate reduction** for constant expressions
- Example: `3 + 5` → just initialize result to `8` (3 gates instead of 130!)

**Implementation**:
- Add `evaluate_constant()` method to AST nodes
- Modify `QuantumIRGen` to check for constants before generating QFT circuits

**Timeline**: Week 2 | **Effort**: Low | **Impact**: 🔥 90%

### 3. Zero Operand Detection & Identity Operations
**Status**: 🔥 Trivial to implement, 30-40% savings

**Problem**: `a + 0` still runs full QFT algorithm (60+ gates)

**Solution**:
- Detect zero operands at IR generation time
- Skip QFT/IQFT for identity operations:
  - `a + 0 = a` (just copy register)
  - `a * 1 = a` (just copy register)
  - `a * 0 = 0` (just initialize to zero)

**Impact**: **40% gate reduction** when operand is zero

**Implementation**:
```python
# In ir_gen.py
if is_constant(operand) and get_value(operand) == 0:
    # Skip QFT, just copy or initialize
```

**Timeline**: Week 2 | **Effort**: Low | **Impact**: 🔥 40%

### 4. Enable Existing Disabled Optimizations
**Status**: 🟢 Easy wins - already implemented, just disabled

**Quick fixes**:
- ✅ Enable **Hermitian gate cancellation**: H·H = I, X·X = I
- ✅ Enable **Common Subexpression Elimination** (CSE)
- ✅ Activate `DraperOptimizer` passes

**Impact**: 10-15% additional reduction with zero new code

**Timeline**: Week 2 | **Effort**: Low | **Impact**: 10-15%

---

## 🔥 WEEK 3: High-Impact Classical Optimizations

### 5. Algebraic Simplification
**Status**: 🔥 Medium effort, 30% typical savings

**Optimizations**:
- **Strength reduction**: `a * 2` → `a << 1` (shift, not multiply)
- **Reassociation**: `(a + 3) + 5` → `a + 8` (fold constants)
- **Commutativity**: `a + 5` same as `5 + a` (optimize order)

**Impact**: Reduces complex operations to simpler ones (30% reduction)

**Implementation**: Add algebraic rewrite rules in AST or new IR layer

**Timeline**: Week 3 | **Effort**: Medium | **Impact**: 🔥 30%

### 6. Value Range Analysis
**Status**: 🟡 Enables dynamic bit-width and partial QFT

**Purpose**:
```c
int a = 3;    // Range: [3, 3]
int b = 5;    // Range: [5, 5] 
int c = a + b;  // Range: [8, 8] → needs only 4 bits, not 8!
```

**Benefits**:
- Determine exact bit-width needed per operation
- Use 8-bit as base minimum
- Reduces qubit count for small numbers
- **Enables Task #10 (Partial QFT optimization)**

**Implementation**: Track min/max values through symbol table, propagate through expressions

**Timeline**: Week 3 | **Effort**: Medium | **Impact**: 🔥 30% + enables Task #10

### 7. Dead Store Elimination & Copy Propagation
**Status**: 🟡 Standard compiler optimization

**Dead stores**:
```c
int x = 3;   // Dead if x never read before next assignment
x = 5;       // Overwrites without reading
```

**Copy propagation**:
```c
int a = 5;
int b = a;   // b is alias of a
int c = b + 3;  // can use 'a' directly, skip 'b'
```

**Impact**: Eliminates unnecessary registers (25-35% qubit reduction)

**Timeline**: Week 3 | **Effort**: Medium | **Impact**: 25-35% qubits

---

## 🟡 WEEK 4: Validation & Quantum-Level Optimizations

### 8. Fix and Update Validation Framework
**Status**: 🟡 Blocked by Task #1 (multiplication fix)

**Current State**: 
- `backend/validate.py` exists but outdated
- Imports from non-existent `main` module
- Doesn't work with current architecture

**Required**:
1. Update imports to use `C2Q` modules
2. Adapt to OnQubit operation format
3. Create truth table test cases for addition, subtraction, multiplication
4. Integrate with test suite
5. Validate optimization passes preserve correctness
6. **Add optimization impact reporting**:
   - Show before/after metrics for each optimization pass
   - Display: gate count reduction, depth reduction, qubit count
   - Example output:
     ```
     Original circuit: 134 gates, depth 48, 24 qubits
     After constant folding: 8 gates (-94%), depth 3 (-94%), 8 qubits (-67%)
     After phase precision: 7 gates (-1%), depth 3 (0%), 8 qubits (0%)
     After dead code elim: 5 gates (-29%), depth 2 (-33%), 8 qubits (0%)
     Total reduction: 96% gates, 96% depth, 67% qubits
     ```
   - Verify correctness at each optimization stage (not just final result)

**Why important**: 
- Ensures correctness before deploying on real quantum hardware
- Provides visibility into which optimizations are effective
- Catches bugs introduced by optimization passes

**Blocked by**: Must fix multiplication first (Task #1)

**Timeline**: Week 4 | **Effort**: Medium | **Impact**: ✅ Correctness

### 9. Create Automated Test Suite
**Status**: 🟡 Depends on Task #8 (validate.py must work first)

**Current State**:
- Test files exist in `tests/inputs/` (13 C programs)
- No automated test runner (manual testing only)
- No CI/CD integration

**Test Types Needed**:

**Integration Tests** (verify end-to-end correctness):
```python
def test_addition_correctness():
    """Compile C code → quantum circuit → simulate → verify result"""
    result = compile_and_validate("test_add_new.c")
    assert result["c"] == 8  # 3 + 5 = 8
```

**Regression Tests** (verify optimizations preserve correctness):
```python
def test_optimization_preserves_correctness():
    """Ensure optimized circuit produces same result as unoptimized"""
    unopt = compile_and_validate("test.c", optimize=False)
    opt = compile_and_validate("test.c", optimize=True)
    assert unopt == opt  # Same result, fewer gates
```

**Unit Tests** (test individual compiler components):
```python
def test_lexer_tokenizes_correctly():
    tokens = CLexer.tokenize("int a = 5;")
    assert tokens == [INT, IDENTIFIER, EQUALS, NUMBER, SEMICOLON]

def test_parser_builds_ast():
    ast = CParser.parse("int a = 5;")
    assert isinstance(ast, VarDeclExprAST)
```

**Implementation**:
1. Create `tests/test_compiler.py` with pytest
2. Use `validate.py` to verify quantum circuits produce correct classical results
3. Test all 13 input files for correctness
4. Add regression tests for each optimization pass
5. Integrate with GitHub Actions for CI/CD

**Why after validate.py**:
- Need working validation to verify quantum circuit correctness
- Can't write meaningful tests until multiplication works (Task #1)
- Formal test suite automates what's currently manual testing

**Timeline**: Week 4 | **Effort**: Medium | **Impact**: ✅ Testing infrastructure

### 10. Partial QFT Optimization
**Status**: 🟡 High impact quantum optimization (depends on Task #6)

**Idea**: When operands are small, apply QFT only to used bits

**Example**: `3 + 5` max result is 8
- Current: QFT on all 8 bits (28 Hadamard + 28 phase gates)
- Optimized: QFT on only 4 bits (10 Hadamard + 6 phase gates)

**Impact**: 50% reduction in Hadamard and phase gates

**Implementation**: Requires value range analysis (Task #6) to know bit usage

**Timeline**: Week 4 | **Effort**: Medium | **Impact**: 50%

### 11. Phase Rotation Consolidation
**Status**: 🟡 Medium impact

**Optimization**: Merge multiple phase rotations on same qubit pair
- `cp(θ₁, c, t); cp(θ₂, c, t)` → `cp(θ₁+θ₂, c, t)`

**Impact**: 20% reduction in phase gates

**Implementation**: Pattern matching pass in optimization pipeline

**Timeline**: Week 4 | **Effort**: Low | **Impact**: 20%

### 12. Commutation-Based Gate Scheduling
**Status**: 🟢 Reduces depth, not gate count

**Idea**: Phase gates on different qubits commute → reorder for parallelism

**Impact**: Reduces circuit **depth** (better for NISQ devices), not gate count

**Timeline**: Week 4 | **Effort**: Medium | **Impact**: Depth reduction

### 13. SWAP Network Optimization
**Status**: 🟢 Lower priority

**Idea**: 
- QFT needs SWAPs for bit reversal
- Track qubit permutations virtually
- Apply SWAPs only when necessary

**Impact**: 10% reduction in SWAP gates

**Timeline**: Week 4 | **Effort**: High | **Impact**: 10%

---

## 🟢 FUTURE ENHANCEMENTS

### 14. Dynamic Bit-Width Sizing
**Status**: 🟢 Enabled by Task #6 (value range analysis)

**Purpose**: Dynamically allocate qubits based on operand size
- `int a = 5;` → 8 bits (base minimum)
- `int b = 1000;` → 10 bits (need more)

**Benefits**: Efficient resource utilization, fewer qubits for small numbers

### 15. Overflow Detection
**Status**: 🟢 Nice to have

**Options**:
1. Compile-time warning for constant expressions
2. Runtime quantum overflow flag (extra qubit)
3. Automatic bit-width expansion

### 16. Extended C Language Support
**Status**: 🟢 Future

- Control flow: `if`, `else`, `while`, `for`
- Comparison operators: `<`, `>`, `==`, `!=`
- Logical operators: `&&`, `||`, `!`
- Bitwise operators: `&`, `|`, `^`, `<<`, `>>`
- Arrays and pointers

### 17. Alternative Arithmetic Algorithms
**Status**: 💡 Research

- Ripple-carry adder (simpler, more gates)
- Carry-lookahead adder (parallel, complex)
- Different multiplication approaches
- Division/modulo operations

### 18. Hardware-Specific Optimizations
**Status**: 💡 Future

- Gate set translation for specific quantum computers
- Qubit topology mapping  
- Error mitigation strategies
- Noise-aware compilation

---

## 📊 Expected Impact Summary

| Task | Type | Effort | Impact | Timeline |
|------|------|--------|--------|----------|
| #1 Multiplication fix | Critical | High | ✅ Correctness | Week 1 |
| #2 Constant folding | Classical | Low | 🔥 90% | Week 2 |
| #3 Zero detection | Classical | Low | 🔥 40% | Week 2 |
| #4 Enable disabled opts | Quantum | Low | 10-15% | Week 2 |
| #5 Algebraic simplify | Classical | Medium | 🔥 30% | Week 3 |
| #6 Value range | Classical | Medium | 🔥 30% | Week 3 |
| #7 Dead store elim | Classical | Medium | 25-35% qubits | Week 3 |
| #8 Validation | Testing | Medium | ✅ Correctness | Week 4 |
| #9 Test suite | Testing | Medium | ✅ CI/CD | Week 4 |
| #10 Partial QFT | Quantum | Medium | 50% | Week 4 |
| #11 Phase consolidation | Quantum | Low | 20% | Week 4 |
| #12 Gate scheduling | Quantum | Medium | Depth ↓ | Week 4 |
| #13 SWAP optimization | Quantum | High | 10% | Week 4 |

**Total expected reduction**: 70-90% gate reduction for typical programs!

---

## 🧭 Implementation Strategy

### Phase 1 (Week 1): 🔴 Critical Foundation
**Task #1**: Fix multiplication algorithm
- Research Draper/Toffoli gates
- Test with `test_mult_2x3.c` (should output 6)
- **Blocks everything else**

### Phase 2 (Week 2): 🔥 Quick Wins
**Tasks #2, #3, #4**: Easy high-impact optimizations
- Constant folding (90% for constants)
- Zero operand detection (40% for identities)
- Enable disabled optimizations (10-15% bonus)
- **Combined: 50-70% reduction for typical code**

### Phase 3 (Week 3): 🔥 Classical Optimizations
**Tasks #5, #6, #7**: Deeper AST-level optimizations
- Algebraic simplification (30%)
- Value range analysis (enables Task #10)
- Dead store elimination (25-35% qubit savings)

### Phase 4 (Week 4): 🟡 Validation & Quantum Polish
**Tasks #8-#13**: Testing + final quantum optimizations
- Fix validate.py → verify correctness
- Add pytest suite → automate testing
- Partial QFT (50% gates)
- Phase consolidation (20% gates)
- Gate scheduling & SWAP optimization

### Phase 5 (Future): 🟢 Enhancements
**Tasks #14-#18**: Long-term improvements
- Dynamic bit-width
- Overflow detection
- Extended C support
- Alternative algorithms
- Hardware-specific optimizations

---

## 🎯 Key Insights

### Why This Order?
1. **Fix multiplication first** → Can't test/optimize broken code
2. **Classical opts before quantum** → Preventing gate generation >> optimizing generated gates
3. **Validation after basics work** → Need correct multiplication to validate
4. **Testing last** → Need validation framework to write meaningful tests

### The Big Win
**Classical optimizations (Tasks #2-#7)** provide **more value** than quantum-level opts:
- Classical: `3+5` compiled to `8` → **0 quantum gates generated** (100% reduction!)
- Quantum: Generate 130 gates, optimize to 127 → 2.3% reduction

**Avoid generating unnecessary gates > optimizing gates after generation**

---

## 📝 Notes

- **Priority Legend**: 🔴 Critical | 🔥 High Impact | 🟡 Important | 🟢 Nice to have | 💡 Research
- Update this file as tasks are completed
- Tasks are numbered 1-18 in execution order
