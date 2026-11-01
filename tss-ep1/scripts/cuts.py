"""ep1 のカット定義（bpy を使わない）。文言の差し替えはこのファイルだけで済ませる（TSS 制作設計書 第3章）。

フレームは動画全体の通し番号（1始まり、30fps）。テロップは VSE で重ねる（行のリスト、改行で区切る）。
telops の (開始, 終了) はカットの頭からのフレーム数。
"""
FPS = 30
TOTAL_FRAMES = 1440

# 11-01: 「レンズと重力で光を集めるのがピンとこない」「1AUの距離感がわからない」（ユーザー）で、
# 1aに「曲げて」、2aに「太陽が巨大なレンズになる」（2aを6→8秒）、3bに1AUの説明（3bを8→10秒）を足した。
# 3bは「1AUは…」ではなく「…は1AU」→「光が集まるのは548AUより先」（ユーザー。文が数字で終わり、1AU→548AUが並ぶ。
# 「その線が始まるのは」は間に1AUが入るので「その」が何を指すか分からない）。
# 1AUは目盛りの「100 AU」が流れてくるときに出す（見る人が「AUって何？」と思う瞬間）。上へ抜ける太陽に重ならないよう1.5秒から
CUTS = [
    dict(id="1a", start=1, end=180, telops=[(20, 170, ["レンズは", "光を曲げて", "集める"])],
         note="レンズは記号的"),
    dict(id="2a", start=181, end=420,
         telops=[(25, 120, ["太陽の重力も", "光を曲げる"]), (135, 235, ["太陽が", "巨大なレンズになる"])],
         note="角度を約3万倍に誇張"),
    dict(id="3a", start=421, end=660, telops=[(80, 230, ["でも集まるのは", "点じゃなく線"])],
         note="光線は十数本、横方向は約3万倍"),
    dict(id="3b", start=661, end=960,
         telops=[(45, 130, ["地球と太陽の距離は", "1AU"]), (145, 295, ["光が集まるのは", "548AUより先"])],
         note="軸方向は実物比、一定速、AU目盛り。海王星とボイジャー1号は距離の目印"),
    dict(id="4a", start=961, end=1140, telops=[(50, 170, ["ここなら", "系外惑星の像が", "得られる"])],
         note="探査機は記号的。太陽の円盤と輪は望遠鏡の視野の中"),
    dict(id="4b", start=1141, end=1350,
         # 後半は最初「口径1mで / 100万画素」だったが「ピンとこない」（口径は普段使わない言葉、100万画素はスマホより少なく聞こえる）。
         # 「大陸まで見える」は、像が細かくなって大陸が見えてくる頃に3行目が出るように。100万画素は投稿文へ
         telops=[(10, 95, ["ふつうの望遠鏡なら", "月より大きい鏡が要る"]),
                 (120, 210, ["太陽を使えば", "1mの鏡で", "大陸まで見える"])],
         note="惑星の像はイメージ（隅に表記）"),
    dict(id="4c", start=1351, end=1440, telops=[(10, 85, ["これを", "太陽重力レンズという"])],
         note="背景は星だけの宇宙"),
]
CUT_BY_ID = {c["id"]: c for c in CUTS}
RENDERED_CUTS = [c["id"] for c in CUTS]


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
