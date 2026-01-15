# VALORANT User-Mode Integrity Monitor (Educational)

## 📌 Overview

This project is a **user-mode integrity monitor** for **VALORANT**, created for **educational purposes**.

The goal of the project is to demonstrate how **OS-level process monitoring** and **behavior-based detection logic** work in practice — **without interacting with the game memory or bypassing any anti-cheat systems**.

The program monitors system processes **only while VALORANT is running** and logs newly spawned processes during active gameplay sessions.

---

## 🎯 Purpose of the Project

- Learn **system-level thinking**, not game hacking
- Practice **process lifecycle monitoring**
- Understand how **behavioral detection** works conceptually
- Build a **portfolio-ready security / IT project**
- Work with Python in a **practical, minimal way**

This project is **not a cheat**, **not a bypass**, and **not an anti-cheat replacement**.

---

## 🔒 What This Project DOES NOT Do

❌ Does NOT access game memory  
❌ Does NOT inject code  
❌ Does NOT interfere with Riot Vanguard  
❌ Does NOT bypass or disable any protection  
❌ Does NOT modify VALORANT files  

This tool operates **entirely in user-mode**, using publicly available OS APIs.

---

## ✅ What This Project DOES

✔ Detects when `VALORANT.exe` starts and stops  
✔ Takes snapshots of running system processes  
✔ Detects **new processes spawned during gameplay**  
✔ Filters known/expected processes using an allowlist  
✔ Logs events with timestamps to a file  

---

## 🧠 How It Works (High Level)

1. The program continuously checks whether `VALORANT.exe` is running
2. When the game starts:
   - The current process list is saved as a baseline
3. While the game is running:
   - New processes are detected by comparing snapshots
4. Known/allowed processes are filtered out
5. Unexpected processes are logged for analysis
6. When the game closes:
   - Monitoring pauses until the next session

---

## 🛠 Technologies Used

- **Python 3.10+**
- **psutil** — process and system monitoring library
- Standard Python libraries (`time`, `datetime`, `os`)

---

## 📂 Project Structure

- `monitor.py` — main monitoring logic
- `monitor_log.txt` — generated runtime log
- `README.md` — project documentation

---

The monitor will automatically detect the game session and log events.


Example Log Output:

```bash
[2026-01-15 18:41:12] VALORANT Integrity Monitor started
[2026-01-15 18:42:05] New process while VALORANT running: obs64.exe | pid=1234
[2026-01-15 18:55:33] VALORANT session ended
```
---

Educational Value:
This project demonstrates:
OS-level telemetry usage
Behavioral monitoring concepts
Event-driven system logic
Practical Python scripting
Security-oriented thinking

It is suitable as:
a personal learning project
a portfolio item
a foundation for further system monitoring tools



!!!⚠️Disclaimer
This project is created strictly for educational purposes.

VALORANT and Riot Vanguard are trademarks of Riot Games, Inc.
This project is not affiliated with or endorsed by Riot Games.
