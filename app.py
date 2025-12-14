import pandas as pd
import numpy as np
import re
import streamlit as st
from io import BytesIO

THRESHOLD = 5

EAN_COL_MY = "EAN Code"
STOCK_COL_MY = "Stock"

IMAGE_COL_TPL = "Image"
STATUS_COL_TPL = "Status"

def extract_ean_from_image(image_name):
    if pd.isna(image_name):
        return np.nan
    s = str(image_name)
    m = re.search(r"ean[_+]?(\d{8,14})_", s, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"\+(\d{8,14})_", s)
    if m:
        return m.group(1)
    return np.nan

def to_excel_bytes(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return out.getvalue()

st.title("تحديث حالة المنتجات حسب المخزون")

my_file = st.file_uploader("ارفع ملف المنتجات", type=["xlsx", "csv"])
tpl_file = st.file_uploader("ارفع ملف القالب", type=["xlsx", "csv"])

if my_file and tpl_file:
    my = pd.read_excel(my_file) if my_file.name.endswith("xlsx") else pd.read_csv(my_file)
    tpl = pd.read_excel(tpl_file) if tpl_file.name.endswith("xlsx") else pd.read_csv(tpl_file)

    my[EAN_COL_MY] = my[EAN_COL_MY].astype(str).str.strip()
    my_stock = pd.to_numeric(my[STOCK_COL_MY], errors="coerce")
    stock_map = my.assign(_stock=my_stock).groupby(EAN_COL_MY)["_stock"].max()

    tpl_ean = tpl[IMAGE_COL_TPL].apply(extract_ean_from_image)
    matched_stock = tpl_ean.map(stock_map)

    if STATUS_COL_TPL not in tpl.columns:
        tpl[STATUS_COL_TPL] = ""

    mask = matched_stock.notna()
    tpl.loc[mask, STATUS_COL_TPL] = np.where(
        matched_stock[mask] < THRESHOLD, "inactive", "active"
    )

    st.success(f"تم تحديث {int(mask.sum())} منتج")

    st.download_button(
        "تحميل الملف النهائي",
        data=to_excel_bytes(tpl),
        file_name="foods_bulk_format_updated.xlsx"
    )
