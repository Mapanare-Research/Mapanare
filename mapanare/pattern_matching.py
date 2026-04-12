"""Decision-tree pattern matching compilation (Maranget 2008).

Shared helper for both semantic checking (exhaustiveness) and MIR
lowering (code generation). See docs/roadmap/v4/v4.34.0/DESIGN.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from mapanare.ast_nodes import (
    ConstructorPattern,
    IdentPattern,
    LiteralPattern,
    OrPattern,
    Pattern,
    WildcardPattern,
)

# ---------------------------------------------------------------------------
# Constructor enumeration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConstructorInfo:
    """A single constructor for a type (e.g., ``Some`` with arity 1)."""

    tag: str
    arity: int


@dataclass
class TypeContext:
    """Type information for a pattern matrix column.

    Callers construct these from their own type resolution logic.
    """

    is_closed: bool
    all_constructors: list[ConstructorInfo] = field(default_factory=list)
    # For sub-column type resolution during specialization, the caller
    # provides a map: constructor_tag -> list of TypeContexts (one per arity slot).
    sub_contexts: dict[str, list[TypeContext]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pattern matrix
# ---------------------------------------------------------------------------


@dataclass
class PatternRow:
    """One row of the pattern matrix = one match arm."""

    patterns: list[Pattern]
    action_idx: int


@dataclass
class PatternMatrix:
    """Rows of patterns over columns of scrutinees."""

    rows: list[PatternRow]
    type_contexts: list[TypeContext]


# ---------------------------------------------------------------------------
# Decision tree nodes
# ---------------------------------------------------------------------------


@dataclass
class DTLeaf:
    """Match arm reached — execute the action."""

    action_idx: int


@dataclass
class DTFail:
    """No arm matches — non-exhaustive."""

    witness: Pattern


@dataclass
class DTSwitch:
    """Branch on a scrutinee column."""

    column_idx: int
    cases: list[tuple[str, DecisionTree]]
    default: DecisionTree | None


DecisionTree = DTLeaf | DTFail | DTSwitch


# ---------------------------------------------------------------------------
# Pattern classification helpers
# ---------------------------------------------------------------------------


def _is_wildcard(pat: Pattern, variant_names: set[str] | None = None) -> bool:
    """True if the pattern matches everything (wildcard or non-variant ident)."""
    if isinstance(pat, WildcardPattern):
        return True
    if isinstance(pat, IdentPattern):
        if variant_names is not None:
            return pat.name not in variant_names
        return True
    # OrPattern is never a wildcard (it should be expanded before reaching here)
    return False


def _get_constructor_tag(pat: Pattern, variant_names: set[str] | None = None) -> str | None:
    """Extract the constructor tag from a pattern, or None if wildcard."""
    if isinstance(pat, ConstructorPattern):
        return pat.name
    if isinstance(pat, IdentPattern):
        if variant_names is not None and pat.name in variant_names:
            return pat.name
    if isinstance(pat, LiteralPattern):
        return _literal_tag(pat)
    return None


def _literal_tag(pat: LiteralPattern) -> str:
    """Convert a literal pattern to its string tag for switch cases."""
    from mapanare.ast_nodes import BoolLiteral, FloatLiteral, IntLiteral, StringLiteral

    v = pat.value
    if isinstance(v, IntLiteral):
        return str(v.value)
    if isinstance(v, FloatLiteral):
        return str(v.value)
    if isinstance(v, BoolLiteral):
        return "true" if v.value else "false"
    if isinstance(v, StringLiteral):
        return v.value
    return str(v)


def _constructor_arity(pat: Pattern) -> int:
    """Get the number of sub-patterns for a constructor pattern."""
    if isinstance(pat, ConstructorPattern):
        return len(pat.args)
    return 0


def _all_variant_names(ctx: TypeContext) -> set[str]:
    """Get all variant names from a type context."""
    return {c.tag for c in ctx.all_constructors}


# ---------------------------------------------------------------------------
# Column operations (Maranget §3)
# ---------------------------------------------------------------------------


def specialize(matrix: PatternMatrix, col: int, tag: str, arity: int) -> PatternMatrix:
    """Specialize the matrix by constructor ``tag`` at column ``col``.

    Keep rows where column ``col`` has constructor ``tag`` or a wildcard.
    Replace column ``col`` with ``arity`` sub-patterns.
    """
    new_rows: list[PatternRow] = []
    variant_names = _all_variant_names(matrix.type_contexts[col]) if matrix.type_contexts else set()

    for row in matrix.rows:
        pat = row.patterns[col]

        if isinstance(pat, ConstructorPattern) and pat.name == tag:
            # Constructor matches: expand sub-patterns into new columns
            sub_pats = pat.args
            # Pad with wildcards if sub-patterns are fewer than arity
            while len(sub_pats) < arity:
                sub_pats = list(sub_pats) + [WildcardPattern()]
            new_patterns = row.patterns[:col] + sub_pats + row.patterns[col + 1 :]
            new_rows.append(PatternRow(patterns=new_patterns, action_idx=row.action_idx))

        elif isinstance(pat, IdentPattern) and pat.name in variant_names and pat.name == tag:
            # Variant-as-ident matching this tag (zero-arity constructor)
            new_patterns = row.patterns[:col] + row.patterns[col + 1 :]
            new_rows.append(PatternRow(patterns=new_patterns, action_idx=row.action_idx))

        elif isinstance(pat, LiteralPattern) and _literal_tag(pat) == tag:
            # Literal matching this tag (zero-arity)
            new_patterns = row.patterns[:col] + row.patterns[col + 1 :]
            new_rows.append(PatternRow(patterns=new_patterns, action_idx=row.action_idx))

        elif _is_wildcard(pat, variant_names):
            # Wildcard/variable: matches any constructor, expand to arity wildcards
            wild_pats = [WildcardPattern() for _ in range(arity)]
            new_patterns = row.patterns[:col] + wild_pats + row.patterns[col + 1 :]
            new_rows.append(PatternRow(patterns=new_patterns, action_idx=row.action_idx))

    # Build new type contexts: replace column col with sub-column contexts
    old_ctx = matrix.type_contexts[col] if col < len(matrix.type_contexts) else TypeContext(False)
    sub_ctxs = old_ctx.sub_contexts.get(tag, [])
    # Pad with open-type contexts if sub_contexts don't cover all arity slots
    while len(sub_ctxs) < arity:
        sub_ctxs = list(sub_ctxs) + [TypeContext(is_closed=False)]
    new_contexts = matrix.type_contexts[:col] + sub_ctxs + matrix.type_contexts[col + 1 :]

    return PatternMatrix(rows=new_rows, type_contexts=new_contexts)


def default_matrix(matrix: PatternMatrix, col: int) -> PatternMatrix:
    """Default matrix: keep only wildcard/variable rows, remove column ``col``."""
    new_rows: list[PatternRow] = []
    variant_names = _all_variant_names(matrix.type_contexts[col]) if matrix.type_contexts else set()

    for row in matrix.rows:
        pat = row.patterns[col]
        if _is_wildcard(pat, variant_names):
            new_patterns = row.patterns[:col] + row.patterns[col + 1 :]
            new_rows.append(PatternRow(patterns=new_patterns, action_idx=row.action_idx))

    new_contexts = matrix.type_contexts[:col] + matrix.type_contexts[col + 1 :]
    return PatternMatrix(rows=new_rows, type_contexts=new_contexts)


# ---------------------------------------------------------------------------
# Column selection heuristic (Maranget §5)
# ---------------------------------------------------------------------------


def select_column(matrix: PatternMatrix) -> int:
    """Pick the column with the most distinct constructors; leftmost tiebreak."""
    best_col = 0
    best_score = -1
    variant_sets: list[set[str]] = []

    for col_idx in range(len(matrix.type_contexts)):
        variant_names = _all_variant_names(matrix.type_contexts[col_idx])
        variant_sets.append(variant_names)
        seen: set[str] = set()
        for row in matrix.rows:
            if col_idx < len(row.patterns):
                tag = _get_constructor_tag(row.patterns[col_idx], variant_names)
                if tag is not None:
                    seen.add(tag)
        score = len(seen)
        if score > best_score:
            best_score = score
            best_col = col_idx

    return best_col


# ---------------------------------------------------------------------------
# Decision tree builder
# ---------------------------------------------------------------------------


def _is_all_wildcards(row: PatternRow, contexts: list[TypeContext]) -> bool:
    """True if every pattern in the row is a wildcard or non-variant ident."""
    for i, pat in enumerate(row.patterns):
        variant_names = _all_variant_names(contexts[i]) if i < len(contexts) else set()
        if not _is_wildcard(pat, variant_names):
            return False
    return True


def _collect_constructors(
    matrix: PatternMatrix, col: int
) -> list[ConstructorInfo]:
    """Collect all distinct constructor tags appearing in column ``col``."""
    seen: set[str] = set()
    result: list[ConstructorInfo] = []
    variant_names = _all_variant_names(matrix.type_contexts[col])

    for row in matrix.rows:
        if col >= len(row.patterns):
            continue
        pat = row.patterns[col]
        tag = _get_constructor_tag(pat, variant_names)
        if tag is not None and tag not in seen:
            seen.add(tag)
            arity = _constructor_arity(pat)
            result.append(ConstructorInfo(tag=tag, arity=arity))

    return result


def _sort_by_definition_order(
    ctors: list[ConstructorInfo], ctx: TypeContext
) -> list[ConstructorInfo]:
    """Sort constructors by enum definition order (for closed types) or
    by first-appearance order (for open types / literals)."""
    if ctx.is_closed and ctx.all_constructors:
        # Sort by position in the enum definition
        order = {c.tag: i for i, c in enumerate(ctx.all_constructors)}
        return sorted(ctors, key=lambda c: order.get(c.tag, len(order)))
    # For open types (literals), preserve first-appearance order (already in order)
    return ctors


def _expand_row(row: PatternRow) -> list[PatternRow]:
    """Expand a row: if any column has an OrPattern, split into multiple rows."""
    for col_idx, pat in enumerate(row.patterns):
        if isinstance(pat, OrPattern):
            result: list[PatternRow] = []
            for alt in pat.alternatives:
                new_patterns = row.patterns[:col_idx] + [alt] + row.patterns[col_idx + 1 :]
                new_row = PatternRow(patterns=new_patterns, action_idx=row.action_idx)
                result.extend(_expand_row(new_row))
            return result
    return [row]


def expand_or_patterns(matrix: PatternMatrix) -> PatternMatrix:
    """Expand OrPattern entries into multiple rows with the same action_idx."""
    new_rows: list[PatternRow] = []
    for row in matrix.rows:
        new_rows.extend(_expand_row(row))
    return PatternMatrix(rows=new_rows, type_contexts=matrix.type_contexts)


def build_decision_tree(matrix: PatternMatrix) -> DecisionTree:
    """Build a decision tree from a pattern matrix (Maranget 2008)."""
    # v4.35.0: expand or-patterns into multiple rows before the algorithm
    matrix = expand_or_patterns(matrix)

    # Base case 1: no rows — non-exhaustive
    if not matrix.rows:
        witness = _build_fail_witness(matrix)
        return DTFail(witness=witness)

    # Base case 2: first row is all wildcards — it matches
    if _is_all_wildcards(matrix.rows[0], matrix.type_contexts):
        return DTLeaf(action_idx=matrix.rows[0].action_idx)

    # Recursive case: choose a column and split
    col = select_column(matrix)
    ctx = matrix.type_contexts[col] if col < len(matrix.type_contexts) else TypeContext(False)

    # Collect constructors appearing in this column
    ctors_in_column = _collect_constructors(matrix, col)
    ctors_sorted = _sort_by_definition_order(ctors_in_column, ctx)

    # Build cases for each constructor
    cases: list[tuple[str, DecisionTree]] = []
    for ctor in ctors_sorted:
        specialized = specialize(matrix, col, ctor.tag, ctor.arity)
        subtree = build_decision_tree(specialized)
        cases.append((ctor.tag, subtree))

    # Build default branch if needed
    default: DecisionTree | None = None
    covered_tags = {c.tag for c in ctors_in_column}
    all_tags = {c.tag for c in ctx.all_constructors} if ctx.is_closed else set()

    if not ctx.is_closed or not covered_tags >= all_tags:
        defaulted = default_matrix(matrix, col)
        default = build_decision_tree(defaulted)

    return DTSwitch(column_idx=col, cases=cases, default=default)


def _build_fail_witness(matrix: PatternMatrix) -> Pattern:
    """Construct the simplest pattern that would match the empty matrix.

    Returns a wildcard. The calling DTSwitch wraps this in the constructor
    that led to the empty matrix.
    """
    return WildcardPattern()


def build_witness_for_switch(
    switch: DTSwitch, ctx: TypeContext
) -> Pattern | None:
    """Walk a DTSwitch to find a DTFail and reconstruct the missing pattern."""
    # Check each case's subtree for DTFail
    for tag, subtree in switch.cases:
        if isinstance(subtree, DTFail):
            ctor = _find_ctor_info(tag, ctx)
            if ctor and ctor.arity > 0:
                return ConstructorPattern(name=tag, args=[subtree.witness])
            return ConstructorPattern(name=tag, args=[])
        if isinstance(subtree, DTSwitch):
            inner = build_witness_for_switch(subtree, _sub_ctx(ctx, tag))
            if inner is not None:
                ctor = _find_ctor_info(tag, ctx)
                if ctor and ctor.arity > 0:
                    return ConstructorPattern(name=tag, args=[inner])
                return inner

    # Check default subtree
    if switch.default is not None:
        if isinstance(switch.default, DTFail):
            # The missing pattern is an uncovered constructor (for closed types)
            # or a wildcard (for open types)
            missing = _find_missing_constructor(switch, ctx)
            if missing:
                if missing.arity > 0:
                    return ConstructorPattern(
                        name=missing.tag,
                        args=[WildcardPattern() for _ in range(missing.arity)],
                    )
                return ConstructorPattern(name=missing.tag, args=[])
            return switch.default.witness
        if isinstance(switch.default, DTSwitch):
            return build_witness_for_switch(switch.default, TypeContext(is_closed=False))

    return None


def _find_ctor_info(tag: str, ctx: TypeContext) -> ConstructorInfo | None:
    """Find a ConstructorInfo by tag in a TypeContext."""
    for c in ctx.all_constructors:
        if c.tag == tag:
            return c
    return None


def _sub_ctx(ctx: TypeContext, tag: str) -> TypeContext:
    """Get the sub-context for a constructor's first sub-column."""
    subs = ctx.sub_contexts.get(tag, [])
    return subs[0] if subs else TypeContext(is_closed=False)


def _find_missing_constructor(switch: DTSwitch, ctx: TypeContext) -> ConstructorInfo | None:
    """Find the first constructor in the type that is not covered by the switch."""
    covered = {tag for tag, _ in switch.cases}
    for c in ctx.all_constructors:
        if c.tag not in covered:
            return c
    return None


# ---------------------------------------------------------------------------
# Post-construction analysis
# ---------------------------------------------------------------------------


def find_unreachable_arms(tree: DecisionTree, num_arms: int) -> set[int]:
    """Return the set of arm indices that are never reached."""
    reached: set[int] = set()
    _collect_reached(tree, reached)
    return set(range(num_arms)) - reached


def _collect_reached(tree: DecisionTree, reached: set[int]) -> None:
    """Collect all action_idx values that appear in DTLeaf nodes."""
    if isinstance(tree, DTLeaf):
        reached.add(tree.action_idx)
    elif isinstance(tree, DTSwitch):
        for _, subtree in tree.cases:
            _collect_reached(subtree, reached)
        if tree.default is not None:
            _collect_reached(tree.default, reached)


def collect_fail_witnesses(tree: DecisionTree) -> list[Pattern]:
    """Collect all DTFail witness patterns from a decision tree."""
    witnesses: list[Pattern] = []
    _collect_fails(tree, witnesses)
    return witnesses


def _collect_fails(tree: DecisionTree, witnesses: list[Pattern]) -> None:
    """Recursively collect DTFail witnesses."""
    if isinstance(tree, DTFail):
        witnesses.append(tree.witness)
    elif isinstance(tree, DTSwitch):
        for _, subtree in tree.cases:
            _collect_fails(subtree, witnesses)
        if tree.default is not None:
            _collect_fails(tree.default, witnesses)


def has_any_fail(tree: DecisionTree) -> bool:
    """Check if the decision tree contains any DTFail nodes."""
    if isinstance(tree, DTFail):
        return True
    if isinstance(tree, DTSwitch):
        for _, subtree in tree.cases:
            if has_any_fail(subtree):
                return True
        if tree.default is not None:
            return has_any_fail(tree.default)
    return False


# ---------------------------------------------------------------------------
# Witness display
# ---------------------------------------------------------------------------


def display_witness(pat: Pattern) -> str:
    """Render a witness pattern for diagnostic messages."""
    if isinstance(pat, WildcardPattern):
        return "_"
    if isinstance(pat, ConstructorPattern):
        if not pat.args:
            return pat.name
        args = ", ".join(display_witness(a) for a in pat.args)
        return f"{pat.name}({args})"
    if isinstance(pat, IdentPattern):
        return pat.name
    if isinstance(pat, LiteralPattern):
        return _literal_tag(pat)
    if isinstance(pat, OrPattern):
        return " | ".join(display_witness(a) for a in pat.alternatives)
    return "_"
