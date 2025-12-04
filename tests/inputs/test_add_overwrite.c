// Test addition with register overwrite (a = a + b)
int main()
{
    int a = 3;
    int b = 5;
    a = a + b;  // Should update a's register, result = 8
    return 0;
}
