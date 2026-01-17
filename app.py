import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================
# Faylni o'qish funksiyasi
# ==========================
def load_file(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        file_name = uploaded_file.name.lower()
        # Fayl formatini aniqlash
        if file_name.endswith('.xlsx'):
            # .xlsx faylini openpyxl bilan o'qish
            df = pd.read_excel(BytesIO(uploaded_file.read()), engine='openpyxl')
        elif file_name.endswith('.xls'):
            # .xls faylini xlrd bilan o'qish
            df = pd.read_excel(BytesIO(uploaded_file.read()), engine='xlrd')
        elif file_name.endswith('.csv'):
            # csv faylini o'qish
            df = pd.read_csv(BytesIO(uploaded_file.read()))
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

orders_file = st.file_uploader("Birinchi fayl: Zakazlar (orders)", type=['xlsx','xls','csv'])
sales_file = st.file_uploader("Ikkinchi fayl: Sotuv/Qaytish (sales/returns)", type=['xlsx','xls','csv'])

if orders_file and sales_file:
    orders = load_file(orders_file)
    sales = load_file(sales_file)
    
    if orders is not None and sales is not None:
        st.success("✅ Fayllar muvaffaqiyatli yuklandi!")

        # ==========================
        # KPI lar
        # ==========================
        st.subheader("📊 Umumiy KPI lar")

        # Umumiy zakaz
        total_orders = orders['Количество'].sum()
        st.write(f"Umumiy zakaz miqdori: {total_orders}")

        # Kantragen bo‘yicha zakaz
        orders_by_client = orders.groupby('Контрагент')['Количество'].sum().reset_index()
        st.write("Kantragen bo‘yicha zakazlar:")
        st.dataframe(orders_by_client)

        # Sotuv va qaytish
        sales['Продажная сумма'] = pd.to_numeric(sales['Продажная сумма'], errors='coerce').fillna(0)
        sales['Возврат сумма'] = pd.to_numeric(sales['Возврат сумма'], errors='coerce').fillna(0)
        total_sold = sales['Продажная сумма'].sum()
        total_returned = sales['Возврат сумма'].sum()
        st.write(f"Umumiy sotuv: {total_sold}")
        st.write(f"Umumiy qaytgan: {total_returned}")

        # Foizlarni hisoblash
        sold_percent = (total_sold / total_orders)*100 if total_orders>0 else 0
        return_percent = (total_returned / total_orders)*100 if total_orders>0 else 0
        st.write(f"Sotilgan foizi: {sold_percent:.2f}%")
        st.write(f"Qaytgan foizi: {return_percent:.2f}%")

        # ==========================
        # Sana filteri
        # ==========================
        st.subheader("📅 Sana bo‘yicha filter")
        orders['Период'] = pd.to_datetime(orders['Период'], errors='coerce')
        sales['Период'] = pd.to_datetime(sales['Период'], errors='coerce')

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
        # Mahsulot bo‘yicha tahlil
        # ==========================
        st.subheader("🛒 Mahsulot bo‘yicha tahlil")

        product_orders = filtered_orders.groupby('Номенклатура')['Количество'].sum().reset_index()
        product_sales = filtered_sales.groupby('Номенклатура')['Продажная сумма'].sum().reset_index()
        product_returns = filtered_sales.groupby('Номенклатура')['Возврат сумма'].sum().reset_index()

        # Mahsulotlarni birlashtirish
        product_summary = product_orders.merge(product_sales, on='Номенклатура', how='left') \
                                        .merge(product_returns, on='Номенклатура', how='left') \
                                        .fillna(0)
        product_summary.rename(columns={'Количество':'Zakaz miqdori',
                                        'Продажная сумма':'Sotilgan summa',
                                        'Возврат сумма':'Qaytgan summa'}, inplace=True)
        st.dataframe(product_summary)

        # ==========================
        # Grafiklar
        # ==========================
        st.subheader("📈 Mahsulotlar grafiklari")

        def plot_bar(data, y_col, color, title):
            fig, ax = plt.subplots(figsize=(10,6))
            sns.barplot(data=data, x='Номенклатура', y=y_col, color=color)
            plt.xticks(rotation=45, ha='right')
            plt.title(title)
            st.pyplot(fig)

        plot_bar(product_summary, 'Zakaz miqdori', 'skyblue', "Mahsulotlar bo‘yicha Zakaz miqdori")
        plot_bar(product_summary, 'Sotilgan summa', 'green', "Mahsulotlar bo‘yicha Sotilgan summa")
        plot_bar(product_summary, 'Qaytgan summa', 'red', "Mahsulotlar bo‘yicha Qaytgan summa")

        # ==========================
        # Haftalik trendlar
        # ==========================
        st.subheader("📆 Haftalik trendlar")

        filtered_orders['weekday'] = filtered_orders['Период'].dt.day_name()
        filtered_sales['weekday'] = filtered_sales['Период'].dt.day_name()

        weekday_orders = filtered_orders.groupby('weekday')['Количество'].sum() \
                                       .reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).fillna(0)
        weekday_returns = filtered_sales.groupby('weekday')['Возврат количество'].sum() \
                                       .reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).fillna(0)

        st.write("Hafta kunlari bo‘yicha Zakazlar:")
        st.bar_chart(weekday_orders)

        st.write("Hafta kunlari bo‘yicha Qaytishlar:")
        st.bar_chart(weekday_returns)
