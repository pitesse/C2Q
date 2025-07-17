builtin.module {
  "quantum.func"() ({
    %q0_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q0_1 = "quantum.OnQubit_not"(%q0_0) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_2 = "quantum.OnQubit_not"(%q0_1) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q1_1 = "quantum.OnQubit_not"(%q1_0) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_2 = "quantum.OnQubit_not"(%q1_1) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_3 = "quantum.OnQubit_hadamard"(%q1_2) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_4 = "quantum.OnQubit_controlled_phase"(%q1_3, %q1_3) {control_index = 1 : i32, target_index = 0 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_5 = "quantum.OnQubit_controlled_phase"(%q1_4, %q1_4) {control_index = 2 : i32, target_index = 0 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_6 = "quantum.OnQubit_controlled_phase"(%q1_5, %q1_5) {control_index = 3 : i32, target_index = 0 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_7 = "quantum.OnQubit_controlled_phase"(%q1_6, %q1_6) {control_index = 4 : i32, target_index = 0 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_8 = "quantum.OnQubit_controlled_phase"(%q1_7, %q1_7) {control_index = 5 : i32, target_index = 0 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_9 = "quantum.OnQubit_controlled_phase"(%q1_8, %q1_8) {control_index = 6 : i32, target_index = 0 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_10 = "quantum.OnQubit_controlled_phase"(%q1_9, %q1_9) {control_index = 7 : i32, target_index = 0 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_11 = "quantum.OnQubit_hadamard"(%q1_10) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_12 = "quantum.OnQubit_controlled_phase"(%q1_11, %q1_11) {control_index = 2 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_13 = "quantum.OnQubit_controlled_phase"(%q1_12, %q1_12) {control_index = 3 : i32, target_index = 1 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_14 = "quantum.OnQubit_controlled_phase"(%q1_13, %q1_13) {control_index = 4 : i32, target_index = 1 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_15 = "quantum.OnQubit_controlled_phase"(%q1_14, %q1_14) {control_index = 5 : i32, target_index = 1 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_16 = "quantum.OnQubit_controlled_phase"(%q1_15, %q1_15) {control_index = 6 : i32, target_index = 1 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_17 = "quantum.OnQubit_controlled_phase"(%q1_16, %q1_16) {control_index = 7 : i32, target_index = 1 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_18 = "quantum.OnQubit_hadamard"(%q1_17) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_19 = "quantum.OnQubit_controlled_phase"(%q1_18, %q1_18) {control_index = 3 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_20 = "quantum.OnQubit_controlled_phase"(%q1_19, %q1_19) {control_index = 4 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_21 = "quantum.OnQubit_controlled_phase"(%q1_20, %q1_20) {control_index = 5 : i32, target_index = 2 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_22 = "quantum.OnQubit_controlled_phase"(%q1_21, %q1_21) {control_index = 6 : i32, target_index = 2 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_23 = "quantum.OnQubit_controlled_phase"(%q1_22, %q1_22) {control_index = 7 : i32, target_index = 2 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_24 = "quantum.OnQubit_hadamard"(%q1_23) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_25 = "quantum.OnQubit_controlled_phase"(%q1_24, %q1_24) {control_index = 4 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_26 = "quantum.OnQubit_controlled_phase"(%q1_25, %q1_25) {control_index = 5 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_27 = "quantum.OnQubit_controlled_phase"(%q1_26, %q1_26) {control_index = 6 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_28 = "quantum.OnQubit_controlled_phase"(%q1_27, %q1_27) {control_index = 7 : i32, target_index = 3 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_29 = "quantum.OnQubit_hadamard"(%q1_28) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_30 = "quantum.OnQubit_controlled_phase"(%q1_29, %q1_29) {control_index = 5 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_31 = "quantum.OnQubit_controlled_phase"(%q1_30, %q1_30) {control_index = 6 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_32 = "quantum.OnQubit_controlled_phase"(%q1_31, %q1_31) {control_index = 7 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_33 = "quantum.OnQubit_hadamard"(%q1_32) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_34 = "quantum.OnQubit_controlled_phase"(%q1_33, %q1_33) {control_index = 6 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_35 = "quantum.OnQubit_controlled_phase"(%q1_34, %q1_34) {control_index = 7 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_36 = "quantum.OnQubit_hadamard"(%q1_35) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_37 = "quantum.OnQubit_controlled_phase"(%q1_36, %q1_36) {control_index = 7 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_38 = "quantum.OnQubit_hadamard"(%q1_37) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_39 = "quantum.OnQubit_swap"(%q1_38) {qubit1_index = 0 : i32, qubit2_index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_40 = "quantum.OnQubit_swap"(%q1_39) {qubit1_index = 1 : i32, qubit2_index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_41 = "quantum.OnQubit_swap"(%q1_40) {qubit1_index = 2 : i32, qubit2_index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_42 = "quantum.OnQubit_swap"(%q1_41) {qubit1_index = 3 : i32, qubit2_index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_43 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_42) {control_index = 0 : i32, target_index = 0 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_44 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_43) {control_index = 0 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_45 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_44) {control_index = 0 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_46 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_45) {control_index = 0 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_47 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_46) {control_index = 0 : i32, target_index = 4 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_48 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_47) {control_index = 0 : i32, target_index = 5 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_49 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_48) {control_index = 0 : i32, target_index = 6 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_50 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_49) {control_index = 0 : i32, target_index = 7 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_51 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_50) {control_index = 1 : i32, target_index = 1 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_52 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_51) {control_index = 1 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_53 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_52) {control_index = 1 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_54 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_53) {control_index = 1 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_55 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_54) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_56 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_55) {control_index = 1 : i32, target_index = 6 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_57 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_56) {control_index = 1 : i32, target_index = 7 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_58 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_57) {control_index = 2 : i32, target_index = 2 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_59 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_58) {control_index = 2 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_60 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_59) {control_index = 2 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_61 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_60) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_62 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_61) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_63 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_62) {control_index = 2 : i32, target_index = 7 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_64 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_63) {control_index = 3 : i32, target_index = 3 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_65 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_64) {control_index = 3 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_66 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_65) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_67 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_66) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_68 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_67) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_69 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_68) {control_index = 4 : i32, target_index = 4 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_70 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_69) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_71 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_70) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_72 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_71) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_73 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_72) {control_index = 5 : i32, target_index = 5 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_74 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_73) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_75 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_74) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_76 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_75) {control_index = 6 : i32, target_index = 6 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_77 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_76) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_78 = "quantum.OnQubit_controlled_phase"(%q0_2, %q1_77) {control_index = 7 : i32, target_index = 7 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_79 = "quantum.OnQubit_swap"(%q1_78) {qubit1_index = 0 : i32, qubit2_index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_80 = "quantum.OnQubit_swap"(%q1_79) {qubit1_index = 1 : i32, qubit2_index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_81 = "quantum.OnQubit_swap"(%q1_80) {qubit1_index = 2 : i32, qubit2_index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_82 = "quantum.OnQubit_swap"(%q1_81) {qubit1_index = 3 : i32, qubit2_index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_83 = "quantum.OnQubit_hadamard"(%q1_82) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_84 = "quantum.OnQubit_controlled_phase"(%q1_83, %q1_83) {control_index = 7 : i32, target_index = 6 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_85 = "quantum.OnQubit_hadamard"(%q1_84) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_86 = "quantum.OnQubit_controlled_phase"(%q1_85, %q1_85) {control_index = 7 : i32, target_index = 5 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_87 = "quantum.OnQubit_controlled_phase"(%q1_86, %q1_86) {control_index = 6 : i32, target_index = 5 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_88 = "quantum.OnQubit_hadamard"(%q1_87) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_89 = "quantum.OnQubit_controlled_phase"(%q1_88, %q1_88) {control_index = 7 : i32, target_index = 4 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_90 = "quantum.OnQubit_controlled_phase"(%q1_89, %q1_89) {control_index = 6 : i32, target_index = 4 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_91 = "quantum.OnQubit_controlled_phase"(%q1_90, %q1_90) {control_index = 5 : i32, target_index = 4 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_92 = "quantum.OnQubit_hadamard"(%q1_91) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_93 = "quantum.OnQubit_controlled_phase"(%q1_92, %q1_92) {control_index = 7 : i32, target_index = 3 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_94 = "quantum.OnQubit_controlled_phase"(%q1_93, %q1_93) {control_index = 6 : i32, target_index = 3 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_95 = "quantum.OnQubit_controlled_phase"(%q1_94, %q1_94) {control_index = 5 : i32, target_index = 3 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_96 = "quantum.OnQubit_controlled_phase"(%q1_95, %q1_95) {control_index = 4 : i32, target_index = 3 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_97 = "quantum.OnQubit_hadamard"(%q1_96) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_98 = "quantum.OnQubit_controlled_phase"(%q1_97, %q1_97) {control_index = 7 : i32, target_index = 2 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_99 = "quantum.OnQubit_controlled_phase"(%q1_98, %q1_98) {control_index = 6 : i32, target_index = 2 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_100 = "quantum.OnQubit_controlled_phase"(%q1_99, %q1_99) {control_index = 5 : i32, target_index = 2 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_101 = "quantum.OnQubit_controlled_phase"(%q1_100, %q1_100) {control_index = 4 : i32, target_index = 2 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_102 = "quantum.OnQubit_controlled_phase"(%q1_101, %q1_101) {control_index = 3 : i32, target_index = 2 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_103 = "quantum.OnQubit_hadamard"(%q1_102) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_104 = "quantum.OnQubit_controlled_phase"(%q1_103, %q1_103) {control_index = 7 : i32, target_index = 1 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_105 = "quantum.OnQubit_controlled_phase"(%q1_104, %q1_104) {control_index = 6 : i32, target_index = 1 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_106 = "quantum.OnQubit_controlled_phase"(%q1_105, %q1_105) {control_index = 5 : i32, target_index = 1 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_107 = "quantum.OnQubit_controlled_phase"(%q1_106, %q1_106) {control_index = 4 : i32, target_index = 1 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_108 = "quantum.OnQubit_controlled_phase"(%q1_107, %q1_107) {control_index = 3 : i32, target_index = 1 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_109 = "quantum.OnQubit_controlled_phase"(%q1_108, %q1_108) {control_index = 2 : i32, target_index = 1 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_110 = "quantum.OnQubit_hadamard"(%q1_109) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_111 = "quantum.OnQubit_controlled_phase"(%q1_110, %q1_110) {control_index = 7 : i32, target_index = 0 : i32, phase = -0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_112 = "quantum.OnQubit_controlled_phase"(%q1_111, %q1_111) {control_index = 6 : i32, target_index = 0 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_113 = "quantum.OnQubit_controlled_phase"(%q1_112, %q1_112) {control_index = 5 : i32, target_index = 0 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_114 = "quantum.OnQubit_controlled_phase"(%q1_113, %q1_113) {control_index = 4 : i32, target_index = 0 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_115 = "quantum.OnQubit_controlled_phase"(%q1_114, %q1_114) {control_index = 3 : i32, target_index = 0 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_116 = "quantum.OnQubit_controlled_phase"(%q1_115, %q1_115) {control_index = 2 : i32, target_index = 0 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_117 = "quantum.OnQubit_controlled_phase"(%q1_116, %q1_116) {control_index = 1 : i32, target_index = 0 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_118 = "quantum.OnQubit_hadamard"(%q1_117) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_3_1 = "quantum.OnQubit_hadamard"(%q1_2) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_4_1 = "quantum.OnQubit_controlled_phase"(%q1_3_1, %q1_3_1) {control_index = 1 : i32, target_index = 0 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_5_1 = "quantum.OnQubit_controlled_phase"(%q1_4_1, %q1_4_1) {control_index = 2 : i32, target_index = 0 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_6_1 = "quantum.OnQubit_controlled_phase"(%q1_5_1, %q1_5_1) {control_index = 3 : i32, target_index = 0 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_7_1 = "quantum.OnQubit_controlled_phase"(%q1_6_1, %q1_6_1) {control_index = 4 : i32, target_index = 0 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_8_1 = "quantum.OnQubit_controlled_phase"(%q1_7_1, %q1_7_1) {control_index = 5 : i32, target_index = 0 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_9_1 = "quantum.OnQubit_controlled_phase"(%q1_8_1, %q1_8_1) {control_index = 6 : i32, target_index = 0 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_10_1 = "quantum.OnQubit_controlled_phase"(%q1_9_1, %q1_9_1) {control_index = 7 : i32, target_index = 0 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_11_1 = "quantum.OnQubit_hadamard"(%q1_10_1) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_12_1 = "quantum.OnQubit_controlled_phase"(%q1_11_1, %q1_11_1) {control_index = 2 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_13_1 = "quantum.OnQubit_controlled_phase"(%q1_12_1, %q1_12_1) {control_index = 3 : i32, target_index = 1 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_14_1 = "quantum.OnQubit_controlled_phase"(%q1_13_1, %q1_13_1) {control_index = 4 : i32, target_index = 1 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_15_1 = "quantum.OnQubit_controlled_phase"(%q1_14_1, %q1_14_1) {control_index = 5 : i32, target_index = 1 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_16_1 = "quantum.OnQubit_controlled_phase"(%q1_15_1, %q1_15_1) {control_index = 6 : i32, target_index = 1 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_17_1 = "quantum.OnQubit_controlled_phase"(%q1_16_1, %q1_16_1) {control_index = 7 : i32, target_index = 1 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_18_1 = "quantum.OnQubit_hadamard"(%q1_17_1) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_19_1 = "quantum.OnQubit_controlled_phase"(%q1_18_1, %q1_18_1) {control_index = 3 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_20_1 = "quantum.OnQubit_controlled_phase"(%q1_19_1, %q1_19_1) {control_index = 4 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_21_1 = "quantum.OnQubit_controlled_phase"(%q1_20_1, %q1_20_1) {control_index = 5 : i32, target_index = 2 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_22_1 = "quantum.OnQubit_controlled_phase"(%q1_21_1, %q1_21_1) {control_index = 6 : i32, target_index = 2 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_23_1 = "quantum.OnQubit_controlled_phase"(%q1_22_1, %q1_22_1) {control_index = 7 : i32, target_index = 2 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_24_1 = "quantum.OnQubit_hadamard"(%q1_23_1) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_25_1 = "quantum.OnQubit_controlled_phase"(%q1_24_1, %q1_24_1) {control_index = 4 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_26_1 = "quantum.OnQubit_controlled_phase"(%q1_25_1, %q1_25_1) {control_index = 5 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_27_1 = "quantum.OnQubit_controlled_phase"(%q1_26_1, %q1_26_1) {control_index = 6 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_28_1 = "quantum.OnQubit_controlled_phase"(%q1_27_1, %q1_27_1) {control_index = 7 : i32, target_index = 3 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_29_1 = "quantum.OnQubit_hadamard"(%q1_28_1) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_30_1 = "quantum.OnQubit_controlled_phase"(%q1_29_1, %q1_29_1) {control_index = 5 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_31_1 = "quantum.OnQubit_controlled_phase"(%q1_30_1, %q1_30_1) {control_index = 6 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_32_1 = "quantum.OnQubit_controlled_phase"(%q1_31_1, %q1_31_1) {control_index = 7 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_33_1 = "quantum.OnQubit_hadamard"(%q1_32_1) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_34_1 = "quantum.OnQubit_controlled_phase"(%q1_33_1, %q1_33_1) {control_index = 6 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_35_1 = "quantum.OnQubit_controlled_phase"(%q1_34_1, %q1_34_1) {control_index = 7 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_36_1 = "quantum.OnQubit_hadamard"(%q1_35_1) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_37_1 = "quantum.OnQubit_controlled_phase"(%q1_36_1, %q1_36_1) {control_index = 7 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_38_1 = "quantum.OnQubit_hadamard"(%q1_37_1) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_39_1 = "quantum.OnQubit_swap"(%q1_38_1) {qubit1_index = 0 : i32, qubit2_index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_40_1 = "quantum.OnQubit_swap"(%q1_39_1) {qubit1_index = 1 : i32, qubit2_index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_41_1 = "quantum.OnQubit_swap"(%q1_40_1) {qubit1_index = 2 : i32, qubit2_index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_42_1 = "quantum.OnQubit_swap"(%q1_41_1) {qubit1_index = 3 : i32, qubit2_index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_43_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_42_1) {control_index = 0 : i32, target_index = 0 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_44_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_43_1) {control_index = 0 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_45_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_44_1) {control_index = 0 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_46_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_45_1) {control_index = 0 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_47_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_46_1) {control_index = 0 : i32, target_index = 4 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_48_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_47_1) {control_index = 0 : i32, target_index = 5 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_49_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_48_1) {control_index = 0 : i32, target_index = 6 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_50_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_49_1) {control_index = 0 : i32, target_index = 7 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_51_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_50_1) {control_index = 1 : i32, target_index = 1 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_52_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_51_1) {control_index = 1 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_53_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_52_1) {control_index = 1 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_54_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_53_1) {control_index = 1 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_55_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_54_1) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_56_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_55_1) {control_index = 1 : i32, target_index = 6 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_57_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_56_1) {control_index = 1 : i32, target_index = 7 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_58_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_57_1) {control_index = 2 : i32, target_index = 2 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_59_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_58_1) {control_index = 2 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_60_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_59_1) {control_index = 2 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_61_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_60_1) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_62_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_61_1) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_63_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_62_1) {control_index = 2 : i32, target_index = 7 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_64_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_63_1) {control_index = 3 : i32, target_index = 3 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_65_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_64_1) {control_index = 3 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_66_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_65_1) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_67_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_66_1) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_68_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_67_1) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_69_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_68_1) {control_index = 4 : i32, target_index = 4 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_70_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_69_1) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_71_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_70_1) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_72_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_71_1) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_73_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_72_1) {control_index = 5 : i32, target_index = 5 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_74_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_73_1) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_75_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_74_1) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_76_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_75_1) {control_index = 6 : i32, target_index = 6 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_77_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_76_1) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_78_1 = "quantum.OnQubit_controlled_phase"(%q1_118, %q1_77_1) {control_index = 7 : i32, target_index = 7 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_79_1 = "quantum.OnQubit_swap"(%q1_78_1) {qubit1_index = 0 : i32, qubit2_index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_80_1 = "quantum.OnQubit_swap"(%q1_79_1) {qubit1_index = 1 : i32, qubit2_index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_81_1 = "quantum.OnQubit_swap"(%q1_80_1) {qubit1_index = 2 : i32, qubit2_index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_82_1 = "quantum.OnQubit_swap"(%q1_81_1) {qubit1_index = 3 : i32, qubit2_index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_83_1 = "quantum.OnQubit_hadamard"(%q1_82_1) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_84_1 = "quantum.OnQubit_controlled_phase"(%q1_83_1, %q1_83_1) {control_index = 7 : i32, target_index = 6 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_85_1 = "quantum.OnQubit_hadamard"(%q1_84_1) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_86_1 = "quantum.OnQubit_controlled_phase"(%q1_85_1, %q1_85_1) {control_index = 7 : i32, target_index = 5 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_87_1 = "quantum.OnQubit_controlled_phase"(%q1_86_1, %q1_86_1) {control_index = 6 : i32, target_index = 5 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_88_1 = "quantum.OnQubit_hadamard"(%q1_87_1) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_89_1 = "quantum.OnQubit_controlled_phase"(%q1_88_1, %q1_88_1) {control_index = 7 : i32, target_index = 4 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_90_1 = "quantum.OnQubit_controlled_phase"(%q1_89_1, %q1_89_1) {control_index = 6 : i32, target_index = 4 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_91_1 = "quantum.OnQubit_controlled_phase"(%q1_90_1, %q1_90_1) {control_index = 5 : i32, target_index = 4 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_92_1 = "quantum.OnQubit_hadamard"(%q1_91_1) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_93_1 = "quantum.OnQubit_controlled_phase"(%q1_92_1, %q1_92_1) {control_index = 7 : i32, target_index = 3 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_94_1 = "quantum.OnQubit_controlled_phase"(%q1_93_1, %q1_93_1) {control_index = 6 : i32, target_index = 3 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_95_1 = "quantum.OnQubit_controlled_phase"(%q1_94_1, %q1_94_1) {control_index = 5 : i32, target_index = 3 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_96_1 = "quantum.OnQubit_controlled_phase"(%q1_95_1, %q1_95_1) {control_index = 4 : i32, target_index = 3 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_97_1 = "quantum.OnQubit_hadamard"(%q1_96_1) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_98_1 = "quantum.OnQubit_controlled_phase"(%q1_97_1, %q1_97_1) {control_index = 7 : i32, target_index = 2 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_99_1 = "quantum.OnQubit_controlled_phase"(%q1_98_1, %q1_98_1) {control_index = 6 : i32, target_index = 2 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_100_1 = "quantum.OnQubit_controlled_phase"(%q1_99_1, %q1_99_1) {control_index = 5 : i32, target_index = 2 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_101_1 = "quantum.OnQubit_controlled_phase"(%q1_100_1, %q1_100_1) {control_index = 4 : i32, target_index = 2 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_102_1 = "quantum.OnQubit_controlled_phase"(%q1_101_1, %q1_101_1) {control_index = 3 : i32, target_index = 2 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_103_1 = "quantum.OnQubit_hadamard"(%q1_102_1) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_104_1 = "quantum.OnQubit_controlled_phase"(%q1_103_1, %q1_103_1) {control_index = 7 : i32, target_index = 1 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_105_1 = "quantum.OnQubit_controlled_phase"(%q1_104_1, %q1_104_1) {control_index = 6 : i32, target_index = 1 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_106_1 = "quantum.OnQubit_controlled_phase"(%q1_105_1, %q1_105_1) {control_index = 5 : i32, target_index = 1 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_107_1 = "quantum.OnQubit_controlled_phase"(%q1_106_1, %q1_106_1) {control_index = 4 : i32, target_index = 1 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_108_1 = "quantum.OnQubit_controlled_phase"(%q1_107_1, %q1_107_1) {control_index = 3 : i32, target_index = 1 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_109_1 = "quantum.OnQubit_controlled_phase"(%q1_108_1, %q1_108_1) {control_index = 2 : i32, target_index = 1 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_110_1 = "quantum.OnQubit_hadamard"(%q1_109_1) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_111_1 = "quantum.OnQubit_controlled_phase"(%q1_110_1, %q1_110_1) {control_index = 7 : i32, target_index = 0 : i32, phase = -0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_112_1 = "quantum.OnQubit_controlled_phase"(%q1_111_1, %q1_111_1) {control_index = 6 : i32, target_index = 0 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_113_1 = "quantum.OnQubit_controlled_phase"(%q1_112_1, %q1_112_1) {control_index = 5 : i32, target_index = 0 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_114_1 = "quantum.OnQubit_controlled_phase"(%q1_113_1, %q1_113_1) {control_index = 4 : i32, target_index = 0 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_115_1 = "quantum.OnQubit_controlled_phase"(%q1_114_1, %q1_114_1) {control_index = 3 : i32, target_index = 0 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_116_1 = "quantum.OnQubit_controlled_phase"(%q1_115_1, %q1_115_1) {control_index = 2 : i32, target_index = 0 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_117_1 = "quantum.OnQubit_controlled_phase"(%q1_116_1, %q1_116_1) {control_index = 1 : i32, target_index = 0 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q1_118_1 = "quantum.OnQubit_hadamard"(%q1_117_1) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
  }) {func_name = "main"} : () -> ()
}
