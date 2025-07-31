// Test multiplication with register overwrite (a = a * b)
int main()
{
    int a = 2;
    int b = 3;
    a = a * b;  // Should update a's register, result = 6
    return 0;
}
