"""Mapanare Language Server — provides hover, go-to-def, find-refs, diagnostics, and completion."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer

from mapanare.lsp.analysis import DocumentAnalysis, analyze_document

logger = logging.getLogger("mapanare-lsp")

server = LanguageServer("mapanare-lsp", "v0.2.0")

# Document cache: uri -> DocumentAnalysis
_documents: dict[str, DocumentAnalysis] = {}


def _analyze_and_publish(uri: str, source: str) -> None:
    """Analyze a document and publish diagnostics."""
    analysis, errors = analyze_document(uri, source)
    if analysis:
        _documents[uri] = analysis

    diagnostics: list[lsp.Diagnostic] = []
    for err in errors:
        line = max(0, err.line - 1)
        col = max(0, err.column - 1)
        diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=line, character=col),
                    end=lsp.Position(line=line, character=col + 1),
                ),
                message=err.message,
                severity=lsp.DiagnosticSeverity.Error,
                source="mapanare",
            )
        )

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
