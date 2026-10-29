#!/usr/bin/env python3
"""Linux Disc Analyzer entry point."""
import sys
import os
import signal
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from gui.window import MainWindow


def main():
    # Handle Ctrl+C cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    win = MainWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
