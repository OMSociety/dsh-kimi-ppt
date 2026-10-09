# Changelog

本项目的更改记录在此文件。

All notable changes to this project are documented in this file.

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-10-09

### 新增

- 本地导出的图片按 `fit` 规范实现三种模式（`cover` 默认 / `contain` / `fill`）与 `crop` 裁剪：`skills/kimi-ppt/scripts/pptd_to_pptx.py` 写 `a:srcRect`，`skills/kimi-ppt/scripts/pptd_to_png.py` 按同语义渲染。
- 本地导出的 `table` 接入主题样式的最小映射：`style`（`$key` 或内联）与 `cell.textStyle` 解引用 `theme.tableStyles` / `theme.textStyles`，覆盖首行强调、边框、纯色填充、zebra 条纹与字号/色/粗斜/字体族；单元格内联字段优先。
- 两条本地命令结束时向 stderr 打印 `dropped` 降级清单（`dropped: <类型>/<元素>: <原因>`，末行 `dropped total: N`）。
- `skills/kimi-ppt/scripts/check_fonts.py` 枚举已装字体时合并 HKLM 与 HKCU（每用户字体安装落 HKCU），并把实装名匹配收紧到词边界。
- `find_download` 在多个候选共享同一最新时间戳时判定为歧义下载、报错放弃，并只接受严格最新的 `.pptx`。

### 修复

- 本地导出把图片按 `bounds` 拉伸：现按 `fit`（默认 `cover`）等比裁剪或居中留白。
- `line` 元素的 `points` 从 `viewBox` 映射到 `bounds` 并取首末点为端点；PNG 预览的坐标映射补上 `scale`，同一 deck 在不同 `scale` 下形状一致。
- PNG 预览补齐 rotation 绘制与 `custom` 灰描边（与导出一致）；无 `fill` 的 shape 按规范渲染为无填充，两轨口径一致。
- 直角三角形枚举名与文档对齐（`rtTriangle`）。
- 空 `pages` 两条命令一致报错退出；`--help` 不再触发依赖安装副作用；`.preview` 等派生目录不再混入导出载荷；WebSocket 握手异常转为友好报错；清理死代码与失效默认值。

### 变更

- `peerDependencies` 区间改为两段式 `>=0.1.5-rc.2 <0.2.0-0 || >=0.2.0-rc.1 <0.3.0-0`：DSH 安装闸按 `includePrerelease` 判定，包管理器解析 peer 时不带该选项，各预发布元组须单列一段；本版在 DSH 0.2.0-rc.2 上验证。
- `skills/kimi-ppt/SKILL.md` 的本地轨道能力清单与实际行为对齐（含 `dropped` 计数说明）；`README.md` 的安装说明（桌面版在应用内安装）、脚本路径、依赖口径（Chrome 或 Edge、`agent-browser` 自动安装、`statics.moonshot.cn`）与两条轨道表述对齐。
- `skills/kimi-ppt/reference/design_system/` 各 `design.md` 的标题类别词与术语统一；`skills/kimi-ppt/reference/local-fonts.md` 更正字体文件名拼写。
- `CHANGELOG.md` 自 1.1.1 起随 npm 包发布。

### Added

- Local image export now implements the `fit` modes (`cover` default / `contain` / `fill`) and `crop` per the spec: `skills/kimi-ppt/scripts/pptd_to_pptx.py` writes `a:srcRect`, and `skills/kimi-ppt/scripts/pptd_to_png.py` renders the same semantics.
- The local `table` export maps theme styles minimally: `style` (`$key` or inline) and `cell.textStyle` resolve `theme.tableStyles` / `theme.textStyles`, covering header emphasis, borders, solid fills, zebra bands, and size/colour/bold/italic/family; inline cell fields win.
- Both local commands print a `dropped` degradation list to stderr (`dropped: <type>/<element>: <reason>`, ending with `dropped total: N`).
- `skills/kimi-ppt/scripts/check_fonts.py` merges HKLM and HKCU when enumerating installed fonts (per-user installs land in HKCU), and tightens installed-name matching to word boundaries.
- `find_download` reports an ambiguous download and gives up when several candidates share the newest timestamp, and only accepts the strictly newest `.pptx`.

### Fixed

- Local export stretched images to `bounds`; it now crops or letterboxes per `fit` (default `cover`).
- `line` elements map `points` from `viewBox` to `bounds` and use the first/last point as endpoints; the PNG preview now applies the `scale` factor, so one deck renders identically at any scale.
- The PNG preview draws rotation and the `custom` grey outline (matching the export track); shapes without `fill` render unfilled per the spec, consistently across both tracks.
- The right-triangle enum name is aligned with the docs (`rtTriangle`).
- Empty `pages` fails fast on both commands; `--help` no longer triggers dependency installation; derived directories such as `.preview` no longer leak into the export payload; WebSocket handshake errors turn into friendly messages; dead code and stale defaults removed.

### Changed

- The `peerDependencies` range is now two-segment `>=0.1.5-rc.2 <0.2.0-0 || >=0.2.0-rc.1 <0.3.0-0`: the DSH install gate evaluates with `includePrerelease` while package managers do not, so each prerelease tuple needs its own segment; this release is verified on DSH 0.2.0-rc.2.
- `skills/kimi-ppt/SKILL.md`'s local-track capability list is aligned with the actual behaviour (including the `dropped` counter); `README.md` install notes (desktop installs happen in the app), script paths, dependency wording (Chrome or Edge, automatic `agent-browser` install, `statics.moonshot.cn`), and the two-track descriptions are aligned.
- Titles and terminology unified across `skills/kimi-ppt/reference/design_system/` `design.md` files; a font filename typo fixed in `skills/kimi-ppt/reference/local-fonts.md`.
- `CHANGELOG.md` has shipped inside the npm package since 1.1.1.

## [1.1.2] - 2026-10-04

### 新增

- 插件有了自己的图标：包根 `icon.svg`（36×36，橙蓝双卡层叠 + 两道白色文字条），由 `package.json` 顶层 `icon` 字段声明并列入 `files`。插件列表里不再显示 DSH 的默认图形。
- 插件列表里的显示名与描述有了中英两份（`locale/en.json`、`locale/zh.json` 的 `meta.title` 与 `meta.description`），标题中英都写作「Kimi PPT」；`package.json` 的 `exports` 与 `files` 相应放行 `locale/*.json`。此前该处回退成包名与英文 `description`，在中文界面里中英混排。

### Added

- The plugin now ships its own icon: `icon.svg` at the package root (36×36, an orange slide behind a blue one, with two white text bars), declared through the top-level `icon` field in `package.json` and listed in `files`. The plugin list no longer falls back to the default DSH artwork.
- The plugin's display name and description in the plugin list now ship in both languages (`meta.title` and `meta.description` in `locale/en.json` and `locale/zh.json`), titled `Kimi PPT` in both; `exports` and `files` in `package.json` admit `locale/*.json` accordingly. The list previously fell back to the package name and the English `description`, mixing languages inside a Chinese interface.

## [1.1.1] - 2026-09-28

### 修复

- 注册 `kimi-ppt` 技能时补上 `source`，加载该技能不再报 `loaded skill "kimi-ppt" source must be a string`。

### 变更

- 声明宿主依赖区间 `>=0.1.5-rc.2 <0.3.0-0`（`peerDependencies`：`@deepseek-ai/dsh-skill`）。DSH 0.1.7-rc.1 起的兼容闸按该字段逐条判定插件能否在宿主上加载；本插件在 DSH 0.2.0-rc.1 上安装与加载正常。

### Fixed

- Skill registration now passes `source`, so the `kimi-ppt` skill no longer raises `loaded skill "kimi-ppt" source must be a string` when it is loaded.

### Changed

- Declared the host range `>=0.1.5-rc.2 <0.3.0-0` in `peerDependencies` (`@deepseek-ai/dsh-skill`). The compatibility gate in dsh 0.1.7-rc.1 and later checks this field entry by entry to decide whether the plugin may load on the host; this plugin installs and loads normally on dsh 0.2.0-rc.1.

## [1.1.0] - 2026-09-14

### 修复

- `skills/kimi-ppt/scripts/check_fonts.py`：规范名 → 实装名映射表补齐 `思源黑体 CN`；缺失字体没有对应替代建议时，报告不再输出 `替代 None`。
- `skills/kimi-ppt/reference/fonts.md`：`Stylized font` 列取值与字体类型对齐——`阿里妈妈刀隶体`、`阿里妈妈东方大楷`、`站酷文艺体`、`飞波正点体`、`得意黑`、`ZCOOL KuaiLe` 标记为风格化字体（原取值按「有无使用限制」填写，与列名语义相反）。
- `skills/kimi-ppt/scripts/pptd_to_pptx.py`：模块文档字符串与实现对齐——`table` 已支持，`icon` / `chart` 静默跳过，`image` 需本地文件，未知 `shapeName` 退化为矩形。

### 变更

- `skills/kimi-ppt/SKILL.md` 补齐开箱所需事实：`.pptd` 必须声明 `version: v2`；两条轨道的依赖与边界（Node.js 18+ 含 npm、Chrome 或 Edge、`agent-browser ≥0.33.2` 由脚本经 npm 安装或升级、自动安装范围 `PyYAML` / `Pillow` / `websocket-client`、本地轨道的元素支持为真子集、输出已存在须 `--force`）。
- 预览命令简化为 `python scripts/pptd_to_png.py <deck.pptd>`（缺省输出 `<工程目录>/.preview`），并说明预览不渲染 `table` / `icon` / `chart`；示例占位符统一为 `<工程目录>`。
- 叙述通用化，去掉对特定机器与平台的假设；术语统一为「本地轨道 / 桌面增强轨道」，映射表口径统一为「以 `skills/kimi-ppt/scripts/check_fonts.py` 在本机的输出为准」。
- `skills/kimi-ppt/reference/local-fonts.md`：`精品点阵体`、`LXGW Bright`、`ZCOOL KuaiLe` 独立为「中英混排（Mixed CJK–Latin）」分组，与 `fonts.md` 分组一致；删除与 `skills/kimi-ppt/SKILL.md` 重复的规则声明，并标注映射表为常见实装名参考。
- `skills/kimi-ppt/reference/slides_categories.md`：用法说明由三条列表合并为一句，章节编号统一为 `1.` / `2.`。

### 移除

- `skills/kimi-ppt/SKILL.md` 的本地编辑器入口 `npx open-kimi-ppt-skill serve`：上游 npm 包 `open-kimi-ppt-skill` 已于 2026-08-07 下架，该入口不可用；手动编辑统一为「改 `.page` → `skills/kimi-ppt/scripts/pptd_to_png.py` 预览 → 重导出」。

### Fixed

- `skills/kimi-ppt/scripts/check_fonts.py`: the canonical name to installed name mapping table now includes `思源黑体 CN`; when a missing font has no corresponding substitution suggestion, the report no longer prints `替代 None`.
- `skills/kimi-ppt/reference/fonts.md`: the values in the `Stylized font` column are now aligned with the font type — `阿里妈妈刀隶体`, `阿里妈妈东方大楷`, `站酷文艺体`, `飞波正点体`, `得意黑` and `ZCOOL KuaiLe` are marked as stylized fonts (the previous values were filled in by "whether there are usage restrictions", which is the opposite of what the column name means).
- `skills/kimi-ppt/scripts/pptd_to_pptx.py`: the module docstring is now aligned with the implementation — `table` is already supported, `icon` / `chart` are silently skipped, `image` requires a local file, and an unknown `shapeName` degrades to a rectangle.

### Changed

- `skills/kimi-ppt/SKILL.md` now includes the facts needed to get started: a `.pptd` must declare `version: v2`; the dependencies and boundaries of the two tracks (Node.js 18+ with npm, Chrome or Edge, `agent-browser ≥0.33.2` installed or upgraded by the script via npm, the automatic installation scope `PyYAML` / `Pillow` / `websocket-client`, the element support of the local track being a proper subset, and `--force` being required when the output already exists).
- The preview command is simplified to `python scripts/pptd_to_png.py <deck.pptd>` (the default output is `<工程目录>/.preview`), and it is now documented that the preview does not render `table` / `icon` / `chart`; the example placeholder is unified as `<工程目录>`.
- The wording is generalized, removing assumptions about a specific machine and platform; the terminology is unified as "local track / desktop enhancement track", and the mapping table guidance is unified as "based on the output of `skills/kimi-ppt/scripts/check_fonts.py` on the local machine".
- `skills/kimi-ppt/reference/local-fonts.md`: `精品点阵体`, `LXGW Bright` and `ZCOOL KuaiLe` are split out into a "Mixed CJK–Latin" group, consistent with the grouping in `fonts.md`; the rule statements duplicated with `skills/kimi-ppt/SKILL.md` are removed, and the mapping table is annotated as a reference for common installed names.
- `skills/kimi-ppt/reference/slides_categories.md`: the usage notes are merged from three list items into one sentence, and the section numbering is unified as `1.` / `2.`.

### Removed

- The local editor entry point `npx open-kimi-ppt-skill serve` in `skills/kimi-ppt/SKILL.md`: the upstream npm package `open-kimi-ppt-skill` was unpublished on 2026-08-07, so that entry point is unavailable; manual editing is unified as "edit `.page` → preview with `skills/kimi-ppt/scripts/pptd_to_png.py` → re-export".

## [1.0.3] - 2026-09-12

### 变更

- **字体路径动态解析与跨平台健壮性增强**：`skills/kimi-ppt/scripts/check_fonts.py` 与 `skills/kimi-ppt/scripts/pptd_to_png.py` 在 Windows 环境下优先读取 `%SystemRoot%\Fonts` 及当前用户字体目录（`~\AppData\Local\Microsoft\Windows\Fonts`），不再硬编码 `C:\Windows\Fonts`；POSIX 环境增加 `~/.local/share/fonts` 探测支持。
- **脱敏与通用化表述优化**：`skills/kimi-ppt/reference/local-fonts.md` 脱敏「本机」口吻，优化为面向各机型通用实装名称与典型免费商用字体推荐。
- **冗余清理**：清理分发与备份中遗留的 `__pycache__` 编译缓存。

## [1.0.2] - 2026-09-12

### 新增

- **字体解析跨平台**：`skills/kimi-ppt/scripts/check_fonts.py` 与 `skills/kimi-ppt/scripts/pptd_to_png.py` 不再写死 `C:\Windows\Fonts`——Windows 仍读字体注册表，Linux / macOS 改扫系统字体目录（fontconfig / Font Book 常用路径，去掉字重后缀还原族名），并新增系统兜底字体解析（按需选 bold/常规字形），预览渲染在非 Windows 机器上不再因找不到字体而失败。

### 修复

- `skills/kimi-ppt/reference/local-fonts.md` 里的两处失效引用（指向已被中文版 `skills/kimi-ppt/SKILL.md` 删除的旧小节名 `Font availability check`）改为指向现行「三、字体核对（防豆腐块）」。

### 变更

- `skills/kimi-ppt/reference/local-fonts.md` 明确**映射表是某台基准机的快照、不是通用事实**：换机器先跑 `skills/kimi-ppt/scripts/check_fonts.py`，以脚本输出为准；`skills/kimi-ppt/SKILL.md` 相应把「写本机实装名」改为「写目标机的实装名」，并说明字体目录的平台差异。

## [1.0.1] - 2026-09-09

### 变更

- `skills/kimi-ppt/SKILL.md` 由英文叙述改为**中文精炼版**：按「需求确认 → 前置检查 → 字体核对 → 生成 → 校验 → 导出交付」六步重排，篇幅从 217 行压到 116 行，去除与 `skills/kimi-ppt/reference/` 重复的英文长段说明。
- 补齐被原版分散在正文中的关键约束：需求确认四维度表、工程目录布局、复刻/编辑/套模板/风格迁移四类生成策略、配图四条纪律、导出后 CT_Slide 根级 `transition` 校验、动画与备注默认不加。
- 明确**本地轨道为默认**：`skills/kimi-ppt/scripts/pptd_to_pptx.py`（纯本地、离线）优先，`skills/kimi-ppt/scripts/export_pptx.py`（字体嵌入 + 淡入淡出）作为桌面增强轨道，沙箱受限时直接回退、不反复重试。
