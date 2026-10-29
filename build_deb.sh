#!/usr/bin/env bash
set -e

APP_NAME="disc-analyzer"
VERSION="1.0.0"
ARCH="all"
PKG_DIR="build/deb_pkg"

echo "==> Сборка автономного исполняемого пакета $APP_NAME..."
python3 -c '
import os, shutil, zipapp
b = "build/bundle"
if os.path.exists(b): shutil.rmtree(b)
os.makedirs(b, exist_ok=True)
for d in ["core", "gui", "assets"]:
    if os.path.exists(d):
        shutil.copytree(d, os.path.join(b, d), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copy("main.py", os.path.join(b, "__main__.py"))
shutil.copy("main.py", os.path.join(b, "main.py"))
zipapp.create_archive(b, "disc-analyzer.bin", interpreter="/usr/bin/env python3")
os.chmod("disc-analyzer.bin", 0o755)
'

echo "==> Формирование файловой структуры DEB..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

cp disc-analyzer.bin "$PKG_DIR/usr/bin/$APP_NAME"
chmod 755 "$PKG_DIR/usr/bin/$APP_NAME"

cp assets/icons/icon_256x256.png "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"

cat << "EOF" > "$PKG_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Name=Disc Analyzer
Comment=Анализ накопителей, S.M.A.R.T., тест скорости и карта секторов
Exec=/usr/bin/disc-analyzer
Icon=disc-analyzer
Terminal=false
Type=Application
Categories=System;Utility;Filesystem;
StartupNotify=true
StartupWMClass=disc-analyzer
EOF

cat << "EOF" > "$PKG_DIR/DEBIAN/control"
Package: disc-analyzer
Version: 1.0.0
Architecture: all
Maintainer: d8739486 <d8739486@gmail.com>
Depends: python3, python3-gi, python3-gi-cairo, gir1.2-gtk-3.0
Section: utils
Priority: optional
Description: Modern Linux Disc Analyzer
 Native GTK3 storage utility for Linux Mint and Ubuntu.
 Features S.M.A.R.T. health diagnostics, drive speed benchmark,
 WinDirStat-like disk usage treemap, and Victoria-like sector verification.
EOF

echo "==> Упаковка пакета dpkg-deb..."
dpkg-deb --build "$PKG_DIR" "${APP_NAME}_${VERSION}_${ARCH}.deb"

echo "==> Успешно собран пакет: ${APP_NAME}_${VERSION}_${ARCH}.deb"

