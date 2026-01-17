import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# ==========================
# Faylni o'qish funksiyasi
# ==========================
def load_file(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        file_name = uploaded_file.name.lower()
        file_bytes = BytesIO(uploaded_file.read())
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(file_bytes, engine='openpyxl')
        elif file_name.endswith('.xls'):
            df = pd.read_excel(file_bytes, engine='xlrd')
        elif file_name.endswith('.csv'):
            df = pd.read_csv(file_bytes)
        else:
            st.error("Fayl formati noto‘g‘ri. Faqat .xlsx, .xls yoki .csv ruxsat etiladi.")
            return None
        return df
    except Exception as e:
        st.error(f"Faylni o'qishda xatolik: {e}")
        return None

# ==========================
# Streamlit UI
# ==========================
st.title("📊 Zakaz va Sotuv/Qaytish Analizi")

orders_file = st.file_uploader("1️⃣ Birinchi fayl: Zakazlar (orders)", type=['xlsx','xls','csv'])
sales_file = st.file_uploader("2️⃣ Ikkinchi fayl: Sotuv/Qaytish (sales/returns)", type=['xlsx','xls','csv'])

if orders_file and sales_file:
    orders = load_file(orders_file)
    sales = load_file(sales_file)
    
    if orders is not None and sales is not None:
        st.success("✅ Fayllar muvaffaqiyatli yuklandi!")

        # ==========================
        # Sana ustunini datetime ga o'tkazish
        # ==========================
        orders['Период'] = pd.to_datetime(orders['Период'], errors='coerce')
        sales['Период'] = pd.to_datetime(sales['Период'], errors='coerce')

        # ==========================
        # Sana bo‘yicha filter
        # ==========================
        st.subheader("📅 Sana bo‘yicha filter")
        min_date = min(orders['Период'].min(), sales['Период'].min())
        max_date = max(orders['Период'].max(), sales['Период'].max())

        date_range = st.date_input("Sana oralig‘i:", [min_date, max_date])

        filtered_orders = orders[(orders['Период']>=pd.to_datetime(date_range[0])) & 
                                 (orders['Период']<=pd.to_datetime(date_range[1]))]
        filtered_sales = sales[(sales['Период']>=pd.to_datetime(date_range[0])) & 
                               (sales['Период']<=pd.to_datetime(date_range[1]))]

        st.write(f"Zakazlar filtrlash: {filtered_orders.shape[0]} qator")
        st.write(f"Sotuv/Qaytish filtrlash: {filtered_sales.shape[0]} qator")

        # ==========================
        # KPI lar
        # ==========================
        st.subheader("📊 Umumiy KPI lar")

        total_orders = filtered_orders['Количество'].sum()
        st.write(f"Umumiy zakaz miqdori: {total_orders}")

        orders_by_client = filtered_orders.groupby('Контрагент')['Количество'].sum().reset_index()
        st.write("Kantragen bo‘yicha zakazlar:")
        st.dataframe(orders_by_client)

        # Sotuv va qaytish
        # Numeric ga o'tkazish
        for col in ['Продажная сумма', 'Возврат сумма', 'Количество', 'Возврат количество']:
            if col in filtered_sales.columns:
                filtered_sales[col] = pd.to_numeric(filtered_sales[col], errors='coerce')
            if col in filtered_orders.columns:
                filtered_orders[col] = pd.to_numeric(filtered_orders[col], errors='coerce')

        total_sold = filtered_sales['Продажная сумма'].sum() if 'Продажная сумма' in filtered_sales.columns else 0
        total_returned = filtered_sales['Возврат сумма'].sum() if 'Возврат сумма' in filtered_sales.columns else 0
        st.write(f"Umumiy sotuv: {total_sold}")
        st.write(f"Umumiy qaytgan: {total_returned}")

        # Foiz hisoblash
        sold_percent = (total_sold / total_orders)*100 if total_orders>0 else 0
        return_percent = (total_returned / total_orders)*100 if total_orders>0 else 0
        st.write(f"Sotilgan foizi: {sold_percent:.2f}%")
        st.write(f"Qaytgan foizi: {return_percent:.2f}%")

        # ==========================
        # Mahsulot bo‘yicha tahlil
        # ==========================
        st.subheader("🛒 Mahsulot bo‘yicha tahlil")
        product_orders = filtered_orders.groupby('Номенклатура')['Количество'].sum().reset_index()
        product_sales = filtered_sales.groupby('Номенклатура')['Продажная сумма'].sum().reset_index() if 'Продажная сумма' in filtered_sales.columns else pd.DataFrame({'Номенклатура':[], 'Продажная сумма':[]})
        product_returns = filtered_sales.groupby('Номенклатура')['Возврат сумма'].sum().reset_index() if 'Возврат сумма' in filtered_sales.columns else pd.DataFrame({'Номенклатура':[], 'Возврат сумма':[]})

        product_summary = product_orders.merge(product_sales, on='Номенклатура', how='left') \
                                        .merge(product_returns, on='Номенклатура', how='left') \
                                        .fillna(0)
        product_summary.rename(columns={'Количество':'Zakaz miqdori','Продажная сумма':'Sotilgan summa','Возврат сумма':'Qaytgan summa'}, inplace=True)

        # Zararga ishlayotgan mahsulotlar (sotilgan < qaytgan)
        product_summary['Zarar'] = product_summary['Sotilgan summa'] - product_summary['Qaytgan summa']
        product_summary['Zarar status'] = product_summary['Zarar'].apply(lambda x: "Zararga ishlamoqda" if x<0 else "Normal")
        st.dataframe(product_summary)

        # ==========================
        # Grafiklar
        # ==========================
        st.subheader("📈 Mahsulotlar grafiklari")

        fig, ax = plt.subplots(figsize=(10,6))
        sns.barplot(data=product_summary, x='Номенклатура', y='Zakaz miqdori', color='skyblue')
        plt.xticks(rotation=45, ha='right')
        plt.title("Mahsulotlar bo‘yicha Zakaz miqdori")
        st.pyplot(fig)

        fig2, ax2 = plt.subplots(figsize=(10,6))
        sns.barplot(data=product_summary, x='Номенклатура', y='Sotilgan summa', color='green')
        plt.xticks(rotation=45, ha='right')
        plt.title("Mahsulotlar bo‘yicha Sotilgan summa")
        st.pyplot(fig2)

        fig3, ax3 = plt.subplots(figsize=(10,6))
        sns.barplot(data=product_summary, x='Номенклатура', y='Qaytgan summa', color='red')
        plt.xticks(rotation=45, ha='right')
        plt.title("Mahsulotlar bo‘yicha Qaytgan summa")
        st.pyplot(fig3)

        fig4, ax4 = plt.subplots(figsize=(10,6))
        sns.barplot(data=product_summary, x='Номенклатура', y='Zarar', palette='coolwarm')
        plt.xticks(rotation=45, ha='right')
        plt.title("Mahsulotlar bo‘yicha Zarar/Qaytgan")
        st.pyplot(fig4)

        # ==========================
        # Haftalik trendlar
        # ==========================
        st.subheader("📆 Haftalik trendlar")
        filtered_orders['weekday'] = filtered_orders['Период'].dt.day_name()
        filtered_sales['weekday'] = filtered_sales['Период'].dt.day_name()

        weekday_orders = filtered_orders.groupby('weekday')['Количество'].sum() \
                                .reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).fillna(0)

        if 'Возврат количество' in filtered_sales.columns:
            weekday_returns = filtered_sales.groupby('weekday')['Возврат количество'].sum() \
                                        .reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).fillna(0)
        else:
            weekday_returns = pd.Series([0]*7, index=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])

        st.write("Hafta kunlari bo‘yicha Zakazlar:")
        st.bar_chart(weekday_orders)
        st.write("Hafta kunlari bo‘yicha Qaytishlar:")
        st.bar_chart(weekday_returns)
