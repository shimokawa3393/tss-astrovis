"""ep1「太陽を望遠鏡にする」の計算層。bpy を import しない純Python。

光線は衝突パラメータ b（太陽の中心からの距離）で太陽の脇を通り、
曲がり角 α = 4GM/(c²b) だけ曲がって、焦点距離 F = b/α = b²c²/(4GM) で軸と交わる。
`python physics.py` で検算する（通らなければ描画に進まない）。
"""
import math

# 定数（SI）
G = 6.67430e-11          # 万有引力定数 [m^3 kg^-1 s^-2]（CODATA 2018）
C = 2.99792458e8         # 光速 [m/s]
GM_SUN = 1.32712440018e20  # 太陽の重力定数 [m^3/s^2]（IAU）
R_SUN = 6.957e8          # 太陽の公称半径 [m]（IAU 2015 B3）
AU = 1.495978707e11      # 天文単位 [m]（IAU 2012）
ARCSEC = math.pi / 180 / 3600

NEPTUNE_AU = 30.1        # 目盛りの目印だけに使う（台本「使う数値と出典」）


def deflection_angle(b):
    """衝突パラメータ b [m] の光線の曲がり角 [rad]。"""
    return 4 * GM_SUN / (C**2 * b)


def focal_distance(b):
    """衝突パラメータ b [m] の光線が軸と交わる距離 [m]（太陽の中心から）。"""
    return b**2 * C**2 / (4 * GM_SUN)


def to_au(m):
    return m / AU


def _check(name, value, expected, rel):
    ok = abs(value - expected) <= rel * expected
    print(f"{'OK ' if ok else 'NG '} {name}: {value:.6g}（期待 {expected:.6g} ±{rel:.1%}）")
    return ok


if __name__ == "__main__":
    a = deflection_angle(R_SUN)
    results = [
        _check("曲がり角 b=R [rad]", a, 8.49e-6, 0.005),
        _check("曲がり角 b=R [秒角]", a / ARCSEC, 1.75, 0.005),
        _check("焦点距離 b=R [AU]", to_au(focal_distance(R_SUN)), 547.8, 0.001),
        _check("焦点距離 b=2R [AU]", to_au(focal_distance(2 * R_SUN)), 2191, 0.001),
        _check("焦点距離 b=3R [AU]", to_au(focal_distance(3 * R_SUN)), 4930, 0.001),
        # 論文値（Patla & Nemiroff 548.30AU）とは定数の丸めの差だけ
        _check("論文値との差 b=R [AU]", to_au(focal_distance(R_SUN)), 548.30, 0.002),
    ]
    print("全部OK" if all(results) else "NGあり：描画に進まない")
    raise SystemExit(0 if all(results) else 1)
