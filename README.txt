# Polipone v2 - Setup rapido

1) Installa **Python 3.10+**.
2) Scarica ed estrai questo pacchetto ZIP.
3) Apri terminale nella cartella.
4) (Consigliato) Crea e attiva ambiente virtuale:
   Windows:
       python -m venv .venv
       .venv\Scripts\activate
   macOS / Linux:
       python3 -m venv .venv
       source .venv/bin/activate
5) Installa dipendenze:
   pip install -r requirements.txt
6) Avvia l'app:
   streamlit run polipone.py
7) Apri il browser su http://localhost:8501

Note: implementati Jolly (ogni 2 giornate) e Sfide (ogni 5 giornate).
