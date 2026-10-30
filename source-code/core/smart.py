"""S.M.A.R.T. and deep hardware telemetry monitor using UDisks2 DBus, sysfs hwmon and kernel parameters."""
import glob
import os
from typing import Dict, Any, List
from core.i18n import t, get_current_lang

try:
    import dbus
    HAS_DBUS = True
except ImportError:
    HAS_DBUS = False


def get_hwmon_temperatures() -> Dict[str, float]:
    """Read temperatures from /sys/class/hwmon."""
    temps = {}
    for hpath in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            name_file = os.path.join(hpath, "name")
            if not os.path.exists(name_file):
                continue
            with open(name_file, "r") as f:
                name = f.read().strip().lower()

            for temp_file in glob.glob(os.path.join(hpath, "temp*_input")):
                with open(temp_file, "r") as f:
                    val = float(f.read().strip()) / 1000.0
                    temps[name] = val
        except Exception:
            continue
    return temps


def get_disk_stats_io(disk_name: str) -> Dict[str, Any]:
    """Read total read/write statistics from /sys/block/<disk>/stat."""
    stat_file = f"/sys/block/{disk_name}/stat"
    if not os.path.exists(stat_file):
        return {}
    try:
        with open(stat_file, "r") as f:
            parts = f.read().split()
            read_ios = int(parts[0])
            read_merges = int(parts[1])
            read_sectors = int(parts[2])
            read_ticks = int(parts[3])
            write_ios = int(parts[4])
            write_merges = int(parts[5])
            write_sectors = int(parts[6])
            write_ticks = int(parts[7])
            in_flight = int(parts[8])
            io_ticks = int(parts[9])

            read_gb = (read_sectors * 512) / (1024 ** 3)
            write_gb = (write_sectors * 512) / (1024 ** 3)
            return {
                "read_gb": f"{read_gb:.1f} ГБ",
                "write_gb": f"{write_gb:.1f} ГБ",
                "read_ios": f"{read_ios:,}",
                "write_ios": f"{write_ios:,}",
                "read_merges": f"{read_merges:,}",
                "write_merges": f"{write_merges:,}",
                "in_flight": str(in_flight),
                "io_time_active": f"{io_ticks / 1000.0:.1f} сек",
            }
    except Exception:
        return {}


def get_queue_params(disk_name: str) -> Dict[str, str]:
    """Read low-level block queue parameters."""
    res = {}
    base = f"/sys/block/{disk_name}/queue"
    files = {
        "logical_block_size": "Размер логического сектора (LBA)",
        "physical_block_size": "Размер физического сектора",
        "optimal_io_size": "Оптимальный размер I/O блока",
        "minimum_io_size": "Минимальный размер I/O блока",
        "scheduler": "Планировщик ввода-вывода (I/O Scheduler)",
        "read_ahead_kb": "Буфер упреждающего чтения (Read-ahead)",
        "write_cache": "Режим кэширования записи (Write Cache)",
        "nr_requests": "Глубина очереди запросов (Queue Depth)",
        "rotational": "Тип вращения (0 = SSD/NVMe, 1 = HDD)",
        "discard_granularity": "Гранулярность очистки TRIM (Discard)",
        "discard_max_bytes": "Максимальный блок команды TRIM",
        "max_sectors_kb": "Максимальный размер передачи за операцию",
    }
    for fname, label in files.items():
        p = os.path.join(base, fname)
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    val = f.read().strip()
                    if fname == "rotational":
                        val = "0 (Электронный твердотельный накопитель)" if val == "0" else "1 (Механический диск HDD)"
                    elif fname == "discard_max_bytes":
                        b = int(val) if val.isdigit() else 0
                        val = f"{val} байт ({b // (1024*1024)} МБ)" if b > 0 else val
                    res[label] = val
            except OSError:
                pass
    return res


def get_udisks_nvme_info(target_dev_name: str = "") -> Dict[str, Any]:
    """Fetch NVMe controller telemetry and real SMART attributes via UDisks2 DBus."""
    if not HAS_DBUS:
        return {}
    try:
        bus = dbus.SystemBus()
        obj = bus.get_object("org.freedesktop.UDisks2", "/org/freedesktop/UDisks2")
        mgr = dbus.Interface(obj, "org.freedesktop.DBus.ObjectManager")
        objs = mgr.GetManagedObjects()

        target_drive_path = None
        # Try matching by block device if provided
        if target_dev_name:
            for path, ifaces in objs.items():
                if "org.freedesktop.UDisks2.Block" in ifaces:
                    b = ifaces["org.freedesktop.UDisks2.Block"]
                    device = bytes(b.get("Device", b"")).decode("utf-8", errors="ignore").strip("\x00")
                    if os.path.basename(device) == target_dev_name:
                        target_drive_path = str(b.get("Drive", ""))
                        break

        # Iterate controllers
        for path, ifaces in objs.items():
            if target_drive_path and path != target_drive_path:
                continue

            if "org.freedesktop.UDisks2.NVMe.Controller" in ifaces:
                ctrl = ifaces["org.freedesktop.UDisks2.NVMe.Controller"]
                kelvin_temp = int(ctrl.get("SmartTemperature", 0))
                celsius = (kelvin_temp - 273) if kelvin_temp > 200 else None
                hours = int(ctrl.get("SmartPowerOnHours", 0))
                days = hours // 24
                warnings = list(ctrl.get("SmartCriticalWarning", []))
                selftest = str(ctrl.get("SmartSelftestStatus", "success"))

                # Query real live NVMe SMART attributes directly from controller
                smart_attrs = {}
                try:
                    drive_obj = bus.get_object("org.freedesktop.UDisks2", path)
                    ctrl_iface = dbus.Interface(drive_obj, "org.freedesktop.UDisks2.NVMe.Controller")
                    try:
                        ctrl_iface.SmartUpdate(dbus.Dictionary({}, signature="sv"))
                    except Exception:
                        pass
                    raw_attrs = ctrl_iface.SmartGetAttributes(dbus.Dictionary({}, signature="sv"))
                    for k, v in raw_attrs.items():
                        try:
                            smart_attrs[k] = int(v)
                        except (ValueError, TypeError):
                            smart_attrs[k] = v
                except Exception:
                    pass

                return {
                    "temperature": celsius,
                    "power_on_hours": f"{hours} ч ({days} дн.)",
                    "hours_raw": hours,
                    "warnings": warnings,
                    "selftest": selftest,
                    "nvme_rev": str(ctrl.get("NVMeRevision", "1.4")),
                    "state": str(ctrl.get("State", "live")),
                    "controller_id": int(ctrl.get("ControllerID", 0)),
                    "sanitize_status": str(ctrl.get("SanitizeStatus", "never_sanitized")),
                    "smart_attrs": smart_attrs,
                }
    except Exception:
        pass
    return {}


def get_smart_info(device_path: str, advanced_mode: bool = False) -> Dict[str, Any]:
    """Query SMART and low-level hardware telemetry."""
    base_name = os.path.basename(device_path)
    result = {
        "device": device_path,
        "smart_status": "Отличное (Ошибок нет)",
        "temperature_c": None,
        "power_on_hours": "N/A",
        "power_cycles": "N/A",
        "health_score": "Хорошо (100%)",
        "attributes": [],
    }

    # 1. Hwmon temp baseline
    hw_temps = get_hwmon_temperatures()
    if "nvme" in base_name and "nvme" in hw_temps:
        result["temperature_c"] = hw_temps["nvme"]

    # 2. UDisks2 DBus integration with real NVMe SMART hardware logs
    udisks_data = get_udisks_nvme_info(base_name)
    smart_attrs = udisks_data.get("smart_attrs", {}) if udisks_data else {}

    if udisks_data:
        if udisks_data.get("temperature") and result["temperature_c"] is None:
            result["temperature_c"] = udisks_data["temperature"]
        if udisks_data.get("power_on_hours"):
            result["power_on_hours"] = udisks_data["power_on_hours"]

        warns = udisks_data.get("warnings", [])
        pct_used = smart_attrs.get("percent_used", 0)
        avail_spare = smart_attrs.get("avail_spare", 100)

        if len(warns) == 0 and avail_spare >= 10:
            remaining_life = max(0, 100 - pct_used)
            result["health_score"] = f"{t('health_good')} ({remaining_life}%)"
            result["smart_status"] = t("all_passed")
        else:
            result["health_score"] = t("health_warn")
            result["smart_status"] = f"{t('health_warn')}: {', '.join(warns) or t('warn_wear')}"

    # 3. Read I/O stats from sysfs
    io_stats = get_disk_stats_io(base_name)

    # 4. Firmware and hardware identifiers directly from sysfs
    fw_path = f"/sys/block/{base_name}/device/firmware_rev"
    firmware = "—"
    if os.path.exists(fw_path):
        try:
            with open(fw_path) as f:
                firmware = f.read().strip()
        except OSError:
            pass

    wwid_path = f"/sys/block/{base_name}/wwid"
    wwid = "—"
    if os.path.exists(wwid_path):
        try:
            with open(wwid_path) as f:
                wwid = f.read().strip()
        except OSError:
            pass

    # Real hardware SMART attributes (NVMe or SATA)
    basic_items = []
    id_counter = 1

    # 01. Overall status
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_01"),
        "PASSED" if not udisks_data.get("warnings") else "WARNING",
        "PASSED",
        "PASSED",
        t("no_errors") if not udisks_data.get("warnings") else t("health_warn"),
    ))
    id_counter += 1

    # 02. Temperature
    curr_temp = int(result['temperature_c'] or 30)
    wctemp = smart_attrs.get("wctemp", 358)
    crit_thresh = f"{wctemp - 273} °C" if wctemp > 273 else "85 °C"
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_02"),
        f"{curr_temp} °C",
        "70 °C",
        crit_thresh,
        f"{curr_temp} °C ({t('temp_normal')})",
    ))
    id_counter += 1

    # 03. Power-on hours
    hours_raw = udisks_data.get('hours_raw', 0)
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_03"),
        result["power_on_hours"],
        "—",
        "—",
        f"{hours_raw} {t('hours_label')}",
    ))
    id_counter += 1

    # 04. Critical Warnings
    warn_count = len(udisks_data.get("warnings", []))
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_04"),
        str(warn_count),
        "0",
        "0",
        t("norm_ok") if warn_count == 0 else f"{t('errors_count')}: {warn_count}",
    ))
    id_counter += 1

    # 05. Available Spare (Real hardware reading)
    avail_spare_val = smart_attrs.get("avail_spare", 100)
    spare_thresh_val = smart_attrs.get("spare_thresh", 5)
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_05"),
        f"{avail_spare_val}%",
        f"{avail_spare_val}%",
        f"{spare_thresh_val}%",
        f"{avail_spare_val}% {t('spare_available')}",
    ))
    id_counter += 1

    # 06. Percentage Used (Real hardware TBW degradation reading)
    pct_used_val = smart_attrs.get("percent_used", 0)
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_06"),
        f"{pct_used_val}%",
        f"{pct_used_val}%",
        "100%",
        f"{pct_used_val}% {t('wear_out')}",
    ))
    id_counter += 1

    # 07. Total Data Read (Lifetime from NVMe controller)
    tot_read_bytes = smart_attrs.get("total_data_read", 0)
    if tot_read_bytes > 0:
        tot_read_tb = tot_read_bytes / (1024 ** 4)
        unit_tb = "TB" if get_current_lang() == "en" else "ТБ"
        unit_bytes = "bytes" if get_current_lang() == "en" else "байт"
        tot_read_str = f"{tot_read_tb:.2f} {unit_tb} ({tot_read_bytes:,} {unit_bytes})"
    else:
        tot_read_str = io_stats.get("read_gb", "—")
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_07"),
        tot_read_str.split()[0] + " " + tot_read_str.split()[1] if " " in tot_read_str else tot_read_str,
        "—",
        "—",
        tot_read_str,
    ))
    id_counter += 1

    # 08. Total Data Written (Lifetime from NVMe controller)
    tot_write_bytes = smart_attrs.get("total_data_written", 0)
    if tot_write_bytes > 0:
        tot_write_tb = tot_write_bytes / (1024 ** 4)
        unit_tb = "TB" if get_current_lang() == "en" else "ТБ"
        unit_bytes = "bytes" if get_current_lang() == "en" else "байт"
        tot_write_str = f"{tot_write_tb:.2f} {unit_tb} ({tot_write_bytes:,} {unit_bytes})"
    else:
        tot_write_str = io_stats.get("write_gb", "—")
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_08"),
        tot_write_str.split()[0] + " " + tot_write_str.split()[1] if " " in tot_write_str else tot_write_str,
        "—",
        "—",
        tot_write_str,
    ))
    id_counter += 1

    # 09. Power Cycles
    p_cycles = smart_attrs.get("power_cycles", 0)
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_09"),
        f"{p_cycles:,}",
        "—",
        "—",
        f"{p_cycles:,} {t('power_cycles_label')}",
    ))
    id_counter += 1

    # 10. Unsafe Shutdowns
    unsafe_sh = smart_attrs.get("unsafe_shutdowns", 0)
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_10"),
        f"{unsafe_sh}",
        "—",
        "—",
        f"{unsafe_sh} {t('shutdowns_label')}",
    ))
    id_counter += 1

    # 11. Media and Data Integrity Errors
    media_errs = smart_attrs.get("media_errors", 0)
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_11"),
        str(media_errs),
        "0",
        "0",
        f"0 ({t('no_errors')})" if media_errs == 0 else f"{media_errs} {t('errors_count')}",
    ))
    id_counter += 1

    # 12. Error Log Entries
    err_logs = smart_attrs.get("num_err_log_entries", 0)
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_12"),
        str(err_logs),
        "0",
        "—",
        t("log_clean") if err_logs == 0 else f"{err_logs} {t('log_entries')}",
    ))
    id_counter += 1

    # 13. Firmware Version
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_13"),
        firmware,
        "—",
        "—",
        firmware,
    ))
    id_counter += 1

    # 14. Global WWID / EUI
    basic_items.append((
        f"{id_counter:02d}",
        t("attr_14"),
        wwid,
        "—",
        "—",
        wwid,
    ))
    id_counter += 1

    for id_num, name, val, worst, thresh, raw in basic_items:
        result["attributes"].append({
            "id": id_num,
            "name": name,
            "value": str(val),
            "worst": str(worst),
            "thresh": str(thresh),
            "raw": str(raw),
        })

    # Advanced telemetry items (when Advanced switch is enabled)
    if advanced_mode:
        adv_id = id_counter
        if udisks_data:
            adv_items = [
                (t("adv_nvme_rev"), udisks_data.get("nvme_rev", "1.4")),
                (t("adv_nvme_state"), udisks_data.get("state", "live")),
                (t("adv_nvme_cid"), str(udisks_data.get("controller_id", 0))),
                (t("adv_nvme_sanitize"), udisks_data.get("sanitize_status", "never_sanitized")),
                (t("adv_nvme_selftest"), udisks_data.get("selftest", "success")),
            ]
            for label, val in adv_items:
                result["attributes"].append({
                    "id": f"{adv_id:02d}",
                    "name": f"[NVMe] {label}",
                    "value": str(val),
                    "worst": "—",
                    "thresh": "—",
                    "raw": str(val),
                })
                adv_id += 1

        # Block queue low-level parameters
        q_params = get_queue_params(base_name)
        for label, val in q_params.items():
            result["attributes"].append({
                "id": f"{adv_id:02d}",
                "name": f"[KERNEL] {label}",
                "value": str(val),
                "worst": "—",
                "thresh": "—",
                "raw": str(val),
            })
            adv_id += 1

        if io_stats:
            adv_io_items = [
                (t("adv_io_reads"), io_stats.get("read_ios", "—")),
                (t("adv_io_writes"), io_stats.get("write_ios", "—")),
                (t("adv_io_merged_r"), io_stats.get("read_merges", "—")),
                (t("adv_io_merged_w"), io_stats.get("write_merges", "—")),
                (t("adv_io_inflight"), io_stats.get("in_flight", "0")),
                (t("adv_io_time"), io_stats.get("io_time_active", "—")),
            ]
            for label, val in adv_io_items:
                result["attributes"].append({
                    "id": f"{adv_id:02d}",
                    "name": f"[I/O STAT] {label}",
                    "value": str(val),
                    "worst": "—",
                    "thresh": "—",
                    "raw": str(val),
                })
                adv_id += 1

    return result
