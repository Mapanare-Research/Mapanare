<div align="center">

<img width="1280" height="640" alt="mapanare-repo" src="https://github.com/user-attachments/assets/176d26e7-0c42-49ef-99d2-b8192cd75e53" />

# Mapanare

**/mah-pah-NAH-reh/**

**A linguagem de programacao AI-nativa.**

*Agentes. Sinais. Streams. Tensores. De primeira classe, nao frameworks.*

Compila para binarios nativos via LLVM e WebAssembly.
**~168x mais rapido que Python. No mesmo nivel de Rust e C.**

[English](../README.md) | [Espanol](README.es.md) | [中文版](README.zh-CN.md) | Portugues

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-Backend_Nativo-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![WebAssembly](https://img.shields.io/badge/WebAssembly-Backend-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)
![Plataforma](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![Licenca](https://img.shields.io/badge/licenca-MIT-green.svg?style=flat-square)](../LICENSE)
[![Versao](https://img.shields.io/badge/versao-5.0.6-blue.svg?style=flat-square)](../CHANGELOG.md)
[![Testes](https://img.shields.io/badge/testes-5720+_passando-brightgreen.svg?style=flat-square)]()
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**Website**](https://mapanare.dev) · [**Documentacao**](https://mapanare.dev/docs) · [**Downloads**](https://mapanare.dev/download) · [**Discord**](https://discord.gg/5hpGBm3WXf)

</div>

---

## Instalar

```bash
curl -fsSL https://mapanare.dev/install | bash
```

```powershell
# Windows (PowerShell)
irm https://mapanare.dev/install.ps1 | iex
```

Ou baixe binarios em [Releases](https://github.com/Mapanare-Research/Mapanare/releases).

---

## Hello World

```mn
fn main() {
    print("ola do mapanare")
}
```

```bash
mapanare run hello.mn        # compilar + executar
mapanare build hello.mn      # produzir um binario nativo
```

---

## Escreva Python, Compile Nativo

Pegue seus scripts Python existentes e compile para binarios nativos:

```bash
mapanare build seu_script.py -o seu_script
./seu_script   # 33-239x mais rapido
```

[Guia Python para Nativo](https://mapanare.dev/docs/guides/python-to-native)

---

## Recursos da Linguagem

```mn
// Agentes — atores concorrentes de primeira classe
agent Contador {
    state count: Int = 0
    on incrementar { count = count + 1 }
    on obter_contagem -> Int { return count }
}

// Sinais — estado reativo
let temperatura = signal(72.0)
let alerta = computed(() => temperatura.get() > 100.0)

// Streams — pipelines de dados composiveis
let resultados = data_stream
    |> filter((x) => x > 0)
    |> map((x) => x * 2)
    |> collect()

// Pattern matching
match resposta {
    Ok(dados) => processar(dados),
    Err(e) => print(e)
}

// AI stdlib
import ai::llm
let resposta = ask(ollama("llama3.2"), "O que e Mapanare?")
```

Referencia completa, tutoriais e receitas em [mapanare.dev/docs](https://mapanare.dev/docs).

---

## Contribuir

Veja [CONTRIBUTING.md](../CONTRIBUTING.md). Mudancas na linguagem requerem um [RFC](rfcs/).

## Licenca

Licenca MIT — veja [LICENSE](../LICENSE).

---

<div align="center">

**Mapanare** — A linguagem que a IA merece.

[Reportar Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [Solicitar Feature](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

Feito com carinho por [Juan Denis](https://juandenis.com)

</div>
