culebra Triage: C:\Users\Juan\Documents\GitHub\Mapanare\docs\roadmap\v5\v5.6.9\culebra\stage2-baseline.ll — 5 root causes, 15748 total findings (977 critical, 14771 high, 0 medium)

  1. [critical] function-count-drop (940 hits)
     fix: Run 'culebra diff' between stage outputs and investigate any 'only in A' functions

  2. [critical] return-type-divergence (37 hits)
     fix: Fix the self-hosted emitter's declaration of this function to match

  3. [high] fixed-point-delta (7302 hits)
     fix: Use 'culebra fixedpoint' to identify which functions prevent convergence, then fix the underlying code-gen bugs

  4. [high] byte-count-mismatch (6362 hits)
     fix: Run 'culebra strings <file>' to find and fix byte count mismatches

  5. [high] stage-output-divergence (1107 hits)
     fix: Run 'culebra fixedpoint <compiler> <source>' to identify which functions diverge between stages

