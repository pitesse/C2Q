builtin.module {
  "quantum.func"() ({
    %q0_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q0_1 = "quantum.OnQubit_not"(%q0_0) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q1_1 = "quantum.OnQubit_not"(%q1_0) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q2_1 = "quantum.OnQubit_not"(%q2_0) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_2 = "quantum.OnQubit_not"(%q2_1) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_3 = "quantum.OnQubit_not"(%q2_2) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_4 = "quantum.OnQubit_not"(%q2_3) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
  }) {func_name = "main"} : () -> ()
}
