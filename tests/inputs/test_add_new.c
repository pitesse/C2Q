// Test addition with new variable (int c = a + b)
int main()
{
    int a = 3;
    int b = 5;
    int c = a + b;  // Should create new register for c, result = 8
    return c;
}
