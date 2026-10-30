"""Tab 1: S.M.A.R.T. and Drive Health view with SVG badges, drive icons, and hardware detection."""
import math
import threading
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from core.disk_info import get_block_devices
from core.smart import get_smart_info
from core.i18n import t, get_current_lang
from gui.ui_utils import get_svg_image, get_svg_pixbuf


def get_attribute_description(name: str, num: str) -> str:
    """Human-friendly explanation for SMART and kernel attributes in English or Russian."""
    is_en = get_current_lang() == "en"
    smart_dict_ru = {
        "01": "Общий статус аппаратной самодиагностики накопителя (Raw Read Error Rate). PASSED или отсутствие ошибок свидетельствует о стабильности считывания данных с поверхности.",
        "02": "Текущая температура контроллера или ячеек памяти. Оптимальный рабочий диапазон для NVMe SSD — до 65-70°C, для SATA SSD и HDD — до 45°C.",
        "03": "Общее суммарное время наработки накопителя во включенном состоянии (Power-On Hours). Позволяет оценить реальный возраст устройства.",
        "04": "Счетчик критических предупреждений встроенной системы защиты накопителя. Значение 0 означает нормальное бессбойное состояние.",
        "05": "Доступный резерв ячеек памяти (Available Spare). Показывает процент оставшихся резервных блоков flash-памяти для замены изношенных ячеек. Заводской порог обычно составляет 5-10%.",
        "06": "Процент износа ресурса ячеек (Percentage Used). Отражает реальную выработку ресурса перезаписи (TBW) ячеек памяти. 0% — новый диск, 100% — достижение гарантированного ресурса.",
        "07": "Суммарный объем информации, прочитанной за всю историю службы диска (Total Host Data Read). Считывается напрямую из контроллера NVMe.",
        "08": "Суммарный объем информации, записанной за всю историю службы диска (Total Host Data Written). Считывается напрямую из контроллера NVMe.",
        "09": "Количество полных циклов включения и выключения питания (Power Cycle Count).",
        "10": "Небезопасные отключения питания (Unsafe Shutdowns). Число отключений при аварии, сбоях электросети или принудительном выключении без сброса кэша.",
        "11": "Ошибки целостности данных памяти (Media and Data Integrity Errors). Некорректируемые аппаратные ошибки чтения флеш-памяти или CRC.",
        "12": "Записи журнала ошибок контроллера (Number of Error Information Log Entries). Количество зарегистрированных инцидентов контроллера.",
        "13": "Версия микропрограммы накопителя (Firmware Revision).",
        "14": "Глобальный аппаратный идентификатор накопителя (WWID / EUI-64).",
    }
    smart_dict_en = {
        "01": "Overall hardware self-test diagnostic status (Raw Read Error Rate). PASSED indicates surface integrity and stable flash read capability.",
        "02": "Current operating temperature of the controller or memory chips. Recommended range for NVMe SSD is below 65-70°C, and under 45°C for SATA/HDD.",
        "03": "Cumulative power-on time (Power-On Hours). Indicates the operational age and service time of the storage drive.",
        "04": "Critical warnings counter from hardware controller protection. Zero value confirms healthy error-free hardware state.",
        "05": "Remaining spare flash blocks (Available Spare). Factory threshold is typically 5-10%. Lower values indicate flash cell exhaustion.",
        "06": "Percentage of guaranteed TBW endurance consumed (Percentage Used). 0% is factory-fresh, 100% means rated warranty endurance reached.",
        "07": "Total lifetime data read from the storage device by host systems (Total Host Data Read), read directly from controller registers.",
        "08": "Total lifetime data written to flash memory (Total Host Data Written).",
        "09": "Total count of complete hardware power-on cycles (Power Cycle Count).",
        "10": "Abnormal or emergency shutdowns without flush synchronization (Unsafe Shutdowns).",
        "11": "Uncorrectable data integrity and flash media read errors (Media and Data Integrity Errors).",
        "12": "Number of logged hardware error events in controller non-volatile memory (Error Information Log).",
        "13": "Controller internal firmware revision string (Firmware Revision).",
        "14": "Globally unique hardware identifier (WWID / EUI-64).",
    }

    clean_num = num.strip().lstrip("0") or "0"
    smart_dict = smart_dict_en if is_en else smart_dict_ru
    if clean_num in smart_dict:
        return smart_dict[clean_num]
    if num.strip() in smart_dict:
        return smart_dict[num.strip()]

    nl = name.lower()
    if is_en:
        if "revision" in nl or "spec" in nl:
            return "NVMe Express architectural standard version supported by this storage controller."
        if "state" in nl or "controller" in nl:
            return "Current operational state of the NVMe controller. 'live' indicates ready and running without faults."
        if "sanitize" in nl:
            return "Low-level block erase sanitize state. 'never_sanitized' denotes standard operating mode without purge."
        if "selftest" in nl:
            return "Result of last autonomous background self-test diagnostic."
        return "Hardware self-diagnostic telemetry or Linux kernel block queue parameter."
    else:
        if "ревизия" in nl or "revision" in nl:
            return "Версия стандарта протокола NVMe Express, которую аппаратно поддерживает контроллер накопителя."
        if "состояние" in nl or "state" in nl:
            return "Текущий статус контроллера NVMe. Состояние 'live' подтверждает полную готовность и работу без сбоев."
        if "очистки" in nl or "sanitize" in nl:
            return "Статус низкоуровневой очистки ячеек памяти (Sanitize)."
        if "selftest" in nl or "фонового" in nl:
            return "Результат последнего аппаратного теста накопителя (Self-test)."
        return "Параметр аппаратной самодиагностики диска или системной телеметрии ядра Linux."


class SmoothSwitch(Gtk.EventBox):
    """
    Animated modern switch with smooth sliding knob,
    vector Cairo rendering, and responsive feedback.
    """
    def __init__(self, active=False, on_toggle=None):
        super().__init__()
        self.active = active
        self.on_toggle = on_toggle
        self.anim_val = 1.0 if active else 0.0
        self.anim_timer = None
        self.set_app_paintable(True)
        self.set_size_request(46, 24)
        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._on_click)

    def set_active(self, active: bool):
        if self.active != active:
            self.active = active
            self._start_anim()

    def get_active(self) -> bool:
        return self.active

    def _on_click(self, widget, event):
        self.active = not self.active
        self._start_anim()
        if self.on_toggle:
            self.on_toggle(self.active)
        return True

    def _start_anim(self):
        if not self.anim_timer:
            self.anim_timer = GLib.timeout_add(16, self._anim_step)

    def _anim_step(self):
        target = 1.0 if self.active else 0.0
        step = 0.32  # 2x faster toggle switch animation
        if abs(self.anim_val - target) <= step:
            self.anim_val = target
            self.anim_timer = None
            self.queue_draw()
            return False
        if self.anim_val < target:
            self.anim_val += step
        else:
            self.anim_val -= step
        self.queue_draw()
        return True

    def _on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height
        r = h / 2.0

        # Background color blend (off: calm slate #38383e, on: vibrant blue #1f9ede)
        t = self.anim_val
        cr_r = (56.0 / 255.0) + ((31.0 / 255.0 - 56.0 / 255.0) * t)
        cr_g = (56.0 / 255.0) + ((158.0 / 255.0 - 56.0 / 255.0) * t)
        cr_b = (62.0 / 255.0) + ((222.0 / 255.0 - 62.0 / 255.0) * t)
        cr.set_source_rgb(cr_r, cr_g, cr_b)

        # Rounded pill track
        cr.new_sub_path()
        cr.arc(w - r, r, r, -math.pi / 2, math.pi / 2)
        cr.arc(r, r, r, math.pi / 2, 3 * math.pi / 2)
        cr.close_path()
        cr.fill_preserve()

        # Track border
        border_r = (74.0 / 255.0) + ((56.0 / 255.0 - 74.0 / 255.0) * t)
        border_g = (74.0 / 255.0) + ((189.0 / 255.0 - 74.0 / 255.0) * t)
        border_b = (82.0 / 255.0) + ((248.0 / 255.0 - 82.0 / 255.0) * t)
        cr.set_source_rgb(border_r, border_g, border_b)
        cr.set_line_width(1.0)
        cr.stroke()

        # Smooth sliding white knob
        slider_r = r - 3.0
        slider_x = r + (w - 2 * r) * t
        slider_y = r
        cr.arc(slider_x, slider_y, slider_r, 0, 2 * math.pi)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.fill_preserve()
        cr.set_source_rgba(0, 0, 0, 0.2)
        cr.set_line_width(0.8)
        cr.stroke()
        return True


class SmartSummaryTableWidget(Gtk.EventBox):
    """
    Unified table-style panel matching the exact color and border
    of the Mint-Y dark desktop application (#26262b / #2a2a2f base with #3b3b42 border),
    completely eliminating dark-blue hues.
    """
    def __init__(self):
        super().__init__()
        self.set_app_paintable(True)
        self.connect("draw", self._on_draw)

    def _on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height

        # Background matching the application neutral dark theme (#26262b)
        cr.set_source_rgb(38 / 255.0, 38 / 255.0, 43 / 255.0)
        cr.rectangle(0, 0, w, h)
        cr.fill_preserve()

        # Outer border matching the application clean borders (#3a3a42)
        cr.set_source_rgb(58 / 255.0, 58 / 255.0, 66 / 255.0)
        cr.set_line_width(1.0)
        cr.stroke()

        # Vertical column dividers (columns at 25%, 50%, 75%)
        cr.set_source_rgb(58 / 255.0, 58 / 255.0, 66 / 255.0)
        cr.set_line_width(1.0)
        for i in range(1, 4):
            x = int(w * i / 4.0) + 0.5
            cr.move_to(x, 1)
            cr.line_to(x, h - 1)
        cr.stroke()

        if self.get_child():
            self.propagate_draw(self.get_child(), cr)

        return True


class SmartTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        self.set_margin_top(14)
        self.set_margin_bottom(14)
        self.set_margin_start(14)
        self.set_margin_end(14)

        self.devices = []
        self.advanced_mode = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Left Panel: Physical Drive List
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_box.set_size_request(340, -1)

        head_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        head_icon = get_svg_image("disk", size=18, color="#1f9ede")
        head_box.pack_start(head_icon, False, False, 0)
        self.header_lbl = Gtk.Label(label=t("drives_title"), xalign=0)
        self.header_lbl.get_style_context().add_class("section-title")
        head_box.pack_start(self.header_lbl, True, True, 0)
        left_box.pack_start(head_box, False, False, 0)

        # Drives TreeView with Icons
        # Store: Icon (Pixbuf), Model, Size, Path, Type
        self.dev_store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, str)
        self.dev_tree = Gtk.TreeView(model=self.dev_store)
        self.dev_tree.set_headers_visible(True)
        self.dev_tree.get_selection().connect("changed", self._on_drive_selected)
        self.dev_tree.connect("button-press-event", self._on_drive_button_press)

        # Drive Icon + Name Column
        self.col_dev = Gtk.TreeViewColumn(t("drive_col_name"))
        self.col_dev.set_expand(True)

        cell_icon = Gtk.CellRendererPixbuf()
        cell_icon.set_padding(4, 4)
        self.col_dev.pack_start(cell_icon, False)
        self.col_dev.add_attribute(cell_icon, "pixbuf", 0)

        cell_dev = Gtk.CellRendererText()
        cell_dev.set_property("ellipsize", 3)
        cell_dev.set_padding(4, 6)
        self.col_dev.pack_start(cell_dev, True)
        self.col_dev.add_attribute(cell_dev, "text", 1)
        self.dev_tree.append_column(self.col_dev)

        # Size Column
        self.col_size = Gtk.TreeViewColumn(t("drive_col_size"))
        cell_size = Gtk.CellRendererText()
        cell_size.set_property("xalign", 1.0)
        cell_size.set_padding(4, 6)
        self.col_size.pack_start(cell_size, False)
        self.col_size.add_attribute(cell_size, "text", 2)
        self.col_size.set_min_width(75)
        self.col_size.set_max_width(90)
        self.dev_tree.append_column(self.col_size)

        scroll_left = Gtk.ScrolledWindow()
        scroll_left.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_left.add(self.dev_tree)
        left_box.pack_start(scroll_left, True, True, 0)

        # Bottom Left: Controls
        box_controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        box_switch = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.lbl_switch = Gtk.Label(label=t("adv_mode"), xalign=0)
        self.lbl_switch.get_style_context().add_class("metric-title")
        self.switch_adv = SmoothSwitch(active=False, on_toggle=self._on_advanced_toggled)

        box_switch.pack_start(self.lbl_switch, True, True, 0)
        box_switch.pack_start(self.switch_adv, False, False, 0)
        box_controls.pack_start(box_switch, False, False, 0)

        btn_refresh = Gtk.Button()
        ref_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ref_box.pack_start(get_svg_image("refresh", size=15, color="#cbd5e1"), False, False, 0)
        self.lbl_refresh = Gtk.Label(label=t("btn_refresh_drives"))
        ref_box.pack_start(self.lbl_refresh, False, False, 0)
        btn_refresh.add(ref_box)
        btn_refresh.connect("clicked", lambda b: self.refresh())
        box_controls.pack_start(btn_refresh, False, False, 0)

        left_box.pack_start(box_controls, False, False, 0)
        self.pack_start(left_box, False, False, 0)

        # Single vertical divider line between left and right panels
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(sep, False, False, 4)

        # Right Panel: Drive Details & SMART
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # Top Summary Metrics: Unified Table Panel matching app style and colors
        self.summary_table_widget = SmartSummaryTableWidget()

        grid_cards = Gtk.Grid()
        grid_cards.set_column_homogeneous(True)
        self.summary_table_widget.add(grid_cards)

        def _make_metric_cell(icon_name: str, icon_color: str, title: str):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.set_margin_top(10)
            box.set_margin_bottom(10)
            box.set_margin_start(14)
            box.set_margin_end(14)

            h_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            h_row.pack_start(get_svg_image(icon_name, size=15, color=icon_color), False, False, 0)
            lbl_title = Gtk.Label(label=title, xalign=0)
            lbl_title.get_style_context().add_class("metric-title")
            h_row.pack_start(lbl_title, True, True, 0)
            box.pack_start(h_row, False, False, 0)

            lbl_val = Gtk.Label(label="—", xalign=0)
            lbl_val.get_style_context().add_class("metric-value")
            box.pack_start(lbl_val, False, False, 0)

            return box, box, lbl_val

        # 1. Health Cell
        self.frame_health, self.card_health, self.lbl_health = _make_metric_cell("check_circle", "#73D216", t("card_health"))
        self.lbl_health.set_text(f"{t('health_good')} (100%)")
        self.lbl_health.get_style_context().add_class("badge-good")
        grid_cards.attach(self.frame_health, 0, 0, 1, 1)

        # 2. Temp Cell
        self.frame_temp, self.card_temp, self.lbl_temp = _make_metric_cell("thermometer", "#F27835", t("card_temp"))
        self.lbl_temp.set_text("—")
        grid_cards.attach(self.frame_temp, 1, 0, 1, 1)

        # 3. Interface / Type Cell
        self.frame_type, self.card_type, self.lbl_type = _make_metric_cell("cpu", "#1f9ede", t("card_interface"))
        self.lbl_type.set_text("—")
        grid_cards.attach(self.frame_type, 2, 0, 1, 1)

        # 4. Hours Cell
        self.frame_sn, self.card_sn, self.lbl_sn = _make_metric_cell("clock", "#a855f7", t("card_uptime"))
        self.lbl_sn.set_text("—")
        grid_cards.attach(self.frame_sn, 3, 0, 1, 1)

        right_box.pack_start(self.summary_table_widget, False, False, 0)

        # S.M.A.R.T. Attributes Table
        lbl_attr_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_attr_box.pack_start(get_svg_image("pulse", size=16, color="#1f9ede"), False, False, 0)
        self.lbl_attr = Gtk.Label(label=t("smart_table_title"), xalign=0)
        self.lbl_attr.get_style_context().add_class("section-title")
        lbl_attr_box.pack_start(self.lbl_attr, True, True, 0)

        # Loading spinner indicator when querying drive data
        self.smart_spinner = Gtk.Spinner()
        lbl_attr_box.pack_end(self.smart_spinner, False, False, 0)
        right_box.pack_start(lbl_attr_box, False, False, 0)

        self.smart_store = Gtk.ListStore(str, str, str, str, str, str)
        self.smart_tree = Gtk.TreeView(model=self.smart_store)
        self.smart_tree.set_grid_lines(Gtk.TreeViewGridLines.NONE)
        self.smart_tree.connect("button-press-event", self._on_smart_tree_button_press)

        cols = [
            (t("smart_col_num"), 0, 48, False, 0.0),
            (t("smart_col_param"), 1, 320, True, 0.0),
            (t("smart_col_curr"), 2, 95, False, 0.0),
            (t("smart_col_worst"), 3, 80, False, 0.0),
            (t("smart_col_thresh"), 4, 80, False, 0.0),
            (t("smart_col_val"), 5, 200, True, 0.0),
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
            self.smart_tree.append_column(column)

        scroll_smart = Gtk.ScrolledWindow()
        scroll_smart.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll_smart.add(self.smart_tree)
        right_box.pack_start(scroll_smart, True, True, 0)

        self.pack_start(right_box, True, True, 0)

    def _on_advanced_toggled(self, is_active: bool):
        self.advanced_mode = is_active
        self._update_current_smart()

    def refresh(self):
        self.dev_store.clear()
        self.devices = get_block_devices()

        ssd_icon = get_svg_pixbuf("zap", size=18, color="#3b82f6")
        hdd_icon = get_svg_pixbuf("disk", size=18, color="#94a3b8")

        for dev in self.devices:
            pix = ssd_icon if dev.get("is_ssd") else hdd_icon
            self.dev_store.append([
                pix,
                dev["model"],
                dev["size_str"],
                dev["path"],
                dev["media_type"],
            ])

        if len(self.dev_store) > 0:
            self.dev_tree.get_selection().select_path(Gtk.TreePath.new_first())

    def _on_drive_selected(self, selection):
        self._update_current_smart()

    def _on_drive_button_press(self, tree, event):
        if event.button == 3:  # Right click
            path_info = tree.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path, col, _, _ = path_info
                tree.get_selection().select_path(path)
                model = tree.get_model()
                dev_path = model[path][3]
                dev_model = model[path][1]
                dev_size = model[path][2]
                self._show_drive_context_menu(dev_path, dev_model, dev_size, event)
                return True
        return False

    def _show_drive_context_menu(self, dev_path: str, dev_model: str, dev_size: str, event):
        menu = Gtk.Menu()

        ref_lbl = "Обновить телеметрию SMART" if get_current_lang() == "ru" else "Refresh S.M.A.R.T. Telemetry"
        item_refresh = Gtk.MenuItem(label=ref_lbl)
        item_refresh.connect("activate", lambda m: self._update_current_smart())
        menu.append(item_refresh)

        copy_lbl = "Скопировать системный путь диска" if get_current_lang() == "ru" else "Copy Device Node Path"
        item_copy = Gtk.MenuItem(label=copy_lbl)
        def _copy_path(m):
            clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clip.set_text(dev_path, -1)
        item_copy.connect("activate", _copy_path)
        menu.append(item_copy)

        menu.append(Gtk.SeparatorMenuItem())

        prop_lbl = "Подробные сведения об устройстве" if get_current_lang() == "ru" else "Device Hardware Properties"
        item_props = Gtk.MenuItem(label=prop_lbl)
        item_props.connect("activate", lambda m: self._show_drive_properties(dev_path, dev_model, dev_size))
        menu.append(item_props)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

    def _on_smart_tree_button_press(self, tree, event):
        if event.button == 3:  # Right-click
            pos = tree.get_path_at_pos(int(event.x), int(event.y))
            if pos is not None:
                path, col, _, _ = pos
                tree.get_selection().select_path(path)
                model = tree.get_model()
                tree_iter = model.get_iter(path)
                num = model.get_value(tree_iter, 0)
                name = model.get_value(tree_iter, 1)
                cur = model.get_value(tree_iter, 2)
                worst = model.get_value(tree_iter, 3)
                thresh = model.get_value(tree_iter, 4)
                val = model.get_value(tree_iter, 5)

                menu = Gtk.Menu()

                # 1. Parameter Info
                item_info = Gtk.MenuItem(label="Справка по параметру" if get_current_lang() == "ru" else "Parameter Documentation")
                item_info.connect("activate", lambda w: self._show_attribute_info(num, name, cur, worst, thresh, val))
                menu.append(item_info)

                menu.append(Gtk.SeparatorMenuItem())

                # 2. Copy Value
                display_val = val if len(val) < 25 else (val[:22] + "...")
                copy_lbl = f"Копировать значение ({display_val})" if get_current_lang() == "ru" else f"Copy Value ({display_val})"
                item_copy_val = Gtk.MenuItem(label=copy_lbl)
                item_copy_val.connect("activate", lambda w: self._copy_to_clipboard(val))
                menu.append(item_copy_val)

                # 3. Copy Row
                copy_row_lbl = "Копировать строку целиком" if get_current_lang() == "ru" else "Copy Entire Row"
                item_copy_row = Gtk.MenuItem(label=copy_row_lbl)
                row_str = f"№{num} | {name} | {cur} | {worst} | {thresh} | {val}"
                item_copy_row.connect("activate", lambda w: self._copy_to_clipboard(row_str))
                menu.append(item_copy_row)

                menu.append(Gtk.SeparatorMenuItem())

                # 4. Refresh
                refresh_lbl = "Обновить показатели S.M.A.R.T." if get_current_lang() == "ru" else "Refresh S.M.A.R.T. Telemetry"
                item_refresh = Gtk.MenuItem(label=refresh_lbl)
                item_refresh.connect("activate", lambda w: self._update_current_smart())
                menu.append(item_refresh)

                menu.show_all()
                menu.popup(None, None, None, None, event.button, event.time)
                return True
        return False

    def _copy_to_clipboard(self, text: str):
        clip = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clip.set_text(text, -1)

    def _show_attribute_info(self, num: str, name: str, cur: str, worst: str, thresh: str, val: str):
        desc = get_attribute_description(name, num)
        dialog = Gtk.Dialog(
            title=f"Info: {name}" if get_current_lang() == "en" else f"Справка: {name}",
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_button("Close" if get_current_lang() == "en" else "Закрыть", Gtk.ResponseType.CLOSE)
        dialog.set_default_size(520, 240)

        box = dialog.get_content_area()
        box.set_spacing(12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(18)
        box.set_margin_end(18)

        # Title
        lbl_head = Gtk.Label(xalign=0)
        lbl_head.set_markup(f'<span font_desc="15" weight="bold" color="#ffffff">{name}</span> (№ {num})')
        box.pack_start(lbl_head, False, False, 0)

        # Values Grid
        grid = Gtk.Grid()
        grid.set_column_spacing(16)
        grid.set_row_spacing(6)

        def _add_stat(row, title, val_str):
            lbl_t = Gtk.Label(label=title, xalign=0)
            lbl_t.get_style_context().add_class("metric-title")
            lbl_v = Gtk.Label(label=val_str, xalign=0)
            lbl_v.get_style_context().add_class("metric-value")
            grid.attach(lbl_t, 0, row, 1, 1)
            grid.attach(lbl_v, 1, row, 1, 1)

        is_en = get_current_lang() == "en"
        _add_stat(0, "Raw Value / Status:" if is_en else "Значение / Статус:", val)
        _add_stat(1, "Current Value:" if is_en else "Текущий показатель:", cur)
        _add_stat(2, "Worst Value:" if is_en else "Худший показатель:", worst)
        _add_stat(3, "Critical Threshold:" if is_en else "Критический порог:", thresh)
        box.pack_start(grid, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 4)

        # Description
        lbl_desc_title = Gtk.Label(
            label="Attribute Description & Purpose:" if is_en else "Описание и назначение параметра:",
            xalign=0
        )
        lbl_desc_title.get_style_context().add_class("section-title")
        box.pack_start(lbl_desc_title, False, False, 0)

        lbl_desc = Gtk.Label(label=desc, xalign=0)
        lbl_desc.set_line_wrap(True)
        lbl_desc.get_style_context().add_class("metric-title")
        box.pack_start(lbl_desc, True, True, 0)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _show_drive_properties(self, dev_path: str, dev_model: str, dev_size: str):
        dev_info = next((d for d in self.devices if d["path"] == dev_path), {})
        is_en = get_current_lang() == "en"
        dialog = Gtk.Dialog(
            title=f"Drive Hardware Properties: {dev_model}" if is_en else f"Параметры накопителя: {dev_model}",
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.set_default_size(480, 320)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(14)
        box.set_margin_bottom(14)
        box.set_margin_start(16)
        box.set_margin_end(16)

        grid = Gtk.Grid()
        grid.set_column_spacing(14)
        grid.set_row_spacing(8)

        media_desc = ("Solid State Drive (SSD)" if dev_info.get("is_ssd") else "Hard Disk Drive (HDD)") if is_en else \
                     ("Твердотельный накопитель (SSD)" if dev_info.get("is_ssd") else "Жёсткий диск (HDD)")

        props = [
            ("Model:" if is_en else "Модель:", dev_model),
            ("Device Node:" if is_en else "Системный узел:", dev_path),
            ("Capacity:" if is_en else "Ёмкость:", dev_size),
            ("Serial Number:" if is_en else "Серийный номер:", dev_info.get("serial", "N/A" if is_en else "Не указан")),
            ("Media Type:" if is_en else "Тип носителя:", media_desc),
            ("Bus Transport:" if is_en else "Интерфейс шины:", dev_info.get("tran", "NVMe / PCIe").upper()),
            ("File System:" if is_en else "Файловая система:", dev_info.get("fstype", "ext4 / btrfs")),
        ]

        for i, (k, v) in enumerate(props):
            lbl_k = Gtk.Label(label=k, xalign=0)
            lbl_k.get_style_context().add_class("section-title")
            grid.attach(lbl_k, 0, i, 1, 1)

            lbl_v = Gtk.Label(label=str(v), xalign=0)
            lbl_v.set_selectable(True)
            grid.attach(lbl_v, 1, i, 1, 1)

        box.pack_start(grid, True, True, 0)
        dialog.add_button("Close" if is_en else "Закрыть", Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show_all()

    def _update_current_smart(self):
        selection = self.dev_tree.get_selection()
        model, tree_iter = selection.get_selected()
        if not tree_iter:
            return

        dev_path = model[tree_iter][3]
        dev_info = next((d for d in self.devices if d["path"] == dev_path), None)
        if not dev_info:
            return

        # Start loading indicator
        self.smart_spinner.start()

        def _worker():
            smart = get_smart_info(dev_path, advanced_mode=self.advanced_mode)
            GLib.idle_add(self._apply_smart_data, smart, dev_info)

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_smart_data(self, smart, dev_info):
        self.smart_spinner.stop()

        health = smart.get("health_score", "Хорошо (100%)")
        self.lbl_health.set_text(health)
        style = self.lbl_health.get_style_context()
        style.remove_class("badge-good")
        style.remove_class("badge-warn")
        style.remove_class("badge-bad")

        if "Bad" in health or "FAIL" in health or "Ошибка" in health:
            style.add_class("badge-bad")
        elif "Warning" in health or "Внимание" in health:
            style.add_class("badge-warn")
        else:
            style.add_class("badge-good")

        temp = smart.get("temperature_c")
        self.lbl_temp.set_text(f"{temp:.1f} °C" if temp is not None else "Норма")
        self.lbl_type.set_text(dev_info["media_type"])
        hours = smart.get("power_on_hours", "N/A")
        sn = dev_info.get("serial", "")
        self.lbl_sn.set_text(f"{hours} | S/N: {sn}" if sn != "N/A" else str(hours))

        # Fill SMART table
        self.smart_store.clear()
        attrs = smart.get("attributes", [])
        for a in attrs:
            self.smart_store.append([
                str(a.get("id", "-")),
                str(a.get("name", "")),
                str(a.get("value", "-")),
                str(a.get("worst", "-")),
                str(a.get("thresh", "-")),
                str(a.get("raw", "")),
            ])
        return False
