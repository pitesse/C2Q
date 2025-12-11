builtin.module {
  "quantum.func"() ({
    %q0_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q0_1 = "quantum.OnQubit_not"(%q0_0) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_2 = "quantum.OnQubit_not"(%q0_1) {index = 1 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_3 = "quantum.OnQubit_not"(%q0_2) {index = 2 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_4 = "quantum.OnQubit_not"(%q0_3) {index = 3 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_5 = "quantum.OnQubit_not"(%q0_4) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_6 = "quantum.OnQubit_not"(%q0_5) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_7 = "quantum.OnQubit_not"(%q0_6) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q0_8 = "quantum.OnQubit_not"(%q0_7) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q1_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q1_1 = "quantum.OnQubit_not"(%q1_0) {index = 0 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_0 = "quantum.init"() {type = vector<8xi1>, value = 0 : i8} : () -> vector<8xi1>
    %q2_1 = "quantum.OnQubit_cnot"(%q1_1, %q2_0) {control_index = 0 : i32, target_index = 0 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_2 = "quantum.OnQubit_cnot"(%q1_1, %q2_1) {control_index = 1 : i32, target_index = 1 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_3 = "quantum.OnQubit_cnot"(%q1_1, %q2_2) {control_index = 2 : i32, target_index = 2 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_4 = "quantum.OnQubit_cnot"(%q1_1, %q2_3) {control_index = 3 : i32, target_index = 3 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_5 = "quantum.OnQubit_cnot"(%q1_1, %q2_4) {control_index = 4 : i32, target_index = 4 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_6 = "quantum.OnQubit_cnot"(%q1_1, %q2_5) {control_index = 5 : i32, target_index = 5 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_7 = "quantum.OnQubit_cnot"(%q1_1, %q2_6) {control_index = 6 : i32, target_index = 6 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_8 = "quantum.OnQubit_cnot"(%q1_1, %q2_7) {control_index = 7 : i32, target_index = 7 : i32} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_9 = "quantum.OnQubit_hadamard"(%q2_8) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_10 = "quantum.OnQubit_controlled_phase"(%q2_9, %q2_9) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_11 = "quantum.OnQubit_controlled_phase"(%q2_10, %q2_10) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_12 = "quantum.OnQubit_controlled_phase"(%q2_11, %q2_11) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_13 = "quantum.OnQubit_controlled_phase"(%q2_12, %q2_12) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_17 = "quantum.OnQubit_hadamard"(%q2_13) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_18 = "quantum.OnQubit_controlled_phase"(%q2_17, %q2_17) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_19 = "quantum.OnQubit_controlled_phase"(%q2_18, %q2_18) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_20 = "quantum.OnQubit_controlled_phase"(%q2_19, %q2_19) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_21 = "quantum.OnQubit_controlled_phase"(%q2_20, %q2_20) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_24 = "quantum.OnQubit_hadamard"(%q2_21) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_25 = "quantum.OnQubit_controlled_phase"(%q2_24, %q2_24) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_26 = "quantum.OnQubit_controlled_phase"(%q2_25, %q2_25) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_27 = "quantum.OnQubit_controlled_phase"(%q2_26, %q2_26) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_28 = "quantum.OnQubit_controlled_phase"(%q2_27, %q2_27) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_30 = "quantum.OnQubit_hadamard"(%q2_28) {index = 4 : i32} : (vector<8xi1>) -> vector<8xi1>
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
    %q2_45 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_44) {control_index = 0 : i32, target_index = 0 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_46 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_45) {control_index = 0 : i32, target_index = 1 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_47 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_46) {control_index = 0 : i32, target_index = 2 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_48 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_47) {control_index = 0 : i32, target_index = 3 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_49 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_48) {control_index = 0 : i32, target_index = 4 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_53 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_49) {control_index = 1 : i32, target_index = 1 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_54 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_53) {control_index = 1 : i32, target_index = 2 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_55 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_54) {control_index = 1 : i32, target_index = 3 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_56 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_55) {control_index = 1 : i32, target_index = 4 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_57 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_56) {control_index = 1 : i32, target_index = 5 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_60 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_57) {control_index = 2 : i32, target_index = 2 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_61 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_60) {control_index = 2 : i32, target_index = 3 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_62 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_61) {control_index = 2 : i32, target_index = 4 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_63 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_62) {control_index = 2 : i32, target_index = 5 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_64 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_63) {control_index = 2 : i32, target_index = 6 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_66 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_64) {control_index = 3 : i32, target_index = 3 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_67 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_66) {control_index = 3 : i32, target_index = 4 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_68 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_67) {control_index = 3 : i32, target_index = 5 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_69 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_68) {control_index = 3 : i32, target_index = 6 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_70 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_69) {control_index = 3 : i32, target_index = 7 : i32, phase = 0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_71 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_70) {control_index = 4 : i32, target_index = 4 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_72 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_71) {control_index = 4 : i32, target_index = 5 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_73 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_72) {control_index = 4 : i32, target_index = 6 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_74 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_73) {control_index = 4 : i32, target_index = 7 : i32, phase = 0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_75 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_74) {control_index = 5 : i32, target_index = 5 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_76 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_75) {control_index = 5 : i32, target_index = 6 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_77 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_76) {control_index = 5 : i32, target_index = 7 : i32, phase = 0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_78 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_77) {control_index = 6 : i32, target_index = 6 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_79 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_78) {control_index = 6 : i32, target_index = 7 : i32, phase = 1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_80 = "quantum.OnQubit_controlled_phase"(%q0_8, %q2_79) {control_index = 7 : i32, target_index = 7 : i32, phase = 3.1415926535897931 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
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
    %q2_97 = "quantum.OnQubit_controlled_phase"(%q2_95, %q2_95) {control_index = 1 : i32, target_index = 5 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_98 = "quantum.OnQubit_controlled_phase"(%q2_97, %q2_97) {control_index = 2 : i32, target_index = 5 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_99 = "quantum.OnQubit_controlled_phase"(%q2_98, %q2_98) {control_index = 3 : i32, target_index = 5 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_100 = "quantum.OnQubit_controlled_phase"(%q2_99, %q2_99) {control_index = 4 : i32, target_index = 5 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_101 = "quantum.OnQubit_hadamard"(%q2_100) {index = 5 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_104 = "quantum.OnQubit_controlled_phase"(%q2_101, %q2_101) {control_index = 2 : i32, target_index = 6 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_105 = "quantum.OnQubit_controlled_phase"(%q2_104, %q2_104) {control_index = 3 : i32, target_index = 6 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_106 = "quantum.OnQubit_controlled_phase"(%q2_105, %q2_105) {control_index = 4 : i32, target_index = 6 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_107 = "quantum.OnQubit_controlled_phase"(%q2_106, %q2_106) {control_index = 5 : i32, target_index = 6 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_108 = "quantum.OnQubit_hadamard"(%q2_107) {index = 6 : i32} : (vector<8xi1>) -> vector<8xi1>
    %q2_112 = "quantum.OnQubit_controlled_phase"(%q2_108, %q2_108) {control_index = 3 : i32, target_index = 7 : i32, phase = -0.19634954084936207 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_113 = "quantum.OnQubit_controlled_phase"(%q2_112, %q2_112) {control_index = 4 : i32, target_index = 7 : i32, phase = -0.39269908169872414 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_114 = "quantum.OnQubit_controlled_phase"(%q2_113, %q2_113) {control_index = 5 : i32, target_index = 7 : i32, phase = -0.78539816339744828 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_115 = "quantum.OnQubit_controlled_phase"(%q2_114, %q2_114) {control_index = 6 : i32, target_index = 7 : i32, phase = -1.5707963267948966 : f64} : (vector<8xi1>, vector<8xi1>) -> vector<8xi1>
    %q2_116 = "quantum.OnQubit_hadamard"(%q2_115) {index = 7 : i32} : (vector<8xi1>) -> vector<8xi1>
  }) {func_name = "main"} : () -> ()
}
