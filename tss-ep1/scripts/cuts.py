"""ep1 のカット定義（bpy を使わない）。文言の差し替えはこのファイルだけで済ませる（TSS 制作設計書 第3章）。

フレームは動画全体の通し番号（1始まり、30fps）。テロップは VSE で重ねる（行のリスト、改行で区切る）。
telops の (開始, 終了) はカットの頭からのフレーム数。
"""
FPS = 30
TOTAL_FRAMES = 1320

CUTS = [
    dict(id="1a", start=1, end=180, telops=[(20, 170, ["レンズは", "光を集める"])],
         note="レンズは記号的"),
    dict(id="2a", start=181, end=360, telops=[(20, 170, ["太陽の重力も", "光を曲げる"])],
         note="角度を約3万倍に誇張"),
    dict(id="3a", start=361, end=600, telops=[(80, 230, ["でも集まるのは", "点じゃなく線"])],
         note="光線は十数本、横方向は約3万倍"),
    dict(id="3b", start=601, end=840, telops=[(30, 240, ["ただし", "548AUより先"])],
         note="軸方向は実物比、一定速、AU目盛り"),
    dict(id="4a", start=841, end=1020, telops=[(50, 170, ["ここなら", "系外惑星の像が", "得られる"])],
         note="探査機は記号的。太陽の円盤と輪は望遠鏡の視野の中"),
    dict(id="4b", start=1021, end=1230,
         telops=[(10, 95, ["ふつうの望遠鏡なら", "月より大きい鏡が", "要る"]),
                 (110, 210, ["太陽を使えば", "口径1mで", "100万画素"])],
         note="惑星の像はイメージ（隅に表記）"),
    dict(id="4c", start=1231, end=1320, telops=[(10, 85, ["これを", "太陽重力レンズという"])],
         note="暗転。編集で作る（レンダーしない）"),
]
CUT_BY_ID = {c["id"]: c for c in CUTS}
RENDERED_CUTS = [c["id"] for c in CUTS if c["id"] != "4c"]


def cut_of(frame):
    for c in CUTS:
        if c["start"] <= frame <= c["end"]:
            return c["id"]
    raise ValueError(f"frame {frame} はどのカットにも入らない")


if __name__ == "__main__":
    total = 0
    for c in CUTS:
        n = c["end"] - c["start"] + 1
        total += n
        print(f"{c['id']}: {c['start']}〜{c['end']}（{n}フレーム、{n / FPS:.1f}秒）"
              f" {' / '.join('・'.join(lines) for _, _, lines in c['telops'])}")
    assert total == TOTAL_FRAMES and all(a["end"] + 1 == b["start"] for a, b in zip(CUTS, CUTS[1:]))
    for c in CUTS:
        for _, _, lines in c["telops"]:
            assert all(len(line) <= 12 for line in lines), lines
    print(f"合計 {total}フレーム（{total / FPS:.0f}秒）")
