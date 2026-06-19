import asyncio
import glob
import sys
from typing import List, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.cv_analyzer import CVAnalysis, analyze_all_cvs
from agents.interview_agent import run_interview
from agents.scoring_agent import CandidateScore, rank_all_candidates
from agents.report_writer import HiringReport, generate_hiring_report, format_report


class HiringSystemState(TypedDict):
    job_description: str
    cv_paths: List[str]

    cv_analyses: List[CVAnalysis]
    interview_results: List[dict]
    candidate_scores: List[CandidateScore]
    final_report: str

    current_stage: str
    errors: List[str]


async def cv_analysis_node(state: HiringSystemState) -> HiringSystemState:
    print("\n" + "="*55)
    print("STAGE 1: CV Analysis")
    print("="*55)

    results = await analyze_all_cvs(state["cv_paths"])

    successful = [r["data"] for r in results if r.get("status") == "success"]
    errors = [f"CV failed: {r['path']} — {r['reason']}" for r in results if r.get("status") == "failed"]

    print(f" Analyzed: {len(successful)} CVs")

    return {
        **state,
        "cv_analyses": successful,
        "errors": state["errors"] + errors,
        "current_stage": "interview"
    }


async def interview_node(state: HiringSystemState) -> HiringSystemState:
    print("\n" + "="*55)
    print("STAGE 2: Interviews")
    print("="*55)

    interview_results = []
    errors = []

    for cv_analysis in state["cv_analyses"]:
        try:
            qa_pairs = await run_interview(cv_analysis, state["job_description"])
            interview_results.append({
                "cv_analysis": {
                    "candidate_name": cv_analysis.candidate_name,
                    "years_of_experience": cv_analysis.years_of_experience,
                    "technical_skills": cv_analysis.technical_skills,
                    "education": cv_analysis.education,
                    "previous_roles": cv_analysis.previous_roles,
                    "strength_summary": cv_analysis.strength_summary,
                    "weakness_summary": cv_analysis.weakness_summary
                },
                "job_description": state["job_description"],
                "interview_qa": qa_pairs
            })
        except Exception as e:
            errors.append(f"Interview failed for {cv_analysis.candidate_name}: {e}")

    print(f"\n Completed: {len(interview_results)} interviews")

    return {
        **state,
        "interview_results": interview_results,
        "errors": state["errors"] + errors,
        "current_stage": "scoring"
    }


async def scoring_node(state: HiringSystemState) -> HiringSystemState:
    print("\n" + "="*55)
    print("STAGE 3: Scoring & Ranking")
    print("="*55)

    ranked_scores = await rank_all_candidates(state["interview_results"])

    print(f" Scored and ranked: {len(ranked_scores)} candidates")

    return {
        **state,
        "candidate_scores": ranked_scores,
        "current_stage": "report"
    }


async def report_node(state: HiringSystemState) -> HiringSystemState:
    print("\n" + "="*55)
    print("STAGE 4: Generating Report")
    print("="*55)

    report = await generate_hiring_report(
        job_description=state["job_description"],
        ranked_candidates=state["candidate_scores"]
    )

    formatted = format_report(report)

    print(" Report ready")

    return {
        **state,
        "final_report": formatted,
        "current_stage": "complete"
    }


def route_after_cv_analysis(state: HiringSystemState) -> str:
    if not state["cv_analyses"]:
        print(" No CVs successfully analyzed. Stopping.")
        return "end"
    return "interview"


def route_after_interviews(state: HiringSystemState) -> str:
    if not state["interview_results"]:
        print(" No interviews completed. Stopping.")
        return "end"
    return "scoring"


def build_hiring_system():
    graph = StateGraph(HiringSystemState)

    graph.add_node("cv_analysis", cv_analysis_node)
    graph.add_node("interview", interview_node)
    graph.add_node("scoring", scoring_node)
    graph.add_node("report", report_node)

    graph.set_entry_point("cv_analysis")

    graph.add_conditional_edges(
        "cv_analysis",
        route_after_cv_analysis,
        {"interview": "interview", "end": END}
    )

    graph.add_conditional_edges(
        "interview",
        route_after_interviews,
        {"scoring": "scoring", "end": END}
    )

    graph.add_edge("scoring", "report")
    graph.add_edge("report", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


async def run_hiring_system(
    job_description: str,
    cv_paths: List[str]
) -> str:

    print("\n AI Hiring System Starting...")
    print(f"   Job: {job_description[:60]}...")
    print(f"   CVs: {len(cv_paths)} files")

    system = build_hiring_system()

    initial_state: HiringSystemState = {
        "job_description": job_description,
        "cv_paths": cv_paths,
        "cv_analyses": [],
        "interview_results": [],
        "candidate_scores": [],
        "final_report": "",
        "current_stage": "cv_analysis",
        "errors": []
    }

    config = {"configurable": {"thread_id": "hiring-session-001"}}
    final_state = await system.ainvoke(initial_state, config)

    if final_state["errors"]:
        print(f"\n {len(final_state['errors'])} error(s) encountered:")
        for error in final_state["errors"]:
            print(f"   └─ {error}")

    return final_state["final_report"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m agents.orchestrator path/to/cvs/")
        sys.exit(1)

    cv_folder = sys.argv[1]
    cv_files = glob.glob(f"{cv_folder}/*.pdf")

    if not cv_files:
        print(f"❌ No PDF files found in: {cv_folder}")
        sys.exit(1)

    job_desc = input("Enter job description: ").strip()

    report = asyncio.run(run_hiring_system(job_desc, cv_files))
    print(report)