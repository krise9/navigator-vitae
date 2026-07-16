import json

import streamlit as st

from engines.database import has_completed_behavior, save_response
from engines.mbti_engine import calculate_mbti
from engines.registry import get_person


MODULE_VERSION = "v0.1"
QUESTIONS_FILE = "questions/mbti.json"


def load_mbti_questions() -> list[dict]:
    """Laadt de MBTI-vragen uit het JSON-bestand."""
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def render_admin_result(result: dict, navigator_id: str, full_name: str) -> None:
    """Toont het resultaat van de huidige inzending aan de Navigator."""
    st.divider()
    st.subheader("Admin-weergave")

    st.write("Navigator ID:", navigator_id)
    st.write("Naam:", full_name)
    st.metric("Type", result["type"])

    st.markdown("### Ruwe scores")
    st.json(result["scores"])

    axis_positions = result["axis_positions"]

    # De bestaande engine gebruikt:
    # I_E: 0 = I, 100 = E
    # S_N: 0 = S, 100 = N
    # T_F: 0 = T, 100 = F
    # J_P: 0 = J, 100 = P
    introversion = 100 - axis_positions["I_E"]
    extraversion = axis_positions["I_E"]

    sensing = 100 - axis_positions["S_N"]
    intuition = axis_positions["S_N"]

    thinking = 100 - axis_positions["T_F"]
    feeling = axis_positions["T_F"]

    judging = 100 - axis_positions["J_P"]
    perceiving = axis_positions["J_P"]

    st.markdown("### Denk- en gedragsassen")

    axes = [
        ("Introversie", introversion),
        ("Extraversie", extraversion),
        ("Sensing", sensing),
        ("Intuïtie", intuition),
        ("Thinking", thinking),
        ("Feeling", feeling),
        ("Judging", judging),
        ("Perceiving", perceiving),
    ]

    for label, value in axes:
        value = max(0.0, min(100.0, float(value)))
        st.write(f"{label}: {value:.1f}%")
        st.progress(value / 100)


def render_mbti_module() -> None:
    """Rendert de volledige Module 2-flow."""
    st.title("Navigator Vitae")
    st.subheader(
        f"Module 2: Denk- en gedragsvoorkeuren {MODULE_VERSION}"
    )

    questions = load_mbti_questions()

    navigator_id = st.text_input(
        "Navigator ID",
        placeholder="Bijvoorbeeld: NV-2026-000001",
        key="mbti_navigator_id",
    ).strip()

    if not navigator_id:
        return

    try:
        person = get_person(navigator_id)
    except Exception as error:
        st.error("De verbinding met de deelnemersdatabase is mislukt.")
        st.exception(error)
        return

    if not person:
        st.error("Navigator ID niet gevonden.")
        return

    first_name = person.get("first_name", "")
    last_name = person.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()

    st.success(f"Welkom, {first_name}.")
    st.caption(f"Navigator ID: {navigator_id}")

    try:
        already_completed = has_completed_behavior(navigator_id)
    except Exception as error:
        st.error("De eerdere deelname kon niet worden gecontroleerd.")
        st.exception(error)
        return

    if already_completed:
        st.warning(
            "Deze module werd al ingevuld voor deze Navigator ID. "
            "Neem contact op met de Navigator als een nieuwe deelname nodig is."
        )
        return

    st.info(
        """
        Er bestaan geen goede of foute antwoorden.

        Kies telkens het antwoord dat het meest spontaan bij je past,
        niet het antwoord waarvan je vindt dat je het zou moeten kiezen.
        """
    )

    st.write(f"Aantal vragen: {len(questions)}")

    answers = {}

    for index, question in enumerate(questions, start=1):
        st.markdown(f"### Vraag {index} van {len(questions)}")

        choice = st.radio(
            question["text"],
            ["A", "B"],
            index=None,
            format_func=lambda option, q=question: q[option],
            key=f"mbti_answer_{question['id']}",
        )

        answers[question["id"]] = choice

    if not st.button(
        "Verzenden",
        type="primary",
        key="submit_mbti",
    ):
        return

    unanswered = [
        question["id"]
        for question in questions
        if answers.get(question["id"]) is None
    ]

    if unanswered:
        st.error(
            f"Je hebt nog {len(unanswered)} vragen niet beantwoord."
        )
        return

    try:
        result = calculate_mbti(answers, questions)
        save_response(navigator_id, result)
    except Exception as error:
        st.error("Het resultaat kon niet worden opgeslagen.")
        st.exception(error)
        return

    st.success("Bedankt. Je antwoorden zijn opgeslagen.")

    st.session_state["last_result"] = result
    st.session_state["last_navigator_id"] = navigator_id
    st.session_state["last_person_name"] = full_name

    admin_code = st.text_input(
        "Admin code",
        type="password",
        key="mbti_admin_code",
    )

    if admin_code == "kris123":
        render_admin_result(
            result=result,
            navigator_id=navigator_id,
            full_name=full_name,
        )