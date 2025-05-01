builtin.module {
  "quantum.func"() ({
    %q0_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %q0_1 = "quantum.OnQubit_not"(%q0_0) {index = 0 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q0_2 = "quantum.OnQubit_not"(%q0_1) {index = 2 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q1_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %q1_1 = "quantum.OnQubit_not"(%q1_0) {index = 1 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q1_2 = "quantum.OnQubit_not"(%q1_1) {index = 3 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %q3_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
  }) {func_name = "main"} : () -> ()
}
