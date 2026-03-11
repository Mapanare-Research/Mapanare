<div align="center">

<img width="3200" height="1344" alt="MapanareDevTo" src="https://github.com/user-attachments/assets/99b80387-afd9-4b07-beb8-59a8f63f7ac7" />

# Mapanare

**/mah-pah-NAH-reh/**

**A linguagem de programacao AI-nativa.**

*Agentes. Sinais. Streams. Tensores. De primeira classe, nao frameworks.*

Mapanare compila para Python (transpilador) e binarios nativos (LLVM), com um compilador auto-hospedado em desenvolvimento.

[English](../README.md) | [Espanol](README.es.md) | [中文版](README.zh-CN.md) | Portugues

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-Backend_Nativo-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![Plataforma](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![Licenca](https://img.shields.io/badge/licenca-MIT-green.svg?style=flat-square)](../LICENSE)
[![Versao](https://img.shields.io/badge/versao-0.3.1-blue.svg?style=flat-square)](../CHANGELOG.md)
[![Testes](https://img.shields.io/badge/testes-2090_passando_(82_arquivos)-brightgreen.svg?style=flat-square)]()
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**Primeiros Passos**](getting-started.md) · [Por que Mapanare?](#por-que-mapanare) · [Instalar](#instalar) · [A Linguagem](#a-linguagem) · [Benchmarks](#benchmarks) · [CLI](#cli) · [Arquitetura](#arquitetura-do-compilador) · [Roteiro](ROADMAP.md) · [Contribuir](#contribuir) · [Discord](https://discord.gg/5hpGBm3WXf)

</div>

---

## Por que Mapanare?

Todas as linguagens principais tratam agentes, sinais, streams e tensores como construcoes de biblioteca — uma camada de abstracao longe do compilador. Isso significa sem verificacao de fluxo de dados em tempo de compilacao, sem checagem estatica de formas de tensores, e sem garantias a nivel de linguagem sobre passagem de mensagens.

Mapanare torna essas primitivas **parte da linguagem**:

- **Agentes** sao tao naturais quanto funcoes — declarar, criar, enviar, receber, tudo com sintaxe dedicada verificada pelo compilador
- **Sinais** substituem o callback hell com rastreamento automatico de dependencias
- **Streams** compoem com `|>` da forma como voce pensa sobre dados, com fusao de operadores integrada
- **Tensores** obteem validacao de formas em tempo de compilacao — erros de forma capturados antes da execucao
- **Sem POO** — structs, enums e pattern matching em vez de hierarquias de classes

Leia o [manifesto](manifesto.md) completo.

---

## Instalar

### Linux / macOS

```bash
curl -fsSL https://mapanare.dev/install | bash
```

### Windows (PowerShell)

```powershell
irm https://mapanare.dev/install.ps1 | iex
```

### Download Manual

Baixe o ultimo binario em [Releases](https://github.com/Mapanare-Research/Mapanare/releases).

| Plataforma | Arquivo |
|------------|---------|
| Linux (x64) | `mapanare-linux-x64.tar.gz` |
| macOS (Apple Silicon) | `mapanare-mac-arm64.tar.gz` |
| Windows (x64) | `mapanare-win-x64.zip` |

Extraia e adicione `mapanare` ao seu PATH, depois verifique:

```bash
mapanare --version
```

---

## A Linguagem

### Basicos

```mn
fn main() {
    let name = "Mundo"
    println("Ola, " + name + "!")

    let mut count = 0
    while count < 5 {
        println(str(count))
        count += 1
    }

    for i in 0..5 {
        println(str(i))
    }
}
```

### Structs, Enums e Pattern Matching

Sem classes, sem heranca. Structs, enums e pattern matching em seu lugar.

```mn
enum Forma {
    Circulo(Float),
    Rect(Float, Float),
}

fn area(s: Forma) -> Float {
    match s {
        Circulo(r) => 3.14159 * r * r,
        Rect(w, h) => w * h,
    }
}
```

### Tratamento de Erros

```mn
fn dividir(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("divisao por zero")
    }
    return Ok(a / b)
}

let valor = dividir(10.0, 3.0)?
```

### Agentes (Experimental)

Atores concorrentes com canais tipados.

```mn
agent Saudador {
    input nome: String
    output saudacao: String

    fn handle(nome: String) -> String {
        return "Ola, " + nome + "!"
    }
}

let saudador = spawn Saudador()
saudador.nome <- "Mundo"
let resultado = sync saudador.saudacao
print(resultado)
```

### Sinais (Experimental)

Estado reativo com rastreamento automatico de dependencias.

```mn
let mut count = signal(0)
let doubled = signal { count * 2 }
```

### Streams (Experimental)

Pipelines assincronos com o operador `|>`.

```mn
let dados = stream([1, 2, 3, 4, 5])
let resultado = dados
    |> filter(fn(x) { x > 2 })
    |> map(fn(x) { x * 10 })
```

---

## CLI

```
mapanare run <arquivo>       Compilar e executar
mapanare build <arquivo>     Compilar para binario nativo via LLVM
mapanare jit <arquivo>       Compilar JIT e executar nativamente
mapanare check <arquivo>     Apenas verificar tipos
mapanare compile <arquivo>   Transpilar para Python
mapanare emit-llvm <arquivo> Emitir LLVM IR
mapanare repl                Iniciar REPL interativo
mapanare fmt <arquivo>       Formatar codigo fonte
mapanare init [caminho]      Inicializar um novo projeto
mapanare install <pacote>    Instalar um pacote (baseado em git)
mapanare targets             Listar alvos de compilacao suportados
```

---

## Arquitetura do Compilador

```
fonte .mn → Lexer → Parser → AST → Analise Semantica → Otimizador → Emissao
                                                                        ↓
                                                                 Python | LLVM IR
                                                                        ↓
                                                         Interpretador | Binario Nativo
```

---

## Roteiro

| Versao | Tema | Estado |
|--------|------|--------|
| **v0.1.0** | Fundacao — compilador bootstrap, backends duplos, runtime, LSP, stdlib | Lancado |
| **v0.2.0** | Auto-Hospedagem — codegen LLVM, runtime C, compilador auto-hospedado (5.800 linhas .mn) | Lancado |
| **v0.3.0** | Profundidade sobre Amplitude — traits, modulos, codegen de agentes, memoria arena, 1.960+ testes | Lancado |
| **v0.4.0** | Pronto para o Mundo — FFI, endurecimento runtime C, diagnosticos, limpeza de escopo | Proximo |
| **v0.5.0** | O Ecossistema — registro de pacotes, playground WASM, linter | Planejado |
| **v1.0.0** | Estavel — spec da linguagem congelado, garantias de compatibilidade | Planejado |

Veja o [roteiro](ROADMAP.md) completo para detalhes.

---

## Contribuir

Veja [CONTRIBUTING.md](../CONTRIBUTING.md). Os padroes da comunidade e processos do projeto estao em [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md), [GOVERNANCE.md](../GOVERNANCE.md), e [SECURITY.md](../SECURITY.md). Mudancas na linguagem requerem um [RFC](rfcs/).

---

## Licenca

Licenca MIT — veja [LICENSE](../LICENSE) para detalhes.

---

<div align="center">

**Mapanare** — A linguagem que a IA merece.

[Reportar Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [Solicitar Feature](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [Spec](SPEC.md) · [Changelog](../CHANGELOG.md) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

Feito com cuidado por [Juan Denis](https://juandenis.com)

</div>
