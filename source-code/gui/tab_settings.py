"""Settings Tab allowing runtime language toggle, default benchmark preferences, and app info."""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from core.i18n import t, get_current_lang, set_current_lang
from core.config import get_setting, set_setting
from gui.ui_utils import get_svg_image
from gui.tab_smart import SmoothSwitch


class SettingsTab(Gtk.Box):
    def __init__(self, main_window=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.main_window = main_window

        self._build_ui()

    def _build_ui(self):
        # Header
        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        h_box.pack_start(get_svg_image("settings", size=20, color="#1f9ede"), False, False, 0)
        lbl_title = Gtk.Label(label=t("settings_title"), xalign=0)
        lbl_title.get_style_context().add_class("section-title")
        h_box.pack_start(lbl_title, True, True, 0)
        self.pack_start(h_box, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep, False, False, 2)

        # Settings Card Container
        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        settings_box.get_style_context().add_class("card-panel")
        settings_box.set_margin_top(8)

        # Row 1: Language
        row_lang = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        desc_lang = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_lang = Gtk.Label(label=t("settings_lang_label"), xalign=0)
        lbl_lang.get_style_context().add_class("metric-title")
        lbl_lang_sub = Gtk.Label(label=t("settings_lang_desc"), xalign=0)
        lbl_lang_sub.get_style_context().add_class("info-dim")
        desc_lang.pack_start(lbl_lang, False, False, 0)
        desc_lang.pack_start(lbl_lang_sub, False, False, 0)
        row_lang.pack_start(desc_lang, True, True, 0)

        self.combo_lang = Gtk.ComboBoxText()
        self.combo_lang.append("en", "English (Default)")
        self.combo_lang.append("ru", "Русский")
        self.combo_lang.set_active_id(get_current_lang())
        self.combo_lang.set_size_request(200, -1)
        self.combo_lang.connect("changed", self._on_language_changed)
        row_lang.pack_end(self.combo_lang, False, False, 0)
        settings_box.pack_start(row_lang, False, False, 4)

        # Row 2: Benchmark preset size
        row_bench = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        desc_bench = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_bench = Gtk.Label(label=t("settings_bench_label"), xalign=0)
        lbl_bench.get_style_context().add_class("metric-title")
        lbl_bench_sub = Gtk.Label(label=t("settings_bench_desc"), xalign=0)
        lbl_bench_sub.get_style_context().add_class("info-dim")
        desc_bench.pack_start(lbl_bench, False, False, 0)
        desc_bench.pack_start(lbl_bench_sub, False, False, 0)
        row_bench.pack_start(desc_bench, True, True, 0)

        self.combo_bench_size = Gtk.ComboBoxText()
        sizes = [("256", "256 MB"), ("512", "512 MB"), ("1024", "1 GB (Default)"), ("2048", "2 GB"), ("4096", "4 GB")]
        for s_id, s_lbl in sizes:
            self.combo_bench_size.append(s_id, s_lbl)
        current_size = str(get_setting("benchmark_size_mb", "1024"))
        self.combo_bench_size.set_active_id(current_size if current_size in [s[0] for s in sizes] else "1024")
        self.combo_bench_size.set_size_request(200, -1)
        self.combo_bench_size.connect("changed", self._on_bench_size_changed)
        row_bench.pack_end(self.combo_bench_size, False, False, 0)
        settings_box.pack_start(row_bench, False, False, 4)

        # Row 3: Advanced Mode toggle
        row_adv = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        desc_adv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_adv = Gtk.Label(label=t("settings_adv_label"), xalign=0)
        lbl_adv.get_style_context().add_class("metric-title")
        lbl_adv_sub = Gtk.Label(label=t("settings_adv_desc"), xalign=0)
        lbl_adv_sub.get_style_context().add_class("info-dim")
        desc_adv.pack_start(lbl_adv, False, False, 0)
        desc_adv.pack_start(lbl_adv_sub, False, False, 0)
        row_adv.pack_start(desc_adv, True, True, 0)

        self.switch_adv_default = SmoothSwitch(
            active=bool(get_setting("advanced_mode", False)),
            on_toggle=self._on_adv_switch_changed
        )
        row_adv.pack_end(self.switch_adv_default, False, False, 0)
        settings_box.pack_start(row_adv, False, False, 4)

        self.pack_start(settings_box, False, False, 0)

        # About Card
        about_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        about_box.get_style_context().add_class("card-panel")
        
        lbl_about_head = Gtk.Label(label=t("settings_about_title"), xalign=0)
        lbl_about_head.get_style_context().add_class("section-title")
        about_box.pack_start(lbl_about_head, False, False, 0)

        lbl_about = Gtk.Label(label=t("settings_about_desc"), xalign=0)
        lbl_about.set_line_wrap(True)
        about_box.pack_start(lbl_about, False, False, 0)

        lbl_config_path = Gtk.Label(label=f"Config Path: ~/.config/disk-analyzer/settings.json", xalign=0)
        lbl_config_path.get_style_context().add_class("info-dim")
        about_box.pack_start(lbl_config_path, False, False, 0)

        self.pack_start(about_box, False, False, 10)

    def _on_language_changed(self, combo):
        selected = combo.get_active_id()
        if selected:
            set_current_lang(selected)
            if self.main_window and hasattr(self.main_window, "retranslate_ui"):
                self.main_window.retranslate_ui()

    def _on_bench_size_changed(self, combo):
        selected = combo.get_active_id()
        if selected:
            set_setting("benchmark_size_mb", selected)

    def _on_adv_switch_changed(self, is_active: bool):
        set_setting("advanced_mode", is_active)

