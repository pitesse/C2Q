// Test subtraction with new variable (int c = a - b)
int main()
{
    int a = 8;
    int b = 3;
    int c = a - b;  // Should create new register for c, result = 5
    return c;
}
