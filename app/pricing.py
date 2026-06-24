"""Implementazione di riferimento (pura, testabile) delle regole di prezzo.

La stessa logica vive nelle view SQL (db/02_views.sql), che e' la sorgente
usata a runtime. Questo modulo serve a documentare e testare la regola in
isolamento, senza dipendere dal DB.
"""
from __future__ import annotations


def prezzo_finale(prezzo_listino: float,
                  prezzo_fisso: float | None = None,
                  sconto_pct: float | None = None) -> float:
    """Prezzo unitario per il cliente.

    Priorita':
      1) prezzo_fisso > 0  -> prezzo fisso, meno eventuale sconto_pct
      2) prezzo_fisso == 0 ma sconto_pct > 0 -> listino scontato
      3) altrimenti -> prezzo di listino
    """
    pf = prezzo_fisso or 0
    sc = sconto_pct or 0
    if pf > 0:
        return round(pf * (1 - sc / 100), 4)
    if sc > 0:
        return round(prezzo_listino * (1 - sc / 100), 4)
    return round(prezzo_listino, 4)


def totale_riga(qta: int, prezzo: float,
                sconto1: float = 0, sconto2: float = 0, sconto3: float = 0) -> float:
    """Totale riga ordine con i tre sconti a cascata."""
    return round(
        qta * prezzo
        * (1 - sconto1 / 100)
        * (1 - sconto2 / 100)
        * (1 - sconto3 / 100),
        2,
    )
