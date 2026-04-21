; ModuleID = '62_list_output'
source_filename = "62_list_output"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [8 x i8] c"declare ", align 8
@.str.1 = private constant [2 x i8] c" @", align 8
@.str.2 = private constant [2 x i8] c"()", align 8
@.str.3 = private constant [3 x i8] c"foo", align 8
@.str.4 = private constant [3 x i8] c"i64", align 8
@.str.5 = private constant [3 x i8] c"bar", align 8
@.str.6 = private constant [4 x i8] c"void", align 8
@.str.7 = private constant [3 x i8] c"baz", align 8
@.str.8 = private constant [6 x i8] c"double", align 8
@.str.9 = private constant [1 x i8] c"\0A", align 8

declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
declare void @__mn_list_push(ptr, ptr) nounwind
declare void @__mn_str_free({ptr, i64}) nounwind willreturn
declare void @free(ptr) nounwind willreturn
declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
declare {ptr, i64} @__mn_str_join({ptr, i64}, ptr)
declare void @__mn_str_println({ptr, i64})
declare void @__mn_list_free(ptr) nounwind willreturn
declare void @__mn_intern_destroy()

define internal {{ptr, i64, i64, i64, i64}, i64} @add_decl({{ptr, i64, i64, i64, i64}, i64} %st, {ptr, i64} %name, {ptr, i64} %ret) nounwind willreturn {
pre_entry:
  %st.addr = alloca {{ptr, i64, i64, i64, i64}, i64}, align 8
  %name.addr = alloca {ptr, i64}, align 8
  %ret.addr = alloca {ptr, i64}, align 8
  %t0.a.3 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t0.a.3
  %str_track.7 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.7
  %t1.a.8 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t1.a.8
  %t2.a.12 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t2.a.12
  %str_track.16 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.16
  %t3.a.17 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.17
  %str_track.21 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.21
  %t4.a.22 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.22
  %t5.a.26 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t5.a.26
  %str_track.30 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.30
  %t6.a.31 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.31
  %_inl1_s.a.33 = alloca {{ptr, i64, i64, i64, i64}, i64}, align 8
  store {{ptr, i64, i64, i64, i64}, i64} zeroinitializer, ptr %_inl1_s.a.33
  %_inl1_t0.a.36 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %_inl1_t0.a.36
  %ea.38 = alloca {ptr, i64}, align 8
  store {{ptr, i64, i64, i64, i64}, i64} %st, ptr %st.addr
  store {ptr, i64} %name, ptr %name.addr
  store {ptr, i64} %ret, ptr %ret.addr
  br label %entry
entry:
  %sp.0 = getelementptr inbounds [8 x i8], ptr @.str.0, i64 0, i64 0
  %s.1 = insertvalue {ptr, i64} undef, ptr %sp.0, 0
  %s.2 = insertvalue {ptr, i64} %s.1, i64 8, 1
  store {ptr, i64} %s.2, ptr %t0.a.3
  %l.4 = load {ptr, i64}, ptr %t0.a.3
  %l.5 = load {ptr, i64}, ptr %ret.addr
  %rt.6 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.4, {ptr, i64} %l.5)
  store {ptr, i64} %rt.6, ptr %str_track.7
  store {ptr, i64} %rt.6, ptr %t1.a.8
  %sp.9 = getelementptr inbounds [2 x i8], ptr @.str.1, i64 0, i64 0
  %s.10 = insertvalue {ptr, i64} undef, ptr %sp.9, 0
  %s.11 = insertvalue {ptr, i64} %s.10, i64 2, 1
  store {ptr, i64} %s.11, ptr %t2.a.12
  %l.13 = load {ptr, i64}, ptr %t1.a.8
  %l.14 = load {ptr, i64}, ptr %t2.a.12
  %rt.15 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.13, {ptr, i64} %l.14)
  store {ptr, i64} %rt.15, ptr %str_track.16
  store {ptr, i64} %rt.15, ptr %t3.a.17
  %l.18 = load {ptr, i64}, ptr %t3.a.17
  %l.19 = load {ptr, i64}, ptr %name.addr
  %rt.20 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.18, {ptr, i64} %l.19)
  store {ptr, i64} %rt.20, ptr %str_track.21
  store {ptr, i64} %rt.20, ptr %t4.a.22
  %sp.23 = getelementptr inbounds [2 x i8], ptr @.str.2, i64 0, i64 0
  %s.24 = insertvalue {ptr, i64} undef, ptr %sp.23, 0
  %s.25 = insertvalue {ptr, i64} %s.24, i64 2, 1
  store {ptr, i64} %s.25, ptr %t5.a.26
  %l.27 = load {ptr, i64}, ptr %t4.a.22
  %l.28 = load {ptr, i64}, ptr %t5.a.26
  %rt.29 = call {ptr, i64} @__mn_str_concat({ptr, i64} %l.27, {ptr, i64} %l.28)
  store {ptr, i64} %rt.29, ptr %str_track.30
  store {ptr, i64} %rt.29, ptr %t6.a.31
  br label %_inl1_entry
_inl1_entry:
  %l.32 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %st.addr
  store {{ptr, i64, i64, i64, i64}, i64} %l.32, ptr %_inl1_s.a.33
  %fg.34 = getelementptr inbounds {{ptr, i64, i64, i64, i64}, i64}, ptr %_inl1_s.a.33, i32 0, i32 0
  %fv.35 = load {ptr, i64, i64, i64, i64}, ptr %fg.34
  store {ptr, i64, i64, i64, i64} %fv.35, ptr %_inl1_t0.a.36
  %l.37 = load {ptr, i64}, ptr %t6.a.31
  store {ptr, i64} %l.37, ptr %ea.38
  store {ptr, i64} zeroinitializer, ptr %str_track.30
  call void @__mn_list_push(ptr %_inl1_t0.a.36, ptr %ea.38)
  %ul.39 = load {ptr, i64, i64, i64, i64}, ptr %_inl1_t0.a.36
  store {ptr, i64, i64, i64, i64} %ul.39, ptr %_inl1_t0.a.36
  %l.40 = load {ptr, i64, i64, i64, i64}, ptr %_inl1_t0.a.36
  %fs.41 = getelementptr inbounds {{ptr, i64, i64, i64, i64}, i64}, ptr %_inl1_s.a.33, i32 0, i32 0
  store {ptr, i64, i64, i64, i64} %l.40, ptr %fs.41
  br label %_inl1_ret
_inl1_ret:
  %l.42 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %_inl1_s.a.33
  %ret.slf.43 = extractvalue {{ptr, i64, i64, i64, i64}, i64} %l.42, 0
  %ret.slp.44 = extractvalue {ptr, i64, i64, i64, i64} %ret.slf.43, 0
  %ret.rs.45 = extractvalue {{ptr, i64, i64, i64, i64}, i64} %l.42, 0
  %ret.rp.46 = extractvalue {ptr, i64, i64, i64, i64} %ret.rs.45, 0
  %drop.s.47 = load {ptr, i64}, ptr %str_track.7
  %drop.p.48 = extractvalue {ptr, i64} %drop.s.47, 0
  %drop.null.49 = icmp eq ptr %drop.p.48, null
  br i1 %drop.null.49, label %drop.skip.50, label %drop.check.50
drop.check.50:
  %drop.same.51 = icmp eq ptr %drop.p.48, %ret.rp.46
  br i1 %drop.same.51, label %drop.skip.50, label %drop.snext.52
drop.snext.52:
  call void @__mn_str_free({ptr, i64} %drop.s.47)
  br label %drop.skip.50
drop.skip.50:
  %drop.s.53 = load {ptr, i64}, ptr %str_track.16
  %drop.p.54 = extractvalue {ptr, i64} %drop.s.53, 0
  %drop.null.55 = icmp eq ptr %drop.p.54, null
  br i1 %drop.null.55, label %drop.skip.56, label %drop.check.56
drop.check.56:
  %drop.same.57 = icmp eq ptr %drop.p.54, %ret.rp.46
  br i1 %drop.same.57, label %drop.skip.56, label %drop.snext.58
drop.snext.58:
  call void @__mn_str_free({ptr, i64} %drop.s.53)
  br label %drop.skip.56
drop.skip.56:
  %drop.s.59 = load {ptr, i64}, ptr %str_track.21
  %drop.p.60 = extractvalue {ptr, i64} %drop.s.59, 0
  %drop.null.61 = icmp eq ptr %drop.p.60, null
  br i1 %drop.null.61, label %drop.skip.62, label %drop.check.62
drop.check.62:
  %drop.same.63 = icmp eq ptr %drop.p.60, %ret.rp.46
  br i1 %drop.same.63, label %drop.skip.62, label %drop.snext.64
drop.snext.64:
  call void @__mn_str_free({ptr, i64} %drop.s.59)
  br label %drop.skip.62
drop.skip.62:
  %drop.s.65 = load {ptr, i64}, ptr %str_track.30
  %drop.p.66 = extractvalue {ptr, i64} %drop.s.65, 0
  %drop.null.67 = icmp eq ptr %drop.p.66, null
  br i1 %drop.null.67, label %drop.skip.68, label %drop.check.68
drop.check.68:
  %drop.same.69 = icmp eq ptr %drop.p.66, %ret.rp.46
  br i1 %drop.same.69, label %drop.skip.68, label %drop.snext.70
drop.snext.70:
  call void @__mn_str_free({ptr, i64} %drop.s.65)
  br label %drop.skip.68
drop.skip.68:
  ret {{ptr, i64, i64, i64, i64}, i64} %l.42
}

define i64 @main() nounwind willreturn {
pre_entry:
  %t0.a.1 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t0.a.1
  %empty.a.3 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %empty.a.3
  %t1.a.4 = alloca i64, align 8
  store i64 0, ptr %t1.a.4
  %t2.a.9 = alloca {{ptr, i64, i64, i64, i64}, i64}, align 8
  store {{ptr, i64, i64, i64, i64}, i64} zeroinitializer, ptr %t2.a.9
  %st.a.11 = alloca {{ptr, i64, i64, i64, i64}, i64}, align 8
  store {{ptr, i64, i64, i64, i64}, i64} zeroinitializer, ptr %st.a.11
  %t3.a.15 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t3.a.15
  %t4.a.19 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t4.a.19
  %t5.a.24 = alloca {{ptr, i64, i64, i64, i64}, i64}, align 8
  store {{ptr, i64, i64, i64, i64}, i64} zeroinitializer, ptr %t5.a.24
  %t6.a.29 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t6.a.29
  %t7.a.33 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t7.a.33
  %t8.a.38 = alloca {{ptr, i64, i64, i64, i64}, i64}, align 8
  store {{ptr, i64, i64, i64, i64}, i64} zeroinitializer, ptr %t8.a.38
  %t9.a.43 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t9.a.43
  %t10.a.47 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t10.a.47
  %t11.a.52 = alloca {{ptr, i64, i64, i64, i64}, i64}, align 8
  store {{ptr, i64, i64, i64, i64}, i64} zeroinitializer, ptr %t11.a.52
  %t12.a.57 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t12.a.57
  %t13.a.60 = alloca {ptr, i64, i64, i64, i64}, align 8
  store {ptr, i64, i64, i64, i64} zeroinitializer, ptr %t13.a.60
  %jl.63 = alloca {ptr, i64, i64, i64, i64}, align 8
  %str_track.65 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %str_track.65
  %t14.a.66 = alloca {ptr, i64}, align 8
  store {ptr, i64} zeroinitializer, ptr %t14.a.66
  %t15.a.68 = alloca i1, align 8
  store i1 0, ptr %t15.a.68
  br label %entry
entry:
  %ln.0 = call {ptr, i64, i64, i64, i64} @__mn_list_new(i64 16)
  store {ptr, i64, i64, i64, i64} %ln.0, ptr %t0.a.1
  %l.2 = load {ptr, i64, i64, i64, i64}, ptr %t0.a.1
  store {ptr, i64, i64, i64, i64} %l.2, ptr %empty.a.3
  store i64 0, ptr %t1.a.4
  %l.5 = load {ptr, i64, i64, i64, i64}, ptr %empty.a.3
  %si.6 = insertvalue {{ptr, i64, i64, i64, i64}, i64} undef, {ptr, i64, i64, i64, i64} %l.5, 0
  %l.7 = load i64, ptr %t1.a.4
  %si.8 = insertvalue {{ptr, i64, i64, i64, i64}, i64} %si.6, i64 %l.7, 1
  store {{ptr, i64, i64, i64, i64}, i64} %si.8, ptr %t2.a.9
  %l.10 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %t2.a.9
  store {{ptr, i64, i64, i64, i64}, i64} %l.10, ptr %st.a.11
  %sp.12 = getelementptr inbounds [3 x i8], ptr @.str.3, i64 0, i64 0
  %s.13 = insertvalue {ptr, i64} undef, ptr %sp.12, 0
  %s.14 = insertvalue {ptr, i64} %s.13, i64 3, 1
  store {ptr, i64} %s.14, ptr %t3.a.15
  %sp.16 = getelementptr inbounds [3 x i8], ptr @.str.4, i64 0, i64 0
  %s.17 = insertvalue {ptr, i64} undef, ptr %sp.16, 0
  %s.18 = insertvalue {ptr, i64} %s.17, i64 3, 1
  store {ptr, i64} %s.18, ptr %t4.a.19
  %l.20 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %st.a.11
  %l.21 = load {ptr, i64}, ptr %t3.a.15
  %l.22 = load {ptr, i64}, ptr %t4.a.19
  %c.23 = call {{ptr, i64, i64, i64, i64}, i64} @add_decl({{ptr, i64, i64, i64, i64}, i64} %l.20, {ptr, i64} %l.21, {ptr, i64} %l.22)
  store {{ptr, i64, i64, i64, i64}, i64} %c.23, ptr %t5.a.24
  %l.25 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %t5.a.24
  store {{ptr, i64, i64, i64, i64}, i64} %l.25, ptr %st.a.11
  %sp.26 = getelementptr inbounds [3 x i8], ptr @.str.5, i64 0, i64 0
  %s.27 = insertvalue {ptr, i64} undef, ptr %sp.26, 0
  %s.28 = insertvalue {ptr, i64} %s.27, i64 3, 1
  store {ptr, i64} %s.28, ptr %t6.a.29
  %sp.30 = getelementptr inbounds [4 x i8], ptr @.str.6, i64 0, i64 0
  %s.31 = insertvalue {ptr, i64} undef, ptr %sp.30, 0
  %s.32 = insertvalue {ptr, i64} %s.31, i64 4, 1
  store {ptr, i64} %s.32, ptr %t7.a.33
  %l.34 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %st.a.11
  %l.35 = load {ptr, i64}, ptr %t6.a.29
  %l.36 = load {ptr, i64}, ptr %t7.a.33
  %c.37 = call {{ptr, i64, i64, i64, i64}, i64} @add_decl({{ptr, i64, i64, i64, i64}, i64} %l.34, {ptr, i64} %l.35, {ptr, i64} %l.36)
  store {{ptr, i64, i64, i64, i64}, i64} %c.37, ptr %t8.a.38
  %l.39 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %t8.a.38
  store {{ptr, i64, i64, i64, i64}, i64} %l.39, ptr %st.a.11
  %sp.40 = getelementptr inbounds [3 x i8], ptr @.str.7, i64 0, i64 0
  %s.41 = insertvalue {ptr, i64} undef, ptr %sp.40, 0
  %s.42 = insertvalue {ptr, i64} %s.41, i64 3, 1
  store {ptr, i64} %s.42, ptr %t9.a.43
  %sp.44 = getelementptr inbounds [6 x i8], ptr @.str.8, i64 0, i64 0
  %s.45 = insertvalue {ptr, i64} undef, ptr %sp.44, 0
  %s.46 = insertvalue {ptr, i64} %s.45, i64 6, 1
  store {ptr, i64} %s.46, ptr %t10.a.47
  %l.48 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %st.a.11
  %l.49 = load {ptr, i64}, ptr %t9.a.43
  %l.50 = load {ptr, i64}, ptr %t10.a.47
  %c.51 = call {{ptr, i64, i64, i64, i64}, i64} @add_decl({{ptr, i64, i64, i64, i64}, i64} %l.48, {ptr, i64} %l.49, {ptr, i64} %l.50)
  store {{ptr, i64, i64, i64, i64}, i64} %c.51, ptr %t11.a.52
  %l.53 = load {{ptr, i64, i64, i64, i64}, i64}, ptr %t11.a.52
  store {{ptr, i64, i64, i64, i64}, i64} %l.53, ptr %st.a.11
  %sp.54 = getelementptr inbounds [1 x i8], ptr @.str.9, i64 0, i64 0
  %s.55 = insertvalue {ptr, i64} undef, ptr %sp.54, 0
  %s.56 = insertvalue {ptr, i64} %s.55, i64 1, 1
  store {ptr, i64} %s.56, ptr %t12.a.57
  %fg.58 = getelementptr inbounds {{ptr, i64, i64, i64, i64}, i64}, ptr %st.a.11, i32 0, i32 0
  %fv.59 = load {ptr, i64, i64, i64, i64}, ptr %fg.58
  store {ptr, i64, i64, i64, i64} %fv.59, ptr %t13.a.60
  %l.61 = load {ptr, i64}, ptr %t12.a.57
  %l.62 = load {ptr, i64, i64, i64, i64}, ptr %t13.a.60
  store {ptr, i64, i64, i64, i64} %l.62, ptr %jl.63
  %rt.64 = call {ptr, i64} @__mn_str_join({ptr, i64} %l.61, ptr %jl.63)
  store {ptr, i64} %rt.64, ptr %str_track.65
  store {ptr, i64} %rt.64, ptr %t14.a.66
  %l.67 = load {ptr, i64}, ptr %t14.a.66
  call void @__mn_str_println({ptr, i64} %l.67)
  store i1 0, ptr %t15.a.68
  %drop.s.69 = load {ptr, i64}, ptr %str_track.65
  %drop.p.70 = extractvalue {ptr, i64} %drop.s.69, 0
  %drop.null.71 = icmp eq ptr %drop.p.70, null
  br i1 %drop.null.71, label %drop.skip.72, label %drop.check.72
drop.check.72:
  call void @__mn_str_free({ptr, i64} %drop.s.69)
  br label %drop.skip.72
drop.skip.72:
  %drop.lv.73 = load {ptr, i64, i64, i64, i64}, ptr %empty.a.3
  %drop.lp.74 = extractvalue {ptr, i64, i64, i64, i64} %drop.lv.73, 0
  %drop.lnull.75 = icmp eq ptr %drop.lp.74, null
  br i1 %drop.lnull.75, label %drop.lskip.76, label %drop.lcheck.76
drop.lcheck.76:
  call void @__mn_list_free(ptr %empty.a.3)
  br label %drop.lskip.76
drop.lskip.76:
  call void @__mn_intern_destroy()
  ret i64 0
}


!mapanare.version = !{!0}
!0 = !{!"4.101.0"}
!1 = !{!"Mapanare TBAA"}
!2 = !{!"int", !1}
!3 = !{!"float", !1}
!4 = !{!"ptr", !1}
!5 = !{!"bool", !1}
!6 = !{!2, !2, i64 0}
!7 = !{!3, !3, i64 0}
!8 = !{!4, !4, i64 0}
!9 = !{!5, !5, i64 0}
