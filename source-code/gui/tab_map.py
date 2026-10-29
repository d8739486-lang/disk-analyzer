"""Map & Sector Verification Tab with Two Modes: Space Blocks Map (WinDirStat) & Surface Bad Sector Scanner (Victoria style)."""
import os
import subprocess
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from core.disk_info import get_block_devices, format_bytes
from core.scanner import DirectoryScanner
from core.surface_scanner import SurfaceScanner
from gui.treemap_widget import TreemapWidget
from gui.sector_grid_widget import SectorGridWidget
from gui.ui_utils import get_svg_image, get_svg_pixbuf


class MapTab(Gtk.Box):
    """Tab providing both interactive Space Treemap and Sector Grid verification."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(12)

        self.current_mode = "space"  # "space" or "sectors"
        self.is_scanning = False
        self.scanner_thread = None
        self.active_surface_scanner = None
        self.active_dir_scanner = None

        self._build_ui()
        self._load_mounts()

    def _build_ui(self):
        # Top Controls Bar
        ctrl_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Mode Switcher (Space Blocks Map vs Sector Surface Scan)
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        self.btn_mode_space = Gtk.Button()
        b_sp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        b_sp_box.pack_start(get_svg_image("grid", size=14, color="#ffffff"), False, False, 0)
        b_sp_box.pack_start(Gtk.Label(label="Карта занятого места"), False, False, 0)
        self.btn_mode_space.add(b_sp_box)
        self.btn_mode_space.get_style_context().add_class("primary-btn")
        self.btn_mode_space.connect("clicked", lambda b: self._switch_mode("space"))
        mode_box.pack_start(self.btn_mode_space, False, False, 0)

        self.btn_mode_sectors = Gtk.Button()
        b_sec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        b_sec_box.pack_start(get_svg_image("shield_check", size=14, color="#ffffff"), False, False, 0)
        b_sec_box.pack_start(Gtk.Label(label="Проверка секторов (Блоки)"), False, False, 0)
        self.btn_mode_sectors.add(b_sec_box)
        self.btn_mode_sectors.connect("clicked", lambda b: self._switch_mode("sectors"))
        mode_box.pack_start(self.btn_mode_sectors, False, False, 0)

        ctrl_bar.pack_start(mode_box, False, False, 0)

        lbl_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        ctrl_bar.pack_start(lbl_sep, False, False, 4)

        lbl_target = Gtk.Label(label="Раздел:")
        lbl_target.get_style_context().add_class("section-title")
        ctrl_bar.pack_start(lbl_target, False, False, 0)

        self.combo_target = Gtk.ComboBoxText()
        self.combo_target.set_size_request(260, -1)
        ctrl_bar.pack_start(self.combo_target, False, False, 0)

        # Single Action Button (Starts as "Запустить", transforms to "Остановить" in-place)
        self.btn_action = Gtk.Button()
        self.btn_action.get_style_context().add_class("primary-btn")
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_icon = get_svg_image("play", size=14, color="#ffffff")
        self.action_lbl = Gtk.Label(label="Сканировать")
        self.action_box.pack_start(self.action_icon, False, False, 0)
        self.action_box.pack_start(self.action_lbl, False, False, 0)
        self.btn_action.add(self.action_box)
        self.btn_action.connect("clicked", self._on_action_toggle)
        ctrl_bar.pack_start(self.btn_action, False, False, 0)

        self.pack_start(ctrl_bar, False, False, 0)

        # Single horizontal line separating top controls from visualization
        sep_top = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep_top, False, False, 2)

        # Main Visualization Stack (Treemap vs Sector Grid) - Instant snap switch (NO animation)
        self.stage_stack = Gtk.Stack()
        self.stage_stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.stage_stack.set_transition_duration(0)

        # 1. Mode Space View: Treemap
        space_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.treemap = TreemapWidget()
        self.treemap.on_item_hover = self._on_treemap_hover
        self.treemap.on_item_context_menu = self._on_treemap_context_menu
        space_container.pack_start(self.treemap, True, True, 0)
        self.stage_stack.add_named(space_container, "view_space")

        # 2. Mode Sectors View: Victoria / HD Tune Grid + Legend Sidebar
        sectors_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        # Grid Canvas
        self.sector_grid = SectorGridWidget(total_blocks=1200)
        self.sector_grid.on_block_hover = self._on_sector_block_hover
        sectors_container.pack_start(self.sector_grid, True, True, 0)

        # Sidebar with Live Statistics and Block Legend
        legend_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        legend_box.set_size_request(220, -1)
        
        lbl_legend_title = Gtk.Label(label="Статус блоков", xalign=0)
        lbl_legend_title.get_style_context().add_class("section-title")
        legend_box.pack_start(lbl_legend_title, False, False, 0)

        self.lbl_stat_fast = self._create_legend_row(legend_box, "#34d399", "< 5 мс (Отлично):", "0")
        self.lbl_stat_normal = self._create_legend_row(legend_box, "#38bdf8", "< 25 мс (Нормально):", "0")
        self.lbl_stat_slow = self._create_legend_row(legend_box, "#facc15", "< 100 мс (Внимание):", "0")
        self.lbl_stat_vslow = self._create_legend_row(legend_box, "#fb923c", "< 500 мс (Медленно):", "0")
        self.lbl_stat_bad = self._create_legend_row(legend_box, "#ef4444", "Ошибки / Бэды:", "0")

        lbl_sep_leg = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        legend_box.pack_start(lbl_sep_leg, False, False, 4)

        self.lbl_sector_progress = Gtk.Label(label="Проверено: 0 / 1200", xalign=0)
        self.lbl_sector_progress.get_style_context().add_class("metric-title")
        legend_box.pack_start(self.lbl_sector_progress, False, False, 0)

        sectors_container.pack_start(legend_box, False, False, 0)
        self.stage_stack.add_named(sectors_container, "view_sectors")

        self.pack_start(self.stage_stack, True, True, 0)

        # Single horizontal line separating visualization from bottom status
        sep_bot = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep_bot, False, False, 2)

        # Bottom Status Bar & Info
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.spinner = Gtk.Spinner()
        status_box.pack_start(self.spinner, False, False, 0)

        self.lbl_status = Gtk.Label(
            label="Выберите режим и нажмите кнопку для запуска сканирования.",
            xalign=0
        )
        self.lbl_status.get_style_context().add_class("metric-title")
        status_box.pack_start(self.lbl_status, True, True, 0)

        self.pack_start(status_box, False, False, 0)

    def _create_legend_row(self, container: Gtk.Box, color_hex: str, title: str, init_val: str) -> Gtk.Label:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Color indicator square
        color_box = Gtk.Box()
        color_box.set_size_request(12, 12)
        # Apply style directly
        css_data = f"* {{ background-color: {color_hex}; border-radius: 2px; }}"
        prov = Gtk.CssProvider()
        prov.load_from_data(css_data.encode())
        color_box.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        row.pack_start(color_box, False, False, 0)

        lbl = Gtk.Label(label=title, xalign=0)
        lbl.get_style_context().add_class("metric-title")
        row.pack_start(lbl, True, True, 0)

        val_lbl = Gtk.Label(label=init_val, xalign=1)
        val_lbl.get_style_context().add_class("metric-value")
        row.pack_start(val_lbl, False, False, 0)

        container.pack_start(row, False, False, 0)
        return val_lbl

    def _load_mounts(self):
        devices = get_block_devices()
        seen = set()

        # Always offer user home
        home = os.path.expanduser("~")
        self.combo_target.append(home, f"Домашняя папка ({home})")
        seen.add(home)

        for dev in devices:
            for part in dev.get("partitions", []):
                mp = part.get("mountpoint")
                if mp and mp not in seen and os.path.exists(mp):
                    seen.add(mp)
                    label = part.get("label") or mp
                    self.combo_target.append(mp, f"{label} ({mp})")

        self.combo_target.set_active(0)

    def _switch_mode(self, mode: str):
        if self.is_scanning:
            self._stop_current_scan()

        self.current_mode = mode
        if mode == "space":
            self.btn_mode_space.get_style_context().add_class("primary-btn")
            self.btn_mode_sectors.get_style_context().remove_class("primary-btn")
            self.stage_stack.set_visible_child_name("view_space")
            self.action_lbl.set_text("Сканировать карту места")
            self.lbl_status.set_text("Режим карты: пропорциональные блоки файлов и папок.")
        else:
            self.btn_mode_sectors.get_style_context().add_class("primary-btn")
            self.btn_mode_space.get_style_context().remove_class("primary-btn")
            self.stage_stack.set_visible_child_name("view_sectors")
            self.action_lbl.set_text("Проверить секторы")
            self.lbl_status.set_text("Режим сканирования секторов: сетка блоков со скоростью отклика.")

    def _on_action_toggle(self, btn):
        if self.is_scanning:
            self._stop_current_scan()
        else:
            self._start_current_scan()

    def _start_current_scan(self):
        target = self.combo_target.get_active_id() or os.path.expanduser("~")
        if not os.path.exists(target):
            self.lbl_status.set_text("Ошибка: раздел недоступен.")
            return

        self.is_scanning = True
        self.btn_action.get_style_context().remove_class("primary-btn")
        self.btn_action.get_style_context().add_class("danger-btn")
        self.action_lbl.set_text("Остановить")
        self.action_icon.set_from_pixbuf(get_svg_pixbuf("stop", size=14, color="#ffffff"))
        self.spinner.start()

        if self.current_mode == "space":
            self.treemap.clear()
            self.lbl_status.set_text(f"Анализ структуры каталогов: {target} ...")
            self.active_dir_scanner = DirectoryScanner(
                target,
                on_progress=lambda cnt, cur: GLib.idle_add(self._on_dir_progress, cnt, cur)
            )
            threading.Thread(target=self._run_treemap_scan, daemon=True).start()
        else:
            self.sector_grid.reset()
            self.lbl_stat_fast.set_text("0")
            self.lbl_stat_normal.set_text("0")
            self.lbl_stat_slow.set_text("0")
            self.lbl_stat_vslow.set_text("0")
            self.lbl_stat_bad.set_text("0")
            self.lbl_sector_progress.set_text("Проверено: 0 / 1200")
            self.lbl_status.set_text(f"Сканирование секторов на разделе {target} ...")

            self.active_surface_scanner = SurfaceScanner(
                target,
                total_grid_blocks=1200,
                on_block_done=lambda idx, tot, sec_tot, ms, st, lba: GLib.idle_add(self._on_sector_block, idx, tot, sec_tot, ms, st, lba),
                on_complete=lambda stats: GLib.idle_add(self._on_surface_complete, stats)
            )
            threading.Thread(target=self.active_surface_scanner.run, daemon=True).start()

    def _stop_current_scan(self):
        if self.active_dir_scanner:
            self.active_dir_scanner.cancel()
        if self.active_surface_scanner:
            self.active_surface_scanner.cancel()
        self._reset_action_ui("Операция остановлена пользователем.")

    def _reset_action_ui(self, msg: str):
        self.is_scanning = False
        self.spinner.stop()
        self.btn_action.get_style_context().remove_class("danger-btn")
        self.btn_action.get_style_context().add_class("primary-btn")
        default_label = "Сканировать карту места" if self.current_mode == "space" else "Проверить секторы"
        self.action_lbl.set_text(default_label)
        self.action_icon.set_from_pixbuf(get_svg_pixbuf("play", size=14, color="#ffffff"))
        self.lbl_status.set_text(msg)

    def _run_treemap_scan(self):
        root = self.active_dir_scanner.scan()
        GLib.idle_add(self._on_treemap_complete, root)

    def _on_dir_progress(self, count: int, cur_path: str):
        if not self.is_scanning:
            return False
        short = (cur_path[:65] + "...") if len(cur_path) > 65 else cur_path
        self.lbl_status.set_text(f"Индексация блоков: {count} файлов | {short}")
        return False

    def _on_treemap_complete(self, root_node):
        if not self.is_scanning:
            return False
        self.treemap.set_tree_data(root_node)
        total = root_node.get("size", 0)
        self._reset_action_ui(f"Карта построена. Проанализировано {format_bytes(total)}.")
        return False

    def _on_sector_block(self, idx: int, total: int, sec_tot: int, ms: float, status: str, lba: str):
        if not self.is_scanning:
            return False
        self.sector_grid.update_block(idx, status, latency=ms)
        self.lbl_sector_progress.set_text(f"Блоков: {idx + 1} / {total}\nСекторов LBA: ~{sec_tot:,}")
        self.lbl_status.set_text(f"Проверка: Блок {idx + 1}/{total} | {lba} | Отклик: {ms:.1f} мс [{status}]")

        # Update counter
        if self.active_surface_scanner:
            stats = self.active_surface_scanner.stats
            self.lbl_stat_fast.set_text(str(stats["fast"]))
            self.lbl_stat_normal.set_text(str(stats["normal"]))
            self.lbl_stat_slow.set_text(str(stats["slow"]))
            self.lbl_stat_vslow.set_text(str(stats["very_slow"]))
            self.lbl_stat_bad.set_text(str(stats["bad"]))
        return False

    def _on_sector_block_hover(self, idx: int, status: str, latency: float):
        if idx < 0:
            if not self.is_scanning:
                self.lbl_status.set_text("Наведите курсор на блок для просмотра подробностей отклика LBA.")
            return

        if self.active_surface_scanner:
            spb = self.active_surface_scanner.sectors_per_block
            lba_start = idx * spb
            lba_end = (idx + 1) * spb - 1
            lba_str = f"LBA: {lba_start:,} — {lba_end:,}"
        else:
            lba_str = f"Блок #{idx + 1}"

        lat_str = f"{latency:.1f} мс" if latency > 0 else "Не проверен"
        self.lbl_status.set_text(f"Инспекция: {lba_str} | Статус: {status.upper()} | Задержка отклика: {lat_str}")

    def _on_surface_complete(self, stats: dict):
        if not self.is_scanning:
            return False
        bad_count = stats.get("bad", 0)
        if bad_count > 0:
            msg = f"Проверка завершена. Обнаружено поврежденных блоков: {bad_count}!"
        else:
            msg = "Проверка секторов успешно завершена. Поврежденных блоков не обнаружено."
        self._reset_action_ui(msg)
        return False

    def _on_treemap_hover(self, name: str, path: str, size: int, is_dir: bool):
        if not name:
            if not self.is_scanning:
                self.lbl_status.set_text("Наведите курсор на блок или нажмите ПКМ для действий.")
            return
        t = "Папка" if is_dir else "Файл"
        self.lbl_status.set_text(f"{t}: {name} ({format_bytes(size)}) | Путь: {path}")

    def _on_treemap_context_menu(self, rect_item: dict, event):
        path = rect_item.get("path", "")
        if not path or not os.path.exists(path):
            return

        menu = Gtk.Menu()

        # Item 1: Open with default app
        item_open = Gtk.MenuItem(label="Открыть файл / запустить")
        item_open.connect("activate", lambda m: subprocess.Popen(["xdg-open", path]))
        menu.append(item_open)

        # Item 2: Open containing folder in Thunar
        item_thunar = Gtk.MenuItem(label="Показать в диспетчере файлов (Thunar)")
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        item_thunar.connect("activate", lambda m: subprocess.Popen(["thunar", folder]))
        menu.append(item_thunar)

        # Item 3: Open in terminal
        item_term = Gtk.MenuItem(label="Открыть терминал здесь (xfce4-terminal)")
        item_term.connect("activate", lambda m: subprocess.Popen(["xfce4-terminal", f"--working-directory={folder}"]))
        menu.append(item_term)

        menu.append(Gtk.SeparatorMenuItem())

        # Item 4: Properties / Details dialog
        item_props = Gtk.MenuItem(label="Свойства и подробности")
        item_props.connect("activate", lambda m: self._show_item_properties(rect_item))
        menu.append(item_props)

        # Item 5: Copy Path
        item_copy = Gtk.MenuItem(label="Скопировать путь")
        def _copy_path(m):
            clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clip.set_text(path, -1)
        item_copy.connect("activate", _copy_path)
        menu.append(item_copy)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

    def _show_item_properties(self, item: dict):
        dialog = Gtk.Dialog(
            title=f"Свойства: {item.get('name')}",
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.set_default_size(440, 260)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(14)
        box.set_margin_bottom(14)
        box.set_margin_start(16)
        box.set_margin_end(16)

        grid = Gtk.Grid()
        grid.set_column_spacing(14)
        grid.set_row_spacing(8)

        props = [
            ("Имя:", item.get("name", "")),
            ("Тип:", "Папка / Каталог" if item.get("is_dir") else "Файл данных"),
            ("Размер:", format_bytes(item.get("size", 0))),
            ("Точный размер:", f"{item.get('size', 0):,} байт"),
            ("Полный путь:", item.get("path", "")),
        ]

        for i, (k, v) in enumerate(props):
            lbl_k = Gtk.Label(label=k, xalign=0)
            lbl_k.get_style_context().add_class("section-title")
            grid.attach(lbl_k, 0, i, 1, 1)

            lbl_v = Gtk.Label(label=str(v), xalign=0)
            lbl_v.set_selectable(True)
            lbl_v.set_line_wrap(True)
            grid.attach(lbl_v, 1, i, 1, 1)

        box.pack_start(grid, True, True, 0)
        dialog.add_button("Закрыть", Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show_all()

