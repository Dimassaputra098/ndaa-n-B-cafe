import streamlit as st
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from login import login
from menu_crud import menu_page
from transaksi_crud import transaksi_page
from import_excel import import_excel_page
from database import get_connection
import time

st.set_page_config(
    page_title="Analisis Cafe",
    layout="centered"
)


if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Kelola Menu",
        "Kelola Transaksi",
        "Import Excel",
        "Reset Data"
    ]
)
st.sidebar.divider()

if st.sidebar.button("Logout"):

    st.session_state["login"] = False

    st.success("Berhasil logout.")

    st.rerun()

if menu == "Kelola Menu":

    menu_page()

    st.stop()

if menu == "Kelola Transaksi":

    transaksi_page()

    st.stop()

if menu == "Import Excel":

    import_excel_page()

    st.stop()

st.title("☕ Analisis Menu Bundling Cafe ndaa & B")

conn = get_connection()

df = pd.read_sql(
    """
    SELECT
        t.id_transaksi AS transaksi,
        m.nama_menu AS item
    FROM detail_transaksi d
    JOIN transaksi t
        ON d.id_transaksi = t.id_transaksi
    JOIN menu m
        ON d.id_menu = m.id_menu
    ORDER BY t.id_transaksi
    """,
    conn
)

if menu == "Reset Data":

    st.title("🗑 Reset Data Transaksi")

    st.warning(
        "Menu tidak akan dihapus. Hanya data transaksi yang akan dikosongkan."
    )

    konfirmasi = st.checkbox(
        "Saya yakin ingin menghapus seluruh transaksi"
    )

    if konfirmasi:

        if st.button("🗑 Hapus Semua Transaksi"):

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM detail_transaksi")
            cursor.execute("DELETE FROM transaksi")

            conn.commit()
            conn.close()

            st.success("✅ Seluruh data transaksi berhasil dihapus.")
            

    st.stop()  

conn.close()

if df.empty:

    st.warning(
        "Belum ada data transaksi."
    )

    st.stop()

min_sup = st.slider(
    "Minimal Kemunculan (Support)",
    0.01,
    1.0,
    0.05
)

min_conf = st.slider(
    "Tingkat Kepastian (Confidence)",
    0.1,
    1.0,
    0.3
)
transaksi = (
    df.groupby("transaksi")["item"]
    .apply(list)
    .tolist()
)

te = TransactionEncoder()

te_data = te.fit(transaksi).transform(transaksi)

df_encoded = pd.DataFrame(
    te_data,
    columns=te.columns_
)

freq = apriori(
    df_encoded,
    min_support=min_sup,
    use_colnames=True
)

if freq.empty:

    st.warning(
        "Tidak ditemukan frequent itemset."
    )

else:

    rules = association_rules(
        freq,
        metric="confidence",
        min_threshold=min_conf
    )

    if rules.empty:

        st.warning(
            "Tidak ditemukan association rules."
        )

    else:

        # ==========================
        # HITUNG SCORE
        # ==========================

        rules["score"] = (
            rules["support"] * 0.3 +
            rules["confidence"] * 0.4 +
            rules["lift"] * 0.3
        )

        rules = rules.sort_values(
            by="score",
            ascending=False
        )

        # ==========================
        # KPI DASHBOARD
        # ==========================

        conn = get_connection()

        total_menu = pd.read_sql(
            "SELECT COUNT(*) total FROM menu",
            conn
        ).iloc[0]["total"]

        total_transaksi = pd.read_sql(
            "SELECT COUNT(*) total FROM transaksi",
            conn
        ).iloc[0]["total"]

        conn.close()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "🍽 Total Menu",
            total_menu
        )

        col2.metric(
            "🛒 Total Transaksi",
            total_transaksi
        )

        col3.metric(
            "📋 Total Rules",
            len(rules)
        )

        # ==========================
        # MENU TERLARIS
        # ==========================

        st.subheader(
            "📈 Menu Terlaris"
        )

        conn = get_connection()

        menu_terlaris = pd.read_sql(
            """
            SELECT
                m.nama_menu,
                COUNT(*) jumlah
            FROM detail_transaksi d
            JOIN menu m
                ON d.id_menu = m.id_menu
            GROUP BY m.nama_menu
            ORDER BY jumlah DESC
            LIMIT 10
            """,
            conn
        )

        conn.close()

        st.bar_chart(
            menu_terlaris.set_index(
                "nama_menu"
            )
        )
        # ==========================
# MENU KURANG LAKU
# ==========================

        st.subheader(
        "📉 Menu Kurang Laku"
        )

        conn = get_connection()

        menu_kurang_laku = pd.read_sql(
        """
        SELECT
        m.nama_menu,
        COUNT(d.id_menu) AS jumlah
        FROM menu m
        LEFT JOIN detail_transaksi d
        ON m.id_menu = d.id_menu
        GROUP BY m.id_menu
        ORDER BY jumlah ASC
        LIMIT 5
        """,
        conn
        )

        conn.close()

        st.dataframe(
        menu_kurang_laku,
        use_container_width=True
        )
        

        # ==========================
        # TOP 3 BUNDLING
        # ==========================

        st.subheader(
            "🏆 Top 3 Rekomendasi Bundling"
        )

        unique_rules = []
        seen = set()

        for _, row in rules.iterrows():

            bundle = sorted(
                list(row["antecedents"]) +
                list(row["consequents"])
            )

            key = tuple(bundle)

            if key in seen:
                continue

            seen.add(key)
            unique_rules.append(row)

        top3 = unique_rules[:3]

        cols = st.columns(3)

        for idx, row in enumerate(top3):

            antecedent = ", ".join(
                list(row["antecedents"])
            )

            consequent = ", ".join(
                list(row["consequents"])
            )

            with cols[idx]:

                st.success(
                    f"""
### Ranking #{idx+1}

{antecedent.upper()}
+
{consequent.upper()}

Support:
{row['support']*100:.2f}%

Confidence:
{row['confidence']*100:.2f}%

Lift:
{row['lift']:.2f}

Score:
{row['score']:.3f}
"""
                )

        # ==========================
        # TABEL RULES
        # ==========================

        st.subheader(
            "📊 Hasil Analisis"
        )

        st.dataframe(
            rules,
            use_container_width=True
        )

        # ==========================
        # DOWNLOAD EXCEL
        # ==========================

        rules.to_excel(
            "hasil_bundling.xlsx",
            index=False
        )

        with open(
            "hasil_bundling.xlsx",
            "rb"
        ) as file:

            st.download_button(
                label="📥 Download Hasil Excel",
                data=file,
                file_name="hasil_bundling.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
