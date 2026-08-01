import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

try:
    from langchain_deepseek import ChatDeepSeek
except Exception:  # pragma: no cover
    ChatDeepSeek = None

load_dotenv()


ONCOLOGIST_SYSTEM = """
You are the ONCOLOGIST agent in a simulated tumor board.

Your role is not to diagnose from tissue. Your role is to reason from clinical stage, prognosis,
treatment options, guideline-oriented strategy, clinical trial eligibility when relevant, toxicity,
patient fitness, and quality-of-life trade-offs.

You should consider treatment options such as surgery, chemotherapy, immunotherapy, targeted therapy,
radiation therapy, clinical trials, surveillance, and palliative care when relevant.

You should use evidence-based guideline reasoning, including NCCN and ESMO when relevant, but do not
claim that a recommendation is guideline-confirmed unless the case provides enough information to support it.

Reasoning style:
- Think in terms of survival probabilities, survival outcomes, expected treatment benefit, toxicity,
  patient fitness, and quality-of-life trade-offs.
- Reason in the following order:
  1. Determine the clinical stage or likely stage.
  2. Determine the treatment intent, such as curative, disease control, palliation, or further diagnostic clarification.
  3. Identify pathology-driven treatment factors.
  4. Compare reasonable treatment options.
  5. Weigh expected benefit against toxicity and quality-of-life impact.
  6. State the current recommendation.
- Do not recommend treatment based on cancer type alone.
- If key staging, biomarker, resectability, or patient-fitness information is missing, give a provisional
  recommendation and list what information is needed before final treatment selection.

Behavior rules:
- Think like a medical oncologist: treatment sequencing, survival benefit, toxicity, resectability,
  staging, follow-up, and patient goals.
- Explicitly use the facts provided by the Pathologist, but do not invent pathology details or make up new facts.
- Ask at least one specific pathology clarification that could significantly affect the treatment decision.
- When asking clarification, focus on biomarkers, margins, tumor grade, tissue adequacy, histologic subtype,
  receptor status, molecular findings, or ambiguous pathology findings.
- Before accepting the conclusion provided by the Pathologist, identify at least one limitation, uncertainty,
  or complicating factor that may affect the treatment decision.
- When the Pathologist provides new or corrected information, explicitly state whether it changes your
  treatment recommendation and why.
- This is an educational simulation and must not be used for real clinical decision-making.

Return structured Markdown with:
1. Interpretation
2. Treatment reasoning
3. Questions or concerns for the Pathologist
4. Current recommendation
""".strip()


PATHOLOGIST_SYSTEM = """
You are the PATHOLOGIST agent in a simulated tumor board.

Your role is not to choose a full systemic therapy plan. Your role is to interpret tissue findings,
histology, tumor grade, margins, receptor status, biomarker status, molecular implications, sample adequacy,
and ambiguities in the pathology report.

You should focus on what the specimen directly shows and explain how those findings constrain or affect
oncology decision-making.

Reasoning style:
- Stay grounded in what is observed, not inferred.
- Separate confirmed findings, inferred implications, and missing or pending information.
- Flag ambiguities in the pathology report that may affect treatment decisions.
- Do not infer missing biomarkers, receptor status, margins, grade, or molecular results.
- If the pathology report does not support a conclusion, explicitly say that it cannot be concluded
  from the available specimen.

Behavior rules:
- Think like a pathologist: what is directly observed, what is inferred from the observed findings,
  and what cannot be concluded from the specimen.
- Interpret histology, grade, margins, receptor or biomarker status, molecular findings, tissue adequacy,
  and diagnostic uncertainty.
- Flag insufficient tissue, missing stains, pending biomarkers, discordant findings, ambiguous morphology,
  or pathology facts that may change management.
- Challenge treatment assumptions if the tissue evidence is incomplete or points in a different direction.
- Explain treatment implications only as they relate to pathology findings.
- Do not overstep into detailed oncology treatment sequencing unless explaining the implications of pathology.
- Before accepting the Oncologist's treatment direction, identify at least one pathology-based caveat,
  missing result, or uncertainty when relevant.
- This is an educational simulation and must not be used for real clinical decision-making.

Return structured Markdown with:
1. Tissue interpretation
2. Clinically relevant pathology implications
3. Uncertainties or missing information
4. What the Oncologist should account for
""".strip()


EVALUATOR_SYSTEM = """
You are the EVALUATION agent for an educational multi-agent tumor-board simulation.
Your job is to judge whether the oncologist-pathologist discussion has converged enough to stop.
You are not a third clinical decision maker. You evaluate conversation quality and convergence.

Evaluate using these criteria:
1. Role separation: Did each agent contribute non-overlapping expertise?
2. Information exchange: Did one agent's statement change, constrain, or clarify the other's reasoning?
3. Open issues: Are there unresolved pathology, staging, biomarker, or treatment uncertainties?
4. Final-plan readiness: Is the conversation ready for a joint educational summary?

Return ONLY valid JSON with this schema:
{
  "converged": true/false,
  "score": 0-100,
  "reason": "short explanation",
  "remaining_gaps": ["gap 1", "gap 2"],
  "suggested_next_prompt": "one concise instruction for the next speaker, or empty string if converged"
}
""".strip()


SUMMARY_SYSTEM = """
You are producing the final joint educational tumor-board summary.
Use only the provided case and transcript. Do not invent missing tests or results.
Make clear what is known, what is uncertain, and what should be followed up.
""".strip()


@dataclass
class Turn:
    iteration: int
    speaker: str
    role: str
    content: str
    evaluation: Optional[Dict[str, Any]] = None


@dataclass
class TumorBoardResult:
    case_id: str
    max_iterations: int
    use_evaluator: bool
    converged: bool
    transcript: List[Turn]
    final_summary: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def _get_qwen_llm(model: Optional[str] = None, temperature: float = 0.2):
    return ChatOpenAI(
        model=model or os.getenv("QWEN_MODEL", "qwen-plus"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
        temperature=temperature,
    )


def _get_deepseek_llm(model: Optional[str] = None, temperature: float = 0.2):
    # Prefer provider-specific LangChain integration when installed.
    if ChatDeepSeek is not None:
        return ChatDeepSeek(
            model=model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            temperature=temperature,
            max_retries=2,
        )
    # Fallback: DeepSeek is OpenAI-compatible.
    return ChatOpenAI(
        model=model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=temperature,
    )


def build_llms():
    # default
    oncologist_llm = _get_qwen_llm(temperature=0.2)
    pathologist_llm = _get_deepseek_llm(temperature=0.2)

    # swap
    oncologist_llm = _get_deepseek_llm(temperature=0.2)
    pathologist_llm = _get_qwen_llm(temperature=0.2)

    evaluator_provider = os.getenv("EVALUATOR_PROVIDER", "qwen").lower()
    if evaluator_provider == "deepseek":
        evaluator_llm = _get_deepseek_llm(model=os.getenv("EVALUATOR_MODEL"), temperature=0.0)
    else:
        evaluator_llm = _get_qwen_llm(model=os.getenv("EVALUATOR_MODEL"), temperature=0.0)
    return oncologist_llm, pathologist_llm, evaluator_llm


def stream_agent(llm, system_prompt: str, case_text: str, transcript: List[Turn], task: str):
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
        PATIENT CASE:
        {case_text}

        TRANSCRIPT SO FAR:
        {format_transcript(transcript) if transcript else "No prior transcript."}

        YOUR TASK:
        {task}
        """.strip()),
    ]

    full_text = ""
    for chunk in llm.stream(messages):
        token = chunk.content if hasattr(chunk, "content") else str(chunk)
        if token:
            full_text += token
            yield token, full_text


def stream_tumor_board(case_obj, max_iterations: int = 4, use_evaluator: bool = True):
    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")

    oncologist_llm, pathologist_llm, evaluator_llm = build_llms()
    case_text = case_obj.render()
    transcript: List[Turn] = []
    converged = False

    opening_tasks = [
        ("Pathologist", "Pathology interpretation", pathologist_llm, PATHOLOGIST_SYSTEM,
         "Round 1: Open the tumor board. Interpret the pathology findings, identify tumor type/grade/biomarkers, and flag ambiguities."),
        ("Oncologist", "Treatment strategy", oncologist_llm, ONCOLOGIST_SYSTEM,
         "Round 2: Respond to the pathology interpretation. State initial treatment hypothesis and ask at least one specific pathology clarification."),
        ("Pathologist", "Pathology clarification", pathologist_llm, PATHOLOGIST_SYSTEM,
         "Round 3: Answer the oncologist's question(s). Raise any pathology fact that complicates or challenges the proposed treatment."),
        ("Oncologist", "Revised treatment plan", oncologist_llm, ONCOLOGIST_SYSTEM,
         "Round 4: Revise the treatment recommendation using the pathologist's input. State whether remaining uncertainty prevents a final plan."),
    ]

    for idx in range(max_iterations):
        if idx < len(opening_tasks):
            speaker, role, llm, sys_prompt, task = opening_tasks[idx]
        else:
            if idx % 2 == 0:
                speaker, role, llm, sys_prompt = "Pathologist", "Targeted refinement", pathologist_llm, PATHOLOGIST_SYSTEM
            else:
                speaker, role, llm, sys_prompt = "Oncologist", "Targeted refinement", oncologist_llm, ONCOLOGIST_SYSTEM

            last_eval = transcript[-1].evaluation if transcript and transcript[-1].evaluation else {}
            suggested = last_eval.get(
                "suggested_next_prompt",
                "Address remaining uncertainties and state whether you agree the discussion can converge."
            )
            task = f"Additional structured convergence round: {suggested}"

        yield {
            "type": "turn_start",
            "iteration": idx + 1,
            "speaker": speaker,
            "role": role,
        }

        content = ""
        for token, full_text in stream_agent(llm, sys_prompt, case_text, transcript, task):
            content = full_text
            yield {
                "type": "token",
                "iteration": idx + 1,
                "speaker": speaker,
                "role": role,
                "token": token,
                "content": full_text,
            }

        turn = Turn(iteration=idx + 1, speaker=speaker, role=role, content=content)
        transcript.append(turn)

        yield {
            "type": "turn_end",
            "iteration": idx + 1,
            "speaker": speaker,
            "role": role,
            "content": content,
        }

        if use_evaluator and idx >= 1:
            yield {
                "type": "evaluation_start",
                "iteration": idx + 1,
            }

            evaluation = evaluate_convergence(evaluator_llm, case_text, transcript)
            turn.evaluation = evaluation

            yield {
                "type": "evaluation_end",
                "iteration": idx + 1,
                "evaluation": evaluation,
            }

            if evaluation.get("converged") is True and idx >= 3:
                converged = True
                break

    if not use_evaluator:
        converged = True

    yield {
        "type": "summary_start",
    }

    final_summary = make_final_summary(oncologist_llm, pathologist_llm, case_text, transcript)

    result = TumorBoardResult(
        case_id=case_obj.case_id,
        max_iterations=max_iterations,
        use_evaluator=use_evaluator,
        converged=converged,
        transcript=transcript,
        final_summary=final_summary,
    )

    yield {
        "type": "done",
        "result": result,
    }

def format_transcript(transcript: List[Turn]) -> str:
    chunks = []
    for t in transcript:
        chunks.append(f"[Iteration {t.iteration}] {t.speaker} ({t.role})\n{t.content}")
        if t.evaluation:
            chunks.append(f"[Evaluation after iteration {t.iteration}]\n{json.dumps(t.evaluation, indent=2)}")
    return "\n\n".join(chunks)


def invoke_agent(llm, system_prompt: str, case_text: str, transcript: List[Turn], task: str) -> str:
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
        PATIENT CASE:
        {case_text}

        TRANSCRIPT SO FAR:
        {format_transcript(transcript) if transcript else "No prior transcript."}

        YOUR TASK:
        {task}
        """.strip()),
    ]
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


def evaluate_convergence(evaluator_llm, case_text: str, transcript: List[Turn]) -> Dict[str, Any]:
    response = evaluator_llm.invoke([
        SystemMessage(content=EVALUATOR_SYSTEM),
        HumanMessage(content=f"""
        PATIENT CASE:
        {case_text}

        TRANSCRIPT:
        {format_transcript(transcript)}

        Evaluate convergence now. Return only JSON.
        """.strip())
    ])
    raw = response.content if hasattr(response, "content") else str(response)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {
            "converged": False,
            "score": 0,
            "reason": f"Evaluator did not return valid JSON: {raw[:300]}",
            "remaining_gaps": ["Invalid evaluator JSON"],
            "suggested_next_prompt": "Clarify unresolved facts and explicitly state whether a joint summary is ready.",
        }


def make_final_summary(oncologist_llm, pathologist_llm, case_text: str, transcript: List[Turn]) -> str:
    path_input = f"""
    PATIENT CASE:
    {case_text}

    FULL TRANSCRIPT:
    {format_transcript(transcript)}

    As the pathologist, write your contribution to the final summary. Focus on diagnosis, tissue evidence,
    biomarker uncertainty, and pathology-driven implications. Use concise Markdown.
    """.strip()
    path_part = pathologist_llm.invoke([SystemMessage(content=SUMMARY_SYSTEM), HumanMessage(content=path_input)]).content

    onc_input = f"""
    PATIENT CASE:
    {case_text}

    FULL TRANSCRIPT:
    {format_transcript(transcript)}

    PATHOLOGIST FINAL CONTRIBUTION:
    {path_part}

    As the oncologist, integrate the pathologist contribution into a final joint tumor-board summary with these sections:
    1. Working diagnosis
    2. Key pathology facts
    3. Treatment recommendation
    4. Key uncertainties / follow-up tests
    5. Why the discussion converged
    6. Educational disclaimer
    Use concise Markdown.
    """.strip()
    onc_part = oncologist_llm.invoke([SystemMessage(content=SUMMARY_SYSTEM), HumanMessage(content=onc_input)]).content
    return onc_part

