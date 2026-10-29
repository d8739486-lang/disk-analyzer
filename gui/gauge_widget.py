"""Speed Gauge Widget (Speedtest.net style) rendered with Cairo."""
import math
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class SpeedGauge(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(260, 200)
        self.connect("draw", self._on_draw)

        self.current_speed = 0.0
        self.target_speed = 0.0
        self.max_scale_speed = 3500.0  # Default scale for fast NVMe/SSD
        self.stage_name = "ГОТОВ К ТЕСТУ"
        self.is_active = False

        self._anim_timer = None

    def set_speed(self, speed: float, stage: str = ""):
        self.target_speed = max(0.0, speed)
        if stage:
            self.stage_name = stage
        self.is_active = True

        # Dynamically scale max if speeds are higher
        if self.target_speed > self.max_scale_speed:
            self.max_scale_speed = math.ceil(self.target_speed / 1000.0) * 1000.0

        if not self._anim_timer:
            self._anim_timer = GLib.timeout_add(25, self._on_tick)

    def reset(self, stage: str = "ГОТОВ"):
        self.target_speed = 0.0
        self.stage_name = stage
        self.is_active = False
        self.queue_draw()

    def _on_tick(self):
        diff = self.target_speed - self.current_speed
        if abs(diff) < 0.2:
            self.current_speed = self.target_speed
            self.queue_draw()
            if not self.is_active and self.current_speed == 0:
                self._anim_timer = None
                return False
        else:
            # Smooth spring-like lerp
            self.current_speed += diff * 0.22
            self.queue_draw()
        return True

    def _on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        cx = width / 2.0
        cy = height * 0.78
        radius = min(width * 0.44, height * 0.68)

        start_angle = math.pi * 0.82
        end_angle = math.pi * 2.18
        total_angle = end_angle - start_angle

        # 1. Background Arc (Dark Track)
        cr.set_line_width(14)
        cr.set_line_cap(1)  # CAIRO_LINE_CAP_ROUND
        cr.set_source_rgba(0.14, 0.16, 0.21, 0.8)
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()

        # 2. Speed Progress Arc (Speedtest Cyan / Emerald Glow)
        fraction = min(1.0, max(0.0, self.current_speed / self.max_scale_speed))
        current_arc_angle = start_angle + (fraction * total_angle)

        if fraction > 0.005:
            # Active arc without any blur/glow
            cr.set_line_width(12)
            cr.set_source_rgba(0.22, 0.74, 0.97, 1.0)  # Pure solid sky-blue
            cr.arc(cx, cy, radius, start_angle, current_arc_angle)
            cr.stroke()

        # 3. Ticks along the arc
        tick_count = 10
        for i in range(tick_count + 1):
            ang = start_angle + (i / tick_count) * total_angle
            r_in = radius - 14
            r_out = radius - 8
            x1 = cx + r_in * math.cos(ang)
            y1 = cy + r_in * math.sin(ang)
            x2 = cx + r_out * math.cos(ang)
            y2 = cy + r_out * math.sin(ang)

            cr.set_line_width(2)
            if ang <= current_arc_angle and fraction > 0.005:
                cr.set_source_rgba(0.2, 0.9, 0.7, 0.9)
            else:
                cr.set_source_rgba(0.3, 0.35, 0.42, 0.5)
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()

        # 4. Needle
        needle_angle = current_arc_angle
        nx = cx + (radius - 22) * math.cos(needle_angle)
        ny = cy + (radius - 22) * math.sin(needle_angle)

        cr.set_line_width(3.5)
        cr.set_line_cap(1)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.95)
        cr.move_to(cx, cy)
        cr.line_to(nx, ny)
        cr.stroke()

        # Center Pivot Dot
        cr.set_source_rgba(0.08, 0.85, 0.62, 1.0)
        cr.arc(cx, cy, 7, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.arc(cx, cy, 3, 0, 2 * math.pi)
        cr.fill()

        # 5. Big Center Speed Digital Display
        cr.select_font_face("-apple-system, BlinkMacSystemFont, 'Segoe UI', Ubuntu, sans-serif", 0, 1)
        cr.set_font_size(28)
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)

        speed_str = f"{self.current_speed:.1f}"
        extents = cr.text_extents(speed_str)
        cr.move_to(cx - extents.width / 2.0, cy - 20)
        cr.show_text(speed_str)

        # "МБ/с" label
        cr.set_font_size(12)
        cr.set_source_rgba(0.55, 0.60, 0.70, 1.0)
        u_str = "МБ/с"
        uext = cr.text_extents(u_str)
        cr.move_to(cx - uext.width / 2.0, cy - 4)
        cr.show_text(u_str)

        # Stage sublabel (e.g. "ЧТЕНИЕ SEQ 1M")
        cr.set_font_size(11)
        if self.is_active:
            cr.set_source_rgba(0.2, 0.9, 0.68, 1.0)
        else:
            cr.set_source_rgba(0.45, 0.50, 0.58, 1.0)
        sext = cr.text_extents(self.stage_name)
        cr.move_to(cx - sext.width / 2.0, cy + 28)
        cr.show_text(self.stage_name)

        return False

