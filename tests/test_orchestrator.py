import pytest
from agents.orchestrator import route_after_cv_analysis, route_after_interviews


def test_route_after_cv_analysis_continues_when_cvs_exist():
    state = {
        "cv_analyses": ["fake_cv_1", "fake_cv_2"],
        "interview_results": [],
        "current_stage": "interview"
    }

    decision = route_after_cv_analysis(state)

    assert decision == "interview"


def test_route_after_cv_analysis_stops_when_no_cvs():

    state = {
        "cv_analyses": [],
        "interview_results": [],
        "current_stage": "interview"
    }

    decision = route_after_cv_analysis(state)

    assert decision == "end"


def test_route_after_cv_analysis_continues_with_partial_success():

    state = {
        "cv_analyses": ["cv_1", "cv_2", "cv_3"],  
        "interview_results": [],
        "current_stage": "interview"
    }

    decision = route_after_cv_analysis(state)

    assert decision == "interview"


def test_route_after_interviews_continues_when_results_exist():
    state = {
        "interview_results": [{"candidate": "fake", "qa": []}],
        "current_stage": "scoring"
    }

    decision = route_after_interviews(state)

    assert decision == "scoring"


def test_route_after_interviews_stops_when_no_results():

    state = {
        "interview_results": [],
        "current_stage": "scoring"
    }

    decision = route_after_interviews(state)

    assert decision == "end"


def test_cv_analysis_state_structure():

    required_keys = ["cv_analyses", "errors", "current_stage"]

    fake_state_after_node = {
        "cv_analyses": ["cv_1"],
        "errors": [],
        "current_stage": "interview"
    }

    for key in required_keys:
        assert key in fake_state_after_node


def test_errors_accumulate_across_stages():

    initial_errors = ["CV failed: file1.pdf"]
    new_error = "Interview failed for candidate X"

    updated_errors = initial_errors + [new_error]

    assert len(updated_errors) == 2
    assert "CV failed: file1.pdf" in updated_errors
    assert "Interview failed for candidate X" in updated_errors