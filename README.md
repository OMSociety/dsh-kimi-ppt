<div align="center">

<img src="https://raw.githubusercontent.com/OMSociety/dsh-kimi-ppt/main/docs/logo.png" width="160" alt="dsh-kimi-ppt logo"/>

# DSH Kimi PPT

**DeepSeek Harness 插件 —— 内含 kimi-ppt 技能：创建 / 编辑 / 复刻 / 导出 PPT，DSH 内纯本地导出**

  <p>
    <a href="https://www.npmjs.com/package/dsh-kimi-ppt"><img src="https://img.shields.io/npm/v/dsh-kimi-ppt?color=4f6ef7&label=version" alt="Version"></a>
    <a href="https://github.com/deepseek-ai/dsh"><img src="https://img.shields.io/badge/DSH-%3E%3D0.1.5--rc.2%20%3C0.3-4f6ef7" alt="DSH"></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/OMSociety/dsh-kimi-ppt?color=4f6ef7" alt="License"></a>
    <a href="https://github.com/OMSociety/dsh-kimi-ppt/stargazers"><img src="https://img.shields.io/github/stars/OMSociety/dsh-kimi-ppt?color=4f6ef7" alt="Stars"></a>
    <a href="https://github.com/OMSociety/dsh-kimi-ppt/issues"><img src="https://img.shields.io/github/issues/OMSociety/dsh-kimi-ppt?color=4f6ef7" alt="Issues"></a>
  </p>

**目录**：• [核心特性](#核心特性) • [功能概览](#功能概览) • [安装方式](#安装方式) • [命令](#命令) • [设计系统与字体](#设计系统与字体) • [常见问题](#常见问题) • [更新日志](#更新日志)
</div>

> **免责声明**：本插件内含的 `kimi-ppt` 技能为**非官方**项目，未获 Moonshot AI 认可或支持。仅供学习与研究使用。

## 核心特性

| 特性 | 说明 |
|---|---|
| **PPTD DSL** | 基于 Moonshot `.pptd`（YAML）抽象 OOXML，单页自包含、可视即所得 |
| **双素材导出** | 默认产出「可编辑 PPTD 项目 + 本地生成的 .pptx」 |
| **设计系统** | 内置学术 / 咨询 / 金融 / 促销 / 工作等场景预设主题 |
| **DSH 本地导出** | python-pptx 本地生成 `.pptx`，Pillow 本地渲染预览图；离线稳定 |
| **本机字体** | 按实装字体解析，缺失自动提示 + 给本地替代（MiSans / Century Gothic…） |
| **插件即技能** | 通过 `dsh plugin add` 安装，宿主自动注册 `skills/kimi-ppt` 技能根 |

## 功能概览

- **创建与编辑**：从零生成，或导入 `.pptx` 转 `.pptd` 再逐页精修、复刻图片/PDF 为 PPTD。
- **双素材导出**：一个 deck 同时给出 ① 可继续编辑的 PPTD 项目目录；② 纯本地生成的 `.pptx`；字体嵌入与淡入淡出转场由可选的桌面增强导出附加（需桌面环境与网络）。
- **设计系统**：选题后套用预设主题（如学术答辩/咨询/金融），保证版式、配色、层级一致。
- **DSH 本地导出与预览**（本仓库增强）：`pptd_to_pptx.py` 纯本地生成 PPTX；`pptd_to_png.py` 纯本地渲染每页预览图做视觉 QA，不依赖浏览器/外网。

## 安装方式

1. **安装插件**（DSH 用户级，宿主自动把这技能挂到技能目录）：

   ```powershell
   # 先停掉正在运行的 DSH（运行中的服务会锁住依赖，装完再起）
   dsh plugin --profile <profile> add "dsh-kimi-ppt"
   ```

   > **桌面版用户**：桌面的 `desktop` profile 由应用独占管理，CLI 无法代管安装；请在桌面应用内安装此插件。
2. **重启 DSH**：技能目录自动发现；对话里直接说"帮我做一份 PPT"即触发。

> **依赖**：本地导出仅需 `python-pptx` + `Pillow` + `PyYAML`。桌面增强导出（字体嵌入/淡入淡出）另需 Node.js 18+（含 npm）、`agent-browser`（由脚本经 npm 自动安装或升级，≥0.33.2）、Chrome 或 Edge，以及可连 `www.kimi.com` 与 `statics.moonshot.cn`（宿主页脚本 CDN）。

## 命令

技能脚本随插件包安装，位于 profile 的 `node_modules/dsh-kimi-ppt/skills/kimi-ppt/scripts/`（desktop profile 实例：`~/.dsh/profiles/desktop/node_modules/dsh-kimi-ppt/skills/kimi-ppt/scripts/`）；脚本不会复制到 `~/.dsh/skills/`。下表中的 `scripts/...` 指该目录：

| 命令 | 说明 |
|---|---|
| `python scripts/pptd_to_pptx.py <deck.pptd> -o <deck.pptx>` | 本地生成 PPTX（python-pptx，离线） |
| `python scripts/pptd_to_png.py <deck.pptd> -o <.preview>` | 本地渲染每页预览图 + `overview.jpg` |
| `python scripts/check_fonts.py <deck.pptd>` | 检查本机字体，输出 已装/缺失/替代 |
| `python scripts/export_pptx.py <deck.pptd> -o <deck.pptx>` | 桌面增强导出 PPTX（字体嵌入/淡入淡出，需桌面环境与网络） |
| `python scripts/export_images.py <deck.pptd> --output <.qa-images>` | 桌面增强导出整页图（视觉 QA） |

## 设计系统与字体

**预设主题**（`reference/design_system/`）：`academic` 学术 · `consulting` 咨询 · `finance` 金融 · `promotion` 促销 · `work` 工作。

**字体**（`reference/local-fonts.md`，规范名→实装名映射 + 免费商用标记）：

| 场景 | 推荐（中文 / 西文） | 说明 |
|---|---|---|
| 默认正文 | `MiSans` / `Arial` | 干净现代 |
| 几何标题 | `MiSans` / `Century Gothic` | 更 Bauhaus，适合设计 |
| 学术衬线 | `思源宋体 CN` / `Georgia` | 论文/文学 |
| 手写/特色 | `站酷文艺体` / `得意黑` / `飞波正点体` | 品牌/文化 |

> **提示**：生成前跑 `check_fonts.py` 验证；缺失会提示并给本地替代（如 MiSans→更纱黑体 SC、QuattrocentoSans→Century Gothic）。

## 常见问题

- **字体变成底格（tofu）**：deck 用了未安装字体 → 改成本机字体或按映射替换；见 `reference/local-fonts.md`。
- **桌面增强导出失败**：`agent-browser` 建 socket 权限或连 `kimi.com` / `statics.moonshot.cn` 超时 → 改用本地 `pptd_to_pptx.py` / `pptd_to_png.py`。
- **本地导出没有字体嵌入/淡入淡出**：这两项仅在桌面增强导出提供。

## 更新日志

参见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

- 基于 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) 插件/技能体系。

## 许可证与作者

[MIT](LICENSE)。

[OMSociety](https://github.com/OMSociety)
