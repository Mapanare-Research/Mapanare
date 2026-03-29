"""Mapanare Language Server — provides hover, go-to-def, find-refs, diagnostics, and completion."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer

from mapanare.lsp.analysis import (
    DocumentAnalysis,
    analyze_document,
    invalidate_document,
)

logger = logging.getLogger("mapanare-lsp")

server = LanguageServer("mapanare-lsp", "v0.5.0")

# Document cache: uri -> DocumentAnalysis
_documents: dict[str, DocumentAnalysis] = {}
# Source text cache: uri -> source string (needed for formatting and code actions)
_sources: dict[str, str] = {}
# Diagnostics with fix info: uri -> list of (lsp.Diagnostic, LspDiagnostic) pairs
_fixable_diagnostics: dict[str, list[tuple[lsp.Diagnostic, object]]] = {}


def _analyze_and_publish(uri: str, source: str) -> None:
    """Analyze a document and publish diagnostics."""
    _sources[uri] = source
    analysis, diags = analyze_document(uri, source)
    if analysis:
        _documents[uri] = analysis

    diagnostics: list[lsp.Diagnostic] = []
    fixable: list[tuple[lsp.Diagnostic, object]] = []

    for d in diags:
        line = max(0, d.line - 1)
        col = max(0, d.column - 1)
        end_line = max(0, d.end_line - 1) if d.end_line else line
        end_col = max(0, d.end_column - 1) if d.end_column else col + 1

        severity_map = {
            "error": lsp.DiagnosticSeverity.Error,
            "warning": lsp.DiagnosticSeverity.Warning,
            "info": lsp.DiagnosticSeverity.Information,
            "hint": lsp.DiagnosticSeverity.Hint,
        }

        lsp_diag = lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=line, character=col),
                end=lsp.Position(line=end_line, character=end_col),
            ),
            message=d.message,
            severity=severity_map.get(d.severity, lsp.DiagnosticSeverity.Error),
            source="mapanare",
        )

        # Attach suggestions as related information
        if d.suggestions:
            suggestion_text = "; ".join(s.message for s in d.suggestions)
            lsp_diag.message = f"{d.message} ({suggestion_text})"

        diagnostics.append(lsp_diag)

        # Track fixable diagnostics (W002, W005)
        if d.severity == "warning" and ("[W002]" in d.message or "[W005]" in d.message):
            fixable.append((lsp_diag, d))

    _fixable_diagnostics[uri] = fixable

    server.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
    )


# -- Lifecycle ---------------------------------------------------------------


@server.feature(lsp.INITIALIZE)
def on_initialize(params: lsp.InitializeParams) -> lsp.InitializeResult:
    return lsp.InitializeResult(
        capabilities=lsp.ServerCapabilities(
            text_document_sync=lsp.TextDocumentSyncOptions(
                open_close=True,
                change=lsp.TextDocumentSyncKind.Full,
                save=lsp.SaveOptions(include_text=True),
            ),
            hover_provider=True,
            definition_provider=True,
            references_provider=True,
            completion_provider=lsp.CompletionOptions(
                trigger_characters=[".", ":", "<"],
                resolve_provider=False,
            ),
            code_action_provider=lsp.CodeActionOptions(
                code_action_kinds=[
                    lsp.CodeActionKind.QuickFix,
                    lsp.CodeActionKind.SourceFixAll,
                ],
            ),
            document_formatting_provider=True,
        ),
    )


# -- Document sync -----------------------------------------------------------


@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def on_open(params: lsp.DidOpenTextDocumentParams) -> None:
    uri = params.text_document.uri
    source = params.text_document.text
    _analyze_and_publish(uri, source)


@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def on_change(params: lsp.DidChangeTextDocumentParams) -> None:
    uri = params.text_document.uri
    if params.content_changes:
        source = params.content_changes[-1].text
        _analyze_and_publish(uri, source)


@server.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
def on_save(params: lsp.DidSaveTextDocumentParams) -> None:
    uri = params.text_document.uri
    if params.text:
        _analyze_and_publish(uri, params.text)


@server.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def on_close(params: lsp.DidCloseTextDocumentParams) -> None:
    uri = params.text_document.uri
    _documents.pop(uri, None)
    _sources.pop(uri, None)
    _fixable_diagnostics.pop(uri, None)
    invalidate_document(uri)
    server.text_document_publish_diagnostics(lsp.PublishDiagnosticsParams(uri=uri, diagnostics=[]))


# -- Hover ------------------------------------------------------------------


@server.feature(lsp.TEXT_DOCUMENT_HOVER)
def on_hover(params: lsp.HoverParams) -> Optional[lsp.Hover]:
    uri = params.text_document.uri
    analysis = _documents.get(uri)
    if not analysis:
        return None

    line = params.position.line
    col = params.position.character
    content = analysis.hover_at(line, col)
    if content:
        return lsp.Hover(
            contents=lsp.MarkupContent(
                kind=lsp.MarkupKind.Markdown,
                value=content,
            )
        )
    return None


# -- Go to definition -------------------------------------------------------


@server.feature(lsp.TEXT_DOCUMENT_DEFINITION)
def on_definition(
    params: lsp.DefinitionParams,
) -> Optional[lsp.Location]:
    uri = params.text_document.uri
    analysis = _documents.get(uri)
    if not analysis:
        return None

    line = params.position.line
    col = params.position.character
    loc = analysis.definition_at(line, col)
    if loc:
        return lsp.Location(
            uri=loc.uri,
            range=lsp.Range(
                start=lsp.Position(line=loc.line, character=loc.column),
                end=lsp.Position(line=loc.end_line, character=loc.end_column),
            ),
        )
    return None


# -- Find references ---------------------------------------------------------


@server.feature(lsp.TEXT_DOCUMENT_REFERENCES)
def on_references(
    params: lsp.ReferenceParams,
) -> Optional[list[lsp.Location]]:
    uri = params.text_document.uri
    analysis = _documents.get(uri)
    if not analysis:
        return None

    line = params.position.line
    col = params.position.character
    refs = analysis.references_at(line, col)
    if not refs:
        return None

    return [
        lsp.Location(
            uri=r.uri,
            range=lsp.Range(
                start=lsp.Position(line=r.line, character=r.column),
                end=lsp.Position(line=r.end_line, character=r.end_column),
            ),
        )
        for r in refs
    ]


# -- Completion --------------------------------------------------------------


@server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
def on_completion(
    params: lsp.CompletionParams,
) -> lsp.CompletionList:
    uri = params.text_document.uri
    analysis = _documents.get(uri)
    if not analysis:
        return lsp.CompletionList(is_incomplete=False, items=[])

    line = params.position.line
    col = params.position.character
    candidates = analysis.completions_at(line, col)

    items: list[lsp.CompletionItem] = []
    for c in candidates:
        kind = _map_completion_kind(c.kind)
        items.append(
            lsp.CompletionItem(
                label=c.label,
                kind=kind,
                detail=c.detail,
                documentation=c.documentation or None,
            )
        )

    return lsp.CompletionList(is_incomplete=False, items=items)


# -- Code actions (Quick Fix) ------------------------------------------------


@server.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)
def on_code_action(
    params: lsp.CodeActionParams,
) -> Optional[list[lsp.CodeAction]]:
    uri = params.text_document.uri
    fixable = _fixable_diagnostics.get(uri, [])
    if not fixable:
        return None

    source = _sources.get(uri, "")
    lines = source.split("\n")
    actions: list[lsp.CodeAction] = []

    for lsp_diag, raw_diag in fixable:
        # Check if this diagnostic overlaps with the requested range
        diag_range = lsp_diag.range
        if diag_range.end.line < params.range.start.line:
            continue
        if diag_range.start.line > params.range.end.line:
            continue

        line_idx = diag_range.start.line
        if line_idx >= len(lines):
            continue

        if "[W002]" in lsp_diag.message:
            # Fix: remove the unused import line
            edit = lsp.TextEdit(
                range=lsp.Range(
                    start=lsp.Position(line=line_idx, character=0),
                    end=lsp.Position(line=line_idx + 1, character=0),
                ),
                new_text="",
            )
            actions.append(
                lsp.CodeAction(
                    title="Remove unused import",
                    kind=lsp.CodeActionKind.QuickFix,
                    diagnostics=[lsp_diag],
                    edit=lsp.WorkspaceEdit(
                        changes={uri: [edit]},
                    ),
                )
            )

        elif "[W005]" in lsp_diag.message:
            # Fix: remove `mut` keyword
            old_line = lines[line_idx]
            new_line = old_line.replace("let mut ", "let ", 1)
            if new_line != old_line:
                edit = lsp.TextEdit(
                    range=lsp.Range(
                        start=lsp.Position(line=line_idx, character=0),
                        end=lsp.Position(line=line_idx, character=len(old_line)),
                    ),
                    new_text=new_line,
                )
                actions.append(
                    lsp.CodeAction(
                        title="Remove unnecessary `mut`",
                        kind=lsp.CodeActionKind.QuickFix,
                        diagnostics=[lsp_diag],
                        edit=lsp.WorkspaceEdit(
                            changes={uri: [edit]},
                        ),
                    )
                )

    # "Fix all" action when there are multiple fixes
    if len(actions) > 1:
        all_edits: list[lsp.TextEdit] = []
        all_diags: list[lsp.Diagnostic] = []
        for action in actions:
            if action.edit and action.edit.changes:
                all_edits.extend(action.edit.changes.get(uri, []))
            if action.diagnostics:
                all_diags.extend(action.diagnostics)
        actions.append(
            lsp.CodeAction(
                title="Fix all auto-fixable lint warnings",
                kind=lsp.CodeActionKind.SourceFixAll,
                diagnostics=all_diags,
                edit=lsp.WorkspaceEdit(changes={uri: all_edits}),
            )
        )

    return actions if actions else None


# -- Document formatting -----------------------------------------------------


@server.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def on_formatting(
    params: lsp.DocumentFormattingParams,
) -> Optional[list[lsp.TextEdit]]:
    uri = params.text_document.uri
    source = _sources.get(uri)
    if source is None:
        return None

    from mapanare.cli import _format_mapanare

    formatted = _format_mapanare(source)
    if formatted == source:
        return None

    # Replace the entire document
    line_count = source.count("\n")
    last_line = source.split("\n")[-1] if source else ""
    return [
        lsp.TextEdit(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=line_count, character=len(last_line)),
            ),
            new_text=formatted,
        )
    ]


def _map_completion_kind(kind: str) -> lsp.CompletionItemKind:
    return {
        "function": lsp.CompletionItemKind.Function,
        "variable": lsp.CompletionItemKind.Variable,
        "keyword": lsp.CompletionItemKind.Keyword,
        "type": lsp.CompletionItemKind.Class,
        "class": lsp.CompletionItemKind.Class,
        "struct": lsp.CompletionItemKind.Struct,
        "enum": lsp.CompletionItemKind.Enum,
        "enum_member": lsp.CompletionItemKind.EnumMember,
        "field": lsp.CompletionItemKind.Field,
        "text": lsp.CompletionItemKind.Text,
    }.get(kind, lsp.CompletionItemKind.Text)


def main() -> None:
    """Entry point for the Mapanare language server."""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    logger.info("Starting Mapanare Language Server")
    server.start_io()


if __name__ == "__main__":
    main()
