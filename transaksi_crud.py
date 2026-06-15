import streamlit as st
import pandas as pd
from database import get_connection
from datetime import date

def transaksi_page():

    st.header("🛒 Kelola Transaksi")

    conn = get_connection()

    menu_df = pd.read_sql(
        "SELECT * FROM menu",
        conn
    )

    conn.close()

    if menu_df.empty:

        st.warning(
            "Belum ada data menu."
        )

        return

    tanggal = st.date_input(
        "Tanggal",
        value=date.today()
    )

    pilihan_menu = st.multiselect(
        "Pilih Menu",
        menu_df["nama_menu"]
    )

    if st.button("Simpan Transaksi"):

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO transaksi
            (tanggal)
            VALUES (%s)
            """,
            (tanggal,)
        )

        conn.commit()

        id_transaksi = cur.lastrowid

        for menu in pilihan_menu:

            cur.execute(
                """
                SELECT id_menu
                FROM menu
                WHERE nama_menu=%s
                """,
                (menu,)
            )

            id_menu = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO detail_transaksi
                (
                    id_transaksi,
                    id_menu
                )
                VALUES
                (
                    %s,
                    %s
                )
                """,
                (
                    id_transaksi,
                    id_menu
                )
            )

        conn.commit()
        conn.close()

        st.success(
            "Transaksi berhasil disimpan"
        )