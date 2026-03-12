"""Generate HTML documentation from Mapanare doc comments (/// syntax)."""

from __future__ import annotations

import html
from dataclasses import dataclass

from mapanare.ast_nodes import (
    AgentDef,
    DocComment,
    EnumDef,
    ExportDef,
    FnDef,
    Param,
    Program,
    StructDef,
    TraitDef,
    TypeAlias,
    TypeExpr,
)


@dataclass
class DocItem:
    """A documented item extracted from the AST."""

    name: str = ""
    kind: str = ""  # "function", "struct", "enum", "agent", "trait", "type"
    doc: str = ""
    signature: str = ""
    public: bool = False


def _type_to_str(t: TypeExpr | None) -> str:
    if t is None:
        return "Void"
    from mapanare.ast_nodes import FnType, GenericType, NamedType, TensorType

    if isinstance(t, NamedType):
        return t.name
    if isinstance(t, GenericType):
        args = ", ".join(_type_to_str(a) for a in t.args)
        return f"{t.name}<{args}>"
    if isinstance(t, TensorType):
        return f"Tensor<{_type_to_str(t.element_type)}>[...]"
    if isinstance(t, FnType):
        params = ", ".join(_type_to_str(p) for p in t.param_types)
        return f"fn({params}) -> {_type_to_str(t.return_type)}"
    return "?"


def _param_str(p: Param) -> str:
    return f"{p.name}: {_type_to_str(p.type_annotation)}"


def _fn_signature(fn: FnDef) -> str:
    params = ", ".join(_param_str(p) for p in fn.params)
    ret = _type_to_str(fn.return_type)
    pub = "pub " if fn.public else ""
    return f"{pub}fn {fn.name}({params}) -> {ret}"


def extract_doc_items(program: Program) -> list[DocItem]:
    """Extract documented items from a program AST."""
    items: list[DocItem] = []
    for defn in program.definitions:
        if isinstance(defn, DocComment) and defn.definition:
            inner = defn.definition
            item = _definition_to_item(inner, defn.text)
            if item:
                items.append(item)
        elif isinstance(defn, ExportDef) and defn.definition:
            if isinstance(defn.definition, DocComment) and defn.definition.definition:
                item = _definition_to_item(defn.definition.definition, defn.definition.text)
                if item:
                    item.public = True
                    items.append(item)
        else:
            item = _definition_to_item(defn, "")
            if item and item.public:
                items.append(item)
    return items


def _definition_to_item(defn: object, doc: str) -> DocItem | None:
    if isinstance(defn, FnDef):
        return DocItem(
            name=defn.name,
            kind="function",
            doc=doc,
            signature=_fn_signature(defn),
            public=defn.public,
        )
    if isinstance(defn, StructDef):
        fields = ", ".join(f"{f.name}: {_type_to_str(f.type_annotation)}" for f in defn.fields)
        return DocItem(
            name=defn.name,
            kind="struct",
            doc=doc,
            signature=f"struct {defn.name} {{ {fields} }}",
            public=defn.public,
        )
    if isinstance(defn, EnumDef):
        variants = ", ".join(v.name for v in defn.variants)
        return DocItem(
            name=defn.name,
            kind="enum",
            doc=doc,
            signature=f"enum {defn.name} {{ {variants} }}",
            public=defn.public,
        )
    if isinstance(defn, AgentDef):
        inputs = ", ".join(f"{i.name}: {_type_to_str(i.type_annotation)}" for i in defn.inputs)
        outputs = ", ".join(f"{o.name}: {_type_to_str(o.type_annotation)}" for o in defn.outputs)
        return DocItem(
            name=defn.name,
            kind="agent",
            doc=doc,
            signature=f"agent {defn.name} {{ input: {inputs}; output: {outputs} }}",
            public=defn.public,
        )
    if isinstance(defn, TraitDef):
        methods = ", ".join(m.name for m in defn.methods)
        return DocItem(
            name=defn.name,
            kind="trait",
            doc=doc,
            signature=f"trait {defn.name} {{ {methods} }}",
            public=defn.public,
        )
    if isinstance(defn, TypeAlias):
        return DocItem(
            name=defn.name,
            kind="type",
            doc=doc,
            signature=f"type {defn.name} = {_type_to_str(defn.type_expr)}",
            public=defn.public,
        )
    return None


def generate_html(items: list[DocItem], module_name: str = "module") -> str:
    """Generate HTML documentation page from doc items."""
    sections: list[str] = []
    sections.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(module_name)} — Mapanare Documentation</title>
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  max-width: 900px; margin: 0 auto; padding: 2rem;
  color: #1a1a2e; background: #fafafa;
}}
h1 {{ color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 0.5rem; }}
h2 {{ color: #0f3460; margin-top: 2rem; }}
.item {{
  background: #fff; border: 1px solid #e0e0e0;
  border-radius: 8px; padding: 1.5rem; margin: 1rem 0;
}}
.item-header {{ display: flex; align-items: center; gap: 0.5rem; }}
.badge {{
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
}}
.badge-function {{ background: #e3f2fd; color: #1565c0; }}
.badge-struct {{ background: #e8f5e9; color: #2e7d32; }}
.badge-enum {{ background: #fff3e0; color: #e65100; }}
.badge-agent {{ background: #f3e5f5; color: #7b1fa2; }}
.badge-trait {{ background: #fce4ec; color: #c62828; }}
.badge-type {{ background: #e0f7fa; color: #00695c; }}
.badge-pub {{ background: #c8e6c9; color: #1b5e20; font-size: 0.65rem; }}
.signature {{
  font-family: "JetBrains Mono", "Fira Code", monospace;
  background: #f5f5f5; padding: 0.75rem; border-radius: 4px;
  margin: 0.75rem 0; font-size: 0.9rem; overflow-x: auto;
}}
.doc {{ color: #424242; line-height: 1.6; }}
.toc {{
  background: #fff; padding: 1rem 1.5rem;
  border-radius: 8px; border: 1px solid #e0e0e0;
}}
.toc ul {{ list-style: none; padding-left: 1rem; }}
.toc a {{ text-decoration: none; color: #0f3460; }}
.toc a:hover {{ text-decoration: underline; }}
footer {{
  margin-top: 3rem; padding-top: 1rem;
  border-top: 1px solid #e0e0e0; color: #757575; font-size: 0.85rem;
}}
</style>
</head>
<body>
<h1>{html.escape(module_name)}</h1>
""")

    # Group by kind
    groups: dict[str, list[DocItem]] = {}
    for item in items:
        groups.setdefault(item.kind, []).append(item)

    # Table of contents
    sections.append('<div class="toc"><strong>Contents</strong><ul>')
    kind_labels = {
        "function": "Functions",
        "struct": "Structs",
        "enum": "Enums",
        "agent": "Agents",
        "trait": "Traits",
        "type": "Type Aliases",
    }
    for kind, label in kind_labels.items():
        if kind in groups:
            sections.append(f'<li><a href="#{kind}s">{label}</a></li>')
    sections.append("</ul></div>")

    # Emit sections
    for kind, label in kind_labels.items():
        if kind not in groups:
            continue
        sections.append(f'<h2 id="{kind}s">{label}</h2>')
        for item in groups[kind]:
            pub_badge = ' <span class="badge badge-pub">pub</span>' if item.public else ""
            doc_html = f'<p class="doc">{html.escape(item.doc)}</p>' if item.doc else ""
            sections.append(f"""<div class="item" id="{html.escape(item.name)}">
<div class="item-header">
<span class="badge badge-{kind}">{kind}</span>{pub_badge}
<strong>{html.escape(item.name)}</strong>
</div>
<pre class="signature">{html.escape(item.signature)}</pre>
{doc_html}
</div>""")

    sections.append("""<footer>
Generated by <code>mapanare doc</code>
</footer>
</body>
</html>""")

    return "\n".join(sections)
