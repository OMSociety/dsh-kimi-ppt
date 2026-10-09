# 本地导出字体（以运行时实装为准）

> 本文件是**本地导出**的字体基准：**设计选型读 `fonts.md`**（规范名、是否风格化），**本地落地命中读本文件**——`fonts.md` 的规范名表达设计意图、供桌面增强导出用，本地导出必须写实装名：`fontFamily` 填下表的「实际安装名」，或让导出器按下表映射（规范名 ≠ 实装名时以实装名为准）。
>
> 下表只是常见实装名的参考：以 `SKILL.md`「三、字体核对」里 `check_fonts.py` 在本机的输出为准，确需长期复用时再把自己机器上的结果回写本表。
>
> 字体未装时的处理动作同样见 `SKILL.md`「三、字体核对（防豆腐块）」，本文件只给映射与用途。

## 规范名 → 实际安装名 映射

### 中文
| 规范名（fonts.md/设计用） | 典型实装名 | 免费商用 | 说明 |
|---|---|---|---|
| MiSans | `MiSans` | ✅ 小米官方全球免费商用 | 默认中文首选；多字重建议安装 |
| Noto Sans SC | `Noto Sans SC` | ✅ | 别名：`思源黑体 CN`（同为 Source Han Sans） |
| Source Han Serif / 思源宋体 | `思源宋体 CN` | ✅ | 别名：`Noto Serif SC` |
| 阿里妈妈刀隶体 | `阿里妈妈刀隶体` | ✅ 阿里官方免费商用 | |
| 阿里妈妈东方大楷 | `阿里妈妈东方大楷` | ✅ | |
| 阿里妈妈数黑体 | `阿里妈妈数黑体` | ✅ | 常见为 Bold 字重 |
| 站酷文艺体 | `站酷文艺体` | ✅ ZCOOL | 同类备选 `站酷高端黑`、`站酷快乐体2016修订版` |
| 得意黑 (Smiley Sans) | `得意黑 斜体` | ✅ | 官方预设仅斜体字形（符合其设计） |
| 飞波正点体 | `飞波正点体` | ✅（免费商用） | |
| 霞鹜新致宋 | `霞鹜新致宋＋` | ✅ LXGW | 注：名字带「＋」 |

### 中英混排（Mixed CJK–Latin）
| 规范名 | 典型实装名 | 免费商用 | 说明 |
|---|---|---|---|
| 精品点阵体 | `精品点阵体9×9…`（1.93 R/B、方格/光晕/渐层/立体/圆形版、港版） | ✅ | 用 `精品点阵体9×9 1.93 R` 作默认 |
| LXGW Bright | `霞鹜文楷` | ✅ LXGW | 霞鹜文楷家族 |
| ZCOOL KuaiLe | `ZCOOL KuaiLe` | ✅ ZCOOL | |

### 英文
| 规范名 | 典型实装名 | 免费商用 | 说明 |
|---|---|---|---|
| Liter | `Liter` | ✅ OFL | |
| HedvigLettersSans | `Hedvig Letters Sans` | ✅ | 注意空格 |
| Oranienbaum | `Oranienbaum` | ✅ OFL | |
| QuattrocentoSans | `Quattrocento Sans` | ✅ OFL | 注意空格 |
| Unna | `Unna` | ✅ OFL | |
| Coda | `Coda` | ✅ OFL | |
| Jersey15 | `Jersey 15` | ✅ OFL | |
| Jersey20Charted | `Jersey 20 Charted` | ✅ OFL | |
| SortsMillGoudy | `Sorts Mill Goudy`（注意空格） | ✅ OFL | （SortsMillGoudy-Regular/Italic.ttf） |

### 本地常见补充（系统预装 / 免费商用）
| 字体 | 用途建议 |
|---|---|
| `Century Gothic` / `Bahnschrift` | **几何感**，适合 Bauhaus/设计标题（比 Arial 更对味） |
| `Franklin Gothic` / `Impact` / `Rockwell` | 展示/强调标题 |
| `Georgia` / `Cambria` / `Constantia` | 学术衬线正文 |
| `Microsoft YaHei`（微软雅黑） | 默认中文回退 |
| `SimHei` `SimSun` `FangSong` `KaiTi` | 系统标准中文 |
| `更纱黑体 SC`（=Sarasa Gothic J/K） | MiSans 类似，备选中文黑体 |

> 这一组多为 Windows 中文系统预装；其他平台按 `check_fonts.py` 的输出替换。

## 检查命令（脚本 `scripts/check_fonts.py`）

按「规范名 → 实装名」映射翻译后，对照本机已装字体，输出 `已装 / 缺失 / 本地可用替代`：

```bash
python scripts/check_fonts.py <deck.pptd>                  # 从 .pptd 的 theme.textStyles + 页面内联 fontFamily 收集字体
python scripts/check_fonts.py --fonts "MiSans" "Georgia"   # 直接给字体名检查
python scripts/check_fonts.py <deck.pptd> --list-missing   # 只列出缺失（供用户安装）
```
