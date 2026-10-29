"""Helper module for SVG icons and native system MIME file icons."""
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Rsvg', '2.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, GdkPixbuf, Rsvg, Gio, GLib


SVG_ICONS = {
    "disk": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="22" y1="12" x2="2" y2="12"></line>
        <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path>
        <line x1="6" y1="16" x2="6.01" y2="16"></line>
        <line x1="10" y1="16" x2="10.01" y2="16"></line>
    </svg>''',

    "speedometer": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2v2"></path>
        <path d="m4.93 4.93 1.41 1.41"></path>
        <path d="M20 12h2"></path>
        <path d="m19.07 4.93-1.41 1.41"></path>
        <path d="M2 12h2"></path>
        <path d="M5.64 17.36A9 9 0 1 1 18.36 17.36"></path>
        <path d="m12 12 4-4"></path>
    </svg>''',

    "pie_chart": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
        <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
    </svg>''',

    "pulse": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
    </svg>''',

    "thermometer": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"></path>
    </svg>''',

    "cpu": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
        <rect x="9" y="9" width="6" height="6"></rect>
        <line x1="9" y1="1" x2="9" y2="4"></line>
        <line x1="15" y1="1" x2="15" y2="4"></line>
        <line x1="9" y1="20" x2="9" y2="23"></line>
        <line x1="15" y1="20" x2="15" y2="23"></line>
        <line x1="20" y1="9" x2="23" y2="9"></line>
        <line x1="20" y1="14" x2="23" y2="14"></line>
        <line x1="1" y1="9" x2="4" y2="9"></line>
        <line x1="1" y1="14" x2="4" y2="14"></line>
    </svg>''',

    "clock": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
    </svg>''',

    "refresh": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
    </svg>''',

    "check_circle": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>''',

    "alert_triangle": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
        <line x1="12" y1="9" x2="12" y2="13"></line>
        <line x1="12" y1="17" x2="12.01" y2="17"></line>
    </svg>''',

    "folder": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
    </svg>''',

    "play": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
    </svg>''',

    "stop": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
    </svg>''',

    "arrow_up": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="19" x2="12" y2="5"></line>
        <polyline points="5 12 12 5 19 12"></polyline>
    </svg>''',

    "arrow_left": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="19" y1="12" x2="5" y2="12"></line>
        <polyline points="12 19 5 12 12 5"></polyline>
    </svg>''',

    "arrow_down": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="5" x2="12" y2="19"></line>
        <polyline points="19 12 12 19 5 12"></polyline>
    </svg>''',

    "grid": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7"></rect>
        <rect x="14" y="3" width="7" height="7"></rect>
        <rect x="14" y="14" width="7" height="7"></rect>
        <rect x="3" y="14" width="7" height="7"></rect>
    </svg>''',

    "shield_check": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
        <polyline points="9 12 11 14 15 10"></polyline>
    </svg>''',

    "download": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
    </svg>''',

    "upload": '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="17 8 12 3 7 8"></polyline>
        <line x1="12" y1="3" x2="12" y2="15"></line>
    </svg>''',
}

_icon_cache = {}


def get_svg_pixbuf(name: str, size: int = 16, color: str = "#ffffff") -> GdkPixbuf.Pixbuf:
    """Render an embedded SVG icon into GdkPixbuf at specific size and color."""
    cache_key = (name, size, color)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    raw_svg = SVG_ICONS.get(name)
    if not raw_svg:
        return None

    rendered_svg = raw_svg.format(size=size, color=color)
    try:
        loader = Rsvg.Handle.new_from_data(rendered_svg.encode("utf-8"))
        pb = loader.get_pixbuf()
        _icon_cache[cache_key] = pb
        return pb
    except Exception:
        return None


def get_svg_image(name: str, size: int = 16, color: str = "#ffffff") -> Gtk.Image:
    """Return Gtk.Image with the specified SVG icon."""
    pb = get_svg_pixbuf(name, size=size, color=color)
    if pb:
        return Gtk.Image.new_from_pixbuf(pb)
    return Gtk.Image.new_from_icon_name("image-missing", Gtk.IconSize.MENU)


def get_file_system_icon(file_path: str, is_dir: bool = False, size: int = 16) -> GdkPixbuf.Pixbuf:
    """Query Linux native icon theme for the exact file/folder type (XFCE/Mint theme)."""
    theme = Gtk.IconTheme.get_default()

    if is_dir:
        if ("folder", size) in _icon_cache:
            return _icon_cache[("folder", size)]
        try:
            pb = theme.load_icon("folder", size, Gtk.IconLookupFlags.FORCE_SIZE)
            _icon_cache[("folder", size)] = pb
            return pb
        except Exception:
            return get_svg_pixbuf("folder", size=size, color="#94a3b8")

    ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ""
    if ext and (ext, size) in _icon_cache:
        return _icon_cache[(ext, size)]

    try:
        gfile = Gio.File.new_for_path(file_path)
        info = gfile.query_info("standard::icon", Gio.FileQueryInfoFlags.NONE, None)
        gicon = info.get_icon()
        if gicon:
            icon_info = theme.lookup_by_gicon(gicon, size, Gtk.IconLookupFlags.FORCE_SIZE)
            if icon_info:
                pb = icon_info.load_icon()
                if ext:
                    _icon_cache[(ext, size)] = pb
                return pb
    except Exception:
        pass

    try:
        pb = theme.load_icon("text-x-generic", size, Gtk.IconLookupFlags.FORCE_SIZE)
        return pb
    except Exception:
        return get_svg_pixbuf("disk", size=size, color="#a1a1aa")
