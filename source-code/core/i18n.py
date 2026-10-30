"""Internationalization (i18n) module for Disk Analyzer.
Defaults to English with persistent user selection support (English / Russian).
"""
import os
from core.config import get_setting, set_setting

TRANSLATIONS = {
    "en": {
        "app_title": "Disk Analyzer",
        "app_subtitle": "Storage Drive Monitor • Disk Space • Speed Benchmark",
        "tab_smart": "Drives & S.M.A.R.T.",
        "tab_usage": "Disk Space Usage",
        "tab_bench": "Speed Benchmark",
        "tab_map": "Block Map & Sector Verify",
        "tab_settings": "Settings",
        
        # Drives tab
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
        
        # Usage tab
        "usage_title": "Disk Space Breakdown",
        "btn_back": "Back",
        "btn_up": "Up",
        "partition": "Partition:",
        "path": "Path:",
        "btn_scan": "Analyze Space",
        "btn_stop": "Stop",
        "used": "Used",
        "free": "Free",
        "total": "Total",
        "btn_open_folder": "Open in File Manager",
        "btn_refresh": "Refresh",
        "col_name": "Name",
        "col_size": "Size",
        "col_percent": "% of Parent",
        "col_items": "Items",
        "scan_status_idle": "Select a partition and press 'Analyze Space'",
        "scan_status_scanning": "Scanning folders and files...",
        "scan_status_done": "Scan completed successfully",

        # Benchmark tab
        "bench_target": "Target Partition:",
        "bench_size": "Test Block Size:",
        "btn_start_bench": "Start Speed Test",
        "btn_cancel_bench": "Cancel Test",
        "bench_seq_read": "Sequential Read (SEQ 1M)",
        "bench_seq_read_sub": "Game loading, video editing, large file transfers",
        "bench_seq_write": "Sequential Write (SEQ 1M)",
        "bench_seq_write_sub": "Copying movies, game installs, big backups",
        "bench_rnd_read": "Random System Response (4K RND)",
        "bench_rnd_read_sub": "Desktop responsiveness, UI fluidity, app launching",
        "bench_rnd_write": "Random Small Blocks Write (4K RND)",
        "bench_rnd_write_sub": "System logs, browser cache, background services",
        "bench_history": "Benchmark History",

        # Map tab
        "mode_treemap": "Disk Space Treemap",
        "mode_surface": "Sector Surface Verification",
        "sec_fast": "< 5 ms (Fast):",
        "sec_norm": "< 25 ms (Normal):",
        "sec_slow": "< 100 ms (Slow):",
        "sec_vslow": "< 500 ms (Very Slow):",
        "sec_bad": "Errors / Bad Blocks:",
        "tested": "Verified:",
        "btn_start_scan": "Start Scan",
        "btn_deep_scan": "Deep Analysis",
        "scan_surface_target": "Storage Drive:",

        # Settings tab
        "settings_title": "Application Preferences",
        "settings_lang_label": "Application Language:",
        "settings_lang_desc": "Choose between English and Russian.",
        "settings_bench_label": "Default Benchmark Test Size:",
        "settings_bench_desc": "Preset size of temporary file generated for speed benchmark.",
        "settings_adv_label": "Expert S.M.A.R.T. Mode on startup:",
        "settings_adv_desc": "Show low-level kernel I/O queue and NVMe controller telemetry by default.",
        "settings_restart_note": "Language changes apply immediately.",
        "settings_about_title": "About Disk Analyzer",
        "settings_about_desc": "Modern GTK3 storage utility for Linux. Deeply integrated with Mint-Y theme. Developed with AI assistance (Antigravity).",
        "settings_save_btn": "Save & Apply",
    },
    "ru": {
        "app_title": "Disk Analyzer",
        "app_subtitle": "Мониторинг накопителей • Анализ памяти • Скорость диска",
        "tab_smart": "Накопители & S.M.A.R.T.",
        "tab_usage": "Анализ занятого места",
        "tab_bench": "Тест скорости (Benchmark)",
        "tab_map": "Карта блоков & Проверка",
        "tab_settings": "Настройки",

        # Drives tab
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

        # Usage tab
        "usage_title": "Распределение занятого места",
        "btn_back": "Назад",
        "btn_up": "Вверх",
        "partition": "Раздел:",
        "path": "Путь:",
        "btn_scan": "Анализ места",
        "btn_stop": "Остановить",
        "used": "Занято",
        "free": "Свободно",
        "total": "Всего",
        "btn_open_folder": "Открыть в диспетчере файлов",
        "btn_refresh": "Обновить",
        "col_name": "Имя",
        "col_size": "Размер",
        "col_percent": "% от родителя",
        "col_items": "Элементов",
        "scan_status_idle": "Выберите раздел и нажмите «Анализ места»",
        "scan_status_scanning": "Сканирование файлов и каталогов...",
        "scan_status_done": "Сканирование успешно завершено",

        # Benchmark tab
        "bench_target": "Тестируемый раздел:",
        "bench_size": "Объем файла теста:",
        "btn_start_bench": "Запустить тест скорости",
        "btn_cancel_bench": "Отменить тест",
        "bench_seq_read": "Чтение больших файлов (SEQ 1M)",
        "bench_seq_read_sub": "Запуск игр, загрузка видеомонтажа и открытие больших баз данных",
        "bench_seq_write": "Запись больших файлов (SEQ 1M)",
        "bench_seq_write_sub": "Копирование фильмов, игр, установщиков и тяжелых архивов",
        "bench_rnd_read": "Случайный отклик системы (4K RND)",
        "bench_rnd_read_sub": "Главный параметр отзывчивости рабочего стола, меню и открытия программ",
        "bench_rnd_write": "Случайная запись мелких блоков (4K RND)",
        "bench_rnd_write_sub": "Запись логов, кэша браузера, фоновых сервисов и обновлений ОС",
        "bench_history": "История тестирования",

        # Map tab
        "mode_treemap": "Карта занятого места",
        "mode_surface": "Проверка секторов (Блоки)",
        "sec_fast": "< 5 мс (Отлично):",
        "sec_norm": "< 25 мс (Нормально):",
        "sec_slow": "< 100 мс (Внимание):",
        "sec_vslow": "< 500 мс (Медленно):",
        "sec_bad": "Ошибки / Бэды:",
        "tested": "Проверено:",
        "btn_start_scan": "Сканировать",
        "btn_deep_scan": "Глубокий анализ",
        "scan_surface_target": "Накопитель:",

        # Settings tab
        "settings_title": "Настройки программы",
        "settings_lang_label": "Язык интерфейса:",
        "settings_lang_desc": "Выберите язык: Английский (English) или Русский.",
        "settings_bench_label": "Размер тестового файла по умолчанию:",
        "settings_bench_desc": "Предустановленный объем для тестов скорости накопителя.",
        "settings_adv_label": "Включать режим мастера при старте:",
        "settings_adv_desc": "Отображать низкоуровневую телеметрию ядра и NVMe по умолчанию.",
        "settings_restart_note": "Язык сохраняется в конфигурации (~/.config/disk-analyzer).",
        "settings_about_title": "О программе Disk Analyzer",
        "settings_about_desc": "Нативная утилита мониторинга дисков на GTK3 под Linux Mint. Разработано с помощью ИИ (Antigravity).",
        "settings_save_btn": "Применить",
    }
}


def get_current_lang() -> str:
    """Default language is English unless user changed it in settings."""
    saved_lang = get_setting("language", "en")
    if saved_lang in TRANSLATIONS:
        return saved_lang
    return "en"


CURRENT_LANG = get_current_lang()


def set_current_lang(lang: str):
    """Change language and persist to disk."""
    global CURRENT_LANG
    if lang in TRANSLATIONS:
        CURRENT_LANG = lang
        set_setting("language", lang)


def t(key: str, default: str = "") -> str:
    """Translate key based on currently chosen language (defaults to English)."""
    lang_dict = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["en"])
    if key in lang_dict:
        return lang_dict[key]
    # Fallback to English dict if missing in current
    if key in TRANSLATIONS["en"]:
        return TRANSLATIONS["en"][key]
    return default or key
