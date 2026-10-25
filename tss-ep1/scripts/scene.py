"""ep1 の描画層（bpy）。光線・太陽・軸・星空・コンポジターを組む。

座標: 光線の面は XZ（X が横、Z が上）。太陽の中心が原点、軸は -Z へ伸びる。カメラは -Y から +Y を向く。
単位: 1 BU = AXIAL_AU_PER_BU AU（軸方向は実物比）。横方向だけ LATERAL_K 倍する（台本「実物/模式化」）。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

from physics import R_SUN, deflection_angle, focal_distance, to_au

EP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURE_DIR = os.path.join(EP_DIR, "textures")
SUN_TEXTURE = os.path.join(TEXTURE_DIR, "2k_sun.jpg")  # Solar System Scope（CC BY 4.0、投稿文にクレジット）
STARS_EXR = os.path.join(TEXTURE_DIR, "hiptyc_2020_16k_gal.exr")  # NASA SVS Deep Star Maps 2020（投稿文にクレジット）

RESOLUTION = (1080, 1920)
AXIAL_AU_PER_BU = 10.0
LATERAL_K = 3e4  # 横方向の拡大率（10-25に決定。2a・3a・3bで共通）
B_RATIOS = [1 + 2 * i / 12 for i in range(13)]  # b = 太陽半径の1〜3倍を13本（片側）

RAY_COLOR = (1.0, 0.72, 0.38, 1)
RAY_STRENGTH = 0.9
RAY_FADE_AU = 800  # 軸と交わってから消えるまでの距離
LINE_STRENGTH = (4.0, 12.0)  # 焦線の明るさ（548AUの始まり → 下端）。下ほど多くの光線が交わっている
AXIS_STRENGTH = 0.25
SUN_STRENGTH = 2.2
SUN_TINT_CENTER = (1.0, 0.62, 0.18, 1)  # 中心は明るい黄色寄り
SUN_TINT_LIMB = (1.0, 0.28, 0.03, 1)  # 縁は濃いオレンジ（周辺減光）
CORONA_COLOR = (1.0, 0.42, 0.08, 1)
CORONA_STRENGTH = 4.0
CORONA_EXTENT = 0.9  # 太陽の縁から、光が消えるまで（太陽半径の倍数）
CORONA_POWER = 2.0  # 大きいほど縁の近くに光が締まる
STAR_STRENGTH = 0.6

SUN_RADIUS_BU = to_au(R_SUN) * LATERAL_K / AXIAL_AU_PER_BU


def bu(au):
    return au / AXIAL_AU_PER_BU


def ray_lateral_bu(b_ratio):
    return b_ratio * SUN_RADIUS_BU


def ray_focus_bu(b_ratio):
    return bu(to_au(focal_distance(b_ratio * R_SUN)))


def apparent_angle_deg(b_ratio):
    return math.degrees(math.atan(LATERAL_K * deflection_angle(b_ratio * R_SUN)))


# ------------------------------------------------------------
# 材質
# ------------------------------------------------------------
def new_material(name):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat, mat.node_tree


def emission_material(name, color, strength):
    mat, nt = new_material(name)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = color
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat


def z_ramp_material(name, color, z_from, z_to, strength_from, strength_to, opacity_from=1.0, opacity_to=1.0):
    """Z に沿って明るさと不透明度が変わる発光。消える側を透かすので奥の星が隠れない（Rikenomics 第5章）。"""
    mat, nt = new_material(name)
    mat.surface_render_method = 'BLENDED'
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    coord = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    strength = nt.nodes.new('ShaderNodeMapRange')
    opacity = nt.nodes.new('ShaderNodeMapRange')
    for node, lo, hi in ((strength, strength_from, strength_to), (opacity, opacity_from, opacity_to)):
        node.clamp = True
        node.inputs['From Min'].default_value = z_from
        node.inputs['From Max'].default_value = z_to
        node.inputs['To Min'].default_value = lo
        node.inputs['To Max'].default_value = hi
        nt.links.new(sep.outputs['Z'], node.inputs['Value'])
    em.inputs['Color'].default_value = color
    nt.links.new(coord.outputs['Object'], sep.inputs[0])
    nt.links.new(strength.outputs[0], em.inputs['Strength'])
    nt.links.new(opacity.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return mat


def sun_material():
    mat, nt = new_material("SunSurface")
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(SUN_TEXTURE, check_existing=True)
    em.inputs['Strength'].default_value = SUN_STRENGTH
    # 中心が明るい黄色、縁が濃いオレンジ（カメラに向く度合いで混ぜる）
    facing = nt.nodes.new('ShaderNodeLayerWeight')
    facing.inputs['Blend'].default_value = 0.5
    limb = nt.nodes.new('ShaderNodeMix')
    limb.data_type = 'RGBA'
    limb.inputs['A'].default_value = SUN_TINT_CENTER
    limb.inputs['B'].default_value = SUN_TINT_LIMB
    nt.links.new(facing.outputs['Facing'], limb.inputs['Factor'])
    tint = nt.nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1.0
    nt.links.new(limb.outputs['Result'], tint.inputs['B'])
    nt.links.new(tex.outputs['Color'], tint.inputs['A'])
    nt.links.new(tint.outputs['Result'], em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs[0])
    return mat


# ------------------------------------------------------------
# 形
# ------------------------------------------------------------
def polyline(name, points, material, width_bu):
    data = bpy.data.curves.new(name, type='CURVE')
    data.dimensions = '3D'
    data.resolution_u = 1
    data.bevel_depth = width_bu / 2
    data.bevel_resolution = 2
    spline = data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1.0)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def build_rays(top_z, bottom_z, width_bu):
    """上から平行に来て太陽の面（z=0）で曲がり、焦点で軸と交わる光線。交わった先は薄れて消える。

    曲がりは実際には太陽のすぐ近く（軸方向に太陽半径の数倍、AUに比べて0）で起きるので、z=0 で折る。
    """
    rays = []
    for i, b_ratio in enumerate(B_RATIOS):
        x0 = ray_lateral_bu(b_ratio)
        f = ray_focus_bu(b_ratio)
        fade = z_ramp_material(f"RayFade_{i:02d}", RAY_COLOR, -f, -f - bu(RAY_FADE_AU), RAY_STRENGTH, RAY_STRENGTH, 1.0, 0.0)
        for side in (-1, 1):
            x = side * x0
            slope = -x / f  # z が 1 下がるごとの x の変化
            end_z = max(bottom_z, -f - bu(RAY_FADE_AU))
            end_x = x + slope * (-end_z)
            rays.append(polyline(f"Ray_{i:02d}_{'L' if side < 0 else 'R'}",
                                 [(x, 0, top_z), (x, 0, 0), (0, 0, -f), (end_x, 0, end_z)], fade, width_bu))
    return rays


def build_axis_and_line(top_z, bottom_z, axis_width_bu, line_width_bu):
    axis = polyline("Axis", [(0, 0, top_z), (0, 0, bottom_z)],
                    emission_material("AxisGlow", RAY_COLOR, AXIS_STRENGTH), axis_width_bu)
    f1, f3 = ray_focus_bu(B_RATIOS[0]), ray_focus_bu(B_RATIOS[-1])
    line_mat = z_ramp_material("FocalLineGlow", RAY_COLOR, -f1, -f3, *LINE_STRENGTH)
    line = polyline("FocalLine", [(0, -0.5, -f1), (0, -0.5, bottom_z)], line_mat, line_width_bu)
    return axis, line


def build_sun():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=SUN_RADIUS_BU, location=(0, 0, 0), segments=64, ring_count=32)
    sun = bpy.context.active_object
    sun.name = "Sun"
    bpy.ops.object.shade_smooth()  # プリミティブはフラットシェーディング（Rikenomics 第5章）
    sun.rotation_euler = (math.radians(20), 0, math.radians(35))
    sun.data.materials.append(sun_material())
    build_corona()
    return sun


def build_corona():
    """太陽の後ろの板に、縁から外へ薄れる光をノイズで揺らして描く（燃えている感じ）。加算なので奥の星は隠れない。"""
    size = SUN_RADIUS_BU * (1 + CORONA_EXTENT) * 2.2
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, SUN_RADIUS_BU * 1.5, 0), rotation=(math.radians(90), 0, 0))
    plane = bpy.context.active_object
    plane.name = "Corona"
    mat, nt = new_material("CoronaGlow")
    mat.surface_render_method = 'BLENDED'
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    coord = nt.nodes.new('ShaderNodeTexCoord')
    length = nt.nodes.new('ShaderNodeVectorMath')
    length.operation = 'LENGTH'
    falloff = nt.nodes.new('ShaderNodeMapRange')
    falloff.clamp = True
    falloff.inputs['From Min'].default_value = SUN_RADIUS_BU * 0.95
    falloff.inputs['From Max'].default_value = SUN_RADIUS_BU * (1 + CORONA_EXTENT)
    falloff.inputs['To Min'].default_value = 1.0
    falloff.inputs['To Max'].default_value = 0.0
    power = nt.nodes.new('ShaderNodeMath')
    power.operation = 'POWER'
    power.inputs[1].default_value = CORONA_POWER
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.noise_dimensions = '4D'  # W を動かせば揺らめく（アニメーション用）
    noise.inputs['Scale'].default_value = 3.0 / SUN_RADIUS_BU
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Distortion'].default_value = 1.5
    flicker = nt.nodes.new('ShaderNodeMapRange')
    flicker.inputs['From Min'].default_value = 0.35
    flicker.inputs['From Max'].default_value = 0.65
    flicker.inputs['To Min'].default_value = 0.15
    flicker.inputs['To Max'].default_value = 2.0
    shape = nt.nodes.new('ShaderNodeMath')
    shape.operation = 'MULTIPLY'
    gain = nt.nodes.new('ShaderNodeMath')
    gain.operation = 'MULTIPLY'
    gain.inputs[1].default_value = CORONA_STRENGTH
    em.inputs['Color'].default_value = CORONA_COLOR
    nt.links.new(coord.outputs['Object'], length.inputs[0])
    nt.links.new(length.outputs['Value'], falloff.inputs['Value'])
    nt.links.new(falloff.outputs[0], power.inputs[0])
    direction = nt.nodes.new('ShaderNodeVectorMath')
    direction.operation = 'NORMALIZE'
    radial = nt.nodes.new('ShaderNodeVectorMath')
    radial.operation = 'SCALE'
    radial.inputs['Scale'].default_value = 0.15  # 外向きにはゆっくり変わる（筋になる）
    streak = nt.nodes.new('ShaderNodeVectorMath')
    streak.operation = 'MULTIPLY_ADD'
    streak.inputs[1].default_value = (SUN_RADIUS_BU * 2.5,) * 3
    nt.links.new(coord.outputs['Object'], direction.inputs[0])
    nt.links.new(coord.outputs['Object'], radial.inputs[0])
    nt.links.new(direction.outputs[0], streak.inputs[0])
    nt.links.new(radial.outputs[0], streak.inputs[2])
    nt.links.new(streak.outputs[0], noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'], flicker.inputs['Value'])
    nt.links.new(power.outputs[0], shape.inputs[0])
    nt.links.new(flicker.outputs[0], shape.inputs[1])
    nt.links.new(shape.outputs[0], gain.inputs[0])
    nt.links.new(gain.outputs[0], em.inputs['Strength'])
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    plane.data.materials.append(mat)
    return plane


# ------------------------------------------------------------
# 背景・カメラ・レンダー
# ------------------------------------------------------------
def build_world():
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = STAR_STRENGTH
    tex = nt.nodes.new('ShaderNodeTexEnvironment')
    tex.image = bpy.data.images.load(STARS_EXR, check_existing=True)
    tex.interpolation = 'Cubic'
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    # 天の川の帯が画面に入らない向き（銀河の極の方向を見る）
    mapping.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    nt.links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs[0], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs[0])


def build_camera(center_z, view_height_bu, vfov_deg):
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.sensor_fit = 'VERTICAL'  # 縦型は AUTO だと長辺に当たる（Rikenomics 第5章）
    cam_data.angle = math.radians(vfov_deg)
    distance = view_height_bu / 2 / math.tan(math.radians(vfov_deg) / 2)
    cam_data.clip_start = 1.0
    cam_data.clip_end = distance * 4
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (0, -distance, center_z)
    cam.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = cam
    return cam


def build_compositor(scene):
    ng = bpy.data.node_groups.new("Ep1Compositor", 'CompositorNodeTree')
    ng.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    scene.compositing_node_group = ng
    rl = ng.nodes.new('CompositorNodeRLayers')
    glare = ng.nodes.new('CompositorNodeGlare')
    glare.inputs['Type'].default_value = 'Fog Glow'
    glare.inputs['Quality'].default_value = 'High'
    glare.inputs['Threshold'].default_value = 1.0
    glare.inputs['Size'].default_value = 0.8
    glare.inputs['Strength'].default_value = 0.8
    out = ng.nodes.new('NodeGroupOutput')
    ng.links.new(rl.outputs['Image'], glare.inputs['Image'])
    ng.links.new(glare.outputs['Image'], out.inputs['Image'])


def setup_render(scene, resolution_percentage=100):
    engine_ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engine_ids else 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = resolution_percentage
    scene.render.image_settings.file_format = 'PNG'
    # AgX は明るいオレンジがピンクに抜けた。Standard は明るいほど オレンジ→黄→白 になり、炎に見える
    scene.view_settings.view_transform = 'Standard'
    build_world()
    build_compositor(scene)


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.materials, bpy.data.curves, bpy.data.meshes, bpy.data.cameras, bpy.data.node_groups):
        for item in list(block):
            block.remove(item)
