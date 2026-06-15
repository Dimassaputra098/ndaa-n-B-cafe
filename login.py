import streamlit as st
from database import get_connection

def login():

    st.subheader("Login Admin")

    username = st.text_input("Username")
    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM admin
            WHERE username=%s
            AND password=%s
            """,
            (username,password)
        )

        user = cur.fetchone()

        conn.close()

        if user:

            st.session_state["login"] = True
            st.success("Login Berhasil")

        else:

            st.error("Username atau Password Salah")