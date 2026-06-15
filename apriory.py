import streamlit as st
import pandas as pd
import plotly.express as px

from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.frequent_patterns import association_rules

# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="Dashboard Analisis Bundling Menu Cafe",
    page_icon="☕",
    layout="wide"
)

st.title("☕ Dashboard Analisis Bundling Menu Cafe")
st.markdown(
    "Analisis Pola Pembelian Pelanggan Menggunakan Algoritma FP-Growth"
)

# =====================================
# SIDEBAR
# =====================================

st.sidebar.header("Parameter Analisis")

uploaded_file = st.sidebar.file_uploader(
    "Upload File Excel",
    type=["xlsx"]
)

min_support = st.sidebar.slider(
    "Minimum Support",
    0.01,
    1.00,
    0.05,
    0.01
)

min_confidence = st.sidebar.slider(
    "Minimum Confidence",
    0.01,
    1.00,
    0.40,
    0.01
)

min_lift = st.sidebar.slider(
    "Minimum Lift",
    1.00,
    10.00,
    1.20,
    0.10
)

# =====================================
# KATEGORI MENU
# =====================================

kategori = {
    "Mie": "Makanan",
    "Nasi Goreng": "Makanan",
    "Ayam Crispy": "Makanan",

    "Roti Bakar": "Snack",
    "Kentang Goreng": "Snack",
    "Toast Coklat": "Snack",

    "Es Teh": "Minuman",
    "Kopi Susu": "Minuman",
    "Es Jeruk": "Minuman",
    "Milkshake": "Minuman"
}

# =====================================
# PROSES
# =====================================

if uploaded_file:

    try:

        df = pd.read_excel(uploaded_file)

        if "transaksi" not in df.columns or "item" not in df.columns:

            st.error(
                "File harus memiliki kolom 'transaksi' dan 'item'"
            )

        else:

            # =====================================
            # DATA TRANSAKSI
            # =====================================

            transaksi = (
                df.groupby("transaksi")["item"]
                .apply(list)
                .tolist()
            )

            # =====================================
            # ENCODING
            # =====================================

            te = TransactionEncoder()

            te_array = te.fit(transaksi).transform(transaksi)

            df_encoded = pd.DataFrame(
                te_array,
                columns=te.columns_
            )

            # =====================================
            # FP-GROWTH
            # =====================================

            frequent_itemsets = fpgrowth(
                df_encoded,
                min_support=min_support,
                use_colnames=True
            )

            if frequent_itemsets.empty:

                st.warning(
                    "Tidak ditemukan frequent itemset."
                )

            else:

                rules = association_rules(
                    frequent_itemsets,
                    metric="confidence",
                    min_threshold=min_confidence
                )

                rules = rules[
                    rules["lift"] >= min_lift
                ]

                if rules.empty:

                    st.warning(
                        "Tidak ditemukan rule yang memenuhi syarat."
                    )

                else:

                    # =====================================
                    # SCORE
                    # =====================================

                    rules["score"] = (
                        rules["support"] * 0.3 +
                        rules["confidence"] * 0.4 +
                        rules["lift"] * 0.3
                    )

                    rules = rules.sort_values(
                        by="score",
                        ascending=False
                    )

                    
                    # =====================================
                    # KPI
                    # =====================================

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

                    st.subheader("📋 Ringkasan Sistem")

                    st.write(f"Jumlah Menu : {total_menu}")
                    st.write(f"Jumlah Transaksi : {total_transaksi}")
                    st.write(f"Jumlah Rules : {len(rules)}")

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Total Transaksi",
                        len(transaksi)
                    )

                    col2.metric(
                        "Jumlah Menu",
                        len(df["item"].unique())
                    )

                    col3.metric(
                        "Frequent Itemset",
                        len(frequent_itemsets)
                    )

                    col4.metric(
                        "Aturan Bundling",
                        len(rules)
                    )

                    # =====================================
                    # MENU TERLARIS
                    # =====================================

                    st.subheader("🔥 Top 10 Menu Terlaris")

                    menu_terlaris = (
                        df["item"]
                        .value_counts()
                        .reset_index()
                    )

                    menu_terlaris.columns = [
                        "Menu",
                        "Jumlah"
                    ]

                    fig = px.bar(
                        menu_terlaris.head(10),
                        x="Menu",
                        y="Jumlah",
                        text="Jumlah"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                    # =====================================
                    # PIE CHART
                    # =====================================

                    st.subheader("🥧 Komposisi Penjualan")

                    fig2 = px.pie(
                        menu_terlaris.head(10),
                        names="Menu",
                        values="Jumlah"
                    )

                    st.plotly_chart(
                        fig2,
                        use_container_width=True
                    )

                    # =====================================
                    # MENU KURANG LAKU
                    # =====================================

                    st.subheader("⚠️ Menu Kurang Laku")

                    kurang_laku = (
                        df["item"]
                        .value_counts()
                        .sort_values()
                        .head(10)
                        .reset_index()
                    )

                    kurang_laku.columns = [
                        "Menu",
                        "Jumlah Terjual"
                    ]

                    st.dataframe(
                        kurang_laku,
                        use_container_width=True
                    )

                    # =====================================
                    # HASIL ANALISIS
                    # =====================================

                    hasil = pd.DataFrame({

                        "Produk Utama":
                        rules["antecedents"].apply(
                            lambda x: ", ".join(list(x))
                        ),

                        "Produk Pasangan":
                        rules["consequents"].apply(
                            lambda x: ", ".join(list(x))
                        ),

                        "Support (%)":
                        (rules["support"] * 100).round(2),

                        "Confidence (%)":
                        (rules["confidence"] * 100).round(2),

                        "Lift":
                        rules["lift"].round(2),

                        "Score":
                        rules["score"].round(3)

                    })

                    st.subheader(
                        "📋 Hasil Analisis Bundling"
                    )

                    st.dataframe(
                        hasil,
                        use_container_width=True
                    )

                    # =====================================
                    # TOP 10 BUNDLING
                    # =====================================

                    st.subheader(
                        "🏆 Top 10 Bundling Terbaik"
                    )

                    fig3 = px.bar(
                        hasil.head(10),
                        x="Confidence (%)",
                        y="Produk Utama",
                        color="Lift",
                        orientation="h"
                    )

                    st.plotly_chart(
                        fig3,
                        use_container_width=True
                    )

                    # =====================================
                    # TOP 3 REKOMENDASI UNIK
                    # =====================================

                    st.subheader(
                        "📝 Top 3 Rekomendasi Bundling"
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

                        kategori_bundle = set()

                        for item in bundle:

                            if item in kategori:
                                kategori_bundle.add(
                                    kategori[item]
                                )

                        if len(kategori_bundle) < 2:
                            continue

                        seen.add(key)

                        unique_rules.append({
                            "bundle": bundle,
                            "support": row["support"],
                            "confidence": row["confidence"],
                            "lift": row["lift"],
                            "score": row["score"],
                            "kategori": kategori_bundle
                        })

                    unique_rules = sorted(
                        unique_rules,
                        key=lambda x: x["score"],
                        reverse=True
                    )

                    top3 = unique_rules[:3]

                    cols = st.columns(3)

                    for idx, row in enumerate(top3):

                        bundle = " + ".join(
                            row["bundle"]
                        )

                        kategori_text = ", ".join(
                            sorted(row["kategori"])
                        )

                        with cols[idx]:

                            st.success(
                                f"""
### Ranking #{idx+1}

**{bundle.upper()}**

Kategori:
{kategori_text}

Support :
{row['support']*100:.2f}%

Confidence :
{row['confidence']*100:.2f}%

Lift :
{row['lift']:.2f}

Score :
{row['score']:.3f}
"""
                            )

                    # =====================================
                    # DOWNLOAD
                    # =====================================

                    hasil.to_excel(
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

    except Exception as e:

        st.error(f"Error: {e}")

else:

    st.info(
        "Silakan upload file Excel terlebih dahulu."
    )