# VS Code Extension Publish Steps

Steps to publish the Mapanare VS Code extension to the marketplace.
This is a lead decision — the artifact is ready as of v4.40.0.

## Prerequisites

1. `vsce` installed: `npm install -g @vscode/vsce`
2. A Personal Access Token (PAT) from dev.azure.com
3. Publisher `mapanare-research` registered

## Steps

```bash
cd editor/vscode
vsce package    # creates mapanare-0.6.0.vsix
vsce publish    # pushes to marketplace
```

## Pre-publish checklist

- [ ] `package.json` version matches the release
- [ ] README.md has current screenshots
- [ ] All LSP features tested manually (MANUAL_SMOKE_TEST.md)
- [ ] CHANGELOG.md in extension dir up to date
