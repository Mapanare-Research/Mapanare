; ModuleID = '/mnt/c/Users/Juan/Documents/GitHub/Mapanare/docs/roadmap/v4/v4.109.0/artifacts/matmul_naive.bc'
source_filename = "matmul_naive"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str.0 = private constant [11 x i8] c"checksum = ", align 8

; Function Attrs: mustprogress nounwind willreturn
declare { ptr, i64, i64, i64, i64 } @__mn_list_new(i64) local_unnamed_addr #0

; Function Attrs: nounwind
declare void @__mn_list_push(ptr, ptr) local_unnamed_addr #1

; Function Attrs: nounwind
declare ptr @__mn_list_get(ptr, i64) local_unnamed_addr #1

; Function Attrs: mustprogress nounwind willreturn
declare { ptr, i64 } @__mn_str_from_int(i64) local_unnamed_addr #0

; Function Attrs: mustprogress nounwind willreturn
declare { ptr, i64 } @__mn_str_concat({ ptr, i64 }, { ptr, i64 }) local_unnamed_addr #0

declare void @__mn_str_println({ ptr, i64 }) local_unnamed_addr

; Function Attrs: mustprogress nounwind willreturn
declare void @__mn_str_free({ ptr, i64 }) local_unnamed_addr #0

; Function Attrs: mustprogress nounwind willreturn
declare void @__mn_list_free(ptr) local_unnamed_addr #0

declare void @__mn_intern_destroy() local_unnamed_addr

; Function Attrs: mustprogress nounwind willreturn
define noundef i64 @main() local_unnamed_addr #0 {
pre_entry:
  %t2.a.3 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.1.gep94 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 1
  %.fca.2.gep95 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 2
  %.fca.3.gep96 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 3
  %.fca.4.gep97 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t2.a.3, i64 0, i32 4
  %a.a.5 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.1.gep84 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 1
  %.fca.2.gep85 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 2
  %.fca.3.gep86 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 3
  %.fca.4.gep87 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %a.a.5, i64 0, i32 4
  %t3.a.7 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.1.gep69 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 1
  %.fca.2.gep70 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 2
  %.fca.3.gep71 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 3
  %.fca.4.gep72 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t3.a.7, i64 0, i32 4
  %b.a.9 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.1.gep59 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 1
  %.fca.2.gep60 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 2
  %.fca.3.gep61 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 3
  %.fca.4.gep62 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %b.a.9, i64 0, i32 4
  %t4.a.11 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %0 = getelementptr inbounds i8, ptr %b.a.9, i64 8
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %0, i8 0, i64 32, i1 false)
  %.fca.1.gep44 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 1
  %.fca.2.gep45 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 2
  %.fca.3.gep46 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 3
  %.fca.4.gep47 = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %t4.a.11, i64 0, i32 4
  %c.a.13 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 1
  %.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 2
  %.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 3
  %.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %c.a.13, i64 0, i32 4
  %ea.38 = alloca i64, align 8
  %ea.56 = alloca i64, align 8
  %ea.60 = alloca i64, align 8
  %lp.82 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.88 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.100 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.111 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.186 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.199 = alloca { ptr, i64, i64, i64, i64 }, align 8
  %lp.230 = alloca { ptr, i64, i64, i64, i64 }, align 8
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(40) %c.a.13, i8 0, i64 40, i1 false)
  %ln.2 = tail call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.2.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 0
  store ptr %ln.2.fca.0.extract, ptr %t2.a.3, align 8
  %ln.2.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 1
  store i64 %ln.2.fca.1.extract, ptr %.fca.1.gep94, align 8
  %ln.2.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 2
  store i64 %ln.2.fca.2.extract, ptr %.fca.2.gep95, align 8
  %ln.2.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 3
  store i64 %ln.2.fca.3.extract, ptr %.fca.3.gep96, align 8
  %ln.2.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.2, 4
  store i64 %ln.2.fca.4.extract, ptr %.fca.4.gep97, align 8
  store ptr %ln.2.fca.0.extract, ptr %a.a.5, align 8
  store i64 %ln.2.fca.1.extract, ptr %.fca.1.gep84, align 8
  store i64 %ln.2.fca.2.extract, ptr %.fca.2.gep85, align 8
  store i64 %ln.2.fca.3.extract, ptr %.fca.3.gep86, align 8
  store i64 %ln.2.fca.4.extract, ptr %.fca.4.gep87, align 8
  %ln.6 = tail call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.6.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 0
  store ptr %ln.6.fca.0.extract, ptr %t3.a.7, align 8
  %ln.6.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 1
  store i64 %ln.6.fca.1.extract, ptr %.fca.1.gep69, align 8
  %ln.6.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 2
  store i64 %ln.6.fca.2.extract, ptr %.fca.2.gep70, align 8
  %ln.6.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 3
  store i64 %ln.6.fca.3.extract, ptr %.fca.3.gep71, align 8
  %ln.6.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.6, 4
  store i64 %ln.6.fca.4.extract, ptr %.fca.4.gep72, align 8
  store ptr %ln.6.fca.0.extract, ptr %b.a.9, align 8
  %ln.10 = tail call { ptr, i64, i64, i64, i64 } @__mn_list_new(i64 8)
  %ln.10.fca.0.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 0
  store ptr %ln.10.fca.0.extract, ptr %t4.a.11, align 8
  %ln.10.fca.1.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 1
  store i64 %ln.10.fca.1.extract, ptr %.fca.1.gep44, align 8
  %ln.10.fca.2.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 2
  store i64 %ln.10.fca.2.extract, ptr %.fca.2.gep45, align 8
  %ln.10.fca.3.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 3
  store i64 %ln.10.fca.3.extract, ptr %.fca.3.gep46, align 8
  %ln.10.fca.4.extract = extractvalue { ptr, i64, i64, i64, i64 } %ln.10, 4
  store i64 %ln.10.fca.4.extract, ptr %.fca.4.gep47, align 8
  br label %while_body1

while_header3.preheader:                          ; preds = %while_body1
  %l.184.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 1
  %l.184.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 2
  %l.184.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 3
  %l.184.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.186, i64 0, i32 4
  %l.197.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 1
  %l.197.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 2
  %l.197.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 3
  %l.197.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.199, i64 0, i32 4
  %l.227.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 1
  %l.227.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 2
  %l.227.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 3
  %l.227.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.230, i64 0, i32 4
  br label %while_header6.preheader

while_body1:                                      ; preds = %pre_entry, %while_body1
  %idx.a.16.0115 = phi i64 [ 0, %pre_entry ], [ %i.65, %while_body1 ]
  %1 = trunc i64 %idx.a.16.0115 to i16
  %2 = mul nuw i16 %1, 3
  %i.35.lhs.trunc = add nuw nsw i16 %2, 7
  %i.35113 = urem i16 %i.35.lhs.trunc, 100
  %i.35.zext = zext nneg i16 %i.35113 to i64
  store i64 %i.35.zext, ptr %ea.38, align 8
  call void @__mn_list_push(ptr nonnull %t2.a.3, ptr nonnull %ea.38)
  %ul.39.fca.0.load = load ptr, ptr %t2.a.3, align 8
  %ul.39.fca.1.load = load i64, ptr %.fca.1.gep94, align 8
  %ul.39.fca.2.load = load i64, ptr %.fca.2.gep95, align 8
  %ul.39.fca.3.load = load i64, ptr %.fca.3.gep96, align 8
  %ul.39.fca.4.load = load i64, ptr %.fca.4.gep97, align 8
  store ptr %ul.39.fca.0.load, ptr %a.a.5, align 8
  store i64 %ul.39.fca.1.load, ptr %.fca.1.gep84, align 8
  store i64 %ul.39.fca.2.load, ptr %.fca.2.gep85, align 8
  store i64 %ul.39.fca.3.load, ptr %.fca.3.gep86, align 8
  store i64 %ul.39.fca.4.load, ptr %.fca.4.gep87, align 8
  %3 = mul nuw i16 %1, 5
  %i.53.lhs.trunc = add nuw i16 %3, 13
  %i.53114 = urem i16 %i.53.lhs.trunc, 100
  %i.53.zext = zext nneg i16 %i.53114 to i64
  store i64 %i.53.zext, ptr %ea.56, align 8
  call void @__mn_list_push(ptr nonnull %t3.a.7, ptr nonnull %ea.56)
  %ul.57.fca.0.load = load ptr, ptr %t3.a.7, align 8
  %ul.57.fca.1.load = load i64, ptr %.fca.1.gep69, align 8
  %ul.57.fca.2.load = load i64, ptr %.fca.2.gep70, align 8
  %ul.57.fca.3.load = load i64, ptr %.fca.3.gep71, align 8
  %ul.57.fca.4.load = load i64, ptr %.fca.4.gep72, align 8
  store ptr %ul.57.fca.0.load, ptr %b.a.9, align 8
  store i64 %ul.57.fca.1.load, ptr %.fca.1.gep59, align 8
  store i64 %ul.57.fca.2.load, ptr %.fca.2.gep60, align 8
  store i64 %ul.57.fca.3.load, ptr %.fca.3.gep61, align 8
  store i64 %ul.57.fca.4.load, ptr %.fca.4.gep62, align 8
  store i64 0, ptr %ea.60, align 8
  call void @__mn_list_push(ptr nonnull %t4.a.11, ptr nonnull %ea.60)
  %ul.61.fca.0.load = load ptr, ptr %t4.a.11, align 8
  %ul.61.fca.1.load = load i64, ptr %.fca.1.gep44, align 8
  %ul.61.fca.2.load = load i64, ptr %.fca.2.gep45, align 8
  %ul.61.fca.3.load = load i64, ptr %.fca.3.gep46, align 8
  %ul.61.fca.4.load = load i64, ptr %.fca.4.gep47, align 8
  store ptr %ul.61.fca.0.load, ptr %c.a.13, align 8
  store i64 %ul.61.fca.1.load, ptr %.fca.1.gep, align 8
  store i64 %ul.61.fca.2.load, ptr %.fca.2.gep, align 8
  store i64 %ul.61.fca.3.load, ptr %.fca.3.gep, align 8
  store i64 %ul.61.fca.4.load, ptr %.fca.4.gep, align 8
  %i.65 = add nuw nsw i64 %idx.a.16.0115, 1
  %exitcond.not = icmp eq i64 %i.65, 4096
  br i1 %exitcond.not, label %while_header3.preheader, label %while_body1

while_header6.preheader:                          ; preds = %while_header3.preheader, %while_exit8
  %i.a.70.0119 = phi i64 [ 0, %while_header3.preheader ], [ %i.168, %while_exit8 ]
  %i.178 = shl nuw nsw i64 %i.a.70.0119, 6
  br label %while_header9.preheader

while_exit5:                                      ; preds = %while_exit8
  store ptr %ul.61.fca.0.load, ptr %lp.82, align 8
  %l.80.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 1
  store i64 %ul.61.fca.1.load, ptr %l.80.fca.1.gep, align 8
  %l.80.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 2
  store i64 %ul.61.fca.2.load, ptr %l.80.fca.2.gep, align 8
  %l.80.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 3
  store i64 %ul.61.fca.3.load, ptr %l.80.fca.3.gep, align 8
  %l.80.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.82, i64 0, i32 4
  store i64 %ul.61.fca.4.load, ptr %l.80.fca.4.gep, align 8
  %rt.83 = call ptr @__mn_list_get(ptr nonnull %lp.82, i64 0)
  store ptr %ul.61.fca.0.load, ptr %lp.88, align 8
  %l.86.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 1
  store i64 %ul.61.fca.1.load, ptr %l.86.fca.1.gep, align 8
  %l.86.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 2
  store i64 %ul.61.fca.2.load, ptr %l.86.fca.2.gep, align 8
  %l.86.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 3
  store i64 %ul.61.fca.3.load, ptr %l.86.fca.3.gep, align 8
  %l.86.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.88, i64 0, i32 4
  store i64 %ul.61.fca.4.load, ptr %l.86.fca.4.gep, align 8
  %rt.89 = call ptr @__mn_list_get(ptr nonnull %lp.88, i64 63)
  %p2i.93 = ptrtoint ptr %rt.83 to i64
  %p2i.94 = ptrtoint ptr %rt.89 to i64
  %i.95 = add nsw i64 %p2i.94, %p2i.93
  store ptr %ul.61.fca.0.load, ptr %lp.100, align 8
  %l.98.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 1
  store i64 %ul.61.fca.1.load, ptr %l.98.fca.1.gep, align 8
  %l.98.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 2
  store i64 %ul.61.fca.2.load, ptr %l.98.fca.2.gep, align 8
  %l.98.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 3
  store i64 %ul.61.fca.3.load, ptr %l.98.fca.3.gep, align 8
  %l.98.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.100, i64 0, i32 4
  store i64 %ul.61.fca.4.load, ptr %l.98.fca.4.gep, align 8
  %rt.101 = call ptr @__mn_list_get(ptr nonnull %lp.100, i64 4032)
  %p2i.105 = ptrtoint ptr %rt.101 to i64
  %i.106 = add nsw i64 %i.95, %p2i.105
  store ptr %ul.61.fca.0.load, ptr %lp.111, align 8
  %l.109.fca.1.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 1
  store i64 %ul.61.fca.1.load, ptr %l.109.fca.1.gep, align 8
  %l.109.fca.2.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 2
  store i64 %ul.61.fca.2.load, ptr %l.109.fca.2.gep, align 8
  %l.109.fca.3.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 3
  store i64 %ul.61.fca.3.load, ptr %l.109.fca.3.gep, align 8
  %l.109.fca.4.gep = getelementptr inbounds { ptr, i64, i64, i64, i64 }, ptr %lp.111, i64 0, i32 4
  store i64 %ul.61.fca.4.load, ptr %l.109.fca.4.gep, align 8
  %rt.112 = call ptr @__mn_list_get(ptr nonnull %lp.111, i64 4095)
  %p2i.116 = ptrtoint ptr %rt.112 to i64
  %i.117 = add nsw i64 %i.106, %p2i.116
  %rt.124 = call { ptr, i64 } @__mn_str_from_int(i64 %i.117)
  %rt.124.fca.0.extract7 = extractvalue { ptr, i64 } %rt.124, 0
  %rt.129 = call { ptr, i64 } @__mn_str_concat({ ptr, i64 } { ptr @.str.0, i64 11 }, { ptr, i64 } %rt.124)
  %rt.129.fca.0.extract5 = extractvalue { ptr, i64 } %rt.129, 0
  call void @__mn_str_println({ ptr, i64 } %rt.129) #1
  %drop.null.136 = icmp eq ptr %rt.124.fca.0.extract7, null
  br i1 %drop.null.136, label %drop.skip.137, label %drop.check.137

while_header9.preheader:                          ; preds = %while_header6.preheader, %while_exit11
  %j.a.78.0118 = phi i64 [ 0, %while_header6.preheader ], [ %i.235, %while_exit11 ]
  br label %while_body10

while_exit8:                                      ; preds = %while_exit11
  %i.168 = add nuw nsw i64 %i.a.70.0119, 1
  %exitcond122.not = icmp eq i64 %i.168, 64
  br i1 %exitcond122.not, label %while_exit5, label %while_header6.preheader

while_body10:                                     ; preds = %while_header9.preheader, %while_body10
  %k.a.164.0117 = phi i64 [ 0, %while_header9.preheader ], [ %i.216, %while_body10 ]
  %sum.a.161.0116 = phi i64 [ 0, %while_header9.preheader ], [ %i.210, %while_body10 ]
  %i.182 = add nuw nsw i64 %k.a.164.0117, %i.178
  store ptr %ul.39.fca.0.load, ptr %lp.186, align 8
  store i64 %ul.39.fca.1.load, ptr %l.184.fca.1.gep, align 8
  store i64 %ul.39.fca.2.load, ptr %l.184.fca.2.gep, align 8
  store i64 %ul.39.fca.3.load, ptr %l.184.fca.3.gep, align 8
  store i64 %ul.39.fca.4.load, ptr %l.184.fca.4.gep, align 8
  %rt.187 = call ptr @__mn_list_get(ptr nonnull %lp.186, i64 %i.182)
  %i.191 = shl nuw nsw i64 %k.a.164.0117, 6
  %i.195 = add nuw nsw i64 %i.191, %j.a.78.0118
  store ptr %ul.57.fca.0.load, ptr %lp.199, align 8
  store i64 %ul.57.fca.1.load, ptr %l.197.fca.1.gep, align 8
  store i64 %ul.57.fca.2.load, ptr %l.197.fca.2.gep, align 8
  store i64 %ul.57.fca.3.load, ptr %l.197.fca.3.gep, align 8
  store i64 %ul.57.fca.4.load, ptr %l.197.fca.4.gep, align 8
  %rt.200 = call ptr @__mn_list_get(ptr nonnull %lp.199, i64 %i.195)
  %p2i.204 = ptrtoint ptr %rt.187 to i64
  %p2i.205 = ptrtoint ptr %rt.200 to i64
  %i.206 = mul nsw i64 %p2i.205, %p2i.204
  %i.210 = add nsw i64 %i.206, %sum.a.161.0116
  %i.216 = add nuw nsw i64 %k.a.164.0117, 1
  %exitcond120.not = icmp eq i64 %i.216, 64
  br i1 %exitcond120.not, label %while_exit11, label %while_body10

while_exit11:                                     ; preds = %while_body10
  %i.225 = add nuw nsw i64 %j.a.78.0118, %i.178
  store ptr %ul.61.fca.0.load, ptr %lp.230, align 8
  store i64 %ul.61.fca.1.load, ptr %l.227.fca.1.gep, align 8
  store i64 %ul.61.fca.2.load, ptr %l.227.fca.2.gep, align 8
  store i64 %ul.61.fca.3.load, ptr %l.227.fca.3.gep, align 8
  store i64 %ul.61.fca.4.load, ptr %l.227.fca.4.gep, align 8
  %rt.231 = call ptr @__mn_list_get(ptr nonnull %lp.230, i64 %i.225)
  store i64 %i.210, ptr %rt.231, align 8
  %i.235 = add nuw nsw i64 %j.a.78.0118, 1
  %exitcond121.not = icmp eq i64 %i.235, 64
  br i1 %exitcond121.not, label %while_exit8, label %while_header9.preheader

drop.check.137:                                   ; preds = %while_exit5
  call void @__mn_str_free({ ptr, i64 } %rt.124)
  br label %drop.skip.137

drop.skip.137:                                    ; preds = %drop.check.137, %while_exit5
  %drop.null.140 = icmp eq ptr %rt.129.fca.0.extract5, null
  br i1 %drop.null.140, label %drop.skip.141, label %drop.check.141

drop.check.141:                                   ; preds = %drop.skip.137
  call void @__mn_str_free({ ptr, i64 } %rt.129)
  br label %drop.skip.141

drop.skip.141:                                    ; preds = %drop.check.141, %drop.skip.137
  %drop.lnull.144 = icmp eq ptr %ul.39.fca.0.load, null
  br i1 %drop.lnull.144, label %drop.lskip.145, label %drop.lcheck.145

drop.lcheck.145:                                  ; preds = %drop.skip.141
  call void @__mn_list_free(ptr nonnull %a.a.5)
  br label %drop.lskip.145

drop.lskip.145:                                   ; preds = %drop.lcheck.145, %drop.skip.141
  %drop.lnull.148 = icmp eq ptr %ul.57.fca.0.load, null
  br i1 %drop.lnull.148, label %drop.lskip.149, label %drop.lcheck.149

drop.lcheck.149:                                  ; preds = %drop.lskip.145
  call void @__mn_list_free(ptr nonnull %b.a.9)
  br label %drop.lskip.149

drop.lskip.149:                                   ; preds = %drop.lcheck.149, %drop.lskip.145
  %drop.lnull.152 = icmp eq ptr %ul.61.fca.0.load, null
  br i1 %drop.lnull.152, label %drop.lskip.153, label %drop.lcheck.153

drop.lcheck.153:                                  ; preds = %drop.lskip.149
  call void @__mn_list_free(ptr nonnull %c.a.13)
  br label %drop.lskip.153

drop.lskip.153:                                   ; preds = %drop.lcheck.153, %drop.lskip.149
  call void @__mn_intern_destroy() #1
  ret i64 0
}

; Function Attrs: nocallback nofree nounwind willreturn memory(argmem: write)
declare void @llvm.memset.p0.i64(ptr nocapture writeonly, i8, i64, i1 immarg) #2

attributes #0 = { mustprogress nounwind willreturn }
attributes #1 = { nounwind }
attributes #2 = { nocallback nofree nounwind willreturn memory(argmem: write) }

!mapanare.version = !{!0}

!0 = !{!"4.109.0"}
