
# الاستخدام:
#   python demo.py path/to/cv1.pdf path/to/cv2.pdf ...
# ============================================================

import asyncio
import sys
from agents.orchestrator import run_hiring_system


SAMPLE_JOB_DESCRIPTION = """
Senior AI Engineer
Requirements: LangChain, LangGraph, FastAPI, Production AI Systems, 4+ years experience
Responsibilities: Build and deploy AI agents, design multi-agent systems
"""


async def main():
    if len(sys.argv) < 2:
        print("Usage: python demo.py path/to/cv1.pdf [path/to/cv2.pdf ...]")
        print("\nNo CVs provided — running with no files will fail at CV Analysis stage,")
        print("which is the expected, handled behavior (see route_after_cv_analysis).")
        sys.exit(1)

    cv_paths = sys.argv[1:]

    print(f"Running demo with {len(cv_paths)} CV(s)...")
    print(f"Job description: {SAMPLE_JOB_DESCRIPTION.strip()[:80]}...\n")

    report = await run_hiring_system(
        job_description=SAMPLE_JOB_DESCRIPTION,
        cv_paths=cv_paths
    )

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())