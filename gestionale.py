import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="CRM Gestionale 2026", layout="wide", initial_sidebar_state="expanded")

# 2. Funzione per caricare e mettere in cache i dati
@st.cache_data
def load_data():
    file_path = "Gestionale 2026.xlsx"
    
    # Leggi i fogli principali
    df_ordini = pd.read_excel(file_path, sheet_name='Ordini', engine='openpyxl')
    df_prodotti = pd.read_excel(file_path, sheet_name='Prodotti Magazzino', engine='openpyxl')
    
    # Converte la data in un formato datetime per facilitare i calcoli
    df_ordini['Data ordine'] = pd.to_datetime(df_ordini['Data ordine'], errors='coerce')
    
    return df_ordini, df_prodotti

df_ordini, df_prodotti = load_data()

# 3. Interfaccia Utente - Titolo
st.title("📊 CRM Gestionale 2026")
st.markdown("---")

# 4. Sidebar per i Filtri
st.sidebar.header("🔍 Filtra Dati Ordini")

# Filtro per Marketplace
marketplaces = df_ordini['Marketplace'].dropna().unique().tolist()
mercati_selezionati = st.sidebar.multiselect(
    "Seleziona Marketplace:", 
    options=marketplaces, 
    default=marketplaces
)

# Filtro date (opzionale, per intervalli)
min_date = df_ordini['Data ordine'].min()
max_date = df_ordini['Data ordine'].max()
if pd.notna(min_date) and pd.notna(max_date):
    start_date, end_date = st.sidebar.date_input(
        "Seleziona un intervallo di date:", 
        [min_date.date(), max_date.date()]
    )
    # Applica i filtri
    mask = (
        (df_ordini['Marketplace'].isin(mercati_selezionati)) & 
        (df_ordini['Data ordine'].dt.date >= start_date) & 
        (df_ordini['Data ordine'].dt.date <= end_date)
    )
    df_filtrato = df_ordini.loc[mask]
else:
    df_filtrato = df_ordini[df_ordini['Marketplace'].isin(mercati_selezionati)]


# 5. Metriche Principali (KPIs)
col1, col2, col3, col4 = st.columns(4)

with col1:
    fatturato_totale = df_filtrato['Fatturato (Lordo)'].sum()
    st.metric(label="💶 Fatturato Lordo", value=f"€ {fatturato_totale:,.2f}")

with col2:
    utile_totale = df_filtrato['Utile '].sum()
    st.metric(label="📈 Utile Netto", value=f"€ {utile_totale:,.2f}")

with col3:
    ordini_totali = len(df_filtrato)
    st.metric(label="📦 Numero Ordini", value=ordini_totali)

with col4:
    costi_logistica = df_filtrato['Costo logistico'].sum()
    st.metric(label="🚚 Costi Logistici", value=f"€ {costi_logistica:,.2f}")

st.markdown("---")

# 6. Organizzazione a Tab per navigare facilmente
tab1, tab2, tab3 = st.tabs(["🛒 Lista Ordini", "📦 Magazzino", "📊 Grafici"])

with tab1:
    st.subheader("Dettaglio Ordini Filtrati")
    # Mostra la tabella interattiva degli ordini
    st.dataframe(
        df_filtrato[['Data ordine', 'Marketplace', 'Prodotto (SKU o nome)', 'Fatturato (Lordo)', 'Utile ', 'Stato ordine']],
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.subheader("Situazione Stock e Riordini")
    
    # Rimuove le colonne superflue o vuote come 'Unnamed: 9' se presente
    colonne_magazzino = [col for col in df_prodotti.columns if not str(col).startswith('Unnamed')]
    df_prod_pulito = df_prodotti[colonne_magazzino]
    
    st.dataframe(
        df_prod_pulito[['Prodotto (SKU o nome)', 'Stock (A magazzino)', 'Copertura stock (Giorni)', 'Quantità da ordinare', 'Allert Riordino']],
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.subheader("Andamento Vendite")
    
    # Prepara i dati raggruppati per Marketplace per il grafico a barre
    if not df_filtrato.empty:
        vendite_market = df_filtrato.groupby('Marketplace')['Fatturato (Lordo)'].sum()
        st.bar_chart(vendite_market)
        
        st.write("Utile generato per Prodotto")
        utile_prodotto = df_filtrato.groupby('Prodotto (SKU o nome)')['Utile '].sum()
        st.bar_chart(utile_prodotto)
    else:
        st.info("Nessun dato disponibile con i filtri selezionati.")