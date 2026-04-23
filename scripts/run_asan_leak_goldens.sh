#!/usr/bin/env bash
# v5.4.2: compile + link + execute every golden under LSan
# (detect_leaks=1:leak_check_at_exit=1) to verify the COMPILED
# output is leak-clean. Orthogonal to scripts/run_asan_goldens.sh
# which checks the compiler (mnc-stage1-asan) itself for
# UAF/overflow during compilation.
#
# Pipeline per golden:
#   mnc-stage1 <t.mn>                            -> t.ll
#   llc -filetype=obj -relocation-model=pic t.ll -> t.o
#   clang -fsanitize=address -fPIE t.o libmapanare_rt.a -> t.exe
#   ASAN_OPTIONS=detect_leaks=1 ./t.exe          -> classify
#
# Classes:
#   CLEAN         — exit 0 + 0 LSan findings
#   LEAK          — LSan reported leaks not covered by suppressions
#   COMPILE_FAIL  — mnc-stage1 nonzero exit (expected for 12 goldens
#                   still unsupported by the self-hosted compiler)
#   LINK_FAIL     — llc or clang failed
#   RUN_FAIL      — exe exited non-zero for a non-leak reason
#                   (crash, assert)
#
# Env overrides:
#   MAPANARE_ROOT   — repo root (defaults to $(pwd))
#   ASAN_LEAK_OUTDIR — output dir (defaults to /tmp/asan-leak)
#   SUPPRESSIONS    — LSan suppression file
set -u

ROOT=${MAPANARE_ROOT:-$(pwd)}
STAGE1=$ROOT/mapanare/self/mnc-stage1
RT=$ROOT/runtime/native/libmapanare_rt.a
OUTDIR=${ASAN_LEAK_OUTDIR:-/tmp/asan-leak}
SUPPRESSIONS=${SUPPRESSIONS:-$ROOT/scripts/asan_leak_suppressions.txt}
TSV=$OUTDIR/asan-leak-summary.tsv

if [ ! -x "$STAGE1" ]; then
  echo "ERROR: $STAGE1 not found or not executable" >&2
  exit 2
fi
if [ ! -f "$RT" ]; then
  echo "ERROR: $RT not found (run make build-rt)" >&2
  exit 2
fi
if [ ! -f "$SUPPRESSIONS" ]; then
  echo "ERROR: $SUPPRESSIONS not found" >&2
  exit 2
fi

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

# Compiled-binary-under-LSan options. detect_leaks=1 is the whole
# point of this sweep. halt_on_error=0 so a UAF in one golden
# doesn't abort before LSan's exit-time leak check runs.
ASAN_RUN="detect_leaks=1:leak_check_at_exit=1:halt_on_error=0:symbolize=1:suppressions=$SUPPRESSIONS"

echo -e "test\tcompile_rc\trun_rc\tleak_count\tleak_bytes\tfirst_frame\tclass" > "$TSV"

count_total=0 count_clean=0 count_leak=0 count_compfail=0 count_linkfail=0 count_runfail=0

for mn in "$ROOT"/tests/golden/*.mn; do
  t=$(basename "$mn" .mn)
  count_total=$((count_total+1))

  LL=$OUTDIR/${t}.ll
  OBJ=$OUTDIR/${t}.o
  EXE=$OUTDIR/${t}.exe
  CERR=$OUTDIR/${t}.compile.err
  LERR=$OUTDIR/${t}.link.err
  RERR=$OUTDIR/${t}.run.err
  ROUT=$OUTDIR/${t}.run.out

  # Step 1: compile .mn -> .ll (plain stage1, not asan — we don't
  # care about the compiler's own leaks in this sweep)
  timeout 60 "$STAGE1" "$mn" > "$LL" 2> "$CERR"
  crc=$?
  if [ $crc -ne 0 ] || [ ! -s "$LL" ]; then
    echo -e "$t\t$crc\t-\t-\t-\t-\tCOMPILE_FAIL" >> "$TSV"
    count_compfail=$((count_compfail+1))
    continue
  fi

  # Step 2: llc -> .o
  if ! llc -filetype=obj -relocation-model=pic "$LL" -o "$OBJ" 2> "$LERR"; then
    echo -e "$t\t$crc\t-\t-\t-\tllc\tLINK_FAIL" >> "$TSV"
    count_linkfail=$((count_linkfail+1))
    continue
  fi

  # Step 3: link with ASan + runtime
  if ! clang -fsanitize=address -fPIE "$OBJ" "$RT" \
      -lm -lpthread -ldl -o "$EXE" 2>> "$LERR"; then
    echo -e "$t\t$crc\t-\t-\t-\tclang\tLINK_FAIL" >> "$TSV"
    count_linkfail=$((count_linkfail+1))
    continue
  fi

  # Step 4: run under LSan (empty stdin, 30 s budget)
  ASAN_OPTIONS="$ASAN_RUN" timeout 30 "$EXE" < /dev/null > "$ROUT" 2> "$RERR"
  rrc=$?

  # Parse LSan findings from stderr.
  # Summary line: "SUMMARY: AddressSanitizer: 19 byte(s) leaked in 6 allocation(s)."
  leak_bytes=$(grep -oE 'SUMMARY: AddressSanitizer: [0-9]+ byte' "$RERR" 2>/dev/null \
               | head -1 | awk '{print $3}')
  leak_count=$(grep -oE 'in [0-9]+ allocation' "$RERR" 2>/dev/null \
               | head -1 | awk '{print $2}')
  : ${leak_bytes:=0}
  : ${leak_count:=0}
  # First allocating frame from LSan trace — the first "#1 0x.. in <sym>"
  # that isn't calloc/malloc itself.
  first_frame=$(grep -m1 -oE '#1 0x[0-9a-f]+ in [a-zA-Z_][a-zA-Z_0-9]*' "$RERR" 2>/dev/null \
                | awk '{print $NF}')
  : ${first_frame:=-}

  if [ "$leak_bytes" != "0" ] && [ "$leak_bytes" -gt 0 ] 2>/dev/null; then
    cls=LEAK
    count_leak=$((count_leak+1))
  elif [ $rrc -ne 0 ]; then
    cls=RUN_FAIL
    count_runfail=$((count_runfail+1))
  else
    cls=CLEAN
    count_clean=$((count_clean+1))
  fi

  echo -e "$t\t$crc\t$rrc\t$leak_count\t$leak_bytes\t$first_frame\t$cls" >> "$TSV"
done

echo
echo "=== ASan leak-detection golden summary ==="
echo "Total: $count_total"
echo "  CLEAN:        $count_clean"
echo "  LEAK:         $count_leak"
echo "  COMPILE_FAIL: $count_compfail"
echo "  LINK_FAIL:    $count_linkfail"
echo "  RUN_FAIL:     $count_runfail"
echo "TSV:  $TSV"
