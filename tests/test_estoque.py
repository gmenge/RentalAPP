from datetime import date, timedelta

import pytest

import database


def dia(n):
    return (date.today() + timedelta(days=n)).isoformat()


def disponivel(eq_id, inicio, fim=None):
    df = database.get_equipamentos_com_disponibilidade(dia(inicio), dia(fim if fim is not None else inicio))
    return int(df[df.id == eq_id].qtd_disponivel.iloc[0])


def alugar(eq_id, inicio, fim, qtd=1):
    itens = [{"id": eq_id, "qtd_alugada": qtd, "subtotal": 1.0}]
    database.registrar_aluguel("1", "Cliente", "Rua", dia(inicio), dia(fim), "08:00", itens, 1.0)


@pytest.fixture
def equipamento(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_NAME", tmp_path / "teste.db")
    monkeypatch.setattr(database, "BACKUP_DIR", tmp_path / "backups")
    database.init_db()
    database.salvar_equipamento("Betoneira", "Marca", "Obra", 100.0, quantidade=2)
    return 1


def test_aluguel_futuro_so_reduz_as_proprias_datas(equipamento):
    alugar(equipamento, 30, 32)

    assert disponivel(equipamento, 0) == 2
    assert disponivel(equipamento, 31) == 1


def test_periodo_usa_o_pico_e_nao_a_soma(equipamento):
    alugar(equipamento, 30, 31)
    alugar(equipamento, 40, 41)

    assert disponivel(equipamento, 25, 45) == 1


def test_recusa_reserva_acima_do_estoque(equipamento):
    alugar(equipamento, 10, 12, qtd=2)

    with pytest.raises(database.EstoqueInsuficienteError):
        alugar(equipamento, 11, 11)


def test_nao_exclui_equipamento_em_contrato_aberto(equipamento):
    alugar(equipamento, 1, 2)

    with pytest.raises(ValueError):
        database.excluir_equipamento(equipamento)


def test_recusa_patrimonio_repetido(equipamento):
    database.salvar_equipamento("Serra", "", "", 10.0, patrimonio="AB-1")

    with pytest.raises(database.PatrimonioDuplicadoError):
        database.salvar_equipamento("Outra", "", "", 10.0, patrimonio="ab-1")
