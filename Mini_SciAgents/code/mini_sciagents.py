import os
import json
import time
from typing import List
import networkx as nx
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# OPERATIONAL CONFIGURATION
# ---------------------------------------------------------------------------
MOCK_MODE = False  # SET TO TRUE TO TEST WITHOUT API TOKENS
MODEL_ID = "gemini-2.5-flash"

# Initialize Client 
client = None
if not MOCK_MODE:
    if "GEMINI_API_KEY" not in os.environ:
        raise ValueError("Please set the GEMINI_API_KEY environment variable.")
    client = genai.Client()

# ---------------------------------------------------------------------------
# 2. DEFINE THE STRUCTURED OUTPUT DATA SCHEMAS (PYDANTIC)
# ---------------------------------------------------------------------------
class HypothesisGeneratorOutput(BaseModel):
    discovered_path: List[str] = Field(description="The list of nodes linking the start and end concept.")
    core_hypothesis: str = Field(description="The central bridge hypothesis linking the target nodes across domains.")
    scientific_rationale: str = Field(description="Initial explanatory logic for why this relationship could exist.")

class ExpanderOutput(BaseModel):
    hypothesis_summary: str = Field(description="The validated hypothesis from Agent 1.")
    proposed_mechanism: str = Field(description="A deep, step-by-step biological or signaling pathway mechanism.")
    experimental_test: str = Field(description="A specific, actionable experiment to test it.")
    vulnerable_assumptions: List[str] = Field(description="Flaws, unproven logical leaps, or fragile assumptions.")

class CriticOutput(BaseModel):
    strongest_element: str = Field(description="The most biologically plausible or structurally sound part of the mechanism.")
    weakest_element: str = Field(description="The biggest logical gap or alternative explanation that ruins the hypothesis.")
    validation_requirements: List[str] = Field(description="What data points or experimental controls must be true for this to hold.")
    final_verdict: str = Field(description="A critical assessment of novelty and viability.")

# ---------------------------------------------------------------------------
# 3. BUILD THE KNOWLEDGE GRAPH (at least 30 Nodes and 50 Edges)
# ---------------------------------------------------------------------------
def build_scientific_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    nodes = [
        "Sleep Deprivation", "Slow-Wave Sleep", "REM Sleep Disruption", "Circadian Rhythm",
        "Locus Coeruleus", "Hypothalamus", "Suprachiasmatic Nucleus", "Pineal Gland",
        "Melatonin", "Cortisol", "Norepinephrine", "Adenosine", "GABA",
        "HPA Axis", "Sympathetic Nervous System", "Vagus Nerve",
        "Blood-Brain Barrier", "Microglial Activation", "Astrocytes", "Glymphatic System",
        "NF-kB Pathway", "Oxidative Stress", "Mitochondrial Dysfunction", "SIRT1", "AMPK",
        "Pro-inflammatory Cytokines", "Anti-inflammatory Cytokines", "IL-6", "TNF-alpha", 
        "Natural Killer Cells", "T-Helper Cells (Th1)", "Regulatory T-cells (Tregs)", "Dendritic Cells"
    ]
    G.add_nodes_from(nodes)
    
    edges = [
        ("Sleep Deprivation", "HPA Axis", "hyperactivates"),
        ("Sleep Deprivation", "Sympathetic Nervous System", "upregulates"),
        ("Sleep Deprivation", "REM Sleep Disruption", "induces"),
        ("Sleep Deprivation", "Slow-Wave Sleep", "suppresses"),
        ("Sleep Deprivation", "Circadian Rhythm", "desynchronizes"),
        ("Sleep Deprivation", "Adenosine", "accumulates"),
        ("Sleep Deprivation", "Glymphatic System", "impairs"),
        ("Sleep Deprivation", "Blood-Brain Barrier", "disrupts_permeability_of"),
        ("Circadian Rhythm", "Suprachiasmatic Nucleus", "governed_by"),
        ("Suprachiasmatic Nucleus", "Pineal Gland", "signals_to"),
        ("Pineal Gland", "Melatonin", "secretes"),
        ("Sleep Deprivation", "Melatonin", "attenuates"),
        ("Melatonin", "Oxidative Stress", "scavenges"),
        ("Melatonin", "SIRT1", "upregulates"),
        ("HPA Axis", "Cortisol", "triggers_release_of"),
        ("Sympathetic Nervous System", "Norepinephrine", "releases"),
        ("Locus Coeruleus", "Norepinephrine", "modulates"),
        ("Sleep Deprivation", "Locus Coeruleus", "overstimulates"),
        ("Glymphatic System", "Oxidative Stress", "fails_to_clear"),
        ("Blood-Brain Barrier", "Microglial Activation", "permits_periphery_infiltration_causing"),
        ("Microglial Activation", "Pro-inflammatory Cytokines", "secretes"),
        ("Microglial Activation", "Astrocytes", "cross_talks_with"),
        ("Astrocytes", "GABA", "modulates_clearance_of"),
        ("Norepinephrine", "NF-kB Pathway", "activates"),
        ("Oxidative Stress", "NF-kB Pathway", "induces"),
        ("Oxidative Stress", "Mitochondrial Dysfunction", "accelerates"),
        ("Mitochondrial Dysfunction", "AMPK", "triggers"),
        ("SIRT1", "NF-kB Pathway", "inhibits"),
        ("AMPK", "SIRT1", "phosphorylates/activates"),
        ("NF-kB Pathway", "Pro-inflammatory Cytokines", "transcribes"),
        ("Pro-inflammatory Cytokines", "IL-6", "includes"),
        ("Pro-inflammatory Cytokines", "TNF-alpha", "includes"),
        ("Cortisol", "Anti-inflammatory Cytokines", "acutely_stimulates"),
        ("Cortisol", "T-Helper Cells (Th1)", "suppresses"),
        ("Cortisol", "Regulatory T-cells (Tregs)", "downregulates_chronic_exposure"),
        ("TNF-alpha", "Natural Killer Cells", "modulates_cytotoxicity_of"),
        ("IL-6", "Natural Killer Cells", "alters_receptor_expression_on"),
        ("Norepinephrine", "Natural Killer Cells", "downregulates_via_beta_receptors"),
        ("Regulatory T-cells (Tregs)", "Natural Killer Cells", "restrains"),
        ("T-Helper Cells (Th1)", "Natural Killer Cells", "potentiates_via_IL-2"),
        ("Cortisol", "Dendritic Cells", "inhibits_maturation_of"),
        ("Dendritic Cells", "T-Helper Cells (Th1)", "fails_to_prime"),
        ("Vagus Nerve", "Anti-inflammatory Cytokines", "stimulates_via_cholinergic_pathway"),
        ("Sleep Deprivation", "Vagus Nerve", "depresses_tone_of"),
        ("REM Sleep Disruption", "HPA Axis", "sensitizes"),
        ("Slow-Wave Sleep", "Glymphatic System", "maximizes"),
        ("IL-6", "HPA Axis", "cross_talks_positive_feedback_to"),
        ("TNF-alpha", "Blood-Brain Barrier", "compromises"),
        ("Adenosine", "GABA", "co-modulates_sleep_homeostasis_with"),
        ("SIRT1", "Mitochondrial Dysfunction", "protects_against"),
        ("AMPK", "NF-kB Pathway", "indirectly_attenuates"),
        ("Pro-inflammatory Cytokines", "Circadian Rhythm", "disrupts_clock_genes_via"),
        ("Dendritic Cells", "Regulatory T-cells (Tregs)", "induces_differentiation_of"),
        ("IL-6", "Regulatory T-cells (Tregs)", "inhibits_generation_of"),
        ("TNF-alpha", "Oxidative Stress", "amplifies")
    ]
    for u, v, r in edges:
        G.add_edge(u, v, relation=r)
    return G

def audit_graph_requirements(G: nx.DiGraph) -> bool:
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    print("\n========================================================")
    print("KNOWLEDGE GRAPH COMPLIANCE CHECK")
    print("========================================================")
    print(f"Nodes: {num_nodes} (Requirement: ≥30) -> {'PASS' if num_nodes >= 30 else 'FAIL'}")
    print(f"Edges: {num_edges} (Requirement: ≥50) -> {'PASS' if num_edges >= 50 else 'FAIL'}")
    print("========================================================\n")
    return num_nodes >= 30 and num_edges >= 50

# ---------------------------------------------------------------------------
# 4. MULTI-AGENT PIPELINE 
# ---------------------------------------------------------------------------
def run_sciagents_pipeline(start_node: str, end_node: str, graph: nx.DiGraph):
    print(f"PIPELINE RUN: [{start_node}] ↔ [{end_node}]")
    
    try:
        shortest_path = nx.shortest_path(graph, source=start_node, target=end_node)
        path_context = " -> ".join([f"{shortest_path[i]} ({graph[shortest_path[i]][shortest_path[i+1]]['relation']}) -> {shortest_path[i+1]}" for i in range(len(shortest_path)-1)])
        graph_context = f"Direct path found: {path_context}"
    except nx.NetworkXNoPath:
        graph_context = "Non-contiguous mapping context."

    # IF TOKEN LIMIT IS TRIGGERED, RUN SIMULATION
    if MOCK_MODE:
        return {
            "start_concept": start_node,
            "end_concept": end_node,
            "initial_hypothesis": {
                "discovered_path": [start_node, "Intermediary Variable", end_node],
                "core_hypothesis": f"Upregulation of system triggers at {start_node} modulates cellular target behaviors on {end_node}.",
                "scientific_rationale": "Biochemical shifts cross over neurological junctions to influence peripheral immunity."
            },
            "draft_mechanism": {
                "hypothesis_summary": "Simulated local path response",
                "proposed_mechanism": f"Pathway activations from {start_node} alter signaling expressions changing performance profiles.",
                "experimental_test": "Flow cytometry mapping variant assay targets over controlled trial populations.",
                "vulnerable_assumptions": ["Assumes translational conservation from murine models."]
            },
            "critic_peer_review": {
                "strongest_element": "Clear operationalized assay endpoint tracking.",
                "weakest_element": "Lacks specific separation from systemic glucocorticoid backgrounds.",
                "validation_requirements": ["Isolate hormone tracking controls."],
                "final_verdict": "High structural novelty baseline confirmed."
            }
        }

# --- AGENT 1: HYPOTHESIS GENERATOR ---
    print("  [Agent 1] Generating core hypothesis...")
    prompt_agent1 = f"""
    You are a sophisticated neuroimmunologist and computational biologist trained in advanced cross-disciplinary scientific research and innovation. 
    Your objective is to deeply analyze the provided knowledge graph topology connecting the neurological concept '{start_node}' and the immunological concept '{end_node}'.
    
    Graph Context: {graph_context}
    
    Do not simply restate obvious correlations. Instead, identify the molecular conduits, neuroendocrine signaling cascades, or epigenetic shifts that bridge these two distinct physiological domains.
    Craft a detailed, groundbreaking research hypothesis investigating a hidden mechanistic link that incorporates both core concepts. Your creativity in linking these concepts to address unsolved clinical problems or emergent biological behaviors will be highly valued.
    Reference precise receptors, cellular subtypes, or transcription factors.
    """
    response_agent1 = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt_agent1,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=HypothesisGeneratorOutput, temperature=0.3)
    )
    agent1_data = response_agent1.parsed

    # --- AGENT 2: EXPANDER ---
    print("  [Agent 2] Expanding biological mechanism...")
    prompt_agent2 = f"""
    You are a senior molecular biologist, immunologist, and experimental assay designer. 
    Your task is to take the upstream hypothesis generated by Agent 1 and drastically enrich it with a concrete, multi-scale biological pathway execution model.
    
    Upstream Output Context:
    {json.dumps(agent1_data.model_dump(), indent=2)}
    
    1. Propose a deep, step-by-step intracellular and intercellular pathway mechanism. Explain the exact cascade from central neural disruption down to peripheral cellular dysfunction. Be specific across all scales, from the molecular/genetic level to macroscale physiological profiles.
    2. Propose an actionable, high-impact empirical testing framework (such as in vitro models, in vivo assays, flow cytometry, or RNA-seq) capable of evaluating this exact hypothesis.
    3. Rigorously extract and flag the hidden unproven assumptions or model translation vulnerabilities.
    """
    response_agent2 = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt_agent2,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=ExpanderOutput, temperature=0.2)
    )
    agent2_data = response_agent2.parsed

    # --- AGENT 3: CRITIC ---
    print("  [Agent 3] Executing scientific critique...")
    prompt_agent3 = f"""
    You are a notoriously strict, expert peer-reviewer for top-tier journals like Nature Immunology and The Journal of Neuroscience. 
    Your mission is to execute a brutal, logical sanity check on the expanded hypothesis and mechanism provided by Agent 2. 
    
    Upstream Output Context:
    {json.dumps(agent2_data.model_dump(), indent=2)}
    
    1. Identify the strongest element where the biological pathway aligns flawlessly with established medical literature.
    2. Pinpoint the weakest element—isolate the fatal logical gaps, unaddressed confounding variables, or alternative biochemical explanations that could invalidate the hypothesis.
    3. List explicit validation requirements, specifying the precise positive and negative experimental controls that must be true for this hypothesis to hold weight.
    """
    response_agent3 = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt_agent3,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=CriticOutput, temperature=0.1)
    )
    agent3_data = response_agent3.parsed

    return {
        "start_concept": start_node,
        "end_concept": end_node,
        "initial_hypothesis": agent1_data.model_dump(),
        "draft_mechanism": agent2_data.model_dump(),
        "critic_peer_review": agent3_data.model_dump()
    }

# ---------------------------------------------------------------------------
# 5. MULTI-PAIR EVALUATION (3 RUNS)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    bio_graph = build_scientific_graph()
    
    if audit_graph_requirements(bio_graph):
        concept_pairs = [
            ("Sleep Deprivation", "Natural Killer Cells"),
            ("REM Sleep Disruption", "Microglial Activation"),
            ("Glymphatic System", "Dendritic Cells")
        ]
        
        all_evaluation_runs = {}
        
        for idx, (start, end) in enumerate(concept_pairs, 1):
            print(f"STARTING EVALUATION RUN {idx} OF 3")
            run_key = f"run_{idx}_{start.lower().replace(' ', '_')}_to_{end.lower().replace(' ', '_')}"
            
            run_results = run_sciagents_pipeline(start, end, bio_graph)
            all_evaluation_runs[run_key] = run_results
            print(f" Run {idx} evaluated successfully.")
            
            if not MOCK_MODE and idx < len(concept_pairs):
                print("Sleeping for 20 seconds to prevent rate limiting...")
                time.sleep(20) 

        output_file = "sciagents_3_pair_evaluation.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_evaluation_runs, f, indent=4, ensure_ascii=False)
            
        print(f"SUCCESS: All 3 concept pairs processed! Data stored in '{output_file}'.")