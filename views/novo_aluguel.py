# RentalAPP/views/novo_aluguel.py

import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry

from views.base_frame import BaseFrame
from database import get_equipamentos_com_disponibilidade, registrar_aluguel

class NovoAluguelView(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, titulo="📝 Novo Contrato de Aluguel")
        self.render()

    def render(self):
        self.clear_view()
        self.render_header()

        df_equip = get_equipamentos_com_disponibilidade()
        if df_equip.empty or df_equip['qtd_disponivel'].sum() == 0:
            ctk.CTkLabel(
                self, 
                text="Não há equipamentos disponíveis no estoque no momento.",
                font=ctk.CTkFont(size=14),
                text_color="#71717A"
            ).pack(pady=50)
            return

        frame_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame_scroll.pack(fill="both", expand=True)

        # 1. DADOS DO CLIENTE
        card_cli = ctk.CTkFrame(frame_scroll, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        card_cli.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_cli, 
            text="1. Dados do Cliente", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FAFAFA"
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_cli = ctk.CTkFrame(card_cli, fg_color="transparent")
        f_cli.pack(fill="x", padx=15, pady=(0, 15))
        f_cli.grid_columnconfigure(0, weight=1)
        f_cli.grid_columnconfigure(1, weight=1)

        f_cpf = ctk.CTkFrame(f_cli, fg_color="transparent")
        f_cpf.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_cpf, text="CPF / CNPJ:", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        entry_cpf = ctk.CTkEntry(f_cpf, height=38, corner_radius=8, fg_color="#27272A", border_color="#3F3F46")
        entry_cpf.pack(fill="x")

        f_nome = ctk.CTkFrame(f_cli, fg_color="transparent")
        f_nome.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_nome, text="Nome do Cliente:", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        entry_nome_cli = ctk.CTkEntry(f_nome, height=38, corner_radius=8, fg_color="#27272A", border_color="#3F3F46")
        entry_nome_cli.pack(fill="x")

        f_end = ctk.CTkFrame(f_cli, fg_color="transparent")
        f_end.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_end, text="Endereço Completo:", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        entry_end = ctk.CTkEntry(f_end, height=38, corner_radius=8, fg_color="#27272A", border_color="#3F3F46")
        entry_end.pack(fill="x")

        # 2. PERÍODO DA LOCAÇÃO
        card_dates = ctk.CTkFrame(frame_scroll, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        card_dates.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_dates, 
            text="2. Período da Locação", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FAFAFA"
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_dates = ctk.CTkFrame(card_dates, fg_color="transparent")
        f_dates.pack(fill="x", padx=15, pady=(0, 15))

        estilo_cal = {
            "background": "#27272A",
            "foreground": "#FAFAFA",
            "headersbackground": "#18181B",
            "headersforeground": "#A1A1AA",
            "selectbackground": "#2563EB",
            "selectforeground": "#FFFFFF",
            "normalbackground": "#27272A",
            "normalforeground": "#FAFAFA",
            "weekendbackground": "#18181B",
            "weekendforeground": "#A1A1AA",
            "othermonthbackground": "#09090B",
            "othermonthwebackground": "#09090B",
            "date_pattern": "yyyy-mm-dd",
            "borderwidth": 0
        }

        f_dt_ini = ctk.CTkFrame(f_dates, fg_color="transparent")
        f_dt_ini.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(f_dt_ini, text="Data Início:", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        cal_dt_ini = DateEntry(f_dt_ini, width=14, **estilo_cal)
        cal_dt_ini.pack()

        f_dt_fim = ctk.CTkFrame(f_dates, fg_color="transparent")
        f_dt_fim.grid(row=0, column=1, padx=25, pady=5, sticky="w")
        ctk.CTkLabel(f_dt_fim, text="Data Devolução:", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        cal_dt_fim = DateEntry(f_dt_fim, width=14, **estilo_cal)
        cal_dt_fim.pack()

        cal_dt_ini.bind("<Button-1>", lambda e: cal_dt_ini.drop_down())
        cal_dt_fim.bind("<Button-1>", lambda e: cal_dt_fim.drop_down())

        f_hora = ctk.CTkFrame(f_dates, fg_color="transparent")
        f_hora.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(f_hora, text="Horário:", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        horas_opcoes = [f"{h:02d}:00" for h in range(7, 20)]
        combo_hora = ctk.CTkOptionMenu(f_hora, values=horas_opcoes, width=120, height=32, fg_color="#27272A", button_color="#3F3F46")
        combo_hora.set("08:00")
        combo_hora.pack()

        # 3. EQUIPAMENTO E QUANTIDADE
        card_item = ctk.CTkFrame(frame_scroll, fg_color="#18181B", corner_radius=12, border_width=1, border_color="#27272A")
        card_item.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_item, 
            text="3. Equipamento e Quantidade", 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FAFAFA"
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_item = ctk.CTkFrame(card_item, fg_color="transparent")
        f_item.pack(fill="x", padx=15, pady=(0, 15))
        f_item.grid_columnconfigure(0, weight=1)

        opcoes_eq = df_equip[df_equip['qtd_disponivel'] > 0]
        lista_equipamentos = [f"{r['id']} - {r['nome']} (Disp: {r['qtd_disponivel']})" for _, r in opcoes_eq.iterrows()]

        f_eq = ctk.CTkFrame(f_item, fg_color="transparent")
        f_eq.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_eq, text="Equipamento (Selecione ou Digite):", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        
        combo_eq = ctk.CTkComboBox(f_eq, values=lista_equipamentos, height=38, corner_radius=8, fg_color="#27272A", border_color="#3F3F46", button_color="#3F3F46")
        combo_eq.pack(fill="x")

        f_qtd = ctk.CTkFrame(f_item, fg_color="transparent")
        f_qtd.grid(row=0, column=1, padx=15, pady=5, sticky="w")
        ctk.CTkLabel(f_qtd, text="Quantidade:", font=ctk.CTkFont(size=12), text_color="#A1A1AA").pack(anchor="w", pady=(0, 2))
        combo_qtd = ctk.CTkOptionMenu(f_qtd, values=["1"], width=100, height=38, fg_color="#27272A", button_color="#3F3F46")
        combo_qtd.pack()

        def atualizar_qtd_disponivel(texto_selecionado):
            try:
                match = [item for item in lista_equipamentos if texto_selecionado.lower() in item.lower()]
                item_ref = match[0] if match else (lista_equipamentos[0] if lista_equipamentos else None)
                
                if item_ref:
                    eq_id = int(item_ref.split(" - ")[0])
                    qtd_disp = opcoes_eq[opcoes_eq['id'] == eq_id].iloc[0]['qtd_disponivel']
                    novas_qtds = [str(i) for i in range(1, qtd_disp + 1)]
                    combo_qtd.configure(values=novas_qtds)
                    combo_qtd.set(novas_qtds[0])
            except Exception:
                pass

        def on_key_release_eq(event):
            texto = combo_eq.get()
            matches = [item for item in lista_equipamentos if texto.lower() in item.lower()]
            if matches:
                combo_eq.configure(values=matches)
                atualizar_qtd_disponivel(matches[0])
            else:
                combo_eq.configure(values=lista_equipamentos)

        combo_eq.bind("<KeyRelease>", on_key_release_eq)
        combo_eq.configure(command=atualizar_qtd_disponivel)

        if lista_equipamentos:
            combo_eq.set(lista_equipamentos[0])
            atualizar_qtd_disponivel(lista_equipamentos[0])

        entry_cpf.bind("<Return>", lambda e: entry_nome_cli.focus_set())
        entry_nome_cli.bind("<Return>", lambda e: entry_end.focus_set())
        entry_end.bind("<Return>", lambda e: cal_dt_ini.focus_set())

        def emitir_contrato():
            try:
                cpf, nome_c, end = entry_cpf.get().strip(), entry_nome_cli.get().strip(), entry_end.get().strip()
                d_ini, d_fim = cal_dt_ini.get_date(), cal_dt_fim.get_date()
                hora, qtd = combo_hora.get(), int(combo_qtd.get())

                if not (cpf and nome_c and end):
                    messagebox.showerror("Erro", "Preencha todos os campos do cliente.")
                    return

                if d_fim < d_ini:
                    messagebox.showerror("Erro", "A data de devolução não pode ser anterior à data de início.")
                    return

                dias = (d_fim - d_ini).days
                dias = dias if dias > 0 else 1

                texto_eq = combo_eq.get()
                match = [item for item in lista_equipamentos if texto_eq.lower() in item.lower()]
                if not match:
                    messagebox.showerror("Erro", "Equipamento selecionado é inválido.")
                    return

                eq_id = int(match[0].split(" - ")[0])
                dados_eq = opcoes_eq[opcoes_eq['id'] == eq_id].iloc[0]

                subtotal = qtd * dados_eq['diaria'] * dias
                itens = [{"id": eq_id, "nome": dados_eq['nome'], "diaria": dados_eq['diaria'], "qtd_alugada": qtd, "subtotal": subtotal}]

                registrar_aluguel(cpf, nome_c, end, d_ini.isoformat(), d_fim.isoformat(), hora, itens, subtotal)
                messagebox.showinfo("Sucesso", f"Contrato emitido com sucesso!\nValor Total: R$ {subtotal:.2f}")
                
                self.controller.show_view("gestao_alugueis")

            except ValueError:
                messagebox.showerror("Erro", "Verifique se as datas e quantidades foram inseridas corretamente.")

        btn_confirmar = ctk.CTkButton(
            frame_scroll, 
            text="Emitir Contrato de Aluguel", 
            command=emitir_contrato, 
            height=44,
            corner_radius=8,
            fg_color="#2563EB", 
            hover_color="#1D4ED8",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn_confirmar.pack(pady=(5, 20), fill="x")