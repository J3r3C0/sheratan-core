import streamlit as st
import threading
import subprocess
import os
import sys
import MetaTrader5 as mt5

# Pfad-Fix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules import (
    ml_training_tab,
    gpt_core_tab,
    project_handler_tab,
    gril_module,
    autoupdate_tab,
    insight_module,
    trading_tab
)

status = {"telegram": False, "mt5": False}

def start_telegram_bot():
    try:
        subprocess.Popen(["python", "embedded/trading_bot/telegram_bot.py"])
        status["telegram"] = True
    except Exception:
        status["telegram"] = False

# Seite konfigurieren
def render():
    st.set_page_config(page_title="GPT Hub", layout="wide")
    st.title("🧠 GPT Hub v2.4")

    col1, col2 = st.columns(2)

    # Telegram starten per Checkbox
    if "telegram_started" not in st.session_state:
        st.session_state["telegram_started"] = False
    start_now = col1.checkbox("🤖 Telegram-Bot starten", value=st.session_state["telegram_started"])
    if start_now and not st.session_state["telegram_started"]:
        threading.Thread(target=start_telegram_bot).start()
        st.session_state["telegram_started"] = True

    # MT5 prüfen
    status["mt5"] = mt5.initialize()
    col2.markdown(f"🖥️ MT5 Status: {'✅ Verbunden' if status['mt5'] else '❌ Keine Verbindung'}")

    # Tabs definieren
    TABS = {
        "ML-Training": ml_training_tab.render,
        "GPT": gpt_core_tab.render,
        "Projekt-Handling": project_handler_tab.render,
        "GRIL": gril_module.render,
        "AutoUpdate": autoupdate_tab.render,
        "Einsicht": insight_module.render,
        "Trading": trading_tab.render,
    }

    selection = st.sidebar.radio("📂 Module auswählen", list(TABS.keys()))
    TABS[selection]()

# <--- FEHLTE VORHER
if __name__ == "__main__":
    render()
