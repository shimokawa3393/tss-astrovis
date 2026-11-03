"""ep2 から ep1 の描画部品（scene.py・props.py）を読み込む。太陽・探査機・望遠鏡の視野・星空・コンポジターは ep1 のまま使う。

ep1 には ep2 と同じ名前のファイル（cuts・state・build）があるので、ep1 の import の後に ep2 のフォルダを sys.path の先頭へ戻す
（ep1 の scene.py・props.py は自分のフォルダを先頭に入れる）。
テクスチャも ep1 のもの（tss-ep1/textures）を使う。
"""
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
EP_DIR = os.path.dirname(SCRIPTS_DIR)
EP1_SCRIPTS = os.path.join(os.path.dirname(EP_DIR), "tss-ep1", "scripts")
for path in (SCRIPTS_DIR, EP1_SCRIPTS):
    if path not in sys.path:
        sys.path.append(path)

import props as ep1  # noqa: E402  ep1 の小道具（探査機・望遠鏡の視野・光の点）
import scene as sc  # noqa: E402  ep1 の描画層（材質・線・太陽・にじみ・星空・カメラ・レンダー設定）

while SCRIPTS_DIR in sys.path:
    sys.path.remove(SCRIPTS_DIR)
sys.path.insert(0, SCRIPTS_DIR)
