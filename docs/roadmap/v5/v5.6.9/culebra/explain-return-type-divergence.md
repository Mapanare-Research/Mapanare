culebra [return-type-divergence] Function return type diverges between stages

  Description:
    A runtime function is declared with a different return type in
    stage2 than in stage1. This is the most dangerous ABI mismatch:
    the caller reads a register (or memory) that the callee never
    wrote, getting garbage. In Mapanare v2.2.0, __mn_range was
    declared as returning {i64, i64} in stage2 but ptr in stage1.
    The C runtime returns void*, so stage2's extractvalue read
    garbage from rdx, causing for_start >= for_end and TOKS=0.

  Impact:
    Every call site silently receives garbage. Control flow that
    depends on the return value (loop bounds, conditionals) takes
    wrong paths. The binary runs without crashing but produces
    zero output — the hardest category of bug to diagnose.

  Findings (37 matches):

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 12 in (global)
          10 | @.fmt_float_nl = private constant [5 x i8] c"%lf\0A\00", align 2
          11 | 
    >>    12 | declare {ptr, i64} @__mn_str_concat({ptr, i64}, {ptr, i64}) nounwind willreturn
          13 | declare i64 @__mn_str_eq({ptr, i64}, {ptr, i64}) nounwind readonly willreturn
          14 | declare i64 @__mn_str_cmp({ptr, i64}, {ptr, i64}) nounwind readonly willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 16 in (global)
          14 | declare i64 @__mn_str_cmp({ptr, i64}, {ptr, i64}) nounwind readonly willreturn
          15 | declare i64 @__mn_str_len({ptr, i64}) nounwind readonly willreturn
    >>    16 | declare {ptr, i64} @__mn_str_char_at({ptr, i64}, i64)
          17 | declare i64 @__mn_str_byte_at({ptr, i64}, i64) nounwind readonly willreturn
          18 | declare {ptr, i64} @__mn_str_substr({ptr, i64}, i64, i64) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 18 in (global)
          16 | declare {ptr, i64} @__mn_str_char_at({ptr, i64}, i64)
          17 | declare i64 @__mn_str_byte_at({ptr, i64}, i64) nounwind readonly willreturn
    >>    18 | declare {ptr, i64} @__mn_str_substr({ptr, i64}, i64, i64) nounwind willreturn
          19 | declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
          20 | declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 19 in (global)
          17 | declare i64 @__mn_str_byte_at({ptr, i64}, i64) nounwind readonly willreturn
          18 | declare {ptr, i64} @__mn_str_substr({ptr, i64}, i64, i64) nounwind willreturn
    >>    19 | declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
          20 | declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
          21 | declare {ptr, i64} @__mn_str_from_float(double) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 20 in (global)
          18 | declare {ptr, i64} @__mn_str_substr({ptr, i64}, i64, i64) nounwind willreturn
          19 | declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
    >>    20 | declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
          21 | declare {ptr, i64} @__mn_str_from_float(double) nounwind willreturn
          22 | declare i64 @__mn_str_to_int({ptr, i64}) nounwind readonly willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 21 in (global)
          19 | declare {ptr, i64} @__mn_str_from_int(i64) nounwind willreturn
          20 | declare {ptr, i64} @__mn_str_from_bool(i64) nounwind willreturn
    >>    21 | declare {ptr, i64} @__mn_str_from_float(double) nounwind willreturn
          22 | declare i64 @__mn_str_to_int({ptr, i64}) nounwind readonly willreturn
          23 | declare double @__mn_str_to_float({ptr, i64}) nounwind readonly willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 29 in (global)
          27 | declare i1 @__mn_str_ends_with({ptr, i64}, {ptr, i64}) nounwind readonly willreturn
          28 | declare i64 @__mn_str_find({ptr, i64}, {ptr, i64}) nounwind readonly willreturn
    >>    29 | declare {ptr, i64} @__mn_str_join({ptr, i64}, ptr) nounwind willreturn
          30 | declare void @__mn_str_free({ptr, i64}) nounwind willreturn
          31 | declare void @__mn_list_free(ptr) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 33 in (global)
          31 | declare void @__mn_list_free(ptr) nounwind willreturn
          32 | declare void @free(ptr) nounwind willreturn
    >>    33 | declare {ptr, i64, i64, i64, i64} @__mn_list_new(i64) nounwind willreturn
          34 | declare void @__mn_list_push(ptr, ptr) nounwind
          35 | declare ptr @__mn_list_get(ptr, i64) nounwind readonly willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 38 in (global)
          36 | declare i64 @__mn_list_len(ptr) nounwind readonly willreturn
          37 | declare void @__mn_list_set(ptr, i64, ptr) nounwind
    >>    38 | declare {ptr, i64, i64, i64, i64} @__mn_list_concat(ptr, ptr) nounwind willreturn
          39 | declare i1 @__iter_has_next({i64, i64}) nounwind readonly willreturn
          40 | declare i64 @__iter_next({i64, i64}) nounwind

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 41 in (global)
          39 | declare i1 @__iter_has_next({i64, i64}) nounwind readonly willreturn
          40 | declare i64 @__iter_next({i64, i64}) nounwind
    >>    41 | declare {i64, i64} @__mn_range(i64, i64) nounwind readonly willreturn
          42 | declare void @__mn_range_free(ptr) nounwind willreturn
          43 | declare {ptr, i64} @__mn_str_to_upper({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 43 in (global)
          41 | declare {i64, i64} @__mn_range(i64, i64) nounwind readonly willreturn
          42 | declare void @__mn_range_free(ptr) nounwind willreturn
    >>    43 | declare {ptr, i64} @__mn_str_to_upper({ptr, i64}) nounwind willreturn
          44 | declare {ptr, i64} @__mn_str_to_lower({ptr, i64}) nounwind willreturn
          45 | declare {ptr, i64} @__mn_str_replace({ptr, i64}, {ptr, i64}, {ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 44 in (global)
          42 | declare void @__mn_range_free(ptr) nounwind willreturn
          43 | declare {ptr, i64} @__mn_str_to_upper({ptr, i64}) nounwind willreturn
    >>    44 | declare {ptr, i64} @__mn_str_to_lower({ptr, i64}) nounwind willreturn
          45 | declare {ptr, i64} @__mn_str_replace({ptr, i64}, {ptr, i64}, {ptr, i64}) nounwind willreturn
          46 | declare {ptr, i64, i64, i64, i64} @__mn_str_split({ptr, i64}, {ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 45 in (global)
          43 | declare {ptr, i64} @__mn_str_to_upper({ptr, i64}) nounwind willreturn
          44 | declare {ptr, i64} @__mn_str_to_lower({ptr, i64}) nounwind willreturn
    >>    45 | declare {ptr, i64} @__mn_str_replace({ptr, i64}, {ptr, i64}, {ptr, i64}) nounwind willreturn
          46 | declare {ptr, i64, i64, i64, i64} @__mn_str_split({ptr, i64}, {ptr, i64}) nounwind willreturn
          47 | declare {ptr, i64} @__mn_str_trim({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 46 in (global)
          44 | declare {ptr, i64} @__mn_str_to_lower({ptr, i64}) nounwind willreturn
          45 | declare {ptr, i64} @__mn_str_replace({ptr, i64}, {ptr, i64}, {ptr, i64}) nounwind willreturn
    >>    46 | declare {ptr, i64, i64, i64, i64} @__mn_str_split({ptr, i64}, {ptr, i64}) nounwind willreturn
          47 | declare {ptr, i64} @__mn_str_trim({ptr, i64}) nounwind willreturn
          48 | declare i1 @__mn_str_contains({ptr, i64}, {ptr, i64}) nounwind readonly willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 47 in (global)
          45 | declare {ptr, i64} @__mn_str_replace({ptr, i64}, {ptr, i64}, {ptr, i64}) nounwind willreturn
          46 | declare {ptr, i64, i64, i64, i64} @__mn_str_split({ptr, i64}, {ptr, i64}) nounwind willreturn
    >>    47 | declare {ptr, i64} @__mn_str_trim({ptr, i64}) nounwind willreturn
          48 | declare i1 @__mn_str_contains({ptr, i64}, {ptr, i64}) nounwind readonly willreturn
          49 | declare void @abort() noreturn nounwind

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 53 in (global)
          51 | declare void @__mn_exit(i64)
          52 | declare i64 @__mn_argc()
    >>    53 | declare {ptr, i64} @__mn_argv(i64)
          54 | declare {ptr, i64} @__mn_file_read_or_empty({ptr, i64})
          55 | declare i64 @__mn_file_write({ptr, i64}, {ptr, i64})

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 54 in (global)
          52 | declare i64 @__mn_argc()
          53 | declare {ptr, i64} @__mn_argv(i64)
    >>    54 | declare {ptr, i64} @__mn_file_read_or_empty({ptr, i64})
          55 | declare i64 @__mn_file_write({ptr, i64}, {ptr, i64})
          56 | declare i64 @__mn_system({ptr, i64})

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 59 in (global)
          57 | declare void @__mn_str_eprint({ptr, i64}) nounwind willreturn
          58 | declare void @__mn_str_eprintln({ptr, i64}) nounwind willreturn
    >>    59 | declare {ptr, i64} @__mn_str_chr(i64) nounwind willreturn
          60 | declare i64 @__mn_str_ord({ptr, i64}) nounwind readonly willreturn
          61 | declare noalias ptr @__mn_map_new(i64, i64, i64, i64) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 66 in (global)
          64 | declare i64 @__mn_map_len(ptr) nounwind readonly willreturn
          65 | declare i64 @__mn_map_contains(ptr, ptr) nounwind readonly willreturn
    >>    66 | declare {ptr, i64, i64, i64, i64} @__mn_map_keys(ptr) nounwind willreturn
          67 | declare noalias ptr @malloc(i64) nounwind willreturn
          68 | declare i32 @printf(ptr, ...)

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 130 in (global)
         128 | declare ptr @__mn_signal_get(ptr) nounwind
         129 | declare void @__mn_signal_set(ptr, ptr) nounwind willreturn
    >>   130 | declare {ptr, i64} @__mn_read_line() nounwind willreturn
         131 | declare i64 @__mn_file_append({ptr, i64}, {ptr, i64}) nounwind willreturn
         132 | declare i64 @__mn_file_exists({ptr, i64}) nounwind readonly willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 133 in (global)
         131 | declare i64 @__mn_file_append({ptr, i64}, {ptr, i64}) nounwind willreturn
         132 | declare i64 @__mn_file_exists({ptr, i64}) nounwind readonly willreturn
    >>   133 | declare {ptr, i64, i64, i64, i64} @__mn_dir_list_strings({ptr, i64}) nounwind willreturn
         134 | declare {ptr, i64} @__mn_http_get({ptr, i64}) nounwind willreturn
         135 | declare {ptr, i64} @__mn_sha256_str({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 134 in (global)
         132 | declare i64 @__mn_file_exists({ptr, i64}) nounwind readonly willreturn
         133 | declare {ptr, i64, i64, i64, i64} @__mn_dir_list_strings({ptr, i64}) nounwind willreturn
    >>   134 | declare {ptr, i64} @__mn_http_get({ptr, i64}) nounwind willreturn
         135 | declare {ptr, i64} @__mn_sha256_str({ptr, i64}) nounwind willreturn
         136 | declare {ptr, i64} @__mn_base64_encode_str({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 135 in (global)
         133 | declare {ptr, i64, i64, i64, i64} @__mn_dir_list_strings({ptr, i64}) nounwind willreturn
         134 | declare {ptr, i64} @__mn_http_get({ptr, i64}) nounwind willreturn
    >>   135 | declare {ptr, i64} @__mn_sha256_str({ptr, i64}) nounwind willreturn
         136 | declare {ptr, i64} @__mn_base64_encode_str({ptr, i64}) nounwind willreturn
         137 | declare {ptr, i64} @__mn_base64_decode_str({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 136 in (global)
         134 | declare {ptr, i64} @__mn_http_get({ptr, i64}) nounwind willreturn
         135 | declare {ptr, i64} @__mn_sha256_str({ptr, i64}) nounwind willreturn
    >>   136 | declare {ptr, i64} @__mn_base64_encode_str({ptr, i64}) nounwind willreturn
         137 | declare {ptr, i64} @__mn_base64_decode_str({ptr, i64}) nounwind willreturn
         138 | declare {ptr, i64} @__mn_hmac_sha256_str({ptr, i64}, {ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 137 in (global)
         135 | declare {ptr, i64} @__mn_sha256_str({ptr, i64}) nounwind willreturn
         136 | declare {ptr, i64} @__mn_base64_encode_str({ptr, i64}) nounwind willreturn
    >>   137 | declare {ptr, i64} @__mn_base64_decode_str({ptr, i64}) nounwind willreturn
         138 | declare {ptr, i64} @__mn_hmac_sha256_str({ptr, i64}, {ptr, i64}) nounwind willreturn
         139 | declare {ptr, i64} @__mn_hex_encode_str({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 138 in (global)
         136 | declare {ptr, i64} @__mn_base64_encode_str({ptr, i64}) nounwind willreturn
         137 | declare {ptr, i64} @__mn_base64_decode_str({ptr, i64}) nounwind willreturn
    >>   138 | declare {ptr, i64} @__mn_hmac_sha256_str({ptr, i64}, {ptr, i64}) nounwind willreturn
         139 | declare {ptr, i64} @__mn_hex_encode_str({ptr, i64}) nounwind willreturn
         140 | declare {ptr, i64} @__mn_random_bytes_str(i64) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 139 in (global)
         137 | declare {ptr, i64} @__mn_base64_decode_str({ptr, i64}) nounwind willreturn
         138 | declare {ptr, i64} @__mn_hmac_sha256_str({ptr, i64}, {ptr, i64}) nounwind willreturn
    >>   139 | declare {ptr, i64} @__mn_hex_encode_str({ptr, i64}) nounwind willreturn
         140 | declare {ptr, i64} @__mn_random_bytes_str(i64) nounwind willreturn
         141 | declare i64 @__mn_regex_compile_str({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 140 in (global)
         138 | declare {ptr, i64} @__mn_hmac_sha256_str({ptr, i64}, {ptr, i64}) nounwind willreturn
         139 | declare {ptr, i64} @__mn_hex_encode_str({ptr, i64}) nounwind willreturn
    >>   140 | declare {ptr, i64} @__mn_random_bytes_str(i64) nounwind willreturn
         141 | declare i64 @__mn_regex_compile_str({ptr, i64}) nounwind willreturn
         142 | declare i64 @__mn_regex_exec_str(i64, {ptr, i64}, i64) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 143 in (global)
         141 | declare i64 @__mn_regex_compile_str({ptr, i64}) nounwind willreturn
         142 | declare i64 @__mn_regex_exec_str(i64, {ptr, i64}, i64) nounwind willreturn
    >>   143 | declare {ptr, i64} @__mn_regex_replace_str(i64, {ptr, i64}, {ptr, i64}, i64) nounwind willreturn
         144 | declare i64 @__mn_regex_free(i64) nounwind willreturn
         145 | declare i64 @__mn_file_remove({ptr, i64}) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 152 in (global)
         150 | declare i64 @__mn_file_rename({ptr, i64}, {ptr, i64}) nounwind willreturn
         151 | declare i64 @__mn_file_copy({ptr, i64}, {ptr, i64}) nounwind willreturn
    >>   152 | declare {ptr, i64} @__mn_realpath({ptr, i64}) nounwind willreturn
         153 | declare {ptr, i64} @__mn_tmpfile_path() nounwind willreturn
         154 | declare i64 @__mn_gpu_available() nounwind readonly willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 153 in (global)
         151 | declare i64 @__mn_file_copy({ptr, i64}, {ptr, i64}) nounwind willreturn
         152 | declare {ptr, i64} @__mn_realpath({ptr, i64}) nounwind willreturn
    >>   153 | declare {ptr, i64} @__mn_tmpfile_path() nounwind willreturn
         154 | declare i64 @__mn_gpu_available() nounwind readonly willreturn
         155 | declare {ptr, i64} @__mn_gpu_device_name() nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 155 in (global)
         153 | declare {ptr, i64} @__mn_tmpfile_path() nounwind willreturn
         154 | declare i64 @__mn_gpu_available() nounwind readonly willreturn
    >>   155 | declare {ptr, i64} @__mn_gpu_device_name() nounwind willreturn
         156 | declare i64 @__mn_gpu_device_memory() nounwind readonly willreturn
         157 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr, ptr) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 157 in (global)
         155 | declare {ptr, i64} @__mn_gpu_device_name() nounwind willreturn
         156 | declare i64 @__mn_gpu_device_memory() nounwind readonly willreturn
    >>   157 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr, ptr) nounwind willreturn
         158 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_sub(ptr, ptr) nounwind willreturn
         159 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_mul(ptr, ptr) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 158 in (global)
         156 | declare i64 @__mn_gpu_device_memory() nounwind readonly willreturn
         157 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr, ptr) nounwind willreturn
    >>   158 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_sub(ptr, ptr) nounwind willreturn
         159 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_mul(ptr, ptr) nounwind willreturn
         160 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_div(ptr, ptr) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 159 in (global)
         157 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_add(ptr, ptr) nounwind willreturn
         158 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_sub(ptr, ptr) nounwind willreturn
    >>   159 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_mul(ptr, ptr) nounwind willreturn
         160 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_div(ptr, ptr) nounwind willreturn
         161 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_matmul(ptr, ptr, i64, i64, i64) nounwind willreturn

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 160 in (global)
         158 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_sub(ptr, ptr) nounwind willreturn
         159 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_mul(ptr, ptr) nounwind willreturn
    >>   160 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_div(ptr, ptr) nounwind willreturn
         161 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_matmul(ptr, ptr, i64, i64, i64) nounwind willreturn
         162 | declare void @__mn_coro_scheduler_init(i32)

  [critical] C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll line 161 in (global)
         159 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_mul(ptr, ptr) nounwind willreturn
         160 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_div(ptr, ptr) nounwind willreturn
    >>   161 | declare {ptr, i64, i64, i64, i64} @__mn_gpu_tensor_matmul(ptr, ptr, i64, i64, i64) nounwind willreturn
         162 | declare void @__mn_coro_scheduler_init(i32)
         163 | declare void @__mn_coro_scheduler_destroy()

  Remediation:
    Fix the self-hosted emitter's declaration of this function to match
    the C runtime's actual signature. For __mn_range: the C runtime
    returns void* (an iterator pointer), not {i64, i64}.

    tip: Run with --autofix to apply automatically
