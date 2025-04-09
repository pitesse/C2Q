builtin.module {
  "quantum.comment"() {comment_text = "Begin main function"} : () -> ()
  "quantum.func"() ({
    "quantum.comment"() {comment_text = "Declare variable: a"} : () -> ()
    "quantum.comment"() {comment_text = "Initialize a with expression"} : () -> ()
    "quantum.comment"() {comment_text = "Direct number initialization: 5.0"} : () -> ()
    "quantum.comment"() {comment_text = "Creating qubit with name: q0_0"} : () -> ()
    %q0_0 = "quantum.init"() {type = i32, value = false} : () -> i1
    %0 = "quantum.not"(%q0_0) : (i1) -> i1
    "quantum.comment"() {comment_text = "Declare variable: b"} : () -> ()
    "quantum.comment"() {comment_text = "Initialize b with expression"} : () -> ()
    "quantum.comment"() {comment_text = "Direct number initialization: 10.0"} : () -> ()
    "quantum.comment"() {comment_text = "Creating qubit with name: q32_0"} : () -> ()
    %q32_0 = "quantum.init"() {type = i32, value = false} : () -> i1
    %1 = "quantum.not"(%q32_0) : (i1) -> i1
    "quantum.comment"() {comment_text = "Declare variable: c"} : () -> ()
    "quantum.comment"() {comment_text = "Default initialization of c to |0\u27e9"} : () -> ()
    "quantum.comment"() {comment_text = "Creating qubit with name: q64_0"} : () -> ()
    %q64_0 = "quantum.init"() {type = i32, value = false} : () -> i1
    "quantum.comment"() {comment_text = "Process return value expression"} : () -> ()
    "quantum.comment"() {comment_text = "Initialize number literal: 0.0"} : () -> ()
    "quantum.comment"() {comment_text = "Creating qubit with name: q96_0"} : () -> ()
    %q96_0 = "quantum.init"() {type = i32, value = false} : () -> i1
    "quantum.comment"() {comment_text = "End main function"} : () -> ()
  }) {func_name = "main"} : () -> ()
}
