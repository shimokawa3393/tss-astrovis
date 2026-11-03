"""カットの絵を静止画1枚にする（絵を確定させる段階）。配置は state.LAYOUTS、組み立ては build.build_frame。

実行:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python tss-ep2/scripts/01_still.py -- <絵> [解像度%]
  例: -- c01 50
出力: tss-ep2/stillcheck/still_<絵>.png
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

from build import build_frame
from common import EP_DIR
from state import LAYOUTS


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    name = args[0] if args else "c01"
    percentage = int(args[1]) if len(args) > 1 else 100

    log = build_frame(LAYOUTS[name], percentage)
    print(f"[{name}] {log}")

    out = os.path.join(EP_DIR, "stillcheck", f"still_{name}.png")
    bpy.context.scene.render.filepath = out
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[{name}] {out} {time.time() - t:.1f}s")


main()
