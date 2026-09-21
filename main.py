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
from tkinter import ttk
from database import init_db
from views.dashboard import DashboardView
from views.equipamentos import EquipamentosView
from views.novo_aluguel import NovoAluguelView
from views.gestao_alugueis import GestaoAlugueisView

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def aplicar_estilo_tabelas():
    style = ttk.Style()
    
    # Tenta aplicar o tema 'clamp'. Se falhar no binário empacotado, usa 'default'
    try:
        style.theme_use("clamp")
    except Exception:
        style.theme_use("default")
    
    cor_fundo = "#18181B"
    cor_texto = "#F4F4F5"
    cor_cabecalho = "#09090B"
    cor_selecao = "#2563EB"

    style.configure(
        "Treeview",
        background=cor_fundo,
        foreground=cor_texto,
        fieldbackground=cor_fundo,
        borderwidth=0,
        rowheight=38,
        font=("Segoe UI", 10)
    )

    style.configure(
        "Treeview.Heading",
        background=cor_cabecalho,
        foreground="#A1A1AA",
        relief="flat",
        font=("Segoe UI", 10, "bold")
    )

    style.map(
        "Treeview",
        background=[("selected", cor_selecao)],
        foreground=[("selected", "#FFFFFF")]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#18181B")],
        foreground=[("active", "#FFFFFF")]
    )

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LocaFácil — Sistema de Gestão de Aluguéis")
        self.geometry("1200x750")
        self.minsize(1040, 680)
        self.configure(fg_color="#09090B")

        init_db()
        aplicar_estilo_tabelas()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ------------------- BARRA LATERAL (SIDEBAR) -------------------
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#18181B")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(25, 30), sticky="ew")

        self.logo_icon = ctk.CTkLabel(
            self.logo_frame, 
            text="⚡", 
            font=ctk.CTkFont(size=24)
        )
        self.logo_icon.pack(side="left", padx=(0, 10))

        self.logo_label = ctk.CTkLabel(
            self.logo_frame, 
            text="LocaFácil", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FAFAFA"
        )
        self.logo_label.pack(side="left")

        self.menu_buttons = {}
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("equipamentos", "🛠", "Equipamentos"),  # Limpado caractere invisível
            ("novo_aluguel", "📝", "Novo Aluguel"),
            ("gestao_alugueis", "📂", "Gestão de Aluguéis")
        ]

        for idx, (key, icon, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {label}",        # Espaçamento padronizado
                anchor="w",                     # Fixa todo o conteúdo à esquerda
                height=42,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="normal"),
                fg_color="transparent",
                text_color="#A1A1AA",
                hover_color="#27272A",
                command=lambda k=key: self.show_view(k)
            )
            btn.grid(row=idx, column=0, padx=12, pady=4, sticky="ew")
            self.menu_buttons[key] = btn

        self.lbl_version = ctk.CTkLabel(
            self.sidebar, 
            text="v2.0 • Pro Edition", 
            font=ctk.CTkFont(size=11),
            text_color="#52525B"
        )
        self.lbl_version.grid(row=6, column=0, pady=20)

        # ------------------- ÁREA PRINCIPAL -------------------
        self.main_container = ctk.CTkFrame(self, fg_color="#09090B", corner_radius=0)
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
                btn.configure(fg_color="#2563EB", text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#A1A1AA")

        view = self.views.get(view_name)
        if view:
            if hasattr(view, 'render'):
                view.render()
            view.tkraise()

if __name__ == "__main__":
    app = App()
    app.mainloop()