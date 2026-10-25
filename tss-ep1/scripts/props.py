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
def build_lens_scene(px, top_z, bottom_z, half_width_px, thickness_px, ray_x_px, focus_px, fade_px):
    """凸レンズの断面（中心が原点）と、上から平行に来てレンズで折れ、1点に集まる光線。"""
    w, t = half_width_px * px, thickness_px * px / 2
    xs = [w * (i / 40 - 1) for i in range(81)]
    outline = [(x, t * (1 - (x / w) ** 2)) for x in xs] + [(x, -t * (1 - (x / w) ** 2)) for x in reversed(xs)]
    _filled_shape("LensFill", outline, translucent_emission("LensFillGlow", LENS_EDGE_COLOR, 0.25, LENS_FILL_OPACITY))
    sc.polyline("LensEdge", [(x, -0.05, z) for x, z in outline + outline[:1]],
                sc.emission_material("LensEdgeGlow", LENS_EDGE_COLOR, LENS_EDGE_STRENGTH), 1.2 * px)

    f, fade = focus_px * px, fade_px * px
    mat = sc.z_ramp_material("LensRayFade", sc.RAY_COLOR, -f, -f - fade, sc.RAY_STRENGTH, sc.RAY_STRENGTH, 1.0, 0.0)
    end_depth = min(-bottom_z, f + fade)
    for i, xp in enumerate(ray_x_px):
        for side in (-1, 1):
            x = side * xp * px
            end_x = x - x / f * end_depth
            sc.polyline(f"LensRay_{i:02d}_{'L' if side < 0 else 'R'}",
                        [(x, 0, top_z), (x, 0, 0), (0, 0, -f), (end_x, 0, -end_depth)], mat, 0.9 * px)
    # 集まった点が小さく光る
    bpy.ops.mesh.primitive_uv_sphere_add(radius=4 * px, location=(0, -0.1, -f))
    dot = bpy.context.active_object
    dot.name = "FocusDot"
    dot.data.materials.append(sc.emission_material("FocusDotGlow", FOCUS_GLOW_COLOR, 20.0))
    halo = sc.build_halo(4 * px, FOCUS_GLOW_COLOR, 1.5, 6.0, "FocusHalo")
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


def build_unresolved_dot(center_z, px):
    """ふつうの望遠鏡で見た系外惑星（どれだけ拡大しても1つの光の点）。"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=3 * px, location=(0, 0, center_z))
    dot = bpy.context.active_object
    dot.name = "PlanetDot"
    dot.data.materials.append(sc.emission_material("PlanetDotGlow", (0.8, 0.9, 1.0, 1), 8.0))
    halo = sc.build_halo(3 * px, (0.6, 0.75, 1.0, 1), 0.8, 5.0, "PlanetDotHalo")
    halo.location.z = center_z
    return dot


def build_planet_image(center_z, radius_px, pixels, px, lon_center_deg=20.0, strength=1.0):
    """惑星の像（イメージ）。画面の上で pixels×pixels の格子にそろえたモザイクにする。

    円盤の各点を、格子の中心に寄せてから球の向きに戻し、地球の画像を引く（正距円筒図）。
    照らす向きはカメラ側の左上から（満ち欠けを少し付けて球に見せる）。
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

    lon = math_node('ADD', math_node('ARCTAN2', nx, ny), math.radians(lon_center_deg))
    u = math_node('ADD', math_node('DIVIDE', lon, 2 * math.pi), 0.5)
    v = math_node('ADD', math_node('DIVIDE', math_node('ARCSINE', math_node('MINIMUM', nz, 1.0)), math.pi), 0.5)
    uv = N.new('ShaderNodeCombineXYZ')
    L.new(u, uv.inputs['X'])
    L.new(v, uv.inputs['Y'])
    tex = N.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(EARTH_TEXTURE, check_existing=True)
    tex.extension = 'REPEAT'
    tex.interpolation = 'Closest'
    L.new(uv.outputs[0], tex.inputs['Vector'])

    # 照らす向き（画面の左上・手前から）
    lx, ly, lz = -0.45, 0.75, 0.48
    norm = math.sqrt(lx * lx + ly * ly + lz * lz)
    lit = math_node('ADD', math_node('MULTIPLY', nx, lx / norm), math_node('MULTIPLY', ny, ly / norm))
    lit = math_node('ADD', lit, math_node('MULTIPLY', nz, lz / norm))
    shade = math_node('ADD', math_node('MAXIMUM', lit, 0.0), 0.04)

    em = N.new('ShaderNodeEmission')
    L.new(tex.outputs['Color'], em.inputs['Color'])
    L.new(math_node('MULTIPLY', shade, strength), em.inputs['Strength'])
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(inside, mix.inputs['Fac'])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    out = N.new('ShaderNodeOutputMaterial')
    L.new(mix.outputs[0], out.inputs[0])
    disk.data.materials.append(mat)
    return disk
