from datetime import datetime

from engines.supabase_client import get_participant, get_supabase


def save_response(navigator_id: str, result: dict) -> None:
    supabase = get_supabase()

    participant = get_participant(navigator_id)

    if participant is None:
        raise ValueError("Participant not found.")

    row = {
        "participant_id": participant["id"],
        "navigator_id": navigator_id.strip(),
        "module_version": "v0.1",
        "mbti_type": result["type"],
        "e_score": result["scores"]["E"],
        "i_score": result["scores"]["I"],
        "s_score": result["scores"]["S"],
        "n_score": result["scores"]["N"],
        "t_score": result["scores"]["T"],
        "f_score": result["scores"]["F"],
        "j_score": result["scores"]["J"],
        "p_score": result["scores"]["P"],
        "ie_position": result["axis_positions"]["I_E"],
        "sn_position": result["axis_positions"]["S_N"],
        "tf_position": result["axis_positions"]["T_F"],
        "jp_position": result["axis_positions"]["J_P"],
        "submitted_at": datetime.utcnow().isoformat(),
    }

    (
        supabase
        .table("behavior_results")
        .insert(row)
        .execute()
    )


def has_completed_behavior(navigator_id: str) -> bool:
    supabase = get_supabase()

    response = (
        supabase
        .table("behavior_results")
        .select("id")
        .eq("navigator_id", navigator_id.strip())
        .eq("module_version", "v0.1")
        .limit(1)
        .execute()
    )

    return bool(response.data)