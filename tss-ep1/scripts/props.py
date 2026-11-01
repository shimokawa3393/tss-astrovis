"""ep1 の小道具（bpy）: 1a のレンズ、4b の惑星の像と望遠鏡の視野。光線まわりの共通部品は scene.py。

座標は scene.py と同じ（XZ 面、カメラは -Y から）。長さは px_bu（1px あたりの BU）を掛けて画面の画素で指定する。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

import scene as sc

EARTH_TEXTURE = os.path.join(sc.TEXTURE_DIR, "2k_earth_daymap.jpg")  # Solar System Scope（CC BY 4.0）

LENS_EDGE_COLOR = (0.75, 0.88, 1.0, 1)
LENS_EDGE_STRENGTH = 1.2
LENS_FILL_OPACITY = 0.06
FOCUS_GLOW_COLOR = (1.0, 0.85, 0.6, 1)
VIEWFINDER_STRENGTH = 0.35


def _filled_shape(name, outline, material):
    """XZ 面の閉じた輪郭を、扇形に三角形を張って塗る。"""
    verts = [(0, 0.05, 0)] + [(x, 0.05, z) for x, z in outline]
    n = len(outline)
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def translucent_emission(name, color, strength, opacity):
    mat, nt = sc.new_material(name)
    mat.surface_render_method = 'BLENDED'
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    em.inputs['Color'].default_value = color
    em.inputs['Strength'].default_value = strength
    mix.inputs['Fac'].default_value = opacity
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return mat


# ------------------------------------------------------------
# 1a: レンズ
# ------------------------------------------------------------
def _clip_below(points, z_min):
    """上から下へ並んだ点の列を、z_min より上だけにする（光線が上から伸びていく途中）。"""
    out = [points[0]]
    for a, b in zip(points, points[1:]):
        if b[2] >= z_min:
            out.append(b)
            continue
        t = (a[2] - z_min) / (a[2] - b[2])
        out.append(tuple(a[k] + (b[k] - a[k]) * t for k in range(3)))
        break
    return out


def build_lens_scene(px, top_z, bottom_z, half_width_px, thickness_px, ray_x_px, focus_px, fade_px, front_z=None,
                     ray_alpha=1.0, lens_alpha=1.0):
    """凸レンズの断面（中心が原点）と、上から平行に来てレンズで折れ、1点に集まる光線。

    front_z を渡すと、光線はそこまで（上から伸びていく途中）。集まる点は光線が届いてから光る。
    ray_alpha: 光線と集まる点の明るさ（1aの終わりで消える）。lens_alpha: レンズの明るさ（2aの頭で太陽と入れ替わる）。
    """
    w, t = half_width_px * px, thickness_px * px / 2
    xs = [w * (i / 40 - 1) for i in range(81)]
    outline = [(x, t * (1 - (x / w) ** 2)) for x in xs] + [(x, -t * (1 - (x / w) ** 2)) for x in reversed(xs)]
    if lens_alpha > 0:
        _filled_shape("LensFill", outline, translucent_emission("LensFillGlow", LENS_EDGE_COLOR, 0.25,
                                                                LENS_FILL_OPACITY * lens_alpha))
        sc.polyline("LensEdge", [(x, -0.05, z) for x, z in outline + outline[:1]],
                    translucent_emission("LensEdgeGlow", LENS_EDGE_COLOR, LENS_EDGE_STRENGTH, lens_alpha), 1.2 * px)

    f, fade = focus_px * px, fade_px * px
    mat = sc.z_ramp_material("LensRayFade", sc.RAY_COLOR, -f, -f - fade, sc.RAY_STRENGTH, sc.RAY_STRENGTH,
                             ray_alpha, 0.0)
    end_depth = min(-bottom_z, f + fade)
    front_z = bottom_z if front_z is None else front_z
    if front_z >= top_z or ray_alpha <= 0:
        return
    for i, xp in enumerate(ray_x_px):
        for side in (-1, 1):
            x = side * xp * px
            end_x = x - x / f * end_depth
            sc.polyline(f"LensRay_{i:02d}_{'L' if side < 0 else 'R'}",
                        _clip_below([(x, 0, top_z), (x, 0, 0), (0, 0, -f), (end_x, 0, -end_depth)], front_z), mat,
                        0.9 * px)
    if front_z > -f:
        return
    # 集まった点が小さく光る
    bpy.ops.mesh.primitive_uv_sphere_add(radius=4 * px, location=(0, -0.1, -f))
    dot = bpy.context.active_object
    dot.name = "FocusDot"
    dot.data.materials.append(sc.emission_material("FocusDotGlow", FOCUS_GLOW_COLOR, 20.0 * ray_alpha))
    halo = sc.build_halo(4 * px, FOCUS_GLOW_COLOR, 1.5 * ray_alpha, 6.0, "FocusHalo")
    halo.location.z = -f


# ------------------------------------------------------------
# 4b: 望遠鏡の視野と惑星の像
# ------------------------------------------------------------
def build_viewfinder(center_z, radius_px, px):
    """望遠鏡の視野を表す細い円。前半（光の点）と後半（像）で同じ枠を使う。"""
    pts = [(radius_px * px * math.cos(a), -0.2, center_z + radius_px * px * math.sin(a))
           for a in (2 * math.pi * i / 180 for i in range(181))]
    return sc.polyline("Viewfinder", pts, sc.emission_material("ViewfinderGlow", sc.RULER_COLOR, VIEWFINDER_STRENGTH),
                       1.2 * px)


def build_unresolved_dot(center_z, px, fade=1.0):
    """ふつうの望遠鏡で見た系外惑星（どれだけ拡大しても1つの光の点）。fade は明るさの倍率。"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3 * px, location=(0, 0, center_z))
    dot = bpy.context.active_object
    dot.name = "PlanetDot"
    dot.data.materials.append(sc.emission_material("PlanetDotGlow", (0.8, 0.9, 1.0, 1), 8.0 * fade))
    halo = sc.build_halo(3 * px, (0.6, 0.75, 1.0, 1), 0.8 * fade, 5.0, "PlanetDotHalo")
    halo.location.z = center_z
    return dot


def build_planet_image(center_z, radius_px, pixels, px, lon_center_deg=122.0, lat_center_deg=32.0, strength=1.0,
                       opacity=1.0):
    """惑星の像（イメージ）。画面の上で pixels×pixels の格子にそろえたモザイクにする。

    円盤の各点を、格子の中心に寄せてから球の向きに戻し、地球の画像を引く（正距円筒図）。
    照らす向きはカメラ側の左上から（満ち欠けを少し付けて球に見せる）。
    正面に来るのは (lat_center_deg, lon_center_deg)。既定は日本を少し右に置く向き（10-25ユーザー「日本中心に」→「日本がちょい右にズレてる感じで」）。
    """
    rp = radius_px * px
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=rp, fill_type='TRIFAN', location=(0, 0, center_z),
                                      rotation=(math.radians(90), 0, 0))
    disk = bpy.context.active_object
    disk.name = "PlanetImage"

    mat, nt = sc.new_material("PlanetImageSurface")
    mat.surface_render_method = 'BLENDED'
    N, L = nt.nodes, nt.links

    def math_node(op, a=None, b=None):
        m = N.new('ShaderNodeMath')
        m.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                L.new(v, m.inputs[i])
        return m.outputs[0]

    coord = N.new('ShaderNodeTexCoord')
    # 円盤はX軸まわりに90°回してあるので、ローカルの (x, y) が画面の (横, 縦)
    cell = 2 * rp / pixels
    snap = N.new('ShaderNodeVectorMath')
    snap.operation = 'SNAP'
    snap.inputs[1].default_value = (cell, cell, cell)
    L.new(coord.outputs['Object'], snap.inputs[0])
    shift = N.new('ShaderNodeVectorMath')
    shift.operation = 'ADD'
    shift.inputs[1].default_value = (cell / 2, cell / 2, 0)
    L.new(snap.outputs[0], shift.inputs[0])
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(shift.outputs[0], sep.inputs[0])
    nx = math_node('DIVIDE', sep.outputs['X'], rp)
    nz = math_node('DIVIDE', sep.outputs['Y'], rp)
    r2 = math_node('ADD', math_node('MULTIPLY', nx, nx), math_node('MULTIPLY', nz, nz))
    ny = math_node('SQRT', math_node('MAXIMUM', math_node('SUBTRACT', 1.0, r2), 0.0))
    inside = math_node('LESS_THAN', r2, 1.0)

    # 画面の正面が緯度 lat_center_deg になるよう、X軸まわりに傾けてから緯度・経度を取る
    c, s_ = math.cos(math.radians(lat_center_deg)), math.sin(math.radians(lat_center_deg))
    nz_r = math_node('ADD', math_node('MULTIPLY', nz, c), math_node('MULTIPLY', ny, s_))
    ny_r = math_node('SUBTRACT', math_node('MULTIPLY', ny, c), math_node('MULTIPLY', nz, s_))
    lon = math_node('ADD', math_node('ARCTAN2', nx, ny_r), math.radians(lon_center_deg))
    u = math_node('ADD', math_node('DIVIDE', lon, 2 * math.pi), 0.5)
    v = math_node('ADD', math_node('DIVIDE', math_node('ARCSINE', math_node('MINIMUM', nz_r, 1.0)), math.pi), 0.5)
    uv = N.new('ShaderNodeCombineXYZ')
    L.new(u, uv.inputs['X'])
    L.new(v, uv.inputs['Y'])
    tex = N.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(EARTH_TEXTURE, check_existing=True)
    tex.extension = 'REPEAT'
    tex.interpolation = 'Closest'
    L.new(uv.outputs[0], tex.inputs['Vector'])

    # 照らす向き（画面の左上・手前から）
    lx, ly, lz = -0.2, 0.8, 0.45
    norm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lit = math_node('ADD', math_node('MULTIPLY', nx, lx / norm), math_node('MULTIPLY', ny, ly / norm))
    lit = math_node('ADD', lit, math_node('MULTIPLY', nz, lz / norm))
    shade = math_node('ADD', math_node('MAXIMUM', lit, 0.0), 0.04)

    em = N.new('ShaderNodeEmission')
    L.new(tex.outputs['Color'], em.inputs['Color'])
    L.new(math_node('MULTIPLY', shade, strength), em.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(math_node('MULTIPLY', inside, opacity), mix.inputs['Fac'])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    out = N.new('ShaderNodeOutputMaterial')
    L.new(mix.outputs[0], out.inputs[0])
    disk.data.materials.append(mat)
    return disk


# ------------------------------------------------------------
# 4a: 1200AUの探査機と、太陽のまわりの光の輪（アインシュタインリング）
# ------------------------------------------------------------
PROBE_DISTANCE_AU = 1200  # 論文で像を集める位置（台本: 548AUは最短の理論値、4aの探査機は1200AU）
RING_COLOR = (0.8, 0.9, 1.0, 1)  # 4bの光の点と同じ青白（輪が4bの惑星の光だとつながるように）
RING_STRENGTH = 6.0
PROBE_HULL_COLOR = (0.55, 0.55, 0.58, 1)
PROBE_FOIL_COLOR = (0.75, 0.55, 0.2, 1)  # 本体の断熱材（金色の箔）


def einstein_ring_ratio(distance_au=PROBE_DISTANCE_AU):
    """探査機から見た輪の半径 / 太陽の半径。輪を作る光線の b は焦点距離 F ∝ b² から b = R√(z/F(R))。"""
    from physics import R_SUN, focal_distance, to_au
    return math.sqrt(distance_au / to_au(focal_distance(R_SUN)))


def _metal(name, color, roughness=0.45, metallic=0.8):
    mat, nt = sc.new_material(name)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return mat


def _cylinder(name, radius, depth, location, material, rotation=(0, 0, 0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation,
                                        vertices=vertices)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(material)
    return obj


def build_probe(scale):
    """記号的な探査機。口径1mの望遠鏡の筒が +Y（太陽の方）を向く。原点が筒の後ろの端。"""
    # 金属にすると黒い宇宙を映して真っ黒になるので、金属感は弱くする
    hull = _metal("ProbeHull", PROBE_HULL_COLOR, roughness=0.5, metallic=0.2)
    foil = _metal("ProbeFoil", PROBE_FOIL_COLOR, roughness=0.4, metallic=0.3)
    dark = _metal("ProbeDark", (0.02, 0.02, 0.02, 1), roughness=0.9, metallic=0.0)
    s = scale
    parts = []
    # 望遠鏡の筒（前の口は暗い内側が見える）
    parts.append(_cylinder("ProbeTube", 0.5 * s, 1.6 * s, (0, 0.8 * s, 0), hull, (math.radians(90), 0, 0)))
    parts.append(_cylinder("ProbeTubeInner", 0.46 * s, 0.02 * s, (0, 1.59 * s, 0), dark, (math.radians(90), 0, 0)))
    # 本体（筒の後ろの箱、金色の箔）。筒より細くして、後ろから見ても筒が隠れないようにする
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.3 * s, 0))
    box = bpy.context.active_object
    box.name = "ProbeBus"
    box.scale = (0.6 * s, 0.6 * s, 0.6 * s)
    box.data.materials.append(foil)
    parts.append(box)
    # 電源（RTG）を左右の腕の先に
    for side in (-1, 1):
        parts.append(_cylinder(f"ProbeBoom_{side}", 0.03 * s, 1.6 * s, (side * 1.1 * s, -0.3 * s, 0), hull,
                               (0, math.radians(90), 0), 12))
        parts.append(_cylinder(f"ProbeRTG_{side}", 0.16 * s, 0.6 * s, (side * 1.9 * s, -0.3 * s, 0), dark,
                               (0, math.radians(90), 0), 24))
    return parts


def _attach_to_camera(obj, cam):
    obj.parent = cam
    obj.matrix_parent_inverse.identity()
    return obj


def build_telescope_inset(cam, vfov_deg, center_px, radius_px, sun_radius_px, from_px, grow=1.0, ring_alpha=1.0):
    """探査機の望遠鏡の視野（4bと同じ細い円）。中に太陽の円盤と光の輪を描き、from_px（太陽の点）から広がる線でつなぐ。

    1200AUでは太陽は約1.6秒角、輪は約2.4秒角で、目には点にしか見えない。口径1mの望遠鏡なら分けて見える（11-01）。
    カメラの前（カメラの座標で -Z に1）に貼るので、画面の画素でそのまま置ける。
    grow: 0 で視野は太陽の点に重なって大きさ0、1 で決めた位置と大きさ（動画で点から視野がピュッと開く。1を少し超えてよい）。
    ring_alpha: 光の輪の明るさ（視野が開いてから輪が灯る）。
    """
    k = math.tan(math.radians(vfov_deg) / 2) / (sc.RESOLUTION[1] / 2)  # 1px の長さ（カメラから1の距離で）
    w, h = sc.RESOLUTION

    def local(sx, sy, depth=1.0):
        return ((sx - w / 2) * k * depth, (h / 2 - sy) * k * depth, -depth)

    # 点の脇に「太陽」（海王星の目印と同じ書き方。動画ではこの点から視野がピュッと開く: 11-01ユーザー）
    fx, fy = from_px
    label = sc.text_label("SunDotLabel", "太陽", 0, 0, 26 * k)
    _attach_to_camera(label, cam)
    label.location = local(fx + 22, fy, 0.999)
    label.rotation_euler = (0, 0, 0)
    if grow <= 0.01:
        return

    # 視野の中心は太陽の点から決めた位置へ移り、大きさは grow 倍
    cx, cy = fx + (center_px[0] - fx) * grow, fy + (center_px[1] - fy) * grow
    radius_px, sun_radius_px = radius_px * grow, sun_radius_px * grow
    # 視野の中は黒く塗り、後ろの星と探査機を隠す
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=radius_px * k * 1.01, fill_type='TRIFAN',
                                      location=local(cx, cy, 1.01))
    backing = _attach_to_camera(bpy.context.active_object, cam)
    backing.name = "InsetBacking"
    backing.data.materials.append(sc.emission_material("InsetBackingBlack", (0, 0, 0, 1), 0.0))

    circle = [local(cx + radius_px * math.cos(a), cy + radius_px * math.sin(a), 0.999)
              for a in (2 * math.pi * i / 180 for i in range(181))]
    _attach_to_camera(sc.polyline("InsetViewfinder", circle,
                                  sc.emission_material("InsetViewfinderGlow", sc.RULER_COLOR, VIEWFINDER_STRENGTH),
                                  1.2 * k), cam)
    # 太陽の点から視野の円に接する2本の線（拡大していることを示す）
    d = math.hypot(cx - fx, cy - fy)
    base = math.atan2(cy - fy, cx - fx)
    spread = math.asin(radius_px / d)
    leader = sc.emission_material("InsetLeaderGlow", sc.RULER_COLOR, VIEWFINDER_STRENGTH * 0.6)
    tangent_len = math.sqrt(d * d - radius_px * radius_px)
    for side in (-1, 1):
        a = base + side * spread
        start = 14  # 太陽の点のにじみに重ならないよう少し離す
        if tangent_len <= start:
            continue
        _attach_to_camera(sc.polyline(f"InsetLeader_{side}",
                                      [local(fx + start * math.cos(a), fy + start * math.sin(a), 0.999),
                                       local(fx + tangent_len * math.cos(a), fy + tangent_len * math.sin(a), 0.999)],
                                      leader, 1.0 * k), cam)

    # 太陽の円盤（にじみは輪が埋もれないよう小さく）と光の輪
    sun_r = sun_radius_px * k
    bpy.ops.mesh.primitive_uv_sphere_add(radius=sun_r, location=local(cx, cy, 1.0), segments=64, ring_count=32)
    sun = _attach_to_camera(bpy.context.active_object, cam)
    sun.name = "InsetSun"
    bpy.ops.object.shade_smooth()
    sun.rotation_euler = (math.radians(20), 0, math.radians(35))
    sun.data.materials.append(sc.sun_material())
    halo = sc.build_halo(sun_r, extent=0.6, strength=0.5, name="InsetSunHalo")
    _attach_to_camera(halo, cam)
    halo.location = local(cx, cy, 1.0 + sun_r * 1.5)
    halo.rotation_euler = (0, 0, 0)
    if ring_alpha <= 0:
        return
    ring_px = sun_radius_px * einstein_ring_ratio()
    ring = [local(cx + ring_px * math.cos(a), cy + ring_px * math.sin(a), 0.998)
            for a in (2 * math.pi * i / 240 for i in range(241))]
    _attach_to_camera(sc.polyline("EinsteinRing", ring, sc.emission_material("EinsteinRingGlow", RING_COLOR,
                                                                              RING_STRENGTH * ring_alpha), 2.5 * k), cam)


def build_probe_view(sun_from_top, probe_offset, vfov_deg, inset_center_px, inset_radius_px, inset_sun_radius_px,
                     inset_grow=1.0, ring_alpha=1.0, sun_distance=4000.0):
    """探査機の後ろ上から、太陽の方を見る。目で見た太陽は明るい点。円盤と輪は望遠鏡の視野の中に描く。

    太陽は +Y のずっと先。探査機は原点で +Y を向く。カメラは probe_offset（探査機から見た位置）に置き、
    太陽が画面の上から sun_from_top、横は中央に来るよう、太陽の方向から傾ける。
    """
    import mathutils
    w, h = sc.RESOLUTION
    tan_half = math.tan(math.radians(vfov_deg) / 2)
    cam_loc = mathutils.Vector(probe_offset)
    sun_loc = mathutils.Vector((cam_loc.x, sun_distance, cam_loc.z))  # 太陽はカメラの真正面の方向（横は中央）
    pitch = math.atan((0.5 - sun_from_top) * 2 * tan_half)  # 正なら太陽が中心より上（カメラを下へ傾ける）
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.sensor_fit = 'VERTICAL'
    cam_data.angle = math.radians(vfov_deg)
    cam_data.clip_start = 0.05
    cam_data.clip_end = sun_distance * 2
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (math.radians(90) - pitch, 0, 0)
    bpy.context.scene.camera = cam

    # 目で見た太陽: 明るい点とにじみ（1200AUでは約1.6秒角、約-11等）
    dist = (sun_loc - cam_loc).length
    px = dist * tan_half / (h / 2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=4 * px, location=sun_loc)
    dot = bpy.context.active_object
    dot.name = "SunDot"
    dot.data.materials.append(sc.emission_material("SunDotGlow", FOCUS_GLOW_COLOR, 20.0))
    halo = sc.build_halo(4 * px, FOCUS_GLOW_COLOR, 1.5, 8.0, "SunDotHalo")
    halo.location = sun_loc + mathutils.Vector((0, 4 * px * 1.5, 0))

    build_telescope_inset(cam, vfov_deg, inset_center_px, inset_radius_px, inset_sun_radius_px,
                          (w / 2, sun_from_top * h), inset_grow, ring_alpha)

    # 探査機を太陽の光（筒の前から）と、弱い星明かり（カメラ側の左上から）で照らす
    build_probe(1.0)
    key = bpy.data.lights.new("SunLight", type='SUN')
    key.energy = 3.0
    key_obj = bpy.data.objects.new("SunLight", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.rotation_euler = (math.radians(-90), 0, 0)  # +Y から -Y へ
    fill = bpy.data.lights.new("FillLight", type='SUN')
    fill.energy = 2.0
    fill.color = (0.75, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(60), 0, math.radians(-30))
    return cam
