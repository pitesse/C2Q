# C2Q Compiler - Development Roadmap

**Priority Order**: Critical fix → AST optimizations (highest impact) → Quantum optimizations → Validation/Testing → Future enhancements

---


---

## 🔥 WEEK 2: Quick Wins (Easy High-Impact Optimizations)

These optimizations happen **before** quantum gate generation, avoiding unnecessary circuits entirely.


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

#

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
