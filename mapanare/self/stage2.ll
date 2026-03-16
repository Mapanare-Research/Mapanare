; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/mapanare/self/main.mn'
source_filename = "/mnt/c/Users/Juan/Documents/GitHub/Mapanare/mapanare/self/main.mn"

@.newline = private constant [2 x i8] c"\0A\00"
@.fmt_int = private constant [4 x i8] c"%ld\00"
@.fmt_int_nl = private constant [5 x i8] c"%ld\0A\00"
@.fmt_float = private constant [4 x i8] c"%lf\00"
@.fmt_float_nl = private constant [5 x i8] c"%lf\0A\00"

declare { i8*, i64 } @__mn_str_concat({ i8*, i64 }, { i8*, i64 })
declare i64 @__mn_str_eq({ i8*, i64 }, { i8*, i64 })
declare i64 @__mn_str_cmp({ i8*, i64 }, { i8*, i64 })
declare i64 @__mn_str_len({ i8*, i64 })
declare { i8*, i64 } @__mn_str_char_at({ i8*, i64 }, i64)
declare i64 @__mn_str_byte_at({ i8*, i64 }, i64)
declare { i8*, i64 } @__mn_str_substr({ i8*, i64 }, i64, i64)
declare { i8*, i64 } @__mn_str_from_int(i64)
declare { i8*, i64 } @__mn_str_from_bool(i1)
declare { i8*, i64 } @__mn_str_from_float(double)
declare i64 @__mn_str_to_int({ i8*, i64 })
declare double @__mn_str_to_float({ i8*, i64 })
declare void @__mn_str_println({ i8*, i64 })
declare void @__mn_str_print({ i8*, i64 })
declare i1 @__mn_str_starts_with({ i8*, i64 }, { i8*, i64 })
declare i1 @__mn_str_ends_with({ i8*, i64 }, { i8*, i64 })
declare i64 @__mn_str_find({ i8*, i64 }, { i8*, i64 })
declare { i8*, i64, i64, i64 } @__mn_list_new(i64)
declare void @__mn_list_push({ i8*, i64, i64, i64 }*, i8*)
declare i8* @__mn_list_get({ i8*, i64, i64, i64 }*, i64)
declare i64 @__mn_list_len({ i8*, i64, i64, i64 }*)
declare { i8*, i64 } @__mn_str_to_upper({ i8*, i64 })
declare { i8*, i64 } @__mn_str_to_lower({ i8*, i64 })
declare { i8*, i64 } @__mn_str_replace({ i8*, i64 }, { i8*, i64 }, { i8*, i64 })
declare { i8*, i64, i64, i64 } @__mn_str_split({ i8*, i64 }, { i8*, i64 })
declare { i8*, i64 } @__mn_str_trim({ i8*, i64 })
declare i1 @__mn_str_contains({ i8*, i64 }, { i8*, i64 })
declare void @__mn_panic({ i8*, i64 })
declare i32 @printf(i8*, ...)
declare i8* @__mapanare_tensor_add(i8*, i8*)
declare i8* @__mapanare_tensor_sub(i8*, i8*)
declare i8* @__mapanare_tensor_mul(i8*, i8*)
declare i8* @__mapanare_tensor_div(i8*, i8*)
declare i8* @__mapanare_matmul(i8*, i8*)
declare i8* @__mapanare_tensor_alloc(i64, i64*, i64)
declare void @__mapanare_tensor_free(i8*)
declare i1 @__mapanare_tensor_shape_eq(i8*, i8*)
declare i8* @__mapanare_detect_gpus()
declare i8* @__mn_agent_spawn(i8*, i8*)
declare void @__mn_agent_send(i8*, i8*, i8*)
declare i8* @__mn_agent_sync(i8*, i8*)
declare i8* @__mn_signal_new(i8*)
declare i8* @__mn_signal_get(i8*)
declare void @__mn_signal_set(i8*, i8*)

%struct.CompileResult = type { i1, { i8*, i64 }, { i8*, i64, i64, i64 } }

define %struct.CompileResult @new_compile_result(i1 %success, { i8*, i64 } %ir_text, { i8*, i64, i64, i64 } %errors) {
entry:
  %t0 = add i64 0, 6019782
  ret i64 %t0
}

define { i8*, i64 } @version() {
entry:
  %t0 =insertvalue { i1, i8* } undef, i1 0, 0
  ret { i1, i8* } %t0
}

define %struct.CompileResult @compile({ i8*, i64 } %source, { i8*, i64 } %filename) {
entry:
  %t0 =call i64 @parse({ i8*, i64 } %source, { i8*, i64 } %filename)
  %program =add i64 %t0, 0
  %t1 =call i64 @check(i64 %program, { i8*, i64 } %filename)
  %errors =add i64 %t1, 0
  %t2 =call i64 @__mn_list_len({ i8*, i64, i64, i64 }* %errors)
  %t3 = add i64 0, 0
  %t4 =icmp sgt i64 %t2, %t3
if_then0:
  %t5 =insertvalue { i1, i8* } undef, i1 0, 0
  ret { i1, i8* } %t5
if_else1:
  br label %if_merge2
if_merge2:
  br i1 %t4, label %if_then0, label %if_else1
  %t7 =call i64 @lower(i64 %program, { i8*, i64 } %filename)
  %mir_module =add i64 %t7, 0
  %t8 =call i64 @emit_mir_module(i64 %mir_module, { i8*, i64 } %filename)
  %ir_text =add i64 %t8, 0
  %t9.new =call { i8*, i64, i64, i64 } @__mn_list_new(i64 8)
  %t9.addr =alloca { i8*, i64, i64, i64 }
  store { i8*, i64, i64, i64 } %t9.new, { i8*, i64, i64, i64 }* %t9.addr
  %t9 =load { i8*, i64, i64, i64 }, { i8*, i64, i64, i64 }* %t9.addr
  %no_errors.addr =alloca { i8*, i64, i64, i64 }
  store { i8*, i64, i64, i64 } %t9, { i8*, i64, i64, i64 }* %no_errors.addr
  %no_errors =load { i8*, i64, i64, i64 }, { i8*, i64, i64, i64 }* %no_errors.addr
  %t10 =insertvalue { i1, i8* } undef, i1 0, 0
  ret { i1, i8* } %t10
}

define { i8*, i64 } @format_error(%struct.SemanticError %err) {
entry:
  %t0 =insertvalue { i1, i8* } undef, i1 0, 0
  ret { i1, i8* } %t0
}

define %struct.CompileResult @compile_and_print({ i8*, i64 } %source, { i8*, i64 } %filename) {
entry:
  %t0 =call %struct.CompileResult @compile({ i8*, i64 } %source, { i8*, i64 } %filename)
  %cr =add i64 %t0, 0
  %t1 =extractvalue i64 %cr, 0
if_then0:
  %t2 =extractvalue i64 %cr, 0
  call i32 (i8*, ...) @printf(i8* @.fmt_int_nl, i64 %t2)
  br label %if_merge2
if_else1:
  br label %if_merge2
if_merge2:
  br i1 %t1, label %if_then0, label %if_else1
  %if_result4 = phi i64 [ %t3, %if_then0 ], [ %void, %if_else1 ]
  %t5 =insertvalue { i1, i8* } undef, i1 0, 0
  ret { i1, i8* } %t5
}

define void @main() {
entry:
  %t0 =insertvalue { i1, i8* } undef, i1 0, 0
  ret void
}

