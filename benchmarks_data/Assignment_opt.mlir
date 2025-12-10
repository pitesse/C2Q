builtin.module {
  "quantum.func"() ({
    %q0_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q0_1 = "quantum.OnQubit_not"(%q0_0) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_2 = "quantum.OnQubit_not"(%q0_1) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
  }) {func_name = "main"} : () -> ()
}
