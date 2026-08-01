from tumor_board.agents import ask
from tumor_board.prompts import CASE_FIDELITY_RULES
from tumor_board.state import TumorBoardState


def pathologist_independent_assessment_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "pathologist_independent_assessment": ask(
            "pathologist",
            "Before the tumor board discussion, write your independent pathology "
            "assessment of the case packet. Ground your answer in the pathology "
            "report and source image captions. Do not respond to the oncologist.\n\n"
            f"{CASE_FIDELITY_RULES}\n\n"
            f"{state['case_packet']}",
            node="pathologist_independent_assessment",
        )
    }


def oncologist_independent_assessment_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "oncologist_independent_assessment": ask(
            "oncologist",
            "Before the tumor board discussion, write your independent oncology "
            "assessment of the case packet. Focus on clinical stage, treatment "
            "intent, initial treatment direction, and pathology details you may "
            "need clarified. Do not respond to the pathologist.\n\n"
            f"{CASE_FIDELITY_RULES}\n\n"
            f"{state['case_packet']}",
            images=state["oncologist_images"],
            node="oncologist_independent_assessment",
        )
    }


def pathologist_opening_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "pathologist_opening": ask(
            "pathologist",
            "Round 1 - Pathologist opens. Present the pathology interpretation: "
            "tumor type, grade, biomarkers, margins, and uncertainties. Do not "
            "choose treatment.\n\n"
            f"{CASE_FIDELITY_RULES}\n\n"
            f"Case packet:\n{state['case_packet']}\n\n"
            "Your independent pathology assessment:\n"
            f"{state['pathologist_independent_assessment']}",
            node="pathologist_opening",
        )
    }


def oncologist_response_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "oncologist_response": ask(
            "oncologist",
            "Round 2 - Oncologist responds. Acknowledge the pathology, state your "
            "initial treatment hypothesis, and ask at least one specific pathology "
            "clarification that could change treatment.\n\n"
            f"{CASE_FIDELITY_RULES}\n\n"
            f"Case packet:\n{state['case_packet']}\n\n"
            "Your independent oncology assessment:\n"
            f"{state['oncologist_independent_assessment']}\n\n"
            f"Pathologist opening:\n{state['pathologist_opening']}",
            images=state["oncologist_images"],
            node="oncologist_response",
        )
    }


def pathologist_reply_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "pathologist_reply": ask(
            "pathologist",
            "Round 3 - Pathologist replies. Answer the oncologist's pathology "
            "question and raise any pathology finding that complicates or qualifies "
            "the proposed plan. If the question asks about a feature that is not "
            "reported, explicitly say it is not reported / cannot be assessed from "
            "the provided core biopsy; do not supply a grade, pattern, extent, or "
            "presence for that feature.\n\n"
            f"{CASE_FIDELITY_RULES}\n\n"
            f"Case packet:\n{state['case_packet']}\n\n"
            f"Oncologist response:\n{state['oncologist_response']}",
            node="pathologist_reply",
        )
    }


def oncologist_revision_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "oncologist_revision": ask(
            "oncologist",
            "Round 4 - Oncologist's joint summary contribution. Based on the full "
            "discussion so far, write the oncology portion of the joint tumor board "
            "summary. Structure your output as:\n"
            "1. What changed from your initial assessment and why.\n"
            "2. Final treatment recommendation with rationale (staging, intent, "
            "first-line regimen, sequencing).\n"
            "3. Key clinical uncertainties that remain.\n"
            "4. Follow-up tests or staging workup you are requesting.\n\n"
            "Do not introduce findings not explicitly reported in the case packet. "
            "Use 'not reported' for missing pathology details rather than inferring "
            "absence.\n\n"
            f"{CASE_FIDELITY_RULES}\n\n"
            f"Case packet:\n{state['case_packet']}\n\n"
            f"Oncologist response:\n{state['oncologist_response']}\n\n"
            f"Pathologist reply:\n{state['pathologist_reply']}",
            images=state["oncologist_images"],
            node="oncologist_revision",
        )
    }


def pathologist_final_contribution_node(state: TumorBoardState) -> dict[str, str]:
    # Runs in parallel with oncologist_revision_node - does NOT see the
    # oncologist's final summary so both contributions are independent.
    return {
        "pathologist_final_contribution": ask(
            "pathologist",
            "Summary contribution — Pathologist. Based on the full board discussion "
            "below, write your independent pathology portion of the joint summary. "
            "Structure your output as:\n"
            "1. Final diagnosis and key pathology findings.\n"
            "2. Biomarker interpretation and clinical implications.\n"
            "3. Pathology uncertainties that remain (unreported findings, "
            "specimens needed).\n"
            "4. Follow-up pathology tests you are recommending.\n\n"
            "Do not choose treatment. Do not speculate about findings not in the "
            "report.\n\n"
            f"{CASE_FIDELITY_RULES}\n\n"
            f"Case packet:\n{state['case_packet']}\n\n"
            f"Pathologist opening (Round 1):\n{state['pathologist_opening']}\n\n"
            f"Oncologist response (Round 2):\n{state['oncologist_response']}\n\n"
            f"Pathologist reply (Round 3):\n{state['pathologist_reply']}",
            node="pathologist_final_contribution",
        )
    }


def consistency_check_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "consistency_check": ask(
            "board_chair",
            "Both specialist summary contributions are provided below, along with "
            "the original case packet. Validate them:\n\n"
            "Case packet (ground truth):\n"
            f"{state['case_packet']}\n\n"
            "Oncologist summary contribution:\n"
            f"{state['oncologist_revision']}\n\n"
            "Pathologist summary contribution:\n"
            f"{state['pathologist_final_contribution']}\n\n"
            "Your validation should cover:\n"
            "1. Unsupported or contradicted statements — anything either specialist "
            "stated that is not in the case packet or conflicts with it.\n"
            "2. Unresolved disagreements — material differences between the two "
            "contributions that were not reconciled during discussion.\n"
            "3. Completeness — whether the two contributions together form an "
            "actionable board decision, or whether critical gaps remain.\n\n"
            "If both contributions are internally consistent and case-grounded, "
            "say so briefly. Do not re-summarize findings that are correct.",
            node="consistency_check",
        )
    }


def final_summary_node(state: TumorBoardState) -> dict[str, str]:
    return {
        "final_summary": (
            "─── Oncology contribution ───\n"
            f"{state['oncologist_revision']}\n\n"
            "─── Pathology contribution ───\n"
            f"{state['pathologist_final_contribution']}\n\n"
            "─── Board chair consistency check ───\n"
            f"{state['consistency_check']}\n\n"
        )
    }
