"""Sector Surface Grid Widget: Renders Victoria / HD Tune style block map with hover inspect."""
import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from typing import List, Optional, Callable


class SectorGridWidget(Gtk.DrawingArea):
    """Draws a responsive grid of cubes representing disk sectors with live latency and hover details."""

    COLOR_MAP = {
        "empty": (0.13, 0.16, 0.22),       # Unscanned / pending
        "fast": (0.20, 0.75, 0.35),        # < 5ms: Solid Vibrant Green
        "normal": (0.25, 0.65, 0.85),      # < 25ms: Sky Blue
        "slow": (0.85, 0.70, 0.15),        # < 100ms: Amber / Yellow
        "very_slow": (0.95, 0.45, 0.15),   # < 500ms: Orange
        "bad": (0.95, 0.15, 0.20),         # > 500ms / Error: Pure Red Bad block
    }

    def __init__(self, total_blocks: int = 1200):
        super().__init__()
        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )

        self.total_blocks = total_blocks
        self.block_status: List[str] = ["empty"] * total_blocks
        self.block_latencies: List[float] = [0.0] * total_blocks
        self.current_index: int = -1
        self.hovered_index: int = -1
        self.on_block_hover: Optional[Callable[[int, str, float], None]] = None

        self._cols = 40
        self._block_size = 12
        self._gap = 2
        self._offset_x = 4
        self._offset_y = 4

        self.connect("draw", self._on_draw)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("leave-notify-event", self._on_leave)

    def set_total_blocks(self, count: int):
        self.total_blocks = count
        self.block_status = ["empty"] * count
        self.block_latencies = [0.0] * count
        self.current_index = -1
        self.hovered_index = -1
        self.queue_draw()

    def update_block(self, idx: int, status: str, latency: float = 0.0):
        if 0 <= idx < len(self.block_status):
            self.block_status[idx] = status
            self.block_latencies[idx] = latency
            self.current_index = idx
            self.queue_draw()

    def reset(self):
        self.block_status = ["empty"] * self.total_blocks
        self.block_latencies = [0.0] * self.total_blocks
        self.current_index = -1
        self.hovered_index = -1
        self.queue_draw()

    def _on_draw(self, widget, cr: cairo.Context):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height

        # Fill background
        cr.set_source_rgb(0.09, 0.11, 0.15)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        if self.total_blocks <= 0:
            return False

        gap = 2
        block_size = 13

        cols = max(1, int((w - gap) / (block_size + gap)))
        rows = max(1, int((h - gap) / (block_size + gap)))
        max_drawable = min(self.total_blocks, cols * rows)

        self._cols = cols
        self._block_size = block_size
        self._gap = gap

        grid_w = cols * (block_size + gap) - gap
        grid_h = rows * (block_size + gap) - gap
        self._offset_x = max(6, int((w - grid_w) / 2))
        self._offset_y = max(6, int((h - grid_h) / 2))

        for i in range(max_drawable):
            r = i // cols
            c = i % cols
            bx = self._offset_x + c * (block_size + gap)
            by = self._offset_y + r * (block_size + gap)

            status = self.block_status[i]
            col = self.COLOR_MAP.get(status, self.COLOR_MAP["empty"])

            if i == self.hovered_index:
                # Hover highlight
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.rectangle(bx - 1, by - 1, block_size + 2, block_size + 2)
                cr.fill()
                cr.set_source_rgb(col[0], col[1], col[2])
                cr.rectangle(bx, by, block_size, block_size)
                cr.fill()
            elif i == self.current_index:
                cr.set_source_rgb(0.9, 0.95, 1.0)
                cr.rectangle(bx, by, block_size, block_size)
                cr.fill()
            else:
                cr.set_source_rgb(col[0], col[1], col[2])
                cr.rectangle(bx, by, block_size, block_size)
                cr.fill()

        return False

    def _on_motion(self, widget, event):
        x, y = event.x, event.y
        rel_x = x - self._offset_x
        rel_y = y - self._offset_y
        step = self._block_size + self._gap

        hit_idx = -1
        if rel_x >= 0 and rel_y >= 0:
            c = int(rel_x // step)
            r = int(rel_y // step)
            if 0 <= c < self._cols:
                idx = r * self._cols + c
                if 0 <= idx < self.total_blocks:
                    hit_idx = idx

        if hit_idx != self.hovered_index:
            self.hovered_index = hit_idx
            self.queue_draw()
            if self.on_block_hover:
                if hit_idx >= 0:
                    st = self.block_status[hit_idx]
                    lat = self.block_latencies[hit_idx]
                    self.on_block_hover(hit_idx, st, lat)
                else:
                    self.on_block_hover(-1, "", 0.0)

    def _on_leave(self, widget, event):
        if self.hovered_index != -1:
            self.hovered_index = -1
            self.queue_draw()
            if self.on_block_hover:
                self.on_block_hover(-1, "", 0.0)
