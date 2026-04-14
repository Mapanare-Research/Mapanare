; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/fib.bc'
source_filename = "fib_recursive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [10 x i8] c"fib(35) = ", align 8

; Function Attrs: mustprogress nounwind willreturn
declare { ptr, i64 } @__mn_str_from_int(i64) local_unnamed_addr #0

; Function Attrs: mustprogress nounwind willreturn
declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 }) local_unnamed_addr #0

declare void @__mn_str_println({ ptr, i64 }) local_unnamed_addr

; Function Attrs: mustprogress nounwind willreturn
declare void @__mn_str_free({ ptr, i64 }) local_unnamed_addr #0

declare void @__mn_intern_destroy() local_unnamed_addr

; Function Attrs: mustprogress nofree nosync nounwind willreturn memory(none)
define internal fastcc i64 @fib(i64 %n) unnamed_addr #1 {
pre_entry:
  %i.34 = icmp slt i64 %n, 2
  br i1 %i.34, label %common.ret, label %if_merge2

common.ret:                                       ; preds = %if_merge2, %pre_entry
  %accumulator.tr.lcssa = phi i64 [ 0, %pre_entry ], [ %i.25, %if_merge2 ]
  %n.tr.lcssa = phi i64 [ %n, %pre_entry ], [ %i.18, %if_merge2 ]
  %accumulator.ret.tr = add nsw i64 %n.tr.lcssa, %accumulator.tr.lcssa
  ret i64 %accumulator.ret.tr

if_merge2:                                        ; preds = %pre_entry, %if_merge2
  %n.tr6 = phi i64 [ %i.18, %if_merge2 ], [ %n, %pre_entry ]
  %accumulator.tr5 = phi i64 [ %i.25, %if_merge2 ], [ 0, %pre_entry ]
  %i.10 = add nsw i64 %n.tr6, -1
  %c.13 = tail call fastcc i64 @fib(i64 %i.10)
  %i.18 = add nsw i64 %n.tr6, -2
  %i.25 = add nsw i64 %c.13, %accumulator.tr5
  %i.3 = icmp ult i64 %n.tr6, 4
  br i1 %i.3, label %common.ret, label %if_merge2
}

; Function Attrs: mustprogress nounwind willreturn
define noundef i64 @main() local_unnamed_addr #0 {
pre_entry:
  %c.2 = tail call fastcc i64 @fib(i64 35)
  %rt.9 = tail call { ptr, i64 } @__mn_str_from_int(i64 %c.2)
  %rt.9.fca.0.extract3 = extractvalue { ptr, i64 } %rt.9, 0
  %rt.14 = tail call { ptr, i64 } @__mn_str_concat({ ptr, i64 } { ptr @.str.0, i64 10 }, { ptr, i64 } %rt.9)
  %rt.14.fca.0.extract1 = extractvalue { ptr, i64 } %rt.14, 0
  tail call void @__mn_str_println({ ptr, i64 } %rt.14) #2
  %drop.null.21 = icmp eq ptr %rt.9.fca.0.extract3, null
  br i1 %drop.null.21, label %drop.skip.22, label %drop.check.22

drop.check.22:                                    ; preds = %pre_entry
  tail call void @__mn_str_free({ ptr, i64 } %rt.9)
  br label %drop.skip.22

drop.skip.22:                                     ; preds = %drop.check.22, %pre_entry
  %drop.null.25 = icmp eq ptr %rt.14.fca.0.extract1, null
  br i1 %drop.null.25, label %drop.skip.26, label %drop.check.26

drop.check.26:                                    ; preds = %drop.skip.22
  tail call void @__mn_str_free({ ptr, i64 } %rt.14)
  br label %drop.skip.26

drop.skip.26:                                     ; preds = %drop.check.26, %drop.skip.22
  tail call void @__mn_intern_destroy() #2
  ret i64 0
}

attributes #0 = { mustprogress nounwind willreturn }
attributes #1 = { mustprogress nofree nosync nounwind willreturn memory(none) }
attributes #2 = { nounwind }

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
