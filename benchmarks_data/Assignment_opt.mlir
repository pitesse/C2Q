builtin.module {
  "quantum.func"() ({
    %q0_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q0_1 = "quantum.OnQubit_not"(%q0_0) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_2 = "quantum.OnQubit_not"(%q0_1) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q1_1 = "quantum.OnQubit_not"(%q1_0) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_2 = "quantum.OnQubit_not"(%q1_1) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q2_1 = "quantum.OnQubit_cnot"(%q1_2, %q2_0) {control_index = 0 : i32, target_index = 0 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_2 = "quantum.OnQubit_cnot"(%q1_2, %q2_1) {control_index = 1 : i32, target_index = 1 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_3 = "quantum.OnQubit_cnot"(%q1_2, %q2_2) {control_index = 2 : i32, target_index = 2 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_4 = "quantum.OnQubit_cnot"(%q1_2, %q2_3) {control_index = 3 : i32, target_index = 3 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_5 = "quantum.OnQubit_cnot"(%q1_2, %q2_4) {control_index = 4 : i32, target_index = 4 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_6 = "quantum.OnQubit_cnot"(%q1_2, %q2_5) {control_index = 5 : i32, target_index = 5 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_7 = "quantum.OnQubit_cnot"(%q1_2, %q2_6) {control_index = 6 : i32, target_index = 6 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_8 = "quantum.OnQubit_cnot"(%q1_2, %q2_7) {control_index = 7 : i32, target_index = 7 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_9 = "quantum.OnQubit_hadamard"(%q2_8) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_10 = "quantum.OnQubit_controlled_phase"(%q2_9, %q2_9) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_11 = "quantum.OnQubit_controlled_phase"(%q2_10, %q2_10) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_12 = "quantum.OnQubit_controlled_phase"(%q2_11, %q2_11) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_13 = "quantum.OnQubit_controlled_phase"(%q2_12, %q2_12) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_15 = "quantum.OnQubit_controlled_phase"(%q2_14, %q2_14) {control_index = 1 : i32, target_index = 7 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_16 = "quantum.OnQubit_controlled_phase"(%q2_15, %q2_15) {control_index = 0 : i32, target_index = 7 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_17 = "quantum.OnQubit_hadamard"(%q2_16) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_18 = "quantum.OnQubit_controlled_phase"(%q2_17, %q2_17) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_19 = "quantum.OnQubit_controlled_phase"(%q2_18, %q2_18) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_20 = "quantum.OnQubit_controlled_phase"(%q2_19, %q2_19) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_21 = "quantum.OnQubit_controlled_phase"(%q2_20, %q2_20) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_22 = "quantum.OnQubit_controlled_phase"(%q2_21, %q2_21) {control_index = 1 : i32, target_index = 6 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_23 = "quantum.OnQubit_controlled_phase"(%q2_22, %q2_22) {control_index = 0 : i32, target_index = 6 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_24 = "quantum.OnQubit_hadamard"(%q2_23) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_25 = "quantum.OnQubit_controlled_phase"(%q2_24, %q2_24) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_26 = "quantum.OnQubit_controlled_phase"(%q2_25, %q2_25) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_27 = "quantum.OnQubit_controlled_phase"(%q2_26, %q2_26) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_28 = "quantum.OnQubit_controlled_phase"(%q2_27, %q2_27) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_29 = "quantum.OnQubit_controlled_phase"(%q2_28, %q2_28) {control_index = 0 : i32, target_index = 5 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_30 = "quantum.OnQubit_hadamard"(%q2_29) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_31 = "quantum.OnQubit_controlled_phase"(%q2_30, %q2_30) {control_index = 3 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_32 = "quantum.OnQubit_controlled_phase"(%q2_31, %q2_31) {control_index = 2 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_33 = "quantum.OnQubit_controlled_phase"(%q2_32, %q2_32) {control_index = 1 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_34 = "quantum.OnQubit_controlled_phase"(%q2_33, %q2_33) {control_index = 0 : i32, target_index = 4 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_35 = "quantum.OnQubit_hadamard"(%q2_34) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_36 = "quantum.OnQubit_controlled_phase"(%q2_35, %q2_35) {control_index = 2 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_37 = "quantum.OnQubit_controlled_phase"(%q2_36, %q2_36) {control_index = 1 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_38 = "quantum.OnQubit_controlled_phase"(%q2_37, %q2_37) {control_index = 0 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_39 = "quantum.OnQubit_hadamard"(%q2_38) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_40 = "quantum.OnQubit_controlled_phase"(%q2_39, %q2_39) {control_index = 1 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_41 = "quantum.OnQubit_controlled_phase"(%q2_40, %q2_40) {control_index = 0 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_42 = "quantum.OnQubit_hadamard"(%q2_41) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_43 = "quantum.OnQubit_controlled_phase"(%q2_42, %q2_42) {control_index = 0 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_44 = "quantum.OnQubit_hadamard"(%q2_43) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_45 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_44) {control_index = 0 : i32, target_index = 0 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_46 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_45) {control_index = 0 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_47 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_46) {control_index = 0 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_48 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_47) {control_index = 0 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_49 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_48) {control_index = 0 : i32, target_index = 4 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_50 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_49) {control_index = 0 : i32, target_index = 5 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_51 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_50) {control_index = 0 : i32, target_index = 6 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_52 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_51) {control_index = 0 : i32, target_index = 7 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_53 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_52) {control_index = 1 : i32, target_index = 1 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_54 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_53) {control_index = 1 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_55 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_54) {control_index = 1 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_56 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_55) {control_index = 1 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_57 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_56) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_58 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_57) {control_index = 1 : i32, target_index = 6 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_59 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_58) {control_index = 1 : i32, target_index = 7 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_60 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_59) {control_index = 2 : i32, target_index = 2 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_61 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_60) {control_index = 2 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_62 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_61) {control_index = 2 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_63 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_62) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_64 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_63) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_65 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_64) {control_index = 2 : i32, target_index = 7 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_66 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_65) {control_index = 3 : i32, target_index = 3 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_67 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_66) {control_index = 3 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_68 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_67) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_69 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_68) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_70 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_69) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_71 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_70) {control_index = 4 : i32, target_index = 4 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_72 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_71) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_73 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_72) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_74 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_73) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_75 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_74) {control_index = 5 : i32, target_index = 5 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_76 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_75) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_77 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_76) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_78 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_77) {control_index = 6 : i32, target_index = 6 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_79 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_78) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_80 = "quantum.OnQubit_controlled_phase"(%q0_2, %q2_79) {control_index = 7 : i32, target_index = 7 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_81 = "quantum.OnQubit_hadamard"(%q2_80) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_82 = "quantum.OnQubit_controlled_phase"(%q2_81, %q2_81) {control_index = 0 : i32, target_index = 1 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_83 = "quantum.OnQubit_hadamard"(%q2_82) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_84 = "quantum.OnQubit_controlled_phase"(%q2_83, %q2_83) {control_index = 0 : i32, target_index = 2 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_85 = "quantum.OnQubit_controlled_phase"(%q2_84, %q2_84) {control_index = 1 : i32, target_index = 2 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_86 = "quantum.OnQubit_hadamard"(%q2_85) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_87 = "quantum.OnQubit_controlled_phase"(%q2_86, %q2_86) {control_index = 0 : i32, target_index = 3 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_88 = "quantum.OnQubit_controlled_phase"(%q2_87, %q2_87) {control_index = 1 : i32, target_index = 3 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_89 = "quantum.OnQubit_controlled_phase"(%q2_88, %q2_88) {control_index = 2 : i32, target_index = 3 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_90 = "quantum.OnQubit_hadamard"(%q2_89) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_91 = "quantum.OnQubit_controlled_phase"(%q2_90, %q2_90) {control_index = 0 : i32, target_index = 4 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_92 = "quantum.OnQubit_controlled_phase"(%q2_91, %q2_91) {control_index = 1 : i32, target_index = 4 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_93 = "quantum.OnQubit_controlled_phase"(%q2_92, %q2_92) {control_index = 2 : i32, target_index = 4 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_94 = "quantum.OnQubit_controlled_phase"(%q2_93, %q2_93) {control_index = 3 : i32, target_index = 4 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_95 = "quantum.OnQubit_hadamard"(%q2_94) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_96 = "quantum.OnQubit_controlled_phase"(%q2_95, %q2_95) {control_index = 0 : i32, target_index = 5 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_97 = "quantum.OnQubit_controlled_phase"(%q2_96, %q2_96) {control_index = 1 : i32, target_index = 5 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_98 = "quantum.OnQubit_controlled_phase"(%q2_97, %q2_97) {control_index = 2 : i32, target_index = 5 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_99 = "quantum.OnQubit_controlled_phase"(%q2_98, %q2_98) {control_index = 3 : i32, target_index = 5 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_100 = "quantum.OnQubit_controlled_phase"(%q2_99, %q2_99) {control_index = 4 : i32, target_index = 5 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_101 = "quantum.OnQubit_hadamard"(%q2_100) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_102 = "quantum.OnQubit_controlled_phase"(%q2_101, %q2_101) {control_index = 0 : i32, target_index = 6 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_103 = "quantum.OnQubit_controlled_phase"(%q2_102, %q2_102) {control_index = 1 : i32, target_index = 6 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_104 = "quantum.OnQubit_controlled_phase"(%q2_103, %q2_103) {control_index = 2 : i32, target_index = 6 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_105 = "quantum.OnQubit_controlled_phase"(%q2_104, %q2_104) {control_index = 3 : i32, target_index = 6 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_106 = "quantum.OnQubit_controlled_phase"(%q2_105, %q2_105) {control_index = 4 : i32, target_index = 6 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_107 = "quantum.OnQubit_controlled_phase"(%q2_106, %q2_106) {control_index = 5 : i32, target_index = 6 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_108 = "quantum.OnQubit_hadamard"(%q2_107) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_109 = "quantum.OnQubit_controlled_phase"(%q2_108, %q2_108) {control_index = 0 : i32, target_index = 7 : i32, phase = -0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_110 = "quantum.OnQubit_controlled_phase"(%q2_109, %q2_109) {control_index = 1 : i32, target_index = 7 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_111 = "quantum.OnQubit_controlled_phase"(%q2_110, %q2_110) {control_index = 2 : i32, target_index = 7 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_112 = "quantum.OnQubit_controlled_phase"(%q2_111, %q2_111) {control_index = 3 : i32, target_index = 7 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_113 = "quantum.OnQubit_controlled_phase"(%q2_112, %q2_112) {control_index = 4 : i32, target_index = 7 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_114 = "quantum.OnQubit_controlled_phase"(%q2_113, %q2_113) {control_index = 5 : i32, target_index = 7 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_115 = "quantum.OnQubit_controlled_phase"(%q2_114, %q2_114) {control_index = 6 : i32, target_index = 7 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_116 = "quantum.OnQubit_hadamard"(%q2_115) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q3_1 = "quantum.OnQubit_cnot"(%q1_2, %q3_0) {control_index = 0 : i32, target_index = 0 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_2 = "quantum.OnQubit_cnot"(%q1_2, %q3_1) {control_index = 1 : i32, target_index = 1 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_3 = "quantum.OnQubit_cnot"(%q1_2, %q3_2) {control_index = 2 : i32, target_index = 2 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_4 = "quantum.OnQubit_cnot"(%q1_2, %q3_3) {control_index = 3 : i32, target_index = 3 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_5 = "quantum.OnQubit_cnot"(%q1_2, %q3_4) {control_index = 4 : i32, target_index = 4 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_6 = "quantum.OnQubit_cnot"(%q1_2, %q3_5) {control_index = 5 : i32, target_index = 5 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_7 = "quantum.OnQubit_cnot"(%q1_2, %q3_6) {control_index = 6 : i32, target_index = 6 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_8 = "quantum.OnQubit_cnot"(%q1_2, %q3_7) {control_index = 7 : i32, target_index = 7 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_9 = "quantum.OnQubit_hadamard"(%q3_8) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_10 = "quantum.OnQubit_controlled_phase"(%q3_9, %q3_9) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_11 = "quantum.OnQubit_controlled_phase"(%q3_10, %q3_10) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_12 = "quantum.OnQubit_controlled_phase"(%q3_11, %q3_11) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_13 = "quantum.OnQubit_controlled_phase"(%q3_12, %q3_12) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_14 = "quantum.OnQubit_controlled_phase"(%q3_13, %q3_13) {control_index = 2 : i32, target_index = 7 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_15 = "quantum.OnQubit_controlled_phase"(%q3_14, %q3_14) {control_index = 1 : i32, target_index = 7 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_16 = "quantum.OnQubit_controlled_phase"(%q3_15, %q3_15) {control_index = 0 : i32, target_index = 7 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_17 = "quantum.OnQubit_hadamard"(%q3_16) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_18 = "quantum.OnQubit_controlled_phase"(%q3_17, %q3_17) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_19 = "quantum.OnQubit_controlled_phase"(%q3_18, %q3_18) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_20 = "quantum.OnQubit_controlled_phase"(%q3_19, %q3_19) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_21 = "quantum.OnQubit_controlled_phase"(%q3_20, %q3_20) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_22 = "quantum.OnQubit_controlled_phase"(%q3_21, %q3_21) {control_index = 1 : i32, target_index = 6 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_23 = "quantum.OnQubit_controlled_phase"(%q3_22, %q3_22) {control_index = 0 : i32, target_index = 6 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_24 = "quantum.OnQubit_hadamard"(%q3_23) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_25 = "quantum.OnQubit_controlled_phase"(%q3_24, %q3_24) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_26 = "quantum.OnQubit_controlled_phase"(%q3_25, %q3_25) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_27 = "quantum.OnQubit_controlled_phase"(%q3_26, %q3_26) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_28 = "quantum.OnQubit_controlled_phase"(%q3_27, %q3_27) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_29 = "quantum.OnQubit_controlled_phase"(%q3_28, %q3_28) {control_index = 0 : i32, target_index = 5 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_30 = "quantum.OnQubit_hadamard"(%q3_29) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_31 = "quantum.OnQubit_controlled_phase"(%q3_30, %q3_30) {control_index = 3 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_32 = "quantum.OnQubit_controlled_phase"(%q3_31, %q3_31) {control_index = 2 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_33 = "quantum.OnQubit_controlled_phase"(%q3_32, %q3_32) {control_index = 1 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_34 = "quantum.OnQubit_controlled_phase"(%q3_33, %q3_33) {control_index = 0 : i32, target_index = 4 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_35 = "quantum.OnQubit_hadamard"(%q3_34) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_36 = "quantum.OnQubit_controlled_phase"(%q3_35, %q3_35) {control_index = 2 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_37 = "quantum.OnQubit_controlled_phase"(%q3_36, %q3_36) {control_index = 1 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_38 = "quantum.OnQubit_controlled_phase"(%q3_37, %q3_37) {control_index = 0 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_39 = "quantum.OnQubit_hadamard"(%q3_38) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_40 = "quantum.OnQubit_controlled_phase"(%q3_39, %q3_39) {control_index = 1 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_41 = "quantum.OnQubit_controlled_phase"(%q3_40, %q3_40) {control_index = 0 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_42 = "quantum.OnQubit_hadamard"(%q3_41) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_43 = "quantum.OnQubit_controlled_phase"(%q3_42, %q3_42) {control_index = 0 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_44 = "quantum.OnQubit_hadamard"(%q3_43) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_45 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_44) {control_index = 0 : i32, target_index = 0 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_46 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_45) {control_index = 0 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_47 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_46) {control_index = 0 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_48 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_47) {control_index = 0 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_49 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_48) {control_index = 0 : i32, target_index = 4 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_50 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_49) {control_index = 0 : i32, target_index = 5 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_51 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_50) {control_index = 0 : i32, target_index = 6 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_52 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_51) {control_index = 0 : i32, target_index = 7 : i32, phase = 0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_53 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_52) {control_index = 1 : i32, target_index = 1 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_54 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_53) {control_index = 1 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_55 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_54) {control_index = 1 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_56 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_55) {control_index = 1 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_57 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_56) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_58 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_57) {control_index = 1 : i32, target_index = 6 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_59 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_58) {control_index = 1 : i32, target_index = 7 : i32, phase = 0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_60 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_59) {control_index = 2 : i32, target_index = 2 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_61 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_60) {control_index = 2 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_62 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_61) {control_index = 2 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_63 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_62) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_64 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_63) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_65 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_64) {control_index = 2 : i32, target_index = 7 : i32, phase = 0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_66 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_65) {control_index = 3 : i32, target_index = 3 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_67 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_66) {control_index = 3 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_68 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_67) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_69 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_68) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_70 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_69) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_71 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_70) {control_index = 4 : i32, target_index = 4 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_72 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_71) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_73 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_72) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_74 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_73) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_75 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_74) {control_index = 5 : i32, target_index = 5 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_76 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_75) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_77 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_76) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_78 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_77) {control_index = 6 : i32, target_index = 6 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_79 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_78) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_80 = "quantum.OnQubit_controlled_phase"(%q2_116, %q3_79) {control_index = 7 : i32, target_index = 7 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_81 = "quantum.OnQubit_hadamard"(%q3_80) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_82 = "quantum.OnQubit_controlled_phase"(%q3_81, %q3_81) {control_index = 0 : i32, target_index = 1 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_83 = "quantum.OnQubit_hadamard"(%q3_82) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_84 = "quantum.OnQubit_controlled_phase"(%q3_83, %q3_83) {control_index = 0 : i32, target_index = 2 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_85 = "quantum.OnQubit_controlled_phase"(%q3_84, %q3_84) {control_index = 1 : i32, target_index = 2 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_86 = "quantum.OnQubit_hadamard"(%q3_85) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_87 = "quantum.OnQubit_controlled_phase"(%q3_86, %q3_86) {control_index = 0 : i32, target_index = 3 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_88 = "quantum.OnQubit_controlled_phase"(%q3_87, %q3_87) {control_index = 1 : i32, target_index = 3 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_89 = "quantum.OnQubit_controlled_phase"(%q3_88, %q3_88) {control_index = 2 : i32, target_index = 3 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_90 = "quantum.OnQubit_hadamard"(%q3_89) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_91 = "quantum.OnQubit_controlled_phase"(%q3_90, %q3_90) {control_index = 0 : i32, target_index = 4 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_92 = "quantum.OnQubit_controlled_phase"(%q3_91, %q3_91) {control_index = 1 : i32, target_index = 4 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_93 = "quantum.OnQubit_controlled_phase"(%q3_92, %q3_92) {control_index = 2 : i32, target_index = 4 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_94 = "quantum.OnQubit_controlled_phase"(%q3_93, %q3_93) {control_index = 3 : i32, target_index = 4 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_95 = "quantum.OnQubit_hadamard"(%q3_94) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_96 = "quantum.OnQubit_controlled_phase"(%q3_95, %q3_95) {control_index = 0 : i32, target_index = 5 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_97 = "quantum.OnQubit_controlled_phase"(%q3_96, %q3_96) {control_index = 1 : i32, target_index = 5 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_98 = "quantum.OnQubit_controlled_phase"(%q3_97, %q3_97) {control_index = 2 : i32, target_index = 5 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_99 = "quantum.OnQubit_controlled_phase"(%q3_98, %q3_98) {control_index = 3 : i32, target_index = 5 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_100 = "quantum.OnQubit_controlled_phase"(%q3_99, %q3_99) {control_index = 4 : i32, target_index = 5 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_101 = "quantum.OnQubit_hadamard"(%q3_100) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_102 = "quantum.OnQubit_controlled_phase"(%q3_101, %q3_101) {control_index = 0 : i32, target_index = 6 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_103 = "quantum.OnQubit_controlled_phase"(%q3_102, %q3_102) {control_index = 1 : i32, target_index = 6 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_104 = "quantum.OnQubit_controlled_phase"(%q3_103, %q3_103) {control_index = 2 : i32, target_index = 6 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_105 = "quantum.OnQubit_controlled_phase"(%q3_104, %q3_104) {control_index = 3 : i32, target_index = 6 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_106 = "quantum.OnQubit_controlled_phase"(%q3_105, %q3_105) {control_index = 4 : i32, target_index = 6 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_107 = "quantum.OnQubit_controlled_phase"(%q3_106, %q3_106) {control_index = 5 : i32, target_index = 6 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_108 = "quantum.OnQubit_hadamard"(%q3_107) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q3_109 = "quantum.OnQubit_controlled_phase"(%q3_108, %q3_108) {control_index = 0 : i32, target_index = 7 : i32, phase = -0.024543692606170259 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_110 = "quantum.OnQubit_controlled_phase"(%q3_109, %q3_109) {control_index = 1 : i32, target_index = 7 : i32, phase = -0.049087385212340517 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_111 = "quantum.OnQubit_controlled_phase"(%q3_110, %q3_110) {control_index = 2 : i32, target_index = 7 : i32, phase = -0.098174770424681035 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_112 = "quantum.OnQubit_controlled_phase"(%q3_111, %q3_111) {control_index = 3 : i32, target_index = 7 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_113 = "quantum.OnQubit_controlled_phase"(%q3_112, %q3_112) {control_index = 4 : i32, target_index = 7 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_114 = "quantum.OnQubit_controlled_phase"(%q3_113, %q3_113) {control_index = 5 : i32, target_index = 7 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q3_115 = "quantum.OnQubit_controlled_phase"(%q3_114, %q3_114) {control_index = 6 : i32, target_index = 7 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q4_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
  }) {func_name = "main"} : () -> ()
}
