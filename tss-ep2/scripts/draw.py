"""ep2 の絵（bpy）。c01・c02 の横から見た配置図。

座標は ep1 と同じ（XZ 面、Z が上、カメラは -Y から）。長さは px（1px あたりの BU）を掛けて画面の画素で置く。
上から 惑星 → 太陽 → 探査機 の縦一列（ep1 の 2a〜3b と同じく、光は上から来て太陽の下の軸に集まる）。距離は縮めて描く。
"""
import math

import bpy
import mathutils

from common import ep1, sc

PLANET_COLOR = (0.8, 0.9, 1.0, 1)  # ep1 の4bの光の点・4aの輪と同じ青白
PLANET_LIGHT_STRENGTH = 1.2
LINE_STRENGTH = 0.25


def screen_z(from_top, view_h, top_z):
    return top_z - from_top * view_h


def build_side_camera(center_z, view_h, vfov_deg, tilt_deg=0.0):
    """-Y から見るカメラ。tilt_deg だけ上から見下ろす（c02 で光の円錐を立体に見せ、最後は軸の方向から見る）。
    (0, 0, center_z) を画面の中心に、そこを中心に回る。"""
    cam = sc.build_camera(center_z, view_h, vfov_deg)
    if tilt_deg:
        d = -cam.location.y
        t = math.radians(tilt_deg)
        cam.location = (0, -d * math.cos(t), center_z + d * math.sin(t))
        cam.rotation_euler = (math.radians(90) - t, 0, 0)
    return cam


def build_probe_icon(z, height_px, px):
    """ep1 の探査機の模型を、望遠鏡を上（太陽の方）へ向けて置く。height_px は筒の後ろからフードの先までの画面の高さ。"""
    scale = height_px * px / 2.0  # 模型は後ろの板から フードの先まで約2.0（scale 1）
    parts = ep1.build_probe(scale)
    root = bpy.data.objects.new("ProbeRoot", None)
    bpy.context.collection.objects.link(root)
    for p in parts:
        p.parent = root
    root.rotation_euler = (math.radians(90), 0, math.radians(-25))  # +Y（筒）→ +Z。少し回して皿のアンテナと電池を見せる
    root.location = (0, 0, z - 0.75 * scale)
    key = bpy.data.lights.new("SunLight", type='SUN')
    key.energy = 3.0
    key_obj = bpy.data.objects.new("SunLight", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.rotation_euler = (0, 0, 0)  # 上（太陽）から下へ
    fill = bpy.data.lights.new("FillLight", type='SUN')
    fill.energy = 1.5
    fill.color = (0.75, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(70), 0, math.radians(-20))
    return root


def build_planet_dot(z, px, fade=1.0):
    dot = ep1.build_unresolved_dot(z, px, fade)
    return dot


def build_alignment_line(top_z, bottom_z, px, alpha=1.0, grow=1.0):
    """3つを結ぶ一直線（ep1 の軸と同じ細い線）。grow: 惑星から下へ伸びる途中。"""
    if grow <= 0 or alpha <= 0:
        return None
    mat = ep1.translucent_emission("AlignLineGlow", sc.RAY_COLOR, LINE_STRENGTH * 2, alpha)
    return sc.polyline("AlignLine", [(0, 0.3, top_z), (0, 0.3, top_z + (bottom_z - top_z) * grow)], mat, 0.8 * px)


def build_labels(items, px, alpha=1.0):
    """(名前, x_px, z) を ep1 の目印と同じ書き方で置く。alpha で薄れる（c02 の頭）。"""
    if alpha <= 0:
        return
    for name, x_px, z in items:
        label = sc.text_label(f"Label_{name}", name, x_px * px, z, sc.LABEL_PX * px)
        label.data.materials[0] = ep1.translucent_emission(f"Label_{name}Glow", sc.RULER_COLOR, sc.RULER_STRENGTH * 1.6,
                                                           alpha)


def _bend_path(p, b_vec, q, n=24):
    """惑星 p → 太陽の脇 b_vec → 探査機 q。太陽の脇の折れ目を2次ベジエで丸める（曲がりは見やすく誇張）。"""
    p, b, q = mathutils.Vector(p), mathutils.Vector(b_vec), mathutils.Vector(q)
    a = b + (p - b) * 0.25
    c = b + (q - b) * 0.25
    pts = [p, a]
    for i in range(1, n):
        t = i / n
        pts.append((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c)
    pts += [c, q]
    return pts


def _clip(points, length):
    """点の列を、始めから length の長さまでにする（光が惑星から伸びていく途中）。"""
    out = [points[0]]
    left = length
    for a, b in zip(points, points[1:]):
        seg = (b - a).length
        if seg >= left:
            out.append(a + (b - a) * (left / seg))
            return out
        out.append(b)
        left -= seg
    return out


def build_light_cone(planet_z, probe_z, ring_px, px, count=24, grow=1.0, alpha=1.0, phase_deg=0.0):
    """惑星の光が太陽の周りのぜんぶの方向から曲がって、探査機に集まる（円錐を2つ合わせた形）。

    ring_px: 光が太陽の脇を通る半径（画面の画素）。grow: 0〜1 で惑星から伸びる長さ。
    """
    mat = ep1.translucent_emission("ConeRayGlow", PLANET_COLOR, PLANET_LIGHT_STRENGTH, alpha)
    paths = []
    for k in range(count):
        a = math.radians(phase_deg) + 2 * math.pi * k / count
        b_vec = (ring_px * px * math.cos(a), ring_px * px * math.sin(a), 0)
        pts = _bend_path((0, 0, planet_z), b_vec, (0, 0, probe_z))
        total = sum((y - x).length for x, y in zip(pts, pts[1:]))
        if grow < 1:
            pts = _clip(pts, total * grow)
        if len(pts) >= 2:
            paths.append(sc.polyline(f"ConeRay_{k:02d}", [tuple(v) for v in pts], mat, 1.0 * px))
    return paths


# ------------------------------------------------------------
# c03〜c06: 望遠鏡の視野の中（ep1 の props.build_telescope_inset の上に重ねる）
# ------------------------------------------------------------
GLARE_COLOR = (1.0, 0.82, 0.55, 1)  # 太陽の光がにじんで白っぽく飽和する
HAZE_COLOR = (1.0, 0.7, 0.4, 1)  # 隠したあとに残るコロナのもや


def _inset_local(vfov_deg):
    """ep1 の build_telescope_inset と同じ、画面の画素 → カメラの座標（カメラから depth の距離）。"""
    k = math.tan(math.radians(vfov_deg) / 2) / (sc.RESOLUTION[1] / 2)
    w, h = sc.RESOLUTION

    def local(sx, sy, depth=1.0):
        return ((sx - w / 2) * k * depth, (h / 2 - sy) * k * depth, -depth)
    return k, local


def _attach(obj, cam, location, rotation=(0, 0, 0)):
    obj.parent = cam
    obj.matrix_parent_inverse.identity()
    obj.location = location
    obj.rotation_euler = rotation
    return obj


def build_inset_extras(cam, vfov_deg, center_px, sun_radius_px, ring_ratio, glare=0.0, occulter=0.0, haze=0.0,
                       planet=0.0, streaks=0.0, planet_center_px=None, planet_radius_px=60):
    """視野の中に重ねる。どれも 0〜1。

    glare: 太陽の光がにじんで視野いっぱいに広がり、輪が埋もれる（c04 前半）。
    occulter: コロナグラフの黒い円が太陽の円盤を覆う。haze: 隠しても残るコロナのもや（主な雑音: Turyshev & Toth 2022）。
    planet / streaks: 狙った惑星のイメージと、そのあちこちから輪の全周へ広がる光の筋（c05）。
    深さ: 輪 0.998・視野の円 0.999・太陽の中心 1.0（ep1）。太陽は球なので手前の面は 1.0 - 半径（約0.95）まで出る。
    にじみと黒い円はそれより手前に置く（0.997 では太陽の円盤がにじみの中から透けて見え、黒い円は太陽に隠れた）。
    黒い円 0.935・にじみ 0.94・もや 0.941（同じ深さだと、黒い円が広がる途中でにじみとちらついた）。
    """
    k, local = _inset_local(vfov_deg)
    cx, cy = center_px
    sun_r = sun_radius_px * k
    if glare > 0:
        g = sc.build_halo(sun_r * 0.94, GLARE_COLOR, 12.0 * glare, 1.55, "InsetGlare")
        _attach(g, cam, local(cx, cy, 0.94))
    if occulter > 0:
        bpy.ops.mesh.primitive_circle_add(vertices=128, radius=sun_r * 0.935 * 1.06 * occulter, fill_type='TRIFAN')
        disk = _attach(bpy.context.active_object, cam, local(cx, cy, 0.935))
        disk.name = "Coronagraph"
        disk.data.materials.append(sc.emission_material("CoronagraphBlack", (0, 0, 0, 1), 0.0))
    if haze > 0:
        hz = sc.build_halo(sun_r * 0.941 * 1.06, HAZE_COLOR, 0.9 * haze, 1.4, "InsetHaze")
        _attach(hz, cam, local(cx, cy, 0.941))
    if planet > 0 and planet_center_px:
        px_, py_ = planet_center_px
        img = ep1.build_planet_image(0, planet_radius_px, 1000, k * 0.999, opacity=planet)
        _attach(img, cam, local(px_, py_, 0.999))
        if streaks > 0:
            _planet_streaks(cam, local, k, planet_center_px, planet_radius_px, (cx, cy), sun_radius_px * ring_ratio,
                            streaks)


def _planet_streaks(cam, local, k, planet_px, planet_r_px, ring_center_px, ring_px, alpha, sources=5, per_source=18):
    """惑星の何か所か（海・陸・雲のつもり）から、輪の全周へ広がる細い光の筋。

    輪のどこが惑星のどこ、という対応はないので（台本の精度の注意）、どの点からも輪の全周へ広げる。
    太陽（と黒い円）より奥に置き、輪の向こう側へ回る筋は円盤に隠れる。
    """
    mat = ep1.translucent_emission("StreakGlow", PLANET_COLOR, 0.8, 0.35 * alpha)
    px_, py_ = planet_px
    rx, ry = ring_center_px
    for i in range(sources):
        a = 2 * math.pi * i / sources + 0.4
        sx, sy = px_ + 0.55 * planet_r_px * math.cos(a), py_ + 0.55 * planet_r_px * math.sin(a)
        for j in range(per_source):
            b = 2 * math.pi * (j + i / sources) / per_source
            ex, ey = rx + ring_px * math.cos(b), ry + ring_px * math.sin(b)
            sc.polyline(f"Streak_{i}_{j:02d}", [local(sx, sy, 1.002), local(ex, ey, 1.002)], mat, 0.8 * k).parent = cam


RING_LABEL = "アインシュタインリング"
RING_LABEL_PX = (720, 500)  # 視野の右上（真上だと「輪の発表」に見えるので斜めから指す: ユーザー「少し斜めにして」）
RING_LABEL_ANGLE = 50  # 線が輪に触れる位置（真上から右へ回った角度）


def build_ring_label(cam, vfov_deg, center_px, ring_px, alpha):
    """輪の名前を ep1 の「太陽」と同じ書き方の目印で添え、細い線で斜め上から輪を指す（c03）。
    名前は発表しない（ユーザー「結局アインシュタインリングでキメてるじゃん」）。"""
    if alpha <= 0:
        return
    k, local = _inset_local(vfov_deg)
    lx, ly = RING_LABEL_PX
    label = sc.text_label("RingLabel", RING_LABEL, 0, 0, sc.LABEL_PX * k, 'CENTER')
    label.data.materials[0] = ep1.translucent_emission("RingLabelGlow", sc.RULER_COLOR, sc.RULER_STRENGTH * 1.6, alpha)
    _attach(label, cam, local(lx, ly, 0.999))
    cx, cy = center_px
    a = math.radians(RING_LABEL_ANGLE)
    tip = (cx + (ring_px + 6) * math.sin(a), cy - (ring_px + 6) * math.cos(a))
    mat = ep1.translucent_emission("RingLabelLeader", sc.RULER_COLOR, ep1.VIEWFINDER_STRENGTH, alpha)
    sc.polyline("RingLabelLine", [local(lx - 40, ly + 30, 0.999), local(*tip, 0.999)], mat, 1.0 * k).parent = cam
