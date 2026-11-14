"""touchHLE 参数白名单（交付件 5/8）。
来源：touchHLE 官方 OPTIONS_HELP.txt（trunk）。
铁律：只放行官方文档公开参数；未知键直接拒绝（raise），不做"透传"。
"""
from __future__ import annotations


class WhitelistError(ValueError):
    pass


# 布尔开关（无值），全部来自官方 OPTIONS_HELP.txt
ALLOWED_BOOL = {
    "--fullscreen",
    "--headless",
    "--no-error-popup",
    "--print-fps",
    "--force-composition",
    "--ignore-gl-errors",
    "--allow-network-access",
    "--upside-down",
    "--landscape-left",
    "--landscape-right",
    "--disable-analog-stick-tilt-controls",
}

# 枚举值（值域封闭）
ALLOWED_ENUM = {
    "--device-family": {"iphone", "ipad"},
    "--gles1": {"gles1_on_gl2", "gles1_native"},
}

# 数值参数: 键 -> (最小值, 最大值)；None 表示不限
ALLOWED_NUM = {
    "--scale-hack": (1, None),
    "--deadzone": (0.0, 1.0),
    "--x-tilt-range": (None, None),
    "--y-tilt-range": (None, None),
    "--x-tilt-offset": (None, None),
    "--y-tilt-offset": (None, None),
}


def validate(extra: dict) -> list[str]:
    """extra(dict) → 合法 argv 片段列表；未知键 / 越域值 → WhitelistError。"""
    out: list[str] = []
    for k, v in (extra or {}).items():
        if not isinstance(k, str) or not k.startswith("--"):
            raise WhitelistError(f"unknown/invalid flag: {k!r}")
        if k in ALLOWED_BOOL:
            if v not in (True, False, None):
                raise WhitelistError(f"{k} must be flag-only")
            if v:
                out.append(k)
        elif k in ALLOWED_ENUM:
            domain = ALLOWED_ENUM[k]
            if v not in domain:
                raise WhitelistError(f"{k} must be one of {sorted(domain)}, got {v!r}")
            out.append(f"{k}={v}")
        elif k in ALLOWED_NUM:
            lo, hi = ALLOWED_NUM[k]
            try:
                x = float(v)
            except (TypeError, ValueError):
                raise WhitelistError(f"{k} must be a number")
            if lo is not None and x < lo:
                raise WhitelistError(f"{k} below {lo}")
            if hi is not None and x > hi:
                raise WhitelistError(f"{k} above {hi}")
            out.append(f"{k}={int(x) if x == int(x) else x}")
        elif k == "--preferred-languages":
            codes = str(v).replace(" ", "").split(",")
            if not all(2 <= len(c) <= 3 for c in codes):
                raise WhitelistError("--preferred-languages must be ISO 639 codes")
            out.append(f"{k}={','.join(codes)}")
        else:
            raise WhitelistError(f"flag not in whitelist: {k}")
    return out
