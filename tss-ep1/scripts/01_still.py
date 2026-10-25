"""カットの絵を静止画1枚にする（絵を確定させる段階。カメラワーク・アニメーションはまだ）。

実行:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python tss-ep1/scripts/01_still.py -- <絵> [解像度%]
  例: -- 3a 100
出力: tss-ep1/stillcheck/still_<絵>.png
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

import scene as sc

VFOV_DEG = 30

# anchor_au が画面の上から anchor_from_top の位置に来る。view_h_bu は画面の高さ（BU）。
# 軸方向も横方向も同じ倍率で写すので、見かけの曲がり角はカットによらない。
# sun_radius_px を指定すると太陽をその大きさの記号にする（省くと一番内側の光線に接する大きさ）。
_3B = dict(view_h_bu=sc.bu(200), anchor_from_top=0.55,
           # 548AUの時点で画面に入るのは b < 約1.12R の光線だけなので、縁の近くを細かく拾う
           b_ratios=[1 + 0.02 * i for i in range(7)], show_line=True,
           sun_radius_px=45, ruler_au=800, neptune=True)
LAYOUTS = {
    # 太陽〜5000AU を画面の上12%〜下85%に入れる（00_scale_check.py と同じ配置）
    "3a": dict(anchor_au=0, anchor_from_top=0.12, view_h_bu=sc.bu(5000) / (0.85 - 0.12),
               b_ratios=sc.B_RATIOS, show_line=True),
    # 太陽の近くに寄る。光線は間引いて、太陽に近いほど大きく曲がるのを見せる。
    # 一番内側の光線は画面の下の方で軸に近づく（「レンズのように1点に集まりそう」と思わせ、3aでくつがえす）
    "2a": dict(anchor_au=0, anchor_from_top=0.45, view_h_bu=sc.SUN_RADIUS_BU / 170 * sc.RESOLUTION[1],
               b_ratios=[1.0, 1.5, 2.0, 2.5, 3.0], show_line=False),
    # 3b: 軸に沿って下る。窓は200AU、いまの深さは画面の上から55%の高さ
    "3b_start": dict(_3B, anchor_au=0),
    "3b_neptune": dict(_3B, anchor_au=30.1),
    "3b": dict(_3B, anchor_au=548),
}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = args[0] if args else "3a"
    percentage = int(args[1]) if len(args) > 1 else 100
    layout = LAYOUTS[name]

    view_h = layout["view_h_bu"]
    top_z = -sc.bu(layout["anchor_au"]) + layout["anchor_from_top"] * view_h
    bottom_z = top_z - view_h
    px = view_h / sc.RESOLUTION[1]
    margin = 10 * px

    sc.clear_scene()
    sun_r = layout["sun_radius_px"] * px if "sun_radius_px" in layout else None
    sc.build_sun(sun_r)
    sc.build_rays(max(top_z, 0) + margin, bottom_z - margin, 0.9 * px, layout["b_ratios"])
    sc.build_axis_and_line(top_z + margin, bottom_z - margin, 0.8 * px, 2.5 * px, layout["show_line"])
    if "ruler_au" in layout:
        sc.build_ruler(layout["ruler_au"], px)
    if layout.get("neptune"):
        sc.build_neptune(20 * px, -150 * px, 26 * px)
    sc.build_camera(top_z - view_h / 2, view_h, VFOV_DEG)

    scene = bpy.context.scene
    sc.setup_render(scene, percentage)
    print(f"[{name}] 1px={px * sc.AXIAL_AU_PER_BU:.3f}AU 太陽の円の半径={(sun_r or sc.SUN_DRAW_RADIUS_BU) / px:.0f}px "
          f"見かけの曲がり角 b=R {sc.apparent_angle_deg(1):.1f}° b=3R {sc.apparent_angle_deg(3):.1f}°")

    out = os.path.join(sc.EP_DIR, "stillcheck", f"still_{name}.png")
    scene.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[{name}] {out} {time.time() - t:.1f}s")


main()
