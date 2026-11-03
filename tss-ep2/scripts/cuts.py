# 第2話「太陽を囲む輪」(39秒 / 1170フレーム / 30fps / n=7)
# テロップは読点・句点なし、改行は要素の区切り。文言の差し替えはこのファイルだけで済ませる。
# numbers は physics_ring.py の関数 / TSS_定数表.md への参照キー。
# 探査機の距離は1200AUで描く(第1話の4aと同じ。輪の半径は太陽半径の約1.48倍)。距離は画面にも投稿文にも出さない。

PROBE_DISTANCE_AU = 1200

CUTS = [
    {
        # どの回から見ても分かるよう、最初のテロップで前提を言う(ユーザー「入りが唐突すぎる」)。
        # 最初と最後のテロップは中央・星だけの背景(TSS 台本フォーマット)
        "id": "c00_premise",
        "frames": 90,
        "telop": ["太陽は", "巨大なレンズになる"],
        "numbers": [],
        "exaggeration": "",
        "start": "星だけの宇宙",
        "end": "同じ",
    },
    {
        "id": "c01_alignment",
        "frames": 150,
        "telop": ["探査機と太陽と惑星が", "一直線に並ぶ"],
        "numbers": [],
        "exaggeration": "距離は縮めて描く。探査機・惑星は記号的な形",
        "start": "探査機・太陽・惑星が一直線に並んだ引きの絵",
        "end": "同じ(一直線の配置)",
    },
    {
        "id": "c02_light_all_around",
        "frames": 180,
        "telop": ["光は太陽の周りの", "ぜんぶの方向から", "曲がって届く"],
        "numbers": ["ring_geometry"],
        "exaggeration": "距離は縮めて描く。曲がりは見やすく誇張。カメラは真横のまま動かさない(見下ろすと背景が流れて光の動きと重なった。軸方向から見た図は、筋が絡まって輪に見えなかったのでやめた)",
        "start": "c01の最後と同じ一直線の絵",
        "end": "光が探査機に集まった円錐状の絵",
    },
    {
        "id": "c03_probe_view_ring",
        "frames": 270,  # 7秒 → 9秒(輪が出たところで名前も説明する。ユーザー「輪が登場してるのに説明が遅い」)
        "telop": ["探査機の望遠鏡では", "太陽を囲む細い輪"],
        # 「アインシュタインリングと呼ぶ」は1行14文字で上限を超えるので3行
        "telop_next": ["この輪を", "アインシュタインリング", "と呼ぶ"],
        "numbers": ["ring_geometry"],            # 輪は太陽半径の約1.48倍(1200AU)
        "exaggeration": "輪の太さ・明るさは強調。半径比は実物どおり(太陽=1、輪=約1.48)",
        "start": "第1話の4aと同じ構図。探査機の後ろ上から見た、点の太陽。点から望遠鏡の視野が開く",
        "end": "望遠鏡の視野の中に、太陽の円盤とそのすぐ外の細い輪",
    },
    {
        "id": "c04_hidden_by_glare",
        "frames": 210,
        "telop": ["でも太陽が眩しすぎる", "隠してやっと見える"],
        "numbers": [],
        "exaggeration": "輪は強調。グレアの広がりは演出",
        "start": "c03の最後と同じ絵",
        "end": "コロナグラフが円盤を覆い、残ったコロナのもやの中に輪がうっすら見える絵",
    },
    {
        "id": "c05_ring_carries_light",
        "frames": 180,
        "telop": ["惑星の光も", "この輪になって届く"],
        "numbers": [],
        "exaggeration": "輪は強調。惑星は太陽の真後ろで見えないので、視野の上にイメージとして出す。光の筋は演出(どの点の光も輪の全周へ広げる)",
        "start": "c04の最後と同じ絵(視野の中の輪)。上に惑星のイメージが現れる",
        "end": "惑星のあちこちから出た光の筋が輪の全周に入り、輪が光る絵",
    },
    {
        "id": "c06_hook",
        "frames": 90,
        # 最後は再構成(次回への引き)。名前で締めない(ユーザー「これを…と言うで決めるのはダサい」)。名前は c03 で説明する
        "telop": ["この輪から", "惑星の像を再構成する"],
        "numbers": [],
        "exaggeration": "",
        "start": "星だけの宇宙(最後のテロップは中央。輪や惑星と重ねない)",
        "end": "同じ",
    },
]

FPS = 30
TOTAL_FRAMES = 1170

# 動画全体の通し番号（1始まり）。レンダー・動画はこちらを使う
_start = 1
for _c in CUTS:
    _c["start"], _c["end"] = _start, _start + _c["frames"] - 1
    _start += _c["frames"]
CUT_BY_ID = {c["id"]: c for c in CUTS}
RENDERED_CUTS = [c["id"] for c in CUTS]

# テロップを出す範囲（カットの頭からのフレーム数）、行ごとに遅らせるフレーム数（None なら0.25秒ずつ）、文言のキー
TELOP_TIMING = {
    "c00_premise": [(10, 85, None, "telop")],
    "c01_alignment": [(20, 140, None, "telop")],
    "c02_light_all_around": [(20, 170, None, "telop")],
    "c03_probe_view_ring": [(50, 140, None, "telop"), (150, 260, None, "telop_next")],  # 視野が開いて輪が灯ってから
    "c04_hidden_by_glare": [(25, 200, [0, 100], "telop")],  # 2行目は黒い円で隠してから
    "c05_ring_carries_light": [(20, 170, None, "telop")],
    "c06_hook": [(5, 85, None, "telop")],
}
IMAGE_NOTE_CUTS = ["c05_ring_carries_light"]  # 惑星はイメージ（隅に表記）
CENTER_TELOP_CUTS = ["c00_premise", "c06_hook"]  # 最初と最後のテロップは中央（背景は星だけ）


def cut_of(frame):
    for c in CUTS:
        if c["start"] <= frame <= c["end"]:
            return c["id"]
    raise ValueError(f"frame {frame} はどのカットにも入らない")


assert sum(c["frames"] for c in CUTS) == TOTAL_FRAMES
assert all(len(line) <= 12 for c in CUTS for key in ("telop", "telop_next") for line in c.get(key, []))
assert not any(ch in line for c in CUTS for line in c["telop"] for ch in "、。")

if __name__ == "__main__":
    for c in CUTS:
        print(c["id"], c["frames"], c["telop"])
    print("total frames:", sum(c["frames"] for c in CUTS))
