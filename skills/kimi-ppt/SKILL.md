---
name: kimi-ppt
description: 生成/编辑/复刻/导出 PPT 与演示文稿。默认产出「可编辑 PPTD 项目 + 本地生成的 .pptx」（用 python-pptx 纯本地导出；字体嵌入/淡入淡出走桌面增强轨道，需桌面环境与网络）。内置学术/咨询/金融/促销/工作等设计系统与本地导出字体映射。当用户要求 PPT、PowerPoint、PPTX、幻灯片、演示文稿、答辩/汇报/讲义、信息图、海报，或要求套用设计风格、转换 .pptd/.pptx 时使用。
---

# kimi-ppt：PPT 生成与本地导出

用 PPTD（YAML 中间格式，单页自包含）写 deck，再**纯本地**导出可编辑 `.pptx`。

## 交付产物（默认必须齐备）

除非用户明确只要 PPTD，默认同时交付：

1. **可编辑 PPTD 工程目录**：`deck.pptd`（主题/大纲）+ `pages/*.page`（单页）+ `media/`（素材）；
2. **本地生成的 `.pptx`**。

工程目录布局（已有等价结构则沿用）：

```text
deck/
  deck.pptd          # 主题与大纲
  pages/*.page       # 每页自包含
  media/             # 本地素材
  deck.pptx          # 默认产出
```

## 工作流

### 一、需求确认（先问清，别猜）

| 维度 | 取值 |
|---|---|
| 目的 | 新建 / 编辑现有 PPT / 从图片·PDF·大纲复刻 |
| 设计方向 | 自定 / 指定设计系统 / 套模板 / 风格迁移 |
| 输入 | 仅主题 / 完整文档 / 逐页大纲 |
| 页数 | 用户指定优先；只给文档时先给页数估算并确认 |

- 先读完用户上传的全部文件与 URL，再读 `reference/pptd.md` 掌握格式约束。
- 内容不足以撑满演示时，先用检索补充材料（除非用户明确说不扩展）。
- 需求冲突或无法判定时**先问用户**：调用 `ask_user_question` 工具把冲突项摆成选项（推荐项放首位并加 `(Recommended)`，每项附一句取舍说明），一次一问；工具不可用或没有界面时退回对话里直接问。不要自行脑补。

### 二、前置检查

**本地轨道（默认）**

- Python：`python-pptx` + `Pillow` + `PyYAML`。本地轨道脚本不会自动安装，缺哪个先补：

  ```bash
  python -m pip install python-pptx Pillow PyYAML
  ```

- 字体目录：自动扫描 Windows 与 macOS/Linux 的常见系统与用户字体目录；找不到就回退系统兜底字体（预览图不因此报错）。

**桌面增强轨道（可选）**

- 另需 Node.js 18+（含 npm）、Chrome 或 Edge，以及可连 `www.kimi.com` 与 `statics.moonshot.cn`（宿主页脚本 CDN，不可达时 deckStatus 报错）；`agent-browser` 由脚本经 npm 自动安装或升级（≥0.33.2），Windows 下脚本会另起一个调试用浏览器实例（端口 9337）。
- 缺 `PyYAML` / `Pillow` / `websocket-client` 时脚本会自行 `pip install --user`。
- 以上任一缺失就**直接退回本地轨道**，不硬等、不反复重试。

### 三、字体核对（防豆腐块）

```bash
python scripts/check_fonts.py <deck.pptd>
```

- 规范名→实装名映射与免费商用状态见 `reference/local-fonts.md`；该表只是常见实装名的参考，一律以 `check_fonts.py` 在本机的输出为准（Windows 读注册表，Linux/macOS 扫系统与用户字体目录）。
- `.pptd` 里一律写**目标机的实装名**，保证本地导出命中真实字体。
- 报缺失时：给出缺失清单 + 本地替代（如 `SortsMillGoudy`→`Georgia`、`MiSans`→`更纱黑体 SC`），确认后改写 `.pptd` 再生成。

### 四、生成

- **新建**：按场景读 `reference/slides_categories.md` 里对应场景的规范。指定设计系统时只读该主题（`reference/design_system/`），**严禁混搭**；自定风格时不要自动挑预设。
- **复刻**（图片/PDF → PPTD）：尽量 1:1。看不清的位置用网格线、放大观察；图标用 Font Awesome 近似；照片/头像这类无法用图形近似的，用脚本裁剪原图后作为图片元素插入。
- **编辑**：先把 `pptx` 转成 `pptd` 并复核关键页，只改目标页、别波及范围外。转换有损，出现错乱就对照原 pptx 修。
- **套模板**：转换后识别页型，重点读封面/总结/分节页，提取版式、可复用组件（图标/形状/正文布局）与元素样式再复用。
- **风格迁移**：分析参考的配色、字体、版式、内容密度与组件，鼓励复用原 PDF/网页的插图与字号层级；给了 URL 不要只读文字，要看视觉。
- **海报/信息图**：读 `reference/general-poster.md`，做成单页或少量页 PPTD，再渲染出图（普通 PPT 请求不要读它）。
- **并行**：一轮内并行写多个 `.page` 文件，减少往返。

**配图纪律**

1. 优先级：用户材料 → 官方/权威来源 → 检索到的相关图 → 生成图。
2. 涉及产品、人物、地点、事件、界面、实验对象时优先用真实图片，别把每页都做成文字 + 色块。
3. 先批量备好图再按比例排版；存 `media/`，**严禁拉伸变形**。
4. 不放与页面结论无关的凑数图。

**版式纪律**：多页 deck 避免版式雷同——同一套「三张等宽卡片」不要页页复用，按内容换用非对称两栏、Zig-Zag 交错、整幅图配文字条、时间轴等；层级用字重与色彩对比控制，不靠超大字号撑场面。

**语体纪律**：少用抽象套话与 AI 腔（"闭环/赋能/解构/主战场/看似…实则…/不是 A 而是 B"），不用口号式比喻，以事实和证据说话。

### 五、校验（导出前必做）

1. **结构校验**：对照 `reference/pptd.md` 查必填字段（`version` 必须是字符串 `v2`，否则本地导出直接退出）、类型、主题 token、资源路径，多轮修复。
2. **视觉 QA**：

   ```bash
   python scripts/pptd_to_png.py <deck.pptd>
   ```

   缺省输出 `<工程目录>/.preview`（`page_N.png` + `overview.jpg`，`-o` 可改路径），逐页核对：图片清晰不变形、文字未压住关键画面、元素未越界、文字与背景对比足够、对齐/间距/字号层级统一、无文字溢出与遮挡。可疑页读全分辨率图确认后再改，改完重跑预览直到全部通过。`.preview/` 是中间产物，交付后可删。

   > 预览图渲染 text / shape / line / image（含 rotation），**不渲染 table、icon、chart**：含表格的页要另开 `.pptx` 核对。需要官方渲染效果时再跑 `scripts/export_images.py`（桌面增强轨道）。
3. **模型不支持读图时**：退化为结构复核，并明确说明跳过了图像 QA。

### 六、导出与交付

两条轨道：**本地轨道**（默认，纯本地/离线/沙箱可用）产出标准可编辑 `.pptx`；**桌面增强轨道**（需桌面环境 + 网络，依赖见「二、前置检查」）在此基础上附加**字体嵌入 + 淡入淡出转场**，这两项只有桌面增强轨道提供。

本地轨道的元素支持是**真子集**，未渲染或未映射的部分会向 stderr 打印 `dropped` 计数清单（末行 `dropped total: N`）：

- **text / shape / line**：支持。line 的 `points` 取首末点映射到 bounds，中间控制点降级为直线（贝塞尔不实现）。
- **image**：只插本地存在的文件；`fit` 三模式（`cover` 默认 / `contain` / `fill`）与 `crop` 正值按规范实现，`cropShape` 与 `crop` 负值（outset）降级。
- **table**：结构、合并单元格与文本支持；主题样式做最小映射（`style` / `textStyle` 的首行强调、边框、纯色填充、zebra、字号/色/粗斜/字体族），其余样式字段降级。
- **无 fill 的 shape** 按规范渲染为无填充；未知 `shapeName` 退成矩形；`custom` 只画灰描边占位（预览与导出一致）。
- **icon / chart** 跳过；`notes`、`animations`、`opacity`、`flip` 本地轨道忽略；rotation 在导出轨道仅支持 shape（预览轨道支持 text / shape / line / image）。
- deck 的 `pages` 为空时两条命令一致报错退出。

deck 含降级项时改用桌面增强轨道，或如实说明差异。两条命令在输出文件已存在时都须加 `--force`，否则直接报错退出。

1. **本地导出**：

   ```bash
   python scripts/pptd_to_pptx.py <deck.pptd> -o <工程目录>/deck.pptx --force
   ```
2. **桌面增强导出**：

   ```bash
   python scripts/export_pptx.py <deck.pptd> --output <工程目录>/deck.pptx --force
   ```

   沙箱报错（socket 权限 / 连接超时）就退回本地轨道。
3. **导出后校验**：确认文件存在；淡入淡出须是每个 slide 的**根级唯一** `transition`（按 CT_Slide 顺序 `cSld` → 可选 `clrMapOvr` → `transition`），PPTX ZIP 完整性通过。只做字节搜索 `<p:fade>` 不算验证。
4. **交付清单**：给出绝对路径的可点击链接——工程目录、`.pptd`、`pages/`、`media/`、`.pptx`；结尾补一句后续操作提示。
5. **手动编辑**：直接用编辑器改 `.page`（或 `.pptd`）→ `pptd_to_png.py` 预览 → 重导出。
6. **动画与备注**：默认**不加**（阅读/自学/打印/发送类 deck 不需要）。用户明确要求或确属现场演示时才用，每页 1~3 组，优先 fade/fly/zoom；`notes` 同理。
