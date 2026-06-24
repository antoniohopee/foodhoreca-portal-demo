# FoodHoreca Portal — Demo

Portale ordini per **agenti commerciali del food service**: catalogo con prezzo
personalizzato per cliente, carrello con moltiplicatore di confezione, gestione
ordini ed **esportazione del tracciato** verso il gestionale, più una pipeline
**ETL** di importazione dati e una **dashboard KPI**.

> Demo a scopo dimostrativo. Tutti i dati (clienti, articoli, prezzi) sono
> fittizi. Nessuna credenziale o informazione reale è inclusa nel repository.

Stack: **Python 3.12 · FastAPI · MySQL 8 · SQL scritto a mano · Docker**.

---

## Cosa mostra

| Area | Funzionalità | Competenza |
|------|--------------|------------|
| **SQL** | Calcolo del prezzo cliente a priorità (prezzo fisso → listino scontato → listino) tramite view dedicata | Modellazione + query non banali |
| **SQL** | Totali riga con 3 sconti a cascata e KPI aggregati (`GROUP BY`, view) | Aggregazioni, viste di business |
| **Python** | Web app FastAPI: catalogo, carrello in sessione, ordini, dettaglio | Backend, routing, templating |
| **Python** | Generazione del **tracciato di export** pipe-separated (record C/D/O) | Logica pura, testabile |
| **Python** | **ETL idempotente**: import CSV → UPSERT, ripristino soft-delete | Integrazione dati / sync gestionale |
| **Qualità** | Test `pytest` su prezzi ed export, eseguibili senza DB | TDD / affidabilità |
| **DevOps** | `docker compose up` avvia DB + app con dati seed | Containerizzazione |

## Avvio rapido

Prerequisito: **Docker Desktop**.

Modo più semplice (avvia Docker se serve, attende l'app e apre il browser):

```bash
./start.sh        # avvia tutto e apre http://localhost:8000
./stop.sh         # ferma (i dati restano)
./stop.sh --reset # ferma e azzera il DB (riparte dai seed)
```

Oppure con i comandi Docker espliciti:

```bash
cp .env.example .env
docker compose up --build
```

Apri **http://localhost:8000**. Il database viene creato e popolato in automatico
al primo avvio (`db/01_schema.sql` → `02_views.sql` → `03_seed.sql`).

### Importare dati via ETL (opzionale)

Simula il flusso "gestionale → CSV → portale" con UPSERT idempotente
(rilanciabile senza creare duplicati):

```bash
docker compose exec web python -m sync.import_csv
```

### Test

```bash
pip install -r requirements.txt   # in un virtualenv
pytest -q
```

I test su prezzi ed export **non richiedono il database**: validano la logica pura.

## Architettura

```
                Browser
                   │  HTTP (Bootstrap UI)
                   ▼
        ┌────────────────────────┐
        │   FastAPI  (app/)       │
        │   ├─ main.py   rotte    │
        │   ├─ queries.py  SQL    │
        │   ├─ pricing.py logica  │
        │   └─ exporter.py TXT    │
        └───────────┬────────────┘
                    │  SQL parametrizzato (SQLAlchemy core, niente ORM)
                    ▼
        ┌────────────────────────┐        ┌────────────────────────┐
        │      MySQL 8            │◀───────│  ETL  (sync/import_csv) │
        │  tabelle + view di      │ UPSERT │  CSV gestionale →       │
        │  business (prezzi, KPI) │        │  import idempotente     │
        └────────────────────────┘        └────────────────────────┘
```

### Scelte tecniche

- **SQL a vista, non nascosto da un ORM.** Le regole di business più delicate
  (prezzo cliente, totali, KPI) vivono in *view* SQL: una sola sorgente di
  verità che app, export ed ETL condividono. `app/pricing.py` ne è la copia
  pura, usata per i test e come documentazione eseguibile.
- **Query parametrizzate ovunque** (nessuna concatenazione di stringhe) →
  niente SQL injection.
- **ETL idempotente**: `INSERT ... ON DUPLICATE KEY UPDATE` con ripristino di
  `deleted_at`, così la sync è ri-eseguibile in sicurezza.
- **Export disaccoppiato**: `exporter.py` è una funzione pura (dict → stringa),
  facile da testare e indipendente dal trasporto (file, FTP, HTTP).

## Dominio: dettagli interessanti

- **Prezzo per cliente** — tre casi, gestiti in `v_prezzo_cliente`:
  1. *prezzo fisso* dedicato (eventualmente scontato);
  2. *listino scontato* (sconto % sul listino del cliente);
  3. *listino* del cliente.
  Nel catalogo un badge mostra l'origine del prezzo.
- **Moltiplicatore di confezione** (`qta_multiplo`): aggiungere a carrello
  incrementa di un'intera confezione (es. cartone da 6), poi la quantità è
  modificabile.
- **Destinazioni di spedizione** (codici `510…`): un ordine può essere spedito a
  una destinazione diversa dalla sede; finisce nel record `D` del tracciato.

## Struttura del progetto

```
foodhoreca-portal-demo/
├── docker-compose.yml      # MySQL + web app
├── Dockerfile
├── requirements.txt
├── db/
│   ├── 01_schema.sql       # tabelle
│   ├── 02_views.sql        # view: prezzo cliente, totali, KPI
│   └── 03_seed.sql         # 3 clienti, 5 articoli, listini, prezzi
├── app/
│   ├── main.py             # rotte FastAPI
│   ├── db.py               # pool + helper query
│   ├── queries.py          # SQL applicativo
│   ├── pricing.py          # regole prezzo (pure, testate)
│   ├── exporter.py         # tracciato TXT C/D/O
│   ├── templates/          # Jinja2 + Bootstrap
│   └── static/
├── sync/
│   ├── import_csv.py       # ETL idempotente
│   └── sample_data/        # CSV di esempio
└── tests/                  # pytest (prezzi, export)
```

## Possibili evoluzioni

Autenticazione e ruoli (admin/capoarea/agente), upload del tracciato via FTP,
storico KPI dal gestionale, PWA offline-first, CI con esecuzione test su push.

---

*Progetto dimostrativo per portfolio.*
