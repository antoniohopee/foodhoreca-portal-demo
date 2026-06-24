"""SQL applicativo. Tutto parametrizzato; la logica di business piu' delicata
(prezzo finale, totali, KPI) vive nelle view in db/02_views.sql.
"""
from __future__ import annotations

from . import db


def nome_articolo(descrizione: str, descrizione_aggiunt: str) -> str:
    """Nome mostrato: descrizione + descrizione_aggiunt concatenate senza
    spazio, con trim solo agli estremi (replica la convenzione del gestionale).
    """
    return f"{descrizione}{descrizione_aggiunt}".strip()


# --- Anagrafiche ------------------------------------------------------------

def lista_clienti(agente_codice: str) -> list[dict]:
    return db.query_all(
        """
        SELECT codice, ragione_sociale, citta, listino_codice
        FROM clienti
        WHERE deleted_at IS NULL
          AND agente_codice = :ag
        ORDER BY ragione_sociale
        """,
        {"ag": agente_codice},
    )


def get_cliente(codice: str) -> dict | None:
    return db.query_one(
        "SELECT * FROM clienti WHERE codice = :c AND deleted_at IS NULL",
        {"c": codice},
    )


def destinazioni_cliente(cliente_codice: str) -> list[dict]:
    return db.query_all(
        """
        SELECT id, codice_indirizzo, descrizione, citta
        FROM indirizzi_spedizione
        WHERE deleted_at IS NULL
          AND cliente_codice = :c
        ORDER BY descrizione
        """,
        {"c": cliente_codice},
    )


# --- Catalogo ---------------------------------------------------------------

def catalogo(cliente_codice: str, cerca: str | None = None) -> list[dict]:
    """Catalogo col prezzo del cliente. La ricerca testuale lavora sul nome
    concatenato SENZA spazi (coerente con il nome mostrato) e sui codici.
    """
    params: dict = {"c": cliente_codice}
    filtro = ""
    if cerca:
        params["q"] = f"%{cerca.replace(' ', '')}%"
        params["qcod"] = f"%{cerca}%"
        filtro = """
          AND (
              REPLACE(CONCAT(a.descrizione, a.descrizione_aggiunt), ' ', '') LIKE :q
              OR a.codice LIKE :qcod
          )
        """
    return db.query_all(
        f"""
        SELECT
            a.codice,
            a.descrizione,
            a.descrizione_aggiunt,
            a.categoria,
            a.unita_misura,
            a.qta_multiplo,
            a.disponibilita,
            vp.prezzo_finale,
            vp.prezzo_listino,
            vp.origine_prezzo
        FROM articoli a
        JOIN v_prezzo_cliente vp
            ON vp.articolo_codice = a.codice
           AND vp.cliente_codice = :c
        WHERE a.deleted_at IS NULL
        {filtro}
        ORDER BY a.categoria, a.descrizione
        """,
        params,
    )


def get_articolo_per_cliente(cliente_codice: str, articolo_codice: str) -> dict | None:
    return db.query_one(
        """
        SELECT
            a.codice, a.descrizione, a.descrizione_aggiunt,
            a.qta_multiplo, vp.prezzo_finale
        FROM articoli a
        JOIN v_prezzo_cliente vp
            ON vp.articolo_codice = a.codice
           AND vp.cliente_codice = :c
        WHERE a.codice = :art AND a.deleted_at IS NULL
        """,
        {"c": cliente_codice, "art": articolo_codice},
    )


# --- Ordini -----------------------------------------------------------------

def crea_ordine(cliente_codice: str, agente_codice: str,
                indirizzo_id: int | None, righe: list[dict]) -> int:
    ordine_id = db.execute(
        """
        INSERT INTO ordini (cliente_codice, agente_codice, indirizzo_id, stato)
        VALUES (:c, :ag, :ind, 'in_coda')
        """,
        {"c": cliente_codice, "ag": agente_codice, "ind": indirizzo_id},
    )
    for r in righe:
        db.execute(
            """
            INSERT INTO ordini_righe
                (ordine_id, articolo_codice, descrizione, qta, prezzo)
            VALUES (:o, :art, :desc, :qta, :prezzo)
            """,
            {
                "o": ordine_id,
                "art": r["codice"],
                "desc": r["descrizione"],
                "qta": r["qta"],
                "prezzo": r["prezzo"],
            },
        )
    return ordine_id


def lista_ordini(agente_codice: str) -> list[dict]:
    return db.query_all(
        """
        SELECT
            o.id, o.stato, o.created_at,
            c.ragione_sociale,
            COALESCE(ROUND(SUM(
                r.qta * r.prezzo
                * (1 - r.sconto1/100) * (1 - r.sconto2/100) * (1 - r.sconto3/100)
            ), 2), 0) AS totale,
            COUNT(r.id) AS n_righe
        FROM ordini o
        JOIN clienti c ON c.codice = o.cliente_codice
        LEFT JOIN ordini_righe r ON r.ordine_id = o.id
        WHERE o.agente_codice = :ag
        GROUP BY o.id, o.stato, o.created_at, c.ragione_sociale
        ORDER BY o.created_at DESC, o.id DESC
        """,
        {"ag": agente_codice},
    )


def get_ordine(ordine_id: int) -> dict | None:
    return db.query_one(
        """
        SELECT
            o.*, c.ragione_sociale, c.citta,
            i.codice_indirizzo, i.descrizione AS dest_descrizione, i.citta AS dest_citta
        FROM ordini o
        JOIN clienti c ON c.codice = o.cliente_codice
        LEFT JOIN indirizzi_spedizione i ON i.id = o.indirizzo_id
        WHERE o.id = :id
        """,
        {"id": ordine_id},
    )


def righe_ordine(ordine_id: int) -> list[dict]:
    return db.query_all(
        """
        SELECT *,
            ROUND(qta * prezzo
                * (1 - sconto1/100) * (1 - sconto2/100) * (1 - sconto3/100), 2) AS totale_riga
        FROM ordini_righe
        WHERE ordine_id = :id
        ORDER BY id
        """,
        {"id": ordine_id},
    )


def annulla_ordine(ordine_id: int, agente_codice: str) -> None:
    db.execute(
        "UPDATE ordini SET stato='annullato' WHERE id=:id AND agente_codice=:ag",
        {"id": ordine_id, "ag": agente_codice},
    )


# --- KPI --------------------------------------------------------------------

def kpi_agente(agente_codice: str) -> dict | None:
    return db.query_one(
        "SELECT * FROM v_kpi_agente WHERE agente_codice = :ag",
        {"ag": agente_codice},
    )


def kpi_top_clienti(agente_codice: str, limit: int = 5) -> list[dict]:
    return db.query_all(
        """
        SELECT cliente_codice, ragione_sociale, n_ordini, totale_ordinato
        FROM v_kpi_cliente
        WHERE agente_codice = :ag
        ORDER BY totale_ordinato DESC
        LIMIT :lim
        """,
        {"ag": agente_codice, "lim": limit},
    )
