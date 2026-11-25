import csv
import math
import re
import unicodedata
from pathlib import Path

import pandas as pd

COLUNAS_MODELO = ["Nome", "Marca", "Categoria", "Diária", "Quantidade", "Patrimônio"]
CAMPOS = ["nome", "marca", "categoria", "diaria", "quantidade", "patrimonio"]

# Nomes de coluna aceitos, já sem acentos, espaços ou símbolos
ALIASES = {
    "nome": {"nome", "nomedoequipamento", "equipamento", "equipamentos", "item", "produto", "ferramenta", "descricao", "name"},
    "marca": {"marca", "fabricante", "brand"},
    "categoria": {"categoria", "tipo", "grupo", "category"},
    "diaria": {"diaria", "diariar", "valordiaria", "valordadiaria", "valor", "valorr", "preco", "precor", "precodiaria", "price", "dailyrate"},
    "quantidade": {"quantidade", "quant", "qtd", "qtde", "qtdtotal", "estoque", "unidades", "quantity", "qty"},
    "patrimonio": {"patrimonio", "npatrimonio", "nopatrimonio", "numpatrimonio", "numeropatrimonio", "numerodepatrimonio", "numerodopatrimonio", "plaqueta", "assettag"},
}

TIPOS_ARQUIVO = [
    ("Listas de equipamentos", "*.xlsx *.xlsm *.xls *.ods *.csv *.tsv *.txt *.xml *.json *.docx *.doc"),
    ("Todos os arquivos", "*.*"),
]


class ErroImportacao(Exception):
    """Arquivo que não pode ser lido, com mensagem pronta para o usuário."""


def chave_equipamento(nome, marca):
    """Identifica um equipamento ignorando maiúsculas e espaços nas pontas."""
    return (str(nome).strip().casefold(), str(marca).strip().casefold())


def converter_valor(valor):
    """Converte valores como 45, '45,50', '1.234,56' ou 'R$ 1.500' em float."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        numero = float(valor)
        if not math.isfinite(numero):
            raise ValueError(f"Valor inválido: {valor}")
        return numero

    texto = re.sub(r"(?i)r\$|\s", "", str(valor))
    if "," in texto and "." in texto:
        milhar = "." if texto.rfind(",") > texto.rfind(".") else ","
        texto = texto.replace(milhar, "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        texto = texto.replace(".", "")

    if not re.fullmatch(r"\d+(\.\d+)?", texto):
        raise ValueError(f"Valor inválido: {valor}")
    return float(texto)


def _texto(valor):
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def _normalizar(valor):
    sem_acento = unicodedata.normalize("NFKD", _texto(valor)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", sem_acento.lower())


def _campo_da_coluna(valor):
    normalizado = _normalizar(valor)
    for campo, nomes in ALIASES.items():
        if normalizado in nomes:
            return campo
    return None


def _dividir_linhas(linhas):
    """Separa linhas de texto pelo primeiro delimitador encontrado."""
    linhas = [linha for linha in linhas if linha.strip()]
    amostra = "\n".join(linhas[:20])
    # A vírgula fica por último porque também é separador decimal
    delimitador = next((d for d in (";", "\t", "|", ",") if d in amostra), ";")
    return [[campo.strip() for campo in linha] for linha in csv.reader(linhas, delimiter=delimitador)]


def _ler_texto(caminho):
    dados = Path(caminho).read_bytes()
    try:
        conteudo = dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        conteudo = dados.decode("cp1252", errors="replace")
    return _dividir_linhas(conteudo.splitlines())


def _ler_docx(caminho):
    from docx import Document

    documento = Document(caminho)
    tabelas = [[[celula.text.strip() for celula in linha.cells] for linha in tabela.rows] for tabela in documento.tables]
    if tabelas:
        for tabela in tabelas:
            if _achar_cabecalho(tabela) is not None:
                return tabela
        return tabelas[0]
    return _dividir_linhas([paragrafo.text for paragrafo in documento.paragraphs])


def _linhas_do_dataframe(df):
    return df.astype(object).values.tolist()


def _ler_linhas(caminho):
    extensao = Path(caminho).suffix.lower()

    if extensao == ".doc":
        raise ErroImportacao("O formato .doc antigo não é suportado.\nAbra o arquivo no Word e use 'Salvar como' para .docx.")
    if extensao in (".xlsx", ".xlsm", ".xls"):
        return _linhas_do_dataframe(pd.read_excel(caminho, header=None, dtype=object))
    if extensao == ".ods":
        return _linhas_do_dataframe(pd.read_excel(caminho, header=None, dtype=object, engine="odf"))
    if extensao in (".csv", ".tsv", ".txt"):
        return _ler_texto(caminho)
    if extensao == ".docx":
        return _ler_docx(caminho)
    if extensao in (".xml", ".json"):
        df = pd.read_xml(caminho, parser="etree") if extensao == ".xml" else pd.read_json(caminho)
        return [list(df.columns)] + _linhas_do_dataframe(df)
    raise ErroImportacao(f"Formato '{extensao or 'desconhecido'}' não suportado.")


def _achar_cabecalho(linhas):
    """Procura a linha de títulos, que pode vir depois de um título da planilha."""
    for indice, linha in enumerate(linhas[:10]):
        campos = {_campo_da_coluna(celula) for celula in linha} - {None}
        if len(campos) >= 2:
            return indice
    return None


def _mapa_colunas(linhas, indice_cabecalho):
    """Retorna {campo: posição da coluna}."""
    if indice_cabecalho is None:
        return dict(zip(CAMPOS, range(len(CAMPOS))))

    mapa = {}
    for posicao, celula in enumerate(linhas[indice_cabecalho]):
        campo = _campo_da_coluna(celula)
        if campo and campo not in mapa:
            mapa[campo] = posicao

    faltando = [nome for campo, nome in (("nome", "Nome"), ("diaria", "Diária")) if campo not in mapa]
    if faltando:
        raise ErroImportacao(f"Coluna obrigatória não encontrada: {', '.join(faltando)}.")
    return mapa


def _analisar_linha(valores):
    """Retorna (equipamento, erro) a partir dos valores crus de uma linha."""
    equipamento = {
        "nome": _texto(valores.get("nome")),
        "marca": _texto(valores.get("marca")),
        "categoria": _texto(valores.get("categoria")),
        "diaria": None,
        "quantidade": None,
        "patrimonio": _texto(valores.get("patrimonio")),
    }

    if not equipamento["nome"]:
        return equipamento, "Nome vazio"

    diaria = valores.get("diaria")
    if _texto(diaria) == "":
        return equipamento, "Diária vazia"
    try:
        equipamento["diaria"] = round(converter_valor(diaria), 2)
    except ValueError:
        return equipamento, f"Diária inválida: {_texto(diaria)}"
    if equipamento["diaria"] <= 0:
        return equipamento, "Diária deve ser maior que zero"

    quantidade = valores.get("quantidade")
    if _texto(quantidade) != "":
        try:
            numero = converter_valor(quantidade)
        except ValueError:
            return equipamento, f"Quantidade inválida: {_texto(quantidade)}"
        if numero < 1 or not numero.is_integer():
            return equipamento, f"Quantidade inválida: {_texto(quantidade)}"
        equipamento["quantidade"] = int(numero)

    return equipamento, None


def ler_equipamentos(caminho):
    """Lê um arquivo e retorna uma lista de dicts com os campos do equipamento,
    mais 'linha' (número no arquivo) e 'erro' (None quando a linha é válida).

    Colunas são reconhecidas pelo título. Sem títulos, a ordem esperada é
    Nome, Marca, Categoria, Diária, Quantidade, Patrimônio. Quantidade vazia vira None.
    """
    try:
        linhas = _ler_linhas(caminho)
    except ErroImportacao:
        raise
    except Exception as e:
        raise ErroImportacao(f"Não foi possível ler o arquivo:\n{e}") from e

    indice_cabecalho = _achar_cabecalho(linhas)
    mapa = _mapa_colunas(linhas, indice_cabecalho)
    primeira = 0 if indice_cabecalho is None else indice_cabecalho + 1

    resultado = []
    vistos = {}
    for numero, linha in enumerate(linhas[primeira:], start=primeira + 1):
        if not any(_texto(celula) for celula in linha):
            continue

        valores = {campo: linha[pos] for campo, pos in mapa.items() if pos < len(linha)}
        equipamento, erro = _analisar_linha(valores)

        if not erro:
            # Com patrimônio, itens de mesmo nome e marca são unidades diferentes
            patrimonio = equipamento["patrimonio"].casefold()
            chave = patrimonio or chave_equipamento(equipamento["nome"], equipamento["marca"])
            if chave in vistos:
                erro = f"Repetido da linha {vistos[chave]}"
            else:
                vistos[chave] = numero

        resultado.append({**equipamento, "linha": numero, "erro": erro})

    if not resultado:
        raise ErroImportacao("Nenhum equipamento encontrado no arquivo.")
    return resultado


def gerar_modelo(caminho):
    """Cria uma planilha .xlsx vazia com as colunas esperadas."""
    pd.DataFrame(columns=COLUNAS_MODELO).to_excel(caminho, index=False)
