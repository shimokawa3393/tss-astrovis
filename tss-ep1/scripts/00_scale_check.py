"""3a（点じゃなく線）の画面に、横方向の拡大率ごとの絵がどう収まるかを2Dで描く。

軸方向は実物比（太陽〜5000AUを画面の上12%〜下85%に入れる）。横方向だけ k 倍する。
出力: tss-ep1/stillcheck/scale_3a.png
"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from physics import R_SUN, deflection_angle, focal_distance, to_au

W, H = 1080, 1920
SUN_Y = 0.12 * H
AXIS_END_AU = 5000
PX_PER_AU = (0.85 - 0.12) * H / AXIS_END_AU
KS = [1e4, 3e4, 5e4]
B_RATIOS = [1 + 2 * i / 12 for i in range(13)]  # b = R〜3R を13本

OUT = Path(__file__).resolve().parent.parent / "stillcheck" / "scale_3a.png"

fig, axes = plt.subplots(1, len(KS), figsize=(4 * len(KS), 7.1), facecolor="black")
for ax, k in zip(axes, KS):
    ax.set_facecolor("black")
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    cx = W / 2
    sun_px = to_au(R_SUN) * k * PX_PER_AU
    # テロップの帯（中央よりやや上）と、避ける下端15%
    ax.add_patch(Rectangle((60, 0.30 * H), W - 120, 0.12 * H, fc="none", ec="#555", ls="--"))
    ax.add_patch(Rectangle((0, 0.85 * H), W, 0.15 * H, fc="#222"))
    ax.plot([cx, cx], [SUN_Y, H], color="#444", lw=0.6)
    for b_ratio in B_RATIOS:
        b = b_ratio * R_SUN
        x_off = b_ratio * sun_px
        f_y = SUN_Y + to_au(focal_distance(b)) * PX_PER_AU
        for side in (-1, 1):
            x0 = cx + side * x_off
            # 上から平行に来て、太陽の面で曲がり、焦点を通って先へ伸びる
            ax.plot([x0, x0], [0, SUN_Y], color="#ffd27a", lw=0.5, alpha=0.8)
            slope = -side * x_off / (f_y - SUN_Y)
            ax.plot([x0, x0 + slope * (H - SUN_Y)], [SUN_Y, H], color="#ffd27a", lw=0.5, alpha=0.8)
    ax.add_patch(Circle((cx, SUN_Y), sun_px, color="#ffb347"))
    f1 = SUN_Y + to_au(focal_distance(R_SUN)) * PX_PER_AU
    ax.plot(cx, f1, "o", color="white", ms=3)
    ang = math.degrees(math.atan(k * deflection_angle(R_SUN)))
    ax.set_title(f"k = {k:.0e}\n太陽半径 {sun_px:.0f}px / 曲がり角 {ang:.1f}°", color="white", fontsize=10,
                 fontname="Hiragino Sans")
    ax.text(cx + 20, f1, "548AU", color="white", fontsize=7, va="center")

fig.savefig(OUT, dpi=110, facecolor="black", bbox_inches="tight")
print(OUT)
