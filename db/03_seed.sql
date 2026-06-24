-- ---------------------------------------------------------------------------
-- Dati demo: 1 agente, 3 clienti, 5 articoli. Tutto fittizio.
-- Pensato per mostrare i 3 casi di calcolo prezzo e una destinazione 510.
-- ---------------------------------------------------------------------------

INSERT INTO agenti (codice, nome, email) VALUES
    ('A01', 'Mario Rossi', 'mario.rossi@example.com');

INSERT INTO listini (codice, descrizione) VALUES
    ('L1', 'Listino Horeca Standard'),
    ('L2', 'Listino Horeca Premium');

-- Clienti --------------------------------------------------------------------
INSERT INTO clienti (codice, ragione_sociale, citta, agente_codice, listino_codice) VALUES
    ('50101', 'Trattoria Da Gino',        'Bologna',  'A01', 'L1'),
    ('50102', 'Hotel Belvedere',          'Rimini',   'A01', 'L2'),
    ('50103', 'Bar Centrale SRL',         'Modena',   'A01', 'L1');

-- Destinazione di spedizione 510 collegata a Hotel Belvedere -----------------
INSERT INTO indirizzi_spedizione (cliente_codice, codice_indirizzo, descrizione, citta) VALUES
    ('50102', '51001', 'Hotel Belvedere - Magazzino Spiaggia', 'Riccione');

-- Articoli (nome = descrizione + descrizione_aggiunt) ------------------------
INSERT INTO articoli (codice, descrizione, descrizione_aggiunt, categoria, unita_misura, qta_multiplo, disponibilita) VALUES
    ('ART001', 'Olio EVO Bio ',       '500ml',        'Condimenti',  'PZ',  6, 240),
    ('ART002', 'Pomodoro Pelato ',    'lattina 2.5kg','Conserve',    'PZ', 12, 600),
    ('ART003', 'Mozzarella Fiordilatte ', 'kg',        'Latticini',   'KG',  1,  80),
    ('ART004', 'Farina Tipo 00 ',     'sacco 25kg',   'Farine',      'PZ',  1, 120),
    ('ART005', 'Caffe Miscela Bar ',  'kg',           'Bevande',     'KG',  4, 160);

-- Prezzi di listino ----------------------------------------------------------
INSERT INTO prezzi (listino_codice, articolo_codice, prezzo) VALUES
    ('L1', 'ART001', 7.5000),
    ('L1', 'ART002', 2.2000),
    ('L1', 'ART003', 8.9000),
    ('L1', 'ART004', 18.0000),
    ('L1', 'ART005', 14.5000),
    ('L2', 'ART001', 6.9000),
    ('L2', 'ART002', 2.0000),
    ('L2', 'ART003', 8.4000),
    ('L2', 'ART004', 17.0000),
    ('L2', 'ART005', 13.5000);

-- Prezzi particolari ---------------------------------------------------------
-- Trattoria Da Gino (L1):
--   ART001 -> prezzo fisso 6.50 (caso 1: prezzo_fisso)
--   ART005 -> sconto 10% sul listino (caso 2: listino_scontato)
--   gli altri -> listino L1 (caso 3)
INSERT INTO prezzi_particolari (cliente_codice, articolo_codice, prezzo_fisso, sconto_pct) VALUES
    ('50101', 'ART001', 6.5000, 0.00),
    ('50101', 'ART005', 0.0000, 10.00),
-- Hotel Belvedere (L2): prezzo fisso scontato su ART003 (fisso 8.00 - 5%)
    ('50102', 'ART003', 8.0000, 5.00);
