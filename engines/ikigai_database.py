from datetime import datetime
from typing import Dict, Optional

from engines.supabase_client import get_participant, get_supabase


IKIGAI_VERSION = "v1.1.2"


def save_ikigai_responses(
    navigator_id: str,
    answers: Dict[str, str],
) -> str:
    """
    Bewaart één volledige Ikigai-inzending.

    Werkwijze:
    1. Zoekt de deelnemer op.
    2. Maakt één record in ikigai_runs.
    3. Maakt één record per antwoord in ikigai_responses.
    4. Geeft het run_id terug.
    """
    supabase = get_supabase()
    participant = get_participant(navigator_id)

    if participant is None:
        raise ValueError("Participant not found.")

    clean_answers = {
        question_id: answer.strip()
        for question_id, answer in answers.items()
        if answer and answer.strip()
    }

    if not clean_answers:
        raise ValueError("No Ikigai answers provided.")

    run_row = {
        "participant_id": participant["id"],
        "navigator_id": navigator_id.strip(),
        "module_version": IKIGAI_VERSION,
        "status": "completed",
        "started_at": datetime.utcnow().isoformat(),
        "submitted_at": datetime.utcnow().isoformat(),
    }

    run_response = (
        supabase
        .table("ikigai_runs")
        .insert(run_row)
        .execute()
    )

    if not run_response.data:
        raise RuntimeError("Ikigai run could not be created.")

    run_id = run_response.data[0]["id"]

    response_rows = [
        {
            "run_id": run_id,
            "question_id": question_id,
            "answer": answer,
            "created_at": datetime.utcnow().isoformat(),
        }
        for question_id, answer in clean_answers.items()
    ]

    (
        supabase
        .table("ikigai_responses")
        .insert(response_rows)
        .execute()
    )

    return run_id


def has_completed_ikigai(navigator_id: str) -> bool:
    """
    Controleert of deze deelnemer Ikigai v1.1.2 al heeft afgerond.
    """
    supabase = get_supabase()

    response = (
        supabase
        .table("ikigai_runs")
        .select("id")
        .eq("navigator_id", navigator_id.strip())
        .eq("module_version", IKIGAI_VERSION)
        .eq("status", "completed")
        .limit(1)
        .execute()
    )

    return bool(response.data)


def load_ikigai_responses(
    navigator_id: str,
) -> Optional[Dict[str, str]]:
    """
    Laadt de meest recente afgeronde Ikigai-inzending.
    Geeft een dictionary terug:
    {
        "IKI01": "...",
        "IKI02": "...",
        ...
    }
    """
    supabase = get_supabase()

    run_response = (
        supabase
        .table("ikigai_runs")
        .select("id")
        .eq("navigator_id", navigator_id.strip())
        .eq("module_version", IKIGAI_VERSION)
        .eq("status", "completed")
        .order("submitted_at", desc=True)
        .limit(1)
        .execute()
    )

    if not run_response.data:
        return None

    run_id = run_response.data[0]["id"]

    responses = (
        supabase
        .table("ikigai_responses")
        .select("question_id, answer")
        .eq("run_id", run_id)
        .execute()
    )

    return {
        row["question_id"]: row["answer"]
        for row in responses.data
    }