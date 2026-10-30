"""Internationalization (i18n) module for Disk Analyzer.
Full dictionary for English (default) and Russian.
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
        "health_good": "Good",
        "health_warn": "Warning",
        "health_bad": "Bad / Error",
        "nvme_fast": "NVMe SSD (High-Speed)",
        "sata_ssd": "SATA SSD Drive",
        "hdd_disk": "HDD Hard Drive",
        "main_nvme": "Primary Storage (NVMe)",
        "sys_drive": "System Storage",
        "hours_label": "hours",
        "days_label": "d.",
        "power_cycles_label": "power cycles",
        "shutdowns_label": "power-cut shutdowns",
        "no_errors": "No errors detected",
        "errors_count": "errors",
        "log_clean": "0 (Log is clean)",
        "log_entries": "entries",
        "spare_available": "available spare memory",
        "wear_out": "flash wear-out",
        "temp_normal": "Operating thermal range",
        "norm_ok": "Normal (0)",
        "all_passed": "Healthy (All tests passed)",
        "warn_wear": "Flash wear / Spare exhausted",

        # SMART attribute names
        "attr_01": "Overall Hardware Self-Test Status",
        "attr_02": "Drive Temperature (Controller / Flash)",
        "attr_03": "Total Power-On Hours",
        "attr_04": "Critical Controller Warnings",
        "attr_05": "Available Spare Memory Cells",
        "attr_06": "Flash Wear Percentage (Percentage Used)",
        "attr_07": "Total Lifetime Data Read (Host Reads)",
        "attr_08": "Total Lifetime Data Written (Host Writes)",
        "attr_09": "Power Cycle Count",
        "attr_10": "Unsafe Shutdowns (Power Cuts)",
        "attr_11": "Media and Data Integrity Errors",
        "attr_12": "Controller Error Log Entries",
        "attr_13": "Drive Firmware Revision",
        "attr_14": "Global Device Identifier (WWID / EUI)",

        # Advanced NVMe / Kernel attributes
        "adv_nvme_rev": "NVMe Express Specification Revision",
        "adv_nvme_state": "NVMe Controller State",
        "adv_nvme_cid": "Controller Hardware ID",
        "adv_nvme_sanitize": "Flash Sanitize Status",
        "adv_nvme_selftest": "Last Background Self-Test Result",
        "adv_io_reads": "Completed Read Operations (Read I/O Ops)",
        "adv_io_writes": "Completed Write Operations (Write I/O Ops)",
        "adv_io_merged_r": "Merged Read Requests",
        "adv_io_merged_w": "Merged Write Requests",
        "adv_io_inflight": "Active In-Flight Requests",
        "adv_io_time": "Total Active Disk I/O Time",

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
        "tree_title": "Drive Explorer (Tree Structure)",
        "col_name": "Name",
        "col_size": "Size",
        "col_type": "Type",
        "col_percent": "% of Parent",
        "col_items": "Items",
        "col_path": "Full Path",
        "scan_status_idle": "Use arrow ▶ to expand directories or double click to enter.",
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
        "mode_surface": "Sector Surface Verification (Blocks)",
        "status_blocks": "Block Status",
        "sec_fast": "< 5 ms (Fast):",
        "sec_norm": "< 25 ms (Normal):",
        "sec_slow": "< 100 ms (Attention):",
        "sec_vslow": "< 500 ms (Slow):",
        "sec_bad": "Errors / Bad Blocks:",
        "tested": "Verified:",
        "btn_start_scan": "Start Scan",
        "btn_deep_scan": "Deep Analysis",
        "scan_surface_target": "Storage Drive:",
        "map_status_ready": "Select mode and target, then click Start to begin scanning.",

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
        "health_good": "Хорошо",
        "health_warn": "Внимание",
        "health_bad": "Ошибка",
        "nvme_fast": "NVMe SSD (Скоростной)",
        "sata_ssd": "SSD диск (SATA)",
        "hdd_disk": "HDD диск (Магнитный)",
        "main_nvme": "Основной накопитель (NVMe)",
        "sys_drive": "Системный накопитель",
        "hours_label": "часов",
        "days_label": "дн.",
        "power_cycles_label": "включений",
        "shutdowns_label": "аварийных отключений",
        "no_errors": "Ошибок не обнаружено",
        "errors_count": "ошибок",
        "log_clean": "0 (Журнал чист)",
        "log_entries": "записей",
        "spare_available": "резервных блоков доступно",
        "wear_out": "износа ресурса памяти",
        "temp_normal": "Рабочий тепловой диапазон",
        "norm_ok": "В норме (0)",
        "all_passed": "Исправен (Все тесты пройдены)",
        "warn_wear": "Износ ячеек памяти",

        # SMART attribute names
        "attr_01": "Общий статус аппаратной самодиагностики",
        "attr_02": "Температура накопителя (Контроллер/Память)",
        "attr_03": "Общая наработка во включенном состоянии",
        "attr_04": "Критические предупреждения контроллера",
        "attr_05": "Доступный резерв ячеек памяти (Available Spare)",
        "attr_06": "Процент износа ресурса ячеек (Percentage Used)",
        "attr_07": "Всего прочитано данных за историю накопителя",
        "attr_08": "Всего записано данных за историю накопителя (Host Writes)",
        "attr_09": "Количество циклов включения питания (Power Cycles)",
        "attr_10": "Небезопасные отключения питания (Unsafe Shutdowns)",
        "attr_11": "Ошибки целостности данных памяти (Media Errors)",
        "attr_12": "Записи журнала ошибок контроллера (Error Log Entries)",
        "attr_13": "Версия микропрограммы накопителя (Firmware)",
        "attr_14": "Глобальный аппаратный идентификатор WWID / EUI",

        # Advanced NVMe / Kernel attributes
        "adv_nvme_rev": "Ревизия спецификации NVMe Express",
        "adv_nvme_state": "Состояние контроллера NVMe (State)",
        "adv_nvme_cid": "Идентификатор контроллера (Controller ID)",
        "adv_nvme_sanitize": "Статус очистки накопителя (Sanitize Status)",
        "adv_nvme_selftest": "Результат последнего фонового Selftest",
        "adv_io_reads": "Выполненные операции чтения (Read I/O Ops)",
        "adv_io_writes": "Выполненные операции записи (Write I/O Ops)",
        "adv_io_merged_r": "Объединенные запросы чтения (Merged Read Requests)",
        "adv_io_merged_w": "Объединенные запросы записи (Merged Write Requests)",
        "adv_io_inflight": "Запросов в обработке прямо сейчас (In-flight I/O)",
        "adv_io_time": "Общее активное время дискового ввода-вывода",

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
        "tree_title": "Проводник накопителя (Древовидная структура)",
        "col_name": "Имя",
        "col_size": "Размер",
        "col_type": "Тип",
        "col_percent": "% от родителя",
        "col_items": "Элементов",
        "col_path": "Полный путь",
        "scan_status_idle": "Используйте стрелочки ▶ для раскрытия папок на месте или дважды кликните по папке.",
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
        "status_blocks": "Статус блоков",
        "sec_fast": "< 5 мс (Отлично):",
        "sec_norm": "< 25 мс (Нормально):",
        "sec_slow": "< 100 мс (Внимание):",
        "sec_vslow": "< 500 мс (Медленно):",
        "sec_bad": "Ошибки / Бэды:",
        "tested": "Проверено:",
        "btn_start_scan": "Сканировать",
        "btn_deep_scan": "Глубокий анализ",
        "scan_surface_target": "Накопитель:",
        "map_status_ready": "Выберите режим и нажмите кнопку для запуска сканирования.",

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
    if key in TRANSLATIONS["en"]:
        return TRANSLATIONS["en"][key]
    return default or key
