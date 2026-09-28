# Changelog

本项目的更改记录在此文件。

All notable changes to this project are documented in this file.

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-09-14

### 修复

- `scripts/check_fonts.py`：规范名 → 实装名映射表补齐 `思源黑体 CN`；缺失字体没有对应替代建议时，报告不再输出 `替代 None`。
- `reference/fonts.md`：`Stylized font` 列取值与字体类型对齐——`阿里妈妈刀隶体`、`阿里妈妈东方大楷`、`站酷文艺体`、`飞波正点体`、`得意黑`、`ZCOOL KuaiLe` 标记为风格化字体（原取值按「有无使用限制」填写，与列名语义相反）。
- `scripts/pptd_to_pptx.py`：模块文档字符串与实现对齐——`table` 已支持，`icon` / `chart` 静默跳过，`image` 需本地文件，未知 `shapeName` 退化为矩形。

### 变更

- `SKILL.md` 补齐开箱所需事实：`.pptd` 必须声明 `version: v2`；两条轨道的依赖与边界（Node.js 18+ 含 npm、Chrome 或 Edge、`agent-browser ≥0.33.2` 由脚本经 npm 安装或升级、自动安装范围 `PyYAML` / `Pillow` / `websocket-client`、本地轨道的元素支持为真子集、输出已存在须 `--force`）。
- 预览命令简化为 `python scripts/pptd_to_png.py <deck.pptd>`（缺省输出 `<工程目录>/.preview`），并说明预览不渲染 `table` / `icon` / `chart`；示例占位符统一为 `<工程目录>`。
- 叙述通用化，去掉对特定机器与平台的假设；术语统一为「本地轨道 / 桌面增强轨道」，映射表口径统一为「以 `check_fonts.py` 在本机的输出为准」。
- `reference/local-fonts.md`：`精品点阵体`、`LXGW Bright`、`ZCOOL KuaiLe` 独立为「中英混排（Mixed CJK–Latin）」分组，与 `fonts.md` 分组一致；删除与 `SKILL.md` 重复的规则声明，并标注映射表为常见实装名参考。
- `reference/slides_categories.md`：用法说明由三条列表合并为一句，章节编号统一为 `1.` / `2.`。

### 移除

- `SKILL.md` 的本地编辑器入口 `npx open-kimi-ppt-skill serve`：上游 npm 包 `open-kimi-ppt-skill` 已于 2026-08-07 下架，该入口不可用；手动编辑统一为「改 `.page` → `pptd_to_png.py` 预览 → 重导出」。

### Fixed

- `scripts/check_fonts.py`: the canonical name to installed name mapping table now includes `思源黑体 CN`; when a missing font has no corresponding substitution suggestion, the report no longer prints `替代 None`.
- `reference/fonts.md`: the values in the `Stylized font` column are now aligned with the font type — `阿里妈妈刀隶体`, `阿里妈妈东方大楷`, `站酷文艺体`, `飞波正点体`, `得意黑` and `ZCOOL KuaiLe` are marked as stylized fonts (the previous values were filled in by "whether there are usage restrictions", which is the opposite of what the column name means).
- `scripts/pptd_to_pptx.py`: the module docstring is now aligned with the implementation — `table` is already supported, `icon` / `chart` are silently skipped, `image` requires a local file, and an unknown `shapeName` degrades to a rectangle.

### Changed

- `SKILL.md` now includes the facts needed to get started: a `.pptd` must declare `version: v2`; the dependencies and boundaries of the two tracks (Node.js 18+ with npm, Chrome or Edge, `agent-browser ≥0.33.2` installed or upgraded by the script via npm, the automatic installation scope `PyYAML` / `Pillow` / `websocket-client`, the element support of the local track being a proper subset, and `--force` being required when the output already exists).
- The preview command is simplified to `python scripts/pptd_to_png.py <deck.pptd>` (the default output is `<工程目录>/.preview`), and it is now documented that the preview does not render `table` / `icon` / `chart`; the example placeholder is unified as `<工程目录>`.
- The wording is generalized, removing assumptions about a specific machine and platform; the terminology is unified as "local track / desktop enhancement track", and the mapping table guidance is unified as "based on the output of `check_fonts.py` on the local machine".
- `reference/local-fonts.md`: `精品点阵体`, `LXGW Bright` and `ZCOOL KuaiLe` are split out into a "Mixed CJK–Latin" group, consistent with the grouping in `fonts.md`; the rule statements duplicated with `SKILL.md` are removed, and the mapping table is annotated as a reference for common installed names.
- `reference/slides_categories.md`: the usage notes are merged from three list items into one sentence, and the section numbering is unified as `1.` / `2.`.

### Removed

- The local editor entry point `npx open-kimi-ppt-skill serve` in `SKILL.md`: the upstream npm package `open-kimi-ppt-skill` was unpublished on 2026-08-07, so that entry point is unavailable; manual editing is unified as "edit `.page` → preview with `pptd_to_png.py` → re-export".

## [1.0.3] - 2026-09-12

### 变更

- **字体路径动态解析与跨平台健壮性增强**：`scripts/check_fonts.py` 与 `scripts/pptd_to_png.py` 在 Windows 环境下优先读取 `%SystemRoot%\Fonts` 及当前用户字体目录（`~\AppData\Local\Microsoft\Windows\Fonts`），不再硬编码 `C:\Windows\Fonts`；POSIX 环境增加 `~/.local/share/fonts` 探测支持。
- **脱敏与通用化表述优化**：`reference/local-fonts.md` 脱敏「本机」口吻，优化为面向各机型通用实装名称与典型免费商用字体推荐。
- **冗余清理**：清理分发与备份中遗留的 `__pycache__` 编译缓存。

## [1.0.2] - 2026-09-12

### 新增

- **字体解析跨平台**：`scripts/check_fonts.py` 与 `scripts/pptd_to_png.py` 不再写死 `C:\Windows\Fonts`——Windows 仍读字体注册表，Linux / macOS 改扫系统字体目录（fontconfig / Font Book 常用路径，去掉字重后缀还原族名），并新增系统兜底字体解析（按需选 bold/常规字形），预览渲染在非 Windows 机器上不再因找不到字体而失败。

### 修复

- `reference/local-fonts.md` 里的两处失效引用（指向已被中文版 `SKILL.md` 删除的旧小节名 `Font availability check`）改为指向现行「三、字体核对（防豆腐块）」。

### 变更

- `reference/local-fonts.md` 明确**映射表是某台基准机的快照、不是通用事实**：换机器先跑 `check_fonts.py`，以脚本输出为准；`SKILL.md` 相应把「写本机实装名」改为「写目标机的实装名」，并说明字体目录的平台差异。

## [1.0.1] - 2026-09-09

### 变更

- `skills/kimi-ppt/SKILL.md` 由英文叙述改为**中文精炼版**：按「需求确认 → 前置检查 → 字体核对 → 生成 → 校验 → 导出交付」六步重排，篇幅从 217 行压到 116 行，去除与 `reference/` 重复的英文长段说明。
- 补齐被原版分散在正文中的关键约束：需求确认四维度表、工程目录布局、复刻/编辑/套模板/风格迁移四类生成策略、配图四条纪律、导出后 CT_Slide 根级 `transition` 校验、动画与备注默认不加。
- 明确**本地轨道为默认**：`pptd_to_pptx.py`（纯本地、离线）优先，`export_pptx.py`（字体嵌入 + 淡入淡出）作为桌面增强轨道，沙箱受限时直接回退、不反复重试。
