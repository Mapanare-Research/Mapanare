; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/string_concat_stripped.bc'
source_filename = "string_concat"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [0 x i8] zeroinitializer, align 8
@.str.1 = private constant [5 x i8] c"hello", align 8
@.str.2 = private constant [6 x i8] c"len = ", align 8

declare ptr @__mn_sb_new(i64) local_unnamed_addr

declare void @__mn_sb_append(ptr, { ptr, i64 }) local_unnamed_addr

declare { ptr, i64 } @__mn_sb_finish(ptr) local_unnamed_addr

declare i64 @__mn_str_len({ ptr, i64 }) local_unnamed_addr

declare { ptr, i64 } @__mn_str_from_int(i64) local_unnamed_addr

declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 }) local_unnamed_addr

declare void @__mn_str_println({ ptr, i64 }) local_unnamed_addr

declare void @__mn_str_free({ ptr, i64 }) local_unnamed_addr

declare void @__mn_intern_destroy() local_unnamed_addr

define noundef i64 @main() local_unnamed_addr {
pre_entry:
  %rt.11 = tail call ptr @__mn_sb_new(i64 64)
  tail call void @__mn_sb_append(ptr %rt.11, { ptr, i64 } { ptr @.str.0, i64 0 })
  br label %while_body1

while_body1:                                      ; preds = %pre_entry, %while_body1
  %i.a.8.09 = phi i64 [ 0, %pre_entry ], [ %i.32, %while_body1 ]
  tail call void @__mn_sb_append(ptr %rt.11, { ptr, i64 } { ptr @.str.1, i64 5 })
  %i.32 = add nuw nsw i64 %i.a.8.09, 1
  %exitcond.not = icmp eq i64 %i.32, 10000
  br i1 %exitcond.not, label %while_exit2, label %while_body1

while_exit2:                                      ; preds = %while_body1
  %rt.36 = tail call { ptr, i64 } @__mn_sb_finish(ptr %rt.11)
  %rt.36.fca.0.extract = extractvalue { ptr, i64 } %rt.36, 0
  %rt.43 = tail call i64 @__mn_str_len({ ptr, i64 } %rt.36)
  %rt.46 = tail call { ptr, i64 } @__mn_str_from_int(i64 %rt.43)
  %rt.46.fca.0.extract3 = extractvalue { ptr, i64 } %rt.46, 0
  %rt.51 = tail call { ptr, i64 } @__mn_str_concat({ ptr, i64 } { ptr @.str.2, i64 6 }, { ptr, i64 } %rt.46)
  %rt.51.fca.0.extract1 = extractvalue { ptr, i64 } %rt.51, 0
  tail call void @__mn_str_println({ ptr, i64 } %rt.51)
  %drop.null.58 = icmp eq ptr %rt.36.fca.0.extract, null
  br i1 %drop.null.58, label %drop.skip.59, label %drop.check.59

drop.check.59:                                    ; preds = %while_exit2
  tail call void @__mn_str_free({ ptr, i64 } %rt.36)
  br label %drop.skip.59

drop.skip.59:                                     ; preds = %drop.check.59, %while_exit2
  %drop.null.62 = icmp eq ptr %rt.46.fca.0.extract3, null
  br i1 %drop.null.62, label %drop.skip.63, label %drop.check.63

drop.check.63:                                    ; preds = %drop.skip.59
  tail call void @__mn_str_free({ ptr, i64 } %rt.46)
  br label %drop.skip.63

drop.skip.63:                                     ; preds = %drop.check.63, %drop.skip.59
  %drop.null.66 = icmp eq ptr %rt.51.fca.0.extract1, null
  br i1 %drop.null.66, label %drop.skip.67, label %drop.check.67

drop.check.67:                                    ; preds = %drop.skip.63
  tail call void @__mn_str_free({ ptr, i64 } %rt.51)
  br label %drop.skip.67

drop.skip.67:                                     ; preds = %drop.check.67, %drop.skip.63
  tail call void @__mn_intern_destroy()
  ret i64 0
}

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
