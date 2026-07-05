import json
import streamlit as st

from engines.database import save_response
from engines.mbti_engine import calculate_mbti
from engines.registry import get_person


st.title("Navigator Vitae")
st.subheader("Module 2: Denk- en gedragsvoorkeuren v0.1")

with open("questions/mbti.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

navigator_id = st.text_input("Navigator ID")

person = None

if navigator_id:
    person = get_person(navigator_id)

    if person:
        st.success(f"Welkom, {person['naam']}.")
    else:
        st.error("Navigator ID niet gevonden.")

if person:
    answers = {}

    for question in questions:
        choice = st.radio(
            question["text"],
            ["A", "B"],
            format_func=lambda x, q=question: q[x],
            key=question["id"]
        )
        answers[question["id"]] = choice

    if st.button("Verzenden"):
        result = calculate_mbti(answers, questions)

        save_response(navigator_id, result)

        st.success("Bedankt. Je antwoorden zijn opgeslagen.")

        st.session_state["last_result"] = result
        st.session_state["last_navigator_id"] = navigator_id
        st.session_state["last_person_name"] = person["naam"]

st.divider()

admin_code = st.text_input("Admin code", type="password")

if admin_code == "kris123":
    st.subheader("Admin-weergave")

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]

        st.write("Navigator ID:", st.session_state["last_navigator_id"])
        st.write("Naam:", st.session_state["last_person_name"])
        st.write("Type:", result["type"])
        st.write("Scores:", result["scores"])
        st.write("Asposities 0-100:", result["axis_positions"])
    else:
        st.info("Nog geen resultaat beschikbaar.")