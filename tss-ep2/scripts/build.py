"""状態（state.LAYOUTS）から、そのフレームの絵を組む（bpy）。静止画と連番で共有する。毎フレーム組み直す。"""
import math

import bpy

import draw
from common import ep1, sc
from state import VIEW_H_BU

VFOV_DEG = 30


def build_frame(s, percentage=100):
    """s を組んでカメラとレンダー設定まで済ませる。ログ用の1行を返す。"""
    sc.clear_scene()
    scene = bpy.context.scene
    kind = s["kind"]
    log = ""

    if kind == "space":
        sc.build_camera(0, VIEW_H_BU, VFOV_DEG)
        log = "星だけ"
    elif kind == "probe":
        cam = ep1.build_probe_view(s["sun_from_top"], s["probe_offset"], s["vfov_deg"], s["inset_center_px"],
                                   s["inset_radius_px"], s["inset_sun_radius_px"], s.get("inset_grow", 1.0),
                                   s.get("ring_alpha", 1.0))
        draw.build_inset_extras(cam, s["vfov_deg"], s["inset_center_px"], s["inset_sun_radius_px"],
                                ep1.einstein_ring_ratio(), s.get("glare", 0.0), s.get("occulter", 0.0),
                                s.get("haze", 0.0), s.get("planet", 0.0), s.get("streaks", 0.0),
                                s.get("planet_center_px"), s.get("planet_radius_px", 60))
        draw.build_ring_label(cam, s["vfov_deg"], s["inset_center_px"],
                              s["inset_sun_radius_px"] * ep1.einstein_ring_ratio(), s.get("ring_label", 0.0))
        log = f"輪の半径=太陽の{ep1.einstein_ring_ratio():.2f}倍"
    elif kind == "side":
        view_h = VIEW_H_BU
        px = view_h / sc.RESOLUTION[1]
        top_z = s["sun_from_top"] * view_h  # 太陽の中心（原点）が上から sun_from_top
        planet_z = draw.screen_z(s["planet_from_top"], view_h, top_z)
        probe_z = draw.screen_z(s["probe_from_top"], view_h, top_z)
        sun_r = s["sun_radius_px"] * px
        sc.build_sun(sun_r, s.get("sun_fade", 1.0))
        # 太陽のにじみ（ep1 の板）をカメラに向ける。見下ろすと板の形が帯になって見えた（c02 で軸の方向へ回るとき）
        t = math.radians(s.get("tilt_deg", 0.0))
        halo = bpy.data.objects["Halo"]
        halo.rotation_euler = (math.radians(90) - t, 0, 0)
        halo.location = (0, 1.5 * sun_r * math.cos(t), -1.5 * sun_r * math.sin(t))
        draw.build_planet_dot(planet_z, px, s.get("planet_fade", 1.0))
        draw.build_probe_icon(probe_z, s["probe_height_px"], px)
        draw.build_alignment_line(planet_z, probe_z, px, s.get("line_alpha", 1.0), s.get("line_grow", 1.0))
        if s.get("cone"):
            ring_px = s["sun_radius_px"] * ep1.einstein_ring_ratio()
            draw.build_light_cone(planet_z, probe_z + s["probe_height_px"] * 0.5 * px, ring_px, px,
                                  grow=s.get("cone_grow", 1.0), alpha=s.get("cone_alpha", 1.0))
        if s.get("labels"):
            draw.build_labels([("系外惑星", 40, planet_z), ("太陽", s["sun_radius_px"] + 30, 0),
                               ("探査機", 90, probe_z)], px, s.get("label_alpha", 1.0))
        draw.build_side_camera(top_z - view_h / 2, view_h, VFOV_DEG, s.get("tilt_deg", 0.0))
        log = f"太陽の半径={s['sun_radius_px']}px 見下ろし={s.get('tilt_deg', 0)}°"
    sc.setup_render(scene, percentage)
    return log
