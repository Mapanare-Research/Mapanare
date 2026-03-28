<div align="center">

<img width="3200" height="1344" alt="MapanareDevTo" src="https://github.com/user-attachments/assets/99b80387-afd9-4b07-beb8-59a8f63f7ac7" />

# Mapanare

**/mah-pah-NAH-reh/**

**AI原生编程语言。**

*代理。信号。流。张量。一等公民，而非框架。*

Mapanare 编译为 Python（转译器）和原生二进制文件（LLVM），自托管编译器正在开发中。

[English](../README.md) | [Español](README.es.md) | 中文版 | [Português](README.pt.md)

<br>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LLVM](https://img.shields.io/badge/LLVM-原生后端-262D3A?style=for-the-badge&logo=llvm&logoColor=white)
![平台](https://img.shields.io/badge/Linux%20%7C%20macOS%20%7C%20Windows-grey?style=for-the-badge)
[![Discord](https://img.shields.io/discord/1480688663674359810?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/5hpGBm3WXf)

[![许可证](https://img.shields.io/badge/许可证-MIT-green.svg?style=flat-square)](../LICENSE)
[![版本](https://img.shields.io/badge/版本-0.3.1-blue.svg?style=flat-square)](../CHANGELOG.md)
[![测试](https://img.shields.io/badge/测试-2090_通过_(82_文件)-brightgreen.svg?style=flat-square)]()
[![GitHub Stars](https://img.shields.io/github/stars/Mapanare-Research/Mapanare?style=flat-square&color=f5c542)](https://github.com/Mapanare-Research/Mapanare/stargazers)

<br>

[**快速开始**](getting-started.md) · [为什么选择 Mapanare？](#为什么选择-mapanare) · [安装](#安装) · [语言特性](#语言特性) · [基准测试](#基准测试) · [CLI](#cli) · [架构](#编译器架构) · [路线图](roadmap/ROADMAP.md) · [贡献](#贡献) · [Discord](https://discord.gg/5hpGBm3WXf)

</div>

---

## 为什么选择 Mapanare？

所有主流语言都将代理、信号、流和张量视为库级构造——与编译器隔了一层抽象。这意味着没有编译时数据流验证，没有静态张量形状检查，也没有语言级别的消息传递保证。

Mapanare 使这些原语成为**语言的一部分**：

- **代理**像函数一样自然——声明、创建、发送、接收，都有编译器检查的专用语法
- **信号**用自动依赖跟踪取代回调地狱
- **流**用 `|>` 按你思考数据的方式组合，内置算子融合
- **张量**获得编译时形状验证——运行前捕获形状错误
- **没有面向对象**——用结构体、枚举和模式匹配代替类层次结构

阅读完整的[宣言](manifesto.md)。

---

## 安装

### Linux / macOS

```bash
curl -fsSL https://mapanare.dev/install | bash
```

### Windows (PowerShell)

```powershell
irm https://mapanare.dev/install.ps1 | iex
```

### 手动下载

从 [Releases](https://github.com/Mapanare-Research/Mapanare/releases) 下载最新二进制文件。

| 平台 | 文件 |
|------|------|
| Linux (x64) | `mapanare-linux-x64.tar.gz` |
| macOS (Apple Silicon) | `mapanare-mac-arm64.tar.gz` |
| Windows (x64) | `mapanare-win-x64.zip` |

解压并将 `mapanare` 添加到你的 PATH，然后验证：

```bash
mapanare --version
```

---

## 语言特性

### 基础

```mn
fn main() {
    let name = "世界"
    println("你好，" + name + "！")

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

### 结构体、枚举和模式匹配

没有类，没有继承。用结构体、枚举和模式匹配代替。

```mn
enum Shape {
    Circle(Float),
    Rect(Float, Float),
}

fn area(s: Shape) -> Float {
    match s {
        Circle(r) => 3.14159 * r * r,
        Rect(w, h) => w * h,
    }
}
```

### 错误处理

```mn
fn divide(a: Float, b: Float) -> Result<Float, String> {
    if b == 0.0 {
        return Err("除以零")
    }
    return Ok(a / b)
}

let value = divide(10.0, 3.0)?
```

### 代理（实验性）

带类型通道的并发角色。

```mn
agent Greeter {
    input name: String
    output greeting: String

    fn handle(name: String) -> String {
        return "你好，" + name + "！"
    }
}

let greeter = spawn Greeter()
greeter.name <- "世界"
let result = sync greeter.greeting
print(result)
```

### 信号（实验性）

带自动依赖跟踪的响应式状态。

```mn
let mut count = signal(0)
let doubled = signal { count * 2 }
```

### 流（实验性）

使用 `|>` 运算符的异步管道。

```mn
let data = stream([1, 2, 3, 4, 5])
let result = data
    |> filter(fn(x) { x > 2 })
    |> map(fn(x) { x * 10 })
```

---

## CLI

```
mapanare run <文件>          编译并运行
mapanare build <文件>        通过 LLVM 编译为原生二进制
mapanare jit <文件>          JIT 编译并原生运行
mapanare check <文件>        仅类型检查
mapanare compile <文件>      转译为 Python
mapanare emit-llvm <文件>    输出 LLVM IR
mapanare repl                启动交互式 REPL
mapanare fmt <文件>          格式化源代码
mapanare init [路径]         初始化新项目
mapanare install <包>        安装包（基于 git）
mapanare targets             列出支持的编译目标
```

---

## 编译器架构

```
.mn 源码 → 词法分析 → 语法分析 → AST → 语义分析 → 优化器 → 输出
                                                                ↓
                                                         Python | LLVM IR
                                                                ↓
                                                     解释器 | 原生二进制
```

---

## 路线图

| 版本 | 主题 | 状态 |
|------|------|------|
| **v0.1.0** | 基础——引导编译器、双后端、运行时、LSP、标准库 | 已发布 |
| **v0.2.0** | 自托管——LLVM 代码生成、C 运行时、自托管编译器（5,800行 .mn） | 已发布 |
| **v0.3.0** | 深度优先——traits、模块、代理代码生成、arena 内存、1,960+ 测试 | 已发布 |
| **v0.4.0** | 面向世界——FFI、C 运行时加固、诊断、作用域清理 | 下一个 |
| **v0.5.0** | 生态系统——包注册中心、WASM 演练场、代码检查器 | 计划中 |
| **v1.0.0** | 稳定版——语言规范冻结、向后兼容保证 | 计划中 |

查看完整的[路线图](roadmap/ROADMAP.md)了解详情。

---

## 贡献

参见 [CONTRIBUTING.md](../CONTRIBUTING.md)。社区标准和项目流程在 [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)、[GOVERNANCE.md](../GOVERNANCE.md) 和 [SECURITY.md](../SECURITY.md) 中。语言更改需要提交 [RFC](rfcs/)。

---

## 许可证

MIT 许可证——详见 [LICENSE](../LICENSE)。

---

<div align="center">

**Mapanare** — AI 值得拥有的语言。

[报告Bug](https://github.com/Mapanare-Research/Mapanare/issues/new?template=bug_report.yml) · [功能请求](https://github.com/Mapanare-Research/Mapanare/issues/new?template=feature_request.yml) · [规范](SPEC.md) · [更新日志](../CHANGELOG.md) · [Discord](https://discord.gg/5hpGBm3WXf) · [Twitter](https://x.com/mapanare)

由 [Juan Denis](https://juandenis.com) 用心打造

</div>
