"""Python-to-Mapanare transpiler.

Translates Python source code into Mapanare (.mn) source text, which can then
be fed through the standard Mapanare compilation pipeline.

Usage::

    from mapanare.from_python import translate_to_mn

    mn_source = translate_to_mn(python_source, "example.py")
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Type mapping
# ---------------------------------------------------------------------------

_PY_TYPE_MAP: dict[str, str] = {
    "int": "Int",
    "float": "Float",
    "str": "String",
    "bool": "Bool",
    "list": "List",
    "dict": "Map",
    "None": "Void",
    "NoneType": "Void",
}

# Python operator → Mapanare operator
_BINOP_MAP: dict[type[ast.operator], str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Mod: "%",
    ast.FloorDiv: "/",  # truncating div (matches // for pos; neg differs: Py floors, Mn truncs)
    ast.Pow: "**",
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.LShift: "<<",
    ast.RShift: ">>",
}

_CMPOP_MAP: dict[type[ast.cmpop], str] = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
}

_UNARYOP_MAP: dict[type[ast.unaryop], str] = {
    ast.USub: "-",
    ast.UAdd: "+",
    ast.Not: "!",
    ast.Invert: "~",
}

_BOOLOP_MAP: dict[type[ast.boolop], str] = {
    ast.And: "&&",
    ast.Or: "||",
}


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class TranslateError(Exception):
    """Raised when a Python construct cannot be translated to Mapanare."""

    def __init__(self, message: str, lineno: int = 0, filename: str = "<unknown>"):
        self.message = message
        self.lineno = lineno
        self.filename = filename
        super().__init__(f"{filename}:{lineno}: {message}")


# ---------------------------------------------------------------------------
# Helper: indentation
# ---------------------------------------------------------------------------


@dataclass
class _Indent:
    """Tracks current indentation level for output formatting."""

    level: int = 0
    _tab: str = "    "

    def push(self) -> None:
        self.level += 1

    def pop(self) -> None:
        self.level = max(0, self.level - 1)

    def prefix(self) -> str:
        return self._tab * self.level


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------


@dataclass
class PythonTranslator:
    """Translates a Python AST into Mapanare source text.

    The translator walks top-level definitions (functions, classes, global
    assignments) and emits valid ``.mn`` source that can be parsed by the
    standard Mapanare parser.
    """

    filename: str = "<unknown>"
    _indent: _Indent = field(default_factory=_Indent)
    _lines: list[str] = field(default_factory=list)
    # Track classes being translated (for self-reference resolution)
    _current_class: str | None = None
    # Track variables that have been assigned (for let vs reassignment)
    _declared_vars: list[set[str]] = field(default_factory=lambda: [set()])

    # -- Scope helpers --

    def _push_scope(self) -> None:
        self._declared_vars.append(set())

    def _pop_scope(self) -> None:
        if len(self._declared_vars) > 1:
            self._declared_vars.pop()

    def _is_declared(self, name: str) -> bool:
        for scope in reversed(self._declared_vars):
            if name in scope:
                return True
        return False

    def _declare(self, name: str) -> None:
        self._declared_vars[-1].add(name)

    # -- Output helpers --

    def _emit(self, text: str) -> None:
        self._lines.append(self._indent.prefix() + text)

    def _emit_raw(self, text: str) -> None:
        self._lines.append(text)

    # -- Type translation --

    def _translate_type(self, node: ast.expr | None) -> str:
        """Translate a Python type annotation to a Mapanare type string."""
        if node is None:
            return "any"

        if isinstance(node, ast.Constant):
            if node.value is None:
                return "Void"
            return "any"

        if isinstance(node, ast.Name):
            return _PY_TYPE_MAP.get(node.id, node.id)

        if isinstance(node, ast.Attribute):
            # e.g. typing.List — just use the attribute name
            return _PY_TYPE_MAP.get(node.attr, node.attr)

        if isinstance(node, ast.Subscript):
            # e.g. list[int], dict[str, int], Optional[int]
            base = self._translate_type(node.value)
            slice_node = node.slice

            if base == "Optional" or base == "Option":
                inner = self._translate_type(slice_node)
                return f"Option<{inner}>"

            if base == "Result":
                if isinstance(slice_node, ast.Tuple):
                    parts = [self._translate_type(e) for e in slice_node.elts]
                    return f"Result<{', '.join(parts)}>"
                inner = self._translate_type(slice_node)
                return f"Result<{inner}, String>"

            if isinstance(slice_node, ast.Tuple):
                parts = [self._translate_type(e) for e in slice_node.elts]
                return f"{base}<{', '.join(parts)}>"

            inner = self._translate_type(slice_node)
            return f"{base}<{inner}>"

        return "any"

    def _infer_type_from_value(self, node: ast.expr) -> str:
        """Infer a Mapanare type from a Python value expression."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "Bool"
            if isinstance(node.value, int):
                return "Int"
            if isinstance(node.value, float):
                return "Float"
            if isinstance(node.value, str):
                return "String"
            if node.value is None:
                return "Option<any>"
        if isinstance(node, ast.List):
            if node.elts:
                inner = self._infer_type_from_value(node.elts[0])
                return f"List<{inner}>"
            return "List<any>"
        if isinstance(node, ast.Dict):
            if node.keys and node.keys[0] is not None:
                kt = self._infer_type_from_value(node.keys[0])
                vt = self._infer_type_from_value(node.values[0])
                return f"Map<{kt}, {vt}>"
            return "Map<any, any>"
        if isinstance(node, ast.JoinedStr):
            return "String"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name in _PY_TYPE_MAP:
                    return _PY_TYPE_MAP[name]
                # Constructor call — assume it returns the class type
                return name
        if isinstance(node, ast.BoolOp):
            return "Bool"
        if isinstance(node, ast.Compare):
            return "Bool"
        return "any"

    # -- Expression translation --

    def _translate_expr(self, node: ast.expr) -> str:
        """Translate a Python expression to a Mapanare expression string."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "true" if node.value else "false"
            if isinstance(node.value, int):
                return str(node.value)
            if isinstance(node.value, float):
                return str(node.value)
            if isinstance(node.value, str):
                escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'
            if node.value is None:
                return "None"
            return repr(node.value)

        if isinstance(node, ast.Name):
            name = node.id
            if name == "True":
                return "true"
            if name == "False":
                return "false"
            if name == "None":
                return "None"
            if name == "self" and self._current_class:
                return "self"
            return name

        if isinstance(node, ast.BinOp):
            left = self._translate_expr(node.left)
            right = self._translate_expr(node.right)
            op = _BINOP_MAP.get(type(node.op))
            if op is None:
                raise TranslateError(
                    f"unsupported binary operator: {type(node.op).__name__}",
                    lineno=node.lineno,
                    filename=self.filename,
                )
            return f"({left} {op} {right})"

        if isinstance(node, ast.UnaryOp):
            operand = self._translate_expr(node.operand)
            op = _UNARYOP_MAP.get(type(node.op))
            if op is None:
                raise TranslateError(
                    f"unsupported unary operator: {type(node.op).__name__}",
                    lineno=node.lineno,
                    filename=self.filename,
                )
            return f"{op}{operand}"

        if isinstance(node, ast.BoolOp):
            op = _BOOLOP_MAP[type(node.op)]
            parts = [self._translate_expr(v) for v in node.values]
            return f" {op} ".join(parts)

        if isinstance(node, ast.Compare):
            result = self._translate_expr(node.left)
            for cmp_op, comparator in zip(node.ops, node.comparators):
                mn_op = _CMPOP_MAP.get(type(cmp_op))
                if mn_op is None:
                    if isinstance(cmp_op, ast.In):
                        # `x in y` is not directly supported; approximate
                        raise TranslateError(
                            "'in' membership test not yet supported in expressions",
                            lineno=node.lineno,
                            filename=self.filename,
                        )
                    if isinstance(cmp_op, ast.NotIn):
                        raise TranslateError(
                            "'not in' membership test not yet supported in expressions",
                            lineno=node.lineno,
                            filename=self.filename,
                        )
                    if isinstance(cmp_op, ast.Is):
                        mn_op = "=="
                    elif isinstance(cmp_op, ast.IsNot):
                        mn_op = "!="
                    else:
                        raise TranslateError(
                            f"unsupported comparison: {type(cmp_op).__name__}",
                            lineno=node.lineno,
                            filename=self.filename,
                        )
                right = self._translate_expr(comparator)
                result = f"({result} {mn_op} {right})"
            return result

        if isinstance(node, ast.Call):
            return self._translate_call(node)

        if isinstance(node, ast.Attribute):
            value = self._translate_expr(node.value)
            return f"{value}.{node.attr}"

        if isinstance(node, ast.Subscript):
            value = self._translate_expr(node.value)
            idx = self._translate_expr(node.slice)
            return f"{value}[{idx}]"

        if isinstance(node, ast.List):
            elts = ", ".join(self._translate_expr(e) for e in node.elts)
            return f"[{elts}]"

        if isinstance(node, ast.Dict):
            pairs: list[str] = []
            for k, v in zip(node.keys, node.values):
                if k is None:
                    continue  # ** unpacking not supported
                ks = self._translate_expr(k)
                vs = self._translate_expr(v)
                pairs.append(f"{ks}: {vs}")
            return "{" + ", ".join(pairs) + "}"

        if isinstance(node, ast.Tuple):
            # Mapanare doesn't have tuples; emit as a list
            elts = ", ".join(self._translate_expr(e) for e in node.elts)
            return f"[{elts}]"

        if isinstance(node, ast.JoinedStr):
            # f-string → string concatenation
            return self._translate_fstring(node)

        if isinstance(node, ast.IfExp):
            # Ternary: `a if cond else b` → inline if/else expression
            cond = self._translate_expr(node.test)
            body = self._translate_expr(node.body)
            orelse = self._translate_expr(node.orelse)
            return f"if {cond} {{ {body} }} else {{ {orelse} }}"

        if isinstance(node, ast.Lambda):
            params = ", ".join(a.arg for a in node.args.args)
            body = self._translate_expr(node.body)
            return f"({params}) => {body}"

        if isinstance(node, ast.Index):
            # Python 3.8 compat
            return self._translate_expr(node.value)  # type: ignore[attr-defined]

        raise TranslateError(
            f"unsupported expression: {type(node).__name__}",
            lineno=getattr(node, "lineno", 0),
            filename=self.filename,
        )

    def _translate_call(self, node: ast.Call) -> str:
        """Translate a function call expression."""
        args = ", ".join(self._translate_expr(a) for a in node.args)

        if isinstance(node.func, ast.Name):
            name = node.func.id
            # Map Python builtins to Mapanare equivalents
            if name == "print":
                return f"print({args})"
            if name == "len":
                return f"len({args})"
            if name == "str":
                return f"str({args})"
            if name == "int":
                return f"int({args})"
            if name == "float":
                return f"float({args})"
            if name == "range":
                return self._translate_range(node)
            if name == "isinstance":
                # Not directly supported
                raise TranslateError(
                    "isinstance() is not supported; use pattern matching instead",
                    lineno=node.lineno,
                    filename=self.filename,
                )
            return f"{name}({args})"

        if isinstance(node.func, ast.Attribute):
            obj = self._translate_expr(node.func.value)
            method = node.func.attr
            # Map common Python methods
            method_map: dict[str, str] = {
                "append": "push",
                "upper": "to_upper",
                "lower": "to_lower",
                "strip": "trim",
                "lstrip": "trim_start",
                "rstrip": "trim_end",
                "startswith": "starts_with",
                "endswith": "ends_with",
                "replace": "replace",
                "split": "split",
                "join": "join",
                "find": "index_of",
                "format": "format",
            }
            mn_method = method_map.get(method, method)
            return f"{obj}.{mn_method}({args})"

        func = self._translate_expr(node.func)
        return f"{func}({args})"

    def _translate_range(self, node: ast.Call) -> str:
        """Translate range() to Mapanare range expression (start..end)."""
        nargs = len(node.args)
        if nargs == 1:
            end = self._translate_expr(node.args[0])
            return f"0..{end}"
        if nargs == 2:
            start = self._translate_expr(node.args[0])
            end = self._translate_expr(node.args[1])
            return f"{start}..{end}"
        if nargs == 3:
            # range(start, end, step) — Mapanare doesn't have step in range syntax
            start = self._translate_expr(node.args[0])
            end = self._translate_expr(node.args[1])
            # Emit just start..end with a comment about the step
            return f"{start}..{end}  // WARNING: step ignored"
        return "0..0"

    def _translate_fstring(self, node: ast.JoinedStr) -> str:
        """Translate an f-string to Mapanare string concatenation."""
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                escaped = value.value.replace("\\", "\\\\").replace('"', '\\"')
                parts.append(f'"{escaped}"')
            elif isinstance(value, ast.FormattedValue):
                expr = self._translate_expr(value.value)
                parts.append(f"str({expr})")
            else:
                parts.append(self._translate_expr(value))
        if not parts:
            return '""'
        return " + ".join(parts)

    # -- Statement translation --

    def _translate_body(self, stmts: list[ast.stmt]) -> None:
        """Translate a block of statements with indentation."""
        self._indent.push()
        self._push_scope()
        for stmt in stmts:
            self._translate_stmt(stmt)
        self._pop_scope()
        self._indent.pop()

    def _translate_stmt(self, node: ast.stmt) -> None:
        """Translate a single Python statement."""
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            self._translate_function(node)
        elif isinstance(node, ast.ClassDef):
            self._translate_class(node)
        elif isinstance(node, ast.Return):
            self._translate_return(node)
        elif isinstance(node, ast.Assign):
            self._translate_assign(node)
        elif isinstance(node, ast.AugAssign):
            self._translate_aug_assign(node)
        elif isinstance(node, ast.AnnAssign):
            self._translate_ann_assign(node)
        elif isinstance(node, ast.If):
            self._translate_if(node)
        elif isinstance(node, ast.For):
            self._translate_for(node)
        elif isinstance(node, ast.While):
            self._translate_while(node)
        elif isinstance(node, ast.Expr):
            # Expression statement (e.g., function call)
            expr = self._translate_expr(node.value)
            self._emit(expr)
        elif isinstance(node, ast.Pass):
            self._emit("// pass")
        elif isinstance(node, ast.Break):
            self._emit("break")
        elif isinstance(node, ast.Continue):
            self._emit("continue")
        elif isinstance(node, ast.Import):
            self._translate_import(node)
        elif isinstance(node, ast.ImportFrom):
            self._translate_import_from(node)
        elif isinstance(node, ast.Try):
            self._translate_try(node)
        elif isinstance(node, ast.Assert):
            cond = self._translate_expr(node.test)
            if node.msg:
                msg = self._translate_expr(node.msg)
                self._emit(f"// assert {cond}, {msg}")
            else:
                self._emit(f"// assert {cond}")
        elif isinstance(node, ast.Delete):
            self._emit("// del (not supported in Mapanare)")
        elif isinstance(node, ast.Global):
            self._emit(f"// global {', '.join(node.names)}")
        elif isinstance(node, ast.Nonlocal):
            self._emit(f"// nonlocal {', '.join(node.names)}")
        elif isinstance(node, ast.With):
            self._translate_with(node)
        elif isinstance(node, ast.Raise):
            self._translate_raise(node)
        else:
            self._emit(
                f"// TODO: unsupported Python statement: {type(node).__name__} "
                f"(line {getattr(node, 'lineno', '?')})"
            )

    def _translate_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Translate a Python function definition."""
        name = node.name
        if name == "__init__":
            # Skip __init__ in class context; handled by class translation
            return
        if name.startswith("__") and name.endswith("__"):
            # Dunder methods get a comment
            self._emit(f"// skipped dunder method: {name}")
            return

        params = self._translate_params(node.args)
        ret_type = self._translate_type(node.returns)

        ret_annotation = f" -> {ret_type}" if ret_type not in ("any", "Void") else ""
        self._emit(f"fn {name}({params}){ret_annotation} {{")

        self._translate_body(node.body)
        self._emit("}")
        self._emit_raw("")

    def _translate_params(self, args: ast.arguments) -> str:
        """Translate function parameters."""
        params: list[str] = []
        for arg in args.args:
            if arg.arg == "self":
                if self._current_class:
                    params.append("self")
                continue
            ann_type = self._translate_type(arg.annotation)
            if ann_type != "any":
                params.append(f"{arg.arg}: {ann_type}")
            else:
                params.append(arg.arg)
        return ", ".join(params)

    def _translate_return(self, node: ast.Return) -> None:
        """Translate a return statement."""
        if node.value is None:
            self._emit("return")
        else:
            val = self._translate_expr(node.value)
            self._emit(f"return {val}")

    def _translate_assign(self, node: ast.Assign) -> None:
        """Translate an assignment statement."""
        if len(node.targets) != 1:
            self._emit(f"// TODO: multi-target assignment (line {node.lineno})")
            return

        target = node.targets[0]

        if isinstance(target, ast.Attribute):
            # e.g. self.x = value (field assignment)
            obj = self._translate_expr(target.value)
            val = self._translate_expr(node.value)
            self._emit(f"{obj}.{target.attr} = {val}")
            return

        if isinstance(target, ast.Subscript):
            # e.g. items[0] = value
            obj = self._translate_expr(target.value)
            idx = self._translate_expr(target.slice)
            val = self._translate_expr(node.value)
            self._emit(f"{obj}[{idx}] = {val}")
            return

        if isinstance(target, ast.Name):
            name = target.id
            val = self._translate_expr(node.value)
            if self._is_declared(name):
                # Reassignment
                self._emit(f"{name} = {val}")
            else:
                # First assignment → let mut
                inferred = self._infer_type_from_value(node.value)
                if inferred != "any":
                    self._emit(f"let mut {name}: {inferred} = {val}")
                else:
                    self._emit(f"let mut {name} = {val}")
                self._declare(name)
            return

        if isinstance(target, ast.Tuple):
            # Tuple unpacking: a, b = expr
            val = self._translate_expr(node.value)
            self._emit(f"// TODO: tuple unpacking not supported (line {node.lineno})")
            self._emit(f"// {ast.dump(target)} = {val}")
            return

        self._emit(f"// TODO: unsupported assignment target: {type(target).__name__}")

    def _translate_aug_assign(self, node: ast.AugAssign) -> None:
        """Translate augmented assignment (+=, -=, etc.)."""
        target = self._translate_expr(node.target)
        val = self._translate_expr(node.value)
        op = _BINOP_MAP.get(type(node.op), "?")
        self._emit(f"{target} = {target} {op} {val}")

    def _translate_ann_assign(self, node: ast.AnnAssign) -> None:
        """Translate annotated assignment: x: int = 5."""
        if node.target is None or not isinstance(node.target, ast.Name):
            self._emit(f"// TODO: unsupported annotated assignment (line {node.lineno})")
            return

        name = node.target.id
        ann_type = self._translate_type(node.annotation)

        if node.value is not None:
            val = self._translate_expr(node.value)
            self._emit(f"let mut {name}: {ann_type} = {val}")
        else:
            # Declaration without value — emit as comment
            self._emit(f"// {name}: {ann_type} (uninitialized)")
        self._declare(name)

    def _translate_if(self, node: ast.If) -> None:
        """Translate an if/elif/else chain."""
        cond = self._translate_expr(node.test)
        self._emit(f"if {cond} {{")
        self._translate_body(node.body)

        orelse = node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                # elif
                elif_node = orelse[0]
                cond = self._translate_expr(elif_node.test)
                self._emit(f"}} else if {cond} {{")
                self._translate_body(elif_node.body)
                orelse = elif_node.orelse
            else:
                # else
                self._emit("} else {")
                self._translate_body(orelse)
                orelse = []

        self._emit("}")

    def _translate_for(self, node: ast.For) -> None:
        """Translate a for loop."""
        target = self._translate_expr(node.target)

        # Check if iterating over range()
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range":
                range_expr = self._translate_range(node.iter)
                self._emit(f"for {target} in {range_expr} {{")
                self._declare(target)
                self._translate_body(node.body)
                self._emit("}")
                return

        iter_expr = self._translate_expr(node.iter)
        self._emit(f"for {target} in {iter_expr} {{")
        self._declare(target)
        self._translate_body(node.body)
        self._emit("}")

    def _translate_while(self, node: ast.While) -> None:
        """Translate a while loop."""
        cond = self._translate_expr(node.test)
        self._emit(f"while {cond} {{")
        self._translate_body(node.body)
        self._emit("}")

    def _translate_class(self, node: ast.ClassDef) -> None:
        """Translate a Python class to a Mapanare struct + impl block."""
        name = node.name
        self._current_class = name

        # Find __init__ to extract fields
        fields: list[tuple[str, str]] = []
        init_method: ast.FunctionDef | None = None
        methods: list[ast.FunctionDef] = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "__init__":
                    init_method = item
                elif not (item.name.startswith("__") and item.name.endswith("__")):
                    methods.append(item)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Class-level annotated field
                field_name = item.target.id
                field_type = self._translate_type(item.annotation)
                fields.append((field_name, field_type))

        # Extract fields from __init__ (self.x = ... assignments)
        if init_method is not None:
            init_fields = self._extract_init_fields(init_method)
            # Merge: init fields take precedence if duplicated
            existing_names = {f[0] for f in fields}
            for fname, ftype in init_fields:
                if fname not in existing_names:
                    fields.append((fname, ftype))

        # Emit struct
        self._emit(f"struct {name} {{")
        self._indent.push()
        for i, (fname, ftype) in enumerate(fields):
            comma = "," if i < len(fields) - 1 else ""
            self._emit(f"{fname}: {ftype}{comma}")
        self._indent.pop()
        self._emit("}")
        self._emit_raw("")

        # Emit impl block with methods
        if methods:
            self._emit(f"impl {name} {{")
            self._indent.push()
            for method in methods:
                self._translate_function(method)
            self._indent.pop()
            self._emit("}")
            self._emit_raw("")

        self._current_class = None

    def _extract_init_fields(self, init: ast.FunctionDef) -> list[tuple[str, str]]:
        """Extract fields from __init__ body by looking at self.x = ... assignments."""
        fields: list[tuple[str, str]] = []
        seen: set[str] = set()

        # Also check __init__ parameter annotations for types
        param_types: dict[str, str] = {}
        for arg in init.args.args:
            if arg.arg != "self" and arg.annotation:
                param_types[arg.arg] = self._translate_type(arg.annotation)

        for stmt in init.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    fname = target.attr
                    if fname in seen:
                        continue
                    seen.add(fname)
                    # Try to get type from init param or infer from value
                    if isinstance(stmt.value, ast.Name) and stmt.value.id in param_types:
                        ftype = param_types[stmt.value.id]
                    else:
                        ftype = self._infer_type_from_value(stmt.value)
                    fields.append((fname, ftype))

        return fields

    def _translate_import(self, node: ast.Import) -> None:
        """Translate import statement to a comment (no direct equivalent)."""
        for alias in node.names:
            self._emit(f"// import {alias.name}")

    def _translate_import_from(self, node: ast.ImportFrom) -> None:
        """Translate from-import statement."""
        module = node.module or ""
        names = ", ".join(
            a.name if a.asname is None else f"{a.name} as {a.asname}" for a in node.names
        )
        self._emit(f"// from {module} import {names}")

    def _translate_try(self, node: ast.Try) -> None:
        """Translate try/except to comments (Mapanare uses Result types)."""
        self._emit("// try {")
        self._translate_body(node.body)
        for handler in node.handlers:
            exc_type = ""
            if handler.type:
                exc_type = self._translate_expr(handler.type)
            exc_name = handler.name or "_"
            self._emit(f"// }} catch ({exc_type} {exc_name}) {{")
            self._translate_body(handler.body)
        if node.finalbody:
            self._emit("// } finally {")
            self._translate_body(node.finalbody)
        self._emit("// }")

    def _translate_with(self, node: ast.With) -> None:
        """Translate with statement to a block with comment."""
        items_str = ", ".join(self._translate_expr(item.context_expr) for item in node.items)
        self._emit(f"// with {items_str} {{")
        self._translate_body(node.body)
        self._emit("// }")

    def _translate_raise(self, node: ast.Raise) -> None:
        """Translate raise to a comment (Mapanare uses Result types)."""
        if node.exc:
            exc = self._translate_expr(node.exc)
            self._emit(f"return Err({exc})  // raise {exc}")
        else:
            self._emit("// raise (re-raise not supported)")

    # -- Top-level translation --

    def translate(self, source: str) -> str:
        """Translate Python source text to Mapanare source text."""
        try:
            tree = ast.parse(source, filename=self.filename)
        except SyntaxError as e:
            raise TranslateError(
                f"Python syntax error: {e.msg}",
                lineno=e.lineno or 0,
                filename=self.filename,
            ) from e

        self._lines = []
        self._emit_raw(f"// Translated from {self.filename} by mapanare transpile")
        self._emit_raw("")

        # Separate top-level constructs
        functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        classes: list[ast.ClassDef] = []
        global_stmts: list[ast.stmt] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)
            else:
                global_stmts.append(node)

        # Emit imports as comments
        for stmt in global_stmts:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                self._translate_stmt(stmt)

        if classes or functions:
            self._emit_raw("")

        # Emit structs from classes
        for cls in classes:
            self._translate_class(cls)

        # Emit functions
        for func in functions:
            self._translate_function(func)

        # Gather remaining global statements (non-import) into fn main()
        main_stmts = [s for s in global_stmts if not isinstance(s, (ast.Import, ast.ImportFrom))]

        # Check if there's already a main function
        has_main = any(
            isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name == "main"
            for f in functions
        )

        if main_stmts and not has_main:
            self._emit("fn main() {")
            self._translate_body(main_stmts)
            self._emit("}")
            self._emit_raw("")

        return "\n".join(self._lines) + "\n"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def translate_to_mn(source: str, filename: str = "<stdin>") -> str:
    """Translate Python source code into Mapanare (.mn) source text.

    Parameters
    ----------
    source:
        The Python source code to translate.
    filename:
        The filename used in error messages and the output header comment.

    Returns
    -------
    str
        Valid Mapanare source code that can be parsed by the Mapanare parser.

    Raises
    ------
    TranslateError
        If a Python construct cannot be translated.
    """
    translator = PythonTranslator(filename=filename)
    return translator.translate(source)
