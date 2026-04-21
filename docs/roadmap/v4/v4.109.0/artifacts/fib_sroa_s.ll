; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/fib_stripped.bc'
source_filename = "fib_recursive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [10 x i8] c"fib(35) = ", align 8

declare { ptr, i64 } @__mn_str_from_int(i64)

declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 })

declare void @__mn_str_println({ ptr, i64 })

declare void @__mn_str_free({ ptr, i64 })

declare void @free(ptr)

declare void @__mn_intern_destroy()

define internal i64 @fib(i64 %n) {
pre_entry:
  br label %entry

entry:                                            ; preds = %pre_entry
  %i.3 = icmp sle i64 %n, 1
  br i1 %i.3, label %if_then0, label %if_else1

if_then0:                                         ; preds = %entry
  ret i64 %n

if_else1:                                         ; preds = %entry
  br label %if_merge2

if_merge2:                                        ; preds = %if_else1
  %i.10 = sub i64 %n, 1
  %c.13 = call i64 @fib(i64 %i.10)
  %i.18 = sub i64 %n, 2
  %c.21 = call i64 @fib(i64 %i.18)
  %i.25 = add i64 %c.13, %c.21
  ret i64 %i.25
}

define i64 @main() {
pre_entry:
  br label %entry

entry:                                            ; preds = %pre_entry
  %c.2 = call i64 @fib(i64 35)
  %sp.4 = getelementptr inbounds [10 x i8], ptr @.str.0, i64 0, i64 0
  %s.5 = insertvalue { ptr, i64 } undef, ptr %sp.4, 0
  %s.6 = insertvalue { ptr, i64 } %s.5, i64 10, 1
  %s.6.fca.0.extract = extractvalue { ptr, i64 } %s.6, 0
  %s.6.fca.1.extract = extractvalue { ptr, i64 } %s.6, 1
  %rt.9 = call { ptr, i64 } @__mn_str_from_int(i64 %c.2)
  %rt.9.fca.0.extract3 = extractvalue { ptr, i64 } %rt.9, 0
  %rt.9.fca.1.extract4 = extractvalue { ptr, i64 } %rt.9, 1
  %rt.9.fca.0.extract = extractvalue { ptr, i64 } %rt.9, 0
  %rt.9.fca.1.extract = extractvalue { ptr, i64 } %rt.9, 1
  %l.12.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %s.6.fca.0.extract, 0
  %l.12.fca.1.insert = insertvalue { ptr, i64 } %l.12.fca.0.insert, i64 %s.6.fca.1.extract, 1
  %l.13.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.9.fca.0.extract, 0
  %l.13.fca.1.insert = insertvalue { ptr, i64 } %l.13.fca.0.insert, i64 %rt.9.fca.1.extract, 1
  %rt.14 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } %l.12.fca.1.insert, { ptr, i64 } %l.13.fca.1.insert)
  %rt.14.fca.0.extract1 = extractvalue { ptr, i64 } %rt.14, 0
  %rt.14.fca.1.extract2 = extractvalue { ptr, i64 } %rt.14, 1
  %rt.14.fca.0.extract = extractvalue { ptr, i64 } %rt.14, 0
  %rt.14.fca.1.extract = extractvalue { ptr, i64 } %rt.14, 1
  %l.17.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.14.fca.0.extract, 0
  %l.17.fca.1.insert = insertvalue { ptr, i64 } %l.17.fca.0.insert, i64 %rt.14.fca.1.extract, 1
  call void @__mn_str_println({ ptr, i64 } %l.17.fca.1.insert)
  %drop.s.19.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.9.fca.0.extract3, 0
  %drop.s.19.fca.1.insert = insertvalue { ptr, i64 } %drop.s.19.fca.0.insert, i64 %rt.9.fca.1.extract4, 1
  %drop.p.20 = extractvalue { ptr, i64 } %drop.s.19.fca.1.insert, 0
  %drop.null.21 = icmp eq ptr %drop.p.20, null
  br i1 %drop.null.21, label %drop.skip.22, label %drop.check.22

drop.check.22:                                    ; preds = %entry
  call void @__mn_str_free({ ptr, i64 } %drop.s.19.fca.1.insert)
  br label %drop.skip.22

drop.skip.22:                                     ; preds = %drop.check.22, %entry
  %drop.s.23.fca.0.insert = insertvalue { ptr, i64 } poison, ptr %rt.14.fca.0.extract1, 0
  %drop.s.23.fca.1.insert = insertvalue { ptr, i64 } %drop.s.23.fca.0.insert, i64 %rt.14.fca.1.extract2, 1
  %drop.p.24 = extractvalue { ptr, i64 } %drop.s.23.fca.1.insert, 0
  %drop.null.25 = icmp eq ptr %drop.p.24, null
  br i1 %drop.null.25, label %drop.skip.26, label %drop.check.26

drop.check.26:                                    ; preds = %drop.skip.22
  call void @__mn_str_free({ ptr, i64 } %drop.s.23.fca.1.insert)
  br label %drop.skip.26

drop.skip.26:                                     ; preds = %drop.check.26, %drop.skip.22
  call void @__mn_intern_destroy()
  ret i64 0
}

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
