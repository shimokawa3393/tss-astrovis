"""PNG連番とテロップを mp4 にまとめる（このマシンに ffmpeg は無いので Blender の VSE。ep4 の 04_encode_video.py と同じ方式）。

テロップは cuts.py（文言とカット内のフレーム）。上から約11%に、行ごとに少しずつ遅れて出る（ステップフェード）。
4b の隅に「イメージ」。

実行:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python tss-ep1/scripts/video.py -- [--draft | --preview]
  ... -- --draft --still 450   （組み上がった画面のその1コマ（元のフレーム番号）だけを stillcheck へ）
出力: tss-ep1/mp4/TSS_Episode01_SGL[_draft|_preview].mp4

Blender 5.x: FFMPEG 出力の前に image_settings.media_type='VIDEO'、VSE は .strips、new_effect は長さで指定（ep2・ep4の教訓）。
レンダー済みの連番に色の変換が二重にかからないよう view_transform は Standard（ep4の教訓）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

import scene as sc
from cuts import CUT_BY_ID, CUTS, FPS, RENDERED_CUTS, TOTAL_FRAMES

DRAFT_STEP = 2
TELOP_FONT = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
TELOP_SIZE = 64  # 本番解像度（横1080）での画素
TELOP_TOP = 0.89  # 1行目の中心の高さ（下から）。上から約11%（アプリの上端のボタンの少し下）
TELOP_LINE = 1.35  # 行の間隔（文字の大きさの倍数）
TELOP_FADE = 0.4  # 秒（ユーザーの好み）
TELOP_STEP = 0.25  # 秒。2行目以降が遅れて出る（ステップフェード）
NAME_CUT = None  # 名前だけ画面の真ん中に出すカット（4cを暗転にしていた頃は "4c"）
IMAGE_NOTE = dict(cut="4b", text="※イメージ", size=30, location=(0.06, 0.24))  # 惑星の像はイメージ（隅に表記）
EP_DIR = sc.EP_DIR
OUTPUT = os.path.join(EP_DIR, "mp4", "TSS_Episode01_SGL.mp4")


def text_strip(editor, name, channel, start, length, body, size, location, anchor_x='CENTER'):
    strip = editor.strips.new_effect(name, 'TEXT', channel, frame_start=start, length=length)
    strip.text = body
    strip.font = bpy.data.fonts.load(TELOP_FONT, check_existing=True)
    strip.font_size = size
    strip.location = location
    strip.anchor_x = anchor_x
    strip.anchor_y = 'CENTER'
    strip.color = (1, 1, 1, 1)
    strip.use_shadow = True
    strip.shadow_color = (0, 0, 0, 0.6)
    strip.shadow_blur = 0.5
    strip.blend_type = 'ALPHA_OVER'
    return strip


def fade(strip, f0, f1, fade_frames):
    for frame, alpha in [(f0, 0.0), (f0 + fade_frames, 1.0), (f1 - fade_frames, 1.0), (f1, 0.0)]:
        strip.blend_alpha = alpha
        strip.keyframe_insert("blend_alpha", frame=frame)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--still", type=int)
    args = ap.parse_args(argv)
    step = DRAFT_STEP if args.draft else 1
    scale = 0.25 if args.draft else 0.5 if args.preview else 1.0
    frames_dir = os.path.join(EP_DIR, "draft_frames" if args.draft else "preview_frames" if args.preview else "frames")
    suffix = "_draft" if args.draft else "_preview" if args.preview else ""

    bpy.ops.wm.read_homefile(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = int(sc.RESOLUTION[0] * scale), int(sc.RESOLUTION[1] * scale)
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'Standard'
    scene.render.fps = FPS // step

    def to_out(frame):  # 元のフレーム番号 → 書き出す動画のフレーム番号
        return (frame - 1) // step + 1

    scene.frame_start, scene.frame_end = 1, to_out(TOTAL_FRAMES)
    editor = scene.sequence_editor_create()

    for cut in RENDERED_CUTS:
        c = CUT_BY_ID[cut]
        frames = range(c["start"] + (-(c["start"] - 1) % step), c["end"] + 1, step)
        files = [f"ep1_{f:04d}.png" for f in frames]
        missing = [f for f in files if not os.path.exists(os.path.join(frames_dir, f))]
        if missing:
            raise SystemExit(f"[video] {cut}: {len(missing)}枚ない（例 {missing[0]}）")
        strip = editor.strips.new_image(f"Cut_{cut}", os.path.join(frames_dir, files[0]), 1, to_out(frames[0]))
        for f in files[1:]:
            strip.elements.append(f)

    fade_frames = max(int(TELOP_FADE * FPS / step), 1)
    channel = 3
    for c in CUTS:
        for i, (t0, t1, lines) in enumerate(c["telops"]):
            centered = c["id"] == NAME_CUT
            top = 0.5 + (len(lines) - 1) / 2 * TELOP_SIZE * TELOP_LINE / sc.RESOLUTION[1] if centered else TELOP_TOP
            for j, line in enumerate(lines):
                f0 = to_out(c["start"] + t0 + int(j * TELOP_STEP * FPS))
                f1 = to_out(c["start"] + t1)
                y = top - j * TELOP_SIZE * TELOP_LINE / sc.RESOLUTION[1]
                strip = text_strip(editor, f"Telop_{c['id']}_{i}_{j}", channel, f0, f1 - f0, line, TELOP_SIZE * scale,
                                   (0.5, y))
                fade(strip, f0, f1, fade_frames)
                channel += 1
    note_cut = CUT_BY_ID[IMAGE_NOTE["cut"]]
    f0, f1 = to_out(note_cut["start"]), to_out(note_cut["end"]) + 1
    text_strip(editor, "ImageNote", channel, f0, f1 - f0, IMAGE_NOTE["text"], IMAGE_NOTE["size"] * scale,
               IMAGE_NOTE["location"], 'LEFT').color = (1, 1, 1, 0.7)

    if args.still:
        scene.frame_set(to_out(args.still))
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = os.path.join(EP_DIR, "stillcheck", f"composite_{args.still:04d}{suffix}.png")
        bpy.ops.render.render(write_still=True)
        print("[video]", scene.render.filepath)
        return

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    scene.render.image_settings.media_type = 'VIDEO'
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM' if (args.draft or args.preview) else 'HIGH'
    scene.render.filepath = OUTPUT.replace(".mp4", f"{suffix}.mp4")
    bpy.ops.render.render(animation=True)
    print("[video]", scene.render.filepath)


main()
