import sys
from pathlib import Path

# Adiciona a raiz do projeto e a pasta 'views' ao caminho de busca do Python
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

VIEWS_DIR = BASE_DIR / "views"
if str(VIEWS_DIR) not in sys.path:
    sys.path.insert(0, str(VIEWS_DIR))

import customtkinter as ctk
from database import init_db
from views import tema
from views.dashboard import DashboardView
from views.equipamentos import EquipamentosView
from views.novo_aluguel import NovoAluguelView
from views.gestao_alugueis import GestaoAlugueisView

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
tema.configurar_ctk()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LocaFácil — Sistema de Gestão de Aluguéis")
        self.geometry("1200x750")
        self.minsize(1040, 680)
        self.configure(fg_color=tema.FUNDO)

        init_db()
        tema.configurar_ttk()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ------------------- BARRA LATERAL (SIDEBAR) -------------------
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=tema.SUPERFICIE)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(25, 30), sticky="ew")

        self.logo_label = ctk.CTkLabel(
            self.logo_frame, 
            text="LocaFácil", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=tema.TEXTO
        )
        self.logo_label.pack(side="left")

        self.menu_buttons = {}
        nav_items = [
            ("dashboard", "Dashboard"),
            ("equipamentos", "Equipamentos"),
            ("novo_aluguel", "Novo Aluguel"),
            ("gestao_alugueis", "Gestão de Aluguéis")
        ]

        for idx, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",                     # Fixa todo o conteúdo à esquerda
                height=42,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="normal"),
                fg_color="transparent",
                text_color=tema.TEXTO_SEC,
                hover_color=tema.BORDA,
                command=lambda k=key: self.show_view(k)
            )
            btn.grid(row=idx, column=0, padx=12, pady=4, sticky="ew")
            self.menu_buttons[key] = btn

        self.lbl_version = ctk.CTkLabel(
            self.sidebar, 
            text="v2.0", 
            font=ctk.CTkFont(size=11),
            text_color=tema.TEXTO_FRACO
        )
        self.lbl_version.grid(row=6, column=0, pady=20)

        # ------------------- ÁREA PRINCIPAL -------------------
        self.main_container = ctk.CTkFrame(self, fg_color=tema.FUNDO, corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=15)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.views = {}
        self.init_views()
        self.show_view("dashboard")

    def init_views(self):
        views_dict = {
            "dashboard": DashboardView,
            "equipamentos": EquipamentosView,
            "novo_aluguel": NovoAluguelView,
            "gestao_alugueis": GestaoAlugueisView
        }
        for key, view_cls in views_dict.items():
            view_instance = view_cls(self.main_container, self)
            view_instance.grid(row=0, column=0, sticky="nsew")
            self.views[key] = view_instance

    def show_view(self, view_name):
        for key, btn in self.menu_buttons.items():
            if key == view_name:
                btn.configure(fg_color=tema.BORDA, text_color=tema.TEXTO)
            else:
                btn.configure(fg_color="transparent", text_color=tema.TEXTO_SEC)

        view = self.views.get(view_name)
        if view:
            if hasattr(view, 'render'):
                view.render()
            view.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()