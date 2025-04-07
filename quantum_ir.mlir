builtin.module {
  %0 = "quantum.init"() {type = i1, value = false, comment = "// Begin main function"} : () -> i1
  "quantum.func"() ({
    %1 = "quantum.init"() {type = i1, value = false, comment = "// Declare variable: a"} : () -> i1
    %2 = "quantum.init"() {type = i1, value = false} : () -> i1
    %3 = "quantum.init"() {type = i1, value = false, comment = "// Initialize a with value"} : () -> i1
    %4 = "quantum.init"() {type = i1, value = false, comment = "// Initialize number literal: 5.0"} : () -> i1
    %5 = "quantum.init"() {type = i1, value = false} : () -> i1
    %6 = "quantum.not"(%5) : (i1) -> i1
    %7 = "quantum.cnot"(%6, %2) : (i1, i1) -> i1
    %8 = "quantum.init"() {type = i1, value = false, comment = "// Declare variable: b"} : () -> i1
    %9 = "quantum.init"() {type = i1, value = false} : () -> i1
    %10 = "quantum.init"() {type = i1, value = false, comment = "// Initialize b with value"} : () -> i1
    %11 = "quantum.init"() {type = i1, value = false, comment = "// Initialize number literal: 10.0"} : () -> i1
    %12 = "quantum.init"() {type = i1, value = false} : () -> i1
    %13 = "quantum.not"(%12) : (i1) -> i1
    %14 = "quantum.cnot"(%13, %9) : (i1, i1) -> i1
    %15 = "quantum.init"() {type = i1, value = false, comment = "// Declare variable: result"} : () -> i1
    %16 = "quantum.init"() {type = i1, value = false} : () -> i1
    %17 = "quantum.init"() {type = i1, value = false, comment = "// Initialize result with value"} : () -> i1
    %18 = "quantum.cnot"(%7, %14) : (i1, i1) -> i1
    %19 = "quantum.cnot"(%18, %16) : (i1, i1) -> i1
    %20 = "quantum.init"() {type = i1, value = false, comment = "// Return from main"} : () -> i1
    %21 = "quantum.init"() {type = i1, value = false, comment = "// Initialize number literal: 0.0"} : () -> i1
    %22 = "quantum.init"() {type = i1, value = false} : () -> i1
    %23 = "quantum.init"() {type = i1, value = false, comment = "// Measure final return value"} : () -> i1
    %24 = "quantum.measure"(%22) : (i1) -> i1
    %25 = "quantum.init"() {type = i1, value = false, comment = "// End main function"} : () -> i1
  }) {func_name = "main"} : () -> ()
}
