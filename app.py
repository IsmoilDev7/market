import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =============================
# STREAMLIT CONFIG
# =============================
st.set_page_config(page_title="Sales & Return Dashboard", layout="wide")
st.title("📊 Savdo va Qaytarish Analitikasi")
st.write("""
Bu dashboard mahsulotlar bo'yicha zakazlar, sotuvlar, qaytarishlar va haftalik trendlarni ko'rsatadi.
Har bir KPI avtomatik hisoblanadi, boshliq ko‘rganda darhol tushunadi.
""")

# =============================
# EXCEL UPLOAD
# =============================
orders_file = st.file_uploader("📥 Zakaz faylini tanlang (orders.xlsx)", type=['xlsx'])
returns_file = st.file_uploader("📥 Qaytish va sotuv faylini tanlang (returns_sales.xlsx)", type=['xlsx'])

if orders_file and returns_file:
    # =============================
    # EXCEL READ & CLEANING
    # =============================
    orders = pd.read_excel(orders_file)
    returns = pd.read_excel(returns_file)
    
    # Sana va sonlarni to'g'rilash
    orders['Период'] = pd.to_datetime(orders['Период'])
    orders['Количество'] = pd.to_numeric(orders['Количество'], errors='coerce')
    orders['Сумма'] = pd.to_numeric(orders['Сумма'], errors='coerce')
    
    returns['Период'] = pd.to_datetime(returns['Период'])
    returns['Количество'] = pd.to_numeric(returns['Количество'], errors='coerce')
    returns['Возврат количество'] = pd.to_numeric(returns['Возврат количество'], errors='coerce')
    returns['Продажная сумма'] = pd.to_numeric(returns['Продажная сумма'], errors='coerce')
    returns['Возврат сумма'] = pd.to_numeric(returns['Возврат сумма'], errors='coerce')
    
    st.success("✅ Excel fayllar muvaffaqiyatli yuklandi va tayyorlandi.")
    
    # =============================
    # DATE FILTER
    # =============================
    min_date = min(orders['Период'].min(), returns['Период'].min())
    max_date = max(orders['Период'].max(), returns['Период'].max())
    date_range = st.date_input("📅 Sana oralig‘i tanlang", [min_date, max_date])
    
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    orders_filtered = orders[(orders['Период'] >= start_date) & (orders['Период'] <= end_date)]
    returns_filtered = returns[(returns['Период'] >= start_date) & (returns['Период'] <= end_date)]
    
    # =============================
    # MAHSULOT BO‘YICHA KPI
    # =============================
    # Zakaz miqdori va summasi
    order_grp = orders_filtered.groupby('Номенклатура').agg(
        total_order_qty=('Количество', 'sum'),
        total_order_sum=('Сумма', 'sum')
    ).reset_index()
    
    # Sotilgan va qaytarilgan
    return_grp = returns_filtered.groupby('Номенклатура').agg(
        sold_qty=('Количество', 'sum'),
        return_qty=('Возврат количество', 'sum'),
        sold_sum=('Продажная сумма', 'sum'),
        return_sum=('Возврат сумма', 'sum')
    ).reset_index()
    
    # Merge KPI
    df_products = order_grp.merge(return_grp, on='Номенклатура', how='left').fillna(0)
    
    # Yetkazilgan, foizlar
    df_products['delivered_qty'] = df_products['total_order_qty'] - df_products['return_qty']
    df_products['sold_percent'] = (df_products['sold_qty'] / df_products['total_order_qty'] * 100).round(2)
    df_products['return_percent'] = (df_products['return_qty'] / df_products['total_order_qty'] * 100).round(2)
    
    # =============================
    # KONTRAGENT BO‘YICHA KPI
    # =============================
    contragent_grp = orders_filtered.groupby('Контрагент').agg(
        total_order_qty=('Количество', 'sum'),
        total_order_sum=('Сумма', 'sum')
    ).reset_index()
    
    contragent_return_grp = returns_filtered.groupby('Контрагент').agg(
        sold_qty=('Количество', 'sum'),
        return_qty=('Возврат количество', 'sum')
    ).reset_index()
    
    df_contragent = contragent_grp.merge(contragent_return_grp, on='Контрагент', how='left').fillna(0)
    df_contragent['delivered_qty'] = df_contragent['total_order_qty'] - df_contragent['return_qty']
    
    # =============================
    # HAFTALIK TREND
    # =============================
    orders_filtered['weekday'] = orders_filtered['Период'].dt.day_name()
    returns_filtered['weekday'] = returns_filtered['Период'].dt.day_name()
    
    orders_week = orders_filtered.groupby('weekday')['Количество'].sum().reset_index()
    returns_week = returns_filtered.groupby('weekday')['Возврат количество'].sum().reset_index()
    
    # =============================
    # DASHBOARD
    # =============================
    st.subheader("📦 Mahsulot bo‘yicha KPI")
    st.dataframe(df_products)
    
    st.subheader("📊 Zakaz vs Qaytarish vs Yetkazilgan")
    fig1 = px.bar(df_products, x='Номенклатура',
                  y=['total_order_qty', 'return_qty', 'delivered_qty'],
                  barmode='group', title='Zakaz, Qaytarish va Yetkazilgan miqdorlar')
    st.plotly_chart(fig1, use_container_width=True)
    
    st.subheader("📈 Sotilgan va Qaytarilgan foizlar (%)")
    fig2 = px.bar(df_products, x='Номенклатура',
                  y=['sold_percent', 'return_percent'],
                  barmode='group', title='Sotilgan va Qaytarilgan foizlar')
    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("👥 Kontragent bo‘yicha KPI")
    st.dataframe(df_contragent)
    
    st.subheader("📆 Haftalik trend: zakaz va qaytarish")
    fig3 = px.line(orders_week, x='weekday', y='Количество', title='Zakazlar haftalik trend')
    fig4 = px.line(returns_week, x='weekday', y='Возврат количество', title='Qaytarishlar haftalik trend')
    st.plotly_chart(fig3, use_container_width=True)
    st.plotly_chart(fig4, use_container_width=True)
    
    # =============================
    # TOP 10 MAHSULOT
    # =============================
    st.subheader("🏆 Top 10 mahsulot (yetkazilgan miqdor bo‘yicha)")
    top_products = df_products.sort_values('delivered_qty', ascending=False).head(10)
    st.dataframe(top_products)
    
    st.success("✅ Dashboard tayyor! Barcha KPI va grafiklar ko‘rildi.")
