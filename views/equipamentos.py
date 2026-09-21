import customtkinter as ctk
from tkinter import ttk, messagebox
from database import (
    get_equipamentos_com_disponibilidade, 
    salvar_equipamento, 
    excluir_equipamento
)

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
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#FAFAFA"
        )
        lbl_titulo.pack(side="left")

        # Botão Excluir Equipamento
        btn_excluir = ctk.CTkButton(
            header_frame,
            text="🗑 Excluir Selecionado",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            height=38,
            font=ctk.CTkFont(weight="bold"),
            command=self.confirmar_exclusao
        )
        btn_excluir.pack(side="right", padx=(10, 0))

        # Botão Novo Equipamento
        btn_novo = ctk.CTkButton(
            header_frame,
            text="+ Novo Equipamento",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=38,
            font=ctk.CTkFont(weight="bold"),
            command=self.abrir_modal_cadastro
        )
        btn_novo.pack(side="right")

        # -------------------------------------------------------------
        # 2. BARRA DE PESQUISA (FILTRO EM TEMPO REAL)
        # -------------------------------------------------------------
        search_frame = ctk.CTkFrame(self, fg_color="#18181B", corner_radius=8)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15), ipady=5)
        search_frame.grid_columnconfigure(0, weight=1)

        self.entry_busca = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Pesquisar por Nome, Marca ou Categoria...",
            height=40,
            border_width=1,
            fg_color="#09090B",
            border_color="#27272A",
            text_color="#FAFAFA"
        )
        self.entry_busca.grid(row=0, column=0, padx=15, pady=8, sticky="ew")
        
        # Evento de digitação para filtrar instantaneamente
        self.entry_busca.bind("<KeyRelease>", self.filtrar_tabela)

        # -------------------------------------------------------------
        # 3. TABELA (TREEVIEW)
        # -------------------------------------------------------------
        table_frame = ctk.CTkFrame(self, fg_color="#18181B", corner_radius=8)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        colunas = ("id", "nome", "marca", "categoria", "diaria", "qtd_total", "qtd_disp")
        self.tree = ttk.Treeview(table_frame, columns=colunas, show="headings")

        # Cabeçalhos
        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome do Equipamento")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("diaria", text="Diária (R$)")
        self.tree.heading("qtd_total", text="Qtd. Total")
        self.tree.heading("qtd_disp", text="Qtd. Disponível")

        # Larguras e Alinhamentos
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("nome", width=200, anchor="w")
        self.tree.column("marca", width=120, anchor="w")
        self.tree.column("categoria", width=120, anchor="w")
        self.tree.column("diaria", width=100, anchor="e")
        self.tree.column("qtd_total", width=90, anchor="center")
        self.tree.column("qtd_disp", width=110, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

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
            
            self.atualizar_tabela(self.todos_equipamentos)
        except Exception as e:
            self.todos_equipamentos = []
            messagebox.showerror("Erro", f"Falha ao carregar equipamentos: {e}")

    def atualizar_tabela(self, lista_dados):
        """Limpa e insere um conjunto específico de dados no Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in lista_dados:
            eq_id = row['id']
            nome = row['nome']
            marca = row['marca'] if row['marca'] else "-"
            categoria = row['categoria'] if row['categoria'] else "-"
            valor_fmt = f"R$ {float(row['diaria'] or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            qtd_total = row['qtd_total']
            qtd_disp = row['qtd_disponivel']

            self.tree.insert("", "end", values=(eq_id, nome, marca, categoria, valor_fmt, qtd_total, qtd_disp))

    def filtrar_tabela(self, event=None):
        """Filtra a lista por correspondência exata de trecho em qualquer campo."""
        termo = self.entry_busca.get().lower().strip()

        if not termo:
            self.atualizar_tabela(self.todos_equipamentos)
            return

        resultados = []
        for row in self.todos_equipamentos:
            campos_unificados = f"{row['id']} {row['nome']} {row['marca']} {row['categoria']}".lower()
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
        nome_eq = valores[1]

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o equipamento:\n'{nome_eq}' (ID: {eq_id})?"):
            try:
                excluir_equipamento(eq_id)
                messagebox.showinfo("Sucesso", "Equipamento excluído com sucesso!")
                self.carregar_dados()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível excluir o equipamento: {e}")

    # -------------------------------------------------------------
    # 4. MODAL DE CADASTRO
    # -------------------------------------------------------------
    def abrir_modal_cadastro(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Cadastrar Equipamento")
        modal.geometry("450x520")
        modal.grab_set()
        modal.resizable(False, False)

        lbl_modal_titulo = ctk.CTkLabel(
            modal, 
            text="Novo Equipamento", 
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
        entry_valor.pack(fill="x", padx=30, pady=(0, 20))

        def salvar():
            nome = entry_nome.get().strip()
            marca = entry_marca.get().strip()
            categoria = entry_categoria.get().strip()
            valor = entry_valor.get().strip()

            if not nome or not valor:
                messagebox.showerror("Erro", "Nome e Valor da Diária são obrigatórios!", parent=modal)
                return

            try:
                valor_float = float(valor.replace(",", "."))
                salvar_equipamento(nome, marca, categoria, valor_float)

                messagebox.showinfo("Sucesso", "Equipamento cadastrado com sucesso!", parent=modal)
                modal.destroy()
                self.carregar_dados()
            except ValueError:
                messagebox.showerror("Erro", "Insira um valor numérico válido para a diária.", parent=modal)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao salvar: {e}", parent=modal)

        btn_salvar = ctk.CTkButton(
            modal, 
            text="Salvar Equipamento", 
            fg_color="#2563EB", 
            hover_color="#1D4ED8",
            height=40,
            command=salvar
        )
        btn_salvar.pack(fill="x", padx=30, pady=10)