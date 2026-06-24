"""FoodHoreca Portal - Demo.

Web app per agenti commerciali del food service: catalogo con prezzo per
cliente, carrello con moltiplicatore articolo, creazione ordine ed export TXT.

Per semplicita' la demo lavora con un agente fisso (niente login): in un
gestionale reale l'agente verrebbe dalla sessione autenticata.
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from . import db, exporter, queries

BASE_DIR = os.path.dirname(__file__)

# Agente "loggato" della demo
AGENTE_CORRENTE = "A01"

app = FastAPI(title="FoodHoreca Portal - Demo")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "demo-secret"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
templates.env.filters["eur"] = lambda v: f"{float(v):.2f} €"


@app.on_event("startup")
def _startup() -> None:
    db.wait_for_db()


# --- Carrello in sessione ---------------------------------------------------
# Struttura: {"cliente": codice, "indirizzo_id": int|None, "righe": {cod: qta}}

def _cart(request: Request) -> dict:
    return request.session.setdefault(
        "cart", {"cliente": None, "indirizzo_id": None, "righe": {}}
    )


def _cart_count(request: Request) -> int:
    return sum(_cart(request)["righe"].values())


# --- Pagine -----------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    kpi = queries.kpi_agente(AGENTE_CORRENTE)
    top = queries.kpi_top_clienti(AGENTE_CORRENTE)
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "kpi": kpi, "top_clienti": top,
        "cart_count": _cart_count(request),
    })


@app.get("/catalogo", response_class=HTMLResponse)
def catalogo(request: Request, cliente: str | None = None, q: str | None = None):
    clienti = queries.lista_clienti(AGENTE_CORRENTE)
    cart = _cart(request)
    cliente_sel = cliente or cart.get("cliente") or (clienti[0]["codice"] if clienti else None)

    articoli = []
    if cliente_sel:
        # Cambiare cliente azzera il carrello (prezzi diversi per cliente)
        if cart.get("cliente") and cart["cliente"] != cliente_sel:
            cart["righe"] = {}
            cart["indirizzo_id"] = None
        cart["cliente"] = cliente_sel
        for a in queries.catalogo(cliente_sel, q):
            a["nome"] = queries.nome_articolo(a["descrizione"], a["descrizione_aggiunt"])
            articoli.append(a)

    return templates.TemplateResponse("catalogo.html", {
        "request": request, "clienti": clienti, "cliente_sel": cliente_sel,
        "articoli": articoli, "cerca": q or "", "cart_count": _cart_count(request),
    })


@app.post("/carrello/add")
def carrello_add(request: Request, codice: str = Form(...),
                 cliente: str = Form(...), step: int = Form(1)):
    cart = _cart(request)
    cart["cliente"] = cliente
    cart["righe"][codice] = cart["righe"].get(codice, 0) + max(1, step)
    return RedirectResponse(f"/catalogo?cliente={cliente}", status_code=303)


@app.get("/carrello", response_class=HTMLResponse)
def carrello(request: Request):
    cart = _cart(request)
    righe, totale = [], 0.0
    destinazioni = []
    if cart["cliente"]:
        destinazioni = queries.destinazioni_cliente(cart["cliente"])
        for cod, qta in cart["righe"].items():
            art = queries.get_articolo_per_cliente(cart["cliente"], cod)
            if not art:
                continue
            prezzo = float(art["prezzo_finale"])
            righe.append({
                "codice": cod,
                "nome": queries.nome_articolo(art["descrizione"], art["descrizione_aggiunt"]),
                "qta": qta,
                "qta_multiplo": art["qta_multiplo"],
                "prezzo": prezzo,
                "totale": round(prezzo * qta, 2),
            })
            totale += prezzo * qta
    return templates.TemplateResponse("carrello.html", {
        "request": request, "righe": righe, "totale": round(totale, 2),
        "cliente": cart["cliente"], "destinazioni": destinazioni,
        "indirizzo_id": cart.get("indirizzo_id"), "cart_count": _cart_count(request),
    })


@app.post("/carrello/update")
def carrello_update(request: Request, codice: str = Form(...), qta: int = Form(...)):
    cart = _cart(request)
    if qta <= 0:
        cart["righe"].pop(codice, None)
    else:
        cart["righe"][codice] = qta
    return RedirectResponse("/carrello", status_code=303)


@app.post("/carrello/destinazione")
def carrello_destinazione(request: Request, indirizzo_id: str = Form("")):
    cart = _cart(request)
    cart["indirizzo_id"] = int(indirizzo_id) if indirizzo_id else None
    return RedirectResponse("/carrello", status_code=303)


@app.post("/ordini/conferma")
def conferma_ordine(request: Request):
    cart = _cart(request)
    if not cart["cliente"] or not cart["righe"]:
        return RedirectResponse("/carrello", status_code=303)

    righe = []
    for cod, qta in cart["righe"].items():
        art = queries.get_articolo_per_cliente(cart["cliente"], cod)
        if not art:
            continue
        righe.append({
            "codice": cod,
            "descrizione": queries.nome_articolo(art["descrizione"], art["descrizione_aggiunt"]),
            "qta": qta,
            "prezzo": float(art["prezzo_finale"]),
        })

    ordine_id = queries.crea_ordine(
        cart["cliente"], AGENTE_CORRENTE, cart.get("indirizzo_id"), righe
    )
    request.session["cart"] = {"cliente": None, "indirizzo_id": None, "righe": {}}
    return RedirectResponse(f"/ordini/{ordine_id}", status_code=303)


@app.get("/ordini", response_class=HTMLResponse)
def ordini(request: Request):
    return templates.TemplateResponse("ordini.html", {
        "request": request, "ordini": queries.lista_ordini(AGENTE_CORRENTE),
        "cart_count": _cart_count(request),
    })


@app.get("/ordini/{ordine_id}", response_class=HTMLResponse)
def ordine_dettaglio(request: Request, ordine_id: int):
    ordine = queries.get_ordine(ordine_id)
    if not ordine:
        return RedirectResponse("/ordini", status_code=303)
    righe = queries.righe_ordine(ordine_id)
    totale = sum(float(r["totale_riga"]) for r in righe)
    return templates.TemplateResponse("ordine_dettaglio.html", {
        "request": request, "ordine": ordine, "righe": righe,
        "totale": round(totale, 2), "cart_count": _cart_count(request),
    })


@app.post("/ordini/{ordine_id}/annulla")
def ordine_annulla(request: Request, ordine_id: int):
    queries.annulla_ordine(ordine_id, AGENTE_CORRENTE)
    return RedirectResponse(f"/ordini/{ordine_id}", status_code=303)


@app.get("/ordini/{ordine_id}/export.txt", response_class=PlainTextResponse)
def ordine_export(ordine_id: int):
    ordine = queries.get_ordine(ordine_id)
    if not ordine:
        return PlainTextResponse("Ordine non trovato", status_code=404)
    righe = queries.righe_ordine(ordine_id)
    destinazione = None
    if ordine.get("indirizzo_id"):
        destinazione = {
            "codice_indirizzo": ordine["codice_indirizzo"],
            "descrizione": ordine["dest_descrizione"],
            "citta": ordine["dest_citta"],
        }
    contenuto = exporter.genera_tracciato(ordine, righe, destinazione)
    filename = exporter.nome_file(ordine_id)
    return PlainTextResponse(contenuto, headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
    })
