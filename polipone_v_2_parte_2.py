import streamlit as st
import pandas as pd
from polipone_v_2_parte_1 import APP_TITLE, LOGO_FILE, load_data, save_all, calcola_classifica

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Polipone", layout="wide")
cols = st.columns([1,6])
with cols[0]:
    if LOGO_FILE.exists():
        st.image(str(LOGO_FILE), width=100)
with cols[1]:
    st.title(APP_TITLE)
    st.caption("Pronostici Serie A con Jolly (ogni 2 giornate) e Sfide (ogni 5 giornate).")

utenti, pronostici, partite = load_data()

menu = st.sidebar.radio("Navigazione", ["Classifica","Pronostici","Gestione Partite (Admin)","Gestione Utenti (Admin)"], index=0)

# -----------------------------
# Classifica
# -----------------------------
if menu=="Classifica":
    st.subheader("Classifica aggiornata")
    classifica = calcola_classifica(utenti,pronostici,partite)
    st.dataframe(classifica)

# -----------------------------
# Pronostici
# -----------------------------
elif menu=="Pronostici":
    st.subheader("Inserisci pronostici per la giornata")
    utente_sel = st.selectbox("Seleziona utente", utenti['utente'].tolist())
    giornate_disponibili = sorted(partite['giornata'].unique())
    giornata_sel = st.selectbox("Seleziona giornata", giornate_disponibili)
    partite_giornata = partite[partite['giornata']==giornata_sel]
    for idx,row in partite_giornata.iterrows():
        pron = st.radio(f"{row['casa']} vs {row['ospite']}", ['1','X','2'], key=f"{utente_sel}_{row['partita']}")
        jolly_disponibile = (giornata_sel>=2) and ((giornata_sel-2)%2==0)
        jolly = st.checkbox("Jolly", key=f"jolly_{utente_sel}_{row['partita']}", value=False, disabled=not jolly_disponibile)
        sfida_disponibile = (giornata_sel>=5) and ((giornata_sel-5)%5==0)
        sfida = False
        sfidato = None
        if sfida_disponibile:
            sfida = st.checkbox("Sfida", key=f"sfida_{utente_sel}_{row['partita']}")
            if sfida:
                avversari = [u for u in utenti['utente'] if u!=utente_sel]
                sfidato = st.selectbox("Seleziona avversario", avversari, key=f"sfidato_{utente_sel}_{row['partita']}")
        if st.button(f"Salva pronostico {row['partita']}", key=f"save_{utente_sel}_{row['partita']}"):
            pronostici = pronostici[~((pronostici['utente']==utente_sel)&(pronostici['giornata']==giornata_sel)&(pronostici['partita']==row['partita']))]
            pronostici = pd.concat([pronostici, pd.DataFrame([{"utente":utente_sel,"giornata":giornata_sel,"partita":row['partita'],"pronostico":pron,"jolly":jolly,"sfida":sfida,"sfidato":sfidato}])], ignore_index=True)
            save_all(utenti,pronostici,partite)
            st.success(f"Pronostico salvato per {row['partita']}")

# -----------------------------
# Gestione Partite
# -----------------------------
elif menu=="Gestione Partite (Admin)":
    st.subheader("Gestione partite")
    col1,col2 = st.columns(2)
    with col1:
        casa = st.text_input("Squadra casa")
        ospite = st.text_input("Squadra ospite")
        quota1 = st.number_input("Quota 1", min_value=1.0, step=0.01)
        quotaX = st.number_input("Quota X", min_value=1.0, step=0.01)
        quota2 = st.number_input("Quota 2", min_value=1.0, step=0.01)
        giornata = st.number_input("Giornata", min_value=1, step=1)
    with col2:
        if st.button("Aggiungi partita"):
            new_id = f"{casa}-{ospite}"
            partite = pd.concat([partite, pd.DataFrame([{"giornata":giornata,"partita":new_id,"casa":casa,"ospite":ospite,"quota1":quota1,"quotaX":quotaX,"quota2":quota2,"risultato":""}])], ignore_index=True)
            save_all(utenti,pronostici,partite)
            st.success(f"Partita {new_id} aggiunta")
    st.dataframe(partite)

# -----------------------------
# Gestione Utenti
# -----------------------------
elif menu=="Gestione Utenti (Admin)":
	st.subheader("Gestione utenti")

# Aggiungi utente
nuovo_utente = st.text_input("Nome nuovo utente")
if st.button("Aggiungi utente"):
    if nuovo_utente not in utenti['utente'].values:
        utenti = pd.concat([utenti, pd.DataFrame([{"utente":nuovo_utente,"punti":0.0,"jolly_usati":0,"gettoni_sfida":0}])], ignore_index=True)
        save_all(utenti,pronostici,partite)
        st.success(f"Utente {nuovo_utente} aggiunto")

# Elimina utente
utente_da_eliminare = st.selectbox("Seleziona utente da eliminare", utenti['utente'].tolist())
if st.button("Elimina utente"):
    utenti = utenti[utenti['utente'] != utente_da_eliminare]
    save_all(utenti,pronostici,partite)
    st.success(f"Utente {utente_da_eliminare} eliminato")

# Mostra tabella utenti aggiornata
st.dataframe(utenti)



