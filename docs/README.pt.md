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
[![Versao](https://img.shields.io/badge/versao-5.41.0-blue.svg?style=flat-square)](../CHANGELOG.md)
[![Testes](https://img.shields.io/badge/testes-5800+_passando-brightgreen.svg?style=flat-square)]()
[![Goldens](https://img.shields.io/badge/goldens-96%2F96-brightgreen.svg?style=flat-square)]()
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

### Compilador nativo — o que `mnc-stage1` entrega

O compilador auto-hospedado roda o corpus completo da v5.27.0 (96/96 goldens nativos):

- **Tensores** — literais, indexacao multi-dim, broadcasting estilo NumPy, slicing, reducoes (sum / mean / max / min / argmax / argmin).
- **Async / await / `block_on`** — coroutines LLVM reais (`presplitcoroutine` + `@llvm.coro.id/begin/save/suspend/end`) com suspensao dirigida pelo scheduler.
- **Parametros tipo closure** — `fn apply(f: fn(Int) -> Int, x: Int)` rebaixado via SSA de chamada indireta.
- **Pattern matching com or-patterns e guards** — `Plus | Minus if cond => body` sobre variantes enum e construtores embutidos (`None` / `Some` / `Ok` / `Err`).
- **Drop-glue de ownership** — lifetimes de string / list / boxed / tensor rastreados em caminhos de retorno e laços; valgrind / ASan / LSan / TSan todos limpos no corpus.
- **Sintaxe terse (arco v5.13–v5.21)** — blocos com dois pontos (Te.1), comprehensions de listas/mapas e lambdas terse (Te.2), interpolacao de strings auto-hospedada (Te.4), ergonomia de structs (Te.5: shorthand de campos, `..base`, destructuring, if-let / while-let / let-else), comparacoes encadeadas (Te.6: `0 < x < 10`).

Ponto fixo auto-hospedado de 3 estagios: STRICT (stage2.ll == stage3.ll byte-identicos em 241,842 linhas; restaurado v5.9.0; mantido atraves da reescrita mecanica de chaves para dois pontos em v5.17.0, da ergonomia de structs em v5.20.0, das comparacoes encadeadas em v5.21.0, da recuperacao CI em v5.23.0, do espelho bootstrap de deprecacao de chaves em v5.23.2, das portas Hy.\* de higiene em v5.24.0, da infraestrutura Pv.\* de prevencao em v5.25.0, das correcoes de codegen Mb.7 + Win64 ABI Mb.9 em v5.26.0, dos fechamentos Eu.\* de payload de enum em v5.26.1, e do fechamento do arco Mc.\* em v5.27.0 — sequencia mais longa na historia do projeto: 23 lancamentos consecutivos). Compilador auto-hospedado encolheu **-2,285 linhas (-8.18%)** liquido de v5.13.0 → v5.21.1 via a reescrita Sh.\* sem quebrar o ponto fixo.

Arco de recuperacao + prevencao v5.23–v5.27: 8 lancamentos fechando os 4 HIGH + 8 MEDIUM do docket painel v5.22.0 + fechando os arcos Mb.\* / Mc.\* / Eu.\* + 4 goldens anteriormente LINK_FAIL (47/48/49/51) agora PASS via Eu.1..Eu.4 (v5.26.1).

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
