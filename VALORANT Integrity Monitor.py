import time         #Pредоставляет функции для работы с системным временем
import psutil           #ЦП, память, диски, сеть, датчики
import os               #Взаимодействие с ОС
import json             #Работа с JSON файлами
from datetime import datetime           #Работа с датой и временем
from PySide6 import QtWidgets, QtCore    #GUI библиотека


#Константы:

GUI_MODE = True          #Если True - запускается GUI, если False - консольный режим
log_callback = None        #Функция обратного вызова для логов GUI
status_callback = None     #Принимает str: "IDLE" / "RUNNING"
quit_callback = None       #Функция обратного вызова для выхода из GUI
in_session = False          #Внутри сессии Valorant или нет?
session_events = []         #Список событий, что нашли за сессию
seen_keys = set()           #Уникальные ключи процессов (имя + путь), чтобы не логировать дубликаты       
known_processes = set()     #Известные PIDы процессов на данный момент
printed_session_header = False                      #Флаг для печати заголовка сессии только один раз
game_pid = None              #PID процесса игры
cfg_file = "config.json"

default_cfg = {
    "default_gui_width": 1600,
    "default_gui_height": 720,
    "game_process": "VALORANT.exe",
    "scan_interval": 0.8,
    "game_check_interval": 0.2,
    "allowlist_keywords": ["edge"],
    "auto_quit_on_game_close": True,
    "enable_main_log": True,
    "main_log_file": "VGC_EDU_log.txt",
    "sessions_dir": "sessions",
}

def load_config():            #Функция загрузки конфигурации из файла config.json
    cfg = dict(default_cfg)   #Начинаем с дефолтной конфигурации
    try:
        with open(cfg_file, "r", encoding="utf-8", errors="ignore") as f:
            user_cfg = json.load(f)
        if isinstance(user_cfg, dict):
            cfg.update(user_cfg)        #Обновляем конфигурацию значениями из файла
    except FileNotFoundError:
        pass
    except Exception:                   #Битый json или другая ошибка — просто используем дефолты
        pass

    try:
        cfg["scan_interval"] = float(cfg.get("scan_interval", default_cfg["scan_interval"]))
        cfg["game_check_interval"] = float(cfg.get("game_check_interval", default_cfg["game_check_interval"]))
    except Exception:
        cfg["scan_interval"] = default_cfg["scan_interval"]
        cfg["game_check_interval"] = default_cfg["game_check_interval"] 

    if cfg["scan_interval"] < 0.1:
        cfg["scan_interval"] = default_cfg["scan_interval"]
    if cfg["game_check_interval"] < 0.01:
        cfg["game_check_interval"] = default_cfg["game_check_interval"] 

    akw = cfg.get("allowlist_keywords", default_cfg["allowlist_keywords"])
    if not isinstance(akw, list):
        akw = default_cfg["allowlist_keywords"]
    cfg["allowlist_keywords"] = [str(x) for x in akw if str(x).strip()]

    cfg["auto_quit_on_game_close"] = bool(cfg.get("auto_quit_on_game_close", True))
    cfg["enable_main_log"] = bool(cfg.get("enable_main_log", True))

    cfg["game_process"] = str(cfg.get("game_process", default_cfg["game_process"]))
    cfg["main_log_file"] = str(cfg.get("main_log_file", default_cfg["main_log_file"]))
    cfg["sessions_dir"] = str(cfg.get("sessions_dir", default_cfg["sessions_dir"]))

    return cfg

_cfg = load_config()

GAME_PROCESS = _cfg["game_process"]
scan_interval = _cfg["scan_interval"]
game_check_interval = _cfg["game_check_interval"]
ALLOWLIST_KEYWORDS = _cfg["allowlist_keywords"]
auto_quit_on_game_close = _cfg["auto_quit_on_game_close"]
enable_main_log = _cfg["enable_main_log"]
LOG_FILE = _cfg["main_log_file"]
SESSIONS_DIR = _cfg["sessions_dir"]
gui_width = int(_cfg.get("default_gui_width", 1200))
gui_height = int(_cfg.get("default_gui_height", 720))

ALLOWLIST_KEYWORDS = [k.lower() for k in ALLOWLIST_KEYWORDS]

def snapshot_pids() -> set[int]:            #Функция создания снимка текущих PIDов процессов
    return set(psutil.pids())

def is_game_running() -> bool:
    global game_pid                         #Функция проверки запущен ли процесс игры   

    if game_pid is not None:                #Если у нас уже есть PID процесса игры, проверяем его
        try:
            if psutil.pid_exists(game_pid):
                p = psutil.Process(game_pid)
                if (p.name() or "") == GAME_PROCESS:
                    return True
        except Exception:
            pass
        game_pid = None                     #Если процесс не найден, сбрасываем PID

    for p in psutil.process_iter(["name", "pid"]):              #Ищем процесс игры среди всех процессов
        try:
            if p.info.get("name") == GAME_PROCESS:              #Если нашли процесс игры
                game_pid = int(p.info.get("pid"))
                return True
        except Exception:
            pass

    return False

def emit_log(message: str):         #Функция логирования с отметкой времени, запись в файл и прокидка в GUI
    stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    line = f"[{stamp}] {message}"

    print(line)

    #Запись в файл лога
    if enable_main_log:
        try:
            with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as f:
                f.write(line + "\n")
        except Exception:
            pass

    #прокидка в GUI
    if log_callback:
        try:
            log_callback(line)
        except Exception:
            pass

def clear_main_log():            #Функция очистки основного лога при старте
    if not enable_main_log:
        return
    try:
        with open(LOG_FILE, "w", encoding="utf-8", errors="ignore") as f:
            f.write("")
    except Exception:
        pass

def set_status(text: str):        #Функция установки статуса в GUI
    if status_callback:
        try:
            status_callback(text)
        except Exception:
            pass

def save_session_summary(lines: list[str]) -> str:          #Создаем папку sessions/, файл с именем и временем, записываем туда строки summary, возвращаем путь
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{stamp}.txt"
    path = os.path.join(SESSIONS_DIR, filename)

    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write("\n".join(lines) + "\n")
    return path

def monitor_loop(stop_flag):      #Основной цикл мониторинга    
    global in_session, printed_session_header, known_processes
    global session_events, seen_keys
    global game_pid

    clear_main_log()
    emit_log("VALORANT Integrity Monitor started.")
    set_status("IDLE")

    last_full_scan = 0.0            #Время последнего полного сканирования процессов

    while not stop_flag["stop"]:    #Пока не установлен флаг остановки        
        game_running = is_game_running()

        # START
        if game_running and not in_session:
            in_session = True
            printed_session_header = False
            known_processes = snapshot_pids()
            last_full_scan = 0.0
            session_events.clear()
            seen_keys.clear()
            emit_log("VALORANT started")
            set_status("RUNNING")
            time.sleep(game_check_interval)
            continue

        # STOP
        if (not game_running) and in_session:
            in_session = False
            game_pid = None
            unique_events = list(dict.fromkeys(session_events))

            emit_log("VALORANT stopped")
            set_status("IDLE")

            summary_lines = []
            summary_lines.append("VALORANT session stopped")
            summary_lines.append(
                f"Summary: {len(unique_events)} unique process(es) ({len(session_events)} events)"
            )
            summary_lines.append("Processes:")
            for entry in unique_events:
                summary_lines.append(f"- {entry}")

            saved_path = save_session_summary(summary_lines)
            emit_log(f"Session summary saved to: {saved_path}")
            emit_log(f"Summary: {len(unique_events)} unique process(es) ({len(session_events)} events)")
            emit_log("Unique processes:")
            for entry in unique_events:
                emit_log(f"  - {entry}")

            emit_log("-" * 40)
            if auto_quit_on_game_close and quit_callback:
                try:
                    quit_callback(saved_path, "\n".join(summary_lines))
                except Exception:
                    pass
            time.sleep(game_check_interval)
            continue

        # IN SESSION
        if in_session:
            now = time.time()                                           #Текущее время

            if not printed_session_header:                              #Печатаем заголовок сессии только один раз
                emit_log("VALORANT monitor started...")
                emit_log(f"Processes running: {len(known_processes)}")
                printed_session_header = True

            if (now - last_full_scan) >= scan_interval:                 #Если прошло достаточно времени с последнего полного сканирования процессов
                last_full_scan = now

                current = snapshot_pids()                               #Создаем снимок текущих PIDов процессов
                new_pids = current - known_processes                    #Находим новые PIDы, которые появились с последнего сканирования

                for pid in new_pids:                                    #Для каждого нового PIDа
                    try:
                        if pid in (0, 4):
                            continue

                        p = psutil.Process(pid)
                        name = p.name() or ""

                        try:                                            #Получаем путь к исполняемому файлу процесса
                            exe = p.exe()
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            exe = "?"

                        if not name:                                    #Если имя процесса пустое - пропускаем
                            continue

                        exe_low = (exe or "").lower()                   #Проверяем системные процессы Windows и пропускаем их
                        if "\\windows\\system32\\" in exe_low or "\\windows\\syswow64\\" in exe_low:
                            continue

                        low = (name + " " + (exe or "")).lower()        #Проверяем на наличие ключевых слов из белого списка и пропускаем такие процессы
                        if any(k in low for k in ALLOWLIST_KEYWORDS):
                            continue

                        entry = f"{name} | pid={pid} | exe={exe}"       #Формируем строку лога для нового процесса
                        key = (name.lower(), (exe or "").lower())

                        if key in seen_keys:                            #Если такой процесс уже был залогирован - пропускаем
                            continue
                        seen_keys.add(key)

                        emit_log(f"New process while VALORANT running: {entry}")        #Логируем новый процесс
                        session_events.append(entry)

                    except (psutil.NoSuchProcess, psutil.AccessDenied):                 #Если процесс завершился или доступ запрещен - пропускаем
                        pass
                    except Exception:
                        pass

                known_processes = current

            time.sleep(game_check_interval)                             #Ждем перед следующей итерацией



        else:                                                           # NOT IN SESSION
            now = time.time()
            if (now - last_full_scan) >= scan_interval:                 #Если прошло достаточно времени с последнего полного сканирования процессов
                last_full_scan = now
                known_processes = snapshot_pids()
            time.sleep(game_check_interval)

class Dashboard(QtWidgets.QMainWindow):        #GUI класс
    log_signal = QtCore.Signal(str)
    status_signal = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.allow_close = False
        self.resize(gui_width, gui_height)
        self.move(self.screen().availableGeometry().center() - self.rect().center())


        self.base_title = "VALORANT Integrity Monitor"
        self.setWindowTitle(self.base_title)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.document().setMaximumBlockCount(3000)  # Ограничение на 3000 строк
        self.log_signal.connect(self.append_log)
        self.status_signal.connect(self.set_status_ui)
        self.setCentralWidget(self.log_view)

        self.tray = QtWidgets.QSystemTrayIcon(self)
        self.tray.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
        self.tray.setToolTip("VALORANT Integrity Monitor")

        menu = QtWidgets.QMenu()
        act_show = menu.addAction("Show / Hide")
        act_quit = menu.addAction("Quit")

        act_show.triggered.connect(self.toggle_visibility)
        act_quit.triggered.connect(self.quit_app)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

    @QtCore.Slot(str)
    def set_status_ui(self, status: str):
        self.setWindowTitle(f"{self.base_title} - {status}")
        self.tray.setToolTip(f"{self.base_title} - {status}")

    def append_log(self, line: str):
        self.log_view.appendPlainText(line)

    @QtCore.Slot()
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def on_tray_click(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.toggle_visibility()
            
    def quit_app(self):
        emit_log("VALORANT Integrity Monitor stopped by user.")
        self.allow_close = True
        QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        if self.allow_close:
            event.accept()
        else:
            event.ignore()
            self.hide()

class MonitorThread(QtCore.QThread):            #Поток для мониторинга
    def __init__(self):
        super().__init__()                      #Инициализация потока
        self.stop_flag = {"stop": False}

    def run(self):
        monitor_loop(self.stop_flag)

    def stop(self):
        self.stop_flag["stop"] = True           #Устанавливаем флаг остановки
        self.wait(1500)                         # Ждем до 1.5 секунд для завершения потока

if __name__ == "__main__":                      #Главный блок запуска

    if GUI_MODE:                                #Если GUI_MODE True - запускаем GUI
        app = QtWidgets.QApplication([])        #Создаем приложение GUI
        dash = Dashboard()                      #Создаем главное окно GUI 

        def _push(line: str):                   #Функция для прокидывания логов в GUI
            dash.log_signal.emit(line)

        def _quit(saved_path: str, summary_text: str):    #Функция для выхода из GUI
            def _ui():
                QtWidgets.QMessageBox.information(
                dash,
                "Session ended",
                f"{summary_text}\n\nSession summary saved to:\n{saved_path}",
                )

                dash.allow_close = True
                QtCore.QTimer.singleShot(150, QtWidgets.QApplication.quit)
            QtCore.QTimer.singleShot(0, _ui)


        def _status(status: str):              #Функция для установки статуса в GUI
            dash.status_signal.emit(status)

        status_callback = _status
        quit_callback = _quit       #Функция для выхода из GUI
        log_callback = _push        #Устанавливаем функцию логов в GUI
        t = MonitorThread()         #Создаем и запускаем поток мониторинга
        t.start()                   #1) запускаем поток мониторинга

        
        app.aboutToQuit.connect(t.stop)         #2) при выходе из приложения останавливаем поток мониторинга

        dash.show()                             #3) показываем главное окно GUI         
        app.exec()                              #4) запускаем главный цикл приложения GUI

    else:
        stop_flag = {"stop": False}             #Флаг остановки мониторинга для консольного режима
        try:
            monitor_loop(stop_flag)
        except KeyboardInterrupt:                                            #Обработка нажатия Ctrl+C для остановки монитора
            stop_flag["stop"] = True                                         #Устанавливаем флаг остановки
            emit_log("VALORANT Integrity Monitor stopped by user.")          #Логируем остановку монитора