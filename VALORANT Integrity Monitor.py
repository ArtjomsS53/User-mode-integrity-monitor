import time         #Pредоставляет функции для работы с системным временем
import psutil           #ЦП, память, диски, сеть, датчики
import os               #Взаимодействие с ОС
from datetime import datetime           #Работа с датой и временем
from PySide6 import QtWidgets, QtCore, QtGui    #GUI библиотека


#Константы:
ALLOWLIST_KEYWORDS = [          #Слова для белого списка процессов
"edge"
]



GAME_PROCESS = "VALORANT.exe"       #Название процесса игры
LOG_FILE = "VGC_EDU_log.txt"        #Файл лога
SESSIONS_DIR = "sessions"           #Папка для сохранения сессий

GUI_MODE = True          #Если True - запускается GUI, если False - консольный режим
log_callback = None        #Функция обратного вызова для логов GUI
status_callback = None     #Принимает str: "IDLE" / "RUNNING"



in_session = False          #Внутри сессии Valorant или нет?
session_events = []         #Список событий, что нашли за сессию
seen_keys = set()           #Уникальные ключи процессов (имя + путь), чтобы не логировать дубликаты       
known_processes = set()     #Известные PIDы процессов на данный момент
printed_session_header = False                      #Флаг для печати заголовка сессии только один раз

def snapshot_pids() -> set[int]:            #Функция создания снимка текущих PIDов процессов
    return set(psutil.pids())

def is_game_running() -> bool:          #Функция проверки запущен ли процесс VALORANT.exe
    for p in psutil.process_iter(["name"]):
        try:   #Ищем нужное название процесса ИЗ ВСЕХ запущенных
            if p.info["name"] == GAME_PROCESS:    #Если название процесса VALORANT.exe -> возврат Ture
                return True
        except Exception:
            pass
    return False  

def emit_log(message: str):         #Функция логирования с отметкой времени, запись в файл и прокидка в GUI

    stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    line = f"[{stamp}] {message}"

    print(line)

    #Запись в файл лога
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
    global not_running_logged

    emit_log("VALORANT Integrity Monitor started.")
    set_status("IDLE")

    while not stop_flag["stop"]:
        game_running = is_game_running()

        # START
        if game_running and not in_session:
            in_session = True
            printed_session_header = False
            known_processes = snapshot_pids()
            session_events.clear()
            seen_keys.clear()

            emit_log("VALORANT started")
            set_status("RUNNING")
            time.sleep(3)
            continue

        # STOP
        if (not game_running) and in_session:
            in_session = False
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
            time.sleep(3)
            continue

        # IN SESSION
        if in_session:
            if not printed_session_header:
                emit_log("VALORANT monitor started...")
                emit_log(f"Processes running: {len(psutil.pids())}")
                printed_session_header = True

            current = snapshot_pids()
            new_pids = current - known_processes

            for pid in new_pids:
                try:
                    if pid in (0, 4):
                        continue

                    p = psutil.Process(pid)
                    name = p.name() or ""
                    
                    try:
                        exe = p.exe()
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        exe = "?"

                    if not name:
                        continue

                    exe_low = (exe or "").lower()
                    if "\\windows\\system32\\" in exe_low or "\\windows\\syswow64\\" in exe_low:
                        continue

                    low = (name + " " + (exe or "")).lower()
                    if any(k.lower() in low for k in ALLOWLIST_KEYWORDS):
                        continue

                    entry = f"{name} | pid={pid} | exe={exe}"
                    key = (name.lower(), (exe or "").lower())

                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    emit_log(f"New process while VALORANT running: {entry}")
                    session_events.append(entry)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                except Exception:
                    pass

            known_processes = current
            time.sleep(3)

        else:
            known_processes = snapshot_pids()
            time.sleep(3)

class Dashboard(QtWidgets.QMainWindow):        #GUI класс
    log_signal = QtCore.Signal(str)
    status_signal = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VALORANT Integrity Monitor")
        self.resize(900, 600)

        self.base_title = "VALORANT Integrity Monitor"
        self.setWindowTitle(self.base_title)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
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
        QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

class MonitorThread(QtCore.QThread):            #Поток для мониторинга
    def __init__(self):
        super().__init__()
        self.stop_flag = {"stop": False}

    def run(self):
        monitor_loop(self.stop_flag)

    def stop(self):
        self.stop_flag["stop"] = True

if __name__ == "__main__":

    if GUI_MODE:                                #Если GUI_MODE True - запускаем GUI
        app = QtWidgets.QApplication([])        #Создаем приложение GUI
        dash = Dashboard()                      #Создаем главное окно GUI 

        def _push(line: str):                   #Функция для прокидывания логов в GUI
            dash.log_signal.emit(line)

        def _status(status: str):              #Функция для установки статуса в GUI
            dash.status_signal.emit(status)
        status_callback = _status

        log_callback = _push

        t = MonitorThread()          #Создаем и запускаем поток мониторинга
        t.start()                   #1) запускаем поток мониторинга

        
        app.aboutToQuit.connect(t.stop)         #2) при выходе из приложения останавливаем поток мониторинга

        dash.show()                             #3) показываем главное окно GUI         
        app.exec()                              #4) запускаем главный цикл приложения GUI

    else:
        stop_flag = {"stop": False}             #Флаг остановки мониторинга для консольного режима
        try:
            monitor_loop(stop_flag)
        except KeyboardInterrupt:           #Обработка нажатия Ctrl+C для остановки монитора
            stop_flag["stop"] = True        #Устанавливаем флаг остановки
            emit_log("VALORANT Integrity Monitor stopped by user.")          #Логируем остановку монитора