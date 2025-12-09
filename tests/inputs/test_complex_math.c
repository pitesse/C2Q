// test_complex_math.c
// Complex arithmetic: multiplication followed by addition
// Expected: (3 * 2) + 2 = 6 + 2 = 8

int main() {
    int a = 3;
    int b = 2;
    
    // Step 1: res = a * b = 3 * 2 = 6
    // Step 2: res = res + b = 6 + 2 = 8
    int res = a * b;
    res = res + b;
    
    return res;  // Expected: 8
}
