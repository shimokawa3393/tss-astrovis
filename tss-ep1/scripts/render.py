"""カット単位のレンダー（PNG連番）。状態は state.scene_state、組み立ては build.build_frame（静止画と共有）。

実行（1カット = 1コマンド。TSS 制作設計書 第3章）:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python tss-ep1/scripts/render.py -- --cut 3a
  ... -- --cut 3a --range 361 450 --draft
  ... -- --all --preview
  --preview: 半分の解像度で preview_frames へ。--draft: 4分の1・低画質・2フレームに1枚で draft_frames へ（動きの確認用）
  すでにあるフレームは飛ばす（途中で止まっても続きから）。--force で撮り直す。
出力: tss-ep1/frames/ep1_<フレーム>.png
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

import scene as sc
from build import build_frame
from cuts import CUT_BY_ID, RENDERED_CUTS
from state import scene_state

DRAFT_STEP = 2


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--cut", choices=RENDERED_CUTS)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--range", nargs=2, type=int)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    if not args.cut and not args.all:
        ap.error("--cut か --all を指定する")

    out_dir = os.path.join(sc.EP_DIR, "draft_frames" if args.draft else "preview_frames" if args.preview else "frames")
    os.makedirs(out_dir, exist_ok=True)
    percentage = 25 if args.draft else 50 if args.preview else 100
    step = DRAFT_STEP if args.draft else 1

    jobs = []
    for cut in ([args.cut] if args.cut else RENDERED_CUTS):
        c = CUT_BY_ID[cut]
        start, end = args.range if args.range else (c["start"], c["end"])
        start, end = max(start, c["start"]), min(end, c["end"])
        first = start + (-(start - 1) % step)  # ドラフトは奇数フレームにそろえる（カットをまたいでも同じ間隔）
        jobs += [(cut, f) for f in range(first, end + 1, step)]

    t_all = time.time()
    done = 0
    for cut, frame in jobs:
        path = os.path.join(out_dir, f"ep1_{frame:04d}.png")
        if os.path.exists(path) and not args.force:
            continue
        t = time.time()
        log = build_frame(scene_state(frame, cut), percentage)
        scene = bpy.context.scene
        if args.draft:
            scene.eevee.taa_render_samples = 8
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        done += 1
        print(f"[render] {cut} {frame} {time.time() - t:.1f}s {log}", flush=True)
    print(f"[render] {done}枚 {time.time() - t_all:.0f}s → {out_dir}")


main()
