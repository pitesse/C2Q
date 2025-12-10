/**
 * @file test_mixed_add.c
 * @brief Test adding 8-bit and 16-bit numbers directly
 */

int main() {
    int a = 2;
    int b = 3;
    int c = 5;
    // First: multiply to get 16-bit result
    int product = a * b;  // 6 in 16-bit register
    // Then: add 8-bit to 16-bit
    int sum = product + c;  // Should be 11
    return sum;
}
