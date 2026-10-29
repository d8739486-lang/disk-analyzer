"""Internationalization (i18n) module for Disk Analyzer supporting Russian, English, and system locale."""
import os
import locale

TRANSLATIONS = {
    "ru": {
        "app_title": "Disk Analyzer",
        "app_subtitle": "Мониторинг накопителей • Анализ памяти • Скорость диска",
        "tab_smart": "Накопители & S.M.A.R.T.",
        "tab_usage": "Анализ занятого места",
        "tab_bench": "Тест скорости (Benchmark)",
        "tab_map": "Карта блоков & Проверка",
        "drives_title": "Физические накопители",
        "drive_col_name": "Накопитель",
        "drive_col_size": "Ёмкость",
        "adv_mode": "Режим мастера (Advanced):",
        "btn_refresh_drives": "Обновить список дисков",
        "card_health": "Состояние накопителя",
        "card_temp": "Температура",
        "card_interface": "Интерфейс",
        "card_uptime": "Время работы / S/N",
        "smart_table_title": "Параметры надёжности и S.M.A.R.T.",
        "smart_col_num": "№",
        "smart_col_param": "Параметр самодиагностики / Телеметрия",
        "smart_col_curr": "Текущее",
        "smart_col_worst": "Худшее",
        "smart_col_thresh": "Порог",
        "smart_col_val": "Значение / Статус",
        "sec_fast": "< 5 мс (Отлично):",
        "sec_norm": "< 25 мс (Нормально):",
        "sec_slow": "< 100 мс (Внимание):",
        "sec_vslow": "< 500 мс (Медленно):",
        "sec_bad": "Ошибки / Бэды:",
        "tested": "Проверено:",
        "btn_start_scan": "Сканировать",
        "btn_stop": "Остановить",
        "btn_start_bench": "Запустить тест скорости",
        "btn_deep_scan": "Глубокий анализ",
        "btn_cancel": "Остановить",
        "bench_target": "Тестируемый раздел:",
        "bench_size": "Объем файла теста:",
        "mode_treemap": "Карта занятого места",
        "mode_surface": "Проверка секторов (Поверхность)",
        "used": "Занято",
        "free": "Свободно",
        "total": "Всего",
    },
    "en": {
        "app_title": "Disk Analyzer",
        "app_subtitle": "Storage Drive Monitor • Disk Space • Speed Benchmark",
        "tab_smart": "Drives & S.M.A.R.T.",
        "tab_usage": "Disk Space Usage",
        "tab_bench": "Speed Benchmark",
        "tab_map": "Block Map & Sector Verify",
        "drives_title": "Physical Storage Drives",
        "drive_col_name": "Drive",
        "drive_col_size": "Capacity",
        "adv_mode": "Expert Mode (Advanced):",
        "btn_refresh_drives": "Refresh Drive List",
        "card_health": "Drive Health",
        "card_temp": "Temperature",
        "card_interface": "Interface",
        "card_uptime": "Power-On Hours / S/N",
        "smart_table_title": "Reliability & S.M.A.R.T. Telemetry",
        "smart_col_num": "#",
        "smart_col_param": "Diagnostic Attribute / Telemetry",
        "smart_col_curr": "Current",
        "smart_col_worst": "Worst",
        "smart_col_thresh": "Thresh",
        "smart_col_val": "Raw Value / Status",
        "sec_fast": "< 5 ms (Fast):",
        "sec_norm": "< 25 ms (Normal):",
        "sec_slow": "< 100 ms (Slow):",
        "sec_vslow": "< 500 ms (Very Slow):",
        "sec_bad": "Errors / Bad Blocks:",
        "tested": "Verified:",
        "btn_start_scan": "Start Scan",
        "btn_stop": "Stop",
        "btn_start_bench": "Start Speed Test",
        "btn_deep_scan": "Deep Analysis",
        "btn_cancel": "Cancel",
        "bench_target": "Target Partition:",
        "bench_size": "Test Block Size:",
        "mode_treemap": "Disk Space Treemap",
        "mode_surface": "Sector Surface Verification",
        "used": "Used",
        "free": "Free",
        "total": "Total",
    }
}


def get_current_lang() -> str:
    """Determine language from system environment (LANG, LC_MESSAGES)."""
    lang_env = os.environ.get("LANG", "") or os.environ.get("LC_MESSAGES", "")
    if lang_env.lower().startswith("ru") or lang_env.lower().startswith("be") or lang_env.lower().startswith("uk"):
        return "ru"
    return "en"


CURRENT_LANG = get_current_lang()


def t(key: str, default: str = "") -> str:
    """Translate key based on system language."""
    lang_dict = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["en"])
    return lang_dict.get(key, TRANSLATIONS["en"].get(key, default or key))

