"""3a（でも集まるのは / 点じゃなく線）の最後の絵を静止画1枚にする。

太陽〜5000AU を画面の上12%〜下85%に入れる（00_scale_check.py と同じ配置）。
実行:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python tss-ep1/scripts/01_still_3a.py -- [解像度%]
出力: tss-ep1/stillcheck/still_3a.png
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

import scene as sc

SUN_FROM_TOP = 0.12
AXIS_END_AU = 5000
AXIS_END_FROM_TOP = 0.85
VFOV_DEG = 30


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    percentage = int(args[0]) if args else 100

    view_h = sc.bu(AXIS_END_AU) / (AXIS_END_FROM_TOP - SUN_FROM_TOP)
    top_z = SUN_FROM_TOP * view_h
    bottom_z = top_z - view_h
    px = view_h / sc.RESOLUTION[1]

    sc.clear_scene()
    sc.build_sun()
    sc.build_rays(top_z + 10 * px, bottom_z - 10 * px, 0.9 * px)
    sc.build_axis_and_line(top_z + 10 * px, bottom_z - 10 * px, 0.8 * px, 2.5 * px)
    sc.build_camera(top_z - view_h / 2, view_h, VFOV_DEG)

    scene = bpy.context.scene
    sc.setup_render(scene, percentage)
    print(f"[3a] 1px={px * sc.AXIAL_AU_PER_BU:.2f}AU 太陽半径={sc.SUN_RADIUS_BU / px:.0f}px "
          f"見かけの曲がり角 b=R {sc.apparent_angle_deg(1):.1f}° b=3R {sc.apparent_angle_deg(3):.1f}°")

    out = os.path.join(sc.EP_DIR, "stillcheck", "still_3a.png")
    scene.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[3a] {out} {time.time() - t:.1f}s")


main()
