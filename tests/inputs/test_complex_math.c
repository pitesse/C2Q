/**
 * @file test_complex_math.c
 * @brief Tests chained arithmetic operations with mixed-width registers.
 *
 * This test verifies that the compiler can handle:
 * - Multiplication (8-bit × 8-bit → 16-bit result)
 * - Addition of 16-bit result with 8-bit operand
 *
 * Expected computation: (3 * 2) + 5 = 6 + 5 = 11
 */

int main()
{
    int a = 3;
    int b = 2;
    int c = 5;
    int res = a * b; // 6 (stored in 16-bit register)
    res = res + c;   // 11 (16-bit + 8-bit → 16-bit)
    return res;
}
