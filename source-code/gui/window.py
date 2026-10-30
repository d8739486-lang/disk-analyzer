"""Main Application Window with Smooth Fade-in Launch and Animated Stack Transitions."""
import sys
import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

from gui.tab_smart import SmartTab
from gui.tab_usage import UsageTab
from gui.tab_benchmark import BenchmarkTab
from gui.tab_map import MapTab
from gui.tab_settings import SettingsTab
from core.i18n import t
from gui.ui_utils import get_svg_image


class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Disk Analyzer")
        self.set_wmclass("disk-analyzer", "disk-analyzer")
        self.set_role("disk-analyzer")
        Gtk.Window.set_default_icon_name("disk-analyzer")

        # Load multi-resolution application icons (both standalone & zipapp support)
        pixbufs = self._load_app_icons()
        if pixbufs:
            self.set_icon_list(pixbufs)
            Gtk.Window.set_default_icon_list(pixbufs)

        # Adaptive geometry: comfortable modern resolution
        screen = Gdk.Screen.get_default()
        if screen:
            screen_w = screen.get_width()
            screen_h = screen.get_height()
            win_w = min(1280, int(screen_w * 0.90))
            win_h = min(820, int(screen_h * 0.88))
            self.set_default_size(win_w, win_h)
        else:
            self.set_default_size(1220, 780)

        self.set_position(Gtk.WindowPosition.CENTER)
        self.maximize()

        # Start with zero opacity for smooth cinematic fade-in
        self.set_opacity(0.0)

        self._load_styles()
        self._build_ui()

        # Trigger smooth fade-in after window shows
        self._fade_opacity = 0.0
        GLib.timeout_add(16, self._animate_fade_in)

    def _animate_fade_in(self):
        self._fade_opacity += 0.16  # 2x faster fade-in
        if self._fade_opacity >= 1.0:
            self.set_opacity(1.0)
            return False  # Stop timer
        self.set_opacity(self._fade_opacity)
        return True

    def _load_styles(self):
        css_provider = Gtk.CssProvider()
        css_content = None

        # 1. Direct file path if running from source tree
        css_file = os.path.join(os.path.dirname(__file__), "styles.css")
        if os.path.isfile(css_file):
            try:
                with open(css_file, "r", encoding="utf-8") as f:
                    css_content = f.read()
            except Exception:
                pass

        # 2. pkgutil loader (works seamlessly inside zipapp and normal packages)
        if not css_content:
            try:
                import pkgutil
                raw = pkgutil.get_data("gui", "styles.css")
                if raw:
                    css_content = raw.decode("utf-8")
            except Exception:
                pass

        # 3. Zipfile fallback from sys.argv[0] or executable path
        if not css_content:
            try:
                import zipfile
                candidates = [sys.argv[0], sys.executable, os.path.abspath(__file__)]
                for cand in candidates:
                    if cand and zipfile.is_zipfile(cand):
                        with zipfile.ZipFile(cand) as z:
                            if "gui/styles.css" in z.namelist():
                                css_content = z.read("gui/styles.css").decode("utf-8")
                                break
            except Exception:
                pass

        if css_content:
            try:
                css_provider.load_from_data(css_content.encode("utf-8"))
                screen = Gdk.Screen.get_default()
                if screen:
                    Gtk.StyleContext.add_provider_for_screen(
                        screen,
                        css_provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_USER,
                    )
            except Exception as e:
                print(f"[Styles] CSS load error: {e}", file=sys.stderr)

    def _build_ui(self):
        # Native window title and subtitle
        self.set_title("Disk Analyzer")

        # Main vertical container
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Modern Animated Stack (Smooth crossfade between sections, 2x faster: 130ms)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(130)  # 130ms snappy smooth fade

        # StackSwitcher styled as top navigation bar
        switcher_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        switcher_bar.get_style_context().add_class("nav-switcher-bar")

        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.stack)
        switcher_bar.pack_start(self.stack_switcher, True, True, 0)
        main_vbox.pack_start(switcher_bar, False, False, 0)

        # Tab 1: Drives & S.M.A.R.T.
        self.tab_smart = SmartTab()
        self.stack.add_titled(self.tab_smart, "tab_smart", t("tab_smart"))

        # Tab 2: Space Analyzer (Read-Only)
        self.tab_usage = UsageTab()
        self.stack.add_titled(self.tab_usage, "tab_usage", t("tab_usage"))

        # Tab 3: Speed Benchmark (Speedtest.net style)
        self.tab_benchmark = BenchmarkTab()
        self.stack.add_titled(self.tab_benchmark, "tab_bench", t("tab_bench"))

        # Tab 4: Map & Bad Sector Verification (WinDirStat Treemap + Victoria Grid)
        self.tab_map = MapTab()
        self.stack.add_titled(self.tab_map, "tab_map", t("tab_map"))

        # Tab 5: Settings (Language, defaults, preferences)
        self.tab_settings = SettingsTab(main_window=self)
        self.stack.add_titled(self.tab_settings, "tab_settings", t("tab_settings"))

        main_vbox.pack_start(self.stack, True, True, 0)
        self.add(main_vbox)

    def retranslate_ui(self):
        """Update tab headers when user changes language in settings."""
        self.stack.child_set_property(self.tab_smart, "title", t("tab_smart"))
        self.stack.child_set_property(self.tab_usage, "title", t("tab_usage"))
        self.stack.child_set_property(self.tab_benchmark, "title", t("tab_bench"))
        self.stack.child_set_property(self.tab_map, "title", t("tab_map"))
        self.stack.child_set_property(self.tab_settings, "title", t("tab_settings"))

    def _load_app_icons(self):
        """Robustly load icons whether running from source dir or inside a .bin zipapp."""
        import zipfile
        pixbufs = []
        sizes = [512, 256, 128, 64, 48, 32, 24, 16]

        # 1. Try file system relative to script or cwd
        for base_dir in [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons"),
            os.path.join(os.getcwd(), "assets", "icons"),
            os.path.expanduser("~/.local/share/icons/hicolor")
        ]:
            if os.path.exists(base_dir):
                for s in sizes:
                    candidates = [
                        os.path.join(base_dir, f"icon_{s}x{s}.png"),
                        os.path.join(base_dir, f"{s}x{s}", "apps", "disk-analyzer.png"),
                        os.path.join(base_dir, f"{s}x{s}", "apps", "disc-analyzer.png")
                    ]
                    for fpath in candidates:
                        if os.path.exists(fpath):
                            try:
                                pixbufs.append(GdkPixbuf.Pixbuf.new_from_file(fpath))
                                break
                            except Exception:
                                pass
                if pixbufs:
                    return pixbufs

        # 2. Try loading directly from zipapp archive if running bundled
        for zip_candidate in [
            getattr(self, "_zipapp_path", None),
            os.environ.get("AGY_APP_BIN"),
            os.path.join(os.getcwd(), "disk-analyzer.bin"),
            os.path.join(os.getcwd(), "disc-analyzer.bin"),
            os.path.abspath(__file__).split(".bin/")[0] + ".bin" if ".bin/" in os.path.abspath(__file__) else None
        ]:
            if zip_candidate and os.path.isfile(zip_candidate):
                try:
                    with zipfile.ZipFile(zip_candidate, "r") as z:
                        for s in sizes:
                            entry = f"assets/icons/icon_{s}x{s}.png"
                            if entry in z.namelist():
                                data = z.read(entry)
                                loader = GdkPixbuf.PixbufLoader.new_with_type("png")
                                loader.write(data)
                                loader.close()
                                pb = loader.get_pixbuf()
                                if pb:
                                    pixbufs.append(pb)
                    if pixbufs:
                        return pixbufs
                except Exception:
                    pass

        return pixbufs
