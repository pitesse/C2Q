int main()
{
    int a = 5;
    int b = 10;
    a = a + b;    // This should overwrite register 'a'
    int c = a + b;  // This should create new register 'c'
    return 0;
}
