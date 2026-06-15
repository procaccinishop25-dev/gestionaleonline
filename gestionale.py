import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------
# 1. CONFIGURAZIONE PAGINA
# -----------------------------------------
st.set_page_config(
    page_title="CRM Decisionale 2026", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------
# 2. SISTEMA DI SICUREZZA (PASSWORD)
# -----------------------------------------
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Accesso Riservato")
        st.text_input(
            "Inserisci la password per accedere al CRM:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Accesso Riservato")
        st.text_input(
            "Password errata. Riprova:",
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error("Accesso negato. Password non valida.")
        return False
    else:
        return True

# -----------------------------------------
# 3. CARICAMENTO DATI (DA GITHUB)
# -----------------------------------------
# Uso ttl=3600 (1 ora) ma la cache si resetta anche quando premi il pulsante o quando aggiorni GitHub
@st.cache_data(ttl=3600)
def load_data():
    file_path = "Gestionale 2026.xlsx" # Legge il file caricato nel repository
    try:
        df_ordini = pd.read_excel(file_path, sheet_name='Ordini', engine='openpyxl')
        df_prodotti = pd.read_excel(file_path, sheet_name='Prodotti Magazzino', engine='openpyxl')
        df_ordini['Data ordine'] = pd.to_datetime(df_ordini['Data ordine'], errors='coerce')
        return df_ordini, df_prodotti
    except Exception as e:
        st.error(f"Errore nella lettura del file Excel: {e}")
        st.stop()

# Esecuzione principale
if check_password():
    
    df_ordini, df_prodotti = load_data()

    # --- SIDEBAR E FILTRI ---
    with st.sidebar:
        st.title("⚙️ Pannello di Controllo")
        
        # Pulsante utilissimo: se hai appena caricato il file su GitHub, premi qui per forzare l'aggiornamento
        if st.button("🔄 Ricarica Dati", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("---")
        st.header("🔍 Filtri Vendite")
        
        marketplaces = df_ordini['Marketplace'].dropna().unique().tolist()
        mercati_selezionati = st.multiselect(
            "Seleziona Marketplace:", 
            options=marketplaces, 
            default=marketplaces
        )
        df_filtrato = df_ordini[df_ordini['Marketplace'].isin(mercati_selezionati)]

    # --- DASHBOARD PRINCIPALE ---
    st.title("🚀 CRM Gestionale 2026")
    st.markdown("---")

    # Creazione delle Schede (Tabs)
    tab_action, tab_ordini, tab_magazzino = st.tabs([
        "🎯 Action Plan Oggi", 
        "📈 Analisi Vendite", 
        "📦 Stato Magazzino"
    ])

    # --- TAB 1: LOGICA DECISIONALE ---
    with tab_action:
        st.header("📋 Priorità e Azioni Suggerite")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚨 Allerta Riordini (Stock)")
            sotto_scorta = df_prodotti[df_prodotti['Stock (A magazzino)'] <= df_prodotti['Punto di riordino (Stock minimo da avere)']]
            
            if not sotto_scorta.empty:
                st.error(f"Attenzione: {len(sotto_scorta)} prodotti da ordinare dal fornitore!")
                st.dataframe(sotto_scorta[['Prodotto (SKU o nome)', 'Stock (A magazzino)', 'Quantità da ordinare']], hide_index=True, use_container_width=True)
            else:
                st.success("✅ Tutte le scorte sono sopra il livello di guardia.")
                
        with col2:
            st.subheader("⚖️ Allerta Margini (< 15%)")
            if not df_filtrato.empty:
                margini = df_filtrato.groupby('Prodotto (SKU o nome)').agg({'Fatturato (Lordo)': 'sum', 'Utile ': 'sum'}).reset_index()
                margini['Margine %'] = (margini['Utile '] / margini['Fatturato (Lordo)']) * 100
                
                critici = margini[margini['Margine %'] < 15]
                if not critici.empty:
                    st.warning("Valutare aumento prezzo o riduzione costi per questi prodotti:")
                    st.dataframe(critici.style.format({'Margine %': '{:.1f}%', 'Fatturato (Lordo)': '€ {:.2f}', 'Utile ': '€ {:.2f}'}), hide_index=True, use_container_width=True)
                else:
                    st.success("✅ Nessun prodotto presenta margini critici.")
            else:
                st.info("Nessun dato di vendita per i filtri selezionati.")

    # --- TAB 2: ANALISI VENDITE E GRAFICI ---
    with tab_ordini:
        st.header("📊 Andamento Economico e Marketplace")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Fatturato Lordo", f"€ {df_filtrato['Fatturato (Lordo)'].sum():,.2f}")
        c2.metric("Utile Netto", f"€ {df_filtrato['Utile '].sum():,.2f}")
        c3.metric("Ordini Effettuati", len(df_filtrato))
        c4.metric("Costi Logistica", f"€ {df_filtrato['Costo logistico'].sum():,.2f}")
        
        st.markdown("---")
        
        if not df_filtrato.empty:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("Fatturato per Canale")
                fig1 = px.bar(df_filtrato.groupby('Marketplace')['Fatturato (Lordo)'].sum().reset_index(), x='Marketplace', y='Fatturato (Lordo)', color='Marketplace', text_auto='.2s')
                st.plotly_chart(fig1, use_container_width=True)
                
            with col_chart2:
                st.subheader("Incidenza Fee per Canale")
                resa = df_filtrato.groupby('Marketplace').agg({'Fatturato (Lordo)': 'sum', 'Fee (€)': 'sum'}).reset_index()
                resa['% Fee'] = (resa['Fee (€)'] / resa['Fatturato (Lordo)']) * 100
                fig2 = px.bar(resa, x='Marketplace', y='% Fee', color='Marketplace', text_auto='.1f')
                fig2.update_layout(yaxis_title="Percentuale Fee (%)")
                st.plotly_chart(fig2, use_container_width=True)

    # --- TAB 3: MAGAZZINO COMPLETO ---
    with tab_magazzino:
        st.header("📦 Inventario e Dati Prodotti")
        colonne_pulite = [c for c in df_prodotti.columns if not str(c).startswith('Unnamed')]
        st.dataframe(df_prodotti[colonne_pulite], use_container_width=True, hide_index=True)
