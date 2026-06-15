import streamlit as st
import pandas as pd
from database import get_connection


def menu_page():

    st.header("🍽 Kelola Menu")

    tab1, tab2 = st.tabs([
        "Tambah Menu",
        "Daftar Menu"
    ])

    # =====================
    # TAMBAH MENU
    # =====================

    with tab1:

        nama = st.text_input(
            "Nama Menu"
        )

        kategori = st.selectbox(
            "Kategori",
            [
                "Makanan",
                "Minuman",
                "Snack"
            ]
        )

        harga = st.number_input(
            "Harga",
            min_value=0
        )

        if st.button(
            "Simpan Menu"
        ):

            conn = get_connection()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO menu
                (
                    nama_menu,
                    kategori,
                    harga
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    nama,
                    kategori,
                    harga
                )
            )

            conn.commit()
            conn.close()

            st.success(
                "Menu berhasil ditambahkan"
            )

    # =====================
    # DAFTAR MENU
    # =====================

    with tab2:

        conn = get_connection()

        df = pd.read_sql(
            """
            SELECT *
            FROM menu
            """,
            conn
        )

        conn.close()

        st.dataframe(
            df,
            use_container_width=True
        )