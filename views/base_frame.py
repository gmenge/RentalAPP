import customtkinter as ctk

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
                text_color="#FAFAFA"
            )
            lbl_title.pack(anchor="w")