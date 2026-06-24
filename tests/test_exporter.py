from datetime import datetime

from app.exporter import genera_tracciato, nome_file

ORDINE = {
    "cliente_codice": "50101",
    "ragione_sociale": "Trattoria Da Gino",
    "citta": "Bologna",
    "created_at": datetime(2026, 6, 24, 10, 30),
}
RIGHE = [
    {"articolo_codice": "ART001", "descrizione": "Olio EVO Bio500ml", "qta": 6, "prezzo": 6.5},
    {"articolo_codice": "ART002", "descrizione": "Pomodoro Pelatolattina 2.5kg", "qta": 12, "prezzo": 2.2},
]


def test_tracciato_senza_destinazione():
    out = genera_tracciato(ORDINE, RIGHE)
    lines = out.strip().split("\n")
    # 1 testata C + 2 righe O
    assert lines[0].startswith("C|50101|Trattoria Da Gino|Bologna|20260624")
    assert lines[1] == "O|1|ART001|Olio EVO Bio500ml|6|6.5000"
    assert lines[2] == "O|2|ART002|Pomodoro Pelatolattina 2.5kg|12|2.2000"
    assert "D|" not in out


def test_tracciato_con_destinazione_510():
    dest = {"codice_indirizzo": "51001", "descrizione": "Magazzino Spiaggia", "citta": "Riccione"}
    out = genera_tracciato(ORDINE, RIGHE, destinazione=dest)
    lines = out.strip().split("\n")
    assert lines[0].startswith("C|")
    assert lines[1] == "D|51001|Magazzino Spiaggia|Riccione"
    assert lines[2].startswith("O|1|")


def test_nome_file_formato():
    nome = nome_file(42, now=datetime(2026, 6, 24, 10, 30, 0))
    assert nome == "OrdiniORD_20260624103000_42.txt"
