import customtkinter as ctk
from tkinter import ttk, messagebox

from views.base_frame import BaseFrame
from database import get_todos_alugueis, finalizar_aluguel

class GestaoAlugueisView(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, titulo="📂 Gestão de Contratos de Aluguel")
        self.render()

    def render(self):
        self.clear_view()
        self.render_header()

        frame_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame_scroll.pack(fill="both", expand=True)

        df_alug = get_todos_alugueis()

        df_ativos = df_alug[df_alug['status'].isin(['Ativo', 'Atrasado'])] if not df_alug.empty else df_alug
        df_concluidos = df_alug[df_alug['status'] == 'Concluído/Devolvido'] if not df_alug.empty else df_alug

        # 1. TABELA DE CONTRATOS ATIVOS / ATRASADOS
        card_ativos = ctk.CTkFrame(frame_scroll, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        card_ativos.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_ativos, 
            text="🟢 Contratos Em Aberto (Ativos e Atrasados)", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FAFAFA"
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_tree_ativos = ctk.CTkFrame(card_ativos, fg_color="transparent")
        f_tree_ativos.pack(fill="x", padx=15, pady=(0, 10))

        cols = ("ID", "Cliente", "CPF/CNPJ", "Início", "Devolução", "Total (R$)", "Status")
        tree_ativos = ttk.Treeview(f_tree_ativos, columns=cols, show="headings", height=6)

        vsb_a = ttk.Scrollbar(f_tree_ativos, orient="vertical", command=tree_ativos.yview)
        tree_ativos.configure(yscrollcommand=vsb_a.set)
        vsb_a.pack(side="right", fill="y")

        for col in cols:
            tree_ativos.heading(col, text=col)
            tree_ativos.column(col, anchor="center", width=120)

        tree_ativos.column("Cliente", anchor="w", width=200)

        if not df_ativos.empty:
            for _, r in df_ativos.iterrows():
                tree_ativos.insert("", "end", values=(
                    r['id'], r['nome_cliente'], r['cpf_cnpj'], r['data_inicio'], r['data_devolucao'], f"R$ {r['valor_total']:.2f}", r['status']
                ))

        tree_ativos.pack(fill="x")

        def dar_baixa_devolucao():
            item_selecionado = tree_ativos.selection()
            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um contrato ATIVO na tabela para registrar a devolução.")
                return

            valores = tree_ativos.item(item_selecionado[0], 'values')
            aluguel_id = int(valores[0])

            if messagebox.askyesno("Confirmar Devolução", f"Confirmar baixa e devolução do Contrato #{aluguel_id}?"):
                finalizar_aluguel(aluguel_id)
                messagebox.showinfo("Sucesso", f"Contrato #{aluguel_id} finalizado com sucesso!")
                self.render()

        btn_devolucao = ctk.CTkButton(
            card_ativos, 
            text="✅ Registrar Devolução / Finalizar Contrato Selecionado", 
            command=dar_baixa_devolucao,
            height=38,
            corner_radius=8,
            fg_color="#059669",
            hover_color="#047857",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        btn_devolucao.pack(padx=15, pady=(5, 15), fill="x")

        # 2. TABELA DE CONTRATOS CONCLUÍDOS
        card_concluidos = ctk.CTkFrame(frame_scroll, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        card_concluidos.pack(fill="x", pady=5)

        ctk.CTkLabel(
            card_concluidos, 
            text="⚪ Histórico de Contratos Concluídos", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FAFAFA"
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_tree_concl = ctk.CTkFrame(card_concluidos, fg_color="transparent")
        f_tree_concl.pack(fill="x", padx=15, pady=(0, 15))

        tree_concluidos = ttk.Treeview(f_tree_concl, columns=cols, show="headings", height=6)

        vsb_c = ttk.Scrollbar(f_tree_concl, orient="vertical", command=tree_concluidos.yview)
        tree_concluidos.configure(yscrollcommand=vsb_c.set)
        vsb_c.pack(side="right", fill="y")

        for col in cols:
            tree_concluidos.heading(col, text=col)
            tree_concluidos.column(col, anchor="center", width=120)

        tree_concluidos.column("Cliente", anchor="w", width=200)

        if not df_concluidos.empty:
            for _, r in df_concluidos.iterrows():
                tree_concluidos.insert("", "end", values=(
                    r['id'], r['nome_cliente'], r['cpf_cnpj'], r['data_inicio'], r['data_devolucao'], f"R$ {r['valor_total']:.2f}", r['status']
                ))

        tree_concluidos.pack(fill="x")