# Mapanare Standard Library Reference

The standard library provides runtime support modules for common tasks. Import them with `import stdlib::module_name`.

---

## math — Numeric and Statistical Functions

**Constants:** `PI`, `E`, `TAU`, `INF`, `NAN`

| Function | Description |
|----------|-------------|
| `abs(x)` | Absolute value |
| `sqrt(x)` | Square root |
| `pow(base, exp)` | Power |
| `log(x, base?)` | Logarithm (natural if no base) |
| `log2(x)`, `log10(x)` | Base-2 and base-10 logarithm |
| `sin(x)`, `cos(x)`, `tan(x)` | Trigonometric functions |
| `asin(x)`, `acos(x)`, `atan(x)` | Inverse trig |
| `atan2(y, x)` | Two-argument arctangent |
| `degrees(rad)`, `radians(deg)` | Angle conversion |
| `floor(x)`, `ceil(x)` | Rounding |
| `round_to(x, decimals)` | Round to N decimal places |
| `clamp(x, lo, hi)` | Clamp to range |
| `lerp(a, b, t)` | Linear interpolation |
| `sum(values)` | Sum of sequence |
| `mean(values)` | Arithmetic mean |
| `median(values)` | Median value |
| `variance(values)` | Population variance |
| `stddev(values)` | Standard deviation |
| `min_val(values)`, `max_val(values)` | Min/max of sequence |
| `percentile(values, p)` | p-th percentile (0-100) |

```mn
import stdlib::math
let r = math::sqrt(16.0)    // 4.0
let avg = math::mean([1.0, 2.0, 3.0])  // 2.0
```

---

## text — String Manipulation

| Function | Description |
|----------|-------------|
| `to_upper(s)`, `to_lower(s)` | Case conversion |
| `capitalize(s)`, `title_case(s)` | Capitalize |
| `camel_case(s)`, `snake_case(s)`, `kebab_case(s)` | Case style conversion |
| `trim(s)`, `trim_start(s)`, `trim_end(s)` | Whitespace trimming |
| `pad_start(s, width, fill)`, `pad_end(s, width, fill)` | Padding |
| `contains(s, sub)` | Substring check |
| `starts_with(s, prefix)`, `ends_with(s, suffix)` | Prefix/suffix check |
| `index_of(s, sub)` | Find index (-1 if not found) |
| `replace(s, old, new)` | String replacement |
| `split(s, sep)` | Split by separator |
| `join(parts, sep)` | Join with separator |
| `lines(s)`, `words(s)` | Split into lines/words |
| `reverse(s)` | Reverse string |
| `repeat(s, n)` | Repeat n times |
| `slug(s)` | URL-friendly slug |
| `is_alpha(s)`, `is_digit(s)` | Character class checks |

```mn
import stdlib::text
let slug = text::slug("Hello World!")  // "hello-world"
let parts = text::split("a,b,c", ",")  // ["a", "b", "c"]
```

---

## time — Timers and Scheduling

| Item | Description |
|------|-------------|
| `TimerSignal(interval)` | Signal that ticks at fixed intervals |
| `Debounce(wait, callback)` | Fire after silence period |
| `Throttle(interval, callback)` | Fire at most once per interval |
| `Stopwatch()` | Monotonic timer with `start()`, `stop()`, `elapsed` |
| `interval(seconds, count?)` | Stream of ticks |
| `delay(seconds)` | Async sleep |

```mn
import stdlib::time
let sw = time::Stopwatch()
sw.start()
// ... work ...
let elapsed = sw.stop()
```

---

## io — File I/O

| Item | Description |
|------|-------------|
| `read_file(path)` | Read file contents (async) |
| `write_file(path, content, append?)` | Write to file (async) |
| `StdinAgent(prompt?)` | Agent that reads stdin lines |
| `StdoutAgent(end?, flush?)` | Agent that prints to stdout |
| `FileReaderAgent(line_mode?)` | Agent that reads files |
| `FileWriterAgent(path?, append?)` | Agent that writes files |

```mn
import stdlib::io
let content = io::read_file("data.txt")
io::write_file("out.txt", "hello")
```

---

## http — HTTP Client/Server

| Item | Description |
|------|-------------|
| `HttpRequest(method, url, headers?, body?)` | Request object |
| `HttpResponse(status, headers?, body?)` | Response object with `.ok`, `.json()` |
| `get(url, headers?, timeout?)` | HTTP GET (async) |
| `post(url, body?, headers?, timeout?)` | HTTP POST (async) |
| `HttpClientAgent(timeout?)` | Agent that sends HTTP requests |
| `HttpServerAgent(host?, port?, handler?)` | Agent that serves HTTP |

```mn
import stdlib::http
let resp = http::get("https://api.example.com/data")
let data = resp.json()
```

---

## log — Structured Logging

| Item | Description |
|------|-------------|
| `LogLevel` | TRACE, DEBUG, INFO, WARN, ERROR, FATAL |
| `Logger(name?, level?)` | Structured logger with agent context |
| `trace(msg)`, `debug(msg)`, `info(msg)` | Log at level |
| `warn(msg)`, `error(msg)`, `fatal(msg)` | Log at level |
| `set_level(level)` | Set default logger level |

```mn
import stdlib::log
log::info("server started", port: 8080)
let logger = log::Logger("myapp")
logger.warn("high latency", ms: 500)
```

---

## pkg — Package Management

| Item | Description |
|------|-------------|
| `init_project(dir, name?)` | Initialize project with `mapanare.toml` |
| `install_package(name, dir, git_url?, branch?)` | Install a package |
| `publish_package(dir, token?)` | Publish to registry |
| `search_packages(query?, keyword?)` | Search registry |
| `bump_version(dir, bump_type)` | Bump version (major/minor/patch) |
| `load_manifest(dir)` | Load `mapanare.toml` manifest |

```mn
// Used via CLI:
// mapanare init myproject
// mapanare install mypackage --git https://github.com/user/repo
// mapanare publish --patch
```
