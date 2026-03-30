<div align="center">

<img width="3200" height="1344" alt="MapanareDevTo" src="https://github.com/user-attachments/assets/99b80387-afd9-4b07-beb8-59a8f63f7ac7" />

# Mapanare

**/mah-pah-NAH-reh/**

**El lenguaje de programacion AI-nativo.**

*Agentes. Senales. Streams. Tensores. De primera clase, no frameworks.*

Mapanare compila a Python (transpilador) y binarios nativos (LLVM), con un compilador auto-hospedado en desarrollo.

[English](../README.md) | Espanol | [中文版](README.zh-CN.md) | [Portugues](README.pt.md)

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-Backend_Nativo-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![Plataforma](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![Licencia](https://img.shields.io/badge/licencia-MIT-green.svg?style=flat-square)](../LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg?style=flat-square)](../CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-2090_pasando_(82_archivos)-brightgreen.svg?style=flat-square)]()
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**Primeros Pasos**](getting-started.md) · [Por que Mapanare?](#por-que-mapanare) · [Instalar](#instalar) · [El Lenguaje](#el-lenguaje) · [Benchmarks](#benchmarks) · [CLI](#cli) · [Arquitectura](#arquitectura-del-compilador) · [Hoja de Ruta](roadmap/ROADMAP.md) · [Contribuir](#contribuir) · [Discord](https://discord.gg/5hpGBm3WXf)

</div>

---

## Por que Mapanare?

Todos los lenguajes principales tratan agentes, senales, streams y tensores como construcciones de biblioteca — una capa de abstraccion lejos del compilador. Eso significa sin verificacion de flujo de datos en tiempo de compilacion, sin chequeo estatico de formas de tensores, y sin garantias a nivel de lenguaje sobre paso de mensajes.

Mapanare hace que estas primitivas sean **parte del lenguaje**:

- **Agentes** son tan naturales como funciones — declarar, crear, enviar, recibir, todo con sintaxis dedicada verificada por el compilador
- **Senales** reemplazan el callback hell con seguimiento automatico de dependencias
- **Streams** se componen con `|>` de la forma en que piensas sobre datos, con fusion de operadores integrada
- **Tensores** obtienen validacion de formas en tiempo de compilacion — errores de forma detectados antes de la ejecucion
- **Sin POO** — structs, enums y pattern matching en lugar de jerarquias de clases

Lee el [manifiesto](manifesto.md) completo.

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

### Descarga Manual

Descarga el ultimo binario desde [Releases](https://github.com/Mapanare-Research/Mapanare/releases).

| Plataforma | Archivo |
|------------|---------|
| Linux (x64) | `mapanare-linux-x64.tar.gz` |
| macOS (Apple Silicon) | `mapanare-mac-arm64.tar.gz` |
| Windows (x64) | `mapanare-win-x64.zip` |

Extrae y agrega `mapanare` a tu PATH, luego verifica:

```bash
mapanare --version
```

---

## El Lenguaje

### Basicos

```mn
fn main() {
    let name = "Mundo"
    print("Hola, " + name + "!")

    let mut count = 0
    while count < 5 {
        print(str(count))
        count += 1
    }

    for i in 0..5 {
        print(str(i))
    }
}
```

### Structs, Enums y Pattern Matching

Sin clases, sin herencia. Structs, enums y pattern matching en su lugar.

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

### Manejo de Errores

```mn
fn dividir(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("division por cero")
    }
    return Ok(a / b)
}

let valor = dividir(10.0, 3.0)?
```

### Agentes (Experimental)

Actores concurrentes con canales tipados.

```mn
agent Saludador {
    input nombre: String
    output saludo: String

    fn handle(nombre: String) -> String {
        return "Hola, " + nombre + "!"
    }
}

let saludador = spawn Saludador()
saludador.nombre <- "Mundo"
let resultado = sync saludador.saludo
print(resultado)
```

### Senales (Experimental)

Estado reactivo con seguimiento automatico de dependencias.

```mn
let mut count = signal(0)
let doubled = signal { count * 2 }
```

### Streams (Experimental)

Pipelines asincronos con el operador `|>`.

```mn
let datos = stream([1, 2, 3, 4, 5])
let resultado = datos
    |> filter(fn(x) { x > 2 })
    |> map(fn(x) { x * 10 })
```

---

## CLI

```
mapanare run <archivo>       Compilar y ejecutar
mapanare build <archivo>     Compilar a binario nativo via LLVM
mapanare jit <archivo>       Compilar JIT y ejecutar nativamente
mapanare check <archivo>     Solo verificar tipos
mapanare compile <archivo>   Transpilar a Python
mapanare emit-llvm <archivo> Emitir LLVM IR
mapanare repl                Iniciar REPL interactivo
mapanare fmt <archivo>       Formatear codigo fuente
mapanare init [ruta]         Inicializar un nuevo proyecto
mapanare install <paq>       Instalar un paquete (basado en git)
mapanare targets             Listar objetivos de compilacion soportados
```

---

## Arquitectura del Compilador

```
fuente .mn → Lexer → Parser → AST → Analisis Semantico → Optimizador → Emision
                                                                          ↓
                                                                   Python | LLVM IR
                                                                          ↓
                                                           Interprete | Binario Nativo
```

---

## Hoja de Ruta

| Version | Tema | Estado |
|---------|------|--------|
| **v0.1.0** | Fundacion — compilador bootstrap, backends duales, runtime, LSP, stdlib | Lanzado |
| **v0.2.0** | Auto-Hospedaje — codegen LLVM, runtime C, compilador auto-hospedado (5,800 lineas .mn) | Lanzado |
| **v0.3.0** | Profundidad sobre Amplitud — traits, modulos, codegen de agentes, memoria arena, 1,960+ tests | Lanzado |
| **v0.4.0** | Listo para el Mundo — FFI, endurecimiento runtime C, diagnosticos, limpieza de alcance | Siguiente |
| **v0.5.0** | El Ecosistema — registro de paquetes, playground WASM, linter | Planeado |
| **v1.0.0** | Estable — spec del lenguaje congelado, garantias de compatibilidad | Planeado |

Ve la [hoja de ruta](roadmap/ROADMAP.md) completa para detalles.

---

## Contribuir

Ve [CONTRIBUTING.md](../CONTRIBUTING.md). Los estandares de la comunidad y procesos del proyecto viven en [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md), [GOVERNANCE.md](../GOVERNANCE.md), y [SECURITY.md](../SECURITY.md). Cambios al lenguaje requieren un [RFC](rfcs/).

---

## Licencia

Licencia MIT — ve [LICENSE](../LICENSE) para detalles.

---

<div align="center">

**Mapanare** — El lenguaje que la IA merece.

[Reportar Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [Solicitar Feature](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [Spec](SPEC.md) · [Changelog](../CHANGELOG.md) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

Hecho con cuidado por [Juan Denis](https://juandenis.com)

</div>
