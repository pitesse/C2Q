/**
 * Overflow Test Case for 8-bit Quantum Arithmetic
 * 
 * Tests modular arithmetic behavior: 255 + 1 = 0 (mod 256)
 * This verifies that the quantum adder correctly wraps around.
 */

int main() {
    int a = 255;  // Maximum 8-bit unsigned value
    int b = 1;    // Adding 1 causes overflow
    int res = a + b;  // Should wrap to 0 (mod 256)
    return res;
}
