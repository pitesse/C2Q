// Test multiplication with new variable (int c = a * b)
int main()
{
    int a = 2;
    int b = 3;
    int c = a * b;  // Should create new register for c, result = 6
    return 0;
}
