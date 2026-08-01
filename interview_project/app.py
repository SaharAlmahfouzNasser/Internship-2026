import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agents import stream_tumor_board
from cases import CASES, get_case

load_dotenv()

st.set_page_config(page_title="Tumor Board Multi-Agent Simulator", layout="wide")
st.title("Tumor Board Multi-Agent Simulator")
st.caption("Educational multi-agent clinical reasoning demo. Not for real clinical decision-making.")

with st.sidebar:
    st.header("Configuration")
    case_titles = {f"{c.case_id} — {c.title}": c.case_id for c in CASES}
    selected_label = st.selectbox("Patient case", list(case_titles.keys()))
    max_iterations = st.slider("Maximum iteration threshold", min_value=2, max_value=10, value=5, step=1)
    use_evaluator = st.toggle("Use evaluation agent for convergence", value=True)
    run_btn = st.button("Run tumor board", type="primary")

case = get_case(case_titles[selected_label])

st.subheader("Selected case")
with st.expander("Clinical summary", expanded=True):
    st.markdown(f"**{case.title}**")
    st.markdown("**Clinical summary**")
    st.write(case.clinical_summary)
    st.markdown("**Imaging findings**")
    st.write(case.imaging_findings)
    st.markdown("**Pathology report**")
    st.write(case.pathology_report)

if run_btn:
    st.session_state.pop("last_result", None)

    st.subheader("Live discussion timeline")

    current_placeholder = None
    current_text = ""
    eval_placeholders = {}

    for event in stream_tumor_board(
        case,
        max_iterations=max_iterations,
        use_evaluator=use_evaluator,
    ):
        if event["type"] == "turn_start":
            with st.container(border=True):
                st.markdown(f"### Iteration {event['iteration']}: {event['speaker']}")
                st.caption(event["role"])
                current_placeholder = st.empty()
                current_text = ""

        elif event["type"] == "token":
            current_text = event["content"]
            if current_placeholder is not None:
                current_placeholder.markdown(current_text)

        elif event["type"] == "evaluation_start":
            eval_placeholders[event["iteration"]] = st.empty()
            eval_placeholders[event["iteration"]].info("Evaluation agent is checking convergence...")

        elif event["type"] == "evaluation_end":
            ev = event["evaluation"]
            score = ev.get("score", 0)

            box = eval_placeholders.get(event["iteration"], st.empty())
            with box.container():
                st.progress(
                    min(max(int(score), 0), 100),
                    text=f"Evaluator convergence score: {score}/100",
                )
                st.markdown(f"**Converged:** `{ev.get('converged')}`")
                st.markdown(f"**Reason:** {ev.get('reason')}")
                gaps = ev.get("remaining_gaps") or []
                if gaps:
                    st.markdown("**Remaining gaps**")
                    for gap in gaps:
                        st.markdown(f"- {gap}")

        elif event["type"] == "summary_start":
            st.info("Generating final joint summary...")

        elif event["type"] == "done":
            st.session_state["last_result"] = event["result"]
            st.success("Tumor board discussion completed.")

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    st.subheader("Discussion timeline")

    for turn in result.transcript:
        with st.container(border=True):
            st.markdown(f"### Iteration {turn.iteration}: {turn.speaker}")
            st.caption(turn.role)
            st.markdown(turn.content)
            if turn.evaluation:
                ev = turn.evaluation
                score = ev.get("score", 0)
                st.progress(min(max(int(score), 0), 100), text=f"Evaluator convergence score: {score}/100")
                st.markdown(f"**Converged:** `{ev.get('converged')}`")
                st.markdown(f"**Reason:** {ev.get('reason')}")
                gaps = ev.get("remaining_gaps") or []
                if gaps:
                    st.markdown("**Remaining gaps**")
                    for gap in gaps:
                        st.markdown(f"- {gap}")

    st.subheader("Final joint summary")
    st.markdown(result.final_summary)

    data = result.to_dict()
    st.download_button(
        label="Download transcript JSON",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name=f"{result.case_id}_transcript.json",
        mime="application/json",
    )
