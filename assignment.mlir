builtin.module {
  "quantum.comment"() {comment_text = "begin main function"} : () -> ()
  "quantum.func"() ({
    "quantum.comment"() {comment_text = "declare variable: a"} : () -> ()
    "quantum.comment"() {comment_text = "initialize a with expression"} : () -> ()
    "quantum.comment"() {comment_text = "direct number initialization: 5.0"} : () -> ()
    "quantum.comment"() {comment_text = "initialize number literal: 5.0"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q0_0 with 32 qubits"} : () -> ()
    %q0_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    "quantum.comment"() {comment_text = "encoding value 5 in binary across qubits"} : () -> ()
    "quantum.comment"() {comment_text = "flipping bit 0 for value 5"} : () -> ()
    "quantum.comment"() {comment_text = "extracting qubit 0 from register q0_0"} : () -> ()
    %q0_0[0] = "quantum.extract_bit"(%q0_0) {index = 0 : i32} : (vector<32xi1>) -> i1
    %0 = "quantum.not"(%q0_0[0]) : (i1) -> i1
    "quantum.comment"() {comment_text = "setting qubit 0 in register q0_0"} : () -> ()
    %q0_1 = "quantum.insert_bit"(%q0_0, %0) {index = 0 : i32} : (vector<32xi1>, i1) -> vector<32xi1>
    "quantum.comment"() {comment_text = "flipping bit 2 for value 5"} : () -> ()
    "quantum.comment"() {comment_text = "extracting qubit 2 from register q0_1"} : () -> ()
    %q0_1[2] = "quantum.extract_bit"(%q0_1) {index = 2 : i32} : (vector<32xi1>) -> i1
    %1 = "quantum.not"(%q0_1[2]) : (i1) -> i1
    "quantum.comment"() {comment_text = "setting qubit 2 in register q0_1"} : () -> ()
    %q0_3 = "quantum.insert_bit"(%q0_1, %1) {index = 2 : i32} : (vector<32xi1>, i1) -> vector<32xi1>
    "quantum.comment"() {comment_text = "updated register to version: q0_3"} : () -> ()
    "quantum.comment"() {comment_text = "binary encoding complete for 5.0"} : () -> ()
    "quantum.comment"() {comment_text = "declare variable: b"} : () -> ()
    "quantum.comment"() {comment_text = "initialize b with expression"} : () -> ()
    "quantum.comment"() {comment_text = "direct number initialization: 10.0"} : () -> ()
    "quantum.comment"() {comment_text = "initialize number literal: 10.0"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q1_0 with 32 qubits"} : () -> ()
    %q1_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    "quantum.comment"() {comment_text = "encoding value 10 in binary across qubits"} : () -> ()
    "quantum.comment"() {comment_text = "flipping bit 1 for value 10"} : () -> ()
    "quantum.comment"() {comment_text = "extracting qubit 1 from register q1_0"} : () -> ()
    %q1_0[1] = "quantum.extract_bit"(%q1_0) {index = 1 : i32} : (vector<32xi1>) -> i1
    %2 = "quantum.not"(%q1_0[1]) : (i1) -> i1
    "quantum.comment"() {comment_text = "setting qubit 1 in register q1_0"} : () -> ()
    %q1_1 = "quantum.insert_bit"(%q1_0, %2) {index = 1 : i32} : (vector<32xi1>, i1) -> vector<32xi1>
    "quantum.comment"() {comment_text = "flipping bit 3 for value 10"} : () -> ()
    "quantum.comment"() {comment_text = "extracting qubit 3 from register q1_1"} : () -> ()
    %q1_1[3] = "quantum.extract_bit"(%q1_1) {index = 3 : i32} : (vector<32xi1>) -> i1
    %3 = "quantum.not"(%q1_1[3]) : (i1) -> i1
    "quantum.comment"() {comment_text = "setting qubit 3 in register q1_1"} : () -> ()
    %q1_3 = "quantum.insert_bit"(%q1_1, %3) {index = 3 : i32} : (vector<32xi1>, i1) -> vector<32xi1>
    "quantum.comment"() {comment_text = "updated register to version: q1_3"} : () -> ()
    "quantum.comment"() {comment_text = "binary encoding complete for 10.0"} : () -> ()
    "quantum.comment"() {comment_text = "declare variable: c"} : () -> ()
    "quantum.comment"() {comment_text = "initialize c with expression"} : () -> ()
    "quantum.comment"() {comment_text = "initializing with binary expression"} : () -> ()
    "quantum.comment"() {comment_text = "perform quantum addition"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q2_0 with 32 qubits"} : () -> ()
    %q2_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    "quantum.comment"() {comment_text = "process return value expression"} : () -> ()
    "quantum.comment"() {comment_text = "initialize number literal: 0.0"} : () -> ()
    "quantum.comment"() {comment_text = "creating register q3_0 with 32 qubits"} : () -> ()
    %q3_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    "quantum.comment"() {comment_text = "end main function"} : () -> ()
  }) {func_name = "main"} : () -> ()
}
