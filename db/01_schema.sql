-- ---------------------------------------------------------------------------
-- FoodHoreca Portal - Demo
-- Schema gestionale: agenti, clienti, catalogo, listini, prezzi, ordini.
-- Ispirato a un portale ordini per agenti commerciali del food service.
-- Tutti i dati sono fittizi.
-- ---------------------------------------------------------------------------

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Agenti commerciali ---------------------------------------------------------
CREATE TABLE agenti (
    codice       VARCHAR(8)   NOT NULL,
    nome         VARCHAR(120) NOT NULL,
    email        VARCHAR(160) NOT NULL,
    PRIMARY KEY (codice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Listini prezzi -------------------------------------------------------------
CREATE TABLE listini (
    codice       VARCHAR(8)   NOT NULL,
    descrizione  VARCHAR(120) NOT NULL,
    PRIMARY KEY (codice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Clienti --------------------------------------------------------------------
-- I clienti con codice che inizia per '510' rappresentano destinazioni di
-- spedizione, non clienti principali (replica una convenzione del gestionale).
CREATE TABLE clienti (
    codice          VARCHAR(12)  NOT NULL,
    ragione_sociale VARCHAR(160) NOT NULL,
    citta           VARCHAR(120) NOT NULL,
    agente_codice   VARCHAR(8)   NOT NULL,
    listino_codice  VARCHAR(8)   NOT NULL,
    deleted_at      DATETIME     NULL DEFAULT NULL,
    PRIMARY KEY (codice),
    KEY idx_clienti_agente (agente_codice),
    CONSTRAINT fk_clienti_agente  FOREIGN KEY (agente_codice)  REFERENCES agenti (codice),
    CONSTRAINT fk_clienti_listino FOREIGN KEY (listino_codice) REFERENCES listini (codice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Destinazioni di spedizione (codici '510...') -------------------------------
CREATE TABLE indirizzi_spedizione (
    id               INT          NOT NULL AUTO_INCREMENT,
    cliente_codice   VARCHAR(12)  NOT NULL,
    codice_indirizzo VARCHAR(12)  NOT NULL,
    descrizione      VARCHAR(160) NOT NULL,
    citta            VARCHAR(120) NOT NULL,
    deleted_at       DATETIME     NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_dest (cliente_codice, codice_indirizzo),
    CONSTRAINT fk_dest_cliente FOREIGN KEY (cliente_codice) REFERENCES clienti (codice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Catalogo articoli ----------------------------------------------------------
-- Il nome mostrato e' la concatenazione di descrizione + descrizione_aggiunt.
-- qta_multiplo e' il moltiplicatore di vendita (es. cartone da 6 pezzi).
CREATE TABLE articoli (
    codice              VARCHAR(16)  NOT NULL,
    descrizione         VARCHAR(120) NOT NULL,
    descrizione_aggiunt VARCHAR(120) NOT NULL DEFAULT '',
    categoria           VARCHAR(60)  NOT NULL,
    unita_misura        VARCHAR(8)   NOT NULL DEFAULT 'PZ',
    qta_multiplo        INT          NOT NULL DEFAULT 1,
    disponibilita       INT          NOT NULL DEFAULT 0,
    deleted_at          DATETIME     NULL DEFAULT NULL,
    PRIMARY KEY (codice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Prezzo di listino per articolo --------------------------------------------
CREATE TABLE prezzi (
    listino_codice  VARCHAR(8)     NOT NULL,
    articolo_codice VARCHAR(16)    NOT NULL,
    prezzo          DECIMAL(10,4)  NOT NULL,
    PRIMARY KEY (listino_codice, articolo_codice),
    CONSTRAINT fk_prezzi_listino  FOREIGN KEY (listino_codice)  REFERENCES listini (codice),
    CONSTRAINT fk_prezzi_articolo FOREIGN KEY (articolo_codice) REFERENCES articoli (codice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Prezzi particolari per cliente --------------------------------------------
-- prezzo_fisso > 0  -> vince sul listino (eventualmente scontato da sconto_pct)
-- prezzo_fisso = 0  -> si applica sconto_pct al prezzo di listino
CREATE TABLE prezzi_particolari (
    cliente_codice  VARCHAR(12)    NOT NULL,
    articolo_codice VARCHAR(16)    NOT NULL,
    prezzo_fisso    DECIMAL(10,4)  NOT NULL DEFAULT 0,
    sconto_pct      DECIMAL(5,2)   NOT NULL DEFAULT 0,
    PRIMARY KEY (cliente_codice, articolo_codice),
    CONSTRAINT fk_pp_cliente  FOREIGN KEY (cliente_codice)  REFERENCES clienti (codice),
    CONSTRAINT fk_pp_articolo FOREIGN KEY (articolo_codice) REFERENCES articoli (codice)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Ordini ---------------------------------------------------------------------
CREATE TABLE ordini (
    id               INT          NOT NULL AUTO_INCREMENT,
    cliente_codice   VARCHAR(12)  NOT NULL,
    agente_codice    VARCHAR(8)   NOT NULL,
    indirizzo_id     INT          NULL DEFAULT NULL,
    stato            ENUM('bozza','in_coda','inviato','annullato') NOT NULL DEFAULT 'bozza',
    note             VARCHAR(255) NOT NULL DEFAULT '',
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_ordini_cliente (cliente_codice),
    KEY idx_ordini_agente (agente_codice),
    CONSTRAINT fk_ordini_cliente   FOREIGN KEY (cliente_codice) REFERENCES clienti (codice),
    CONSTRAINT fk_ordini_agente    FOREIGN KEY (agente_codice)  REFERENCES agenti (codice),
    CONSTRAINT fk_ordini_indirizzo FOREIGN KEY (indirizzo_id)   REFERENCES indirizzi_spedizione (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Righe ordine ---------------------------------------------------------------
-- Totale riga = qta * prezzo * (1-sc1/100) * (1-sc2/100) * (1-sc3/100)
CREATE TABLE ordini_righe (
    id              INT           NOT NULL AUTO_INCREMENT,
    ordine_id       INT           NOT NULL,
    articolo_codice VARCHAR(16)   NOT NULL,
    descrizione     VARCHAR(255)  NOT NULL,
    qta             INT           NOT NULL,
    prezzo          DECIMAL(10,4) NOT NULL,
    sconto1         DECIMAL(5,2)  NOT NULL DEFAULT 0,
    sconto2         DECIMAL(5,2)  NOT NULL DEFAULT 0,
    sconto3         DECIMAL(5,2)  NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_righe_ordine (ordine_id),
    CONSTRAINT fk_righe_ordine FOREIGN KEY (ordine_id) REFERENCES ordini (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
