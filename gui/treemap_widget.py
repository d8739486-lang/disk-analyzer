"""Treemap Space Visualizer Widget: Renders interactive WinDirStat / TreeSize block map."""
import cairo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from typing import List, Dict, Any, Optional

from core.disk_info import format_bytes


class TreemapWidget(Gtk.DrawingArea):
    """Draws nested colored blocks representing directories and files proportionally."""

    COLOR_PALETTE = [
        (0.14, 0.54, 0.85),  # Blue
        (0.10, 0.70, 0.45),  # Green
        (0.92, 0.45, 0.18),  # Orange
        (0.65, 0.35, 0.82),  # Purple
        (0.85, 0.20, 0.35),  # Crimson
        (0.20, 0.75, 0.75),  # Teal
        (0.85, 0.70, 0.15),  # Gold
        (0.40, 0.50, 0.65),  # Slate
    ]

    def __init__(self):
        super().__init__()
        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
        )
        self.connect("draw", self._on_draw)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("leave-notify-event", self._on_leave)
        self.connect("button-press-event", self._on_button_press)

        self.root_node: Optional[Dict[str, Any]] = None
        self.rects: List[Dict[str, Any]] = []
        self.hovered_rect: Optional[Dict[str, Any]] = None
        self.on_item_hover: Optional[callable] = None
        self.on_item_context_menu: Optional[callable] = None

    def set_tree_data(self, root_node: Dict[str, Any]):
        self.root_node = root_node
        self.rects.clear()
        self.hovered_rect = None
        self.queue_draw()

    def clear(self):
        self.root_node = None
        self.rects.clear()
        self.hovered_rect = None
        self.queue_draw()

    def _compute_layout(self, width: int, height: int):
        self.rects.clear()
        if not self.root_node or not self.root_node.get("children"):
            return

        total_size = sum(c.get("size", 0) for c in self.root_node["children"])
        if total_size <= 0:
            return

        # Squarified slice-and-dice layout
        children = sorted(self.root_node["children"], key=lambda x: x.get("size", 0), reverse=True)
        # Display top 60 significant blocks
        top_children = children[:60]
        sum_top = sum(c.get("size", 0) for c in top_children)
        if sum_top <= 0:
            return

        self._layout_slice(top_children, 0, 0, width, height, sum_top, 0)

    def _layout_slice(self, items: List[Dict[str, Any]], x: float, y: float, w: float, h: float, total_val: int, depth: int):
        if not items or w < 2 or h < 2:
            return

        if len(items) == 1:
            item = items[0]
            color = self.COLOR_PALETTE[depth % len(self.COLOR_PALETTE)]
            self.rects.append({
                "x": x + 1,
                "y": y + 1,
                "w": max(2, w - 2),
                "h": max(2, h - 2),
                "name": item.get("name", ""),
                "path": item.get("path", ""),
                "size": item.get("size", 0),
                "is_dir": item.get("is_dir", False),
                "color": color,
            })
            return

        # Split items into two groups approximating equal weight
        half = total_val / 2.0
        acc = 0
        split_idx = 1
        for i, itm in enumerate(items):
            acc += itm.get("size", 0)
            if acc >= half or i == len(items) - 1:
                split_idx = max(1, i)
                break

        group1 = items[:split_idx]
        group2 = items[split_idx:]
        val1 = sum(it.get("size", 0) for it in group1)
        val2 = sum(it.get("size", 0) for it in group2)

        ratio1 = val1 / total_val if total_val > 0 else 0.5

        if w >= h:
            w1 = w * ratio1
            w2 = w - w1
            self._layout_slice(group1, x, y, w1, h, val1, depth)
            self._layout_slice(group2, x + w1, y, w2, h, val2, depth + 1)
        else:
            h1 = h * ratio1
            h2 = h - h1
            self._layout_slice(group1, x, y, w, h1, val1, depth)
            self._layout_slice(group2, x, y + h1, w, h2, val2, depth + 1)

    def _on_draw(self, widget, cr: cairo.Context):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height

        # Dark sleek background
        cr.set_source_rgb(0.08, 0.10, 0.13)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        if not self.root_node or not self.root_node.get("children"):
            cr.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14.5)
            cr.set_source_rgb(0.70, 0.75, 0.82)
            text1 = "Нажмите «Карта занятого места» или «Сканировать» для анализа диска"
            ext1 = cr.text_extents(text1)
            cr.move_to((w - ext1.width) / 2, (h / 2) - 12)
            cr.show_text(text1)

            cr.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(12.5)
            cr.set_source_rgb(0.45, 0.52, 0.62)
            text2 = "Информация о загрузке, чтении секторов и операциях находится снизу в левом углу"
            ext2 = cr.text_extents(text2)
            cr.move_to((w - ext2.width) / 2, (h / 2) + 16)
            cr.show_text(text2)
            return False

        if not self.rects:
            self._compute_layout(w, h)

        for r in self.rects:
            rx, ry, rw, rh = r["x"], r["y"], r["w"], r["h"]
            col = r["color"]
            is_hover = (r is self.hovered_rect)

            if is_hover:
                # Highlight hovered block
                cr.set_source_rgb(min(1.0, col[0] + 0.25), min(1.0, col[1] + 0.25), min(1.0, col[2] + 0.25))
            else:
                cr.set_source_rgb(col[0], col[1], col[2])

            cr.rectangle(rx, ry, rw, rh)
            cr.fill()

            # Clean crisp border
            cr.set_source_rgb(0.08, 0.10, 0.13)
            cr.set_line_width(1.5)
            cr.rectangle(rx, ry, rw, rh)
            cr.stroke()

            # Label if rectangle is large enough
            if rw > 45 and rh > 24:
                cr.set_source_rgb(1.0, 1.0, 1.0)
                cr.set_font_size(11.5)
                name = r["name"]
                if len(name) > int(rw / 7):
                    name = name[:max(3, int(rw / 7) - 2)] + ".."
                cr.move_to(rx + 6, ry + 16)
                cr.show_text(name)

                if rh > 42 and rw > 60:
                    cr.set_source_rgb(0.85, 0.90, 0.95)
                    cr.set_font_size(10.0)
                    sz_str = format_bytes(r["size"])
                    cr.move_to(rx + 6, ry + 32)
                    cr.show_text(sz_str)

        return False

    def _on_motion(self, widget, event):
        x, y = event.x, event.y
        hit = None
        for r in self.rects:
            if r["x"] <= x <= r["x"] + r["w"] and r["y"] <= y <= r["y"] + r["h"]:
                hit = r
                break

        if hit != self.hovered_rect:
            self.hovered_rect = hit
            self.queue_draw()
            if self.on_item_hover and hit:
                self.on_item_hover(hit["name"], hit["path"], hit["size"], hit["is_dir"])
            elif self.on_item_hover and not hit:
                self.on_item_hover("", "", 0, False)

    def _on_button_press(self, widget, event):
        if event.button == 3:  # Right click
            if self.hovered_rect and self.on_item_context_menu:
                self.on_item_context_menu(self.hovered_rect, event)
                return True
        return False

    def _on_leave(self, widget, event):
        if self.hovered_rect:
            self.hovered_rect = None
            self.queue_draw()
            if self.on_item_hover:
                self.on_item_hover("", "", 0, False)

