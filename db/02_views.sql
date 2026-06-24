-- ---------------------------------------------------------------------------
-- View di business. Centralizzano la logica SQL piu' delicata cosi' che
-- applicazione, export ed ETL leggano sempre gli stessi numeri.
-- ---------------------------------------------------------------------------

-- Prezzo finale per coppia (cliente, articolo) ------------------------------
-- Priorita':
--   1) prezzo_particolari.prezzo_fisso > 0  -> prezzo fisso, meno eventuale sconto_pct
--   2) prezzo_fisso = 0 ma sconto_pct > 0   -> prezzo di listino scontato
--   3) altrimenti                           -> prezzo di listino del cliente
CREATE OR REPLACE VIEW v_prezzo_cliente AS
SELECT
    c.codice  AS cliente_codice,
    a.codice  AS articolo_codice,
    pl.prezzo AS prezzo_listino,
    pp.prezzo_fisso,
    pp.sconto_pct,
    CASE
        WHEN pp.prezzo_fisso IS NOT NULL AND pp.prezzo_fisso > 0
            THEN ROUND(pp.prezzo_fisso * (1 - COALESCE(pp.sconto_pct, 0) / 100), 4)
        WHEN pp.sconto_pct IS NOT NULL AND pp.sconto_pct > 0
            THEN ROUND(pl.prezzo * (1 - pp.sconto_pct / 100), 4)
        ELSE pl.prezzo
    END AS prezzo_finale,
    -- Etichetta utile in UI per spiegare DA DOVE viene il prezzo
    CASE
        WHEN pp.prezzo_fisso IS NOT NULL AND pp.prezzo_fisso > 0 THEN 'prezzo_fisso'
        WHEN pp.sconto_pct  IS NOT NULL AND pp.sconto_pct  > 0 THEN 'listino_scontato'
        ELSE 'listino'
    END AS origine_prezzo
FROM clienti c
JOIN articoli a
    ON a.deleted_at IS NULL
LEFT JOIN prezzi pl
    ON pl.listino_codice = c.listino_codice
   AND pl.articolo_codice = a.codice
LEFT JOIN prezzi_particolari pp
    ON pp.cliente_codice = c.codice
   AND pp.articolo_codice = a.codice
WHERE c.deleted_at IS NULL;

-- Totale per riga ordine -----------------------------------------------------
CREATE OR REPLACE VIEW v_righe_totali AS
SELECT
    r.*,
    o.cliente_codice,
    o.agente_codice,
    o.stato,
    o.created_at,
    ROUND(
        r.qta * r.prezzo
        * (1 - r.sconto1 / 100)
        * (1 - r.sconto2 / 100)
        * (1 - r.sconto3 / 100)
    , 2) AS totale_riga
FROM ordini_righe r
JOIN ordini o ON o.id = r.ordine_id;

-- KPI per agente -------------------------------------------------------------
CREATE OR REPLACE VIEW v_kpi_agente AS
SELECT
    a.codice                       AS agente_codice,
    a.nome                         AS agente_nome,
    COUNT(DISTINCT t.ordine_id)    AS n_ordini,
    COUNT(DISTINCT t.cliente_codice) AS n_clienti,
    COALESCE(ROUND(SUM(t.totale_riga), 2), 0) AS totale_ordinato
FROM agenti a
LEFT JOIN v_righe_totali t
    ON t.agente_codice = a.codice
   AND t.stato <> 'annullato'
GROUP BY a.codice, a.nome;

-- KPI per cliente (top clienti) ---------------------------------------------
CREATE OR REPLACE VIEW v_kpi_cliente AS
SELECT
    c.codice          AS cliente_codice,
    c.ragione_sociale,
    c.agente_codice,
    COUNT(DISTINCT t.ordine_id)        AS n_ordini,
    COALESCE(ROUND(SUM(t.totale_riga), 2), 0) AS totale_ordinato
FROM clienti c
LEFT JOIN v_righe_totali t
    ON t.cliente_codice = c.codice
   AND t.stato <> 'annullato'
WHERE c.deleted_at IS NULL
GROUP BY c.codice, c.ragione_sociale, c.agente_codice;
