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


def _lens(px, top_z, bottom_z, front_z, ray_alpha, lens_alpha, shrink_to_px=None):
    """1aのレンズ。2aの頭では、薄れながら太陽の幅まで縮み、太陽の後ろに入る（shrink_to_px）。
    同じ大きさのまま薄れると、太陽に輪がかかって土星に見えた（11-01）。"""
    half_width, thickness = 460, 80
    if shrink_to_px is not None:
        half_width = shrink_to_px + (half_width - shrink_to_px) * lens_alpha
        thickness *= lens_alpha
    props.build_lens_scene(px, top_z, bottom_z, half_width_px=half_width, thickness_px=thickness,
                           ray_x_px=[80, 160, 240, 320, 400],
                           focus_px=0.35 * sc.RESOLUTION[1], fade_px=300, front_z=front_z, ray_alpha=ray_alpha,
                           lens_alpha=lens_alpha)


def build_frame(s, percentage=100):
    """s を組んでカメラとレンダー設定まで済ませる。ログ用の1行を返す。"""
    sc.clear_scene()
    kind = s.get("kind", "rays")
    scene = bpy.context.scene
    if kind == "space":
        sc.build_camera(0, 19.2, VFOV_DEG)
        sc.setup_render(scene, percentage)
        return "星だけ"

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
        _lens(px, top_z + margin, bottom_z - margin, s.get("front_z"), s.get("ray_alpha", 1.0), 1.0)
    elif kind == "planet":
        props.build_viewfinder(0, 380, px)
        if s.get("dot_fade", 0 if s["pixels"] else 1) > 0:
            props.build_unresolved_dot(0, px, s.get("dot_fade", 1.0))
        if s["pixels"]:
            props.build_planet_image(0, 330, s["pixels"], px, opacity=s.get("image_opacity", 1.0))
        log = f"画素={s['pixels']}"
    else:
        sun_r = s["sun_radius_px"] * px if "sun_radius_px" in s else None
        if s.get("lens_alpha", 0) > 0:  # 2aの頭: 1aのレンズが同じ所で薄れていく
            _lens(px, top_z + margin, bottom_z - margin, None, 0.0, s["lens_alpha"],
                  0.8 * (sun_r or sc.SUN_DRAW_RADIUS_BU) / px)
        sc.build_sun(sun_r, s.get("sun_fade", 1.0))
        fronts = s.get("fronts")
        sc.build_rays(max(top_z, 0) + margin, bottom_z - margin, 0.9 * px, s["b_ratios"], s.get("alphas"), fronts)
        line_end_z = -sc.bu(s["line_end_au"]) if "line_end_au" in s else None
        sc.build_axis_and_line(top_z + margin, bottom_z - margin, 0.8 * px, 2.5 * px, s["show_line"], line_end_z)
        if "ruler_au" in s:
            sc.build_ruler(s["ruler_au"], px)
        if s.get("neptune"):
            sc.build_neptune(20 * px, -150 * px, 26 * px)
        if s.get("voyager"):
            sc.build_voyager(-150 * px, px)
        # 誇張の値（台本の「実物/模式化」と突き合わせる）
        log = (f"深さ={s['anchor_au']:.1f}AU 1px={px * sc.AXIAL_AU_PER_BU:.3f}AU "
               f"太陽の円の半径={(sun_r or sc.SUN_DRAW_RADIUS_BU) / px:.0f}px 横{sc.LATERAL_K:.0f}倍 "
               f"見かけの曲がり角 b=R {sc.apparent_angle_deg(1):.1f}°（実物 1.75秒角）")
    if kind != "probe":
        sc.build_camera(top_z - view_h / 2, view_h, VFOV_DEG)
    sc.setup_render(scene, percentage)
    return log
