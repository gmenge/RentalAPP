import re

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

from views import tema
from views.seletor import normalizar
from database import (
    PatrimonioDuplicadoError,
    get_equipamentos_com_disponibilidade,
    importar_equipamentos,
    localizar_equipamentos,
    salvar_equipamento,
    excluir_equipamento
)
from importador import (
    COLUNAS_MODELO,
    TIPOS_ARQUIVO,
    ErroImportacao,
    converter_valor,
    gerar_modelo,
    ler_equipamentos
)

LARGURA_BOTAO = 130

# (chave no dado, título, largura, alinhamento)
COLUNAS_TABELA = (
    ("id", "ID", 50, "center"),
    ("patrimonio", "Patrimônio", 90, "center"),
    ("nome", "Nome do Equipamento", 170, "w"),
    ("marca", "Marca", 110, "w"),
    ("categoria", "Categoria", 110, "w"),
    ("diaria", "Diária (R$)", 90, "e"),
    ("qtd_total", "Qtd. Total", 80, "center"),
    ("qtd_disponivel", "Disp. Hoje", 100, "center"),
)

def chave_ordenacao(valor):
    """Compara textos sem acento e com números na ordem natural (2 antes de 10)."""
    if isinstance(valor, str):
        return [int(parte) if parte.isdigit() else parte for parte in re.split(r"(\d+)", normalizar(valor))]
    return [valor]

class EquipamentosView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        # Layout Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # -------------------------------------------------------------
        # 1. CABEÇALHO DA TELA
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        lbl_titulo = ctk.CTkLabel(
            header_frame,
            text="Gestão de Equipamentos",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=tema.TEXTO
        )
        lbl_titulo.pack(side="left")

        # Botão Excluir Equipamento
        btn_excluir = ctk.CTkButton(
            header_frame,
            text="Excluir",
            **tema.BOTAO_PERIGO,
            width=LARGURA_BOTAO,
            height=36,
            command=self.confirmar_exclusao
        )
        btn_excluir.pack(side="right", padx=(10, 0))

        # Botão Editar Equipamento
        btn_editar = ctk.CTkButton(
            header_frame,
            text="Editar",
            **tema.BOTAO_SECUNDARIO,
            width=LARGURA_BOTAO,
            height=36,
            command=self.editar_selecionado
        )
        btn_editar.pack(side="right", padx=(10, 0))

        # Botão Novo Equipamento
        btn_novo = ctk.CTkButton(
            header_frame,
            text="Novo Equipamento",
            **tema.BOTAO_PRIMARIO,
            width=LARGURA_BOTAO,
            height=36,
            command=self.abrir_modal_cadastro
        )
        btn_novo.pack(side="right")

        # -------------------------------------------------------------
        # 2. BARRA DE PESQUISA (FILTRO EM TEMPO REAL)
        # -------------------------------------------------------------
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        search_frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            search_frame,
            placeholder_text="Pesquisar por Nome, Marca, Categoria ou Patrimônio...",
            height=36,
        )
        self.entry_busca.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # Evento de digitação para filtrar instantaneamente
        self.entry_busca.bind("<KeyRelease>", self.filtrar_tabela)

        btn_importar = ctk.CTkButton(
            search_frame,
            text="Importar Lista",
            **tema.BOTAO_SECUNDARIO,
            width=LARGURA_BOTAO,
            height=36,
            command=self.importar_lista
        )
        btn_importar.grid(row=0, column=1, padx=(0, 10))

        btn_modelo = ctk.CTkButton(
            search_frame,
            text="Baixar Modelo",
            **tema.BOTAO_SECUNDARIO,
            width=LARGURA_BOTAO,
            height=36,
            command=self.baixar_modelo
        )
        btn_modelo.grid(row=0, column=2)

        # -------------------------------------------------------------
        # 3. TABELA (TREEVIEW)
        # -------------------------------------------------------------
        table_frame = ctk.CTkFrame(self, fg_color=tema.SUPERFICIE, corner_radius=8)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=[coluna[0] for coluna in COLUNAS_TABELA], show="headings")

        # Cabeçalhos clicáveis para ordenar
        for chave, titulo, largura, alinhamento in COLUNAS_TABELA:
            self.tree.heading(chave, command=lambda c=chave: self.ordenar_por(c))
            self.tree.column(chave, width=largura, anchor=alinhamento)

        self.ordem_coluna = "nome"
        self.ordem_invertida = False
        self.atualizar_cabecalhos()

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.bind("<Double-1>", self.editar_selecionado)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)

        # Dados em memória para a busca instantânea
        self.todos_equipamentos = []

    def render(self):
        """Atualiza os dados da tela ao ser exibida."""
        self.carregar_dados()

    def carregar_dados(self):
        """Busca os equipamentos do banco de dados unificado e carrega na tabela."""
        try:
            df = get_equipamentos_com_disponibilidade()
            if not df.empty:
                self.todos_equipamentos = df.to_dict("records")
            else:
                self.todos_equipamentos = []
            
            self.filtrar_tabela()
        except Exception as e:
            self.todos_equipamentos = []
            messagebox.showerror("Erro", f"Falha ao carregar equipamentos: {e}")

    def ordenar_por(self, coluna):
        """Ordena pela coluna clicada; clicar de novo inverte a ordem."""
        self.ordem_invertida = coluna == self.ordem_coluna and not self.ordem_invertida
        self.ordem_coluna = coluna
        self.atualizar_cabecalhos()
        self.filtrar_tabela()

    def atualizar_cabecalhos(self):
        for chave, titulo, _, _ in COLUNAS_TABELA:
            seta = ""
            if chave == self.ordem_coluna:
                seta = " ▼" if self.ordem_invertida else " ▲"
            self.tree.heading(chave, text=titulo + seta)

    def atualizar_tabela(self, lista_dados):
        """Limpa e insere um conjunto específico de dados no Treeview, já ordenado."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Campos vazios ficam sempre no fim, em qualquer sentido da ordenação
        preenchidos = [row for row in lista_dados if row[self.ordem_coluna] != ""]
        vazios = [row for row in lista_dados if row[self.ordem_coluna] == ""]
        preenchidos.sort(key=lambda row: chave_ordenacao(row[self.ordem_coluna]), reverse=self.ordem_invertida)

        for row in preenchidos + vazios:
            eq_id = row['id']
            patrimonio = row['patrimonio'] if row['patrimonio'] else "-"
            nome = row['nome']
            marca = row['marca'] if row['marca'] else "-"
            categoria = row['categoria'] if row['categoria'] else "-"
            valor_fmt = f"R$ {float(row['diaria'] or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            qtd_total = row['qtd_total']
            qtd_disp = row['qtd_disponivel']

            self.tree.insert("", "end", values=(eq_id, patrimonio, nome, marca, categoria, valor_fmt, qtd_total, qtd_disp))

    def filtrar_tabela(self, event=None):
        """Filtra a lista por correspondência exata de trecho em qualquer campo."""
        termo = self.entry_busca.get().lower().strip()

        if not termo:
            self.atualizar_tabela(self.todos_equipamentos)
            return

        resultados = []
        for row in self.todos_equipamentos:
            campos_unificados = f"{row['id']} {row['nome']} {row['marca']} {row['categoria']} {row['patrimonio']}".lower()
            if termo in campos_unificados:
                resultados.append(row)

        self.atualizar_tabela(resultados)

    def confirmar_exclusao(self):
        """Ação para excluir o equipamento selecionado no Treeview."""
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um equipamento na tabela para excluir.")
            return

        valores = self.tree.item(selecionado[0], 'values')
        eq_id = int(valores[0])
        nome_eq = valores[2]

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o equipamento:\n'{nome_eq}' (ID: {eq_id})?"):
            try:
                excluir_equipamento(eq_id)
                messagebox.showinfo("Sucesso", "Equipamento excluído com sucesso!")
                self.carregar_dados()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível excluir o equipamento: {e}")

    def editar_selecionado(self, event=None):
        """Abre o modal preenchido com o equipamento selecionado no Treeview."""
        # O duplo clique só vale nas linhas: nos títulos ele ordena a tabela
        if event is not None and self.tree.identify_region(event.x, event.y) != "cell":
            return

        selecionado = self.tree.selection()
        if not selecionado:
            if event is None:
                messagebox.showwarning("Aviso", "Selecione um equipamento na tabela para editar.")
            return

        eq_id = int(self.tree.item(selecionado[0], 'values')[0])
        equipamento = next(row for row in self.todos_equipamentos if row['id'] == eq_id)
        self.abrir_modal_cadastro(equipamento)

    # -------------------------------------------------------------
    # 4. MODAL DE CADASTRO E EDIÇÃO
    # -------------------------------------------------------------
    def abrir_modal_cadastro(self, equipamento=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Equipamento" if equipamento else "Cadastrar Equipamento")
        modal.geometry("450x660")
        modal.grab_set()
        modal.resizable(False, False)

        lbl_modal_titulo = ctk.CTkLabel(
            modal,
            text="Editar Equipamento" if equipamento else "Novo Equipamento",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_modal_titulo.pack(pady=(20, 15))

        # Campo Nome
        lbl_nome = ctk.CTkLabel(modal, text="Nome do Equipamento:", anchor="w")
        lbl_nome.pack(fill="x", padx=30, pady=(5, 0))
        entry_nome = ctk.CTkEntry(modal, placeholder_text="Ex: Furadeira de Impacto")
        entry_nome.pack(fill="x", padx=30, pady=(0, 10))

        # Campo Marca
        lbl_marca = ctk.CTkLabel(modal, text="Marca:", anchor="w")
        lbl_marca.pack(fill="x", padx=30, pady=(5, 0))
        entry_marca = ctk.CTkEntry(modal, placeholder_text="Ex: Bosch, Makita, DeWalt")
        entry_marca.pack(fill="x", padx=30, pady=(0, 10))

        # Campo Categoria
        lbl_categoria = ctk.CTkLabel(modal, text="Categoria:", anchor="w")
        lbl_categoria.pack(fill="x", padx=30, pady=(5, 0))
        entry_categoria = ctk.CTkEntry(modal, placeholder_text="Ex: Ferramentas Elétricas")
        entry_categoria.pack(fill="x", padx=30, pady=(0, 10))

        # Campo Valor Diária
        lbl_valor = ctk.CTkLabel(modal, text="Valor da Diária (R$):", anchor="w")
        lbl_valor.pack(fill="x", padx=30, pady=(5, 0))
        entry_valor = ctk.CTkEntry(modal, placeholder_text="Ex: 45.00")
        entry_valor.pack(fill="x", padx=30, pady=(0, 10))

        # Campo Quantidade
        lbl_quantidade = ctk.CTkLabel(modal, text="Quantidade em Estoque:", anchor="w")
        lbl_quantidade.pack(fill="x", padx=30, pady=(5, 0))
        entry_quantidade = ctk.CTkEntry(modal)
        entry_quantidade.insert(0, "1")
        entry_quantidade.pack(fill="x", padx=30, pady=(0, 10))

        # Campo Patrimônio
        lbl_patrimonio = ctk.CTkLabel(modal, text="Número de Patrimônio:", anchor="w")
        lbl_patrimonio.pack(fill="x", padx=30, pady=(5, 0))
        entry_patrimonio = ctk.CTkEntry(modal, placeholder_text="Opcional")
        entry_patrimonio.pack(fill="x", padx=30, pady=(0, 20))

        if equipamento:
            entry_nome.insert(0, equipamento['nome'])
            entry_marca.insert(0, equipamento['marca'])
            entry_categoria.insert(0, equipamento['categoria'])
            entry_valor.insert(0, f"{equipamento['diaria']:.2f}".replace(".", ","))
            entry_quantidade.delete(0, "end")
            entry_quantidade.insert(0, str(equipamento['qtd_total']))
            if equipamento['patrimonio']:
                entry_patrimonio.insert(0, equipamento['patrimonio'])

        def salvar():
            nome = entry_nome.get().strip()
            marca = entry_marca.get().strip()
            categoria = entry_categoria.get().strip()
            valor = entry_valor.get().strip()

            if not nome or not valor:
                messagebox.showerror("Erro", "Nome e Valor da Diária são obrigatórios!", parent=modal)
                return

            try:
                valor_float = converter_valor(valor)
                quantidade = int(entry_quantidade.get().strip())
                if valor_float <= 0 or quantidade < 1:
                    raise ValueError

                salvar_equipamento(
                    nome, marca, categoria, valor_float, quantidade,
                    equipamento['id'] if equipamento else None,
                    entry_patrimonio.get().strip()
                )

                texto = "atualizado" if equipamento else "cadastrado"
                messagebox.showinfo("Sucesso", f"Equipamento {texto} com sucesso!", parent=modal)
                modal.destroy()
                self.carregar_dados()
            except PatrimonioDuplicadoError as e:
                messagebox.showerror("Erro", str(e), parent=modal)
            except ValueError:
                messagebox.showerror("Erro", "Insira valores numéricos válidos para a diária e a quantidade.", parent=modal)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar: {e}", parent=modal)

        btn_salvar = ctk.CTkButton(
            modal,
            text="Salvar Equipamento",
            **tema.BOTAO_PRIMARIO,
            height=36,
            command=salvar
        )
        btn_salvar.pack(fill="x", padx=30, pady=10)

    # -------------------------------------------------------------
    # 5. IMPORTAÇÃO DE LISTAS
    # -------------------------------------------------------------
    def baixar_modelo(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar planilha modelo",
            defaultextension=".xlsx",
            initialfile="modelo_equipamentos.xlsx",
            filetypes=[("Planilha do Excel", "*.xlsx")]
        )
        if not caminho:
            return

        try:
            gerar_modelo(caminho)
            messagebox.showinfo("Sucesso", f"Modelo salvo com as colunas:\n{', '.join(COLUNAS_MODELO)}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar o modelo: {e}")

    def importar_lista(self):
        caminho = filedialog.askopenfilename(title="Selecionar lista de equipamentos", filetypes=TIPOS_ARQUIVO)
        if not caminho:
            return

        try:
            linhas = ler_equipamentos(caminho)
        except ErroImportacao as e:
            messagebox.showerror("Erro na Importação", str(e))
            return

        self.abrir_previa_importacao(linhas)

    def abrir_previa_importacao(self, linhas):
        """Mostra o que será importado antes de gravar qualquer dado."""
        validas = [linha for linha in linhas if not linha['erro']]
        ids = localizar_equipamentos(validas)
        destino = {linha['linha']: eq_id for linha, eq_id in zip(validas, ids)}
        atualizacoes = sum(eq_id is not None for eq_id in ids)

        modal = ctk.CTkToplevel(self)
        modal.title("Importar Equipamentos")
        modal.geometry("960x520")
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text=f"{len(validas) - atualizacoes} novos, {atualizacoes} a atualizar, {len(linhas) - len(validas)} com erro (ignorados)",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        def confirmar():
            try:
                novos, atualizados = importar_equipamentos(validas)
                messagebox.showinfo("Sucesso", f"Importação concluída!\n{novos} novos e {atualizados} atualizados.", parent=modal)
                modal.destroy()
                self.carregar_dados()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao importar: {e}", parent=modal)

        # Empacotado antes da tabela para não ser comprimido por ela
        ctk.CTkButton(
            modal,
            text=f"Importar {len(validas)} Equipamentos",
            **tema.BOTAO_PRIMARIO,
            height=36,
            state="normal" if validas else "disabled",
            command=confirmar
        ).pack(side="bottom", fill="x", padx=20, pady=15)

        f_tabela = ctk.CTkFrame(modal, fg_color=tema.SUPERFICIE, corner_radius=8)
        f_tabela.pack(fill="both", expand=True, padx=20)

        colunas = ("linha", "nome", "marca", "categoria", "diaria", "quantidade", "patrimonio", "situacao")
        titulos = ("Linha", "Nome", "Marca", "Categoria", "Diária", "Qtd.", "Patrimônio", "Situação")
        larguras = (50, 190, 100, 110, 80, 50, 90, 200)

        tree = ttk.Treeview(f_tabela, columns=colunas, show="headings")
        for coluna, titulo, largura in zip(colunas, titulos, larguras):
            tree.heading(coluna, text=titulo)
            tree.column(coluna, width=largura, anchor="w")
        tree.tag_configure("erro", foreground=tema.ALERTA)

        scrollbar = ttk.Scrollbar(f_tabela, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", pady=10)
        tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        for linha in linhas:
            if linha['erro']:
                situacao = linha['erro']
            elif destino[linha['linha']] is not None:
                situacao = "Atualizar"
            else:
                situacao = "Novo"

            diaria = "" if linha['diaria'] is None else f"R$ {linha['diaria']:.2f}"
            tree.insert(
                "", "end",
                values=(linha['linha'], linha['nome'], linha['marca'], linha['categoria'], diaria, linha['quantidade'] or "", linha['patrimonio'], situacao),
                tags=("erro",) if linha['erro'] else ()
            )
