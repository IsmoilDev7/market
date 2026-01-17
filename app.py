# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Zakaz va Sotuv Analiz", layout="wide")
st.title("🛒 Zakaz va Sotuv Analiz Dashboard")

# -----------------------------
# 1️⃣ Excel fayllarni upload qilish
# -----------------------------
st.header("1️⃣ Excel fayllarni upload qiling")

orders_file = st.file_uploader("Birinchi fayl: Zakazlar (orders)", type=['xlsx'])
sales_file = st.file_uploader("Ikkinchi fayl: Sotuv / Qaytish (sales/returns)", type=['xlsx'])

if orders_file and sales_file:
    
    # Excel fayllarni o'qish
    orders = pd.read_excel(orders_file, engine='openpyxl')
    sales = pd.read_excel(sales_file, engine='openpyxl')

    # -----------------------------
    # 2️⃣ Ustunlarni tozalash va tiplarni o'rnatish
    # -----------------------------
    orders['Период'] = pd.to_datetime(orders['Период'], errors='coerce')
    orders['Количество'] = pd.to_numeric(orders['Количество'], errors='coerce')
    orders['Сумма'] = pd.to_numeric(orders['Сумма'], errors='coerce')
    
    sales['Период'] = pd.to_datetime(sales['Период'], errors='coerce')
    sales['Количество'] = pd.to_numeric(sales['Количество'], errors='coerce')
    sales['Возрат количество'] = pd.to_numeric(sales['Возрат количество'], errors='coerce')
    sales['Продажная сумма'] = pd.to_numeric(sales['Продажная сумма'], errors='coerce')
    sales['Возврат сумма'] = pd.to_numeric(sales['Возврат сумма'], errors='coerce')

    # -----------------------------
    # 3️⃣ Sana filter
    # -----------------------------
    st.subheader("2️⃣ Sana bo'yicha filter")
    min_date = min(orders['Период'].min(), sales['Период'].min())
    max_date = max(orders['Период'].max(), sales['Период'].max())
    start_date, end_date = st.date_input("Davrni tanlang:", [min_date, max_date])

    orders_filtered = orders[(orders['Период'] >= pd.to_datetime(start_date)) &
                             (orders['Период'] <= pd.to_datetime(end_date))]
    sales_filtered = sales[(sales['Период'] >= pd.to_datetime(start_date)) &
                           (sales['Период'] <= pd.to_datetime(end_date))]

    # -----------------------------
    # 4️⃣ KPI lar hisoblash
    # -----------------------------
    st.subheader("3️⃣ Umumiy KPI lar")
    
    total_orders_qty = orders_filtered['Количество'].sum()
    total_orders_sum = orders_filtered['Сумма'].sum()
    total_sales_qty = sales_filtered['Количество'].sum()
    total_sales_sum = sales_filtered['Продажная сумма'].sum()
    total_return_qty = sales_filtered['Возрат количество'].sum()
    total_return_sum = sales_filtered['Возврат сумма'].sum()
    
    delivered_qty = total_sales_qty - total_return_qty
    delivered_sum = total_sales_sum - total_return_sum
    
    sold_percent = (total_sales_qty / total_orders_qty) * 100 if total_orders_qty > 0 else 0
    return_percent = (total_return_qty / total_orders_qty) * 100 if total_orders_qty > 0 else 0
    
    st.metric("📝 Umumiy zakaz miqdori", total_orders_qty)
    st.metric("💰 Umumiy zakaz summasi", total_orders_sum)
    st.metric("📦 Sotilgan miqdor", total_sales_qty)
    st.metric("💵 Sotilgan summa", total_sales_sum)
    st.metric("↩️ Qaytgan miqdor", total_return_qty)
    st.metric("↩️ Qaytgan summa", total_return_sum)
    st.metric("✅ Yetkazilgan miqdor", delivered_qty)
    st.metric("✅ Yetkazilgan summa", delivered_sum)
    st.metric("📊 Sotilgan foiz (%)", f"{sold_percent:.2f}%")
    st.metric("📊 Qaytgan foiz (%)", f"{return_percent:.2f}%")

    # -----------------------------
    # 5️⃣ Haftalik trendlar
    # -----------------------------
    st.subheader("4️⃣ Haftalik trend (zakaz va qaytarish)")
    
    orders_filtered['Hafta_kuni'] = orders_filtered['Период'].dt.day_name()
    sales_filtered['Hafta_kuni'] = sales_filtered['Период'].dt.day_name()
    
    weekly_orders = orders_filtered.groupby('Hafta_kuni')['Количество'].sum().reindex(
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    weekly_returns = sales_filtered.groupby('Hafta_kuni')['Возрат количество'].sum().reindex(
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    
    fig_weekly = px.bar(x=weekly_orders.index, y=[weekly_orders.values, weekly_returns.values],
                        labels={'x':'Hafta kuni', 'y':'Miqdor'}, 
                        title="Hafta kunlari bo'yicha zakaz va qaytish",
                        barmode='group')
    st.plotly_chart(fig_weekly, use_container_width=True)

    # -----------------------------
    # 6️⃣ Har bir mahsulot bo'yicha analiz
    # -----------------------------
    st.subheader("5️⃣ Mahsulotlar bo'yicha batafsil analiz")
    
    product_summary = orders_filtered.groupby('Номенклатура').agg(
        zakaz_qty=('Количество','sum'),
        zakaz_sum=('Сумма','sum')
    ).reset_index()
    
    sales_summary = sales_filtered.groupby('Номенклатура').agg(
        sold_qty=('Количество','sum'),
        sold_sum=('Продажная сумма','sum'),
        return_qty=('Возрат количество','sum'),
        return_sum=('Возврат сумма','sum')
    ).reset_index()
    
    product_merged = pd.merge(product_summary, sales_summary, on='Номенклатура', how='left').fillna(0)
    product_merged['delivered_qty'] = product_merged['sold_qty'] - product_merged['return_qty']
    product_merged['delivered_sum'] = product_merged['sold_sum'] - product_merged['return_sum']
    product_merged['sold_percent'] = np.where(product_merged['zakaz_qty']>0, 
                                              product_merged['sold_qty'] / product_merged['zakaz_qty'] * 100, 0)
    product_merged['return_percent'] = np.where(product_merged['zakaz_qty']>0, 
                                                product_merged['return_qty'] / product_merged['zakaz_qty'] * 100, 0)
    
    st.dataframe(product_merged.style.format({
        'zakaz_qty':'{:.0f}',
        'zakaz_sum':'{:.2f}',
        'sold_qty':'{:.0f}',
        'sold_sum':'{:.2f}',
        'return_qty':'{:.0f}',
        'return_sum':'{:.2f}',
        'delivered_qty':'{:.0f}',
        'delivered_sum':'{:.2f}',
        'sold_percent':'{:.2f}%',
        'return_percent':'{:.2f}%'
    }), use_container_width=True)

    # -----------------------------
    # 7️⃣ Mahsulotlar bo'yicha grafiklar
    # -----------------------------
    st.subheader("6️⃣ Mahsulotlar bo'yicha grafiklar")
    
    fig_products = px.bar(product_merged, x='Номенклатура', y=['zakaz_qty','sold_qty','return_qty'],
                          barmode='group', title="Zakaz, Sotuv va Qaytish miqdori bo'yicha mahsulotlar")
    st.plotly_chart(fig_products, use_container_width=True)
    
else:
    st.info("Iltimos, ikkita Excel faylni tanlang.")
