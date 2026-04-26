culebra Triage: C:\Users\Juan\Documents\GitHub\Mapanare\stage2_v5.7.1.ll — 5 root causes, 15829 total findings (980 critical, 14849 high, 0 medium)

  1. [critical] function-count-drop (943 hits)
     fix: Run 'culebra diff' between stage outputs and investigate any 'only in A' functions

  2. [critical] return-type-divergence (37 hits)
     fix: Fix the self-hosted emitter's declaration of this function to match

  3. [high] fixed-point-delta (7341 hits)
     fix: Use 'culebra fixedpoint' to identify which functions prevent convergence, then fix the underlying code-gen bugs

  4. [high] byte-count-mismatch (6398 hits)
     fix: Run 'culebra strings <file>' to find and fix byte count mismatches

  5. [high] stage-output-divergence (1110 hits)
     fix: Run 'culebra fixedpoint <compiler> <source>' to identify which functions diverge between stages

