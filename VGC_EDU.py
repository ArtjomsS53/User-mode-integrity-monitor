import time         #Pредоставляет функции для работы с системным временем
import psutil           #ЦП, память, диски, сеть, датчики
import os
from datetime import datetime


#Константы:
ALLOWLIST_KEYWORDS = [
"edge"
]



GAME_PROCESS = "VALORANT.exe"
LOG_FILE = "VGC_EDU_log.txt"
SESSIONS_DIR = "sessions"




in_session = False          #Внутри сессии Valorant или нет?
session_events = []         #Список событий, что нашли за сессию
seen_keys = set()                  

known_processes = set()

def snapshot_pids() -> set[int]:
    return set(psutil.pids())

def is_game_running() -> bool:
    for p in psutil.process_iter(["name"]):
        try:   #Ищем нужное название процесса ИЗ ВСЕХ запущенных
            if p.info["name"] == GAME_PROCESS:    #Если название процесса VALORANT.exe -> возврат Ture
                return True
        except Exception:
            pass
    return False  

def log(line: str) -> None:
    stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    out = f"[{stamp}] {line}"
    print(out)
    with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as f:
        f.write(out + "\n")

def save_session_summary(lines: list[str]) -> str:          #Создаем папку sessions/, файл с именем и временем, записываем туда строки summary, возвращаем путь
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{stamp}.txt"
    path = os.path.join(SESSIONS_DIR, filename)

    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write("\n".join(lines) + "\n")
    return path


log("VALORANT Integrity Monitor started.")

printed_session_header = False

while True:
    game_running = is_game_running()            #Определяем, запущена ли игра
    if  game_running and not in_session:         #БЛОК START
        in_session = True
        printed_session_header = False
        known_processes = snapshot_pids()
        session_events.clear()          #Очищает события прошлой сессии
        seen_keys.clear()
        log("VALORANT started")
        time.sleep(3)
        continue
    if (not game_running) and in_session:           #БЛОК VALORANT stopped
        in_session = False
        unique_events = list(dict.fromkeys(session_events))         #Убираем дубли и задаём уникальные ивенты

        log("VALORANT stopped")
        summary_lines = []
        summary_lines.append("VALORANT session stopped")
        summary_lines.append(f"Summary: {len(unique_events)} unique process(es) ({len(session_events)}events)")
        summary_lines.append("Processes:")
        for entry in unique_events:
            summary_lines.append(f"- {entry}")
        
        saved_path = save_session_summary(summary_lines)
        log(f"Session summary saved to: {saved_path}")
        log(f"Summary: {len(unique_events)} unique process(es) ({len(session_events)} events)")
        #log("Top process name:")            #Выводим цифры и топ
        #for proc_name, cnt in name_counter.most_common(10):
            #log(f"  - {proc_name}: {cnt}")
        log("Unique processes:")
        for entry in unique_events:         #Список уникальных процессов
            log(f"  - {entry}")

        log("-" * 40)
        time.sleep(3)
        continue


    if in_session:
        if not printed_session_header:
            print("VALORANT monitor started...")
            print("Processes running:", len(psutil.pids()))
            printed_session_header = True

        current = snapshot_pids()
        new_pids = current - known_processes

        for pid in new_pids:
            try:
                if pid in (0, 4):
                    continue

                p = psutil.Process(pid)
                name = p.name()
                exe = p.exe() if p.exe else "?"

                if not name:
                    continue

                exe_low = exe.lower()

                if "\\windows\\system32\\" in exe_low or "\\windows\\syswow64\\" in exe_low:
                    continue

                low = (name + " " + exe).lower()            #Сравниваем процессы на разрешённый
                if any(k in low for k in ALLOWLIST_KEYWORDS):
                    continue            #Если да то пропускаем его

                entry = f"{name} | pid={pid} | exe={exe}"
                key = (name.lower(), exe.lower())

                if key in seen_keys:
                    continue
                seen_keys.add(key)

                log(f"New process while VALORANT running: {entry}")
                session_events.append(entry)

            except (psutil.NoSuchProcess, psutil.AccessDenied):         # процесс мог быстро закрыться или нет доступа
                pass
            except Exception:
                pass   #Если игра запущена, говорит об этом и говорит сколько процессов запущено, len выдает КОЛ-ВО процессов, а не их ID
        known_processes = current
        time.sleep(3)
    else:
        known_processes = snapshot_pids()           #Снапшотит текущие процессы
        print("VALORANT is NOT running")
        time.sleep(3)
        
