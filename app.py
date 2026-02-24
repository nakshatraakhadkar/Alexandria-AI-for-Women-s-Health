import json
from typing import Dict, Any, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from extractor import extract_clinical_data


st.set_page_config(
    page_title="Alexandria: Clinical NLP Companion",
    page_icon="💜",
    layout="centered",
)


def init_session_state() -> None:
    if "chat_history" not in st.session_state:
        # Each entry: {"role": "user" | "assistant", "content": str, "extracted": dict | None}
        st.session_state.chat_history: List[Dict[str, Any]] = []


def render_header() -> None:
    st.title("Alexandria: Clinical NLP Companion")
    st.caption(
        "A proof-of-concept interface that turns everyday health narratives "
        "into structured, clinically usable data."
    )

    with st.sidebar:
        st.markdown("### About this demo")
        st.write(
            "This prototype illustrates how a conversational interface can capture "
            "symptoms and transform them into standardized clinical signals, "
            "supporting women's health journeys."
        )
        st.markdown("---")
        st.markdown(
            "**Disclaimer:** This is a non-clinical demo and should not be used "
            "for medical decision-making."
        )


def render_chat_history() -> None:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            extracted = message.get("extracted")
            if extracted:
                with st.expander("🔍 View Extracted Clinical Data", expanded=False):
                    st.json(extracted)


def add_message(role: str, content: str, extracted: Dict[str, Any] | None = None) -> None:
    st.session_state.chat_history.append(
        {"role": role, "content": content, "extracted": extracted}
    )


def build_response_text(extracted: Dict[str, Any]) -> str:
    symptoms = extracted.get("extracted_symptoms") or []
    severity = extracted.get("severity")

    if symptoms:
        symptom_list = ", ".join(symptoms)
        base = f"I'm sorry you're experiencing {symptom_list}."
    else:
        base = "Thank you for sharing how you're feeling."

    if severity is not None:
        base += f" You've rated this around {severity}/10."

    base += " I've logged your entry so it can support a clearer clinical picture over time."
    return base


def load_synthetic_data() -> pd.DataFrame:
    """
    Temporary synthetic dataset for the analytics dashboard.
    This will be replaced by pd.read_csv('patient_data.csv') once available.
    """
    num_days = 60
    dates = pd.date_range(end=pd.Timestamp.today(), periods=num_days, freq="D")

    cycle_day = [(i % 28) + 1 for i in range(num_days)]
    sleep_hours = [
        max(4, min(9, 7 + (0.8 if d in (1, 2) else 0) - (i % 5) * 0.2))
        for i, d in enumerate(cycle_day)
    ]
    heart_rate = [
        72 + (5 if d in (1, 2, 3) else 0) + (i % 3)
        for i, d in enumerate(cycle_day)
    ]
    pain_severity = [
        min(10, max(0, 2 + (6 if d in (1, 2, 3) else 0) - (i % 4)))
        for i, d in enumerate(cycle_day)
    ]

    df = pd.DataFrame(
        {
            "Date": dates,
            "Cycle_Day": cycle_day,
            "Sleep_Hours": sleep_hours,
            "Heart_Rate": heart_rate,
            "Pain_Severity": pain_severity,
        }
    )
    return df


def main() -> None:
    init_session_state()
    render_header()

    tab1, tab2 = st.tabs(["💬 Chat Companion", "📈 My Body Analytics"])

    with tab1:
        render_chat_history()

        prompt = st.chat_input("Describe how you're feeling today...")
        if prompt:
            # Show user's message
            with st.chat_message("user"):
                st.markdown(prompt)
            add_message("user", prompt)

            # Run NLP extraction
            extracted = extract_clinical_data(prompt)

            # Build empathetic AI response
            response_text = build_response_text(extracted)

            with st.chat_message("assistant"):
                st.markdown(response_text)
                with st.expander("🔍 View Extracted Clinical Data", expanded=False):
                    st.json(extracted)

            add_message("assistant", response_text, extracted=extracted)

    with tab2:
        st.subheader("Correlation Dashboard")
        st.markdown(
            "Explore how your reported pain intensity may relate to your sleep and heart rate "
            "over time. This view uses temporary synthetic data for the proof of concept."
        )

        df = load_synthetic_data()

        fig = go.Figure()
        fig.add_bar(
            x=df["Date"],
            y=df["Pain_Severity"],
            name="Pain Severity (0–10)",
            marker_color="#c084fc",
            opacity=0.7,
        )
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Sleep_Hours"],
                mode="lines+markers",
                name="Sleep Hours",
                line=dict(color="#22c55e", width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Heart_Rate"],
                mode="lines",
                name="Heart Rate (bpm)",
                line=dict(color="#0ea5e9", width=2, dash="dot"),
            )
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=40, b=40),
            yaxis_title="Intensity / Hours / bpm",
            xaxis_title="Date",
            template="plotly_white",
        )

        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()

