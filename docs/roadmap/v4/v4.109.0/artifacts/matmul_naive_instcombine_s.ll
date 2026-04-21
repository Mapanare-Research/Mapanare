; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/matmul_naive_stripped.bc'
source_filename = "matmul_naive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

declare { ptr, i64, i64, i64, i64 } @__mn_list_new(i64)

declare void @__mn_list_push(ptr, ptr)

declare ptr @__mn_list_get(ptr, i64)

declare { ptr, i64 } @__mn_str_from_int(i64)

declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 })

declare void @__mn_str_println({ ptr, i64 })

declare void @__mn_str_free({ ptr, i64 })

declare void @free(ptr)

declare void @__mn_list_free(ptr)

declare void @__mn_intern_destroy()

define i64 @main() {
pre_entry:
  %n.a.0 = alloca i64, align 8
  store i64 0, ptr %n.a.0, align 8
  %t1.a.1 = alloca i64, align 8
  store i64 0, ptr %t1.a.1, align 8
  %t2.a.3 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store ptr null, ptr %t2.a.3, align 8
  %t2.a.3.repack1 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 1
  store i64 0, ptr %t2.a.3.repack1, align 8
  %t2.a.3.repack2 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 2
  store i64 0, ptr %t2.a.3.repack2, align 8
  %t2.a.3.repack3 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 3
  store i64 0, ptr %t2.a.3.repack3, align 8
  %t2.a.3.repack4 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 4
  store i64 0, ptr %t2.a.3.repack4, align 8
  %a.a.5 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store ptr null, ptr %a.a.5, align 8
  %a.a.5.repack5 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 1
  store i64 0, ptr %a.a.5.repack5, align 8
  %a.a.5.repack6 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 2
  store i64 0, ptr %a.a.5.repack6, align 8
  %a.a.5.repack7 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 3
  store i64 0, ptr %a.a.5.repack7, align 8
  %a.a.5.repack8 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 4
  store i64 0, ptr %a.a.5.repack8, align 8
  %t3.a.7 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store ptr null, ptr %t3.a.7, align 8
  %t3.a.7.repack9 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 1
  store i64 0, ptr %t3.a.7.repack9, align 8
  %t3.a.7.repack10 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 2
  store i64 0, ptr %t3.a.7.repack10, align 8
  %t3.a.7.repack11 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 3
  store i64 0, ptr %t3.a.7.repack11, align 8
  %t3.a.7.repack12 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 4
  store i64 0, ptr %t3.a.7.repack12, align 8
  %b.a.9 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store ptr null, ptr %b.a.9, align 8
  %b.a.9.repack13 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 1
  store i64 0, ptr %b.a.9.repack13, align 8
  %b.a.9.repack14 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 2
  store i64 0, ptr %b.a.9.repack14, align 8
  %b.a.9.repack15 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 3
  store i64 0, ptr %b.a.9.repack15, align 8
  %b.a.9.repack16 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 4
  store i64 0, ptr %b.a.9.repack16, align 8
  %t4.a.11 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store ptr null, ptr %t4.a.11, align 8
  %t4.a.11.repack17 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 1
  store i64 0, ptr %t4.a.11.repack17, align 8
  %t4.a.11.repack18 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 2
  store i64 0, ptr %t4.a.11.repack18, align 8
  %t4.a.11.repack19 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 3
  store i64 0, ptr %t4.a.11.repack19, align 8
  %t4.a.11.repack20 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 4
  store i64 0, ptr %t4.a.11.repack20, align 8
  %c.a.13 = alloca { ptr, i64, i64, i64, i64 }, align 8
  store ptr null, ptr %c.a.13, align 8
  %c.a.13.repack21 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  store i64 0, ptr %c.a.13.repack21, align 8
  %c.a.13.repack22 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  store i64 0, ptr %c.a.13.repack22, align 8
  %c.a.13.repack23 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  store i64 0, ptr %c.a.13.repack23, align 8
  %c.a.13.repack24 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  store i64 0, ptr %c.a.13.repack24, align 8
  %idx.a.16 = alloca i64, align 8
  store i64 0, ptr %idx.a.16, align 8
  %ea.38 = alloca i64, align 8
  %ea.56 = alloca i64, align 8
  %ea.60 = alloca i64, align 8
  %i.a.70 = alloca i64, align 8
  store i64 0, ptr %i.a.70, align 8
  %j.a.78 = alloca i64, align 8
  store i64 0, ptr %j.a.78, align 8
  %t45.a.79 = alloca i64, align 8
  store i64 0, ptr %t45.a.79, align 8
  %lp.82 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t46.a.84 = alloca ptr, align 8
  store ptr null, ptr %t46.a.84, align 8
  %t48.a.85 = alloca i64, align 8
  store i64 0, ptr %t48.a.85, align 8
  %lp.88 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t50.a.96 = alloca i64, align 8
  store i64 0, ptr %t50.a.96, align 8
  %t53.a.97 = alloca i64, align 8
  store i64 0, ptr %t53.a.97, align 8
  %lp.100 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t55.a.107 = alloca i64, align 8
  store i64 0, ptr %t55.a.107, align 8
  %t57.a.108 = alloca i64, align 8
  store i64 0, ptr %t57.a.108, align 8
  %lp.111 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t60.a.122 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %t60.a.122, align 8
  %t60.a.122.repack25 = getelementptr inbounds { ptr, i64 }, ptr %t60.a.122, i64 0, i32 1
  store i64 0, ptr %t60.a.122.repack25, align 8
  %str_track.125 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %str_track.125, align 8
  %str_track.125.repack26 = getelementptr inbounds { ptr, i64 }, ptr %str_track.125, i64 0, i32 1
  store i64 0, ptr %str_track.125.repack26, align 8
  %t61.a.126 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %t61.a.126, align 8
  %t61.a.126.repack27 = getelementptr inbounds { ptr, i64 }, ptr %t61.a.126, i64 0, i32 1
  store i64 0, ptr %t61.a.126.repack27, align 8
  %str_track.130 = alloca { ptr, i64 }, align 8
  store ptr null, ptr %str_track.130, align 8
  %str_track.130.repack28 = getelementptr inbounds { ptr, i64 }, ptr %str_track.130, i64 0, i32 1
  store i64 0, ptr %str_track.130.repack28, align 8
  %sum.a.161 = alloca i64, align 8
  store i64 0, ptr %sum.a.161, align 8
  %k.a.164 = alloca i64, align 8
  store i64 0, ptr %k.a.164, align 8
  %t30.a.183 = alloca i64, align 8
  store i64 0, ptr %t30.a.183, align 8
  %lp.186 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t31.a.188 = alloca ptr, align 8
  store ptr null, ptr %t31.a.188, align 8
  %t33.a.196 = alloca i64, align 8
  store i64 0, ptr %t33.a.196, align 8
  %lp.199 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %t40.a.226 = alloca i64, align 8
  store i64 0, ptr %t40.a.226, align 8
  %lp.230 = alloca { ptr, i64, i64, i64, i64 }, align 8
  br label %entry

entry:                                            ; preds = %pre_entry
  store i64 64, ptr %n.a.0, align 8
  store i64 4096, ptr %t1.a.1, align 8
  %ln.2 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.2.elt = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 0
  store ptr %ln.2.elt, ptr %t2.a.3, align 8
  %t2.a.3.repack30 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 1
  %ln.2.elt31 = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 1
  store i64 %ln.2.elt31, ptr %t2.a.3.repack30, align 8
  %t2.a.3.repack32 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 2
  %ln.2.elt33 = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 2
  store i64 %ln.2.elt33, ptr %t2.a.3.repack32, align 8
  %t2.a.3.repack34 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 3
  %ln.2.elt35 = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 3
  store i64 %ln.2.elt35, ptr %t2.a.3.repack34, align 8
  %t2.a.3.repack36 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 4
  %ln.2.elt37 = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 4
  store i64 %ln.2.elt37, ptr %t2.a.3.repack36, align 8
  %l.4.unpack = load ptr, ptr %t2.a.3, align 8
  %l.4.elt38 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 1
  %l.4.unpack39 = load i64, ptr %l.4.elt38, align 8
  %l.4.elt40 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 2
  %l.4.unpack41 = load i64, ptr %l.4.elt40, align 8
  %l.4.elt42 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 3
  %l.4.unpack43 = load i64, ptr %l.4.elt42, align 8
  %l.4.elt44 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 4
  %l.4.unpack45 = load i64, ptr %l.4.elt44, align 8
  store ptr %l.4.unpack, ptr %a.a.5, align 8
  %a.a.5.repack47 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 1
  store i64 %l.4.unpack39, ptr %a.a.5.repack47, align 8
  %a.a.5.repack49 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 2
  store i64 %l.4.unpack41, ptr %a.a.5.repack49, align 8
  %a.a.5.repack51 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 3
  store i64 %l.4.unpack43, ptr %a.a.5.repack51, align 8
  %a.a.5.repack53 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 4
  store i64 %l.4.unpack45, ptr %a.a.5.repack53, align 8
  %ln.6 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.6.elt = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 0
  store ptr %ln.6.elt, ptr %t3.a.7, align 8
  %t3.a.7.repack55 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 1
  %ln.6.elt56 = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 1
  store i64 %ln.6.elt56, ptr %t3.a.7.repack55, align 8
  %t3.a.7.repack57 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 2
  %ln.6.elt58 = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 2
  store i64 %ln.6.elt58, ptr %t3.a.7.repack57, align 8
  %t3.a.7.repack59 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 3
  %ln.6.elt60 = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 3
  store i64 %ln.6.elt60, ptr %t3.a.7.repack59, align 8
  %t3.a.7.repack61 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 4
  %ln.6.elt62 = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 4
  store i64 %ln.6.elt62, ptr %t3.a.7.repack61, align 8
  %l.8.unpack = load ptr, ptr %t3.a.7, align 8
  %l.8.elt63 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 1
  %l.8.unpack64 = load i64, ptr %l.8.elt63, align 8
  %l.8.elt65 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 2
  %l.8.unpack66 = load i64, ptr %l.8.elt65, align 8
  %l.8.elt67 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 3
  %l.8.unpack68 = load i64, ptr %l.8.elt67, align 8
  %l.8.elt69 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 4
  %l.8.unpack70 = load i64, ptr %l.8.elt69, align 8
  store ptr %l.8.unpack, ptr %b.a.9, align 8
  %b.a.9.repack72 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 1
  store i64 %l.8.unpack64, ptr %b.a.9.repack72, align 8
  %b.a.9.repack74 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 2
  store i64 %l.8.unpack66, ptr %b.a.9.repack74, align 8
  %b.a.9.repack76 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 3
  store i64 %l.8.unpack68, ptr %b.a.9.repack76, align 8
  %b.a.9.repack78 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 4
  store i64 %l.8.unpack70, ptr %b.a.9.repack78, align 8
  %ln.10 = call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.10.elt = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 0
  store ptr %ln.10.elt, ptr %t4.a.11, align 8
  %t4.a.11.repack80 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 1
  %ln.10.elt81 = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 1
  store i64 %ln.10.elt81, ptr %t4.a.11.repack80, align 8
  %t4.a.11.repack82 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 2
  %ln.10.elt83 = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 2
  store i64 %ln.10.elt83, ptr %t4.a.11.repack82, align 8
  %t4.a.11.repack84 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 3
  %ln.10.elt85 = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 3
  store i64 %ln.10.elt85, ptr %t4.a.11.repack84, align 8
  %t4.a.11.repack86 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 4
  %ln.10.elt87 = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 4
  store i64 %ln.10.elt87, ptr %t4.a.11.repack86, align 8
  %l.12.unpack = load ptr, ptr %t4.a.11, align 8
  %l.12.elt88 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 1
  %l.12.unpack89 = load i64, ptr %l.12.elt88, align 8
  %l.12.elt90 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 2
  %l.12.unpack91 = load i64, ptr %l.12.elt90, align 8
  %l.12.elt92 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 3
  %l.12.unpack93 = load i64, ptr %l.12.elt92, align 8
  %l.12.elt94 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 4
  %l.12.unpack95 = load i64, ptr %l.12.elt94, align 8
  store ptr %l.12.unpack, ptr %c.a.13, align 8
  %c.a.13.repack97 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  store i64 %l.12.unpack89, ptr %c.a.13.repack97, align 8
  %c.a.13.repack99 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  store i64 %l.12.unpack91, ptr %c.a.13.repack99, align 8
  %c.a.13.repack101 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  store i64 %l.12.unpack93, ptr %c.a.13.repack101, align 8
  %c.a.13.repack103 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  store i64 %l.12.unpack95, ptr %c.a.13.repack103, align 8
  br label %while_header0

while_header0:                                    ; preds = %while_body1, %entry
  %storemerge = phi i64 [ 0, %entry ], [ %i.65, %while_body1 ]
  store i64 %storemerge, ptr %idx.a.16, align 8
  %l.18 = load i64, ptr %t1.a.1, align 8
  %i.19 = icmp slt i64 %storemerge, %l.18
  br i1 %i.19, label %while_body1, label %while_exit2

while_body1:                                      ; preds = %while_header0
  %l.23 = load i64, ptr %idx.a.16, align 8
  %i.25 = mul i64 %l.23, 3
  %i.30 = add i64 %i.25, 7
  %i.35 = srem i64 %i.30, 100
  store i64 %i.35, ptr %ea.38, align 8
  call void @__mn_list_push(ptr nonnull %t2.a.3, ptr nonnull %ea.38)
  %ul.39.unpack = load ptr, ptr %t2.a.3, align 8
  %ul.39.elt280 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 1
  %ul.39.unpack281 = load i64, ptr %ul.39.elt280, align 8
  %ul.39.elt282 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 2
  %ul.39.unpack283 = load i64, ptr %ul.39.elt282, align 8
  %ul.39.elt284 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 3
  %ul.39.unpack285 = load i64, ptr %ul.39.elt284, align 8
  %ul.39.elt286 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 4
  %ul.39.unpack287 = load i64, ptr %ul.39.elt286, align 8
  store ptr %ul.39.unpack, ptr %a.a.5, align 8
  %a.a.5.repack289 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 1
  store i64 %ul.39.unpack281, ptr %a.a.5.repack289, align 8
  %a.a.5.repack291 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 2
  store i64 %ul.39.unpack283, ptr %a.a.5.repack291, align 8
  %a.a.5.repack293 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 3
  store i64 %ul.39.unpack285, ptr %a.a.5.repack293, align 8
  %a.a.5.repack295 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 4
  store i64 %ul.39.unpack287, ptr %a.a.5.repack295, align 8
  %l.41 = load i64, ptr %idx.a.16, align 8
  %i.43 = mul i64 %l.41, 5
  %i.48 = add i64 %i.43, 13
  %i.53 = srem i64 %i.48, 100
  store i64 %i.53, ptr %ea.56, align 8
  call void @__mn_list_push(ptr nonnull %t3.a.7, ptr nonnull %ea.56)
  %ul.57.unpack = load ptr, ptr %t3.a.7, align 8
  %ul.57.elt297 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 1
  %ul.57.unpack298 = load i64, ptr %ul.57.elt297, align 8
  %ul.57.elt299 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 2
  %ul.57.unpack300 = load i64, ptr %ul.57.elt299, align 8
  %ul.57.elt301 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 3
  %ul.57.unpack302 = load i64, ptr %ul.57.elt301, align 8
  %ul.57.elt303 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 4
  %ul.57.unpack304 = load i64, ptr %ul.57.elt303, align 8
  store ptr %ul.57.unpack, ptr %b.a.9, align 8
  %b.a.9.repack306 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 1
  store i64 %ul.57.unpack298, ptr %b.a.9.repack306, align 8
  %b.a.9.repack308 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 2
  store i64 %ul.57.unpack300, ptr %b.a.9.repack308, align 8
  %b.a.9.repack310 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 3
  store i64 %ul.57.unpack302, ptr %b.a.9.repack310, align 8
  %b.a.9.repack312 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 4
  store i64 %ul.57.unpack304, ptr %b.a.9.repack312, align 8
  store i64 0, ptr %ea.60, align 8
  call void @__mn_list_push(ptr nonnull %t4.a.11, ptr nonnull %ea.60)
  %ul.61.unpack = load ptr, ptr %t4.a.11, align 8
  %ul.61.elt314 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 1
  %ul.61.unpack315 = load i64, ptr %ul.61.elt314, align 8
  %ul.61.elt316 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 2
  %ul.61.unpack317 = load i64, ptr %ul.61.elt316, align 8
  %ul.61.elt318 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 3
  %ul.61.unpack319 = load i64, ptr %ul.61.elt318, align 8
  %ul.61.elt320 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 4
  %ul.61.unpack321 = load i64, ptr %ul.61.elt320, align 8
  store ptr %ul.61.unpack, ptr %c.a.13, align 8
  %c.a.13.repack323 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  store i64 %ul.61.unpack315, ptr %c.a.13.repack323, align 8
  %c.a.13.repack325 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  store i64 %ul.61.unpack317, ptr %c.a.13.repack325, align 8
  %c.a.13.repack327 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  store i64 %ul.61.unpack319, ptr %c.a.13.repack327, align 8
  %c.a.13.repack329 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  store i64 %ul.61.unpack321, ptr %c.a.13.repack329, align 8
  %l.63 = load i64, ptr %idx.a.16, align 8
  %i.65 = add i64 %l.63, 1
  br label %while_header0

while_exit2:                                      ; preds = %while_header0
  br label %while_header3

while_header3:                                    ; preds = %while_exit8, %while_exit2
  %storemerge105 = phi i64 [ 0, %while_exit2 ], [ %i.168, %while_exit8 ]
  store i64 %storemerge105, ptr %i.a.70, align 8
  %l.72 = load i64, ptr %n.a.0, align 8
  %i.73 = icmp slt i64 %storemerge105, %l.72
  br i1 %i.73, label %while_body4, label %while_exit5

while_body4:                                      ; preds = %while_header3
  br label %while_header6

while_exit5:                                      ; preds = %while_header3
  store i64 0, ptr %t45.a.79, align 8
  %l.80.unpack = load ptr, ptr %c.a.13, align 8
  %l.80.elt106 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  %l.80.unpack107 = load i64, ptr %l.80.elt106, align 8
  %l.80.elt108 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  %l.80.unpack109 = load i64, ptr %l.80.elt108, align 8
  %l.80.elt110 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  %l.80.unpack111 = load i64, ptr %l.80.elt110, align 8
  %l.80.elt112 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  %l.80.unpack113 = load i64, ptr %l.80.elt112, align 8
  %l.81 = load i64, ptr %t45.a.79, align 8
  store ptr %l.80.unpack, ptr %lp.82, align 8
  %lp.82.repack115 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 1
  store i64 %l.80.unpack107, ptr %lp.82.repack115, align 8
  %lp.82.repack117 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 2
  store i64 %l.80.unpack109, ptr %lp.82.repack117, align 8
  %lp.82.repack119 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 3
  store i64 %l.80.unpack111, ptr %lp.82.repack119, align 8
  %lp.82.repack121 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 4
  store i64 %l.80.unpack113, ptr %lp.82.repack121, align 8
  %rt.83 = call ptr @__mn_list_get(ptr nonnull %lp.82, i64 %l.81)
  store ptr %rt.83, ptr %t46.a.84, align 8
  store i64 63, ptr %t48.a.85, align 8
  %l.86.unpack = load ptr, ptr %c.a.13, align 8
  %l.86.elt123 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  %l.86.unpack124 = load i64, ptr %l.86.elt123, align 8
  %l.86.elt125 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  %l.86.unpack126 = load i64, ptr %l.86.elt125, align 8
  %l.86.elt127 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  %l.86.unpack128 = load i64, ptr %l.86.elt127, align 8
  %l.86.elt129 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  %l.86.unpack130 = load i64, ptr %l.86.elt129, align 8
  %l.87 = load i64, ptr %t48.a.85, align 8
  store ptr %l.86.unpack, ptr %lp.88, align 8
  %lp.88.repack132 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 1
  store i64 %l.86.unpack124, ptr %lp.88.repack132, align 8
  %lp.88.repack134 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 2
  store i64 %l.86.unpack126, ptr %lp.88.repack134, align 8
  %lp.88.repack136 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 3
  store i64 %l.86.unpack128, ptr %lp.88.repack136, align 8
  %lp.88.repack138 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 4
  store i64 %l.86.unpack130, ptr %lp.88.repack138, align 8
  %rt.89 = call ptr @__mn_list_get(ptr nonnull %lp.88, i64 %l.87)
  %l.91 = load ptr, ptr %t46.a.84, align 8
  %p2i.93 = ptrtoint ptr %l.91 to i64
  %p2i.94 = ptrtoint ptr %rt.89 to i64
  %i.95 = add i64 %p2i.93, %p2i.94
  store i64 %i.95, ptr %t50.a.96, align 8
  store i64 4032, ptr %t53.a.97, align 8
  %l.98.unpack = load ptr, ptr %c.a.13, align 8
  %l.98.elt140 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  %l.98.unpack141 = load i64, ptr %l.98.elt140, align 8
  %l.98.elt142 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  %l.98.unpack143 = load i64, ptr %l.98.elt142, align 8
  %l.98.elt144 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  %l.98.unpack145 = load i64, ptr %l.98.elt144, align 8
  %l.98.elt146 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  %l.98.unpack147 = load i64, ptr %l.98.elt146, align 8
  %l.99 = load i64, ptr %t53.a.97, align 8
  store ptr %l.98.unpack, ptr %lp.100, align 8
  %lp.100.repack149 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 1
  store i64 %l.98.unpack141, ptr %lp.100.repack149, align 8
  %lp.100.repack151 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 2
  store i64 %l.98.unpack143, ptr %lp.100.repack151, align 8
  %lp.100.repack153 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 3
  store i64 %l.98.unpack145, ptr %lp.100.repack153, align 8
  %lp.100.repack155 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 4
  store i64 %l.98.unpack147, ptr %lp.100.repack155, align 8
  %rt.101 = call ptr @__mn_list_get(ptr nonnull %lp.100, i64 %l.99)
  %l.103 = load i64, ptr %t50.a.96, align 8
  %p2i.105 = ptrtoint ptr %rt.101 to i64
  %i.106 = add i64 %l.103, %p2i.105
  store i64 %i.106, ptr %t55.a.107, align 8
  store i64 4095, ptr %t57.a.108, align 8
  %l.109.unpack = load ptr, ptr %c.a.13, align 8
  %l.109.elt157 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  %l.109.unpack158 = load i64, ptr %l.109.elt157, align 8
  %l.109.elt159 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  %l.109.unpack160 = load i64, ptr %l.109.elt159, align 8
  %l.109.elt161 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  %l.109.unpack162 = load i64, ptr %l.109.elt161, align 8
  %l.109.elt163 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  %l.109.unpack164 = load i64, ptr %l.109.elt163, align 8
  %l.110 = load i64, ptr %t57.a.108, align 8
  store ptr %l.109.unpack, ptr %lp.111, align 8
  %lp.111.repack166 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 1
  store i64 %l.109.unpack158, ptr %lp.111.repack166, align 8
  %lp.111.repack168 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 2
  store i64 %l.109.unpack160, ptr %lp.111.repack168, align 8
  %lp.111.repack170 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 3
  store i64 %l.109.unpack162, ptr %lp.111.repack170, align 8
  %lp.111.repack172 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 4
  store i64 %l.109.unpack164, ptr %lp.111.repack172, align 8
  %rt.112 = call ptr @__mn_list_get(ptr nonnull %lp.111, i64 %l.110)
  %l.114 = load i64, ptr %t55.a.107, align 8
  %p2i.116 = ptrtoint ptr %rt.112 to i64
  %i.117 = add i64 %l.114, %p2i.116
  store ptr @.str.0, ptr %t60.a.122, align 8
  %t60.a.122.repack174 = getelementptr inbounds { ptr, i64 }, ptr %t60.a.122, i64 0, i32 1
  store i64 11, ptr %t60.a.122.repack174, align 8
  %rt.124 = call { ptr, i64 } @__mn_str_from_int(i64 %i.117)
  %rt.124.elt = extractvalue { ptr, i64 } %rt.124, 0
  store ptr %rt.124.elt, ptr %str_track.125, align 8
  %str_track.125.repack175 = getelementptr inbounds { ptr, i64 }, ptr %str_track.125, i64 0, i32 1
  %rt.124.elt176 = extractvalue { ptr, i64 } %rt.124, 1
  store i64 %rt.124.elt176, ptr %str_track.125.repack175, align 8
  %rt.124.elt177 = extractvalue { ptr, i64 } %rt.124, 0
  store ptr %rt.124.elt177, ptr %t61.a.126, align 8
  %t61.a.126.repack178 = getelementptr inbounds { ptr, i64 }, ptr %t61.a.126, i64 0, i32 1
  %rt.124.elt179 = extractvalue { ptr, i64 } %rt.124, 1
  store i64 %rt.124.elt179, ptr %t61.a.126.repack178, align 8
  %l.127.unpack = load ptr, ptr %t60.a.122, align 8
  %0 = insertvalue { ptr, i64 } poison, ptr %l.127.unpack, 0
  %l.127.elt180 = getelementptr inbounds { ptr, i64 }, ptr %t60.a.122, i64 0, i32 1
  %l.127.unpack181 = load i64, ptr %l.127.elt180, align 8
  %l.127182 = insertvalue { ptr, i64 } %0, i64 %l.127.unpack181, 1
  %l.128.unpack = load ptr, ptr %t61.a.126, align 8
  %1 = insertvalue { ptr, i64 } poison, ptr %l.128.unpack, 0
  %l.128.elt183 = getelementptr inbounds { ptr, i64 }, ptr %t61.a.126, i64 0, i32 1
  %l.128.unpack184 = load i64, ptr %l.128.elt183, align 8
  %l.128185 = insertvalue { ptr, i64 } %1, i64 %l.128.unpack184, 1
  %rt.129 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } %l.127182, { ptr, i64 } %l.128185)
  %rt.129.elt = extractvalue { ptr, i64 } %rt.129, 0
  store ptr %rt.129.elt, ptr %str_track.130, align 8
  %str_track.130.repack186 = getelementptr inbounds { ptr, i64 }, ptr %str_track.130, i64 0, i32 1
  %rt.129.elt187 = extractvalue { ptr, i64 } %rt.129, 1
  store i64 %rt.129.elt187, ptr %str_track.130.repack186, align 8
  call void @__mn_str_println({ ptr, i64 } %rt.129)
  %drop.s.134.unpack = load ptr, ptr %str_track.125, align 8
  %drop.null.136 = icmp eq ptr %drop.s.134.unpack, null
  br i1 %drop.null.136, label %drop.skip.137, label %drop.check.137

while_header6:                                    ; preds = %while_exit11, %while_body4
  %storemerge227 = phi i64 [ 0, %while_body4 ], [ %i.235, %while_exit11 ]
  store i64 %storemerge227, ptr %j.a.78, align 8
  %l.155 = load i64, ptr %n.a.0, align 8
  %i.156 = icmp slt i64 %storemerge227, %l.155
  br i1 %i.156, label %while_body7, label %while_exit8

while_body7:                                      ; preds = %while_header6
  store i64 0, ptr %sum.a.161, align 8
  br label %while_header9

while_exit8:                                      ; preds = %while_header6
  %l.166 = load i64, ptr %i.a.70, align 8
  %i.168 = add i64 %l.166, 1
  br label %while_header3

while_header9:                                    ; preds = %while_body10, %while_body7
  %storemerge228 = phi i64 [ 0, %while_body7 ], [ %i.216, %while_body10 ]
  store i64 %storemerge228, ptr %k.a.164, align 8
  %l.172 = load i64, ptr %n.a.0, align 8
  %i.173 = icmp slt i64 %storemerge228, %l.172
  br i1 %i.173, label %while_body10, label %while_exit11

while_body10:                                     ; preds = %while_header9
  %l.176 = load i64, ptr %i.a.70, align 8
  %l.177 = load i64, ptr %n.a.0, align 8
  %i.178 = mul i64 %l.176, %l.177
  %l.181 = load i64, ptr %k.a.164, align 8
  %i.182 = add i64 %i.178, %l.181
  store i64 %i.182, ptr %t30.a.183, align 8
  %l.184.unpack = load ptr, ptr %a.a.5, align 8
  %l.184.elt246 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 1
  %l.184.unpack247 = load i64, ptr %l.184.elt246, align 8
  %l.184.elt248 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 2
  %l.184.unpack249 = load i64, ptr %l.184.elt248, align 8
  %l.184.elt250 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 3
  %l.184.unpack251 = load i64, ptr %l.184.elt250, align 8
  %l.184.elt252 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 4
  %l.184.unpack253 = load i64, ptr %l.184.elt252, align 8
  %l.185 = load i64, ptr %t30.a.183, align 8
  store ptr %l.184.unpack, ptr %lp.186, align 8
  %lp.186.repack255 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 1
  store i64 %l.184.unpack247, ptr %lp.186.repack255, align 8
  %lp.186.repack257 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 2
  store i64 %l.184.unpack249, ptr %lp.186.repack257, align 8
  %lp.186.repack259 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 3
  store i64 %l.184.unpack251, ptr %lp.186.repack259, align 8
  %lp.186.repack261 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 4
  store i64 %l.184.unpack253, ptr %lp.186.repack261, align 8
  %rt.187 = call ptr @__mn_list_get(ptr nonnull %lp.186, i64 %l.185)
  store ptr %rt.187, ptr %t31.a.188, align 8
  %l.189 = load i64, ptr %k.a.164, align 8
  %l.190 = load i64, ptr %n.a.0, align 8
  %i.191 = mul i64 %l.189, %l.190
  %l.194 = load i64, ptr %j.a.78, align 8
  %i.195 = add i64 %i.191, %l.194
  store i64 %i.195, ptr %t33.a.196, align 8
  %l.197.unpack = load ptr, ptr %b.a.9, align 8
  %l.197.elt263 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 1
  %l.197.unpack264 = load i64, ptr %l.197.elt263, align 8
  %l.197.elt265 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 2
  %l.197.unpack266 = load i64, ptr %l.197.elt265, align 8
  %l.197.elt267 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 3
  %l.197.unpack268 = load i64, ptr %l.197.elt267, align 8
  %l.197.elt269 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 4
  %l.197.unpack270 = load i64, ptr %l.197.elt269, align 8
  %l.198 = load i64, ptr %t33.a.196, align 8
  store ptr %l.197.unpack, ptr %lp.199, align 8
  %lp.199.repack272 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 1
  store i64 %l.197.unpack264, ptr %lp.199.repack272, align 8
  %lp.199.repack274 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 2
  store i64 %l.197.unpack266, ptr %lp.199.repack274, align 8
  %lp.199.repack276 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 3
  store i64 %l.197.unpack268, ptr %lp.199.repack276, align 8
  %lp.199.repack278 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 4
  store i64 %l.197.unpack270, ptr %lp.199.repack278, align 8
  %rt.200 = call ptr @__mn_list_get(ptr nonnull %lp.199, i64 %l.198)
  %l.202 = load ptr, ptr %t31.a.188, align 8
  %p2i.204 = ptrtoint ptr %l.202 to i64
  %p2i.205 = ptrtoint ptr %rt.200 to i64
  %i.206 = mul i64 %p2i.204, %p2i.205
  %l.208 = load i64, ptr %sum.a.161, align 8
  %i.210 = add i64 %l.208, %i.206
  store i64 %i.210, ptr %sum.a.161, align 8
  %l.214 = load i64, ptr %k.a.164, align 8
  %i.216 = add i64 %l.214, 1
  br label %while_header9

while_exit11:                                     ; preds = %while_header9
  %l.219 = load i64, ptr %i.a.70, align 8
  %l.220 = load i64, ptr %n.a.0, align 8
  %i.221 = mul i64 %l.219, %l.220
  %l.224 = load i64, ptr %j.a.78, align 8
  %i.225 = add i64 %i.221, %l.224
  store i64 %i.225, ptr %t40.a.226, align 8
  %l.227.unpack = load ptr, ptr %c.a.13, align 8
  %l.227.elt229 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  %l.227.unpack230 = load i64, ptr %l.227.elt229, align 8
  %l.227.elt231 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  %l.227.unpack232 = load i64, ptr %l.227.elt231, align 8
  %l.227.elt233 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  %l.227.unpack234 = load i64, ptr %l.227.elt233, align 8
  %l.227.elt235 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  %l.227.unpack236 = load i64, ptr %l.227.elt235, align 8
  %l.228 = load i64, ptr %t40.a.226, align 8
  %l.229 = load i64, ptr %sum.a.161, align 8
  store ptr %l.227.unpack, ptr %lp.230, align 8
  %lp.230.repack238 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 1
  store i64 %l.227.unpack230, ptr %lp.230.repack238, align 8
  %lp.230.repack240 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 2
  store i64 %l.227.unpack232, ptr %lp.230.repack240, align 8
  %lp.230.repack242 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 3
  store i64 %l.227.unpack234, ptr %lp.230.repack242, align 8
  %lp.230.repack244 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 4
  store i64 %l.227.unpack236, ptr %lp.230.repack244, align 8
  %rt.231 = call ptr @__mn_list_get(ptr nonnull %lp.230, i64 %l.228)
  store i64 %l.229, ptr %rt.231, align 8
  %l.233 = load i64, ptr %j.a.78, align 8
  %i.235 = add i64 %l.233, 1
  br label %while_header6

drop.check.137:                                   ; preds = %while_exit5
  %2 = insertvalue { ptr, i64 } poison, ptr %drop.s.134.unpack, 0
  %drop.s.134.elt194 = getelementptr inbounds { ptr, i64 }, ptr %str_track.125, i64 0, i32 1
  %drop.s.134.unpack195 = load i64, ptr %drop.s.134.elt194, align 8
  %drop.s.134196 = insertvalue { ptr, i64 } %2, i64 %drop.s.134.unpack195, 1
  call void @__mn_str_free({ ptr, i64 } %drop.s.134196)
  br label %drop.skip.137

drop.skip.137:                                    ; preds = %drop.check.137, %while_exit5
  %drop.s.138.unpack = load ptr, ptr %str_track.130, align 8
  %drop.null.140 = icmp eq ptr %drop.s.138.unpack, null
  br i1 %drop.null.140, label %drop.skip.141, label %drop.check.141

drop.check.141:                                   ; preds = %drop.skip.137
  %3 = insertvalue { ptr, i64 } poison, ptr %drop.s.138.unpack, 0
  %drop.s.138.elt197 = getelementptr inbounds { ptr, i64 }, ptr %str_track.130, i64 0, i32 1
  %drop.s.138.unpack198 = load i64, ptr %drop.s.138.elt197, align 8
  %drop.s.138199 = insertvalue { ptr, i64 } %3, i64 %drop.s.138.unpack198, 1
  call void @__mn_str_free({ ptr, i64 } %drop.s.138199)
  br label %drop.skip.141

drop.skip.141:                                    ; preds = %drop.check.141, %drop.skip.137
  %drop.lv.142.unpack = load ptr, ptr %a.a.5, align 8
  %drop.lnull.144 = icmp eq ptr %drop.lv.142.unpack, null
  br i1 %drop.lnull.144, label %drop.lskip.145, label %drop.lcheck.145

drop.lcheck.145:                                  ; preds = %drop.skip.141
  call void @__mn_list_free(ptr nonnull %a.a.5)
  br label %drop.lskip.145

drop.lskip.145:                                   ; preds = %drop.lcheck.145, %drop.skip.141
  %drop.lv.146.unpack = load ptr, ptr %b.a.9, align 8
  %drop.lnull.148 = icmp eq ptr %drop.lv.146.unpack, null
  br i1 %drop.lnull.148, label %drop.lskip.149, label %drop.lcheck.149

drop.lcheck.149:                                  ; preds = %drop.lskip.145
  call void @__mn_list_free(ptr nonnull %b.a.9)
  br label %drop.lskip.149

drop.lskip.149:                                   ; preds = %drop.lcheck.149, %drop.lskip.145
  %drop.lv.150.unpack = load ptr, ptr %c.a.13, align 8
  %drop.lnull.152 = icmp eq ptr %drop.lv.150.unpack, null
  br i1 %drop.lnull.152, label %drop.lskip.153, label %drop.lcheck.153

drop.lcheck.153:                                  ; preds = %drop.lskip.149
  call void @__mn_list_free(ptr nonnull %c.a.13)
  br label %drop.lskip.153

drop.lskip.153:                                   ; preds = %drop.lcheck.153, %drop.lskip.149
  call void @__mn_intern_destroy()
  ret i64 0
}

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
