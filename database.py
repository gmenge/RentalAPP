import os
import sys
import sqlite3
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime, date

from importador import chave_equipamento

class EstoqueInsuficienteError(Exception):
    """O período pedido não tem unidades livres de um equipamento."""

class PatrimonioDuplicadoError(Exception):
    """O número de patrimônio já pertence a outro equipamento."""

def _pasta_dados():
    """Retorna a pasta onde os dados ficam salvos de forma permanente."""
    # No executável, __file__ aponta para uma pasta temporária apagada ao fechar o app
    if getattr(sys, "frozen", False):
        pasta = Path(os.environ.get("APPDATA") or Path.home()) / "LocaFacil"
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta
    return Path(__file__).resolve().parent

BASE_DIR = _pasta_dados()
DB_NAME = BASE_DIR / "rental_app.db"
BACKUP_DIR = BASE_DIR / "backups"
DATA_MAXIMA = "9999-12-31"

def get_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite no caminho absoluto."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def realizar_backup():
    """Cria uma cópia de segurança do banco de dados na pasta 'backups/'."""
    try:
        BACKUP_DIR.mkdir(exist_ok=True)
        if not DB_NAME.exists():
            return

        destino_principal = BACKUP_DIR / "rental_app_backup.db"
        shutil.copy2(DB_NAME, destino_principal)
    except Exception as e:
        print(f"Erro ao realizar backup do banco de dados: {e}")

def restaurar_backup():
    """Restaura o banco de dados principal a partir do último backup."""
    backup_file = BACKUP_DIR / "rental_app_backup.db"

    if not backup_file.exists():
        print("Erro: Nenhum arquivo de backup foi encontrado.")
        return False

    try:
        shutil.copy2(backup_file, DB_NAME)
        print("Banco de dados restaurado com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao restaurar o banco de dados: {e}")
        return False

def init_db():
    """Inicializa o banco de dados e cria as tabelas caso não existam."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Tabela de Equipamentos (incluindo marca e categoria)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT DEFAULT '',
                categoria TEXT DEFAULT '',
                quantidade INTEGER NOT NULL DEFAULT 1,
                diaria REAL NOT NULL,
                patrimonio TEXT DEFAULT ''
            )
        """)

        # Migrações automáticas para garantir colunas existentes
        cursor.execute("PRAGMA table_info(equipamentos)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        if "marca" not in colunas:
            cursor.execute("ALTER TABLE equipamentos ADD COLUMN marca TEXT DEFAULT ''")
        if "categoria" not in colunas:
            cursor.execute("ALTER TABLE equipamentos ADD COLUMN categoria TEXT DEFAULT ''")
        if "patrimonio" not in colunas:
            cursor.execute("ALTER TABLE equipamentos ADD COLUMN patrimonio TEXT DEFAULT ''")

        # Tabela de Aluguéis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alugueis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_cpf TEXT NOT NULL,
                cliente_nome TEXT NOT NULL,
                cliente_endereco TEXT NOT NULL,
                data_inicio TEXT NOT NULL,
                data_devolucao TEXT NOT NULL,
                horario TEXT NOT NULL,
                valor_total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Ativo'
            )
        """)

        # Tabela de Itens do Aluguel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_aluguel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aluguel_id INTEGER NOT NULL,
                equipamento_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (aluguel_id) REFERENCES alugueis(id),
                FOREIGN KEY (equipamento_id) REFERENCES equipamentos(id)
            )
        """)

        conn.commit()
    except Exception as e:
        print(f"Erro durante a inicialização do banco: {e}")
    finally:
        conn.close()

    atualizar_status_atrasados()

def atualizar_status_atrasados():
    """Atualiza para 'Atrasado' os aluguéis vencidos."""
    conn = get_connection()
    cursor = conn.cursor()
    hoje = date.today().isoformat()

    cursor.execute("""
        UPDATE alugueis
        SET status = 'Atrasado'
        WHERE status = 'Ativo' AND data_devolucao < ?
    """, (hoje,))

    conn.commit()
    conn.close()

# -------------------------------------------------------------------
# FUNÇÕES DE EQUIPAMENTOS
# -------------------------------------------------------------------

def salvar_equipamento(nome, marca, categoria, diaria, quantidade=1, eq_id=None, patrimonio=""):
    """Insere ou atualiza um equipamento garantindo a existência da tabela."""
    init_db()  # Força verificação da tabela antes de qualquer inserção
    conn = get_connection()
    cursor = conn.cursor()

    if patrimonio:
        cursor.execute(
            "SELECT nome FROM equipamentos WHERE LOWER(patrimonio) = LOWER(?) AND id != ?",
            (patrimonio, eq_id or 0)
        )
        outro = cursor.fetchone()
        if outro:
            conn.close()
            raise PatrimonioDuplicadoError(f"O patrimônio {patrimonio} já pertence a '{outro['nome']}'.")

    if eq_id:
        cursor.execute("""
            UPDATE equipamentos
            SET nome = ?, marca = ?, categoria = ?, quantidade = ?, diaria = ?, patrimonio = ?
            WHERE id = ?
        """, (nome, marca, categoria, quantidade, diaria, patrimonio, eq_id))
    else:
        cursor.execute("""
            INSERT INTO equipamentos (nome, marca, categoria, quantidade, diaria, patrimonio)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, marca, categoria, quantidade, diaria, patrimonio))

    conn.commit()
    conn.close()
    realizar_backup()

def get_todos_equipamentos():
    """Retorna todos os equipamentos em formato DataFrame."""
    init_db()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM equipamentos ORDER BY nome ASC", conn)
    conn.close()
    return df

def _periodos_ocupados(conn):
    """Retorna {equipamento_id: [(inicio, fim, quantidade), ...]} dos aluguéis em aberto."""
    # Um aluguel atrasado segue fora do estoque até ser devolvido, sem data prevista
    linhas = conn.execute("""
        SELECT
            ia.equipamento_id,
            a.data_inicio,
            CASE WHEN a.status = 'Atrasado' THEN ? ELSE a.data_devolucao END AS fim,
            ia.quantidade
        FROM itens_aluguel ia
        JOIN alugueis a ON ia.aluguel_id = a.id
        WHERE a.status IN ('Ativo', 'Atrasado')
    """, (DATA_MAXIMA,)).fetchall()

    periodos = {}
    for eq_id, inicio, fim, quantidade in linhas:
        periodos.setdefault(eq_id, []).append((inicio, fim, quantidade))
    return periodos

def _qtd_ocupada(periodos, inicio, fim):
    """Retorna o pico de unidades em uso em qualquer dia entre inicio e fim."""
    # O uso só aumenta quando um aluguel começa, então basta olhar esses dias
    no_intervalo = [p for p in periodos if p[0] <= fim and p[1] >= inicio]
    dias = {max(p[0], inicio) for p in no_intervalo}
    return max((sum(q for i, f, q in no_intervalo if i <= dia <= f) for dia in dias), default=0)

def get_equipamentos_com_disponibilidade(data_inicio=None, data_fim=None):
    """Retorna equipamentos com a quantidade disponível no período (padrão: hoje)."""
    init_db()
    hoje = date.today().isoformat()
    data_inicio = data_inicio or hoje
    data_fim = data_fim or data_inicio

    conn = get_connection()
    query = """
        SELECT
            id,
            nome,
            COALESCE(marca, '') AS marca,
            COALESCE(categoria, '') AS categoria,
            quantidade AS qtd_total,
            diaria,
            COALESCE(patrimonio, '') AS patrimonio
        FROM equipamentos
        ORDER BY nome ASC
    """
    df = pd.read_sql_query(query, conn)
    periodos = _periodos_ocupados(conn)
    conn.close()

    df['qtd_alugada'] = [_qtd_ocupada(periodos.get(eq_id, []), data_inicio, data_fim) for eq_id in df['id']]
    df['qtd_disponivel'] = (df['qtd_total'] - df['qtd_alugada']).clip(lower=0)

    return df

def excluir_equipamento(eq_id):
    """Exclui um equipamento pelo ID, desde que não esteja em um aluguel em aberto."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM itens_aluguel ia
        JOIN alugueis a ON ia.aluguel_id = a.id
        WHERE ia.equipamento_id = ? AND a.status IN ('Ativo', 'Atrasado')
    """, (eq_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        raise ValueError("Este equipamento está em um aluguel em aberto.")

    cursor.execute("DELETE FROM equipamentos WHERE id = ?", (eq_id,))
    conn.commit()
    conn.close()
    realizar_backup()

deletar_equipamento = excluir_equipamento

def localizar_equipamentos(itens):
    """Retorna, para cada item, o id do cadastro que ele atualiza (None se for novo).

    Com patrimônio, o item corresponde ao cadastro de mesmo patrimônio ou, se não
    houver, preenche um cadastro de mesmo nome e marca que ainda não tenha patrimônio.
    Sem patrimônio, corresponde pelo nome e marca.
    """
    por_patrimonio, por_nome, sem_patrimonio = {}, {}, {}
    for equipamento in get_todos_equipamentos().to_dict("records"):
        chave = chave_equipamento(equipamento['nome'], equipamento['marca'] or '')
        patrimonio = (equipamento['patrimonio'] or '').strip().casefold()
        por_nome.setdefault(chave, equipamento['id'])
        if patrimonio:
            por_patrimonio[patrimonio] = equipamento['id']
        else:
            sem_patrimonio.setdefault(chave, equipamento['id'])

    ids = []
    for item in itens:
        chave = chave_equipamento(item['nome'], item['marca'])
        patrimonio = item['patrimonio'].casefold()
        if patrimonio in por_patrimonio:
            ids.append(por_patrimonio[patrimonio])
        elif patrimonio:
            ids.append(sem_patrimonio.pop(chave, None))
        else:
            ids.append(por_nome.get(chave))
    return ids

def importar_equipamentos(itens):
    """Cadastra uma lista de equipamentos de uma só vez e atualiza os já existentes.

    Em itens existentes, categoria e patrimônio vazios e quantidade None mantêm o
    valor atual. Retorna (novos, atualizados).
    """
    ids = localizar_equipamentos(itens)
    conn = get_connection()
    novos = atualizados = 0

    try:
        for item, eq_id in zip(itens, ids):
            if eq_id:
                conn.execute("""
                    UPDATE equipamentos
                    SET categoria = COALESCE(NULLIF(?, ''), categoria),
                        quantidade = COALESCE(?, quantidade),
                        diaria = ?,
                        patrimonio = COALESCE(NULLIF(?, ''), patrimonio)
                    WHERE id = ?
                """, (item['categoria'], item['quantidade'], item['diaria'], item['patrimonio'], eq_id))
                atualizados += 1
            else:
                conn.execute("""
                    INSERT INTO equipamentos (nome, marca, categoria, quantidade, diaria, patrimonio)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (item['nome'], item['marca'], item['categoria'], item['quantidade'] or 1, item['diaria'], item['patrimonio']))
                novos += 1
        conn.commit()
    finally:
        conn.close()

    realizar_backup()
    return novos, atualizados

# -------------------------------------------------------------------
# FUNÇÕES DO DASHBOARD E ALUGUÉIS
# -------------------------------------------------------------------

def get_estatisticas_dashboard():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(valor_total) FROM alugueis")
    res_fat = cursor.fetchone()[0]
    faturamento_total = res_fat if res_fat else 0.0

    cursor.execute("SELECT COUNT(*) FROM alugueis WHERE status = 'Ativo'")
    alugueis_ativos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM alugueis WHERE status = 'Atrasado'")
    alugueis_atrasados = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantidade) FROM equipamentos")
    res_eq = cursor.fetchone()[0]
    total_equipamentos = res_eq if res_eq else 0

    conn.close()

    return {
        "faturamento_total": float(faturamento_total),
        "alugueis_ativos": int(alugueis_ativos),
        "alugueis_atrasados": int(alugueis_atrasados),
        "total_equipamentos": int(total_equipamentos)
    }

def get_alugueis_recentes(limit=10):
    init_db()
    conn = get_connection()
    query = f"""
        SELECT id, cliente_nome, data_inicio, data_devolucao, valor_total, status
        FROM alugueis
        ORDER BY id DESC
        LIMIT {limit}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def registrar_aluguel(cpf, nome, endereco, dt_inicio, dt_devolucao, horario, itens, valor_total):
    """Registra um aluguel com um ou mais itens, conferindo o estoque do período."""
    init_db()
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()
        periodos = _periodos_ocupados(conn)

        for item in itens:
            cursor.execute("SELECT nome, quantidade FROM equipamentos WHERE id = ?", (item['id'],))
            equipamento = cursor.fetchone()
            ocupadas = _qtd_ocupada(periodos.get(item['id'], []), dt_inicio, dt_devolucao)
            if equipamento is None or item['qtd_alugada'] > equipamento['quantidade'] - ocupadas:
                nome_eq = equipamento['nome'] if equipamento else f"ID {item['id']}"
                raise EstoqueInsuficienteError(f"Estoque insuficiente de '{nome_eq}' nesse período.")

        cursor.execute("""
            INSERT INTO alugueis (cliente_cpf, cliente_nome, cliente_endereco, data_inicio, data_devolucao, horario, valor_total, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Ativo')
        """, (cpf, nome, endereco, dt_inicio, dt_devolucao, horario, valor_total))

        aluguel_id = cursor.lastrowid

        for item in itens:
            cursor.execute("""
                INSERT INTO itens_aluguel (aluguel_id, equipamento_id, quantidade, subtotal)
                VALUES (?, ?, ?, ?)
            """, (aluguel_id, item['id'], item['qtd_alugada'], item['subtotal']))

        conn.commit()
    finally:
        conn.close()

    realizar_backup()

def get_todos_alugueis():
    init_db()
    conn = get_connection()
    query = """
        SELECT a.*, COALESCE(resumo.itens, '') AS itens
        FROM alugueis a
        LEFT JOIN (
            SELECT
                ia.aluguel_id,
                GROUP_CONCAT(ia.quantidade || 'x ' || COALESCE(e.nome, '(excluído)'), ', ') AS itens
            FROM itens_aluguel ia
            LEFT JOIN equipamentos e ON ia.equipamento_id = e.id
            GROUP BY ia.aluguel_id
        ) resumo ON resumo.aluguel_id = a.id
        ORDER BY a.id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def atualizar_aluguel(aluguel_id, cpf, nome, endereco, dt_inicio, dt_devolucao, horario, valor_total):
    """Atualiza os dados de um aluguel, mantendo seus itens e status."""
    init_db()
    conn = get_connection()
    conn.execute("""
        UPDATE alugueis
        SET cliente_cpf = ?, cliente_nome = ?, cliente_endereco = ?,
            data_inicio = ?, data_devolucao = ?, horario = ?, valor_total = ?
        WHERE id = ?
    """, (cpf, nome, endereco, dt_inicio, dt_devolucao, horario, valor_total, aluguel_id))
    conn.commit()
    conn.close()
    realizar_backup()

def excluir_aluguel(aluguel_id):
    """Exclui um aluguel e seus itens."""
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM itens_aluguel WHERE aluguel_id = ?", (aluguel_id,))
    conn.execute("DELETE FROM alugueis WHERE id = ?", (aluguel_id,))
    conn.commit()
    conn.close()
    realizar_backup()

def finalizar_aluguel(aluguel_id):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alugueis SET status = 'Finalizado' WHERE id = ?", (aluguel_id,))
    conn.commit()
    conn.close()
    realizar_backup()

# Inicializa o banco no momento da importação
init_db()