
import streamlit as st
import os
import json
import pandas as pd

st.set_page_config(page_title="JC GPT Hub – Phase 4", layout="wide")
st.title("🧠 JC GPT Hub – System Monitor (Phase 4)")

tab1, tab2, tab3 = st.tabs(["📜 Logs", "💾 SaveStates", "📈 CRV Backtest"])

with tab1:
    st.subheader("📜 System Logs")
    log_file = "logs/system.log"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            st.text(f.read())
    else:
        st.info("Noch keine Logs vorhanden.")

with tab2:
    st.subheader("💾 Gespeicherte Zustände")
    if os.path.exists("saves"):
        save_files = [f for f in os.listdir("saves") if f.endswith(".json")]
        if save_files:
            selected = st.selectbox("Wähle eine Save-Datei:", save_files)
            with open(f"saves/{selected}", "r") as f:
                st.json(json.load(f))
        else:
            st.info("Keine Save-Dateien vorhanden.")
    else:
        st.warning("Verzeichnis 'saves' nicht gefunden.")

with tab3:
    st.subheader("📈 CRV Verlauf (Backtest)")
    crv_file = "saves/crv_history.csv"
    if os.path.exists(crv_file):
        df = pd.read_csv(crv_file)
        st.line_chart(df.set_index("timestamp"))
    else:
        st.info("Noch keine CRV-Historie vorhanden.")
