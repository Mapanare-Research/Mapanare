"""Mapanare Language Website — Built with Cacao"""
import cacao as c

c.config(title="Mapanare — AI-Native Programming Language", theme="dark")


# ──────────────────────────────────────────────
# HOME PAGE
# ──────────────────────────────────────────────
with c.page("/"):
    # Hero
    with c.hero(
        title="The AI-Native Programming Language",
        subtitle=(
            "Agents, signals, streams, and tensors are first-class primitives — not libraries. "
            "Built for the era where AI writes and runs the code."
        ),
        height="520px",
        align="center",
    ):
        with c.row(gap=3, justify="center"):
            c.button("Get Started", on_click="nav:/docs", variant="primary", icon="rocket")
            c.button(
                "GitHub",
                on_click="open:https://github.com/Mapanare-Research/mapanare",
                variant="secondary",
                icon="github",
            )

    c.spacer(2)

    # Hero code sample
    with c.container(size="lg"):
        with c.card("Hello, Mapanare"):
            c.code(
                """agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}

fn main() {
    let greeter = spawn Greeter()
    greeter.name <- "World"
    let result = sync greeter.greeting
    print(result)  // "Hello, World!"
}""",
                language="rust",
                line_numbers=True,
            )

    c.spacer(4)

    # Features
    with c.container(size="lg"):
        c.title("Everything AI needs, built in", level=2)
        c.text(
            "No frameworks, no glue code. Mapanare compiles agents, signals, and tensors directly to native machine code.",
            color="muted",
        )
        c.spacer(2)

        with c.grid(cols=3, gap=4):
            with c.card("Agents"):
                c.badge("concurrency", color="primary")
                c.spacer(1)
                c.text(
                    "Concurrent actors with typed message channels. Spawn, supervise, and scale — no raw threads.",
                    size="sm",
                )
                c.code("spawn Agent()  // <- sync", language="rust")

            with c.card("Signals"):
                c.badge("reactive", color="primary")
                c.spacer(1)
                c.text(
                    "Reactive state that propagates changes automatically. Computed values recompute when dependencies change.",
                    size="sm",
                )
                c.code("let total = signal { price.value * 1.08 }", language="rust")

            with c.card("Streams"):
                c.badge("async", color="primary")
                c.spacer(1)
                c.text(
                    "Async data pipelines with backpressure, fusion, and hot/cold semantics.",
                    size="sm",
                )
                c.code("data |> filter(fn(x) => x > 0) |> map(fn(x) => x * x)", language="rust")

            with c.card("Tensors"):
                c.badge("@gpu", color="success")
                c.spacer(1)
                c.text(
                    "N-dimensional arrays with compile-time shape validation. GPU-accelerated via CUDA, Metal, or Vulkan.",
                    size="sm",
                )
                c.code("Tensor<Float>[M, N]  // shape-checked at compile time", language="rust")

            with c.card("Pipes"):
                c.badge("|> operator", color="primary")
                c.spacer(1)
                c.text(
                    "Compose agents and functions with the pipe operator. Build data-processing graphs declaratively.",
                    size="sm",
                )
                c.code("pipe NLP { Tokenizer |> Embedder |> Classifier }", language="rust")

            with c.card("Native Compilation"):
                c.badge("LLVM", color="warning")
                c.spacer(1)
                c.text(
                    "LLVM backend compiles to native x86_64 and ARM. No Python at runtime. 10x faster than asyncio.",
                    size="sm",
                )
                c.code("mapa compile app.mn -o app --target native", language="bash")

    c.spacer(4)

    # Code Examples
    with c.container(size="lg"):
        c.title("See it in action", level=2)
        c.text(
            "Familiar syntax drawn from Rust, TypeScript, and Python — with AI primitives you won't find anywhere else.",
            color="muted",
        )
        c.spacer(2)

        with c.tabs():
            with c.tab("pipeline", "AI Pipeline", icon="robot"):
                c.code(
                    """pipe SentimentPipeline {
    Tokenizer |> Embedder |> Classifier
}

fn main() {
    let pipeline = spawn SentimentPipeline()
    pipeline.input <- "Mapanare is amazing!"
    let result = sync pipeline.output
    print(result)  // { label: "positive", score: 0.97 }
}""",
                    language="rust",
                    line_numbers=True,
                )

            with c.tab("gpu", "GPU Tensors", icon="cpu"):
                c.code(
                    """@gpu
fn matrix_multiply(
    a: Tensor<Float>[M, K],
    b: Tensor<Float>[K, N]
) -> Tensor<Float>[M, N] {
    return a @ b  // dispatched to CUDA/Metal/Vulkan
}

fn main() {
    let weights = Tensor.load("model.mnw")
    let input = Tensor.zeros([128, 768])
    let output = matrix_multiply(input, weights)
    print(output.shape)  // [128, 512]
}""",
                    language="rust",
                    line_numbers=True,
                )

            with c.tab("reactive", "Reactive Signals", icon="zap"):
                c.code(
                    """fn main() {
    let temperature = signal(72.0)
    let celsius = signal { (temperature.value - 32.0) * 5.0 / 9.0 }

    let readings = Stream.from(sensor)
        |> filter(fn(r) => r.valid)
        |> map(fn(r) => r.value)
        |> chunk(10)

    for batch in readings {
        temperature.set(mean(batch))
        print("Celsius: " + str(celsius.value))  // auto-recomputed
    }
}""",
                    language="rust",
                    line_numbers=True,
                )

    c.spacer(4)

    # Roadmap
    with c.container(size="lg"):
        c.title("Roadmap", level=2)
        c.text(
            "Mapanare is built in the open. Phases 2–5 complete, self-hosting compiler underway.",
            color="muted",
        )
        c.spacer(2)

        with c.steps(direction="vertical"):
            c.step(
                "Foundation",
                description="Repository, CI/CD, spec, community",
                status="active",
                icon="folder",
            )
            c.step(
                "Transpiler",
                description="Mapanare → Python. Lexer, parser, AST, semantic checker, emitter",
                status="complete",
                icon="code",
            )
            c.step(
                "Runtime",
                description="Agent scheduler, signal graph, stream engine, stdlib",
                status="complete",
                icon="play",
            )
            c.step(
                "LLVM Backend",
                description="Native compilation, optimization passes, cross-compilation",
                status="complete",
                icon="cpu",
            )
            c.step(
                "Tensor & GPU",
                description="CUDA, Metal, Vulkan. Model loading, compile-time shapes",
                status="complete",
                icon="box",
            )
            c.step(
                "Self-Hosting",
                description="Compiler rewritten in Mapanare. Bootstrap complete.",
                status="active",
                icon="repeat",
            )
            c.step(
                "Ecosystem",
                description="LSP, VSCode extension, package registry, playground",
                status="pending",
                icon="package",
            )

    c.spacer(4)

    # Quick Start
    with c.container(size="lg"):
        c.title("Get started in seconds", level=2)
        c.spacer(1)

        with c.row(gap=4):
            with c.col(span=6):
                c.code(
                    """# Clone the repository
git clone https://github.com/Mapanare-Research/mapanare.git
cd mapanare

# Install
make install

# Run your first program
mapa run examples/hello.mn""",
                    language="bash",
                )

            with c.col(span=6):
                c.code(
                    """$ mapa run hello.mn
Hello, World!

$ mapa compile app.mn -o app
  Compiling app.mn → LLVM IR
  Optimizing (O2)
  Built: ./app (x86_64-linux-gnu)

$ mapa check pipeline.mn
  No errors found.""",
                    language="bash",
                )

    c.spacer(4)

    # Footer CTA
    with c.container(size="md", center=True):
        c.divider()
        c.spacer(2)
        c.title("Ready to build with Mapanare?", level=2)
        c.text(
            "Join a growing community of developers building AI-native applications.", color="muted"
        )
        c.spacer(1)
        with c.row(gap=2, justify="center"):
            c.button(
                "View on GitHub",
                on_click="open:https://github.com/Mapanare-Research/mapanare",
                variant="primary",
                icon="github",
            )
            c.button("Read the Docs", on_click="nav:/docs", variant="secondary", icon="book")
            c.button(
                "Join Discord",
                on_click="open:https://discord.gg/mapanare",
                variant="secondary",
                icon="message-circle",
            )


# ──────────────────────────────────────────────
# DOCS PAGE
# ──────────────────────────────────────────────
with c.page("/docs"):
    with c.container(size="lg"):
        c.title("Documentation", level=1)
        c.text(
            "Learn how to build AI-native applications with first-class agents, signals, streams, and tensors.",
            color="muted",
        )
        c.spacer(2)

        with c.grid(cols=2, gap=3):
            c.link_card(
                "Getting Started",
                description="Install Mapanare, write your first program, and learn the basics.",
                href="#/getting-started",
                icon="rocket",
            )
            c.link_card(
                "Agents Guide",
                description="Concurrent actors with typed channels, supervision, and backpressure.",
                href="#/getting-started",
                icon="users",
            )
            c.link_card(
                "Reactive Signals",
                description="Automatic change propagation, computed values, and the signal graph.",
                href="#/getting-started",
                icon="zap",
            )
            c.link_card(
                "Tensors & GPU",
                description="Compile-time shape validation. @gpu for CUDA, Metal, and Vulkan.",
                href="#/getting-started",
                icon="box",
            )
            c.link_card(
                "Language Specification",
                description="The complete formal specification — types, syntax, semantics.",
                href="https://github.com/Mapanare-Research/mapanare/blob/main/SPEC.md",
                icon="file-text",
            )
            c.link_card(
                "Roadmap",
                description="See what's been built, what's in progress, and what's next.",
                href="https://github.com/Mapanare-Research/mapanare/blob/main/ROADMAP.md",
                icon="map",
            )

        c.spacer(3)
        c.divider()
        c.spacer(2)

        # Quick Reference
        c.title("Quick Reference", level=3)
        c.spacer(1)

        c.table(
            [
                {
                    "Primitive": "agent",
                    "Description": "Concurrent actor with typed input/output channels and lifecycle hooks",
                },
                {
                    "Primitive": "signal(value)",
                    "Description": "Reactive container — dependents recompute automatically on change",
                },
                {
                    "Primitive": "stream",
                    "Description": "Async iterable with backpressure, fusion, and hot/cold semantics",
                },
                {
                    "Primitive": "pipe",
                    "Description": "Named composition of agents into a data-processing pipeline",
                },
                {
                    "Primitive": "Tensor<T>[shape]",
                    "Description": "N-dimensional array with compile-time shape validation",
                },
                {"Primitive": "spawn", "Description": "Launch an agent as a concurrent task"},
                {"Primitive": "sync", "Description": "Await a value from an agent output channel"},
                {
                    "Primitive": "|>",
                    "Description": "Pipe operator — chain function and agent transformations",
                },
                {"Primitive": "<-", "Description": "Send a message to an agent's input channel"},
                {
                    "Primitive": "@gpu / @cpu",
                    "Description": "Target a function to GPU or CPU execution",
                },
            ],
            columns=["Primitive", "Description"],
            sortable=False,
            paginate=False,
        )


# ──────────────────────────────────────────────
# GETTING STARTED PAGE
# ──────────────────────────────────────────────
with c.page("/getting-started"):
    with c.container(size="lg"):
        c.breadcrumb(
            [
                {"label": "Docs", "href": "#/docs"},
                {"label": "Getting Started"},
            ]
        )
        c.spacer(1)

        c.title("Getting Started", level=1)
        c.text(
            "Install Mapanare, write your first program, and learn the core concepts.",
            color="muted",
        )
        c.spacer(2)

        # Installation
        c.title("Installation", level=2)
        c.text(
            "Mapanare requires Python 3.11+ for the bootstrap compiler. The native LLVM backend requires LLVM 15+."
        )
        c.spacer(1)

        c.code(
            """# Clone the repository
git clone https://github.com/Mapanare-Research/mapanare.git
cd mapanare

# Install (creates the `mapa` command)
make install

# Verify installation
mapa --version""",
            language="bash",
        )

        c.alert(
            "On macOS/Linux, `make install` creates a virtual environment and installs Mapanare as an editable package. "
            'On Windows, use `pip install -e ".[dev]"` directly.',
            type="info",
            title="Platform Note",
        )

        c.spacer(2)

        # Hello World
        c.title("Hello World", level=2)
        c.text("Create a file called hello.mn:")
        c.spacer(1)

        c.code(
            """fn main() {
    print("Hello, Mapanare!")
}""",
            language="rust",
            line_numbers=True,
        )

        c.text("Run it:")
        c.code("$ mapa run hello.mn\nHello, Mapanare!", language="bash")

        c.spacer(2)

        # Agents
        c.title("Agents", level=2)
        c.text(
            "Agents are concurrent actors that communicate through typed message channels. "
            "They are the core concurrency primitive — no raw threads, no shared mutable state."
        )
        c.spacer(1)

        c.code(
            """agent Echo {
    input message: String
    output reply: String

    fn handle(message: String) -> String {
        return "Echo: " + message
    }
}

fn main() {
    let echo = spawn Echo()       // launch the agent
    echo.message <- "hello"       // send a message
    let result = sync echo.reply  // await the response
    print(result)                 // "Echo: hello"
}""",
            language="rust",
            line_numbers=True,
        )

        c.spacer(2)

        # Signals
        c.title("Signals", level=2)
        c.text(
            "Signals are reactive state containers. When a signal's value changes, all dependent computations are automatically re-evaluated."
        )
        c.spacer(1)

        c.code(
            """fn main() {
    let price = signal(100.0)
    let tax_rate = signal(0.08)

    // Computed signal — auto-recomputes
    let total = signal { price.value * (1.0 + tax_rate.value) }

    print(total.value)   // 108.0

    price.set(200.0)
    print(total.value)   // 216.0 (auto-recomputed)
}""",
            language="rust",
            line_numbers=True,
        )

        c.spacer(2)

        # Streams
        c.title("Streams", level=2)
        c.text("Streams are async iterables with built-in backpressure and operator fusion.")
        c.spacer(1)

        c.code(
            """fn main() {
    let data = Stream.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    let result = data
        |> filter(fn(x) => x % 2 == 0)   // even numbers
        |> map(fn(x) => x * x)           // square them
        |> take(3)                        // first 3
        |> collect()                      // [4, 16, 36]

    print(result)
}""",
            language="rust",
            line_numbers=True,
        )

        c.spacer(2)

        # Tensors
        c.title("Tensors & GPU", level=2)
        c.text(
            "Tensors are N-dimensional arrays with compile-time shape validation. Use @gpu to dispatch to CUDA, Metal, or Vulkan."
        )
        c.spacer(1)

        c.code(
            """@gpu
fn forward(
    input: Tensor<Float>[128, 768],
    weights: Tensor<Float>[768, 512]
) -> Tensor<Float>[128, 512] {
    return input @ weights  // matrix multiply on GPU
}""",
            language="rust",
            line_numbers=True,
        )

        c.alert(
            "The compiler verifies tensor shapes at compile time. A shape mismatch is a compile error, not a runtime crash.",
            type="success",
            title="Compile-Time Safety",
        )

        c.spacer(2)

        # CLI
        c.title("CLI Reference", level=2)
        c.spacer(1)

        c.table(
            [
                {"Command": "mapa run <file>", "Description": "Compile and run a .mn file"},
                {
                    "Command": "mapa compile <file>",
                    "Description": "Compile to Python or native binary",
                },
                {"Command": "mapa check <file>", "Description": "Type-check without compiling"},
                {"Command": "mapa fmt <file|dir>", "Description": "Format source code"},
                {"Command": "mapa init", "Description": "Create a new Mapanare project"},
                {"Command": "mapa install <pkg>", "Description": "Install a package"},
                {"Command": "mapa --version", "Description": "Show version"},
            ],
            columns=["Command", "Description"],
            sortable=False,
            paginate=False,
        )

        c.spacer(1)
        c.title("Optimization Levels", level=3)
        c.table(
            [
                {"Flag": "-O0", "Level": "No optimization (fastest compile)"},
                {"Flag": "-O1", "Level": "Constant folding and propagation"},
                {"Flag": "-O2", "Level": "+ Dead code elimination + agent inlining"},
                {"Flag": "-O3", "Level": "+ Stream fusion (maximum optimization)"},
            ],
            columns=["Flag", "Level"],
            sortable=False,
            paginate=False,
        )

        c.spacer(2)

        # Type System
        c.title("Type System", level=2)
        c.text(
            "Mapanare has a static type system with inference. You write types where they clarify; the compiler infers the rest."
        )
        c.spacer(1)

        c.table(
            [
                {"Type": "Int", "Description": "64-bit signed integer"},
                {"Type": "Float", "Description": "64-bit IEEE 754 floating-point"},
                {"Type": "Bool", "Description": "true or false"},
                {"Type": "String", "Description": "Immutable UTF-8 encoded string"},
                {"Type": "Option<T>", "Description": "Some(value) or None — no null pointers"},
                {
                    "Type": "Result<T, E>",
                    "Description": "Ok(value) or Err(error) — recoverable errors",
                },
                {"Type": "List<T>", "Description": "Dynamic ordered collection"},
                {"Type": "Map<K, V>", "Description": "Hash map"},
                {
                    "Type": "Tensor<T>[shape]",
                    "Description": "N-dimensional array with shape validation",
                },
                {"Type": "Signal<T>", "Description": "Reactive state container"},
                {"Type": "Stream<T>", "Description": "Async iterable with backpressure"},
                {"Type": "Channel<T>", "Description": "Typed inter-agent message channel"},
            ],
            columns=["Type", "Description"],
            sortable=False,
            paginate=False,
        )
