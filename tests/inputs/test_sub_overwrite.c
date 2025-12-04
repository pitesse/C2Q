// Test subtraction with register overwrite (a = a - b)
int main()
{
    int a = 8;
    int b = 3;
    a = a - b;  // Should update a's register, result = 5
    return 0;
}
