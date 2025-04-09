builtin.module {
  %0 = "quantum.init"() {type = i1, value = false, comment = "// Begin main function"} : () -> i1
  "quantum.func"() ({
    %1 = "quantum.init"() {type = i1, value = false, comment = "// Declare variable: a"} : () -> i1
    %2 = "quantum.init"() {type = i32, value = false} : () -> i1
    %3 = "quantum.init"() {type = i1, value = false, comment = "// Initialize a with value"} : () -> i1
    %4 = "quantum.init"() {type = i1, value = false, comment = "// Direct number initialization: 5.0"} : () -> i1
    %5 = "quantum.not"(%2) : (i1) -> i1
    %6 = "quantum.init"() {type = i1, value = false, comment = "// Declare variable: b"} : () -> i1
    %7 = "quantum.init"() {type = i32, value = false} : () -> i1
    %8 = "quantum.init"() {type = i1, value = false, comment = "// Initialize b with value"} : () -> i1
    %9 = "quantum.init"() {type = i1, value = false, comment = "// Direct number initialization: 10.0"} : () -> i1
    %10 = "quantum.not"(%7) : (i1) -> i1
    %11 = "quantum.init"() {type = i1, value = false, comment = "// Binary operation: a + b"} : () -> i1
    %12 = "quantum.init"() {type = i1, value = false, comment = "// Perform quantum addition"} : () -> i1
    %13 = "quantum.h"(%5) : (i1) -> i1
    %14 = "quantum.cnot"(%13, %10) : (i1, i1) -> i1
    %15 = "quantum.init"() {type = i1, value = false} : () -> i1
    %16 = "quantum.ccnot"(%13, %14, %15) : (i1, i1, i1) -> i1
    %17 = "quantum.init"() {type = i1, value = false, comment = "// Binary operation: b = expression"} : () -> i1
    %18 = "quantum.init"() {type = i1, value = false, comment = "// Assignment to variable: b"} : () -> i1
    %19 = "quantum.init"() {type = i1, value = false, comment = "// Binary operation: b - a"} : () -> i1
    %20 = "quantum.init"() {type = i1, value = false, comment = "// Perform quantum subtraction"} : () -> i1
    %21 = "quantum.not"(%5) : (i1) -> i1
    %22 = "quantum.h"(%10) : (i1) -> i1
    %23 = "quantum.cnot"(%22, %21) : (i1, i1) -> i1
    %24 = "quantum.init"() {type = i1, value = false} : () -> i1
    %25 = "quantum.ccnot"(%22, %23, %24) : (i1, i1, i1) -> i1
    %26 = "quantum.init"() {type = i1, value = false, comment = "// Process return value expression"} : () -> i1
    %27 = "quantum.init"() {type = i1, value = false, comment = "// Initialize number literal: 0.0"} : () -> i1
    %28 = "quantum.init"() {type = i32, value = false} : () -> i1
    %29 = "quantum.init"() {type = i1, value = false, comment = "// End main function"} : () -> i1
  }) {func_name = "main"} : () -> ()
}
