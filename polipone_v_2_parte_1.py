import streamlit as st
import pandas as pd
import gspread
from gspread.exceptions import APIError, WorksheetNotFound
from google.oauth2.service_account import Credentials
import json
import time

APP_TITLE = "Polipone 🐙⚽"
LOGO_FILE = "logo.png"

# -----------------------------
# Google Sheets setup
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

service_account_info = json.loads(st.secrets["google"]["service_account"])
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
gc = gspread.authorize(creds)

SHEET_ID = st.secrets["google"]["sheet_id"]
UTENTI_SHEET_NAME = st.secrets["google"]["utenti_sheet_name"]
PRONOSTICI_SHEET_NAME = st.secrets["google"]["pronostici_sheet_name"]
PARTITE_SHEET_NAME = st.secrets["google"]["partite_sheet_name"]

# -----------------------------
# Funzioni di lettura / scrittura sicure
# -----------------------------
def safe_read_sheet(sheet_name, retries=3, delay=2):
    for attempt in range(retries):
        try:
            sh = gc.open_by_key(SHEET_ID)
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except APIError:
            if attempt < retries - 1: time.sleep(delay)
            else:
                st.error(f"Impossibile leggere '{sheet_name}' dopo {retries} tentativi.")
                return pd.DataFrame()
        except WorksheetNotFound:
            st.error(f"Foglio '{sheet_name}' non trovato.")
            return pd.DataFrame()

def safe_write_sheet(df, sheet_name, retries=3, delay=2):
    for attempt in range(retries):
        try:
            sh = gc.open_by_key(SHEET_ID)
            try:
                ws = sh.worksheet(sheet_name)
                ws.clear()  # Non cancellare il foglio, solo pulirlo
            except WorksheetNotFound:
                ws = sh.add_worksheet(title=sheet_name, rows=df.shape[0]+10, cols=df.shape[1]+5)
            ws.update([df.columns.values.tolist()] + df.values.tolist())
            return True
        except APIError:
            if attempt < retries - 1: time.sleep(delay)
            else:
                st.error(f"Impossibile scrivere su '{sheet_name}' dopo {retries} tentativi.")
                return False

# -----------------------------
# Caricamento dati in memoria con caching
# -----------------------------
@st.cache_data(ttl=600)
def load_data():
    utenti = safe_read_sheet(UTENTI_SHEET_NAME)
    pronostici = safe_read_sheet(PRONOSTICI_SHEET_NAME)
    partite = safe_read_sheet(PARTITE_SHEET_NAME)

    if not utenti.empty:
        utenti['punti'] = utenti['punti'].fillna(0).astype(float)
    return utenti, pronostici, partite

def save_all(utenti, pronostici, partite):
    safe_write_sheet(utenti, UTENTI_SHEET_NAME)
    safe_write_sheet(pronostici, PRONOSTICI_SHEET_NAME)
    safe_write_sheet(partite, PARTITE_SHEET_NAME)

# -----------------------------
# Funzioni classifica
# -----------------------------
def get_quota(match_row, pron):
    col = f"quota{pron}"
    try: return float(match_row[col])
    except Exception: return None

def calcola_classifica(utenti, pronostici, partite):
    utenti = utenti.copy()
    utenti['punti'] = 0.0
    partite_idx = {(int(r['giornata']), str(r['partita'])): r for _, r in partite.iterrows()}

    for _, p in pronostici.iterrows():
        g = int(p['giornata'])
        rid = str(p['partita'])
        key = (g, rid)
        if key not in partite_idx: continue
        m = partite_idx[key]
        risultato = str(m.get('risultato','')).strip()
        pron = str(p['pronostico']).strip()
        jolly = bool(p.get('jolly', False))
        sfida = bool(p.get('sfida', False))
        sfidato = p.get('sfidato', None)
        quota = get_quota(m, pron)
        if quota is None: continue

        delta = 0.0
        if risultato in ['1','X','2']:
            if pron == risultato:
                delta = quota * (2 if jolly else 1)
            else:
                delta = -2*quota if jolly else 0.0
            utenti.loc[utenti['utente']==p['utente'],'punti'] += float(delta)

            if sfida and sfidato and sfidato in utenti['utente'].values:
                mask_sfidato = (pronostici['utente']==sfidato)&(pronostici['giornata']==g)&(pronostici['partita']==rid)
                if mask_sfidato.any():
                    pron_sfidato = pronostici.loc[mask_sfidato,'pronostico'].values[0]
                    quota_sfidato = get_quota(m,pron_sfidato)
                    if pron==risultato and pron_sfidato!=risultato:
                        utenti.loc[utenti['utente']==sfidato,'punti'] -= quota_sfidato
                    elif pron!=risultato and pron_sfidato==risultato:
                        utenti.loc[utenti['utente']==p['utente'],'punti'] -= quota
    return utenti.sort_values('punti',ascending=False).reset_index(drop=True)




