import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from itertools import combinations

st.set_page_config(
    page_title="Analisis Cafe",
    layout="wide"
)

st.title("Analisis Penjualan & Rekomendasi Bundling")

# =====================================================
# UPLOAD FILE
# =====================================================
uploaded_file = st.file_uploader(
    "Upload File Laporan Cafe",
    type=["xlsx", "csv"]
)

# =====================================================
# PROSES
# =====================================================
if uploaded_file is not None:

    try:

        # =================================================
        # BACA FILE
        # =================================================
        if uploaded_file.name.endswith(".xlsx"):
            raw_df = pd.read_excel(
                uploaded_file,
                header=None
            )
        else:
            raw_df = pd.read_csv(
                uploaded_file,
                header=None
            )

        st.subheader("Preview Data Asli")
        st.dataframe(raw_df)

        # =================================================
        # AMBIL KOLOM PERTAMA
        # =================================================
        df = raw_df[[0]].copy()

        # hapus kosong
        df = df[df[0].notna()]

        # ubah string
        df[0] = df[0].astype(str)

        # hanya ambil data yang ada koma
        df = df[df[0].str.contains(",")]

        # =================================================
        # SPLIT DATA
        # =================================================
        df = df[0].str.split(",", expand=True)

        # hapus tanda kutip
        df = df.replace('"', '', regex=True)

        # ambil 3 kolom pertama
        df = df.iloc[:, :3]

        # =================================================
        # NAMA KOLOM
        # =================================================
        df.columns = [
            "Kategori",
            "Jumlah",
            "Pendapatan"
        ]

        # =================================================
        # UBAH KE NUMERIK
        # =================================================
        df["Jumlah"] = pd.to_numeric(
            df["Jumlah"],
            errors="coerce"
        )

        df["Pendapatan"] = pd.to_numeric(
            df["Pendapatan"],
            errors="coerce"
        )

        # hapus data gagal baca
        df = df.dropna()

        # =================================================
        # HAPUS DATA YANG TIDAK DIPERLUKAN
        # =================================================
        hapus_data = [
            "Qris",
            "Tunai",
            "Debit",
            "Cash",
            "Total",
            "Jumlah pendapatan kategori"
        ]

        df = df[
            ~df["Kategori"].str.lower().isin(
                [x.lower() for x in hapus_data]
            )
        ]

        # =================================================
        # URUTKAN TERLARIS
        # =================================================
        df = df.sort_values(
            by="Jumlah",
            ascending=False
        )

        # reset index
        df = df.reset_index(drop=True)

        # =================================================
        # DATA PENJUALAN
        # =================================================
        st.subheader("Data Penjualan")
        st.dataframe(df)

        # =================================================
        # METRIC
        # =================================================
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Jumlah Kategori",
                len(df)
            )

        with col2:
            st.metric(
                "Kategori Terlaris",
                df.iloc[0]["Kategori"]
            )

        with col3:
            st.metric(
                "Penjualan Tertinggi",
                int(df.iloc[0]["Jumlah"])
            )

        # =================================================
        # TOP 10
        # =================================================
        st.subheader("Top 10 Kategori Terlaris")

        top10 = df.head(10)

        st.dataframe(top10)

        # =================================================
        # GRAFIK PENJUALAN
        # =================================================
        st.subheader("Grafik Penjualan")

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.bar(
            top10["Kategori"],
            top10["Jumlah"]
        )

        ax.set_xlabel("Kategori")
        ax.set_ylabel("Jumlah")
        ax.set_title("Top 10 Kategori Terlaris")

        plt.xticks(rotation=30)

        st.pyplot(fig)

        # =================================================
        # REKOMENDASI BUNDLING
        # =================================================
        st.subheader("Rekomendasi Bundling")

        # ambil top kategori
        top_bundle = df.head(6)

        kategori_list = top_bundle["Kategori"].tolist()
        jumlah_list = top_bundle["Jumlah"].tolist()

        rekomendasi = []

        # kombinasi menu
        for combo in combinations(range(len(kategori_list)), 2):

            i, j = combo

            item1 = kategori_list[i]
            item2 = kategori_list[j]

            jumlah1 = jumlah_list[i]
            jumlah2 = jumlah_list[j]

            # estimasi support
            support = min(jumlah1, jumlah2)

            # confidence sederhana
            confidence = (
                min(jumlah1, jumlah2)
                / max(jumlah1, jumlah2)
            ) * 100

            rekomendasi.append([
                item1,
                item2,
                support,
                round(confidence, 2)
            ])

        # =================================================
        # TABEL BUNDLING
        # =================================================
        bundling_df = pd.DataFrame(
            rekomendasi,
            columns=[
                "Menu 1",
                "Menu 2",
                "Estimasi Support",
                "Confidence (%)"
            ]
        )

        # urut confidence terbesar
        bundling_df = bundling_df.sort_values(
            by="Confidence (%)",
            ascending=False
        )

        st.dataframe(bundling_df)

        # =================================================
        # TOP REKOMENDASI
        # =================================================
        st.subheader("Top Rekomendasi Bundling")

        top_rekomendasi = bundling_df.head(5)

        for index, row in top_rekomendasi.iterrows():

            st.success(
                f"""
                Bundling yang direkomendasikan:

                {row['Menu 1']} + {row['Menu 2']}

                Confidence:
                {row['Confidence (%)']}%
                """
            )

        # =================================================
        # ANALISIS
        # =================================================
        st.subheader("Analisis")

        terlaris = df.iloc[0]["Kategori"]
        terjual = int(df.iloc[0]["Jumlah"])

        st.info(
            f"""
            Kategori/menu paling laku adalah
            '{terlaris}'
            dengan total penjualan
            {terjual} item.

            Menu dengan penjualan tinggi
            lebih cocok dijadikan:
            - promo utama
            - paket hemat
            - rekomendasi bundling
            """
        )

    except Exception as e:
        st.error(f"Terjadi error: {e}")