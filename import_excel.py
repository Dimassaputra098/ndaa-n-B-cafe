import streamlit as st
import pandas as pd
from database import get_connection

def import_excel_page():

    st.header("📥 Import Transaksi Excel")

    file = st.file_uploader(
        "Upload Excel",
        type=["xlsx"]
    )

    if file:

        df = pd.read_excel(file)

        st.dataframe(df)

        if st.button("Import ke Database"):

            conn = get_connection()
            cur = conn.cursor()

            for transaksi_id, group in df.groupby("transaksi"):

                cur.execute(
                    """
                    INSERT INTO transaksi(tanggal)
                    VALUES (CURDATE())
                    """
                )

                conn.commit()

                id_transaksi = cur.lastrowid

                for item in group["item"]:

                    cur.execute(
                        """
                        SELECT id_menu
                        FROM menu
                        WHERE nama_menu=%s
                        """,
                        (item,)
                    )

                    result = cur.fetchone()

                    if result:

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
                                result[0]
                            )
                        )

            conn.commit()
            conn.close()

            st.success(
                "Import berhasil"
            )