// Optimization Showcase Test Case
// This test is designed to trigger multiple optimization passes:
// 1. Dead Code Elimination (unused temp variable)
// 2. Qubit Renumbering/Reuse (redundant initialization)
// 3. Phase Precision Optimization (aggressive threshold)

int main() {
    int a = 5;
    int b = 3;
    
    // 1. Unused computation (Dead Code Elimination target)
    int temp = a + b; 
    
    // 2. Redundant initialization (to trigger Qubit Reuse/Renumbering)
    int c = 10;
    
    // 3. Actual computation
    int result = a * b;
    
    return result; 
}
