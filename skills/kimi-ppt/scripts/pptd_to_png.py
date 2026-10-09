#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pptd_to_png.py — 纯本地 .pptd -> 页面预览图 渲染器（Pillow，无浏览器/无 LibreOffice/无外网）
用于受限环境内的视觉 QA：按 .pptd 每页几何/配色/文字/字体画成一页 PNG，并合成一张 overview.jpg。

用法:
  python pptd_to_png.py <deck.pptd> [-o <outdir>] [--scale 2]
  输出: <outdir>/page_1.png ... /overview.jpg
"""
import os, sys, re, argparse, html
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps

# 系统字体目录（Windows 动态解析系统盘与用户目录；POSIX 走 fontconfig / Font Book 常用路径）
_WIN_FONTS = os.path.join(os.environ.get("SystemRoot", os.environ.get("WINDIR", r"C:\Windows")), "Fonts")
FONT_DIRS = [
    _WIN_FONTS,
    os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\Fonts") if sys.platform.startswith("win") else "",
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/.fonts"),
    os.path.expanduser("~/.local/share/fonts"),
    "/Library/Fonts",
    "/System/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
]
FONT_DIRS = [d for d in FONT_DIRS if d]
FONT_EXTS = (".ttf", ".ttc", ".otf", ".otc")

_SYSTEM_FONTS = None

# 规范名 -> 实装名（与 reference/local-fonts.md 一致；本地导出按实装名找文件）
CANON_TO_INSTALLED = {
    "MiSans": "MiSans", "Noto Sans SC": "Noto Sans SC", "思源宋体": "思源宋体 CN",
    "Source Han Serif": "思源宋体 CN", "阿里妈妈刀隶体": "阿里妈妈刀隶体",
    "阿里妈妈东方大楷": "阿里妈妈东方大楷", "阿里妈妈数黑体": "阿里妈妈数黑体",
    "站酷文艺体": "站酷文艺体", "ZCOOL KuaiLe": "ZCOOL KuaiLe",
    "得意黑": "得意黑 斜体", "Smiley Sans": "得意黑 斜体", "飞波正点体": "飞波正点体",
    "霞鹜新致宋": "霞鹜新致宋＋", "LXGW Bright": "霞鹜文楷", "霞鹜文楷": "霞鹜文楷",
    "精品点阵体": "精品点阵体9×9 1.93 R", "Liter": "Liter",
    "HedvigLettersSans": "Hedvig Letters Sans", "Oranienbaum": "Oranienbaum",
    "QuattrocentoSans": "Quattrocento Sans", "Unna": "Unna", "Coda": "Coda",
    "Jersey15": "Jersey 15", "Jersey20Charted": "Jersey 20 Charted",
    "SortsMillGoudy": "Sorts Mill Goudy", "更纱黑体 SC": "更纱黑体 SC",
    "Sarasa Gothic": "更纱黑体 SC", "Microsoft YaHei": "Microsoft YaHei",
    "微软雅黑": "Microsoft YaHei", "SimHei": "SimHei", "黑体": "SimHei",
    "SimSun": "SimSun", "宋体": "SimSun", "FangSong": "FangSong", "仿宋": "FangSong",
    "KaiTi": "KaiTi", "楷体": "KaiTi", "思源黑体 CN": "思源黑体 CN",
    "Century Gothic": "Century Gothic", "Bahnschrift": "Bahnschrift",
    "Georgia": "Georgia", "Cambria": "Cambria", "Constantia": "Constantia",
}


def _styles(path):
    """文件名里的字重/字形：(weight, italic)。weight 越大越粗。"""
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    tokens = set(re.split(r"[^a-z0-9]+", stem))
    if tokens & {"thin", "hairline"}:
        w = 100
    elif tokens & {"extralight", "ultralight"}:
        w = 200
    elif tokens & {"light"}:
        w = 300
    elif tokens & {"medium"}:
        w = 500
    elif tokens & {"semibold", "demibold", "demi"}:
        w = 600
    elif tokens & {"extrabold", "ultrabold"}:
        w = 800
    elif tokens & {"black", "heavy"}:
        w = 900
    elif tokens & {"bold", "bd"}:
        w = 700
    else:
        w = 400
    italic = bool(tokens & {"italic", "oblique", "it"}) or bool(tokens & {"bi", "bdit"})
    return w, italic


def _scan_fonts():
    """目录扫描兜底：[(family, path, weight, italic)]，族名由文件名推断。"""
    entries = []
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d, followlinks=True):
            for fn in files:
                if fn.lower().endswith(FONT_EXTS):
                    path = os.path.join(root, fn)
                    entries.append((os.path.splitext(fn)[0].strip().lower(), path, *_styles(path)))
    return entries


# 注册表族名里可辨认的字重/字形词；其余情况一律回退用文件名判断
_WEIGHT_WORDS = {
    "thin": 100, "hairline": 100, "extralight": 200, "ultralight": 200, "light": 300,
    "book": 350, "regular": 400, "normal": 400, "medium": 500, "demibold": 600,
    "semibold": 600, "demi": 600, "bold": 700, "extrabold": 800, "ultrabold": 800,
    "black": 900, "heavy": 900,
}
# 「X Bold & X UI Bold」这类合并条目：族名只取 & 前那段
_FAMILY_SPLIT = " & "
# 尾部字重/字形词不属于族名
_TAIL_STYLE = re.compile(
    r"\s+(thin|hairline|extralight|ultralight|light|book|regular|normal|medium|"
    r"demibold|semibold|demi|bold|extrabold|ultrabold|black|heavy|italic|oblique)$")


def _style_from_name(raw):
    """(family, weight, italic)：解析注册表条目名，识别不出字重返回 None 交给文件名兜底。"""
    name = raw.strip().lower()
    italic = bool(re.search(r"\b(italic|oblique)\b", name))
    if _FAMILY_SPLIT in name:          # 「X Bold & X UI Bold」→ 只取 & 前那段
        name = name.split(_FAMILY_SPLIT, 1)[0]
    weight = None
    fam = name
    m = _TAIL_STYLE.search(name)       # 尾部字重/字形词不属于族名
    if m:
        fam = name[:m.start()].strip()
        if m.group(1) in _WEIGHT_WORDS:
            weight = _WEIGHT_WORDS[m.group(1)]
        if m.group(1) in ("italic", "oblique"):
            italic = italic or True
    return fam.strip(), weight, italic


def system_fonts():
    """系统可用字体：[(family, path, weight, italic)]。

    Windows 先读字体注册表拿真实族名与字重（"微软雅黑 Bold & Microsoft YaHei UI Bold"
    → 族 `微软雅黑`、weight 700）；注册表读不到时退到目录扫描（族名由文件名推断）。
    同族同时保留常规与粗体，供调用方按需挑选。
    """
    global _SYSTEM_FONTS
    if _SYSTEM_FONTS is None:
        entries = []
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
            i = 0
            while True:
                try:
                    name, val, _t = winreg.EnumValue(k, i)
                except OSError:
                    break
                raw = re.sub(r"\s*\([^)]*\)\s*$", "", str(name)).strip().lower()
                fn = os.path.basename(str(val))
                path = next((os.path.join(d, fn) for d in FONT_DIRS
                             if fn and os.path.isfile(os.path.join(d, fn))), None)
                if raw and path:
                    fam, weight, italic = _style_from_name(raw)
                    file_weight, file_italic = _styles(fn)
                    if weight is None:
                        weight = file_weight
                    italic = italic or file_italic
                    entries.append((fam, path, weight, italic))
                i += 1
            winreg.CloseKey(k)
        except Exception:
            entries = []
        if not entries:
            entries = _scan_fonts()
        _SYSTEM_FONTS = _dedupe_fonts(entries)
    return _SYSTEM_FONTS


def _dedupe_fonts(entries):
    """同族同字重只留一条：ASCII 族名优先（避免 CJK/乱码变体抢位），文件名短者优先。"""
    best = {}
    for fam, path, weight, italic in entries:
        key = (fam, italic, weight)
        prev = best.get(key)
        if prev is None or (len(os.path.basename(path)), fam.isascii()) < \
                (len(os.path.basename(prev)), fam.isascii()):
            best[key] = path
    return sorted((fam, path, weight, italic) for (fam, italic, weight), path in best.items())


def _family_rank(fam, prefs):
    """族名偏好序（分组：匹配到的 pref 序号 → 是否 ASCII → 族名）；无匹配返回 (-1,) 表示不候选。"""
    for i, pref in enumerate(prefs):
        if pref in fam:
            return i, 0 if fam.isascii() else 1, fam
    return (-1,)


def default_font_file(bold=False):
    """兜底字体：优先常见 CJK 族（同族内按需挑粗/常规字形），再退到任意一个系统字体。

    偏好表刻意只用 ASCII 名（`yahei`/`simsun`…）：中文 Windows 的注册表常常同时给出
    ASCII 与本地化两套族名，ASCII 那套才能在跨区域机器上稳定命中。
    """
    entries = system_fonts()
    if not entries:
        return ""
    prefs = ("yahei", "noto sans cjk", "noto sans sc", "source han", "simhei",
             "simsun", "pingfang", "hiragino", "wenquanyi", "dejavu sans", "arial")
    fams = {f for f, _p, _w, _i in entries}
    ranked = sorted((r, f) for r, f in ((_family_rank(f, prefs), f) for f in fams)
                    if r[0] >= 0)
    fam = ranked[0][1] if ranked else sorted(fams)[0]
    cands = [(p, w, i) for f, p, w, i in entries if f == fam]
    plain = [c for c in cands if not c[2]] or cands     # 优先非斜体
    target = 700 if bold else 400
    plain.sort(key=lambda c: abs(c[1] - target))
    return plain[0][0]


def font_file_for(name, bold):
    """按(规范名)解析本机字体文件；找不到回退系统兜底字体。bold 优先 bold 字形。"""
    base_name = CANON_TO_INSTALLED.get((name or "").strip(), (name or "").strip())
    target = base_name.lower()
    entries = system_fonts()
    cands = [(fam, p, w, i) for fam, p, w, i in entries
             if fam == target or fam.startswith(target + " ") or fam.startswith(target + "&")]
    if not cands:
        cands = [(fam, p, w, i) for fam, p, w, i in entries if target and target in fam]
    if not cands:
        return default_font_file(bold)
    # 斜体最次、族名完全相等优先、字重按需（bold 取 700，否则取 400）
    want = 700 if bold else 400
    cands.sort(key=lambda c: (c[3], c[0] != target, abs(c[2] - want)))
    return cands[0][1]


# ---- 静默降级清单：凡未按 spec 渲染的元素/字段都记一条，结束统一打印 ----
DROPPED = []
_NOTE_SEEN = set()

def _note(element_type, element_id, reason):
    key = (str(element_type), str(element_id), reason)
    if key in _NOTE_SEEN:
        return
    _NOTE_SEEN.add(key)
    DROPPED.append(key)

def _crop_fractions(crop):
    """ImageCrop 四边比例（缺省 0）。负值（outset）或退化源区返回 None，由调用方降级。"""
    if not crop:
        return 0.0, 0.0, 0.0, 0.0
    l = float(crop.get("left", 0) or 0)
    t = float(crop.get("top", 0) or 0)
    r = float(crop.get("right", 0) or 0)
    b = float(crop.get("bottom", 0) or 0)
    if min(l, t, r, b) < 0 or l + r >= 1 or t + b >= 1:
        return None
    return l, t, r, b

# 预览轨支持的形状集（其余名字退矩形并计入 dropped）
_PREVIEW_SHAPES = ("rect", "ellipse", "circle", "roundRect", "triangle", "diamond", "chevron")

def _rotated_layer(bw, bh, angle, fn):
    """在 bounds 尺寸透明层上绘制后绕中心旋转（PIL 逆时针为正，PPT 为顺时针）。"""
    layer = Image.new("RGBA", (max(1, int(bw)), max(1, int(bh))), (0, 0, 0, 0))
    fn(layer)
    return layer.rotate(-float(angle), expand=False)

def resolve_color(c, theme_colors, fallback=None):
    if c is None:
        return "#" + fallback if fallback else None
    s = str(c).strip()
    if s.startswith("$"):
        key = s[1:]
        if key in theme_colors:
            return "#" + theme_colors[key].replace("#", "")
        return "#" + {"black": "111111", "white": "FFFFFF", "red": "E30613",
                      "yellow": "FFC300", "blue": "0066B3", "gray": "F4F4F2",
                      "text": "222222", "accent": "FFC300", "primary": "0066B3",
                      "secondary": "555555"}.get(key, fallback or "000000")
    return "#" + s.replace("#", "")

def plain_paragraphs(text):
    """把 content.text 转成纯文本段落列表，去掉 HTML 标签，保留换行。"""
    if not text:
        return []
    text = html.unescape(str(text))
    text = re.sub(r"</?p[^>]*>", "\n", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            out.append(line)
    return out

def shape_pts(kind, x, y, w, h, border_ex, scale):
    """返回 PIL 多边形绘制所需的点（矩形/三角/菱形等）。"""
    if kind == "triangle":
        return [(x + w / 2, y), (x, y + h), (x + w, y + h)]
    if kind == "diamond":
        return [(x + w / 2, y), (x + w, y + h / 2), (x + w / 2, y + h), (x, y + h / 2)]
    if kind == "chevron":
        return [(x, y), (x + w * 0.7, y), (x + w, y + h / 2), (x + w * 0.7, y + h), (x, y + h), (x + w * 0.3, y + h / 2)]
    if kind == "star5":
        return None  # 复杂星形，退回矩形
    return None      # 退回矩形

def _draw_shape_range(d, el, colors, scale, ox, oy):
    """在 (ox, oy) 处画一个 shape 元素（本地轨道形状子集）。"""
    sn = el.get("shapeName", "rect")
    bw, bh = [v * scale for v in el.get("bounds", [0, 0, 100, 40])[2:4]]
    x, y = ox, oy
    if sn == "custom":
        # 与 pptx 轨一致：灰描边空心占位
        d.rectangle([x, y, x + bw, y + bh], outline="#888888", width=max(1, int(scale)))
        return
    fill = el.get("fill")
    if not fill:
        fc = None                                  # 无填充（pptd.md: default not applied）
    elif fill.get("type", "solid") == "solid":
        fc = resolve_color(fill.get("color"), colors)
    elif fill.get("type") == "gradient":
        stops = fill.get("stops") or []
        fc = resolve_color(stops[0].get("color") if stops else None, colors)
    else:
        fc = None
    border = el.get("border") or {}
    bc = resolve_color(border.get("color"), colors, "000000") if border else None
    bwd = max(1, int(float(border.get("width", 1)) * scale)) if border else 0
    if sn in ("ellipse", "circle"):
        d.ellipse([x, y, x + bw, y + bh], fill=fc, outline=bc, width=bwd)
    elif sn == "roundRect":
        d.rounded_rectangle([x, y, x + bw, y + bh], radius=int(min(bw, bh) * 0.1),
                            fill=fc, outline=bc, width=bwd)
    elif sn in ("triangle", "diamond", "chevron"):
        pts = shape_pts(sn, x, y, bw, bh, border, scale)
        if pts:
            d.polygon(pts, fill=fc, outline=bc)
        else:
            d.rectangle([x, y, x + bw, y + bh], fill=fc, outline=bc, width=bwd)
    else:
        d.rectangle([x, y, x + bw, y + bh], fill=fc, outline=bc, width=bwd)

def _draw_line_range(d, el, colors, scale, ox, oy):
    """在 (ox, oy) 处画 line 元素：points 从 viewBox 坐标系映射到 bounds，取首末点。"""
    bw, bh = [v * scale for v in el.get("bounds", [0, 0, 100, 40])[2:4]]
    pts = (el.get("points") or "0,0 1,1").split()
    p0 = [float(a) for a in pts[0].split(",")]
    p1 = [float(a) for a in pts[-1].split(",")]
    vb = el.get("viewBox")
    if isinstance(vb, (list, tuple)) and len(vb) == 2 and float(vb[0]) and float(vb[1]):
        x0, y0 = ox + p0[0] / float(vb[0]) * bw, oy + p0[1] / float(vb[1]) * bh
        x1, y1 = ox + p1[0] / float(vb[0]) * bw, oy + p1[1] / float(vb[1]) * bh
    else:
        x0, y0 = ox + p0[0] * scale, oy + p0[1] * scale
        x1, y1 = ox + p1[0] * scale, oy + p1[1] * scale
    lc = resolve_color((el.get("border") or {}).get("color"), colors, "000000")
    d.line([(x0, y0), (x1, y1)], fill=lc,
           width=max(1, int(float((el.get("border") or {}).get("width", 1)) * scale)))

def _emit(img, x, y, bw, bh, angle, paint):
    """把 paint(container, ox, oy) 落图；rotation ≠ 0 时画进透明层绕中心旋转后贴回。"""
    if angle:
        layer = _rotated_layer(bw, bh, angle, lambda L: paint(L, 0, 0))
        img.paste(layer, (int(x), int(y)), layer)
    else:
        paint(img, x, y)

def draw_text(draw, el, theme, scale, colors, ox, oy):
    c = el.get("content", {})
    bw, bh = [v * scale for v in el.get("bounds", [0, 0, 100, 40])[2:4]]
    x, y = ox, oy
    tc = theme.get("textStyles", {})
    base = {}
    st = c.get("style")
    if isinstance(st, str) and st.startswith("$"):
        base = tc.get(st[1:], {}) or {}
    font_size = (c.get("fontSize") or base.get("fontSize") or 18) * scale
    color = resolve_color(c.get("color") or base.get("color") or "$text", colors, "222222")
    bold = bool(c.get("bold", base.get("bold", False)))
    fname = c.get("fontFamily") or base.get("fontFamily") or "Microsoft YaHei"
    if isinstance(fname, dict):
        latin = fname.get("latin", "Arial"); ea = fname.get("ea", latin)
    else:
        latin = ea = fname
    lh = c.get("lineHeight", base.get("lineHeight", 1)) or 1
    align = c.get("align") or ["left", "top"]
    lines = plain_paragraphs(c.get("text", ""))
    # 有中文用 ea（须支持 CJK），纯西文用 latin；都按实装名解析
    joined = "".join(lines)
    has_cjk = any(ord(ch) > 0x2E80 for ch in joined)
    chosen = ea if has_cjk else latin
    font_path = font_file_for(chosen, bold)
    try:
        font = ImageFont.truetype(font_path, int(font_size))
    except Exception:
        try:
            font = ImageFont.truetype(default_font_file(bold), int(font_size))
        except Exception:
            font = ImageFont.load_default()
    line_h = int(font_size * lh)
    # 总文本高
    total_h = line_h * max(1, len(lines))
    # 垂直定位
    if align[1] == "middle":
        ty = y + (bh - total_h) / 2
    elif align[1] == "bottom":
        ty = y + bh - total_h
    else:
        ty = y
    for i, line in enumerate(lines):
        lw = draw.textlength(line, font=font)
        if align[0] == "center":
            tx = x + (bw - lw) / 2
        elif align[0] == "right":
            tx = x + bw - lw
        else:
            tx = x
        draw.text((tx, ty + i * line_h), line, font=font, fill=color)
    return

def render_page(page, theme, colors, size, scale, page_no):
    w, h = size
    W, H = int(w * scale), int(h * scale)
    img = Image.new("RGB", (W, H), "#FFFFFF")
    drw = ImageDraw.Draw(img)
    # 背景
    bkg = page.get("background", {}) or {}
    if bkg.get("type", "solid") == "solid":
        bc = resolve_color(bkg.get("color"), colors, "FFFFFF")
        drw.rectangle([0, 0, W, H], fill=bc)
    elif bkg.get("type") == "gradient":
        stops = bkg.get("stops") or []
        if stops:
            gc = resolve_color(stops[0].get("color"), colors, "FFFFFF")
            drw.rectangle([0, 0, W, H], fill=gc)
    if page.get("notes"):
        _note("page", str(page_no - 1), "speaker notes not supported in preview")
    if page.get("animations"):
        _note("page", str(page_no - 1), "animations not supported in preview")
    # 元素（按顺序 = 层序）
    for el in page.get("elements", []):
        et = el.get("elementType")
        eid = el.get("elementId", "?")
        x, y, bw, bh = [v * scale for v in el.get("bounds", [0, 0, 100, 40])]
        angle = float(el.get("rotation") or 0)
        if el.get("opacity") not in (None, 1, 1.0):
            _note(et, eid, "opacity not supported in preview")
        fl = el.get("flip")
        if fl and any(fl):
            _note(et, eid, "flip not supported in preview")
        if et == "shape":
            sn = el.get("shapeName", "rect")
            if sn not in _PREVIEW_SHAPES:
                _note(et, eid, f'shapeName "{sn}" rendered as rect in preview')
            if (el.get("fill") or {}).get("type") == "image":
                _note(et, eid, "image fill on shape not supported in preview")
            _emit(img, x, y, bw, bh, angle,
                  lambda C, ox, oy: _draw_shape_range(ImageDraw.Draw(C), el, colors, scale, ox, oy))
        elif et == "text":
            _emit(img, x, y, bw, bh, angle,
                  lambda C, ox, oy: draw_text(ImageDraw.Draw(C), el, theme, scale, colors, ox, oy))
        elif et == "line":
            if len((el.get("points") or "0,0 1,1").split()) > 2:
                _note(et, eid, "control points degraded to straight segment")
            _emit(img, x, y, bw, bh, angle,
                  lambda C, ox, oy: _draw_line_range(ImageDraw.Draw(C), el, colors, scale, ox, oy))
        elif et == "image":
            src = el.get("src")
            path = os.path.join(os.path.dirname(manifest), src) if src else None
            if path and os.path.isfile(path):
                fit = el.get("fit")
                mode = fit.get("mode") if isinstance(fit, dict) else None
                mode = mode or "cover"
                if mode not in ("cover", "contain", "fill"):
                    _note(et, eid, f'unknown fit mode "{mode}" rendered as cover')
                    mode = "cover"
                if el.get("cropShape"):
                    _note(et, eid, "cropShape not supported in preview")
                crop = el.get("crop")
                fr = _crop_fractions(crop)
                if fr is None:
                    if crop:
                        _note(et, eid, "crop outset not supported in preview; crop ignored")
                    fr = (0.0, 0.0, 0.0, 0.0)

                def paint_im(C, ox, oy, path=path, mode=mode, fr=fr, bw=bw, bh=bh):
                    im = Image.open(path).convert("RGB")
                    iw0, ih0 = im.size
                    if any(fr):
                        im = im.crop((int(iw0 * fr[0]), int(ih0 * fr[1]),
                                      iw0 - int(iw0 * fr[2]), ih0 - int(ih0 * fr[3])))
                    tw, th = max(1, int(bw)), max(1, int(bh))
                    if mode == "contain":
                        k = min(bw / im.width, bh / im.height)
                        nw, nh = max(1, int(im.width * k)), max(1, int(im.height * k))
                        C.paste(im.resize((nw, nh), Image.LANCZOS),
                                (int(ox + (bw - nw) / 2), int(oy + (bh - nh) / 2)))
                    elif mode == "fill":
                        C.paste(im.resize((tw, th), Image.LANCZOS), (int(ox), int(oy)))
                    else:
                        C.paste(ImageOps.fit(im, (tw, th), method=Image.LANCZOS), (int(ox), int(oy)))

                try:
                    _emit(img, x, y, bw, bh, angle, paint_im)
                except Exception:
                    pass
            # 远程/缺失图跳过（SKILL.md 声明的降级）
        elif et == "icon":
            _note(et, eid, "icon elements are not rendered in preview")
        elif et == "table":
            _note(et, eid, "table elements are not rendered in preview")
        elif et == "chart":
            _note(et, eid, "chart elements are not rendered in preview")
        else:
            _note(et, eid, "unknown elementType not rendered in preview")
    out = os.path.join(outdir, f"page_{page_no}.png")
    img.save(out)
    return out, img

def main():
    global manifest, outdir
    DROPPED.clear()
    _NOTE_SEEN.clear()
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("-o", "--output")
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()
    manifest = os.path.abspath(args.manifest)
    base = os.path.dirname(manifest)
    outdir = args.output or os.path.join(base, ".preview")
    os.makedirs(outdir, exist_ok=True)
    m = yaml.safe_load(open(manifest, encoding="utf-8"))
    size = m.get("size", [960, 540])
    theme = m.get("theme", {}) or {}
    colors = theme.get("colors", {}) or {}
    pages = m.get("pages") or []
    if not pages:
        sys.exit("pages 列表必须非空：deck 至少要有一页")
    imgs = []
    for i, rel in enumerate(pages, 1):
        page = yaml.safe_load(open(os.path.join(base, rel), encoding="utf-8"))
        out, img = render_page(page, theme, colors, size, args.scale, i)
        imgs.append((rel, img))
        print("rendered", out)
    # 合成 overview
    if imgs:
        gap = 20
        W = max(im.width for _, im in imgs)
        H = sum(im.height for _, im in imgs) + gap * (len(imgs) + 1)
        ov = Image.new("RGB", (W, H), "#DDDDDD")
        yoff = gap
        for _, im in imgs:
            ov.paste(im, (0, yoff)); yoff += im.height + gap
        ovp = os.path.join(outdir, "overview.jpg")
        ov.save(ovp, quality=92)
        print("overview", ovp)
    for tp, eid, reason in DROPPED:
        print(f"dropped: {tp}/{eid}: {reason}", file=sys.stderr)
    print(f"dropped total: {len(DROPPED)}", file=sys.stderr)

if __name__ == "__main__":
    main()
