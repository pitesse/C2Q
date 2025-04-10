builtin.module {
  "quantum.comment"() {comment_text = "begin main function"} : () -> ()
  "quantum.func"() ({
    "quantum.comment"() {comment_text = "declare variable: a"} : () -> ()
    "quantum.comment"() {comment_text = "initialize a with expression"} : () -> ()
    "quantum.comment"() {comment_text = "direct number initialization: 5.0"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q0_0 with 32 qubits"} : () -> ()
    %q0_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %0 = "quantum.not"(%q0_0) : (vector<32xi1>) -> vector<32xi1>
    "quantum.comment"() {comment_text = "declare variable: b"} : () -> ()
    "quantum.comment"() {comment_text = "initialize b with expression"} : () -> ()
    "quantum.comment"() {comment_text = "direct number initialization: 10.0"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q1_0 with 32 qubits"} : () -> ()
    %q1_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %1 = "quantum.not"(%q1_0) : (vector<32xi1>) -> vector<32xi1>
    "quantum.comment"() {comment_text = "declare variable: c"} : () -> ()
    "quantum.comment"() {comment_text = "default initialization of c to |0\u27e9"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q2_0 with 32 qubits"} : () -> ()
    %q2_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    "quantum.comment"() {comment_text = "process return value expression"} : () -> ()
    "quantum.comment"() {comment_text = "initialize number literal: 0.0"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q3_0 with 32 qubits"} : () -> ()
    %q3_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    "quantum.comment"() {comment_text = "end main function"} : () -> ()
  }) {func_name = "main"} : () -> ()
}
