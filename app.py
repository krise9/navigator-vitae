import json

import streamlit as st

from engines.database import has_completed_behavior, save_response
from engines.mbti_engine import calculate_mbti
from engines.registry import get_person


st.set_page_config(
    page_title="Navigator Vitae",
    page_icon="🧭",
    layout="centered",
)

st.title("Navigator Vitae")
st.subheader("Module 2: Denk- en gedragsvoorkeuren v0.1")

with open("questions/mbti.json", "r", encoding="utf-8") as file:
    questions = json.load(file)

navigator_id = st.text_input(
    "Navigator ID",
    placeholder="Bijvoorbeeld: NV-2026-000001",
).strip()

person = None
full_name = ""

if navigator_id:
    try:
        person = get_person(navigator_id)
    except Exception as error:
        st.error("De verbinding met de deelnemersdatabase is mislukt.")
        st.exception(error)
        st.stop()

    if person:
        first_name = person.get("first_name", "")
        last_name = person.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        st.success(f"Welkom, {first_name}.")
        st.caption(f"Navigator ID: {navigator_id}")
    else:
        st.error("Navigator ID niet gevonden.")

if person:
    try:
        already_completed = has_completed_behavior(navigator_id)
    except Exception as error:
        st.error("De eerdere deelname kon niet worden gecontroleerd.")
        st.exception(error)
        st.stop()

    if already_completed:
        st.warning(
            "Deze module werd al ingevuld voor deze Navigator ID. "
            "Neem contact op met de Navigator als een nieuwe deelname nodig is."
        )
        st.stop()

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
            key=f"answer_{question['id']}",
        )

        answers[question["id"]] = choice

    if st.button("Verzenden", type="primary"):
        unanswered = [
            question["id"]
            for question in questions
            if answers.get(question["id"]) is None
        ]

        if unanswered:
            st.error(
                f"Je hebt nog {len(unanswered)} vragen niet beantwoord."
            )
        else:
            try:
                result = calculate_mbti(answers, questions)
                save_response(navigator_id, result)
            except Exception as error:
                st.error("Het resultaat kon niet worden opgeslagen.")
                st.exception(error)
            else:
                st.success("Bedankt. Je antwoorden zijn opgeslagen.")

                st.session_state["last_result"] = result
                st.session_state["last_navigator_id"] = navigator_id
                st.session_state["last_person_name"] = full_name


st.divider()

admin_code = st.text_input(
    "Admin code",
    type="password",
)

if admin_code == "kris123":
    st.subheader("Admin-weergave")

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]

        st.write(
            "Navigator ID:",
            st.session_state["last_navigator_id"],
        )
        st.write(
            "Naam:",
            st.session_state["last_person_name"],
        )
        st.write(
            "Type:",
            result["type"],
        )

        st.markdown("### Ruwe scores")
        st.json(result["scores"])

        st.markdown("### Asposities")

        axis_positions = result["axis_positions"]

        ie_position = axis_positions["I_E"]
        sn_position = axis_positions["S_N"]
        tf_position = axis_positions["T_F"]
        jp_position = axis_positions["J_P"]

        introversion = 100 - ie_position
        extraversion = ie_position

        sensing = 100 - sn_position
        intuition = sn_position

        thinking = 100 - tf_position
        feeling = tf_position

        judging = 100 - jp_position
        perceiving = jp_position

        st.write(f"Introversie: {introversion:.1f}%")
        st.progress(introversion / 100)

        st.write(f"Extraversie: {extraversion:.1f}%")
        st.progress(extraversion / 100)

        st.write(f"Sensing: {sensing:.1f}%")
        st.progress(sensing / 100)

        st.write(f"Intuïtie: {intuition:.1f}%")
        st.progress(intuition / 100)

        st.write(f"Thinking: {thinking:.1f}%")
        st.progress(thinking / 100)

        st.write(f"Feeling: {feeling:.1f}%")
        st.progress(feeling / 100)

        st.write(f"Judging: {judging:.1f}%")
        st.progress(judging / 100)

        st.write(f"Perceiving: {perceiving:.1f}%")
        st.progress(perceiving / 100)
    else:
        st.info("Nog geen resultaat beschikbaar.")