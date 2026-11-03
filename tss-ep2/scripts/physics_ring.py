"""第2話「太陽を囲む輪」用の計算(bpyをimportしない純Python)。
既存のphysics.pyに追記するか、このファイルをそのままimportする。
定数は TSS_定数表.md のとおり(SI単位)。
"""
import math

C = 299_792_458.0
GM_SUN = 1.32712440018e20
R_SUN = 6.957e8
AU = 1.495978707e11
RG = 2 * GM_SUN / C**2                      # 太陽のシュバルツシルト半径 約2.95 km
ARCSEC = math.pi / 180 / 3600


def deflection_angle(b):
    """光の曲がり角[rad] = 4GM/(c^2 b)"""
    return 4 * GM_SUN / (C**2 * b)


def focal_distance(b):
    """bを通る光が軸と交わる距離[m] = b^2 c^2 / (4GM)"""
    return b**2 * C**2 / (4 * GM_SUN)


def ring_radius(d):
    """探査機が太陽から距離d[m]にいるとき、輪になる光の通る位置b[m]。
    d = focal_distance(b) を b について解いたもの。b = sqrt(2 * rg * d)"""
    return math.sqrt(2 * RG * d)


def ring_geometry(d_au):
    """探査機の視点での輪と太陽の大きさ。d_au: 太陽からの距離[AU]"""
    d = d_au * AU
    b = ring_radius(d)
    return {
        "d_au": d_au,
        "ring_radius_m": b,
        "ring_over_rsun": b / R_SUN,                       # 太陽半径を1としたときの輪の半径
        "ring_angle_arcsec": math.degrees(b / d) * 3600,   # 探査機から見た輪の角半径
        "sun_angle_arcsec": math.degrees(R_SUN / d) * 3600,
        "gap_over_rsun": b / R_SUN - 1,                    # 太陽の縁から輪までの隙間(太陽半径比)
    }


def _selftest():
    # 検算1: 太陽の縁(b=Rsun)で曲がり角が約1.75秒角
    assert abs(deflection_angle(R_SUN) / ARCSEC - 1.7512) < 1e-3
    # 検算2: 同じbで焦点距離が約547.8AU
    assert abs(focal_distance(R_SUN) / AU - 547.8) < 0.2
    # 検算3: 2倍で約2191AU、3倍で約4930AU
    assert abs(focal_distance(2 * R_SUN) / AU - 2191) < 1
    assert abs(focal_distance(3 * R_SUN) / AU - 4930) < 2
    # 検算4(輪): 最短焦点距離の位置では、輪の半径は太陽半径に等しい
    g = ring_geometry(focal_distance(R_SUN) / AU)
    assert abs(g["ring_over_rsun"] - 1.0) < 1e-9
    # 検算5(輪): ring_radiusは focal_distance の逆関数
    b = 1.234 * R_SUN
    assert abs(ring_radius(focal_distance(b)) - b) < 1e-3
    # 検算6(輪): 650AUで輪は太陽半径の約1.09倍、角度は約1.6秒角(台本と同じ値)
    g = ring_geometry(650)
    assert abs(g["ring_over_rsun"] - 1.089) < 0.002
    assert abs(g["ring_angle_arcsec"] - 1.608) < 0.002
    assert abs(g["sun_angle_arcsec"] - 1.476) < 0.002
    # 検算7(輪): 1200AU(第1話の4aと同じ距離)で輪は太陽半径の約1.48倍
    g = ring_geometry(1200)
    assert abs(g["ring_over_rsun"] - 1.480) < 0.002
    print("selftest OK")
    for d in (547.8, 550, 650, 1000, 1200):
        g = ring_geometry(d)
        print("d=%6.1f AU 輪=%.3f Rsun(縁から%.1f%%外) 輪角=%.3f″ 太陽角=%.3f″"
              % (d, g["ring_over_rsun"], g["gap_over_rsun"] * 100,
                 g["ring_angle_arcsec"], g["sun_angle_arcsec"]))


if __name__ == "__main__":
    _selftest()
