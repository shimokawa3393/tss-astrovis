"""カットの絵を静止画1枚にする（絵を確定させる段階）。絵の配置は state.LAYOUTS、組み立ては build.build_frame。

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
from build import build_frame
from state import LAYOUTS


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = args[0] if args else "3a"
    percentage = int(args[1]) if len(args) > 1 else 100
    layout = LAYOUTS[name]

    log = build_frame(layout, percentage)
    print(f"[{name}] {log}")

    out = os.path.join(sc.EP_DIR, "stillcheck", f"still_{name}.png")
    scene = bpy.context.scene
    scene.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[{name}] {out} {time.time() - t:.1f}s")


main()
