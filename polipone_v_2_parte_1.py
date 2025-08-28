import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

APP_TITLE = "Polipone 🐙⚽"
LOGO_FILE = "logo.png"  # Path del logo
SHEET_NAME = "polipone_data"  # Nome del tuo Google Sheet
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Autenticazione Google Sheets
creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
gc = gspread.authorize(creds)

# -----------------------------
# Utility
# -----------------------------
def load_data():
    """Carica dati da Google Sheet nelle tre tabelle principali."""
    sh = gc.open(SHEET_NAME)
    
    # Leggi dati dai fogli
    utenti = pd.DataFrame(sh.worksheet("utenti").get_all_records())
    pronostici = pd.DataFrame(sh.worksheet("pronostici").get_all_records())
    partite = pd.DataFrame(sh.worksheet("partite").get_all_records())
    
    # Assicura che tutte le colonne esistano
    for df, cols in [
        (utenti, ["utente", "punti", "jolly_usati", "gettoni_sfida"]),
        (pronostici, ["utente", "giornata", "partita", "pronostico", "jolly", "sfida", "sfidato"]),
        (partite, ["giornata", "partita", "casa", "ospite", "quota1", "quotaX", "quota2", "risultato"])
    ]:
        for c in cols:
            if c not in df.columns:
                df[c] = ""
    
    # Conversione tipi
    utenti['punti'] = utenti['punti'].fillna(0).astype(float)
    
    return utenti, pronostici, partite

def save_all(utenti, pronostici, partite):
    """Salva i DataFrame su Google Sheets sovrascrivendo i fogli."""
    sh = gc.open(SHEET_NAME)
    
    # Salva utenti
    sh.worksheet("utenti").clear()
    sh.worksheet("utenti").update([utenti.columns.tolist()] + utenti.values.tolist())
    
    # Salva pronostici
    sh.worksheet("pronostici").clear()
    sh.worksheet("pronostici").update([pronostici.columns.tolist()] + pronostici.values.tolist())
    
    # Salva partite
    sh.worksheet("partite").clear()
    sh.worksheet("partite").update([partite.columns.tolist()] + partite.values.tolist())

# -----------------------------
# Funzioni di supporto per classifica
# -----------------------------
def get_quota(match_row, pron):
    col = f"quota{pron}"
    try:
        return float(match_row[col])
    except Exception:
        return None

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
            # gestione sfida
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
