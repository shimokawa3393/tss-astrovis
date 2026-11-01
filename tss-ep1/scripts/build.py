"""状態（state.scene_state / state.LAYOUTS）から、そのフレームの絵を組む（bpy）。

毎フレーム組み直す。線の太さを画面の画素で決めているので、引き（3a）や下り（3b）の間も線が細いまま保てる。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy

import props
import scene as sc

VFOV_DEG = 30


def build_frame(s, percentage=100):
    """s を組んでカメラとレンダー設定まで済ませる。ログ用の1行を返す。"""
    sc.clear_scene()
    kind = s.get("kind", "rays")
    scene = bpy.context.scene
    if kind == "black":
        sc.build_camera(0, 19.2, VFOV_DEG)
        sc.setup_render(scene, percentage)
        return "暗転"

    view_h = s["view_h_bu"]
    top_z = -sc.bu(s["anchor_au"]) + s["anchor_from_top"] * view_h
    bottom_z = top_z - view_h
    px = view_h / sc.RESOLUTION[1]
    margin = 10 * px
    log = ""

    if kind == "probe":
        props.build_probe_view(s["sun_from_top"], s["probe_offset"], s["vfov_deg"], s["inset_center_px"],
                               s["inset_radius_px"], s["inset_sun_radius_px"], s.get("inset_grow", 1.0),
                               s.get("ring_alpha", 1.0))
        log = f"視野の開き={s.get('inset_grow', 1.0):.2f} 輪={s.get('ring_alpha', 1.0):.2f}"
    elif kind == "lens":
        props.build_lens_scene(px, top_z + margin, bottom_z - margin, half_width_px=460, thickness_px=80,
                               ray_x_px=[80, 160, 240, 320, 400], focus_px=0.35 * sc.RESOLUTION[1], fade_px=300,
                               front_z=s.get("front_z"))
    elif kind == "planet":
        props.build_viewfinder(0, 380, px)
        if s.get("dot_fade", 0 if s["pixels"] else 1) > 0:
            props.build_unresolved_dot(0, px, s.get("dot_fade", 1.0))
        if s["pixels"]:
            props.build_planet_image(0, 330, s["pixels"], px, opacity=s.get("image_opacity", 1.0))
        log = f"画素={s['pixels']}"
    else:
        sun_r = s["sun_radius_px"] * px if "sun_radius_px" in s else None
        sc.build_sun(sun_r, s.get("sun_fade", 1.0))
        fronts = s.get("fronts")
        sc.build_rays(max(top_z, 0) + margin, bottom_z - margin, 0.9 * px, s["b_ratios"], s.get("alphas"), fronts)
        line_end_z = -sc.bu(s["line_end_au"]) if "line_end_au" in s else None
        sc.build_axis_and_line(top_z + margin, bottom_z - margin, 0.8 * px, 2.5 * px, s["show_line"], line_end_z)
        if "ruler_au" in s:
            sc.build_ruler(s["ruler_au"], px)
        if s.get("neptune"):
            sc.build_neptune(20 * px, -150 * px, 26 * px)
        # 誇張の値（台本の「実物/模式化」と突き合わせる）
        log = (f"深さ={s['anchor_au']:.1f}AU 1px={px * sc.AXIAL_AU_PER_BU:.3f}AU "
               f"太陽の円の半径={(sun_r or sc.SUN_DRAW_RADIUS_BU) / px:.0f}px 横{sc.LATERAL_K:.0f}倍 "
               f"見かけの曲がり角 b=R {sc.apparent_angle_deg(1):.1f}°（実物 1.75秒角）")
    if kind != "probe":
        sc.build_camera(top_z - view_h / 2, view_h, VFOV_DEG)
    sc.setup_render(scene, percentage)
    return log
