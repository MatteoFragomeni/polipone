import streamlit as st
import pandas as pd
from polipone_v_2_parte_1 import APP_TITLE, LOGO_FILE, load_data, save_all, calcola_classifica

# -----------------------------
# Configurazione pagina
# -----------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")

# -----------------------------
# CSS globale (layout nuovo, sfondo sfumato e leggibile)
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to bottom right, #a8c0ff, #3f2b96);
    color: #000000;
}

/* Header */
.header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
}
.header img {
    margin-right: 15px;
}
.header h1 {
    color: #ffffff;
}

/* Pulsanti grandi principali */
.main-button button {
    background-color: #004aad;
    color: white;
    font-size: 28px;
    padding: 40px;
    margin-bottom: 20px;
    width: 100%;
    border-radius: 20px;
    font-weight: bold;
}
.main-button button:hover {
    background-color: #0073ff;
}

/* Card interne */
.card {
    background-color: rgba(255,255,255,0.85);
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 15px;
    color: #000000;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown(f"""
<div class="header">
    <img src="{LOGO_FILE}" width="80">
    <h1>{APP_TITLE}</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("Pronostici Serie A con **🌟 Jolly** (ogni 2 giornate) e **⚔️ Sfide** (ogni 5 giornate).")

# -----------------------------
# Caricamento dati
# -----------------------------
utenti, pronostici, partite = load_data()

# -----------------------------
# Funzioni delle pagine
# -----------------------------
def page_classifica(utenti, pronostici, partite):
    st.subheader("Classifica aggiornata")
    classifica = calcola_classifica(utenti, pronostici, partite)
    for _, row in classifica.iterrows():
        st.markdown(f"""
        <div class="card">
            <h3 style="color:#004aad;">{row['utente']} 🏆</h3>
            <p><b>Punti:</b> {row['punti']} | 🌟 Jolly: {row['jolly_usati']} | ⚔️ Sfide: {row['gettoni_sfida']}</p>
        </div>
        """, unsafe_allow_html=True)
    if st.button("🔄 Aggiorna classifica"):
        classifica = calcola_classifica(utenti, pronostici, partite)
        st.success("Classifica aggiornata!")

def page_pronostici(utenti, pronostici, partite):
    st.subheader("📋 Gestione Pronostici")
    menu_pron = st.radio("Sottosezione", ["🖊️ Inserimento", "👀 Visualizza", "📊 Dashboard"], horizontal=True)
    
    giornate_disponibili = sorted(partite['giornata'].unique())
    if 'giornata_idx' not in st.session_state:
        st.session_state.giornata_idx = 0

    col_prev, col_curr, col_next = st.columns([1,2,1])
    with col_prev:
        if st.button("⬅️ Giornata precedente") and st.session_state.giornata_idx > 0:
            st.session_state.giornata_idx -= 1
    with col_curr:
        st.markdown(f"<h3 style='text-align:center;'>Giornata {giornate_disponibili[st.session_state.giornata_idx]}</h3>", unsafe_allow_html=True)
    with col_next:
        if st.button("➡️ Giornata successiva") and st.session_state.giornata_idx < len(giornate_disponibili)-1:
            st.session_state.giornata_idx += 1

    giornata_sel = giornate_disponibili[st.session_state.giornata_idx]
    partite_giornata = partite[partite['giornata'] == giornata_sel]

    # --- Inserimento pronostici ---
    if menu_pron == "🖊️ Inserimento":
        utente_sel = st.selectbox("Seleziona utente", utenti['utente'].tolist())
        st.markdown("### Inserisci pronostici")
        for _, row in partite_giornata.iterrows():
            with st.container():
                st.markdown(f"### {row['casa']} 🆚 {row['ospite']}")
                pron = st.radio("Pronostico", ['1','X','2'], key=f"{utente_sel}_{row['partita']}", horizontal=True)
                jolly_disponibile = (giornata_sel >= 2) and ((giornata_sel - 2) % 2 == 0)
                jolly = st.checkbox("🌟 Jolly", key=f"jolly_{utente_sel}_{row['partita']}", value=False, disabled=not jolly_disponibile)
                sfida_disponibile = (giornata_sel >= 5) and ((giornata_sel - 5) % 5 == 0)
                sfida = False
                sfidato = None
                if sfida_disponibile:
                    sfida = st.checkbox("⚔️ Sfida", key=f"sfida_{utente_sel}_{row['partita']}")
                    if sfida:
                        avversari = [u for u in utenti['utente'] if u != utente_sel]
                        sfidato = st.selectbox("Sfidato", avversari, key=f"sfidato_{utente_sel}_{row['partita']}")
                if st.button("💾 Salva pronostico", key=f"save_{utente_sel}_{row['partita']}"):
                    pronostici = pronostici[~((pronostici['utente']==utente_sel) & (pronostici['giornata']==giornata_sel) & (pronostici['partita']==row['partita']))]
                    pronostici = pd.concat([pronostici, pd.DataFrame([{
                        "utente": utente_sel,
                        "giornata": giornata_sel,
                        "partita": row['partita'],
                        "pronostico": pron,
                        "jolly": jolly,
                        "sfida": sfida,
                        "sfidato": sfidato
                    }])], ignore_index=True)
                    save_all(utenti, pronostici, partite)
                    st.success("Pronostico salvato!")

    # --- Visualizza ---
    elif menu_pron == "👀 Visualizza":
        utente_visualizza = st.selectbox("Seleziona utente", utenti['utente'].tolist())
        st.markdown(f"### Pronostici giornata {giornata_sel}")
        pron_salvati = pronostici[(pronostici['giornata']==giornata_sel) & (pronostici['utente']==utente_visualizza)]
        if pron_salvati.empty:
            st.info("Nessun pronostico inserito")
        else:
            for _, row in pron_salvati.iterrows():
                st.markdown(f"<div class='card'>{row['partita']}: {row['pronostico']}</div>", unsafe_allow_html=True)

    # --- Dashboard ---
    elif menu_pron == "📊 Dashboard":
        st.markdown(f"### Dashboard giornata {giornata_sel}")
        for _, row in partite_giornata.iterrows():
            with st.container():
                st.markdown(f"### {row['casa']} 🆚 {row['ospite']}")
                risultato_reale = row['risultato'] if row['risultato'] else "Non ancora registrato"
                st.markdown(f"**Risultato reale:** {risultato_reale}")
                pron_giornata = pronostici[pronostici['partita']==row['partita']]
                if not pron_giornata.empty:
                    cols = st.columns(len(utenti))
                    for i, utente in enumerate(utenti['utente']):
                        pron = pron_giornata[pron_giornata['utente']==utente]['pronostico']
                        jolly = pron_giornata[pron_giornata['utente']==utente]['jolly']
                        sfida = pron_giornata[pron_giornata['utente']==utente]['sfida']
                        pron_text = pron.values[0] if not pron.empty else "—"
                        badge = pron_text
                        if not jolly.empty and jolly.values[0]: badge += " 🌟"
                        if not sfida.empty and sfida.values[0]: badge += " ⚔️"
                        cols[i].markdown(f"<div class='card'><b>{utente}</b><br>{badge}</div>", unsafe_allow_html=True)
                st.markdown("---")

def page_partite(utenti, pronostici, partite):
    st.subheader("⚽ Gestione Partite")
    menu_partite = st.radio("Sottosezione", ["➕ Aggiungi partite", "📝 Aggiorna risultati", "📄 Visualizza tabella"], horizontal=True)
    # --- Inserimento ---
    if menu_partite == "➕ Aggiungi partite":
        col1, col2 = st.columns(2)
        with col1:
            casa = st.text_input("Squadra casa")
            ospite = st.text_input("Squadra ospite")
            quota1 = st.number_input("Quota 1", min_value=1.0, step=0.01)
            quotaX = st.number_input("Quota X", min_value=1.0, step=0.01)
            quota2 = st.number_input("Quota 2", min_value=1.0, step=0.01)
            giornata = st.number_input("Giornata", min_value=1, step=1)
        with col2:
            if st.button("➕ Aggiungi partita"):
                new_id = f"{casa}-{ospite}"
                partite = pd.concat([partite, pd.DataFrame([{
                    "giornata": giornata,
                    "partita": new_id,
                    "casa": casa,
                    "ospite": ospite,
                    "quota1": quota1,
                    "quotaX": quotaX,
                    "quota2": quota2,
                    "risultato": ""
                }])], ignore_index=True)
                save_all(utenti, pronostici, partite)
                st.success(f"Partita {new_id} aggiunta ✅")

    # --- Aggiorna risultati ---
    elif menu_partite == "📝 Aggiorna risultati":
        giornate_disponibili = sorted(partite['giornata'].unique())
        giornata_sel = st.selectbox("Seleziona giornata", giornate_disponibili)
        partite_giornata = partite[partite['giornata'] == giornata_sel]
        for _, row in partite_giornata.iterrows():
            risultato = st.text_input(f"{row['casa']} 🆚 {row['ospite']} (Giornata {giornata_sel})", value=row['risultato'] if row['risultato'] else "", key=f"risultato_{row['partita']}")
            if st.button("💾 Salva risultato", key=f"salva_ris_{row['partita']}"):
                partite.loc[partite['partita']==row['partita'], 'risultato'] = risultato
                save_all(utenti, pronostici, partite)
                st.success(f"Risultato {row['partita']} aggiornato ✅")

    # --- Visualizza ed elimina ---
    elif menu_partite == "📄 Visualizza tabella":
        giornate_disponibili = sorted(partite['giornata'].unique())
        giornata_sel = st.selectbox("Seleziona giornata", giornate_disponibili)
        partite_giornata = partite[partite['giornata'] == giornata_sel]
        st.markdown(f"### 📅 Partite giornata {giornata_sel}")
        if partite_giornata.empty:
            st.info("Nessuna partita registrata per questa giornata.")
        else:
            for _, row in partite_giornata.iterrows():
                st.markdown(f"""
                <div class='card'>
                    <h4>{row['casa']} 🆚 {row['ospite']}</h4>
                    <p>Quote → 1: {row['quota1']} | X: {row['quotaX']} | 2: {row['quota2']}</p>
                    <p>Risultato: {row['risultato'] if row['risultato'] else '—'}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"❌ Elimina {row['casa']} - {row['ospite']}", key=f"del_{row['partita']}"):
                    partite = partite[partite['partita'] != row['partita']]
                    save_all(utenti, pronostici, partite)
                    st.warning(f"Partita {row['casa']} - {row['ospite']} eliminata 🚮")
                    st.experimental_rerun()

def page_utenti(utenti, pronostici, partite):
    st.subheader("Gestione Utenti")
    nuovo_utente = st.text_input("Nome nuovo utente")
    if st.button("➕ Aggiungi utente"):
        if nuovo_utente not in utenti['utente'].values:
            utenti = pd.concat([utenti, pd.DataFrame([{
                "utente": nuovo_utente,
                "punti": 0.0,
                "jolly_usati": 0,
                "gettoni_sfida": 0
            }])], ignore_index=True)
            save_all(utenti, pronostici, partite)
            st.success(f"Utente {nuovo_utente} aggiunto")
    utente_da_eliminare = st.selectbox("Seleziona utente da eliminare", utenti['utente'].tolist())
    if st.button("❌ Elimina utente"):
        utenti = utenti[utenti['utente'] != utente_da_eliminare]
        save_all(utenti, pronostici, partite)
        st.success(f"Utente {utente_da_eliminare} eliminato")
    st.dataframe(utenti)

# -----------------------------
# Menu principale stile app
# -----------------------------
st.markdown("## Seleziona sezione")
if st.button("📊 Classifica"):
    st.session_state['page'] = "classifica"
if st.button("📝 Pronostici"):
    st.session_state['page'] = "pronostici"
if st.button("⚽ Gestione Partite"):
    st.session_state['page'] = "partite"
if st.button("👥 Gestione Utenti"):
    st.session_state['page'] = "utenti"

# -----------------------------
# Mostra pagina scelta
# -----------------------------
page = st.session_state.get('page', 'classifica')
if page == "classifica":
    page_classifica(utenti, pronostici, partite)
elif page == "pronostici":
    page_pronostici(utenti, pronostici, partite)
elif page == "partite":
    page_partite(utenti, pronostici, partite)
elif page == "utenti":
    page_utenti(utenti, pronostici, partite)