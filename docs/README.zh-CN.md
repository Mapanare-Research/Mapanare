<div align="center">

<img width="1280" height="640" alt="mapanare-repo" src="https://github.com/user-attachments/assets/176d26e7-0c42-49ef-99d2-b8192cd75e53" />

# Mapanare

**/mah-pah-NAH-reh/**

**AI原生编程语言。**

*代理。信号。流。张量。一等公民，不是框架。*

通过LLVM和WebAssembly编译为原生二进制文件。
**比Python快约168倍。与Rust和C持平。**

[English](../README.md) | [Espanol](README.es.md) | 中文版 | [Portugues](README.pt.md)

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-原生后端-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![WebAssembly](https://img.shields.io/badge/WebAssembly-后端-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)
![平台](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![许可证](https://img.shields.io/badge/许可证-MIT-green.svg?style=flat-square)](../LICENSE)
[![版本](https://img.shields.io/badge/版本-5.7.0-blue.svg?style=flat-square)](../CHANGELOG.md)
[![测试](https://img.shields.io/badge/测试-5800+_通过-brightgreen.svg?style=flat-square)]()
[![Goldens](https://img.shields.io/badge/goldens-66%2F66-brightgreen.svg?style=flat-square)]()
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**网站**](https://mapanare.dev) · [**文档**](https://mapanare.dev/docs) · [**下载**](https://mapanare.dev/download) · [**Discord**](https://discord.gg/5hpGBm3WXf)

</div>

---

## 安装

```bash
curl -fsSL https://mapanare.dev/install | bash
```

```powershell
# Windows (PowerShell)
irm https://mapanare.dev/install.ps1 | iex
```

或从[Releases](https://github.com/Mapanare-Research/Mapanare/releases)下载二进制文件。

---

## Hello World

```mn
fn main() {
    print("你好，来自mapanare")
}
```

```bash
mapanare run hello.mn        # 编译 + 运行
mapanare build hello.mn      # 生成原生二进制文件
```

---

## 用Python写，编译为原生

将现有Python脚本编译为原生二进制文件：

```bash
mapanare build your_script.py -o your_script
./your_script   # 快33-239倍
```

[Python转原生指南](https://mapanare.dev/docs/guides/python-to-native)

---

## 语言特性

```mn
// 代理 — 一等公民并发角色
agent Counter {
    state count: Int = 0
    on increment { count = count + 1 }
    on get_count -> Int { return count }
}

// 信号 — 响应式状态
let temperature = signal(72.0)
let alert = computed(() => temperature.get() > 100.0)

// 流 — 可组合的数据管道
let results = data_stream
    |> filter((x) => x > 0)
    |> map((x) => x * 2)
    |> collect()

// 模式匹配
match response {
    Ok(data) => process(data),
    Err(e) => print(e)
}

// AI标准库
import ai::llm
let answer = ask(ollama("llama3.2"), "什么是Mapanare?")
```

完整语言参考、教程和菜谱请访问[mapanare.dev/docs](https://mapanare.dev/docs)。

---

## 贡献

请参阅[CONTRIBUTING.md](../CONTRIBUTING.md)。语言变更需要[RFC](rfcs/)。

## 许可证

MIT许可证 — 详见[LICENSE](../LICENSE)。

---

<div align="center">

**Mapanare** — AI值得拥有的语言。

[报告Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [请求功能](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

由[Juan Denis](https://juandenis.com)精心制作

</div>
