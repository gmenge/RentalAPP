import pytest

import importador


@pytest.mark.parametrize("entrada, esperado", [
    (45, 45.0),
    ("45,50", 45.5),
    ("1.234,56", 1234.56),
    ("1,234.56", 1234.56),
    ("R$ 1.500", 1500.0),
    ("2.50", 2.5),
])
def test_converte_valores(entrada, esperado):
    assert importador.converter_valor(entrada) == esperado


@pytest.mark.parametrize("entrada", ["abc", "nan", "inf", "1e5", "", "-5"])
def test_recusa_valores_invalidos(entrada):
    with pytest.raises(ValueError):
        importador.converter_valor(entrada)


def test_reconhece_colunas_em_qualquer_ordem(tmp_path):
    arquivo = tmp_path / "lista.csv"
    arquivo.write_text("Qtd;Diária;Nome;Marca\n2;45,50;Furadeira;Bosch\n", encoding="utf-8")

    item = importador.ler_equipamentos(str(arquivo))[0]

    assert (item["nome"], item["marca"], item["diaria"], item["quantidade"]) == ("Furadeira", "Bosch", 45.5, 2)


def test_sem_titulos_usa_a_ordem_padrao(tmp_path):
    arquivo = tmp_path / "lista.txt"
    arquivo.write_text("Furadeira;Bosch;Obra;45,50;3;P1\n", encoding="utf-8")

    item = importador.ler_equipamentos(str(arquivo))[0]

    assert (item["categoria"], item["quantidade"], item["patrimonio"]) == ("Obra", 3, "P1")


def test_mesmo_nome_com_patrimonios_diferentes_nao_e_repetido(tmp_path):
    arquivo = tmp_path / "lista.csv"
    arquivo.write_text(
        "Nome;Diária;Patrimônio\nSerra;10;A1\nSerra;10;A2\nSerra;10;A1\n", encoding="utf-8"
    )

    linhas = importador.ler_equipamentos(str(arquivo))

    assert [bool(l["erro"]) for l in linhas] == [False, False, True]


def test_recusa_doc_antigo(tmp_path):
    arquivo = tmp_path / "lista.doc"
    arquivo.write_bytes(b"x")

    with pytest.raises(importador.ErroImportacao):
        importador.ler_equipamentos(str(arquivo))
