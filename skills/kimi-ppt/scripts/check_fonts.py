#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_fonts.py — 字体可用性检查（本地导出用）

读 .pptd 声明的字体（或直接给字体名），按「规范名→实装名」映射翻译，
对照本机已装字体，输出：
  已装 / 缺失 / 本地可用替代。

跨平台：Windows 读字体注册表；Linux / macOS 扫系统字体目录
（fontconfig / Font Book 常用路径）。两者都取不到时打印提示，并按「全部缺失」处理。

用法:
  python check_fonts.py <deck.pptd>            # 从 .pptd 的 theme.textStyles 收集字体
  python check_fonts.py --fonts "MiSans" "Georgia"
  python check_fonts.py <deck.pptd> --list-missing   # 只列出缺失（供用户安装）
"""
import os, sys, re, argparse, json
import yaml

# 规范名 -> 实装名（与 reference/local-fonts.md 保持一致）
CANON_TO_INSTALLED = {
    "MiSans": "MiSans",
    "Noto Sans SC": "Noto Sans SC",
    "思源宋体": "思源宋体 CN",
    "Source Han Serif": "思源宋体 CN",
    "思源黑体 CN": "思源黑体 CN",
    "阿里妈妈刀隶体": "阿里妈妈刀隶体",
    "阿里妈妈东方大楷": "阿里妈妈东方大楷",
    "阿里妈妈数黑体": "阿里妈妈数黑体",
    "站酷文艺体": "站酷文艺体",
    "ZCOOL KuaiLe": "ZCOOL KuaiLe",
    "得意黑": "得意黑 斜体",
    "Smiley Sans": "得意黑 斜体",
    "飞波正点体": "飞波正点体",
    "霞鹜新致宋": "霞鹜新致宋＋",
    "LXGW Bright": "霞鹜文楷",
    "霞鹜文楷": "霞鹜文楷",
    "精品点阵体": "精品点阵体9×9 1.93 R",
    "Liter": "Liter",
    "HedvigLettersSans": "Hedvig Letters Sans",
    "Oranienbaum": "Oranienbaum",
    "QuattrocentoSans": "Quattrocento Sans",
    "Unna": "Unna",
    "Coda": "Coda",
    "Jersey15": "Jersey 15",
    "Jersey20Charted": "Jersey 20 Charted",
    "SortsMillGoudy": "Sorts Mill Goudy",
    "更纱黑体 SC": "更纱黑体 SC",
    "Sarasa Gothic": "更纱黑体 SC",
    "Microsoft YaHei": "Microsoft YaHei",
    "微软雅黑": "Microsoft YaHei",
    "SimHei": "SimHei",
    "黑体": "SimHei",
    "SimSun": "SimSun",
    "宋体": "SimSun",
    "FangSong": "FangSong",
    "仿宋": "FangSong",
    "KaiTi": "KaiTi",
    "楷体": "KaiTi",
}

# 缺失时的本地替代建议
ALTERNATIVES = {
    "SortsMillGoudy": ["Georgia", "Cambria"],
    "MiSans": ["更纱黑体 SC", "思源黑体 CN"],
    "Noto Sans SC": ["更纱黑体 SC", "思源黑体 CN"],
    "QuattrocentoSans": ["Century Gothic"],
    "HedvigLettersSans": ["Arial"],
    "Liter": ["Century Gothic", "Arial"],
    "Oranienbaum": ["Georgia", "Cambria"],
    "Unna": ["Cambria"],
    "Coda": ["Arial"],
    "Jersey15": ["Impact", "Franklin Gothic"],
    "Jersey20Charted": ["Impact", "Franklin Gothic"],
    "得意黑": ["思源黑体 CN", "更纱黑体 SC"],
    "精品点阵体": ["SimSun", "SimHei"],
}

# 系统字体目录：Windows 动态解析系统盘与用户目录；POSIX 走 fontconfig / Font Book 的常用路径
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


def _font_files():
    """递归列出系统字体目录里的字体文件名（族名匹配只需文件名）。"""
    names = []
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for _root, _dirs, files in os.walk(d, followlinks=True):
            names.extend(f for f in files if f.lower().endswith(FONT_EXTS))
    return names


def installed_families():
    """Windows：从注册表读已装字体族名集合（HKLM 全机 + HKCU 当前用户，合并去重；已归一化，去掉 (TrueType) 与后缀）。"""
    import winreg
    key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    fams = set()
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            k = winreg.OpenKey(root, key)
        except OSError:
            if root == winreg.HKEY_LOCAL_MACHINE:
                raise
            continue
        i = 0
        while True:
            try:
                name, _val, _t = winreg.EnumValue(k, i)
            except OSError:
                break
            norm = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
            if norm:
                fams.add(norm.casefold())
            i += 1
        winreg.CloseKey(k)
    return fams


def installed_families_posix():
    """POSIX 兜底：按字体文件名猜族名（不依赖 fontconfig，够用即可）。"""
    fams = set()
    for fn in _font_files():
        norm = os.path.splitext(fn)[0].strip().lower()
        norm = re.sub(
            r"[-_ ](regular|bold|italic|oblique|light|medium|black|heavy|thin|"
            r"semibold|demibold|extrabold|extralight|book|roman|condensed|"
            r"regularitalic|bolditalic)$", "", norm).strip()
        if norm:
            fams.add(norm)
    return fams

def normalize_req(name):
    # 归一化规范名，方便与注册表条目「全等/词边界前缀」匹配
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip().casefold()

def present(fam_set, req_installed):
    """判断实装名是否出现在本机。全等命中，或前缀匹配且边界为空格/连字符（容忍字重/变体后缀）。"""
    r = normalize_req(req_installed)
    if not r:
        return False
    for f in fam_set:
        fc = f.casefold()
        if fc == r:
            return True
        if fc.startswith(r) and len(fc) > len(r) and fc[len(r)] in (" ", "-"):
            return True
    return False

def collect_fonts(manifest):
    m = yaml.safe_load(open(manifest, encoding="utf-8"))
    theme = m.get("theme", {}) or {}
    fonts = set()
    for _k, st in (theme.get("textStyles", {}) or {}).items():
        ff = st.get("fontFamily")
        if isinstance(ff, dict):
            fonts.add(ff.get("latin")); fonts.add(ff.get("ea"))
        elif ff:
            fonts.add(ff)
    # 也扫页面内联 fontFamily
    base = os.path.dirname(os.path.abspath(manifest))
    for rel in m.get("pages", []):
        try:
            page = yaml.safe_load(open(os.path.join(base, rel), encoding="utf-8"))
        except Exception:
            continue
        for el in page.get("elements", []):
            c = el.get("content", {})
            ff = c.get("fontFamily")
            if isinstance(ff, dict):
                fonts.add(ff.get("latin")); fonts.add(ff.get("ea"))
            elif ff and isinstance(ff, str):
                fonts.add(ff)
    return {f for f in fonts if f}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?")
    ap.add_argument("--fonts", nargs="*", default=[])
    ap.add_argument("--list-missing", action="store_true")
    args = ap.parse_args()

    req = set(args.fonts or [])
    if args.manifest:
        req |= collect_fonts(args.manifest)
    req = {f for f in req if f}

    if not req:
        ap.error("没有可检查的字体：请提供 <deck.pptd> 或用 --fonts \"MiSans\" \"Georgia\" 指定字体名")

    try:
        fams = installed_families()
    except Exception as e:
        print(f"[warn] 读取字体注册表失败（{e}）；改用系统字体目录扫描", file=sys.stderr)
        fams = installed_families_posix()
    if not fams:
        print("[warn] 未能取到任何已装字体：下列字体将全部标记为缺失；"
              "请在目标机上安装字体，或用 --fonts 逐个核对", file=sys.stderr)
    installed, missing = [], []
    for c in sorted(req):
        inst = CANON_TO_INSTALLED.get(c, c)
        if present(fams, inst):
            installed.append((c, inst))
        else:
            missing.append(c)

    if args.list_missing:
        for c in missing:
            print(c)
        return 0

    print("=== 本机已装字体族数 ===", len(fams))
    print("\n[已装]")
    for c, inst in installed:
        print(f"  {c!r:28} -> {inst!r}")
    print("\n[缺失]")
    if missing:
        for c in missing:
            sug = ALTERNATIVES.get(c)
            if sug:
                print(f"  {c!r:28} 建议安装，或用替代 {', '.join(sug)}")
            else:
                print(f"  {c!r:28} 建议安装")
    else:
        print("  (无)")
    print("\n[本地可用替代建议]")
    for c in missing:
        sug = ALTERNATIVES.get(c)
        if sug:
            print(f"  {c!r} -> {sug}")
    if not missing:
        print("  (所需字体本机均已具备)")

if __name__ == "__main__":
    main()
