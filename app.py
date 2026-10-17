#.\.venv\Scripts\Activate.ps1
#streamlit run app.py
#deactivate
import streamlit as st

import pandas as pd
from pathlib import Path
from iot_assistant import IoTAssistant

st.set_page_config(page_title="IoT Operations Assistant", page_icon="🛠️", layout="wide")
DATA_PATH = Path(__file__).parent / "data" / "iot_operations_01.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()
assistant = IoTAssistant(df)

st.title("🛠️ AI-Powered IoT Operations Assistant")
st.caption("Ask questions about industrial equipment health, sensor readings, maintenance, alerts, and failures.")

with st.sidebar:
    st.header("Access and data")
    role = st.selectbox("Demo user role", ["Operations Manager", "Reliability Engineer", "Viewer"])
    st.info("This is a demonstration role selector. Production deployments should use real authentication and server-side authorization.")
    st.metric("Dataset records", f"{len(df):,}")
    st.metric("Data columns", len(df.columns))
    st.caption(f"Observation dates: {pd.to_datetime(df['observation_date'], errors='coerce').min().date()} to {pd.to_datetime(df['observation_date'], errors='coerce').max().date()}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Equipment records", f"{len(df):,}")
c2.metric("Asset types", f"{df['asset_type'].nunique():,}")
c3.metric("Facilities", f"{df['facility_id'].nunique():,}")
c4.metric("Average health score", f"{df['ai_health_index_score'].mean():.1f}/100")

st.subheader("Ask the assistant")
examples = [
    "How many equipment records are there?",
    "What is the average health score?",
    "Which asset types have the most alerts in the last 7 days?",
    "How many assets are due for preventive maintenance within 7 days?",
    "Show assets with an unscheduled failure within 7 days",
    "What is the average bearing temperature for compressors?",
    "Which facilities have the lowest average health score?",
]
choice = st.selectbox("Try an example question", ["Choose an example..."] + examples)
question = st.text_input("Your question", value="" if choice == "Choose an example..." else choice,
                         placeholder="e.g., What is the average vibration for centrifugal pumps?")
if st.button("Get answer", type="primary") and question.strip():
    result = assistant.answer(question, role=role)
    st.subheader("Answer")
    st.write(result["answer"])
    if result.get("table") is not None:
        st.dataframe(result["table"], use_container_width=True, hide_index=True)
    st.caption("Data provenance: " + result["provenance"])
    if result.get("note"):
        st.warning(result["note"])

st.divider()
st.subheader("Explore the dataset")
tab1, tab2, tab3 = st.tabs(["Asset types", "Health overview", "Data dictionary"])
with tab1:
    counts = df["asset_type"].value_counts().rename_axis("Asset type").reset_index(name="Records")
    st.bar_chart(counts.set_index("Asset type"))
    st.dataframe(counts, use_container_width=True, hide_index=True)
with tab2:
    st.write("Health score distribution")
    st.line_chart(df["ai_health_index_score"].dropna().reset_index(drop=True))
    st.write("Average health score by asset type")
    health = df.groupby("asset_type", as_index=False)["ai_health_index_score"].mean().sort_values("ai_health_index_score")
    st.dataframe(health.round(2), use_container_width=True, hide_index=True)
with tab3:
    dictionary = pd.DataFrame({"Column": df.columns, "Data type": df.dtypes.astype(str).values,
                               "Non-null values": df.notna().sum().values})
    st.dataframe(dictionary, use_container_width=True, hide_index=True)

st.caption("Prototype note: answers are generated from deterministic data-analysis rules. The included RAG module retrieves local reference notes; an external LLM is not required.")
