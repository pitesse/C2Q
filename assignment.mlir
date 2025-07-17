builtin.module {
  "quantum.func"() ({
    %q0_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %q0_1 = "quantum.OnQubit_not"(%q0_0) {index = 0 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q0_2 = "quantum.OnQubit_not"(%q0_1) {index = 2 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q1_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %q1_1 = "quantum.OnQubit_not"(%q1_0) {index = 1 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q1_2 = "quantum.OnQubit_not"(%q1_1) {index = 3 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
    %q2_1 = "quantum.OnQubit_not"(%q2_0) {index = 0 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_2 = "quantum.OnQubit_not"(%q2_1) {index = 4 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_3 = "quantum.OnQubit_not"(%q2_2) {index = 5 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_4 = "quantum.OnQubit_not"(%q2_3) {index = 6 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_5 = "quantum.OnQubit_not"(%q2_4) {index = 7 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_6 = "quantum.OnQubit_not"(%q2_5) {index = 8 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_7 = "quantum.OnQubit_not"(%q2_6) {index = 9 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_8 = "quantum.OnQubit_not"(%q2_7) {index = 10 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_9 = "quantum.OnQubit_not"(%q2_8) {index = 11 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_10 = "quantum.OnQubit_not"(%q2_9) {index = 12 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_11 = "quantum.OnQubit_not"(%q2_10) {index = 13 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_12 = "quantum.OnQubit_not"(%q2_11) {index = 14 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_13 = "quantum.OnQubit_not"(%q2_12) {index = 15 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_14 = "quantum.OnQubit_not"(%q2_13) {index = 16 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_15 = "quantum.OnQubit_not"(%q2_14) {index = 17 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_16 = "quantum.OnQubit_not"(%q2_15) {index = 18 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_17 = "quantum.OnQubit_not"(%q2_16) {index = 19 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_18 = "quantum.OnQubit_not"(%q2_17) {index = 20 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_19 = "quantum.OnQubit_not"(%q2_18) {index = 21 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_20 = "quantum.OnQubit_not"(%q2_19) {index = 22 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_21 = "quantum.OnQubit_not"(%q2_20) {index = 23 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_22 = "quantum.OnQubit_not"(%q2_21) {index = 24 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_23 = "quantum.OnQubit_not"(%q2_22) {index = 25 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_24 = "quantum.OnQubit_not"(%q2_23) {index = 26 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_25 = "quantum.OnQubit_not"(%q2_24) {index = 27 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_26 = "quantum.OnQubit_not"(%q2_25) {index = 28 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_27 = "quantum.OnQubit_not"(%q2_26) {index = 29 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_28 = "quantum.OnQubit_not"(%q2_27) {index = 30 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q2_29 = "quantum.OnQubit_not"(%q2_28) {index = 31 : i32} : (vector<32xi1>) -> vector<32xi1>
    %q3_0 = "quantum.init"() {type = vector<32xi1>, value = 0 : i32} : () -> vector<32xi1>
  }) {func_name = "main"} : () -> ()
}
