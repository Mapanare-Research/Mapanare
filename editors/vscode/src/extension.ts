import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const config = vscode.workspace.getConfiguration("mapanare");

  // -- LSP client -----------------------------------------------------------

  if (config.get<boolean>("lsp.enabled", true)) {
    startLanguageServer(context, config);
  }

  // -- Commands -------------------------------------------------------------

  context.subscriptions.push(
    vscode.commands.registerCommand("mapanare.run", () => {
      runMapaCommand("run");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("mapanare.check", () => {
      runMapaCommand("check");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("mapanare.compile", () => {
      runMapaCommand("compile");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("mapanare.fmt", () => {
      runMapaCommand("fmt");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("mapanare.restartLsp", async () => {
      if (client) {
        await client.stop();
        await client.start();
        vscode.window.showInformationMessage(
          "Mapanare Language Server restarted."
        );
      }
    })
  );
}

export function deactivate(): Thenable<void> | undefined {
  if (client) {
    return client.stop();
  }
  return undefined;
}

// -- Helpers ----------------------------------------------------------------

function startLanguageServer(
  context: vscode.ExtensionContext,
  config: vscode.WorkspaceConfiguration
): void {
  const lspPath = config.get<string>("lsp.path", "mapanare-lsp");

  const serverOptions: ServerOptions = {
    command: lspPath,
    args: [],
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "mapanare" }],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher("**/*.mn"),
    },
  };

  client = new LanguageClient(
    "mapanare-lsp",
    "Mapanare Language Server",
    serverOptions,
    clientOptions
  );

  client.start();
  context.subscriptions.push({
    dispose: () => {
      client?.stop();
    },
  });
}

function runMapaCommand(subcmd: string): void {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active Mapanare file.");
    return;
  }

  const doc = editor.document;
  if (doc.languageId !== "mapanare") {
    vscode.window.showWarningMessage(
      "Active file is not a Mapanare (.mn) file."
    );
    return;
  }

  // Save before running
  doc.save().then(() => {
    const config = vscode.workspace.getConfiguration("mapanare");
    const mapaPath = config.get<string>("compiler.path", "mapa");
    const filePath = doc.uri.fsPath;

    const terminal =
      vscode.window.terminals.find((t) => t.name === "Mapanare") ||
      vscode.window.createTerminal("Mapanare");

    terminal.show();
    terminal.sendText(`${mapaPath} ${subcmd} "${filePath}"`);
  });
}
