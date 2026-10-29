"""Tab 3: Disk Speed Benchmark (Real-time Live Numbers & Gauge)."""
import os
import math
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from core.disk_info import get_block_devices
from core.benchmark import DiskBenchmark
from gui.ui_utils import get_svg_image, get_svg_pixbuf
from gui.gauge_widget import SpeedGauge


def _fmt_bench_speed(val: str) -> str:
    """Format speed digits in crisp bold 32px white typography."""
    return f'<span font_desc="32" weight="800" color="#ffffff">{val}</span>'


class BenchmarkCardWidget(Gtk.EventBox):
    """
    Rock-solid matte card widget matching application card theme (#141921 / #283242).
    Guarantees clean, non-glitchy background and 100% visible child content.
    """
    def __init__(self, is_read: bool = True):
        super().__init__()
        self.is_read = is_read
        self.is_active = False
        self.set_app_paintable(True)
        self.connect("draw", self._on_draw)

    def set_active(self, active: bool):
        self.is_active = active
        self.queue_draw()
        p = self.get_parent()
        if p:
            p.queue_draw()

    def _on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height
        r = 6.0

        # Background matching application card theme (#26262b)
        cr.set_source_rgb(38 / 255.0, 38 / 255.0, 43 / 255.0)
        cr.new_sub_path()
        cr.arc(w - r - 0.5, r + 0.5, r, -math.pi / 2, 0)
        cr.arc(w - r - 0.5, h - r - 0.5, r, 0, math.pi / 2)
        cr.arc(r + 0.5, h - r - 0.5, r, math.pi / 2, math.pi)
        cr.arc(r + 0.5, r + 0.5, r, math.pi, 3 * math.pi / 2)
        cr.close_path()
        cr.fill_preserve()

        # Crisp clean border matching application (#3a3a42)
        cr.set_source_rgb(58 / 255.0, 58 / 255.0, 66 / 255.0)
        cr.set_line_width(1.0)
        cr.stroke()

        if self.get_child():
            self.propagate_draw(self.get_child(), cr)

        return True


class BenchmarkTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(14)
        self.set_margin_end(14)

        self.bench = None
        self.is_running = False
        self._build_ui()
        self.load_targets()

    def _build_ui(self):
        # 1. Top Controls Row
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        ctrl_box.pack_start(get_svg_image("speedometer", size=18, color="#ffffff"), False, False, 0)

        lbl_target = Gtk.Label(label="Тестируемый раздел:")
        lbl_target.get_style_context().add_class("section-title")
        ctrl_box.pack_start(lbl_target, False, False, 0)

        self.combo_target = Gtk.ComboBoxText()
        self.combo_target.set_size_request(340, -1)
        ctrl_box.pack_start(self.combo_target, False, False, 0)

        lbl_size = Gtk.Label(label="Объем файла теста:")
        ctrl_box.pack_start(lbl_size, False, False, 0)

        self.selected_size_mb = "1024"
        self.size_btn = Gtk.MenuButton()
        self.size_btn.get_style_context().add_class("combo-selector-btn")
        self.size_btn.set_size_request(130, -1)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.lbl_selected_size = Gtk.Label(label="1 ГБ", xalign=0.5)
        btn_box.pack_start(self.lbl_selected_size, True, True, 0)
        self.size_btn.add(btn_box)

        self.size_popover = Gtk.Popover()
        self.size_popover.set_no_show_all(True)
        self.size_popover.set_relative_to(self.size_btn)
        self.size_popover.set_position(Gtk.PositionType.BOTTOM)
        self.size_popover.get_style_context().add_class("clean-popover-menu")

        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        pop_box.set_margin_top(6)
        pop_box.set_margin_bottom(6)
        pop_box.set_margin_start(6)
        pop_box.set_margin_end(6)

        self.size_options = [
            ("64",    "64 МБ"),
            ("128",   "128 МБ"),
            ("256",   "256 МБ"),
            ("512",   "512 МБ"),
            ("1024",  "1 ГБ"),
            ("2048",  "2 ГБ"),
            ("4096",  "4 ГБ"),
            ("8192",  "8 ГБ"),
            ("16384", "16 ГБ"),
        ]
        self.size_item_buttons = {}

        for val, label_text in self.size_options:
            item_btn = Gtk.Button(label=label_text)
            item_btn.get_style_context().add_class("popover-item-btn")
            if val == self.selected_size_mb:
                item_btn.get_style_context().add_class("popover-item-selected")
            item_btn.connect("clicked", self._on_size_selected, val, label_text)
            self.size_item_buttons[val] = item_btn
            pop_box.pack_start(item_btn, False, False, 0)

        self.size_popover.add(pop_box)
        pop_box.show_all()
        self.size_btn.set_popover(self.size_popover)
        ctrl_box.pack_start(self.size_btn, False, False, 0)

        # Action Button
        self.btn_action = Gtk.Button()
        self.btn_action.get_style_context().add_class("primary-btn")
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.action_icon = get_svg_image("play", size=14, color="#ffffff")
        self.action_lbl = Gtk.Label(label="Запустить тест скорости")
        self.action_box.pack_start(self.action_icon, False, False, 0)
        self.action_box.pack_start(self.action_lbl, False, False, 0)
        self.btn_action.add(self.action_box)
        self.btn_action.connect("clicked", self._on_action_clicked)
        ctrl_box.pack_start(self.btn_action, False, False, 0)

        self.pack_start(ctrl_box, False, False, 0)

        # Single horizontal separator line
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep, False, False, 2)

        # 2. Stage Box (Speedtest Gauge + Live Progress)
        self.center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        self.center_box.set_no_show_all(True)
        self.center_box.hide()

        gauge_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        gauge_container.set_size_request(280, 190)
        self.gauge = SpeedGauge()
        gauge_container.pack_start(self.gauge, True, True, 0)
        self.center_box.pack_start(gauge_container, False, False, 0)

        stage_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        stage_info_box.set_valign(Gtk.Align.CENTER)

        status_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.bench_spinner = Gtk.Spinner()
        status_header_box.pack_start(self.bench_spinner, False, False, 0)

        self.lbl_status = Gtk.Label(label="Готов к тестированию скорости накопителя.", xalign=0)
        self.lbl_status.get_style_context().add_class("section-title")
        status_header_box.pack_start(self.lbl_status, True, True, 0)
        stage_info_box.pack_start(status_header_box, False, False, 0)

        self.lbl_substatus = Gtk.Label(
            label="Идёт измерение пропускной способности контроллера.",
            xalign=0
        )
        self.lbl_substatus.get_style_context().add_class("metric-title")
        stage_info_box.pack_start(self.lbl_substatus, False, False, 0)

        self.overall_progress = Gtk.ProgressBar()
        self.overall_progress.set_fraction(0.0)
        stage_info_box.pack_start(self.overall_progress, False, False, 0)

        self.center_box.pack_start(stage_info_box, True, True, 0)
        self.pack_start(self.center_box, False, False, 0)

        # 3. 4 Result Cards (2x2 Grid)
        grid_cards = Gtk.Grid()
        grid_cards.set_column_spacing(14)
        grid_cards.set_row_spacing(14)
        grid_cards.set_column_homogeneous(True)
        grid_cards.set_row_homogeneous(True)

        # Card 1: Sequential Write
        self.card_seq_write, self.val_seq_write, self.unit_seq_write, self.spin_seq_write, self.prog_seq_write = self._create_card(
            title="Запись больших файлов (SEQ 1M)",
            desc="Копирование фильмов, игр, установщиков и тяжелых архивов",
            icon_name="upload", is_read=False
        )
        grid_cards.attach(self.card_seq_write, 1, 0, 1, 1)

        # Card 2: Sequential Read
        self.card_seq_read, self.val_seq_read, self.unit_seq_read, self.spin_seq_read, self.prog_seq_read = self._create_card(
            title="Чтение больших файлов (SEQ 1M)",
            desc="Запуск игр, загрузка видеомонтажа и открытие больших баз данных",
            icon_name="download", is_read=True
        )
        grid_cards.attach(self.card_seq_read, 0, 0, 1, 1)

        # Card 3: Random Write
        self.card_rnd_write, self.val_rnd_write, self.unit_rnd_write, self.spin_rnd_write, self.prog_rnd_write = self._create_card(
            title="Случайная запись мелких блоков (4K RND)",
            desc="Запись логов, кэша браузера, фоновых сервисов и обновлений ОС",
            icon_name="upload", is_read=False
        )
        grid_cards.attach(self.card_rnd_write, 1, 1, 1, 1)

        # Card 4: Random Read
        self.card_rnd_read, self.val_rnd_read, self.unit_rnd_read, self.spin_rnd_read, self.prog_rnd_read = self._create_card(
            title="Случайный отклик системы (4K RND)",
            desc="Главный параметр отзывчивости рабочего стола, меню и открытия программ",
            icon_name="download", is_read=True
        )
        grid_cards.attach(self.card_rnd_read, 0, 1, 1, 1)

        self.pack_start(grid_cards, True, True, 0)

        # 4. Dismissible persistent tip box
        config_dir = os.path.expanduser("~/.config/disk-analyzer")
        self.tip_hide_file = os.path.join(config_dir, "hide_bench_tip")

        if not os.path.exists(self.tip_hide_file):
            self.tip_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            lbl_note = Gtk.Label(
                label="💡 Совет для пользователя: высокие показатели 4K RND (>60 МБ/с) означают молниеносный отклик интерфейса Linux,\n"
                      "а высокие показатели SEQ 1M (>2000 МБ/с) гарантируют сверхбыстрое копирование любых гигантских файлов.",
                xalign=0
            )
            lbl_note.get_style_context().add_class("metric-title")
            self.tip_box.pack_start(lbl_note, True, True, 0)

            btn_close_tip = Gtk.Button()
            btn_close_tip.get_style_context().add_class("flat-link-btn")
            btn_close_tip.set_relief(Gtk.ReliefStyle.NONE)
            b_close_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            lbl_b = Gtk.Label(label="Больше не показывать")
            lbl_b.get_style_context().add_class("metric-title")
            b_close_box.pack_start(lbl_b, False, False, 0)
            btn_close_tip.add(b_close_box)
            btn_close_tip.connect("clicked", self._on_dismiss_tip)
            self.tip_box.pack_end(btn_close_tip, False, False, 0)

            self.pack_start(self.tip_box, False, False, 0)

    def _on_dismiss_tip(self, btn):
        try:
            os.makedirs(os.path.dirname(self.tip_hide_file), exist_ok=True)
            with open(self.tip_hide_file, "w") as f:
                f.write("hidden")
        except Exception:
            pass
        if hasattr(self, "tip_box"):
            self.tip_box.hide()
            self.remove(self.tip_box)

    def _create_card(self, title: str, desc: str, icon_name: str, is_read: bool):
        card_widget = BenchmarkCardWidget(is_read=is_read)
        card_widget.get_style_context().add_class("bench-card")
        card_widget.set_size_request(-1, 160)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("bench-card-inner")
        card.set_margin_top(14)
        card.set_margin_bottom(14)
        card.set_margin_start(16)
        card.set_margin_end(16)
        card_widget.add(card)

        # Title row: Icon + Title + Spinner
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon_color = "#38bdf8" if is_read else "#c084fc"
        icon_img = get_svg_image(icon_name, size=18, color=icon_color)
        title_row.pack_start(icon_img, False, False, 0)

        lbl_t = Gtk.Label(label=title, xalign=0)
        lbl_t.get_style_context().add_class("section-title")
        title_row.pack_start(lbl_t, True, True, 0)

        card_spinner = Gtk.Spinner()
        title_row.pack_start(card_spinner, False, False, 0)
        card.pack_start(title_row, False, False, 0)

        # Description
        lbl_d = Gtk.Label(label=desc, xalign=0)
        lbl_d.get_style_context().add_class("metric-title")
        lbl_d.set_line_wrap(True)
        card.pack_start(lbl_d, False, False, 0)

        # Speed row: Value label + Unit label
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        val_lbl = Gtk.Label()
        val_lbl.set_use_markup(True)
        val_lbl.set_markup(_fmt_bench_speed("—"))
        val_lbl.set_xalign(0)
        val_lbl.get_style_context().add_class("bench-speed-value")

        unit_lbl = Gtk.Label(label="МБ/с", xalign=0)
        unit_lbl.get_style_context().add_class("bench-speed-unit")

        speed_box.pack_start(val_lbl, False, False, 0)
        speed_box.pack_start(unit_lbl, False, False, 0)

        # Progress bar shown during active testing of this card
        card_prog = Gtk.ProgressBar()
        card_prog.get_style_context().add_class("card-progressbar")
        card_prog.set_hexpand(True)
        card_prog.set_valign(Gtk.Align.CENTER)
        card_prog.set_no_show_all(True)
        card_prog.hide()
        speed_box.pack_start(card_prog, True, True, 0)

        card.pack_start(speed_box, True, True, 0)

        return card_widget, val_lbl, unit_lbl, card_spinner, card_prog

    def load_targets(self):
        self.combo_target.remove_all()
        home = os.path.expanduser("~")
        devices = get_block_devices()

        targets = []
        for dev in devices:
            for part in dev.get("partitions", []):
                mp = part.get("mountpoint")
                if mp and os.access(mp, os.W_OK):
                    targets.append((mp, f"{part.get('friendly_desc')} — {mp}"))

        targets.append((home, f"Домашняя папка пользователя ({home})"))
        targets.sort(key=lambda x: 0 if x[0] == "/" else 1)

        for path, name in targets:
            self.combo_target.append(path, name)

        if len(targets) > 0:
            self.combo_target.set_active(0)

    def _on_action_clicked(self, btn):
        if self.is_running:
            self._stop_bench()
        else:
            self._start_bench()

    def _on_size_selected(self, btn, val: str, label_text: str):
        self.selected_size_mb = val
        self.lbl_selected_size.set_text(label_text)
        for opt_val, opt_btn in self.size_item_buttons.items():
            if opt_val == val:
                opt_btn.get_style_context().add_class("popover-item-selected")
            else:
                opt_btn.get_style_context().remove_class("popover-item-selected")
        self.size_popover.popdown()

    def _start_bench(self):
        target_dir = self.combo_target.get_active_id() or os.path.expanduser("~")
        if not os.access(target_dir, os.W_OK):
            self.lbl_status.set_text("Ошибка: нет прав на запись в выбранный раздел")
            return

        size_mb = int(self.selected_size_mb or "1024")

        self.is_running = True
        self.btn_action.get_style_context().remove_class("primary-btn")
        self.btn_action.get_style_context().add_class("danger-btn")
        self.action_lbl.set_text("Прервать")
        self.action_icon.set_from_pixbuf(get_svg_pixbuf("stop", size=14, color="#ffffff"))

        self.center_box.show()
        self.bench_spinner.start()

        # Reset all cards: reset to "—", hide progressbars, show labels
        for val_lbl, unit_lbl, prog, spin in [
            (self.val_seq_write, self.unit_seq_write, self.prog_seq_write, self.spin_seq_write),
            (self.val_seq_read, self.unit_seq_read, self.prog_seq_read, self.spin_seq_read),
            (self.val_rnd_write, self.unit_rnd_write, self.prog_rnd_write, self.spin_rnd_write),
            (self.val_rnd_read, self.unit_rnd_read, self.prog_rnd_read, self.spin_rnd_read),
        ]:
            val_lbl.set_markup(_fmt_bench_speed("—"))
            val_lbl.show()
            unit_lbl.show()
            prog.hide()
            prog.set_fraction(0.0)
            spin.stop()

        self.overall_progress.set_fraction(0.0)
        self._set_active_card("seq_write")

        self.bench = DiskBenchmark(target_dir=target_dir, file_size_mb=size_mb)
        threading.Thread(target=self._run_bench_thread, daemon=True).start()

    def _on_bench_finish(self):
        self.is_running = False
        self.btn_action.get_style_context().remove_class("danger-btn")
        self.btn_action.get_style_context().add_class("primary-btn")
        self.action_lbl.set_text("Запустить тест скорости")
        self.action_icon.set_from_pixbuf(get_svg_pixbuf("play", size=14, color="#ffffff"))

        self.bench_spinner.stop()
        self._set_active_card(None)
        
        # Ensure all progressbars hidden and final numbers visible
        for val_lbl, unit_lbl, prog in [
            (self.val_seq_write, self.unit_seq_write, self.prog_seq_write),
            (self.val_seq_read, self.unit_seq_read, self.prog_seq_read),
            (self.val_rnd_write, self.unit_rnd_write, self.prog_rnd_write),
            (self.val_rnd_read, self.unit_rnd_read, self.prog_rnd_read),
        ]:
            prog.hide()
            val_lbl.show()
            unit_lbl.show()

        self.overall_progress.set_fraction(1.0)
        self.gauge.reset("ЗАВЕРШЕНО")
        self.lbl_status.set_text("Тестирование скорости успешно завершено!")
        self.lbl_substatus.set_text("Все 4 цикла измерений зафиксированы в карточках ниже.")
        return False

    def _stop_bench(self):
        if self.bench:
            self.bench.cancel()
        self.is_running = False
        self.bench_spinner.stop()
        self._set_active_card(None)
        self.gauge.reset("ПРЕРВАНО")
        self.lbl_status.set_text("Тест остановлен пользователем.")
        self.lbl_substatus.set_text("Тестирование было прервано досрочно.")

        self.btn_action.get_style_context().remove_class("danger-btn")
        self.btn_action.get_style_context().add_class("primary-btn")
        self.action_lbl.set_text("Запустить тест скорости")
        self.action_icon.set_from_pixbuf(get_svg_pixbuf("play", size=14, color="#ffffff"))

        for val_lbl, unit_lbl, prog in [
            (self.val_seq_write, self.unit_seq_write, self.prog_seq_write),
            (self.val_seq_read, self.unit_seq_read, self.prog_seq_read),
            (self.val_rnd_write, self.unit_rnd_write, self.prog_rnd_write),
            (self.val_rnd_read, self.unit_rnd_read, self.prog_rnd_read),
        ]:
            prog.hide()
            val_lbl.show()
            unit_lbl.show()
            if "0.0" in val_lbl.get_text():
                val_lbl.set_markup(_fmt_bench_speed("—"))

    def _set_active_card(self, stage: str):
        cards_map = {
            "seq_write": (self.card_seq_write, self.val_seq_write, self.unit_seq_write, self.prog_seq_write, self.spin_seq_write,
                          "1/4: Последовательная запись (SEQ 1M Write)...", "ЗАПИСЬ SEQ"),
            "seq_read":  (self.card_seq_read, self.val_seq_read, self.unit_seq_read, self.prog_seq_read, self.spin_seq_read,
                          "2/4: Последовательное чтение (SEQ 1M Read)...",  "ЧТЕНИЕ SEQ"),
            "rnd_write": (self.card_rnd_write, self.val_rnd_write, self.unit_rnd_write, self.prog_rnd_write, self.spin_rnd_write,
                          "3/4: Случайная запись 4K (RND 4K Write)...",     "ЗАПИСЬ 4K"),
            "rnd_read":  (self.card_rnd_read, self.val_rnd_read, self.unit_rnd_read, self.prog_rnd_read, self.spin_rnd_read,
                          "4/4: Случайное чтение 4K (RND 4K Read)...",      "ЧТЕНИЕ 4K"),
        }

        for key, (card, val_lbl, unit_lbl, prog, spin, text, gstage) in cards_map.items():
            card.set_active(False)
            spin.stop()

        if stage in cards_map:
            card, val_lbl, unit_lbl, prog, spin, text, gstage = cards_map[stage]
            card.set_active(True)
            spin.start()
            val_lbl.hide()
            unit_lbl.hide()
            prog.set_fraction(0.0)
            prog.show()
            self.lbl_status.set_text(text)
            self.gauge.set_speed(0.0, gstage)

    def _run_bench_thread(self):
        def on_metric_update(metric_name, speed):
            GLib.idle_add(self._update_metric_final, metric_name, speed)

        def on_metric_progress(metric_name, pct, live_speed):
            GLib.idle_add(self._update_metric_progress, metric_name, pct, live_speed)

        self.bench.run_all(on_update=on_metric_update, on_progress=on_metric_progress)
        GLib.idle_add(self._on_bench_finish)

    def _update_metric_progress(self, metric_name: str, pct: float, live_speed: float):
        if not self.is_running:
            return False

        self.gauge.set_speed(live_speed)

        if metric_name == "seq_write":
            self.prog_seq_write.set_fraction(pct)
            self.overall_progress.set_fraction(0.0 + pct * 0.25)
            self.lbl_substatus.set_text(f"Создание непрерывного потока блоков... Прогресс этапа: {int(pct*100)}%")
        elif metric_name == "seq_read":
            self.prog_seq_read.set_fraction(pct)
            self.overall_progress.set_fraction(0.25 + pct * 0.25)
            self.lbl_substatus.set_text(f"Считывание тестового блока памяти... Прогресс этапа: {int(pct*100)}%")
        elif metric_name == "rnd_write":
            self.prog_rnd_write.set_fraction(pct)
            self.overall_progress.set_fraction(0.50 + pct * 0.25)
            self.lbl_substatus.set_text(f"Случайный доступ блоками 4 КБ... Прогресс этапа: {int(pct*100)}%")
        elif metric_name == "rnd_read":
            self.prog_rnd_read.set_fraction(pct)
            self.overall_progress.set_fraction(0.75 + pct * 0.25)
            self.lbl_substatus.set_text(f"Проверка отклика секторов... Прогресс этапа: {int(pct*100)}%")

        return False

    def _update_metric_final(self, metric_name: str, speed: float):
        if not self.is_running:
            return False

        speed_text = f"{speed:.1f}"

        if metric_name == "seq_write":
            self.card_seq_write.set_active(False)
            self.spin_seq_write.stop()
            self.prog_seq_write.hide()
            self.val_seq_write.set_markup(_fmt_bench_speed(speed_text))
            self.val_seq_write.show()
            self.unit_seq_write.show()
            self._set_active_card("seq_read")
        elif metric_name == "seq_read":
            self.card_seq_read.set_active(False)
            self.spin_seq_read.stop()
            self.prog_seq_read.hide()
            self.val_seq_read.set_markup(_fmt_bench_speed(speed_text))
            self.val_seq_read.show()
            self.unit_seq_read.show()
            self._set_active_card("rnd_write")
        elif metric_name == "rnd_write":
            self.card_rnd_write.set_active(False)
            self.spin_rnd_write.stop()
            self.prog_rnd_write.hide()
            self.val_rnd_write.set_markup(_fmt_bench_speed(speed_text))
            self.val_rnd_write.show()
            self.unit_rnd_write.show()
            self._set_active_card("rnd_read")
        elif metric_name == "rnd_read":
            self.card_rnd_read.set_active(False)
            self.spin_rnd_read.stop()
            self.prog_rnd_read.hide()
            self.val_rnd_read.set_markup(_fmt_bench_speed(speed_text))
            self.val_rnd_read.show()
            self.unit_rnd_read.show()

        return False
