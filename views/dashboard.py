# RentalAPP/views/dashboard.py

import customtkinter as ctk
from views.base_frame import BaseFrame
from database import get_estatisticas_dashboard, get_alugueis_recentes

class DashboardView(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, titulo="📊 Dashboard General")
        self.render()

    def render(self):
        self.clear_view()
        self.render_header()

        dados = get_estatisticas_dashboard()

        # FRAME CARDS DE KPI
        frame_kpis = ctk.CTkFrame(self, fg_color="transparent")
        frame_kpis.pack(fill="x", pady=(0, 20))

        # Configurar 4 colunas iguais
        for i in range(4):
            frame_kpis.grid_columnconfigure(i, weight=1)

        self._criar_card_kpi(frame_kpis, 0, "Faturamento Total", f"R$ {dados['faturamento_total']:.2f}", "#10B981")
        self._criar_card_kpi(frame_kpis, 1, "Aluguéis Ativos", str(dados['alugueis_ativos']), "#2563EB")
        self._criar_card_kpi(frame_kpis, 2, "Aluguéis Atrasados", str(dados['alugueis_atrasados']), "#EF4444")
        self._criar_card_kpi(frame_kpis, 3, "Total Equipamentos", str(dados['total_equipamentos']), "#F59E0B")

        # TABELA DE ALUGUÉIS RECENTES
        lbl_secao = ctk.CTkLabel(
            self, 
            text="Últimas Locações Registradas", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FAFAFA"
        )
        lbl_secao.pack(anchor="w", pady=(10, 10))

        frame_tabela = ctk.CTkScrollableFrame(self, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        frame_tabela.pack(fill="both", expand=True)

        df_recentes = get_alugueis_recentes()

        if df_recentes.empty:
            ctk.CTkLabel(
                frame_tabela, 
                text="Nenhum aluguel registrado até o momento.",
                font=ctk.CTkFont(size=13),
                text_color="#71717A"
            ).pack(pady=30)
            return

        # Cabeçalho da Tabela
        headers = ["ID", "Cliente", "Data Início", "Data Devolução", "Valor Total", "Status"]
        frame_header = ctk.CTkFrame(frame_tabela, fg_color="#27272A", corner_radius=6)
        frame_header.pack(fill="x", padx=5, pady=5)

        for col_idx, header in enumerate(headers):
            frame_header.grid_columnconfigure(col_idx, weight=1)
            ctk.CTkLabel(
                frame_header, 
                text=header, 
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#A1A1AA"
            ).grid(row=0, column=col_idx, padx=10, pady=8, sticky="w")

        # Linhas da Tabela
        for _, row in df_recentes.iterrows():
            f_row = ctk.CTkFrame(frame_tabela, fg_color="transparent")
            f_row.pack(fill="x", padx=5, pady=2)

            for col_idx in range(len(headers)):
                f_row.grid_columnconfigure(col_idx, weight=1)

            ctk.CTkLabel(f_row, text=str(row['id']), font=ctk.CTkFont(size=12), text_color="#FAFAFA").grid(row=0, column=0, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(f_row, text=str(row['cliente_nome']), font=ctk.CTkFont(size=12), text_color="#FAFAFA").grid(row=0, column=1, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(f_row, text=str(row['data_inicio']), font=ctk.CTkFont(size=12), text_color="#A1A1AA").grid(row=0, column=2, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(f_row, text=str(row['data_devolucao']), font=ctk.CTkFont(size=12), text_color="#A1A1AA").grid(row=0, column=3, padx=10, pady=6, sticky="w")
            ctk.CTkLabel(f_row, text=f"R$ {row['valor_total']:.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FAFAFA").grid(row=0, column=4, padx=10, pady=6, sticky="w")

            # Cor do Badge de Status
            status = str(row['status'])
            cor_status = "#10B981" if status == "Ativo" else ("#EF4444" if status == "Atrasado" else "#6B7280")
            
            lbl_status = ctk.CTkLabel(
                f_row, 
                text=status, 
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=cor_status
            )
            lbl_status.grid(row=0, column=5, padx=10, pady=6, sticky="w")

    def _criar_card_kpi(self, parent, col, titulo, valor, cor_destaque):
        card = ctk.CTkFrame(parent, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        card.grid(row=0, column=col, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(
            card, 
            text=titulo, 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A1A1AA"
        ).pack(anchor="w", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            card, 
            text=valor, 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=cor_destaque
        ).pack(anchor="w", padx=15, pady=(0, 15))