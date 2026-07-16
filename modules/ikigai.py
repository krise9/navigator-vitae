import json

import streamlit as st

from engines.ikigai_database import (
    has_completed_ikigai,
    load_ikigai_responses,
    save_ikigai_responses,
)
from engines.registry import get_person


MODULE_VERSION = "v1.1.2"
QUESTIONS_FILE = "questions/ikigai.json"


def load_ikigai_questions() -> list[dict]:
    """Laadt de Ikigai-vragen uit JSON."""
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def render_completed_state(
    navigator_id: str,
    first_name: str,
) -> None:
    """Toont de status wanneer de module al werd afgerond."""
    st.success(f"Welkom, {first_name}.")
    st.caption(f"Navigator ID: {navigator_id}")

    st.warning(
        "Deze module werd al ingevuld voor deze Navigator ID. "
        "Neem contact op met de Navigator als een nieuwe deelname nodig is."
    )


def render_existing_answers(navigator_id: str) -> None:
    """
    Toont bestaande antwoorden alleen wanneer de Navigator
    daar expliciet toegang toe geeft.
    """
    admin_code = st.text_input(
        "Admin code",
        type="password",
        key="ikigai_admin_code",
    )

    if admin_code != "kris123":
        return

    try:
        answers = load_ikigai_responses(navigator_id)
    except Exception as error:
        st.error("De opgeslagen antwoorden konden niet worden geladen.")
        st.exception(error)
        return

    if not answers:
        st.info("Geen opgeslagen antwoorden gevonden.")
        return

    st.divider()
    st.subheader("Admin-weergave")

    questions = load_ikigai_questions()
    questions_by_id = {
        question["id"]: question
        for question in questions
    }

    for question_id, answer in answers.items():
        question = questions_by_id.get(question_id)

        if not question:
            continue

        st.markdown(f"### {question_id}")
        st.write(question["text"])
        st.info(answer)


def render_ikigai_module() -> None:
    """Rendert de volledige Ikigai-module."""
    st.title("Navigator Vitae")
    st.subheader(
        f"Module 1: Levensrichting {MODULE_VERSION}"
    )

    questions = load_ikigai_questions()

    navigator_id = st.text_input(
        "Navigator ID",
        placeholder="Bijvoorbeeld: NV-2026-000001",
        key="ikigai_navigator_id",
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

    try:
        already_completed = has_completed_ikigai(navigator_id)
    except Exception as error:
        st.error("De eerdere deelname kon niet worden gecontroleerd.")
        st.exception(error)
        return

    if already_completed:
        render_completed_state(
            navigator_id=navigator_id,
            first_name=first_name,
        )

        render_existing_answers(navigator_id)
        return

    st.success(f"Welkom, {first_name}.")
    st.caption(f"Navigator ID: {navigator_id}")

    st.info(
        """
        Deze vragen gaan over wat je energie geeft, waar je sterk in bent,
        welke bijdrage je wilt leveren en welke richting mogelijk bij je past.

        Er bestaan geen juiste of foute antwoorden.

        Geef bij voorkeur concrete voorbeelden en situaties.
        Schrijf spontaan, maar voldoende uitgebreid om je antwoord begrijpelijk
        te maken voor iemand die jou nog niet goed kent.
        """
    )

    st.write(f"Aantal vragen: {len(questions)}")

    answers: dict[str, str] = {}

    for index, question in enumerate(questions, start=1):
        st.markdown(f"### Vraag {index} van {len(questions)}")
        st.write(question["text"])

        answer = st.text_area(
            label="Jouw antwoord",
            key=f"ikigai_answer_{question['id']}",
            height=140,
            label_visibility="collapsed",
        )

        answers[question["id"]] = answer

    if not st.button(
        "Definitief verzenden",
        type="primary",
        key="submit_ikigai",
    ):
        return

    unanswered = [
        question["id"]
        for question in questions
        if not answers.get(question["id"], "").strip()
    ]

    if unanswered:
        st.error(
            f"Je hebt nog {len(unanswered)} vragen niet beantwoord."
        )
        return

    try:
        run_id = save_ikigai_responses(
            navigator_id=navigator_id,
            answers=answers,
        )
    except Exception as error:
        st.error("De antwoorden konden niet worden opgeslagen.")
        st.exception(error)
        return

    st.session_state["ikigai_submitted"] = True
    st.session_state["ikigai_run_id"] = run_id
    st.session_state["ikigai_participant_name"] = full_name

    st.success("Bedankt. Je antwoorden zijn opgeslagen.")

    st.write(
        """
        Je antwoorden worden verwerkt binnen jouw persoonlijke
        Navigator-traject.

        De analyse wordt niet automatisch aan jou getoond.
        Ze wordt eerst inhoudelijk beoordeeld en gekoppeld aan de andere
        Navigator-modules.
        """
    )