# RentalAPP/views/novo_aluguel.py

import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry

from views import tema
from views.base_frame import BaseFrame, ESTILO_CALENDARIO, HORARIOS
from views.seletor import SeletorBusca
from database import get_equipamentos_com_disponibilidade, registrar_aluguel, EstoqueInsuficienteError

class NovoAluguelView(BaseFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, titulo="Novo Contrato de Aluguel")
        self.render()

    def render(self):
        self.clear_view()
        self.render_header()

        if get_equipamentos_com_disponibilidade().empty:
            ctk.CTkLabel(
                self,
                text="Nenhum equipamento cadastrado. Cadastre um equipamento para criar contratos.",
                font=ctk.CTkFont(size=14),
                text_color=tema.TEXTO_FRACO
            ).pack(pady=50)
            return

        frame_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        frame_scroll.pack(fill="both", expand=True)

        # 1. DADOS DO CLIENTE
        card_cli = ctk.CTkFrame(frame_scroll, fg_color=tema.SUPERFICIE, corner_radius=8, border_width=1, border_color=tema.BORDA)
        card_cli.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_cli,
            text="1. Dados do Cliente",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=tema.TEXTO
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_cli = ctk.CTkFrame(card_cli, fg_color="transparent")
        f_cli.pack(fill="x", padx=15, pady=(0, 15))
        f_cli.grid_columnconfigure(0, weight=1)
        f_cli.grid_columnconfigure(1, weight=1)

        f_cpf = ctk.CTkFrame(f_cli, fg_color="transparent")
        f_cpf.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_cpf, text="CPF / CNPJ:", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))
        entry_cpf = ctk.CTkEntry(f_cpf, height=38)
        entry_cpf.pack(fill="x")

        f_nome = ctk.CTkFrame(f_cli, fg_color="transparent")
        f_nome.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_nome, text="Nome do Cliente:", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))
        entry_nome_cli = ctk.CTkEntry(f_nome, height=38)
        entry_nome_cli.pack(fill="x")

        f_end = ctk.CTkFrame(f_cli, fg_color="transparent")
        f_end.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_end, text="Endereço Completo:", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))
        entry_end = ctk.CTkEntry(f_end, height=38)
        entry_end.pack(fill="x")

        # 2. PERÍODO DA LOCAÇÃO
        card_dates = ctk.CTkFrame(frame_scroll, fg_color=tema.SUPERFICIE, corner_radius=8, border_width=1, border_color=tema.BORDA)
        card_dates.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_dates,
            text="2. Período da Locação",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=tema.TEXTO
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_dates = ctk.CTkFrame(card_dates, fg_color="transparent")
        f_dates.pack(fill="x", padx=15, pady=(0, 15))

        f_dt_ini = ctk.CTkFrame(f_dates, fg_color="transparent")
        f_dt_ini.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(f_dt_ini, text="Data Início:", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))
        cal_dt_ini = DateEntry(f_dt_ini, width=14, **ESTILO_CALENDARIO)
        cal_dt_ini.pack()

        f_dt_fim = ctk.CTkFrame(f_dates, fg_color="transparent")
        f_dt_fim.grid(row=0, column=1, padx=25, pady=5, sticky="w")
        ctk.CTkLabel(f_dt_fim, text="Data Devolução:", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))
        cal_dt_fim = DateEntry(f_dt_fim, width=14, **ESTILO_CALENDARIO)
        cal_dt_fim.pack()

        cal_dt_ini.bind("<Button-1>", lambda e: cal_dt_ini.drop_down())
        cal_dt_fim.bind("<Button-1>", lambda e: cal_dt_fim.drop_down())

        f_hora = ctk.CTkFrame(f_dates, fg_color="transparent")
        f_hora.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(f_hora, text="Horário:", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))
        combo_hora = ctk.CTkOptionMenu(f_hora, values=HORARIOS, width=120, height=32)
        combo_hora.set("08:00")
        combo_hora.pack()

        # 3. ITENS DO CONTRATO
        card_item = ctk.CTkFrame(frame_scroll, fg_color=tema.SUPERFICIE, corner_radius=8, border_width=1, border_color=tema.BORDA)
        card_item.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            card_item,
            text="3. Itens do Contrato",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=tema.TEXTO
        ).pack(anchor="w", padx=20, pady=(15, 10))

        f_item = ctk.CTkFrame(card_item, fg_color="transparent")
        f_item.pack(fill="x", padx=15, pady=(0, 10))
        f_item.grid_columnconfigure(0, weight=1)

        f_eq = ctk.CTkFrame(f_item, fg_color="transparent")
        f_eq.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f_eq, text="Equipamento (Selecione ou Digite):", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))

        combo_eq = SeletorBusca(f_eq, height=38)
        combo_eq.pack(fill="x")

        f_qtd = ctk.CTkFrame(f_item, fg_color="transparent")
        f_qtd.grid(row=0, column=1, padx=15, pady=5, sticky="w")
        ctk.CTkLabel(f_qtd, text="Quantidade:", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).pack(anchor="w", pady=(0, 2))
        combo_qtd = ctk.CTkOptionMenu(f_qtd, values=["1"], width=100, height=38)
        combo_qtd.pack()

        f_carrinho = ctk.CTkFrame(card_item, fg_color="transparent")

        lbl_total = ctk.CTkLabel(card_item, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color=tema.TEXTO)
        lbl_total.pack(anchor="e", padx=20, pady=(5, 15))

        estoque = {}
        carrinho = []
        lista_equipamentos = []

        def calcular_dias():
            dias = (cal_dt_fim.get_date() - cal_dt_ini.get_date()).days
            return dias if dias > 0 else 1

        def qtd_restante(eq_id):
            no_carrinho = sum(item['qtd_alugada'] for item in carrinho if item['id'] == eq_id)
            return estoque[eq_id]['qtd_disponivel'] - no_carrinho

        def buscar_opcao(texto):
            if texto in lista_equipamentos:
                return texto
            match = combo_eq.buscar(texto)
            return match[0] if match and texto.strip() else None

        def atualizar_qtd_disponivel(texto_selecionado):
            item_ref = buscar_opcao(texto_selecionado)
            if not item_ref:
                combo_qtd.configure(values=["1"])
                combo_qtd.set("1")
                return

            eq_id = int(item_ref.split(" - ")[0])
            novas_qtds = [str(i) for i in range(1, qtd_restante(eq_id) + 1)]
            combo_qtd.configure(values=novas_qtds)
            combo_qtd.set(novas_qtds[0])

        def atualizar_opcoes():
            opcoes = []
            for eq_id, dados in estoque.items():
                if qtd_restante(eq_id) > 0:
                    patrimonio = f" [Pat. {dados['patrimonio']}]" if dados['patrimonio'] else ""
                    rotulo = f"{eq_id} - {dados['nome']}{patrimonio} (Disp: {qtd_restante(eq_id)})"
                    busca = f"{eq_id} {dados['nome']} {dados['marca']} {dados['categoria']} {dados['patrimonio']}"
                    opcoes.append((rotulo, dados['nome'], busca))

            lista_equipamentos[:] = [opcao[0] for opcao in opcoes]
            combo_eq.set_opcoes(opcoes)
            combo_eq.set(lista_equipamentos[0] if lista_equipamentos else "Nenhum disponível nesse período")
            atualizar_qtd_disponivel(combo_eq.get())

        def desenhar_carrinho():
            for widget in f_carrinho.winfo_children():
                widget.destroy()

            dias = calcular_dias()
            total = 0.0
            for item in carrinho:
                diaria = estoque[item['id']]['diaria']
                subtotal = item['qtd_alugada'] * diaria * dias
                total += subtotal

                f_linha = ctk.CTkFrame(f_carrinho, fg_color=tema.BORDA, corner_radius=6)
                f_linha.pack(fill="x", pady=2)
                f_linha.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(f_linha, text=f"{item['qtd_alugada']}x {item['nome']}", font=ctk.CTkFont(size=12), text_color=tema.TEXTO).grid(row=0, column=0, padx=10, pady=4, sticky="w")
                ctk.CTkLabel(f_linha, text=f"R$ {diaria:.2f} / dia", font=ctk.CTkFont(size=12), text_color=tema.TEXTO_SEC).grid(row=0, column=1, padx=10, pady=4)
                ctk.CTkLabel(f_linha, text=f"R$ {subtotal:.2f}", font=ctk.CTkFont(size=12), text_color=tema.TEXTO).grid(row=0, column=2, padx=10, pady=4)
                ctk.CTkButton(
                    f_linha,
                    text="✕",
                    width=30,
                    height=26,
                    fg_color="transparent",
                    hover_color=tema.BORDA_FORTE,
                    command=lambda i=item: remover_item(i)
                ).grid(row=0, column=3, padx=5, pady=4)

            # Vazio, o frame manteria a altura padrão e abriria um buraco no card
            if carrinho:
                f_carrinho.pack(fill="x", padx=20, before=lbl_total)
                lbl_total.configure(text=f"Total ({dias} diária{'s' if dias > 1 else ''}): R$ {total:.2f}")
            else:
                f_carrinho.pack_forget()
                lbl_total.configure(text="Nenhum item adicionado.")

        def mudar_periodo(event=None):
            d_ini, d_fim = cal_dt_ini.get_date(), cal_dt_fim.get_date()
            if d_fim < d_ini:
                cal_dt_fim.set_date(d_ini)
                d_fim = d_ini

            df = get_equipamentos_com_disponibilidade(d_ini.isoformat(), d_fim.isoformat())
            estoque.clear()
            estoque.update({int(r['id']): r for r in df.to_dict("records")})

            removidos = []
            for item in list(carrinho):
                if item['qtd_alugada'] > estoque[item['id']]['qtd_disponivel']:
                    carrinho.remove(item)
                    removidos.append(item['nome'])

            atualizar_opcoes()
            desenhar_carrinho()

            if removidos:
                messagebox.showwarning("Aviso", f"Sem estoque nesse período, removido do contrato:\n{', '.join(removidos)}")

        def adicionar_item():
            item_ref = buscar_opcao(combo_eq.get())
            if not item_ref:
                messagebox.showerror("Erro", "Selecione um equipamento disponível.")
                return

            eq_id = int(item_ref.split(" - ")[0])
            qtd = int(combo_qtd.get())
            existente = next((item for item in carrinho if item['id'] == eq_id), None)
            if existente:
                existente['qtd_alugada'] += qtd
            else:
                carrinho.append({"id": eq_id, "nome": estoque[eq_id]['nome'], "qtd_alugada": qtd})

            atualizar_opcoes()
            desenhar_carrinho()

        def remover_item(item):
            carrinho.remove(item)
            atualizar_opcoes()
            desenhar_carrinho()

        btn_adicionar = ctk.CTkButton(
            f_item,
            text="Adicionar",
            width=110,
            height=36,
            **tema.BOTAO_SECUNDARIO,
            command=adicionar_item
        )
        btn_adicionar.grid(row=0, column=2, padx=(0, 5), pady=5, sticky="s")

        combo_eq.command = atualizar_qtd_disponivel

        cal_dt_ini.bind("<<DateEntrySelected>>", mudar_periodo)
        cal_dt_fim.bind("<<DateEntrySelected>>", mudar_periodo)
        mudar_periodo()

        entry_cpf.bind("<Return>", lambda e: entry_nome_cli.focus_set())
        entry_nome_cli.bind("<Return>", lambda e: entry_end.focus_set())
        entry_end.bind("<Return>", lambda e: cal_dt_ini.focus_set())

        def emitir_contrato():
            try:
                cpf, nome_c, end = entry_cpf.get().strip(), entry_nome_cli.get().strip(), entry_end.get().strip()
                d_ini, d_fim = cal_dt_ini.get_date(), cal_dt_fim.get_date()
                hora = combo_hora.get()

                if not (cpf and nome_c and end):
                    messagebox.showerror("Erro", "Preencha todos os campos do cliente.")
                    return

                if d_fim < d_ini:
                    messagebox.showerror("Erro", "A data de devolução não pode ser anterior à data de início.")
                    return

                if not carrinho:
                    messagebox.showerror("Erro", "Adicione pelo menos um item ao contrato.")
                    return

                dias = calcular_dias()
                itens = [
                    {**item, "subtotal": item['qtd_alugada'] * estoque[item['id']]['diaria'] * dias}
                    for item in carrinho
                ]
                total = sum(item['subtotal'] for item in itens)

                registrar_aluguel(cpf, nome_c, end, d_ini.isoformat(), d_fim.isoformat(), hora, itens, total)
                messagebox.showinfo("Sucesso", f"Contrato emitido com sucesso!\nValor Total: R$ {total:.2f}")

                self.controller.show_view("gestao_alugueis")

            except EstoqueInsuficienteError as e:
                messagebox.showerror("Erro", str(e))
                mudar_periodo()
            except ValueError:
                messagebox.showerror("Erro", "Verifique se as datas e quantidades foram inseridas corretamente.")

        btn_confirmar = ctk.CTkButton(
            frame_scroll,
            text="Emitir Contrato de Aluguel",
            command=emitir_contrato,
            width=220,
            height=36,
            **tema.BOTAO_PRIMARIO,
        )
        btn_confirmar.pack(anchor="e", pady=(5, 20))
