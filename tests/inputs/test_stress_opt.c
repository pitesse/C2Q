// Stress Test: Designed to maximize optimization gains
// This test simulates unrolled loops and cancelling operations
// to demonstrate the power of iterative optimization

int main() {
    int a = 0;
    int step = 1; // Use a variable so the register 'step' is reused for all additions
    
    // Simulate Unrolled Loop: 4x Addition
    // Since 'step' is the same register, the optimizer should merge these 4 arithmetic blocks
    // into a single effective addition of 4 (reducing depth by ~4x).
    a = a + step;
    a = a + step;
    a = a + step;
    a = a + step;
    
    int cancel = 5;
    // Simulate Cancellation: +5 then -5
    // These should completely annihilate each other (QFTs merge, phases cancel to 0).
    a = a + cancel;
    a = a - cancel;
    
    return a; // Expected result: 4
}
