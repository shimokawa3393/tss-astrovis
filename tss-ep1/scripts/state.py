"""フレームごとの絵の状態（`scene_state(frame, cut)`）。静止画（01_still.py）とレンダー（render.py）の両方がここを使う。

状態は build.build_frame に渡す dict。LAYOUTS は各カットで確定した静止画の配置で、動きはそこから値を変えて作る。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scene as sc
from cuts import CUT_BY_ID, cut_of
from physics import R_SUN, focal_distance, to_au

# anchor_au が画面の上から anchor_from_top の位置に来る。view_h_bu は画面の高さ（BU）。
# 軸方向も横方向も同じ倍率で写すので、見かけの曲がり角はカットによらない。
# sun_radius_px を指定すると太陽をその大きさの記号にする（省くと一番内側の光線に接する大きさ）。
_3B = dict(view_h_bu=sc.bu(200), anchor_from_top=0.55,
           # 548AUの時点で画面に入るのは b < 約1.12R の光線だけなので、縁の近くを細かく拾う
           b_ratios=[1 + 0.02 * i for i in range(7)], show_line=True,
           sun_radius_px=45, ruler_au=800, neptune=True, voyager=True)
LAYOUTS = {
    # 太陽〜5000AU を画面の上28%〜85%に入れる。最初は上12%（00_scale_check.py と同じ）だったが、
    # テロップ（上から約11%）が太陽に重なったので下げた（11-01）
    "3a": dict(anchor_au=0, anchor_from_top=0.28, view_h_bu=sc.bu(5000) / (0.85 - 0.28),
               b_ratios=sc.B_RATIOS, show_line=True),
    # 太陽の近くに寄る。光線は間引いて、太陽に近いほど大きく曲がるのを見せる。
    # 一番内側の光線は画面の下の方で軸に近づく（「レンズのように1点に集まりそう」と思わせ、3aでくつがえす）
    "2a": dict(anchor_au=0, anchor_from_top=0.45, view_h_bu=sc.SUN_RADIUS_BU / 170 * sc.RESOLUTION[1],
               b_ratios=[1.0, 1.5, 2.0, 2.5, 3.0], show_line=False),
    # 3b: 軸に沿って下る。窓は200AU、いまの深さは画面の上から55%の高さ
    "3b_start": dict(_3B, anchor_au=0),
    "3b_neptune": dict(_3B, anchor_au=30.1),
    "3b": dict(_3B, anchor_au=548),
    # 1a: レンズの中心を2aの太陽と同じ高さ（上から45%）に置き、集まる点も2aの一番内側の光が軸に近づく高さ（80%）にそろえる
    "1a": dict(kind="lens", anchor_au=0, anchor_from_top=0.45, view_h_bu=19.2),
    # 4b: 望遠鏡の視野（中心は上から60%、テロップは上の帯）。前半は光の点、後半はモザイクの像
    "4b_dot": dict(kind="planet", anchor_au=0, anchor_from_top=0.60, view_h_bu=19.2, pixels=0),
    "4b_mid": dict(kind="planet", anchor_au=0, anchor_from_top=0.60, view_h_bu=19.2, pixels=24),
    "4b": dict(kind="planet", anchor_au=0, anchor_from_top=0.60, view_h_bu=19.2, pixels=1000),
    # 4a: 1200AUの探査機の後ろ上から太陽を見る。目で見た太陽は点（上から62%）、探査機はその下の少し右（右端はSNSのボタンがかぶる）。
    # 太陽の円盤と光の輪（半径は太陽の1.48倍）は、上の望遠鏡の視野の中に描く。視野の上の端は3行のテロップの下（上から約30%）
    "4a": dict(kind="probe", anchor_au=0, anchor_from_top=0.5, view_h_bu=19.2, sun_from_top=0.62,
               probe_offset=(-0.9, -16.0, 4.0), vfov_deg=60, inset_center_px=(540, 760), inset_radius_px=210,
               inset_sun_radius_px=80),
}

# ------------------------------------------------------------
# 動き（カットの頭からのフレーム数 t）
# ------------------------------------------------------------
RAYS_GROW = (15, 75)  # 1a: 平行な光が上から画面の下まで届く（全部の光線が同時に。光の波面）
LENS_RAYS_FADE_OUT = (160, 180)  # 1a: 終わりで光線が消え、レンズだけ残る
LENS_FADE_OUT = (0, 16)  # 2a: レンズが薄れながら縮む（11-01「レンズと重力がピンとこない」）
SUN_FADE_IN = (6, 25)  # 2a: 同じ所に太陽が現れる。レンズより少し遅らせる（重なると土星の輪に見えた）
RAYS_GROW_2A = (25, 85)  # 2a: 太陽の脇を通る光が上から伸びる
ZOOM_OUT = (0, 75)  # 3a: 2aの寄りから3aの引きへ
OTHERS_FADE_OUT = (0, 20)  # 3a: 2aの光線のうち一番内側（b=R）以外を消し、1本から始める
ADD_RAY_FROM, ADD_RAY_EVERY, ADD_RAY_GROW = 75, 10, 15  # 3a: 内側から1本ずつ足す（伸びきるまで15フレーム）
DESCENT_AU = 548  # 3b: 0AU → 548AU を一定速（1フレーム約2.3AU）
DESCENT = (0, 240)  # 3b: 太陽からすぐ下り始め、終わりは548AUで止めて「光が集まるのは548AUより先」
DESCENT_EASE = 12  # 3b: 動き出しと止まりのなめらかさ（フレーム）。その間は一定速
INSET_POP = (30, 46)  # 4a: 太陽の点から視野がピュッと開く
RING_FADE_IN = (50, 70)  # 4a: 開いた視野の中で光の輪が灯る
DOT_TO_IMAGE = (100, 110)  # 4b: 光の点が消え、粗いモザイクが現れる
REFINE = (100, 180)  # 4b: モザイクが細かくなっていく（4 → 1000画素四方）
REFINE_STEPS = [4, 8, 16, 32, 64, 128, 256, 512, 1000]


def _ramp(t, span):
    a, b = span
    return min(max((t - a) / (b - a), 0.0), 1.0)


def _smooth(x):
    return x * x * (3 - 2 * x)


def _ease_out_back(x, overshoot=1.6):
    """行きすぎて戻る（ピュッ）。"""
    x -= 1
    return 1 + x * x * ((overshoot + 1) * x + overshoot)


def _cruise(x, e):
    """0→1 を、動き出しと止まり（それぞれ全体の e）だけなめらかにし、間は一定速で進む。"""
    if x < e:
        p = x * x / (2 * e)
    elif x < 1 - e:
        p = x - e / 2
    else:
        p = (1 - e) - (1 - x) ** 2 / (2 * e)
    return p / (1 - e)


def _lerp(a, b, x):
    return a + (b - a) * x


def _screen(layout):
    view_h = layout["view_h_bu"]
    top_z = -sc.bu(layout["anchor_au"]) + layout["anchor_from_top"] * view_h
    return top_z, top_z - view_h


def scene_state(frame, cut=None):
    """動画全体のフレーム番号 → 絵の状態（build.build_frame に渡す dict）。誇張の値もログ用に入れる。"""
    cut = cut or cut_of(frame)
    c = CUT_BY_ID[cut]
    t = frame - c["start"]

    if cut == "1a":
        s = dict(LAYOUTS["1a"])
        top_z, bottom_z = _screen(s)
        s["front_z"] = _lerp(top_z, bottom_z, _ramp(t, RAYS_GROW))
        s["ray_alpha"] = 1 - _smooth(_ramp(t, LENS_RAYS_FADE_OUT))
    elif cut == "2a":
        s = dict(LAYOUTS["2a"])
        top_z, bottom_z = _screen(s)
        s["lens_alpha"] = 1 - _smooth(_ramp(t, LENS_FADE_OUT))
        s["sun_fade"] = _smooth(_ramp(t, SUN_FADE_IN))
        front = _lerp(-top_z, -bottom_z, _ramp(t, RAYS_GROW_2A))
        s["fronts"] = [front] * len(s["b_ratios"])
    elif cut == "3a":
        s = _state_3a(t)
    elif cut == "3b":
        s = dict(LAYOUTS["3b"], anchor_au=DESCENT_AU * _cruise(_ramp(t, DESCENT), DESCENT_EASE / (DESCENT[1] - DESCENT[0])))
    elif cut == "4a":
        s = dict(LAYOUTS["4a"])
        x = _ramp(t, INSET_POP)
        s["inset_grow"] = _ease_out_back(x) if x > 0 else 0.0
        s["ring_alpha"] = _smooth(_ramp(t, RING_FADE_IN))
    elif cut == "4b":
        s = dict(LAYOUTS["4b"])
        mix = _ramp(t, DOT_TO_IMAGE)
        s["dot_fade"] = 1 - mix
        s["image_opacity"] = mix
        x = _ramp(t, REFINE)
        s["pixels"] = REFINE_STEPS[min(int(x * len(REFINE_STEPS)), len(REFINE_STEPS) - 1)] if mix > 0 else 0
    else:
        # 4c: 名前の背景は星だけの宇宙（11-01ユーザー。暗転 →「真っ暗はどうだろう」→ 3aの引きの絵 →「ただの宇宙でいい」）
        s = dict(kind="space")
    s["cut"], s["frame"], s["t"] = cut, frame, t
    return s


def _state_3a(t):
    """2aの寄りから引き、一番内側の光線1本 → 内側から1本ずつ足して、交わる点が軸に並び焦線が伸びる。"""
    near, far = LAYOUTS["2a"], LAYOUTS["3a"]
    z = _smooth(_ramp(t, ZOOM_OUT))
    s = dict(far)
    # 画面の高さは対数で補間する（寄りと引きで約500倍違う）
    s["view_h_bu"] = math.exp(_lerp(math.log(near["view_h_bu"]), math.log(far["view_h_bu"]), z))
    s["anchor_from_top"] = _lerp(near["anchor_from_top"], far["anchor_from_top"], z)
    top_z, bottom_z = _screen(s)

    b_ratios = sc.B_RATIOS
    in_2a = {round(b, 6) for b in near["b_ratios"]}
    fade_2a = 1 - _ramp(t, OTHERS_FADE_OUT)
    alphas, fronts, line_end_au = [], [], 0.0
    order = 0
    for b in b_ratios:
        focus_au = to_au(focal_distance(b * R_SUN))
        if b == b_ratios[0]:
            alphas.append(1.0)
            fronts.append(None)
            line_end_au = focus_au
            continue
        order += 1
        start = ADD_RAY_FROM + (order - 1) * ADD_RAY_EVERY
        grow = _ramp(t, (start, start + ADD_RAY_GROW))
        if grow > 0:
            alphas.append(1.0)
            # 上の端から画面の下まで伸びる。交わる点を過ぎたら焦線もそこまで伸ばす
            front = _lerp(-top_z, -bottom_z, grow)
            fronts.append(front)
            line_end_au = max(line_end_au, min(focus_au, front * sc.AXIAL_AU_PER_BU))
        elif round(b, 6) in in_2a and fade_2a > 0:
            alphas.append(fade_2a)
            fronts.append(None)
        else:
            alphas.append(0.0)
            fronts.append(None)
    s.update(alphas=alphas, fronts=fronts, line_end_au=line_end_au)
    return s


if __name__ == "__main__":
    # bpy なしでは scene を import できないので、Blender の中で: Blender --background --python state.py
    for f in (1, 60, 175, 181, 195, 250, 421, 500, 660, 661, 706, 800, 930, 990, 991, 1040, 1171, 1300, 1380):
        st = scene_state(f)
        print(f, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in st.items()
                  if k in ("cut", "t", "anchor_au", "view_h_bu", "inset_grow", "ring_alpha", "pixels", "line_end_au",
                           "sun_fade", "lens_alpha", "ray_alpha")})
