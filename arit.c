int operations(int a, int b)
{
    int c, d;
    a = a + 1;
    b = b + 1;
    c = a + b;
    d = a - b;

    return a + b;
}

int main()
{
    int a = 5;
    int b = 10;
    int result = operations(a, b);
    // printf("Result: %d\n", result);
    return 0;
}
