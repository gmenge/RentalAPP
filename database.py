import sqlite3
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime, date

# Força o caminho absoluto baseado no local deste arquivo de script
BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "rental_app.db"
BACKUP_DIR = BASE_DIR / "backups"

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
                diaria REAL NOT NULL
            )
        """)

        # Migrações automáticas para garantir colunas existentes
        cursor.execute("PRAGMA table_info(equipamentos)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        if "marca" not in colunas:
            cursor.execute("ALTER TABLE equipamentos ADD COLUMN marca TEXT DEFAULT ''")
        if "categoria" not in colunas:
            cursor.execute("ALTER TABLE equipamentos ADD COLUMN categoria TEXT DEFAULT ''")

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

def salvar_equipamento(nome, marca, categoria, diaria, quantidade=1, eq_id=None):
    """Insere ou atualiza um equipamento garantindo a existência da tabela."""
    init_db()  # Força verificação da tabela antes de qualquer inserção
    conn = get_connection()
    cursor = conn.cursor()

    if eq_id:
        cursor.execute("""
            UPDATE equipamentos
            SET nome = ?, marca = ?, categoria = ?, quantidade = ?, diaria = ?
            WHERE id = ?
        """, (nome, marca, categoria, quantidade, diaria, eq_id))
    else:
        cursor.execute("""
            INSERT INTO equipamentos (nome, marca, categoria, quantidade, diaria)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, marca, categoria, quantidade, diaria))

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

def get_equipamentos_com_disponibilidade():
    """Retorna equipamentos calculando a quantidade disponível."""
    init_db()
    conn = get_connection()

    query = """
        SELECT 
            e.id, 
            e.nome,
            COALESCE(e.marca, '') AS marca,
            COALESCE(e.categoria, '') AS categoria,
            e.quantidade AS qtd_total, 
            e.diaria,
            COALESCE(SUM(CASE WHEN a.status IN ('Ativo', 'Atrasado') THEN ia.quantidade ELSE 0 END), 0) AS qtd_alugada
        FROM equipamentos e
        LEFT JOIN itens_aluguel ia ON e.id = ia.equipamento_id
        LEFT JOIN alugueis a ON ia.aluguel_id = a.id
        GROUP BY e.id, e.nome, e.marca, e.categoria, e.quantidade, e.diaria
        ORDER BY e.nome ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['qtd_disponivel'] = df['qtd_total'] - df['qtd_alugada']
        df['qtd_disponivel'] = df['qtd_disponivel'].apply(lambda x: max(0, x))
    else:
        df['qtd_disponivel'] = 0

    return df

def excluir_equipamento(eq_id):
    """Exclui um equipamento pelo ID."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM equipamentos WHERE id = ?", (eq_id,))
    conn.commit()
    conn.close()
    realizar_backup()

deletar_equipamento = excluir_equipamento

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
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

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
    conn.close()
    realizar_backup()

def get_todos_alugueis():
    init_db()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM alugueis ORDER BY id DESC", conn)
    conn.close()
    return df

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