"""ETL: importa i CSV del gestionale nel DB del portale.

Replica il pattern della pipeline reale: il gestionale esporta CSV, il portale
li importa con UPSERT idempotente. Rilanciare lo script piu' volte non duplica
i dati e "resuscita" i record tornati disponibili (deleted_at = NULL).

Uso:
    python -m sync.import_csv                 # usa sync/sample_data
    python -m sync.import_csv /percorso/csv   # cartella CSV custom

Richiede le variabili DB_* (vedi .env.example). Eseguibile sia dentro il
container (`docker compose exec web python -m sync.import_csv`) sia in locale.
"""
from __future__ import annotations

import csv
import os
import sys
from typing import Callable

from app import db

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def _upsert(rows: list[dict], sql: str, mapper: Callable[[dict], dict]) -> int:
    n = 0
    for row in rows:
        db.execute(sql, mapper(row))
        n += 1
    return n


def import_articoli(rows: list[dict]) -> int:
    # ON DUPLICATE KEY UPDATE => idempotente; deleted_at riportato a NULL.
    sql = """
        INSERT INTO articoli
            (codice, descrizione, descrizione_aggiunt, categoria,
             unita_misura, qta_multiplo, disponibilita, deleted_at)
        VALUES
            (:codice, :descrizione, :descrizione_aggiunt, :categoria,
             :unita_misura, :qta_multiplo, :disponibilita, NULL)
        ON DUPLICATE KEY UPDATE
            descrizione         = VALUES(descrizione),
            descrizione_aggiunt = VALUES(descrizione_aggiunt),
            categoria           = VALUES(categoria),
            unita_misura        = VALUES(unita_misura),
            qta_multiplo        = VALUES(qta_multiplo),
            disponibilita       = VALUES(disponibilita),
            deleted_at          = NULL
    """
    return _upsert(rows, sql, lambda r: {
        "codice": r["codice"],
        "descrizione": r["descrizione"],
        "descrizione_aggiunt": r.get("descrizione_aggiunt", ""),
        "categoria": r["categoria"],
        "unita_misura": r.get("unita_misura", "PZ"),
        "qta_multiplo": int(r.get("qta_multiplo", 1)),
        "disponibilita": int(r.get("disponibilita", 0)),
    })


def import_prezzi(rows: list[dict]) -> int:
    sql = """
        INSERT INTO prezzi (listino_codice, articolo_codice, prezzo)
        VALUES (:listino_codice, :articolo_codice, :prezzo)
        ON DUPLICATE KEY UPDATE prezzo = VALUES(prezzo)
    """
    return _upsert(rows, sql, lambda r: {
        "listino_codice": r["listino_codice"],
        "articolo_codice": r["articolo_codice"],
        "prezzo": float(r["prezzo"]),
    })


JOBS = [
    ("articoli.csv", import_articoli),
    ("prezzi.csv", import_prezzi),
]


def run(csv_dir: str = SAMPLE_DIR) -> None:
    db.wait_for_db()
    print(f"[sync] import da {csv_dir}")
    for filename, importer in JOBS:
        path = os.path.join(csv_dir, filename)
        if not os.path.exists(path):
            print(f"[sync] salto {filename} (assente)")
            continue
        n = importer(_read_csv(path))
        print(f"[sync] {filename}: {n} righe upsert")
    print("[sync] completato")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else SAMPLE_DIR)
