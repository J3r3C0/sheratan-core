import json
import streamlit as st
from core.config import get_settings
from core.webrelay_client import WebRelayClient
from core.logger import log_event

st.set_page_config(page_title="Sheratan Laptop Dev", layout="wide")

s = get_settings()
st.title("Sheratan Laptop Dev (no Docker)")
st.caption(f"Tower: {s.tower_host} — WebRelay: {s.webrelay_url}")

with st.sidebar:
    st.subheader("Connection")
    tower = st.text_input("SHERATAN_TOWER_HOST", value=s.tower_host)
    webrelay = st.text_input("SHERATAN_WEBRELAY_URL", value=s.webrelay_url)
    model = st.text_input("Model", value="gpt-4o")
    st.markdown("---")
    st.subheader("Notes")
    st.write("Set environment vars permanently with `setx` for stable runs.")

client = WebRelayClient(webrelay)

col1, col2 = st.columns([2,1])
with col1:
    prompt = st.text_area("Prompt", height=220, placeholder="Ask Sheratan / request a decision / generate a JSON job ...")
    if st.button("Send to Tower WebRelay", type="primary", use_container_width=True):
        try:
            res = client.call(prompt=prompt, model=model, meta={"ui": "streamlit", "tower_host": tower})
            log_event(s.log_dir, {"type": "ui_call", "prompt": prompt, "response": res})
            st.session_state["last_res"] = res
        except Exception as e:
            log_event(s.log_dir, {"type": "error", "where": "ui", "error": str(e)})
            st.error(str(e))

with col2:
    st.subheader("Last response")
    res = st.session_state.get("last_res")
    if res is None:
        st.info("No response yet.")
    else:
        st.code(json.dumps(res, indent=2, ensure_ascii=False), language="json")

st.markdown("---")
st.subheader("Logs")
st.write("Events are appended to `logs/events.jsonl` on the laptop.")
