import os
import shutil
import uuid
from typing import List

from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from agents.orchestrator import run_hiring_system

load_dotenv()

app = FastAPI(
    title="AI Hiring System",
    description="Automated CV analysis, AI interviews, and candidate ranking",
    version="1.0.0"
)

sessions = {}


@app.post("/upload-cvs")
async def upload_cvs(
    job_description: str = Form(...),
    files: List[UploadFile] = File(...)
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files uploaded"
        )

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(
        "uploads",
        session_id
    )

    os.makedirs(
        session_dir,
        exist_ok=True
    )

    saved_paths = []
    rejected_files = []

    for file in files:

        if not file.filename:
            continue

        if not file.filename.lower().endswith(".pdf"):
            rejected_files.append(
                file.filename
            )
            continue

        safe_filename = os.path.basename(
            file.filename
        )

        file_path = os.path.join(
            session_dir,
            safe_filename
        )

        with open(file_path, "wb") as f:
            shutil.copyfileobj(
                file.file,
                f
            )

        saved_paths.append(file_path)

    if not saved_paths:
        raise HTTPException(
            status_code=400,
            detail=(
                "No valid PDF files found. "
                f"Rejected: {rejected_files}"
            )
        )

    sessions[session_id] = {
        "job_description": job_description,
        "cv_paths": saved_paths,
        "status": "uploaded",
        "report": None,
        "error": None
    }

    return {
        "session_id": session_id,
        "uploaded": len(saved_paths),
        "rejected": rejected_files,
        "message": (
            f"Successfully uploaded "
            f"{len(saved_paths)} CV(s)"
        ),
        "next_step": (
            f"POST /analyze/{session_id}"
        )
    }


@app.post("/analyze/{session_id}")
async def start_analysis(
    session_id: str,
    background_tasks: BackgroundTasks
):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session = sessions[session_id]

    if session["status"] == "processing":
        return {
            "message": "Analysis already in progress",
            "status": "processing"
        }

    if session["status"] == "complete":
        return {
            "message": "Analysis already completed",
            "next_step": (
                f"GET /report/{session_id}"
            )
        }

    sessions[session_id]["status"] = "processing"

    async def run_analysis_task():
        try:
            report = await run_hiring_system(
                job_description=session[
                    "job_description"
                ],
                cv_paths=session[
                    "cv_paths"
                ]
            )

            sessions[session_id][
                "report"
            ] = report

            sessions[session_id][
                "status"
            ] = "complete"

        except Exception as e:
            sessions[session_id][
                "status"
            ] = "failed"

            sessions[session_id][
                "error"
            ] = str(e)

    background_tasks.add_task(
        run_analysis_task
    )

    return {
        "session_id": session_id,
        "status": "processing",
        "message": (
            "Analysis started "
            "in background"
        ),
        "next_step": (
            f"GET /status/{session_id}"
        )
    }


@app.get("/status/{session_id}")
async def get_status(
    session_id: str
):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session = sessions[
        session_id
    ]

    status = session["status"]

    response = {
        "session_id": session_id,
        "status": status
    }

    if status == "complete":
        response["next_step"] = (
            f"GET /report/{session_id}"
        )

    elif status == "failed":
        response["error"] = (
            session.get(
                "error",
                "Unknown error"
            )
        )

    elif status == "processing":
        response["message"] = (
            "Analysis in progress, "
            "please check again "
            "in 30 seconds"
        )

    return response


@app.get("/report/{session_id}")
async def get_report(
    session_id: str
):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    session = sessions[
        session_id
    ]

    if session[
        "status"
    ] != "complete":
        raise HTTPException(
            status_code=400,
            detail=(
                "Report not ready. "
                f"Current status: "
                f"{session['status']}"
            )
        )

    return {
        "session_id": session_id,
        "status": "complete",
        "report": session["report"]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_sessions": len(
            sessions
        )
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )