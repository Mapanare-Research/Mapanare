<div align="center">

<img width="1280" height="640" alt="mapanare-repo" src="https://github.com/user-attachments/assets/176d26e7-0c42-49ef-99d2-b8192cd75e53" />

# Mapanare

**/mah-pah-NAH-reh/**

**El lenguaje de programacion AI-nativo.**

*Agentes. Senales. Streams. Tensores. De primera clase, no frameworks.*

Compila a binarios nativos via LLVM y WebAssembly.
**~168x mas rapido que Python. A la par con Rust y C.**

[English](../README.md) | Espanol | [中文版](README.zh-CN.md) | [Portugues](README.pt.md)

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-Backend_Nativo-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![WebAssembly](https://img.shields.io/badge/WebAssembly-Backend-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)
![Plataforma](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![Licencia](https://img.shields.io/badge/licencia-MIT-green.svg?style=flat-square)](../LICENSE)
[![Version](https://img.shields.io/badge/version-5.47.5-blue.svg?style=flat-square)](../CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-5800+_pasando-brightgreen.svg?style=flat-square)]()
[![Goldens](https://img.shields.io/badge/goldens-103%2F103-brightgreen.svg?style=flat-square)]()
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**Sitio Web**](https://mapanare.dev) · [**Documentacion**](https://mapanare.dev/docs) · [**Descargas**](https://mapanare.dev/download) · [**Discord**](https://discord.gg/5hpGBm3WXf)

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

O descarga binarios desde [Releases](https://github.com/Mapanare-Research/Mapanare/releases).

---

## Hola Mundo

```mn
fn main() {
    print("hola desde mapanare")
}
```

```bash
mapanare run hola.mn        # compilar + ejecutar
mapanare build hola.mn      # producir un binario nativo
```

---

## Escribe Python, Compila Nativo

Toma tus scripts Python existentes y compilalos a binarios nativos:

```bash
mapanare build tu_script.py -o tu_script
./tu_script   # 33-239x mas rapido
```

[Guia Python a Nativo](https://mapanare.dev/docs/guides/python-to-native)

---

## Caracteristicas del Lenguaje

```mn
// Agentes — actores concurrentes de primera clase
agent Contador {
    state count: Int = 0
    on incrementar { count = count + 1 }
    on obtener_cuenta -> Int { return count }
}

// Senales — estado reactivo
let temperatura = signal(72.0)
let alerta = computed(() => temperatura.get() > 100.0)

// Streams — pipelines de datos componibles
let resultados = data_stream
    |> filter((x) => x > 0)
    |> map((x) => x * 2)
    |> collect()

// Pattern matching
match respuesta {
    Ok(datos) => procesar(datos),
    Err(e) => print(e)
}

// AI stdlib
import ai::llm
let respuesta = ask(ollama("llama3.2"), "Que es Mapanare?")
```

Referencia completa, tutoriales y recetario en [mapanare.dev/docs](https://mapanare.dev/docs).

### Compilador nativo — lo que envia `mnc-stage1`

El compilador auto-hospedado corre el corpus completo de v5.47.0 (103/103 goldens nativos):

- **Tensores** — literales, indexacion multi-dim, broadcasting estilo NumPy, slicing, reducciones (sum / mean / max / min / argmax / argmin).
- **Async / await / `block_on`** — corrutinas LLVM reales (`presplitcoroutine` + `@llvm.coro.id/begin/save/suspend/end`) con suspension dirigida por el scheduler.
- **Parametros tipo cierre** — `fn apply(f: fn(Int) -> Int, x: Int)` lowereado a traves de SSA de llamada indirecta.
- **Pattern matching con or-patterns y guards** — `Plus | Minus if cond => body` sobre variantes enum y constructores incorporados (`None` / `Some` / `Ok` / `Err`).
- **Drop-glue para ownership** — lifetimes de string / list / boxed / tensor rastreados en rutas de retorno y bucles; valgrind / ASan / LSan / TSan todos limpios en el corpus.
- **Sintaxis terse (arco v5.13–v5.21)** — bloques con dos puntos (Te.1), comprensiones de listas/mapas y lambdas terse (Te.2), interpolacion de strings auto-hospedada (Te.4), ergonomia de structs (Te.5: shorthand de campos, `..base`, destructuring, if-let / while-let / let-else), comparaciones encadenadas (Te.6: `0 < x < 10`).

Punto fijo auto-hospedado de 3 etapas: STRICT (stage2.ll == stage3.ll byte-identical en 241,842 lineas; restaurado v5.9.0; mantenido a traves de la reescritura mecanica de llaves a dos puntos en v5.17.0, la ergonomia de structs en v5.20.0, las comparaciones encadenadas en v5.21.0, la recuperacion CI en v5.23.0, el espejo bootstrap de deprecacion de llaves en v5.23.2, las puertas Hy.\* de higiene en v5.24.0, la infraestructura Pv.\* de prevencion en v5.25.0, las correcciones de codegen Mb.7 + Win64 ABI Mb.9 en v5.26.0, los cierres Eu.\* de payload de enum en v5.26.1, y el cierre del arco Mc.\* en v5.27.0 — racha mas larga en la historia del proyecto: 23 lanzamientos consecutivos). Compilador auto-hospedado encogio **-2,285 lineas (-8.18%)** neto de v5.13.0 → v5.21.1 via la reescritura Sh.\* sin romper el punto fijo.

Arco de recuperacion + prevencion v5.23–v5.27: 8 lanzamientos cerrando los 4 HIGH + 8 MEDIUM del docket panel v5.22.0 + cerrando los arcos Mb.\* / Mc.\* / Eu.\* + 4 goldens previamente LINK_FAIL (47/48/49/51) ahora PASS via Eu.1..Eu.4 (v5.26.1).

---

## Contribuir

Ve [CONTRIBUTING.md](../CONTRIBUTING.md). Cambios al lenguaje requieren un [RFC](rfcs/).

## Licencia

Licencia MIT — ve [LICENSE](../LICENSE).

---

<div align="center">

**Mapanare** — El lenguaje que la IA merece.

[Reportar Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [Solicitar Feature](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

Hecho con cuidado por [Juan Denis](https://juandenis.com)

</div>
