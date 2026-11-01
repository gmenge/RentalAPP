import customtkinter as ctk
from tkinter import ttk

FUNDO = "#09090B"
SUPERFICIE = "#18181B"
BORDA = "#27272A"
BORDA_FORTE = "#3F3F46"
TEXTO = "#FAFAFA"
TEXTO_SEC = "#A1A1AA"
TEXTO_FRACO = "#71717A"

# Único tom fora da escala de cinza: só para o que exige atenção
ALERTA = "#F87171"
ALERTA_HOVER = "#7F1D1D"

# Uma ação principal por tela; todas as outras usam o botão secundário
BOTAO_PRIMARIO = {
    "fg_color": TEXTO,
    "hover_color": "#D4D4D8",
    "text_color": FUNDO,
    "text_color_disabled": TEXTO_FRACO,
}
BOTAO_SECUNDARIO = {
    "fg_color": "transparent",
    "hover_color": BORDA,
    "text_color": TEXTO,
    "border_width": 1,
    "border_color": BORDA_FORTE,
}
BOTAO_PERIGO = {**BOTAO_SECUNDARIO, "hover_color": ALERTA_HOVER}


def configurar_ctk():
    """Troca as cores padrão do CustomTkinter. Deve rodar antes de criar widgets."""
    tema = ctk.ThemeManager.theme

    tema["CTk"]["fg_color"] = [FUNDO, FUNDO]
    tema["CTkToplevel"]["fg_color"] = [SUPERFICIE, SUPERFICIE]
    tema["CTkButton"].update({
        "fg_color": [BORDA, BORDA],
        "hover_color": [BORDA_FORTE, BORDA_FORTE],
        "text_color": [TEXTO, TEXTO],
    })
    tema["CTkEntry"].update({
        "border_width": 1,
        "fg_color": [FUNDO, FUNDO],
        "border_color": [BORDA_FORTE, BORDA_FORTE],
        "text_color": [TEXTO, TEXTO],
        "placeholder_text_color": [TEXTO_FRACO, TEXTO_FRACO],
    })
    tema["CTkComboBox"].update({
        "border_width": 1,
        "fg_color": [FUNDO, FUNDO],
        "border_color": [BORDA_FORTE, BORDA_FORTE],
        "button_color": [BORDA_FORTE, BORDA_FORTE],
        "button_hover_color": [TEXTO_FRACO, TEXTO_FRACO],
        "text_color": [TEXTO, TEXTO],
    })
    tema["CTkOptionMenu"].update({
        "fg_color": [BORDA, BORDA],
        "button_color": [BORDA, BORDA],
        "button_hover_color": [BORDA_FORTE, BORDA_FORTE],
        "text_color": [TEXTO, TEXTO],
    })
    tema["DropdownMenu"].update({
        "fg_color": [SUPERFICIE, SUPERFICIE],
        "hover_color": [BORDA, BORDA],
        "text_color": [TEXTO, TEXTO],
    })
    tema["CTkScrollbar"].update({
        "button_color": [BORDA_FORTE, BORDA_FORTE],
        "button_hover_color": [TEXTO_FRACO, TEXTO_FRACO],
    })


def configurar_ttk():
    """Estiliza os widgets ttk (tabelas, barras de rolagem e campos de data)."""
    style = ttk.Style()

    # Tenta aplicar o tema 'clamp'. Se falhar no binário empacotado, usa 'default'
    try:
        style.theme_use("clamp")
    except Exception:
        style.theme_use("default")

    style.configure(
        "Treeview",
        background=SUPERFICIE,
        foreground=TEXTO,
        fieldbackground=SUPERFICIE,
        borderwidth=0,
        rowheight=38,
        font=("Segoe UI", 10)
    )
    style.configure(
        "Treeview.Heading",
        background=SUPERFICIE,
        foreground=TEXTO_FRACO,
        relief="flat",
        font=("Segoe UI", 10)
    )
    style.map(
        "Treeview",
        background=[("selected", BORDA_FORTE)],
        foreground=[("selected", TEXTO)]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", SUPERFICIE)],
        foreground=[("active", TEXTO_SEC)]
    )

    # Barra de rolagem fina, sem setas
    style.layout("Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
        ]})
    ])
    style.configure(
        "Vertical.TScrollbar",
        background=BORDA_FORTE,
        troughcolor=SUPERFICIE,
        bordercolor=SUPERFICIE,
        lightcolor=BORDA_FORTE,
        darkcolor=BORDA_FORTE,
        relief="flat",
        width=8
    )
    style.map("Vertical.TScrollbar", background=[("active", TEXTO_FRACO)])

    # O DateEntry copia o estilo do TCombobox ao ser criado
    style.configure(
        "TCombobox",
        fieldbackground=FUNDO,
        background=BORDA,
        foreground=TEXTO,
        arrowcolor=TEXTO_SEC,
        bordercolor=BORDA_FORTE,
        lightcolor=FUNDO,
        darkcolor=FUNDO,
        insertcolor=TEXTO,
        selectbackground=BORDA_FORTE,
        selectforeground=TEXTO,
        padding=6
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", FUNDO), ("disabled", SUPERFICIE)],
        background=[("active", BORDA_FORTE)],
        arrowcolor=[("active", TEXTO)]
    )
