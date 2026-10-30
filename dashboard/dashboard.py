import os

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="E-Commerce Dashboard", page_icon="🛒", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRIMARY = "#1f5fa8"


@st.cache_data
def load_data():
    df = pd.read_csv(
        os.path.join(BASE_DIR, "main_data.csv"), parse_dates=["order_purchase_timestamp"]
    )
    geo = pd.read_csv(os.path.join(BASE_DIR, "state_geo.csv"))
    return df, geo


def build_rfm(data: pd.DataFrame) -> pd.DataFrame:
    snapshot = data.order_purchase_timestamp.max().normalize() + pd.Timedelta(days=1)
    rfm = (
        data.groupby("customer_unique_id")
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("price", "sum"),
        )
        .reset_index()
    )
    rfm["recency"] = (snapshot - rfm.last_purchase).dt.days
    if len(rfm) < 5:
        rfm["segment"] = "Average"
        return rfm
    rfm["R"] = pd.qcut(rfm.recency.rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["M"] = pd.qcut(rfm.monetary.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    def segment(r):
        if r.frequency >= 2 and r.R >= 4:
            return "Champions"
        if r.frequency >= 2:
            return "Loyal"
        if r.M == 5:
            return "Big Spenders"
        if r.R >= 4:
            return "New/Recent"
        if r.R <= 2:
            return "Lost/Hibernating"
        return "Average"

    rfm["segment"] = rfm.apply(segment, axis=1)
    return rfm


df, geo = load_data()

# ---------------- Sidebar ----------------
st.sidebar.title("Filter")
min_d, max_d = df.order_purchase_timestamp.min().date(), df.order_purchase_timestamp.max().date()
date_range = st.sidebar.date_input("Rentang tanggal", (min_d, max_d), min_value=min_d, max_value=max_d)
all_states = sorted(df.customer_state.unique())
states = st.sidebar.multiselect("Negara bagian pelanggan", all_states, default=all_states)

if len(date_range) != 2:
    st.info("Pilih tanggal awal dan akhir pada sidebar.")
    st.stop()

mask = (
    (df.order_purchase_timestamp.dt.date >= date_range[0])
    & (df.order_purchase_timestamp.dt.date <= date_range[1])
    & (df.customer_state.isin(states))
)
data = df[mask]
if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# ---------------- Header & KPI ----------------
st.title("🛒 Dashboard Analisis E-Commerce (Olist)")
st.caption("Pesanan berstatus *delivered*, Jan 2017 – Agu 2018. Revenue = total harga item (tanpa ongkir).")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"BRL {data.price.sum():,.0f}")
c2.metric("Jumlah Pesanan", f"{data.order_id.nunique():,}")
c3.metric("Pelanggan Unik", f"{data.customer_unique_id.nunique():,}")
c4.metric("Rata-rata Nilai Pesanan", f"BRL {data.price.sum() / data.order_id.nunique():,.2f}")

tab1, tab2 = st.tabs(["Kategori Produk", "Pelanggan (RFM) & Wilayah"])

# ---------------- Tab 1 ----------------
with tab1:
    st.subheader("Kategori apa yang menyumbang revenue tertinggi dan terendah?")
    cat = data.groupby("category").price.sum().sort_values(ascending=False)
    n_top = st.slider("Jumlah kategori yang ditampilkan", 5, 15, 10)

    left, right = st.columns(2)
    top = cat.head(n_top).iloc[::-1].reset_index()
    fig = px.bar(top, x="price", y="category", orientation="h", color_discrete_sequence=[PRIMARY],
                 labels={"price": "Revenue (BRL)", "category": ""}, title=f"{n_top} Kategori Revenue Tertinggi")
    left.plotly_chart(fig)

    bottom = cat.tail(n_top).reset_index()
    fig = px.bar(bottom, x="price", y="category", orientation="h", color_discrete_sequence=["#b8bec6"],
                 labels={"price": "Revenue (BRL)", "category": ""}, title=f"{n_top} Kategori Revenue Terendah")
    right.plotly_chart(fig)

    st.subheader("Tren revenue bulanan")
    default_cats = cat.head(5).index.tolist()
    chosen = st.multiselect("Kategori", cat.index.tolist(), default=default_cats)
    if chosen:
        monthly = (
            data[data.category.isin(chosen)]
            .assign(month=lambda d: d.order_purchase_timestamp.dt.to_period("M").dt.to_timestamp())
            .groupby(["month", "category"], as_index=False).price.sum()
        )
        fig = px.line(monthly, x="month", y="price", color="category", markers=True,
                      labels={"price": "Revenue (BRL)", "month": "Bulan", "category": "Kategori"})
        st.plotly_chart(fig)
    else:
        st.info("Pilih minimal satu kategori.")

# ---------------- Tab 2 ----------------
with tab2:
    st.subheader("Sebaran segmen pelanggan (RFM)")
    rfm = build_rfm(data)
    seg = (
        rfm.groupby("segment")
        .agg(customers=("customer_unique_id", "count"), revenue=("monetary", "sum"),
             avg_recency=("recency", "mean"), avg_monetary=("monetary", "mean"))
        .reset_index()
    )
    seg["% Pelanggan"] = seg.customers / seg.customers.sum() * 100
    seg["% Revenue"] = seg.revenue / seg.revenue.sum() * 100
    seg = seg.sort_values("% Revenue", ascending=False)

    long = seg.melt(id_vars="segment", value_vars=["% Pelanggan", "% Revenue"], var_name="Metrik", value_name="Persen")
    fig = px.bar(long, x="Persen", y="segment", color="Metrik", barmode="group", orientation="h",
                 color_discrete_map={"% Pelanggan": "#b8bec6", "% Revenue": PRIMARY},
                 labels={"Persen": "Persentase (%)", "segment": ""}, title="Proporsi Pelanggan vs Revenue per Segmen")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig)
    st.dataframe(
        seg.rename(columns={"segment": "Segmen", "customers": "Pelanggan", "revenue": "Revenue",
                            "avg_recency": "Rata-rata Recency (hari)", "avg_monetary": "Rata-rata Monetary"})
        .round(1), hide_index=True,
    )

    st.subheader("Kontribusi revenue per negara bagian")
    state = (
        data.groupby("customer_state")
        .agg(revenue=("price", "sum"), customers=("customer_unique_id", "nunique"))
        .reset_index()
    )
    state["revenue_per_customer"] = state.revenue / state.customers
    state["pct"] = state.revenue / state.revenue.sum() * 100

    left, right = st.columns(2)
    top_state = state.sort_values("pct", ascending=False).head(10).iloc[::-1]
    fig = px.bar(top_state, x="pct", y="customer_state", orientation="h", color_discrete_sequence=[PRIMARY],
                 labels={"pct": "% dari total revenue", "customer_state": ""}, title="10 Negara Bagian Teratas")
    left.plotly_chart(fig)

    gm = state.merge(geo, left_on="customer_state", right_on="geolocation_state")
    fig = px.scatter_geo(gm, lat="lat", lon="lng", size="revenue", color="revenue_per_customer",
                         hover_name="customer_state", color_continuous_scale="Blues",
                         labels={"revenue_per_customer": "Revenue/pelanggan (BRL)"},
                         title="Peta Revenue per Negara Bagian", scope="south america")
    fig.update_geos(fitbounds="locations", showcountries=True)
    right.plotly_chart(fig)

st.caption("Sumber data: Olist Brazilian E-Commerce Public Dataset • Proyek Analisis Data")
