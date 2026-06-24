"""Generazione del tracciato di esportazione ordine.

Formato pipe-separated ispirato ai tracciati gestionali (es. Mexal):
  C = testata cliente
  D = destinazione di spedizione (solo se presente)
  O = riga ordine

La funzione e' pura (riceve dict, ritorna stringa) cosi' e' facile testarla.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)

SEP = "|"


def _fmt_prezzo(value) -> str:
    return f"{float(value):.4f}"


def _riga(record: list) -> str:
    return SEP.join("" if v is None else str(v) for v in record)


def genera_tracciato(ordine: dict, righe: list[dict],
                     destinazione: dict | None = None) -> str:
    """Costruisce il contenuto TXT dell'ordine.

    ordine:       dict con cliente_codice, ragione_sociale, citta, created_at
    righe:        lista di dict con articolo_codice, descrizione, qta, prezzo
    destinazione: opzionale, dict con codice_indirizzo, descrizione, citta
    """
    lines: list[str] = []

    # Testata cliente
    lines.append(_riga([
        "C",
        ordine["cliente_codice"],
        ordine["ragione_sociale"],
        ordine.get("citta", ""),
        ordine.get("created_at", _now()).strftime("%Y%m%d")
        if hasattr(ordine.get("created_at"), "strftime")
        else str(ordine.get("created_at", "")),
    ]))

    # Destinazione (record D) solo se l'ordine ha un indirizzo 510
    if destinazione:
        lines.append(_riga([
            "D",
            destinazione["codice_indirizzo"],
            destinazione["descrizione"],
            destinazione.get("citta", ""),
        ]))

    # Righe ordine
    for idx, r in enumerate(righe, start=1):
        lines.append(_riga([
            "O",
            idx,
            r["articolo_codice"],
            r["descrizione"],
            r["qta"],
            _fmt_prezzo(r["prezzo"]),
        ]))

    return "\n".join(lines) + "\n"


def nome_file(ordine_id: int, tipo: str = "ORD",
              now: datetime | None = None) -> str:
    ts = (now or _now()).strftime("%Y%m%d%H%M%S")
    return f"Ordini{tipo}_{ts}_{ordine_id}.txt"
