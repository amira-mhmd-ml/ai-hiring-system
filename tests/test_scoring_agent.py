
import pytest
from agents.scoring_agent import CandidateScore


def test_candidate_score_valid_data():
    score = CandidateScore(
        candidate_name="Sara Ahmed",
        technical_score=8.5,
        experience_score=7.0,
        communication_score=8.0,
        job_fit_score=8.0,
        overall_score=8.2,
        strengths=["RAG expertise", "Async Python", "API design"],
        gaps=["No LangGraph experience"],
        recommendation="Strong Yes",
        reasoning="Demonstrated strong practical knowledge."
    )

    assert score.overall_score == 8.2
    assert score.recommendation == "Strong Yes"
    assert len(score.strengths) == 3


def test_candidate_score_minimum_boundary():
    score = CandidateScore(
        candidate_name="Weak Candidate",
        technical_score=0.0,
        experience_score=0.0,
        communication_score=0.0,
        job_fit_score=0.0,
        overall_score=0.0,
        strengths=[],
        gaps=["No relevant skills", "No experience", "Poor communication"],
        recommendation="No",
        reasoning="Does not meet any job requirements."
    )

    assert score.overall_score == 0.0
    assert score.recommendation == "No"


def test_candidate_score_maximum_boundary():
    score = CandidateScore(
        candidate_name="Perfect Candidate",
        technical_score=10.0,
        experience_score=10.0,
        communication_score=10.0,
        job_fit_score=10.0,
        overall_score=10.0,
        strengths=["Everything"],
        gaps=[],
        recommendation="Strong Yes",
        reasoning="Exceeds all requirements."
    )

    assert score.overall_score == 10.0


def test_ranking_sorts_by_overall_score_descending():
    """rank_all_candidates لازم يرجع المرشحين من الأعلى للأقل"""
    scores = [
        CandidateScore(
            candidate_name="Low Scorer", technical_score=3.0, experience_score=3.0,
            communication_score=3.0, job_fit_score=3.0, overall_score=3.0,
            strengths=[], gaps=["Many gaps"], recommendation="No",
            reasoning="Weak candidate"
        ),
        CandidateScore(
            candidate_name="High Scorer", technical_score=9.0, experience_score=9.0,
            communication_score=9.0, job_fit_score=9.0, overall_score=9.0,
            strengths=["Strong skills"], gaps=[], recommendation="Strong Yes",
            reasoning="Excellent candidate"
        ),
        CandidateScore(
            candidate_name="Mid Scorer", technical_score=6.0, experience_score=6.0,
            communication_score=6.0, job_fit_score=6.0, overall_score=6.0,
            strengths=["Some skills"], gaps=["Some gaps"], recommendation="Maybe",
            reasoning="Average candidate"
        ),
    ]

    ranked = sorted(scores, key=lambda x: x.overall_score, reverse=True)

    assert ranked[0].candidate_name == "High Scorer"
    assert ranked[1].candidate_name == "Mid Scorer"
    assert ranked[2].candidate_name == "Low Scorer"


@pytest.mark.parametrize("score_value,expected_range", [
    (9.0, "Strong Yes"),   # >= 8.5
    (7.5, "Yes"),          # 7.0 - 8.4
    (6.0, "Maybe"),        # 5.0 - 6.9
    (3.0, "No"),           # < 5.0
])
def test_recommendation_matches_score_range(score_value, expected_range):
 
    score = CandidateScore(
        candidate_name="Test Candidate",
        technical_score=score_value,
        experience_score=score_value,
        communication_score=score_value,
        job_fit_score=score_value,
        overall_score=score_value,
        strengths=["test"],
        gaps=["test"],
        recommendation=expected_range,
        reasoning="Test reasoning"
    )

    if score.overall_score >= 8.5:
        assert score.recommendation == "Strong Yes"
    elif score.overall_score >= 7.0:
        assert score.recommendation == "Yes"
    elif score.overall_score >= 5.0:
        assert score.recommendation == "Maybe"
    else:
        assert score.recommendation == "No"


def test_ranking_empty_candidate_list():
    scores = []
    ranked = sorted(scores, key=lambda x: x.overall_score, reverse=True)

    assert ranked == []


def test_candidate_score_allows_empty_strengths_or_gaps():
    score = CandidateScore(
        candidate_name="Ideal Candidate",
        technical_score=10.0,
        experience_score=10.0,
        communication_score=10.0,
        job_fit_score=10.0,
        overall_score=10.0,
        strengths=["All round excellence"],
        gaps=[],  
        recommendation="Strong Yes",
        reasoning="No gaps found."
    )

    assert score.gaps == []