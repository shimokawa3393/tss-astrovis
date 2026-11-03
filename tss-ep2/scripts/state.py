"""ep2 の絵の配置（LAYOUTS）。静止画（01_still.py）で確定させ、動きはあとでここから値を変えて作る。

縦の位置は画面の上からの割合。上の帯（上から約11〜25%）はテロップ、下25%と右下は SNS のボタンがかぶるので空ける。
"""
from cuts import CUT_BY_ID, PROBE_DISTANCE_AU, cut_of

VIEW_H_BU = 19.2  # 画面の高さ（ep1 の 1a・4b と同じ。1px = 0.01 BU）
SUN_RADIUS_PX = 70  # c01・c02 の太陽（記号の大きさ）

_SIDE = dict(kind="side", planet_from_top=0.30, sun_from_top=0.55, probe_from_top=0.80, sun_radius_px=SUN_RADIUS_PX,
             probe_height_px=110, labels=True)
LAYOUTS = {
    # c01: 惑星・太陽・探査機が縦一列。3つを結ぶ細い線と、それぞれの名前
    "c01": dict(_SIDE),
    # c02: 惑星の光が太陽の周りのぜんぶの方向から曲がって探査機に集まる。真横のまま（カメラは動かさない）。
    # 少し上から見下ろす案は、カメラが回る間に光の筋が伸び始め、背景の星も流れて動きが2つ重なった
    # （ユーザー「なんで光の筋が伸びると同時に背景が動く？」→ 動かさない案）。
    # 光が太陽の脇を通る半径は、探査機から見た輪と同じ比（太陽の約1.48倍、1200AU）
    "c02": dict(_SIDE, cone=True, labels=False),
    # c03: ep1 の4aと同じ（探査機の後ろ上から。目で見た太陽は点、円盤と輪は望遠鏡の視野の中）
    "c03": dict(kind="probe", sun_from_top=0.62, probe_offset=(-0.9, -16.0, 4.0), vfov_deg=60,
                inset_center_px=(540, 760), inset_radius_px=210, inset_sun_radius_px=80),
}
# c04: 前半は太陽の光がにじんで視野いっぱいに広がり、輪が埋もれる。後半は黒い円で隠し、残ったもやの中に輪がうっすら
LAYOUTS["c03_label"] = dict(LAYOUTS["c03"], ring_label=1.0)
LAYOUTS["c04_glare"] = dict(LAYOUTS["c03"], glare=1.0)
LAYOUTS["c04"] = dict(LAYOUTS["c03"], occulter=1.0, haze=1.0, ring_alpha=0.15)
# c05: 視野の上に狙った惑星のイメージ（太陽の真後ろで見えないので）。あちこちから輪の全周へ光の筋。c06 は c05 の最後のまま名前
LAYOUTS["c05"] = dict(LAYOUTS["c04"], ring_alpha=1.0, planet=1.0, streaks=1.0, planet_center_px=(540, 450),
                      planet_radius_px=60)
assert PROBE_DISTANCE_AU == 1200  # ep1 の props.einstein_ring_ratio() は 1200AU で輪の比を出す

# ------------------------------------------------------------
# 動き（カットの頭からのフレーム数 t）
# ------------------------------------------------------------
LINE_GROW = (30, 80)  # c01: 惑星から探査機へ一直線が伸びる
LABELS_FADE_OUT = (0, 15)  # c02: 名前が消える
CONE_GROW = (15, 75)  # c02: 惑星の光が伸びて、太陽の周りで曲がって探査機に集まる
INSET_POP = (30, 46)  # c03: 太陽の点から視野がピュッと開く（ep1 の4aと同じ）
RING_FADE_IN = (50, 70)  # c03: 視野の中で光の輪が灯る
RING_LABEL_IN = None  # c03: 輪に名前の目印。c03 のテロップで名前を説明することにしたので出さない（2回出るとくどい）。出すなら (85, 105)
GLARE_UP = (20, 60)  # c04: 太陽の光がにじんで広がり、輪が埋もれる
RING_BURIED = (40, 60)
OCCULT = (90, 110)  # c04: 黒い円が太陽を覆う
GLARE_DOWN = (100, 130)  # c04: まぶしさが引いて、コロナのもやが残る
RING_FAINT = (130, 170, 0.15)  # c04: もやの中に輪がうっすら
PLANET_FADE_IN = (10, 35)  # c05: 視野の上に惑星（イメージ）
STREAKS = (40, 100)  # c05: 惑星のあちこちから輪の全周へ光の筋
RING_BRIGHTEN = (60, 120)  # c05: 輪が光る


def _ramp(t, span):
    a, b = span[0], span[1]
    return min(max((t - a) / (b - a), 0.0), 1.0)


def _smooth(x):
    return x * x * (3 - 2 * x)


def _ease_out_back(x, overshoot=1.6):
    """行きすぎて戻る（ピュッ）。"""
    x -= 1
    return 1 + x * x * ((overshoot + 1) * x + overshoot)


def _lerp(a, b, x):
    return a + (b - a) * x


def scene_state(frame, cut=None):
    """動画全体のフレーム番号 → 絵の状態（build.build_frame に渡す dict）。"""
    cut = cut or cut_of(frame)
    t = frame - CUT_BY_ID[cut]["start"]
    key = cut[:3]
    if key in ("c00", "c06"):
        s = dict(kind="space")
    elif key == "c01":
        s = dict(LAYOUTS["c01"], line_grow=_smooth(_ramp(t, LINE_GROW)))
    elif key == "c02":
        s = dict(LAYOUTS["c02"], labels=True, label_alpha=1 - _ramp(t, LABELS_FADE_OUT),
                 cone_grow=_smooth(_ramp(t, CONE_GROW)))
        # 最後に太陽のまわりを回って軸の方向から見る案は、光の筋が花びらのように絡まって輪に見えなかったのでやめた。
        # 輪は c03 で探査機の視点から見せる
    elif key == "c03":
        x = _ramp(t, INSET_POP)
        s = dict(LAYOUTS["c03"], inset_grow=_ease_out_back(x) if x > 0 else 0.0,
                 ring_alpha=_smooth(_ramp(t, RING_FADE_IN)), ring_label=_smooth(_ramp(t, RING_LABEL_IN)) if RING_LABEL_IN else 0.0)
    elif key == "c04":
        s = dict(LAYOUTS["c04"])
        s["glare"] = _smooth(_ramp(t, GLARE_UP)) * (1 - _smooth(_ramp(t, GLARE_DOWN)))
        s["occulter"] = _smooth(_ramp(t, OCCULT))
        s["haze"] = _smooth(_ramp(t, GLARE_DOWN))
        s["ring_alpha"] = (1 - _ramp(t, RING_BURIED)) if t < RING_FAINT[0] else RING_FAINT[2] * _smooth(_ramp(t, RING_FAINT))
    elif key == "c05":
        s = dict(LAYOUTS["c05"], planet=_smooth(_ramp(t, PLANET_FADE_IN)), streaks=_smooth(_ramp(t, STREAKS)))
        s["ring_alpha"] = _lerp(RING_FAINT[2], 1.0, _smooth(_ramp(t, RING_BRIGHTEN)))
    else:  # c00・c06: 星だけの宇宙に中央のテロップ（最初と最後。TSS 台本フォーマット）
        s = dict(kind="space")
    s["cut"], s["frame"], s["t"] = cut, frame, t
    return s
