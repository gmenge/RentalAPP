import customtkinter as ctk

from views import tema

ESTILO_CALENDARIO = {
    "background": tema.BORDA,
    "foreground": tema.TEXTO,
    "headersbackground": tema.SUPERFICIE,
    "headersforeground": tema.TEXTO_SEC,
    "selectbackground": tema.BORDA_FORTE,
    "selectforeground": tema.TEXTO,
    "normalbackground": tema.BORDA,
    "normalforeground": tema.TEXTO,
    "weekendbackground": tema.SUPERFICIE,
    "weekendforeground": tema.TEXTO_SEC,
    "othermonthbackground": tema.FUNDO,
    "othermonthwebackground": tema.FUNDO,
    "date_pattern": "yyyy-mm-dd",
    "showweeknumbers": False,
    "borderwidth": 0
}

HORARIOS = [f"{h:02d}:00" for h in range(7, 20)]

class BaseFrame(ctk.CTkFrame):
    def __init__(self, parent, controller, titulo=""):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.titulo = titulo

    def clear_view(self):
        """Limpa todos os elementos filhos do frame antes de re-renderizar."""
        for widget in self.winfo_children():
            widget.destroy()

    def render_header(self):
        """Renderiza o cabeçalho padrão com título nas telas."""
        if self.titulo:
            header_frame = ctk.CTkFrame(self, fg_color="transparent")
            header_frame.pack(fill="x", pady=(0, 20))
            
            lbl_title = ctk.CTkLabel(
                header_frame, 
                text=self.titulo, 
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=tema.TEXTO
            )
            lbl_title.pack(anchor="w")