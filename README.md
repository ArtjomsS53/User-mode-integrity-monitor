# User-mode Integrity Monitor (VGC EDU)

A user-mode integrity monitoring tool written in Python, inspired by the conceptual design of modern anti-cheat systems.  
This project is **educational** and focuses on process monitoring, logging, multithreading, and GUI architecture rather than real anti-cheat bypass or kernel-level protection.

---

## 🎯 Project Goals

The main purpose of this project is learning and experimentation:

- Understanding how integrity monitoring works at a **conceptual level**
- Practicing **process enumeration and filtering** in user mode
- Building a **responsive GUI application** using threads and Qt signals
- Designing clean and consistent **logging pipelines**
- Maintaining good repository hygiene (no runtime artifacts tracked in Git)

> ⚠️ This project does **NOT** bypass, hook, or interact with real anti-cheat systems.  
> It only observes user-mode processes for educational purposes.

---

## ✨ Features

- Monitors system processes while **VALORANT** is running
- Detects **newly spawned processes** during an active game session
- Session-based monitoring with automatic **session summaries**
- Graphical **GUI dashboard** built with PySide6
- **System tray support** (background operation, show/hide window)
- Monitoring logic runs inside a **separate QThread**
- Live log streaming to:
  - console
  - local log file
  - GUI window
- Real-time application status:
  - `IDLE`
  - `RUNNING`
- Clean repository structure:
  - no logs in Git
  - no session artifacts in Git
  - runtime data is local-only

---

## 🧱 Architecture Overview

The application is split into clearly separated layers:

- **Core monitoring logic**
  - Process snapshotting using `psutil`
  - Allowlist-based filtering
  - Session lifecycle management
- **Threaded monitor**
  - Runs independently from the GUI
  - Prevents UI freezing
- **GUI layer**
  - Live log display
  - Status indicator
  - System tray integration
- **Signal-based communication**
  - Thread-safe updates between monitor and GUI

---

## 📂 Project Structure

.
├── VALORANT Integrity Monitor.py # Main application (monitor + GUI)
├── README.md # Project documentation
├── to_do.md # Planned improvements
├── .gitignore # Ignore logs & runtime artifacts

Runtime-generated files (not tracked by Git):

- `VGC_EDU_log.txt`
- `sessions/`

---

## 📝 Example Log Output

```bash
[16-01-2026 23:55:39] VALORANT Integrity Monitor started.
[16-01-2026 23:55:51] VALORANT started
[16-01-2026 23:55:54] VALORANT monitor started...
[16-01-2026 23:55:54] New process while VALORANT running: OP.GG.exe | pid=1512 | exe=...
[16-01-2026 23:57:09] VALORANT stopped
[16-01-2026 23:57:09] Session summary saved to: sessions/2026-01-16_23-57-09.txt
```
---

## 🚀 How to Run

### Requirements
- Python 3.10 or newer
- Windows OS
- Required dependencies:
  ```bash
  pip install psutil PySide6
  ```

## How To Launch

python "VALORANT Integrity Monitor.py"

---

📌 Important Notes

- This is a user-mode only project

- No kernel drivers

- No memory scanning

- No game manipulation

- Designed strictly for learning and demonstration

---

🛠 Planned Improvements

- Start / Stop monitoring directly from the system tray

- Configurable allowlist via external file

- GUI-based session summary viewer

- Colored log levels (INFO / EVENT / ALERT)

- Modular check system for extensibility

---

📜 License

Educational use only.
You are free to study, modify, and extend this project for learning purposes.

---

👤 Author

ArtjomsS53
Educational project focused on system monitoring, Python architecture, multithreading, and GUI design.