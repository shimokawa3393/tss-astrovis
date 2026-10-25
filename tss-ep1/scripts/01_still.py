"""カットの最後の絵を静止画1枚にする（絵を確定させる段階。カメラワーク・アニメーションはまだ）。

実行:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python tss-ep1/scripts/01_still.py -- <カット> [解像度%]
  例: -- 3a 100
出力: tss-ep1/stillcheck/still_<カット>.png
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

import scene as sc

VFOV_DEG = 30

# sun_from_top: 太陽の中心の位置（画面の上からの割合）
# view_h_bu: 画面の高さ（BU）。軸方向も横方向も同じ倍率で写すので、見かけの曲がり角はカットによらない
LAYOUTS = {
    # 太陽〜5000AU を画面の上12%〜下85%に入れる（00_scale_check.py と同じ配置）
    "3a": dict(sun_from_top=0.12, view_h_bu=sc.bu(5000) / (0.85 - 0.12),
               b_ratios=sc.B_RATIOS, show_line=True),
    # 太陽の近くに寄る（太陽の半径170px）。光線は間引いて、太陽に近いほど大きく曲がるのを見せる。
    # 一番内側の光線は画面の下の方で軸に近づく（「レンズのように1点に集まりそう」と思わせ、3aでくつがえす）
    "2a": dict(sun_from_top=0.45, view_h_bu=sc.SUN_RADIUS_BU / 170 * sc.RESOLUTION[1],
               b_ratios=[1.0, 1.5, 2.0, 2.5, 3.0], show_line=False),
}


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cut = args[0] if args else "3a"
    percentage = int(args[1]) if len(args) > 1 else 100
    layout = LAYOUTS[cut]

    view_h = layout["view_h_bu"]
    top_z = layout["sun_from_top"] * view_h
    bottom_z = top_z - view_h
    px = view_h / sc.RESOLUTION[1]

    sc.clear_scene()
    sc.build_sun()
    sc.build_rays(top_z + 10 * px, bottom_z - 10 * px, 0.9 * px, layout["b_ratios"])
    sc.build_axis_and_line(top_z + 10 * px, bottom_z - 10 * px, 0.8 * px, 2.5 * px, layout["show_line"])
    sc.build_camera(top_z - view_h / 2, view_h, VFOV_DEG)

    scene = bpy.context.scene
    sc.setup_render(scene, percentage)
    f1_px = sc.ray_focus_bu(1.0) / px
    print(f"[{cut}] 1px={px * sc.AXIAL_AU_PER_BU:.3f}AU 太陽の円の半径={sc.SUN_DRAW_RADIUS_BU / px:.0f}px（b=R の {sc.SUN_DRAW_RADIUS_BU / sc.SUN_RADIUS_BU:.2f}倍） "
          f"548AUは太陽の中心から{f1_px:.0f}px（画面の上から{layout['sun_from_top'] * 100 + f1_px / sc.RESOLUTION[1] * 100:.0f}%） "
          f"見かけの曲がり角 b=R {sc.apparent_angle_deg(1):.1f}° b=3R {sc.apparent_angle_deg(3):.1f}°")

    out = os.path.join(sc.EP_DIR, "stillcheck", f"still_{cut}.png")
    scene.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[{cut}] {out} {time.time() - t:.1f}s")


main()
