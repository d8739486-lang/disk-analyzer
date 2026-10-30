"""Disk and partition discovery module using lsblk, statvfs and udisks2."""
import json
import os
import subprocess
from typing import Dict, List, Any
from core.i18n import t, get_current_lang


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string (IEC units)."""
    if size_bytes < 0:
        return "0 B"
    is_en = get_current_lang() == "en"
    units = ["B", "KB", "MB", "GB", "TB", "PB"] if is_en else ["Б", "КБ", "МБ", "ГБ", "ТБ", "ПБ"]
    val = float(size_bytes)
    for unit in units:
        if val < 1024.0 or unit == units[-1]:
            if unit in ("B", "KB", "Б", "КБ"):
                return f"{int(val)} {unit}"
            return f"{val:.1f} {unit}"
        val /= 1024.0
    return f"{val:.1f} {'TB' if is_en else 'ТБ'}"


def get_mount_usage(mountpoint: str) -> Dict[str, Any]:
    """Get total, used, free space for a mountpoint using statvfs."""
    try:
        stat = os.statvfs(mountpoint)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = total - free
        percent = (used / total * 100.0) if total > 0 else 0.0
        return {
            "total": total,
            "used": used,
            "free": free,
            "percent": percent,
            "total_str": format_bytes(total),
            "used_str": format_bytes(used),
            "free_str": format_bytes(free),
        }
    except Exception:
        return {
            "total": 0,
            "used": 0,
            "free": 0,
            "percent": 0.0,
            "total_str": "0 Б",
            "used_str": "0 Б",
            "free_str": "0 Б",
        }


def get_block_devices() -> List[Dict[str, Any]]:
    """Get structured block devices and partitions list."""
    cmd = [
        "lsblk",
        "-J",
        "-b",
        "-o",
        "NAME,PATH,MODEL,SERIAL,SIZE,TYPE,MOUNTPOINT,FSTYPE,ROTA,TRAN,LABEL",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        devices = data.get("blockdevices", [])
    except Exception:
        devices = []

    result = []
    for dev in devices:
        dev_type = dev.get("type", "")
        # Filter out loop / ram devices
        if dev_type not in ("disk", "nvme"):
            continue

        raw_size = int(dev.get("size") or 0)
        is_ssd = dev.get("rota") is False
        tran = (dev.get("tran") or ("nvme" if "nvme" in dev.get("name", "") else "sata")).lower()

        # Friendly drive label
        model_name = (dev.get("model") or "").strip()
        if not model_name:
            model_name = t("main_nvme") if "nvme" in tran else t("sys_drive")

        media_name = t("nvme_fast") if tran == "nvme" else (t("sata_ssd") if is_ssd else t("hdd_disk"))

        item = {
            "name": dev.get("name", ""),
            "path": dev.get("path") or f"/dev/{dev.get('name')}",
            "model": model_name,
            "serial": (dev.get("serial") or "N/A").strip(),
            "size": raw_size,
            "size_str": format_bytes(raw_size),
            "type": dev_type,
            "transport": tran.upper(),
            "is_ssd": is_ssd,
            "media_type": media_name,
            "partitions": [],
        }

        # Process partitions
        children = dev.get("children", [])
        for ch in children:
            mp = ch.get("mountpoint")
            part_size = int(ch.get("size") or 0)
            label = ch.get("label") or ""
            usage = get_mount_usage(mp) if mp else None

            is_en = get_current_lang() == "en"
            part_name = ch.get("name", "")
            if mp == "/":
                friendly_desc = "Primary System Root (/)" if is_en else "Основной системный раздел (Корень /)"
            elif mp == "/home":
                friendly_desc = "User Home Directory (/home)" if is_en else "Пользовательские данные (/home)"
            elif mp == "/boot/efi":
                friendly_desc = "EFI Bootloader" if is_en else "Загрузчик EFI"
            elif label:
                unm = "Not mounted" if is_en else "Не смонтирован"
                friendly_desc = f"{label} ({mp or unm})"
            elif mp:
                friendly_desc = f"{'Partition' if is_en else 'Раздел'} {part_name} ({mp})"
            else:
                friendly_desc = f"{'Partition' if is_en else 'Раздел'} {part_name}"

            part_info = {
                "name": part_name,
                "path": ch.get("path") or f"/dev/{part_name}",
                "size": part_size,
                "size_str": format_bytes(part_size),
                "fstype": ch.get("fstype") or "unknown",
                "label": label,
                "mountpoint": mp,
                "friendly_desc": friendly_desc,
                "usage": usage,
            }
            item["partitions"].append(part_info)

        result.append(item)

    return result
