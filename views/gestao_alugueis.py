from datetime import date

import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from views import tema
from views.base_frame import BaseFrame, ESTILO_CALENDARIO, HORARIOS
from database import get_todos_alugueis, finalizar_aluguel, atualizar_aluguel, excluir_aluguel
from importador import converter_valor

class GestaoAlugueisView(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, titulo="Gestão de Contratos de Aluguel")
        self.render()

    def render(self):
        self.clear_view()
        self.render_header()

        frame_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame_scroll.pack(fill="both", expand=True)

        df_alug = get_todos_alugueis()

        df_ativos = df_alug[df_alug['status'].isin(['Ativo', 'Atrasado'])] if not df_alug.empty else df_alug
        df_concluidos = df_alug[df_alug['status'] == 'Finalizado'] if not df_alug.empty else df_alug

        # 1. TABELA DE CONTRATOS ATIVOS / ATRASADOS
        card_ativos = ctk.CTkFrame(frame_scroll, fg_color=tema.SUPERFICIE, corner_radius=8, border_width=1, border_color=tema.BORDA)
        card_ativos.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_ativos,
            text="Contratos em Aberto",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=tema.TEXTO
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_tree_ativos = ctk.CTkFrame(card_ativos, fg_color="transparent")
        f_tree_ativos.pack(fill="x", padx=15, pady=(0, 10))

        tree_ativos = self._criar_tabela(f_tree_ativos, df_ativos)

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
            text="Registrar Devolução",
            command=dar_baixa_devolucao,
            height=36,
            **tema.BOTAO_PRIMARIO,
        )
        btn_devolucao.pack(anchor="e", padx=15, pady=(5, 15))

        # 2. TABELA DE CONTRATOS CONCLUÍDOS
        card_concluidos = ctk.CTkFrame(frame_scroll, fg_color=tema.SUPERFICIE, corner_radius=8, border_width=1, border_color=tema.BORDA)
        card_concluidos.pack(fill="x", pady=5)

        ctk.CTkLabel(
            card_concluidos,
            text="Histórico de Contratos",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=tema.TEXTO
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_tree_concl = ctk.CTkFrame(card_concluidos, fg_color="transparent")
        f_tree_concl.pack(fill="x", padx=15, pady=(0, 10))

        tree_concluidos = self._criar_tabela(f_tree_concl, df_concluidos)

        def contrato_selecionado():
            item_selecionado = tree_concluidos.selection()
            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um contrato do histórico.")
                return None

            aluguel_id = int(tree_concluidos.item(item_selecionado[0], 'values')[0])
            return df_concluidos[df_concluidos['id'] == aluguel_id].iloc[0].to_dict()

        def editar_concluido():
            contrato = contrato_selecionado()
            if contrato:
                self.abrir_modal_edicao(contrato)

        def excluir_concluido():
            contrato = contrato_selecionado()
            if not contrato:
                return

            aviso = (
                f"Excluir definitivamente o Contrato #{contrato['id']} de {contrato['cliente_nome']}?\n\n"
                f"O valor de R$ {contrato['valor_total']:.2f} sairá do faturamento total."
            )
            if messagebox.askyesno("Confirmar Exclusão", aviso):
                excluir_aluguel(contrato['id'])
                messagebox.showinfo("Sucesso", f"Contrato #{contrato['id']} excluído com sucesso!")
                self.render()

        f_botoes = ctk.CTkFrame(card_concluidos, fg_color="transparent")
        f_botoes.pack(fill="x", padx=15, pady=(5, 15))

        btn_editar = ctk.CTkButton(
            f_botoes,
            text="Editar Contrato",
            command=editar_concluido,
            height=36,
            **tema.BOTAO_SECUNDARIO,
        )
        btn_editar.pack(side="right")

        btn_excluir = ctk.CTkButton(
            f_botoes,
            text="Excluir Contrato",
            command=excluir_concluido,
            height=36,
            **tema.BOTAO_PERIGO,
        )
        btn_excluir.pack(side="right", padx=(0, 10))

    def _criar_tabela(self, parent, df):
        """Cria uma tabela de contratos preenchida com as linhas do DataFrame."""
        cols = ("ID", "Cliente", "CPF/CNPJ", "Itens", "Início", "Devolução", "Total (R$)", "Status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=6)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=90)

        tree.column("ID", width=40)
        tree.column("Cliente", anchor="w", width=150)
        tree.column("Itens", anchor="w", width=170)

        for _, r in df.iterrows():
            tree.insert("", "end", values=(
                r['id'], r['cliente_nome'], r['cliente_cpf'], r['itens'], r['data_inicio'], r['data_devolucao'], f"R$ {r['valor_total']:.2f}", r['status']
            ))

        tree.pack(fill="x")
        return tree

    def abrir_modal_edicao(self, contrato):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Editar Contrato #{contrato['id']}")
        modal.geometry("460x600")
        modal.grab_set()
        modal.resizable(False, False)

        ctk.CTkLabel(
            modal,
            text=f"Contrato #{contrato['id']}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            modal,
            text=f"Itens: {contrato['itens'] or '-'}",
            font=ctk.CTkFont(size=12),
            text_color=tema.TEXTO_SEC,
            wraplength=400
        ).pack(padx=30, pady=(0, 10))

        def criar_campo(rotulo, valor):
            ctk.CTkLabel(modal, text=rotulo, anchor="w").pack(fill="x", padx=30, pady=(5, 0))
            entry = ctk.CTkEntry(modal)
            entry.insert(0, valor)
            entry.pack(fill="x", padx=30, pady=(0, 5))
            return entry

        entry_cpf = criar_campo("CPF / CNPJ:", contrato['cliente_cpf'])
        entry_nome = criar_campo("Nome do Cliente:", contrato['cliente_nome'])
        entry_end = criar_campo("Endereço Completo:", contrato['cliente_endereco'])

        f_periodo = ctk.CTkFrame(modal, fg_color="transparent")
        f_periodo.pack(fill="x", padx=30, pady=5)

        f_ini = ctk.CTkFrame(f_periodo, fg_color="transparent")
        f_ini.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(f_ini, text="Data Início:").pack(anchor="w")
        cal_ini = DateEntry(f_ini, width=12, **ESTILO_CALENDARIO)
        cal_ini.set_date(date.fromisoformat(contrato['data_inicio']))
        cal_ini.pack()

        f_fim = ctk.CTkFrame(f_periodo, fg_color="transparent")
        f_fim.grid(row=0, column=1, padx=15, sticky="w")
        ctk.CTkLabel(f_fim, text="Data Devolução:").pack(anchor="w")
        cal_fim = DateEntry(f_fim, width=12, **ESTILO_CALENDARIO)
        cal_fim.set_date(date.fromisoformat(contrato['data_devolucao']))
        cal_fim.pack()

        f_hora = ctk.CTkFrame(f_periodo, fg_color="transparent")
        f_hora.grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(f_hora, text="Horário:").pack(anchor="w")
        combo_hora = ctk.CTkOptionMenu(f_hora, values=HORARIOS, width=90)
        combo_hora.set(contrato['horario'])
        combo_hora.pack()

        entry_valor = criar_campo("Valor Total (R$):", f"{contrato['valor_total']:.2f}".replace(".", ","))

        def salvar():
            cpf, nome, endereco = entry_cpf.get().strip(), entry_nome.get().strip(), entry_end.get().strip()
            d_ini, d_fim = cal_ini.get_date(), cal_fim.get_date()

            if not (cpf and nome and endereco):
                messagebox.showerror("Erro", "Preencha todos os campos do cliente.", parent=modal)
                return

            if d_fim < d_ini:
                messagebox.showerror("Erro", "A data de devolução não pode ser anterior à data de início.", parent=modal)
                return

            try:
                valor = converter_valor(entry_valor.get())
            except ValueError:
                messagebox.showerror("Erro", "Insira um valor numérico válido para o total.", parent=modal)
                return

            atualizar_aluguel(contrato['id'], cpf, nome, endereco, d_ini.isoformat(), d_fim.isoformat(), combo_hora.get(), valor)
            messagebox.showinfo("Sucesso", "Contrato atualizado com sucesso!", parent=modal)
            modal.destroy()
            self.render()

        ctk.CTkButton(
            modal,
            text="Salvar Alterações",
            **tema.BOTAO_PRIMARIO,
            height=36,
            command=salvar
        ).pack(fill="x", padx=30, pady=15)
