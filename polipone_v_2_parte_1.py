import streamlit as st
import pandas as pd
from pathlib import Path

APP_TITLE = "Polipone 🐙⚽"
UTENTI_FILE = Path("utenti.csv")
PRONOSTICI_FILE = Path("pronostici.csv")
PARTITE_FILE = Path("partite.csv")
LOGO_FILE = Path("logo.png")

# -----------------------------
# Utility
# -----------------------------
def ensure_csv(path: Path, columns: list):
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)

def load_data():
    ensure_csv(UTENTI_FILE, ["utente", "punti", "jolly_usati", "gettoni_sfida"])
    ensure_csv(PRONOSTICI_FILE, ["utente", "giornata", "partita", "pronostico", "jolly", "sfida", "sfidato"])
    ensure_csv(PARTITE_FILE, ["giornata", "partita", "casa", "ospite", "quota1", "quotaX", "quota2", "risultato"])
    utenti = pd.read_csv(UTENTI_FILE)
    pronostici = pd.read_csv(PRONOSTICI_FILE)
    partite = pd.read_csv(PARTITE_FILE)
    utenti['punti'] = utenti['punti'].fillna(0).astype(float)
    return utenti, pronostici, partite

def save_all(utenti, pronostici, partite):
    utenti.to_csv(UTENTI_FILE, index=False)
    pronostici.to_csv(PRONOSTICI_FILE, index=False)
    partite.to_csv(PARTITE_FILE, index=False)

def get_quota(match_row, pron):
    col = f"quota{pron}"
    try:
        return float(match_row[col])
    except Exception:
        return None

# -----------------------------
# Scoring logic
# -----------------------------
def calcola_classifica(utenti, pronostici, partite):
    utenti = utenti.copy()
    utenti['punti'] = 0.0
    partite_idx = {(int(r['giornata']), str(r['partita'])): r for _, r in partite.iterrows()}

    for _, p in pronostici.iterrows():
        g = int(p['giornata'])
        rid = str(p['partita'])
        key = (g, rid)
        if key not in partite_idx:
            continue
        m = partite_idx[key]
        risultato = str(m.get('risultato','')).strip()
        pron = str(p['pronostico']).strip()
        jolly = bool(p.get('jolly', False))
        sfida = bool(p.get('sfida', False))
        sfidato = p.get('sfidato', None)
        quota = get_quota(m, pron)
        if quota is None:
            continue
        delta = 0.0
        if risultato in ['1','X','2']:
            if pron==risultato:
                delta = quota*(2 if jolly else 1)
            else:
                delta = -2*quota if jolly else 0.0
            utenti.loc[utenti['utente']==p['utente'],'punti'] += float(delta)
            # sfida
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
