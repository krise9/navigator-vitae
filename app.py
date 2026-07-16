import streamlit as st

from modules.ikigai import render_ikigai_module
from modules.mbti import render_mbti_module


st.set_page_config(
    page_title="Navigator Vitae",
    page_icon="🧭",
    layout="centered",
)


def render_home() -> None:
    st.title("Navigator Vitae")

    st.write(
        """
        Navigator Vitae helpt je om je identiteit, richting,
        zingeving en manier van handelen beter te begrijpen.

        Kies hieronder de module die je wilt openen.
        """
    )

    module_choice = st.radio(
        "Kies een module",
        [
            "Module 1: Levensrichting",
            "Module 2: Denk- en gedragsvoorkeuren",
        ],
        index=None,
        key="module_choice",
    )

    if module_choice == "Module 1: Levensrichting":
        st.session_state["active_module"] = "ikigai"
        st.rerun()

    if module_choice == "Module 2: Denk- en gedragsvoorkeuren":
        st.session_state["active_module"] = "mbti"
        st.rerun()


def render_navigation() -> None:
    active_module = st.session_state.get("active_module")

    if active_module:
        if st.button("← Terug naar overzicht", key="back_to_home"):
            st.session_state["active_module"] = None
            st.rerun()


def main() -> None:
    active_module = st.session_state.get("active_module")

    if not active_module:
        render_home()
        return

    render_navigation()

    if active_module == "ikigai":
        render_ikigai_module()
        return

    if active_module == "mbti":
        render_mbti_module()
        return

    st.error("Onbekende module.")
    st.session_state["active_module"] = None


if __name__ == "__main__":
    main()