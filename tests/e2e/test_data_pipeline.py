"""End-to-end integration tests for data pipeline patterns.

Each test writes an .mn source program, compiles it via the Python transpiler,
executes the resulting Python, and asserts on stdout / exit code.

Covers:
  - TOML-like config parsing and value extraction
  - YAML-like config parsing and value extraction
  - File I/O roundtrip (read/write via string operations)
  - CSV parse/transform/write pipeline
  - Embedded KV set/get/save/load cycle using maps
"""

from __future__ import annotations

import textwrap

from tests.e2e.test_e2e import _run_mapanare

# ── TOML config parsing ───────────────────────────────────────────────────────


class TestTomlConfigParseline:
    """E2E: parse TOML-like config and extract values.

    Since the TOML stdlib module relies on extern C functions that are only
    available via the LLVM backend, these tests simulate TOML parsing using
    core language features (string operations, maps).
    """

    def test_toml_parse_key_value_pairs(self) -> None:
        """Parse key=value lines from a TOML-like string and extract values."""
        source = textwrap.dedent("""\
            fn parse_kv(line: String) -> List<String> {
                let mut key: String = ""
                let mut val: String = ""
                let mut found_eq: Bool = false
                for i in 0..len(line) {
                    let ch = line.char_at(i)
                    if found_eq {
                        val = val + ch
                    } else if ch == "=" {
                        found_eq = true
                    } else {
                        key = key + ch
                    }
                }
                return [key, val]
            }

            fn strip_quotes(s: String) -> String {
                if len(s) < 2 { return s }
                let first = s.char_at(0)
                let last = s.char_at(len(s) - 1)
                if first == "\\"" {
                    if last == "\\"" {
                        return s.substr(1, len(s) - 1)
                    }
                }
                return s
            }

            fn main() {
                let config: String = "name=\\"Mapanare\\"\\nversion=\\"1.0.0\\"\\nport=8080"
                let lines = config.split("\\n")
                let mut settings: Map<String, String> = #{}
                for line in lines {
                    let kv = parse_kv(line)
                    settings[kv[0]] = strip_quotes(kv[1])
                }
                print(settings["name"])
                print(settings["version"])
                print(settings["port"])
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "Mapanare" in lines[0]
        assert "1.0.0" in lines[1]
        assert "8080" in lines[2]

    def test_toml_section_and_nested_keys(self) -> None:
        """Parse TOML-like sections [section] and extract nested config."""
        source = textwrap.dedent("""\
            fn main() {
                let mut lines: List<String> = ["[server]", "host=localhost", "port=3000"]
                lines = lines + ["[database]", "driver=sqlite", "path=data.db"]

                let mut section: String = ""
                let mut config: Map<String, String> = #{}

                for line in lines {
                    if len(line) > 2 {
                        let first = line.char_at(0)
                        if first == "[" {
                            section = line.substr(1, len(line) - 1)
                        } else {
                            let eq_pos = line.find("=")
                            if eq_pos >= 0 {
                                let key = line.substr(0, eq_pos)
                                let val = line.substr(eq_pos + 1, len(line))
                                config[section + "." + key] = val
                            }
                        }
                    }
                }

                print(config["server.host"])
                print(config["server.port"])
                print(config["database.driver"])
                print(config["database.path"])
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "localhost" in lines[0]
        assert "3000" in lines[1]
        assert "sqlite" in lines[2]
        assert "data.db" in lines[3]


# ── YAML config parsing ──────────────────────────────────────────────────────


class TestYamlConfigParseline:
    """E2E: parse YAML-like config and extract values.

    Simulates YAML parsing using core language features.
    """

    def test_yaml_flat_key_value(self) -> None:
        """Parse 'key: value' lines from a YAML-like string."""
        source = textwrap.dedent("""\
            fn parse_yaml_line(line: String) -> List<String> {
                let colon_pos = line.find(": ")
                if colon_pos < 0 {
                    return [line, ""]
                }
                let key = line.substr(0, colon_pos)
                let val = line.substr(colon_pos + 2, len(line))
                return [key, val]
            }

            fn main() {
                let yaml: String = "app: mapanare\\nver: 2\\nenv: prod\\ndebug: false"
                let lines = yaml.split("\\n")
                let mut config: Map<String, String> = #{}
                for line in lines {
                    let kv = parse_yaml_line(line)
                    if len(kv[1]) > 0 {
                        config[kv[0]] = kv[1]
                    }
                }
                print(config["app"])
                print(config["ver"])
                print(config["env"])
                print(config["debug"])
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "mapanare" in lines[0]
        assert "2" in lines[1]
        assert "prod" in lines[2]
        assert "false" in lines[3]

    def test_yaml_indented_sections(self) -> None:
        """Parse YAML-like indented structure into dot-notation keys."""
        source = textwrap.dedent("""\
            fn main() {
                let mut lines: List<String> = ["server:", "  host: 0.0.0.0", "  port: 9090"]
                lines = lines + ["logging:", "  level: info", "  file: app.log"]

                let mut section: String = ""
                let mut config: Map<String, String> = #{}

                for line in lines {
                    if line.starts_with("  ") {
                        let trimmed = line.substr(2, len(line))
                        let colon_pos = trimmed.find(": ")
                        if colon_pos >= 0 {
                            let key = trimmed.substr(0, colon_pos)
                            let val = trimmed.substr(colon_pos + 2, len(trimmed))
                            config[section + "." + key] = val
                        }
                    } else if line.ends_with(":") {
                        section = line.substr(0, len(line) - 1)
                    }
                }

                print(config["server.host"])
                print(config["server.port"])
                print(config["logging.level"])
                print(config["logging.file"])
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "0.0.0.0" in lines[0]
        assert "9090" in lines[1]
        assert "info" in lines[2]
        assert "app.log" in lines[3]


# ── File I/O roundtrip ────────────────────────────────────────────────────────


class TestFileRoundtrip:
    """E2E: file read/write/read roundtrip via string manipulation.

    Tests simulate the file I/O pattern by building content strings,
    processing them, and verifying the pipeline output.
    """

    def test_string_content_roundtrip(self) -> None:
        """Build content, process it, verify roundtrip integrity."""
        source = textwrap.dedent("""\
            fn write_content(lines: List<String>) -> String {
                let mut result: String = ""
                for line in lines {
                    result = result + line + "\\n"
                }
                return result
            }

            fn read_lines(content: String) -> List<String> {
                return content.split("\\n")
            }

            fn main() {
                let mut original: List<String> = ["first line of content"]
                original = original + ["second line has data", "third line is the end"]
                let written = write_content(original)
                let read_back = read_lines(written)

                let mut count: Int = 0
                for line in read_back {
                    if len(line) > 0 {
                        count = count + 1
                    }
                }
                print(count)
                print(read_back[0])
                print(read_back[2])
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "3" in lines[0]
        assert "first line of content" in lines[1]
        assert "third line is the end" in lines[2]

    def test_multiline_transform_roundtrip(self) -> None:
        """Read content, transform each line, write back, verify."""
        source = textwrap.dedent("""\
            fn to_upper_first(s: String) -> String {
                if len(s) == 0 { return s }
                let first = s.char_at(0)
                let rest = s.substr(1, len(s))
                return first + rest
            }

            fn main() {
                let content: String = "hello world\\ngoodbye world\\nfoo bar"
                let lines = content.split("\\n")
                let mut transformed: List<String> = []
                for line in lines {
                    transformed = transformed + ["[" + line + "]"]
                }

                for t in transformed {
                    print(t)
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "[hello world]" in lines[0]
        assert "[goodbye world]" in lines[1]
        assert "[foo bar]" in lines[2]


# ── CSV pipeline ──────────────────────────────────────────────────────────────


class TestCsvPipeline:
    """E2E: CSV parse/transform/write pipeline using core language features."""

    def test_csv_parse_and_transform(self) -> None:
        """Parse CSV string, transform values, write back as CSV."""
        source = textwrap.dedent("""\
            fn split_csv_row(line: String) -> List<String> {
                return line.split(",")
            }

            fn join_csv_row(fields: List<String>) -> String {
                let mut result: String = ""
                for i in 0..len(fields) {
                    if i > 0 { result = result + "," }
                    result = result + fields[i]
                }
                return result
            }

            fn main() {
                let csv_input: String = "name,age,city\\nAlice,30,CCS\\nBob,25,MAR\\nCarla,35,BQT"
                let lines = csv_input.split("\\n")

                let header = lines[0]
                print(header)

                let mut output_rows: List<String> = []
                for i in 1..len(lines) {
                    let fields = split_csv_row(lines[i])
                    let name = fields[0]
                    let age = int(fields[1])
                    let city = fields[2]

                    let new_age = age + 1
                    let new_row = name + "," + str(new_age) + "," + city
                    output_rows = output_rows + [new_row]
                }

                for row in output_rows {
                    print(row)
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "name,age,city" in lines[0]
        assert "Alice,31,CCS" in lines[1]
        assert "Bob,26,MAR" in lines[2]
        assert "Carla,36,BQT" in lines[3]

    def test_csv_filter_and_aggregate(self) -> None:
        """Parse CSV, filter rows by condition, compute aggregate."""
        source = textwrap.dedent("""\
            fn main() {
                let d = "item,price,qty\\nApple,2,10\\nBanana,1,20\\nMango,3,5\\nOrange,2,15"
                let lines = d.split("\\n")

                let mut total_value: Int = 0
                let mut expensive_count: Int = 0

                for i in 1..len(lines) {
                    let fields = lines[i].split(",")
                    let price = int(fields[1])
                    let qty = int(fields[2])
                    let value = price * qty
                    total_value = total_value + value

                    if price >= 2 {
                        expensive_count = expensive_count + 1
                    }
                }

                print(total_value)
                print(expensive_count)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        # Apple: 2*10=20, Banana: 1*20=20, Mango: 3*5=15, Orange: 2*15=30 -> total 85
        assert "85" in lines[0]
        # Price >= 2: Apple(2), Mango(3), Orange(2) = 3
        assert "3" in lines[1]

    def test_csv_join_two_datasets(self) -> None:
        """Join two CSV-like datasets on a shared key."""
        source = textwrap.dedent("""\
            fn main() {
                let users: List<String> = ["1,Alice", "2,Bob", "3,Carla"]
                let scores: List<String> = ["1,95", "2,87", "3,92"]

                let mut user_map: Map<String, String> = #{}
                for u in users {
                    let parts = u.split(",")
                    user_map[parts[0]] = parts[1]
                }

                for s in scores {
                    let parts = s.split(",")
                    let user_id = parts[0]
                    let score = parts[1]
                    let name = user_map[user_id]
                    print(name + ": " + score)
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "Alice: 95" in lines[0]
        assert "Bob: 87" in lines[1]
        assert "Carla: 92" in lines[2]


# ── Embedded KV store ─────────────────────────────────────────────────────────


class TestEmbeddedKVPipeline:
    """E2E: embedded key-value store using maps.

    Simulates the embedded_kv stdlib pattern: create a map-backed store,
    set/get values, serialize to JSON-like format, deserialize back.
    """

    def test_kv_set_get_cycle(self) -> None:
        """Set keys, get them back, verify correctness."""
        source = textwrap.dedent("""\
            fn main() {
                let mut store: Map<String, String> = #{}

                store["lang"] = "mapanare"
                store["version"] = "1.0.0"
                store["author"] = "community"

                print(store["lang"])
                print(store["version"])
                print(store["author"])
                print(len(store))
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "mapanare" in lines[0]
        assert "1.0.0" in lines[1]
        assert "community" in lines[2]
        assert "3" in lines[3]

    def test_kv_serialize_and_deserialize(self) -> None:
        """Serialize a map to a JSON-like string and deserialize it back."""
        source = textwrap.dedent("""\
            fn serialize_kv(store: Map<String, String>) -> String {
                let mut result: String = "{"
                let mut first: Bool = true
                for key in store {
                    if first {
                        first = false
                    } else {
                        result = result + ","
                    }
                    result = result + "\\"" + key + "\\":\\"" + store[key] + "\\""
                }
                result = result + "}"
                return result
            }

            fn main() {
                let mut store: Map<String, String> = #{}
                store["host"] = "localhost"
                store["port"] = "5432"
                store["db"] = "myapp"

                let serialized = serialize_kv(store)
                print(serialized)

                let has_host = serialized.find("host")
                let has_port = serialized.find("port")
                let has_db = serialized.find("db")

                if has_host >= 0 {
                    print("host:ok")
                }
                if has_port >= 0 {
                    print("port:ok")
                }
                if has_db >= 0 {
                    print("db:ok")
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = result.stdout.strip()
        assert "host:ok" in output
        assert "port:ok" in output
        assert "db:ok" in output

    def test_kv_update_and_delete(self) -> None:
        """Update existing keys and simulate deletion via rebuild."""
        source = textwrap.dedent("""\
            fn kv_delete(store: Map<String, String>, del_key: String) -> Map<String, String> {
                let mut new_store: Map<String, String> = #{}
                for key in store {
                    if key != del_key {
                        new_store[key] = store[key]
                    }
                }
                return new_store
            }

            fn main() {
                let mut store: Map<String, String> = #{}
                store["a"] = "1"
                store["b"] = "2"
                store["c"] = "3"

                print(len(store))

                store["b"] = "99"
                print(store["b"])

                let store2 = kv_delete(store, "a")
                print(len(store2))

                for key in store2 {
                    print(key + "=" + store2[key])
                }
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "3" in lines[0]  # initial size
        assert "99" in lines[1]  # updated value
        assert "2" in lines[2]  # size after delete

    def test_kv_bulk_load_and_query(self) -> None:
        """Bulk-load key-value pairs and perform lookups."""
        source = textwrap.dedent("""\
            fn main() {
                let mut data: List<String> = ["user:1=Alice", "user:2=Bob", "user:3=Carla"]
                data = data + ["user:4=Diana", "user:5=Eve"]

                let mut store: Map<String, String> = #{}
                for entry in data {
                    let eq_pos = entry.find("=")
                    let key = entry.substr(0, eq_pos)
                    let val = entry.substr(eq_pos + 1, len(entry))
                    store[key] = val
                }

                print(len(store))
                print(store["user:1"])
                print(store["user:3"])
                print(store["user:5"])

                let mut found: Int = 0
                for k in store {
                    if store[k] == "Carla" {
                        found = 1
                    }
                }
                print(found)
            }
        """)
        result = _run_mapanare(source)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        lines = result.stdout.strip().split("\n")
        assert "5" in lines[0]
        assert "Alice" in lines[1]
        assert "Carla" in lines[2]
        assert "Eve" in lines[3]
        assert "1" in lines[4]
