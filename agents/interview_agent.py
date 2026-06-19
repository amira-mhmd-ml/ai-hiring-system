import asyncio
from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from agents.cv_analyzer import CVAnalysis


class InterviewState(TypedDict):
    candidate_name: str
    cv_analysis: dict
    job_description: str
    questions_asked: List[str]
    answers_given: List[str]
    current_question: str
    interview_complete: bool
    qa_pairs: List[dict]


async def generate_question_node(state: InterviewState) -> InterviewState:
    llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.4 # درجة حرارة أعلى قليلاً لإعطاء مرونة وإبداع في صياغة أسئلة المقابلة
)

    questions_so_far = "\n".join(state["questions_asked"]) or "None yet"
    last_answer = state["answers_given"][-1] if state["answers_given"] else "Interview just started"

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a professional senior technical interviewer.
            Generate ONE smart, specific interview question.
            
            Rules:
            - Ask only ONE question per turn
            - Make it specific to this candidate's background AND the job requirements
            - Don't repeat topics already covered
            - If last answer was shallow, go deeper on that topic
            - If 5 questions have been asked, return exactly: INTERVIEW_COMPLETE
            - Questions should test real understanding, not just definitions
            """
        ),
        (
            "human",
            """
            Job Requirements: {job_description}
            
            Candidate Background: {cv_analysis}
            
            Questions Asked So Far:
            {questions_so_far}
            
            Last Answer Given:
            {last_answer}
            
            Generate the next interview question:
            """
        )
    ])

    chain = prompt | llm
    response = await chain.ainvoke({
        "job_description": state["job_description"],
        "cv_analysis": str(state["cv_analysis"]),
        "questions_so_far": questions_so_far,
        "last_answer": last_answer
    })

    question = response.content.strip()

    if "INTERVIEW_COMPLETE" in question:
        qa_pairs = [
            {"question": q, "answer": a}
            for q, a in zip(state["questions_asked"], state["answers_given"])
        ]
        return {**state, "interview_complete": True, "qa_pairs": qa_pairs}

    return {
        **state,
        "current_question": question,
        "questions_asked": state["questions_asked"] + [question]
    }


async def receive_answer_node(state: InterviewState) -> InterviewState:
    print(f"\n Question: {state['current_question']}")
    print("─" * 50)

    answer = input("👤 Candidate Answer: ").strip()

    if not answer:
        answer = "No answer provided"

    return {
        **state,
        "answers_given": state["answers_given"] + [answer]
    }


def should_continue_interview(state: InterviewState) -> str:
    if state["interview_complete"]:
        return "end"
    return "generate_question"


def build_interview_graph():
    graph = StateGraph(InterviewState)

    graph.add_node("generate_question", generate_question_node)
    graph.add_node("receive_answer", receive_answer_node)

    graph.set_entry_point("generate_question")

    graph.add_edge("generate_question", "receive_answer")

    graph.add_conditional_edges(
        "receive_answer",
        should_continue_interview,
        {
            "generate_question": "generate_question",
            "end": END
        }
    )

    return graph.compile()


async def run_interview(
    cv_analysis: CVAnalysis,
    job_description: str
) -> List[dict]:
    print(f"\n{'='*50}")
    print(f"Starting interview for: {cv_analysis.candidate_name}")
    print(f"{'='*50}")

    interview_graph = build_interview_graph()

    initial_state: InterviewState = {
        "candidate_name": cv_analysis.candidate_name,
        "cv_analysis": {
            "name": cv_analysis.candidate_name,
            "experience": cv_analysis.years_of_experience,
            "skills": cv_analysis.technical_skills,
            "education": cv_analysis.education,
            "roles": cv_analysis.previous_roles,
            "strengths": cv_analysis.strength_summary,
            "weaknesses": cv_analysis.weakness_summary
        },
        "job_description": job_description,
        "questions_asked": [],
        "answers_given": [],
        "current_question": "",
        "interview_complete": False,
        "qa_pairs": []
    }

    final_state = await interview_graph.ainvoke(initial_state)

    print(f"\n Interview completed for {cv_analysis.candidate_name}")
    return final_state["qa_pairs"]


if __name__ == "__main__":
    from agents.cv_analyzer import CVAnalysis

    sample_cv = CVAnalysis(
        candidate_name="Sara Ahmed",
        years_of_experience=3,
        technical_skills=["Python", "LangChain", "FastAPI", "PostgreSQL"],
        education="BSc Computer Science",
        previous_roles=["AI Engineer", "Backend Developer"],
        strength_summary="Strong in LLM applications and API development",
        weakness_summary="Limited experience with large-scale distributed systems"
    )

    job_desc = """
    Senior AI Engineer
    Requirements: LangChain, LangGraph, FastAPI, Production AI Systems, 4+ years experience
    Responsibilities: Build and deploy AI agents, design multi-agent systems
    """

    qa_pairs = asyncio.run(run_interview(sample_cv, job_desc))

    print("\n Interview Summary:")
    for i, pair in enumerate(qa_pairs, 1):
        print(f"\nQ{i}: {pair['question']}")
        print(f"A{i}: {pair['answer']}")