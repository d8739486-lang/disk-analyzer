"""Tab 2: Interactive Fast Disk Explorer with Expandable Tree Branches & Real File Icons."""
import os
import subprocess
import threading
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf, GLib
from core.disk_info import get_block_devices, format_bytes, get_mount_usage
from core.scanner import DirectoryScanner
from core.i18n import t, get_current_lang
from gui.ui_utils import get_svg_image, get_svg_pixbuf, get_file_system_icon


class UsageTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.set_margin_top(14)
        self.set_margin_bottom(14)
        self.set_margin_start(14)
        self.set_margin_end(14)

        self.current_path = os.path.expanduser("~")
        self.history_stack = []
        self.current_scanner = None
        self.is_scanning = False
        self._build_ui()
        self.load_partitions()
        self.browse_to(self.current_path, push_history=False)

    def _build_ui(self):
        # Top Control & Mount Selector
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Back Button (Navigate Back)
        self.btn_back = Gtk.Button()
        b_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        b_box.pack_start(get_svg_image("arrow_left", size=14, color="#ffffff"), False, False, 0)
        self.lbl_back = Gtk.Label(label=t("btn_back"))
        b_box.pack_start(self.lbl_back, False, False, 0)
        self.btn_back.add(b_box)
        self.btn_back.set_sensitive(False)
        self.btn_back.connect("clicked", self._on_back_clicked)
        top_box.pack_start(self.btn_back, False, False, 0)

        # Up Button (Parent directory)
        self.btn_up = Gtk.Button()
        u_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        u_box.pack_start(get_svg_image("arrow_up", size=14, color="#ffffff"), False, False, 0)
        self.lbl_up = Gtk.Label(label=t("btn_up"))
        u_box.pack_start(self.lbl_up, False, False, 0)
        self.btn_up.add(u_box)
        self.btn_up.connect("clicked", self._on_up_clicked)
        top_box.pack_start(self.btn_up, False, False, 0)

        self.lbl_part = Gtk.Label(label=t("partition"))
        self.lbl_part.get_style_context().add_class("section-title")
        top_box.pack_start(self.lbl_part, False, False, 0)

        self.combo_mounts = Gtk.ComboBoxText()
        self.combo_mounts.set_size_request(240, -1)
        self.combo_mounts.connect("changed", self._on_mount_changed)
        top_box.pack_start(self.combo_mounts, False, False, 0)

        self.lbl_loc = Gtk.Label(label=t("path"))
        self.lbl_loc.get_style_context().add_class("section-title")
        top_box.pack_start(self.lbl_loc, False, False, 0)

        self.entry_path = Gtk.Entry()
        self.entry_path.set_text(self.current_path)
        self.entry_path.connect("activate", self._on_path_entered)
        top_box.pack_start(self.entry_path, True, True, 0)

        # Action button
        self.btn_scan = Gtk.Button()
        self.btn_scan.get_style_context().add_class("primary-btn")
        self.scan_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.scan_icon = get_svg_image("pulse", size=14, color="#ffffff")
        self.scan_lbl = Gtk.Label(label=t("btn_scan"))
        self.scan_box.pack_start(self.scan_icon, False, False, 0)
        self.scan_box.pack_start(self.scan_lbl, False, False, 0)
        self.btn_scan.add(self.scan_box)
        self.btn_scan.connect("clicked", self._on_scan_toggle)
        top_box.pack_start(self.btn_scan, False, False, 0)

        self.pack_start(top_box, False, False, 0)

        # Capacity summary card
        self.summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        self.lbl_info_title = Gtk.Label(label=t("usage_title"), xalign=0)
        lbl_info_title.get_style_context().add_class("section-title")
        header_row.pack_start(lbl_info_title, False, False, 0)

        # Prominent metrics box
        metrics_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        
        self.lbl_used_box = Gtk.Label(label="Занято: 0 Б", xalign=0)
        self.lbl_used_box.get_style_context().add_class("usage-highlight-used")
        metrics_box.pack_start(self.lbl_used_box, False, False, 0)

        self.lbl_free_box = Gtk.Label(label="Свободно: 0 Б", xalign=0)
        self.lbl_free_box.get_style_context().add_class("usage-highlight-free")
        metrics_box.pack_start(self.lbl_free_box, False, False, 0)

        self.lbl_total_box = Gtk.Label(label="Всего: 0 Б", xalign=0)
        self.lbl_total_box.get_style_context().add_class("usage-highlight-total")
        metrics_box.pack_start(self.lbl_total_box, False, False, 0)

        header_row.pack_end(metrics_box, False, False, 0)
        self.summary_box.pack_start(header_row, False, False, 0)

        # High-visibility Progress Bar
        self.progress_usage = Gtk.ProgressBar()
        self.progress_usage.set_fraction(0.0)
        self.progress_usage.set_show_text(True)
        self.summary_box.pack_start(self.progress_usage, False, False, 0)

        status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.spinner = Gtk.Spinner()
        status_row.pack_start(self.spinner, False, False, 0)
        self.lbl_status = Gtk.Label(
            label="Используйте стрелочки ▶ для раскрытия папок на месте или дважды кликните по папке.",
            xalign=0
        )
        self.lbl_status.get_style_context().add_class("metric-title")
        status_row.pack_start(self.lbl_status, True, True, 0)
        self.summary_box.pack_start(status_row, False, False, 0)

        self.pack_start(self.summary_box, False, False, 0)

        # Single horizontal separator line between summary and treeview table
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep, False, False, 2)

        # Results Tree Table (Explorer with Expandable Branches)
        table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        head_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.lbl_tree_head = Gtk.Label(label=t("tree_title"), xalign=0)
        self.lbl_tree_head.get_style_context().add_class("section-title")
        head_row.pack_start(self.lbl_tree_head, True, True, 0)

        btn_open_ext = Gtk.Button()
        o_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        o_box.pack_start(get_svg_image("disk", size=14, color="#cbd5e1"), False, False, 0)
        self.lbl_open_ext = Gtk.Label(label=t("btn_open_folder"))
        o_box.pack_start(self.lbl_open_ext, False, False, 0)
        btn_open_ext.add(o_box)
        btn_open_ext.connect("clicked", self._on_open_in_file_manager)
        head_row.pack_start(btn_open_ext, False, False, 0)

        table_box.pack_start(head_row, False, False, 0)

        # Tree Store: Icon (Pixbuf), Name, Size, Percent/Type, Items, Path, IsDir, IsLoaded
        self.tree_store = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str, str, str, str, bool, bool)
        self.tree_view = Gtk.TreeView(model=self.tree_store)
        self.tree_view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.tree_view.set_show_expanders(True)
        self.tree_view.connect("row-activated", self._on_row_activated)
        self.tree_view.connect("test-expand-row", self._on_test_expand_row)
        self.tree_view.connect("button-press-event", self._on_tree_button_press)

        # Column 1: Expandable Name + Real System Icon
        self.col_name = Gtk.TreeViewColumn(t("col_name"))
        self.col_name.set_expand(True)
        self.col_name.set_min_width(320)

        cell_icon = Gtk.CellRendererPixbuf()
        cell_icon.set_padding(4, 4)
        self.col_name.pack_start(cell_icon, False)
        self.col_name.add_attribute(cell_icon, "pixbuf", 0)

        cell_name = Gtk.CellRendererText()
        cell_name.set_padding(4, 6)
        self.col_name.pack_start(cell_name, True)
        self.col_name.add_attribute(cell_name, "text", 1)
        self.tree_view.append_column(self.col_name)

        # Other Columns
        cols = [
            (t("col_size"), 2, 110, False, 1.0),
            (t("col_type"), 3, 110, False, 0.0),
            (t("col_items"), 4, 95, False, 1.0),
            (t("col_path"), 5, 280, True, 0.0),
        ]
        for title, idx, width, expand, xalign in cols:
            renderer = Gtk.CellRendererText()
            renderer.set_padding(6, 6)
            renderer.set_property("xalign", xalign)
            column = Gtk.TreeViewColumn(title, renderer, text=idx)
            column.set_min_width(width)
            column.set_resizable(True)
            if expand:
                column.set_expand(True)
            self.tree_view.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.tree_view)
        table_box.pack_start(scroll, True, True, 0)

        self.pack_start(table_box, True, True, 0)

    def load_partitions(self):
        self.combo_mounts.remove_all()
        devices = get_block_devices()

        items_list = []
        for dev in devices:
            for part in dev.get("partitions", []):
                mp = part.get("mountpoint")
                if mp:
                    desc = f"{part.get('friendly_desc')} — {part['size_str']}"
                    items_list.append((mp, desc))

        home = os.path.expanduser("~")
        items_list.append((home, f"Домашняя папка пользователя ({home})"))
        items_list.sort(key=lambda x: 0 if x[0] == home else (1 if x[0] == "/" else 2))

        for path, desc in items_list:
            self.combo_mounts.append(path, desc)

        if len(items_list) > 0:
            self.combo_mounts.set_active(0)

    def browse_to(self, path: str, push_history: bool = True):
        path = os.path.realpath(path)
        if not os.path.exists(path) or not os.path.isdir(path):
            return

        if push_history and self.current_path != path:
            self.history_stack.append(self.current_path)
            self.btn_back.set_sensitive(True)

        self.current_path = path
        self.entry_path.set_text(path)
        self._update_disk_usage_for_path(path)

        self.tree_store.clear()
        self._populate_folder(path, parent_iter=None)
        self.lbl_status.set_text(f"Текущая папка: {path} | Раскрывайте ветки стрелочками ▶")

    def _populate_folder(self, folder_path: str, parent_iter=None):
        entries = []
        try:
            with os.scandir(folder_path) as it:
                for entry in it:
                    try:
                        is_d = entry.is_dir(follow_symlinks=False)
                        st = entry.stat(follow_symlinks=False)
                        size = st.st_size if not is_d else 0
                        entries.append({
                            "name": entry.name,
                            "path": entry.path,
                            "is_dir": is_d,
                            "size": size,
                        })
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError) as e:
            self.lbl_status.set_text(f"Доступ ограничен: {e}")
            return

        entries.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        for e in entries:
            # Query Linux native system mime icon
            icon_pix = get_file_system_icon(e["path"], is_dir=e["is_dir"], size=16)
            size_str = "Папка" if e["is_dir"] else format_bytes(e["size"])
            type_str = "Каталог" if e["is_dir"] else (e["path"].rsplit('.', 1)[-1].upper() + " файл" if '.' in e["name"] else "Файл")

            row_iter = self.tree_store.append(parent_iter, [
                icon_pix,
                e["name"],
                size_str,
                type_str,
                "—",
                e["path"],
                e["is_dir"],
                False  # Not loaded yet
            ])

            # For directories, add a dummy child so that the expander arrow ▶ appears!
            if e["is_dir"]:
                self.tree_store.append(row_iter, [
                    None,
                    "Загрузка...",
                    "",
                    "",
                    "",
                    "",
                    False,
                    True
                ])

    def _on_test_expand_row(self, tree, tree_iter, tree_path):
        """Lazy load child branch contents when clicking expander arrow ▶."""
        model = self.tree_store
        is_loaded = model.get_value(tree_iter, 7)
        if not is_loaded:
            folder_path = model.get_value(tree_iter, 5)
            # Remove dummy child
            first_child = model.iter_children(tree_iter)
            if first_child:
                model.remove(first_child)

            # Populate real children
            self._populate_folder(folder_path, parent_iter=tree_iter)
            model.set_value(tree_iter, 7, True)
        return False  # Allow row expansion

    def _update_disk_usage_for_path(self, path: str):
        usage = get_mount_usage(path)
        pct = usage["percent"]
        self.progress_usage.set_fraction(pct / 100.0)
        self.progress_usage.set_text(f"{pct:.1f}%")
        self.lbl_used_box.set_text(f"Занято: {usage['used_str']}")
        self.lbl_free_box.set_text(f"Свободно: {usage['free_str']}")
        self.lbl_total_box.set_text(f"Всего: {usage['total_str']}")

    def _on_mount_changed(self, combo):
        path = combo.get_active_id()
        if path and os.path.exists(path):
            self.browse_to(path)

    def _on_path_entered(self, entry):
        path = entry.get_text().strip()
        if os.path.exists(path):
            self.browse_to(path)

    def _on_back_clicked(self, btn):
        if self.history_stack:
            prev_path = self.history_stack.pop()
            if not self.history_stack:
                self.btn_back.set_sensitive(False)
            self.browse_to(prev_path, push_history=False)

    def _on_up_clicked(self, btn):
        parent = os.path.dirname(self.current_path)
        if os.path.exists(parent) and parent != self.current_path:
            self.browse_to(parent)

    def _on_row_activated(self, tree, path, column):
        model = tree.get_model()
        tree_iter = model.get_iter(path)
        if not tree_iter:
            return
        is_dir = model.get_value(tree_iter, 6)
        full_path = model.get_value(tree_iter, 5)

        if is_dir:
            # Toggle expand / collapse on double click (standard tree view behavior)
            if tree.row_expanded(path):
                tree.collapse_row(path)
            else:
                tree.expand_row(path, False)
        elif not is_dir and full_path and os.path.exists(full_path):
            # Open file in default system viewer
            try:
                subprocess.Popen(["xdg-open", full_path])
            except Exception:
                pass

    def _on_tree_button_press(self, tree, event):
        # Right-click context menu (Button 3)
        if event.button == 3:
            path_info = tree.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path, col, _, _ = path_info
                tree.get_selection().select_path(path)
                model = tree.get_model()
                tree_iter = model.get_iter(path)
                full_path = model.get_value(tree_iter, 5)
                is_dir = model.get_value(tree_iter, 6)
                self._show_context_menu(event, full_path, is_dir)
                return True
        return False

    def _show_context_menu(self, event, full_path: str, is_dir: bool):
        menu = Gtk.Menu()

        item_open = Gtk.MenuItem(label="Открыть в системе")
        item_open.connect("activate", lambda m: subprocess.Popen(["xdg-open", full_path]))
        menu.append(item_open)

        item_loc = Gtk.MenuItem(label="Показать в Thunar / диспетчере файлов")
        folder = full_path if is_dir else os.path.dirname(full_path)
        item_loc.connect("activate", lambda m: subprocess.Popen(["thunar", folder]))
        menu.append(item_loc)

        item_term = Gtk.MenuItem(label="Открыть терминал здесь (XFCE)")
        item_term.connect("activate", lambda m: subprocess.Popen(["xfce4-terminal", f"--working-directory={folder}"]))
        menu.append(item_term)

        menu.append(Gtk.SeparatorMenuItem())

        item_copy_path = Gtk.MenuItem(label="Скопировать путь")
        def _copy_path(m):
            clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clip.set_text(full_path, -1)
        item_copy_path.connect("activate", _copy_path)
        menu.append(item_copy_path)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

    def _on_open_in_file_manager(self, btn):
        target = self.current_path if os.path.exists(self.current_path) else os.path.expanduser("~")
        try:
            subprocess.Popen(["xdg-open", target])
        except Exception:
            pass

    def _on_scan_toggle(self, btn):
        if self.is_scanning:
            self._stop_scan()
        else:
            self._start_scan()

    def _start_scan(self):
        target_path = self.current_path
        if not os.path.exists(target_path):
            self.lbl_status.set_text("Ошибка: путь не существует")
            return

        self.is_scanning = True
        self.btn_scan.get_style_context().remove_class("primary-btn")
        self.btn_scan.get_style_context().add_class("danger-btn")
        self.scan_lbl.set_text("Остановить")
        self.scan_icon.set_from_pixbuf(get_svg_pixbuf("stop", size=14, color="#ffffff"))

        self.spinner.start()
        self.tree_store.clear()
        self.lbl_status.set_text(f"Глубокое сканирование дерева файлов: {target_path} ...")

        self.current_scanner = DirectoryScanner(
            target_path,
            on_progress=lambda cnt, cur: GLib.idle_add(self._on_scan_progress, cnt, cur)
        )

        threading.Thread(target=self._scan_thread_worker, daemon=True).start()

    def _stop_scan(self):
        if self.current_scanner:
            self.current_scanner.cancel()
        self._reset_scan_ui("Сканирование остановлено пользователем.")

    def _reset_scan_ui(self, status_msg: str):
        self.is_scanning = False
        self.spinner.stop()
        self.btn_scan.get_style_context().remove_class("danger-btn")
        self.btn_scan.get_style_context().add_class("primary-btn")
        self.scan_lbl.set_text("Глубокий анализ")
        self.scan_icon.set_from_pixbuf(get_svg_pixbuf("pulse", size=14, color="#ffffff"))
        self.lbl_status.set_text(status_msg)

    def _scan_thread_worker(self):
        tree_data = self.current_scanner.scan()
        GLib.idle_add(self._on_scan_complete, tree_data)

    def _on_scan_progress(self, count: int, current_path: str):
        if not self.is_scanning:
            return False
        short_path = (current_path[:60] + "...") if len(current_path) > 60 else current_path
        self.lbl_status.set_text(f"Проанализировано элементов: {count} | {short_path}")
        return False

    def _on_scan_complete(self, root_node):
        if not self.is_scanning:
            return False

        total_root_size = root_node.get("size", 0)
        self._reset_scan_ui(
            f"Анализ завершен. Всего данных в ветке: {format_bytes(total_root_size)}"
        )

        def populate_store(node, parent_iter=None, max_depth=3, current_depth=0):
            node_size = node.get("size", 0)
            share_pct = f"{(node_size / total_root_size * 100):.1f}%" if total_root_size > 0 else "0%"
            name = node.get("name", "")
            is_d = node.get("is_dir", False)
            pix = get_file_system_icon(node.get("path", ""), is_dir=is_d, size=16)

            has_children = len(node.get("children", [])) > 0
            # Loaded true if we show children right away
            loaded = current_depth < max_depth

            row_iter = self.tree_store.append(parent_iter, [
                pix,
                name,
                format_bytes(node_size),
                share_pct,
                str(node.get("items_count", 1)),
                node.get("path", ""),
                is_d,
                loaded
            ])

            if current_depth < max_depth:
                for child in node.get("children", []):
                    populate_store(child, row_iter, max_depth, current_depth + 1)
            elif is_d and has_children:
                # Add dummy child so GTK shows the expand arrow without hanging the UI
                self.tree_store.append(row_iter, [
                    None,
                    "Загрузка...",
                    "",
                    "",
                    "",
                    "",
                    False,
                    False
                ])

        populate_store(root_node)
        return False
