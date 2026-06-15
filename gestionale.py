import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------
# 1. CONFIGURAZIONE PAGINA E STILE
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
# 3. CARICAMENTO DATI
# -----------------------------------------
@st.cache_data(ttl=3600)
def load_data():
    file_path = "Gestionale 2026.xlsx" 
    try:
        df_ordini = pd.read_excel(file_path, sheet_name='Ordini', engine='openpyxl')
        df_prodotti = pd.read_excel(file_path, sheet_name='Prodotti Magazzino', engine='openpyxl')
        df_ordini['Data ordine'] = pd.to_datetime(df_ordini['Data ordine'], errors='coerce')
        return df_ordini, df_prodotti
    except Exception as e:
        st.error(f"Errore nella lettura del file Excel: {e}")
        st.stop()

# =========================================
# ESECUZIONE PRINCIPALE DELL'APP
# =========================================
if check_password():
    
    df_ordini, df_prodotti = load_data()

    # --- SIDEBAR E FILTRI ---
    with st.sidebar:
        st.title("⚙️ Pannello di Controllo")
        
        if st.button("🔄 Ricarica Dati", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("---")
        st.header("🔍 Filtri Vendite")
        
        # Filtro Date
        min_date = df_ordini['Data ordine'].min()
        max_date = df_ordini['Data ordine'].max()
        
        if pd.notna(min_date) and pd.notna(max_date):
            date_range = st.date_input(
                "Seleziona Periodo:",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date()
            )
        else:
            date_range = ()

        # Filtro Marketplace
        marketplaces = df_ordini['Marketplace'].dropna().unique().tolist()
        mercati_selezionati = st.multiselect(
            "Seleziona Marketplace:", 
            options=marketplaces, 
            default=marketplaces
        )
        
        # Applica i filtri
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            
            mask = (
                (df_ordini['Marketplace'].isin(mercati_selezionati)) &
                (df_ordini['Data ordine'] >= start_date) &
                (df_ordini['Data ordine'] <= end_date)
            )
            df_filtrato = df_ordini.loc[mask]
        else:
            df_filtrato = df_ordini[df_ordini['Marketplace'].isin(mercati_selezionati)]

    # --- INTESTAZIONE DASHBOARD ---
    st.title("🚀 CRM Gestionale 2026")
    st.markdown("---")

    # --- CREAZIONE DELLE 4 SCHEDE (TABS) ---
    tab_action, tab_ordini, tab_magazzino, tab_cashflow = st.tabs([
        "🎯 Action Plan Oggi", 
        "📈 Analisi Vendite", 
        "📦 Stato Magazzino",
        "💼 Cash Flow & Resi"
    ])

    # -----------------------------------------
    # TAB 1: LOGICA DECISIONALE (AZIONI)
    # -----------------------------------------
    with tab_action:
        st.header("📋 Priorità e Azioni Suggerite")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚨 Allerta Riordini (Stock)")
            sotto_scorta = df_prodotti[df_prodotti['Stock (A magazzino)'] <= df_prodotti['Punto di riordino (Stock minimo da avere)']]
            
            if not sotto_scorta.empty:
                st.error(f"Attenzione: {len(sotto_scorta)} prodotti da ordinare!")
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

        st.markdown("---")
        
        st.subheader("🔄 Allarme Resi (Impatto Economico)")
        df_ordini_resi = df_filtrato.copy()
        
        if 'Quantità resi effettiva' in df_ordini_resi.columns:
            df_ordini_resi['Quantità resi effettiva'] = df_ordini_resi['Quantità resi effettiva'].fillna(0)
            resi_effettuati = df_ordini_resi[df_ordini_resi['Quantità resi effettiva'] > 0]
            
            if not resi_effettuati.empty:
                logistica_bruciata = resi_effettuati['Costo logistico'].sum()
                utile_perso = resi_effettuati['Utile '].sum()
                
                st.warning(f"⚠️ Attenzione: I resi filtrati ti sono costati **€ {logistica_bruciata:,.2f}** di logistica a vuoto e hanno azzerato **€ {utile_perso:,.2f}** di utile.")
                
                top_resi = resi_effettuati.groupby('Prodotto (SKU o nome)')['Quantità resi effettiva'].sum().reset_index()
                st.dataframe(top_resi.sort_values(by='Quantità resi effettiva', ascending=False), hide_index=True, use_container_width=True)
            else:
                st.success("✅ Nessun reso registrato nei dati filtrati.")

    # -----------------------------------------
    # TAB 2: ANALISI VENDITE E GRAFICI
    # -----------------------------------------
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

    # -----------------------------------------
    # TAB 3: MAGAZZINO COMPLETO
    # -----------------------------------------
    with tab_magazzino:
        st.header("📦 Inventario e Dati Prodotti")
        colonne_pulite = [c for c in df_prodotti.columns if not str(c).startswith('Unnamed')]
        st.dataframe(df_prodotti[colonne_pulite], use_container_width=True, hide_index=True)

    # -----------------------------------------
    # TAB 4: CASH FLOW E FONDI IN TRANSITO
    # -----------------------------------------
    with tab_cashflow:
        st.header("⚖️ Riconciliazione e Previsione Incassi")
        st.write("Inserisci i movimenti reali del conto corrente per il periodo filtrato. Il sistema calcolerà il disallineamento e stimerà i fondi in transito in base allo Stato dell'Ordine.")
        
        col_in, col_out, col_results = st.columns([1, 1, 2])
        
        with col_in:
            st.subheader("Entrate Reali")
            incassi = st.number_input("💰 Bonifici ricevuti (€):", min_value=0.0, value=0.0, step=100.0)
            
        with col_out:
            st.subheader("Uscite Reali")
            uscite = st.number_input("💸 Pagamenti (fornitori, logistica, ads) (€):", min_value=0.0, value=0.0, step=100.0)
            
        with col_results:
            st.subheader("Confronto Decisionale")
            
            cash_flow_reale = incassi - uscite
            utile_teorico_excel = df_filtrato['Utile '].sum()
            disallineamento = cash_flow_reale - utile_teorico_excel
            
            st.metric("Flusso di Cassa Reale (Banca)", f"€ {cash_flow_reale:,.2f}")
            st.metric("Utile Teorico (Da Excel)", f"€ {utile_teorico_excel:,.2f}")
            
            if disallineamento < 0:
                st.error(f"⚠️ Buco di Cassa: € {disallineamento:,.2f}")
            elif disallineamento > 0:
                st.success(f"📈 Extra Cassa: + € {disallineamento:,.2f}")
            else:
                st.info("I conti tornano perfettamente.")
        
        st.markdown("---")
        
        # --- CALCOLO FONDI BLOCCATI BASATO SULLO STATO ORDINE ---
        st.subheader("⏳ Stima dei Fondi in Transito (Soldi Ostaggio)")
        
        if 'Stato ordine' in df_filtrato.columns and not df_filtrato.empty:
            # Trova tutti gli stati possibili presenti nel file
            stati_disponibili = df_filtrato['Stato ordine'].dropna().unique().tolist()
            
            # Di default, seleziona tutto ciò che NON è "Pagato"
            stati_non_pagati_default = [s for s in stati_disponibili if str(s).strip().lower() != 'pagato']
            
            # L'utente può scegliere dal menu a tendina quali stati considerare "in sospeso"
            stati_in_sospeso = st.multiselect(
                "Quali stati indicano che i soldi devono ancora arrivare?",
                options=stati_disponibili,
                default=stati_non_pagati_default
            )
            
            # Filtra gli ordini in base agli stati selezionati
            ordini_in_sospeso = df_filtrato[df_filtrato['Stato ordine'].isin(stati_in_sospeso)]
            
            if not ordini_in_sospeso.empty:
                # Stima bonifico: Fatturato Lordo meno Fee
                fondi_in_arrivo = ordini_in_sospeso['Fatturato (Lordo)'].sum() - ordini_in_sospeso['Fee (€)'].sum()
                st.info(f"💶 Hai **{len(ordini_in_sospeso)} ordini** segnati come non pagati. Il valore netto atteso dai marketplace è di **€ {fondi_in_arrivo:,.2f}**.")
                
                # Riconciliazione finale
                if disallineamento < 0:
                    recupero = abs(disallineamento) - fondi_in_arrivo
                    if recupero <= 0:
                        st.success("✅ **Niente panico!** Il tuo disallineamento di cassa è interamente giustificato e coperto dagli ordini in sospeso.")
                    else:
                        st.warning(f"⚠️ **Attenzione:** I soldi in arrivo coprono solo una parte del buco. Ci sono ancora **€ {recupero:,.2f}** mancanti (potrebbero essere investimenti in merce o altre spese fisse).")
            else:
                st.success("Tutti gli ordini nel periodo selezionato risultano incassati. Nessun fondo in sospeso!")
        else:
            st.info("Nessun dato disponibile o colonna 'Stato ordine' mancante nel file Excel.")
