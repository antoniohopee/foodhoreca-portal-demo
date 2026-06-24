from app.pricing import prezzo_finale, totale_riga


def test_prezzo_listino_semplice():
    # Nessun prezzo particolare -> vince il listino
    assert prezzo_finale(7.5) == 7.5


def test_prezzo_fisso_vince_sul_listino():
    # prezzo_fisso > 0 -> usa il fisso, ignora il listino
    assert prezzo_finale(7.5, prezzo_fisso=6.5) == 6.5


def test_prezzo_fisso_con_sconto():
    # fisso 8.00 - 5% = 7.60
    assert prezzo_finale(8.9, prezzo_fisso=8.0, sconto_pct=5) == 7.6


def test_listino_scontato_quando_fisso_zero():
    # fisso 0 ma sconto 10% sul listino 14.50 = 13.05
    assert prezzo_finale(14.5, prezzo_fisso=0, sconto_pct=10) == 13.05


def test_totale_riga_senza_sconti():
    assert totale_riga(6, 6.5) == 39.0


def test_totale_riga_sconti_a_cascata():
    # 10 * 10 * 0.9 * 0.95 * 1 = 85.5
    assert totale_riga(10, 10, sconto1=10, sconto2=5) == 85.5
