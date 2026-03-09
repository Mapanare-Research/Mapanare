# RFC 0001: Agent Syntax

- **Status:** Draft
- **Author:** Mapanare Core Team
- **Created:** 2026-03-08

---

## Summary

This RFC defines the syntax and semantics for agents -- the primary concurrency primitive in Mapanare. Agents are concurrent actors with typed input/output channels, private state, lifecycle hooks, and structured supervision.

---

## Motivation

Modern AI workloads are inherently concurrent: models serve requests, data streams flow between processing stages, and multiple subsystems coordinate in parallel. Existing languages force developers to bolt concurrency onto sequential code using threads, locks, async/await, or external actor frameworks.

Mapanare makes agents a first-class language construct so that:

1. **Concurrency is the default, not an afterthought.** Defining an agent is as natural as defining a function.
2. **Communication is typed and safe.** Input and output channels carry known types, eliminating runtime serialization errors.
3. **Lifecycle management is built in.** Agents have defined states (init, running, paused, stopped) with hooks, removing the need for manual resource management.
4. **Supervision is declarative.** Restart policies are annotations, not error-handling boilerplate.

---

## Detailed Design

### Agent Declaration

An agent is declared with the `agent` keyword followed by a name and a block containing channel declarations, state, and handler functions.

```mn
agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "Hello, " + name + "!"
    }
}
```

**Grammar (EBNF sketch):**

```ebnf
agent_def    = ["pub"] "agent" IDENT "{" { agent_member } "}" ;
agent_member = input_decl | output_decl | let_binding | fn_def ;
input_decl   = "input" IDENT ":" type ;
output_decl  = "output" IDENT ":" type ;
```

### Input and Output Channels

Each agent declares zero or more `input` and `output` channels. Channels are typed, bounded, and FIFO-ordered.

```mn
agent Processor {
    input data: List<Float>
    input config: Config
    output result: Tensor<Float>[128]
    output status: String
}
```

- An agent with zero inputs can be spawned and will run its `on_init` hook immediately.
- An agent with zero outputs is a sink (e.g., a logger or writer).
- Channel types must be concrete (no unresolved generics).

### Private State

Agents can hold private mutable state using `let mut` bindings. State is never shared between agents.

```mn
agent Counter {
    input increment: Int
    output count: Int

    let mut state: Int = 0

    fn handle(increment: Int) -> Int {
        self.state += increment
        return self.state
    }
}
```

State is accessible only within the agent's methods via `self`.

### Handler Function

The `handle` function is invoked each time a message arrives on an input channel. Its parameter type must match the input channel type, and its return type must match the output channel type.

For agents with multiple inputs, overloaded `handle` functions disambiguate by parameter type:

```mn
agent MultiInput {
    input text: String
    input number: Int
    output result: String

    fn handle(text: String) -> String {
        return "text: " + text
    }

    fn handle(number: Int) -> String {
        return "number: " + number.to_string()
    }
}
```

### Lifecycle Hooks

Agents support optional lifecycle hooks:

| Hook | When Called |
|------|------------|
| `on_init()` | After the agent is created, before processing messages. |
| `on_stop()` | When the agent is stopped, after all pending messages are drained. |

```mn
agent ResourceHolder {
    input request: String
    output response: String

    let mut db: Option<Connection> = none

    fn on_init() {
        self.db = Some(Database::connect("localhost"))
    }

    fn on_stop() {
        match self.db {
            Some(conn) => conn.close(),
            None => {},
        }
    }

    fn handle(request: String) -> String {
        // use self.db
        return "ok"
    }
}
```

### Spawning

Agents are instantiated and started with the `spawn` keyword. `spawn` returns a handle to the running agent.

```mn
let greeter = spawn Greeter()
```

The handle exposes the agent's input and output channels:

```mn
greeter.name <- "World"            // send to input
let result = sync greeter.greeting  // receive from output
```

### Communication Operators

| Operator | Meaning |
|----------|---------|
| `<-` | Send a value to an agent's input channel (non-blocking, queued). |
| `sync` | Block until an output value is available. Returns the value. |

### Supervision via Decorators

Restart policies are specified as decorators on `spawn`:

```mn
let worker = spawn MyAgent() @restart(policy: "always", max: 3, window: 60)
```

| Policy | Behavior |
|--------|----------|
| `always` | Restart on any failure, up to `max` times in `window` seconds. |
| `never` | Let the agent stay stopped on failure. |
| `transient` | Restart only on unexpected failures. |

### Pipes and Agent Composition

The `pipe` keyword composes agents into named pipelines using `|>`:

```mn
pipe ClassifyText {
    Tokenizer |> Classifier
}

let pipeline = spawn ClassifyText()
pipeline.text <- "hello world"
let label = sync pipeline.label
```

In a pipe, the output type of agent N must match the input type of agent N+1. The pipe's input is the first agent's input; the pipe's output is the last agent's output.

---

## Alternatives Considered

### 1. Async/Await Instead of Agents

Using `async fn` and `await` (like Rust, JavaScript, Python) was considered. This was rejected because:

- Async/await models a single control flow with suspension points, not independent concurrent entities.
- It lacks built-in typed channels, lifecycle management, and supervision.
- The pipe composition model (`|>` over agents) does not map naturally to async/await.

### 2. Class-Based Actors

Defining agents as classes with `extends Actor` (like Akka in Scala/Java) was considered. This was rejected because:

- It introduces OOP class hierarchies, which Mapanare explicitly avoids.
- The `input`/`output` channel syntax is more declarative and type-safe than method overriding.
- Lifecycle hooks as named functions (`on_init`, `on_stop`) are simpler than overriding abstract methods.

### 3. Go-Style Goroutines and Channels

Using lightweight goroutines with separate `chan` declarations was considered. This was rejected because:

- Channels in Go are separate from the function/goroutine definition, making it harder to see an actor's interface at a glance.
- No built-in lifecycle, supervision, or backpressure.
- Mapanare's `agent` block groups everything (channels, state, handlers) into a single coherent definition.

### 4. CSP (Communicating Sequential Processes)

A pure CSP model (like Occam or Hoare's original formulation) was considered. While Mapanare's agents are inspired by CSP, the full model was too low-level:

- CSP lacks the concept of named, typed channel groups (input/output blocks).
- No lifecycle or supervision primitives.
- Mapanare adds the `pipe` composition abstraction on top of the CSP core.

---

## Unresolved Questions

1. **Generic agents.** Should agents support type parameters (e.g., `agent Transform<T, U>`)? This is deferred to a future RFC.
2. **Agent groups.** The syntax for spawning N instances of the same agent type (fan-out) needs design. Placeholder: `spawn MyAgent[4]()`.
3. **Backpressure configuration.** How to specify buffer size and overflow strategy per-channel is not yet settled. Placeholder: `input data: String @buffer(100, "drop_oldest")`.
4. **Agent-to-agent direct wiring.** Whether agents can be wired point-to-point outside of `pipe` declarations.

---

## References

- [Mapanare Language Specification (SPEC.md)](../SPEC.md) -- Sections 7 (Agent Model), 3 (Keywords), 4 (Operators)
- Hewitt, C. et al. "A Universal Modular ACTOR Formalism for Artificial Intelligence" (1973)
- Armstrong, J. "Making Reliable Distributed Systems in the Presence of Software Errors" (Erlang thesis, 2003)
- Hoare, C.A.R. "Communicating Sequential Processes" (1978)
