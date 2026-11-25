import tkinter as tk
import unicodedata
from tkinter import ttk

import customtkinter as ctk

from views import tema

LINHAS_VISIVEIS = 8
TECLAS_SEM_TEXTO = {
    "Up", "Down", "Left", "Right", "Home", "End", "Return", "Escape", "Tab",
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
}


def normalizar(texto):
    """Prepara um texto para busca, ignorando maiúsculas e acentos."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return sem_acento.casefold().strip()


class SeletorBusca(ctk.CTkFrame):
    """Campo com lista suspensa que filtra enquanto se digita.

    Substitui o CTkComboBox, cuja lista é um menu nativo: não filtra ao digitar,
    não rola com o mouse e não abre ao clicar no texto.
    """

    aberto = None

    def __init__(self, parent, height=38, command=None):
        super().__init__(parent, fg_color="transparent")
        self.command = command
        self.opcoes = []
        self.visiveis = []
        self.popup = None
        self.lista = None

        self.entry = ctk.CTkEntry(self, height=height)
        self.entry.pack(side="left", fill="x", expand=True)

        self.botao = ctk.CTkButton(
            self, text="▼", font=ctk.CTkFont(size=10), width=height, height=height,
            **tema.BOTAO_SECUNDARIO, command=self.alternar
        )
        self.botao.pack(side="left", padx=(4, 0))

        self.entry.bind("<Button-1>", self._ao_clicar)
        self.entry.bind("<KeyRelease>", self._ao_digitar)
        self.entry.bind("<Down>", lambda e: self._mover(1))
        self.entry.bind("<Up>", lambda e: self._mover(-1))
        self.entry.bind("<Return>", self._ao_confirmar)
        self.entry.bind("<Escape>", lambda e: self.fechar())
        self.entry.bind("<FocusOut>", self._ao_perder_foco)
        self.entry.bind("<MouseWheel>", self._rolar)

        self._ligar_janela()

    def _ligar_janela(self):
        """Fecha a lista por eventos da janela. Liga uma vez só, pois as telas são recriadas."""
        janela = self.winfo_toplevel()
        if getattr(janela, "seletor_ligado", False):
            return
        janela.seletor_ligado = True

        def fora(event):
            seletor = SeletorBusca.aberto
            if seletor and not str(event.widget).startswith(str(seletor)):
                seletor.fechar()

        def janela_mudou(event):
            if event.widget is janela and SeletorBusca.aberto:
                SeletorBusca.aberto.fechar()

        janela.bind("<Button-1>", fora, add="+")
        janela.bind("<MouseWheel>", fora, add="+")
        janela.bind("<Configure>", janela_mudou, add="+")

    # -------------------------------------------------------------
    # VALOR E OPÇÕES
    # -------------------------------------------------------------
    def set_opcoes(self, opcoes):
        """Recebe uma lista de (rótulo, nome, texto de busca)."""
        self.opcoes = [(rotulo, normalizar(nome), normalizar(busca)) for rotulo, nome, busca in opcoes]

    def rotulos(self):
        return [opcao[0] for opcao in self.opcoes]

    def get(self):
        return self.entry.get()

    def set(self, texto):
        self.entry.delete(0, "end")
        self.entry.insert(0, texto)

    def buscar(self, texto):
        """Retorna os rótulos que combinam, começando pelos nomes iniciados pelo texto."""
        termo = normalizar(texto)
        if not termo:
            return self.rotulos()

        palavras = termo.split()
        achados = [opcao for opcao in self.opcoes if all(p in opcao[2] for p in palavras)]
        return [o[0] for o in achados if o[1].startswith(termo)] + [o[0] for o in achados if not o[1].startswith(termo)]

    # -------------------------------------------------------------
    # EVENTOS DO CAMPO
    # -------------------------------------------------------------
    def _ao_clicar(self, event=None):
        if self.popup:
            return
        self.abrir()
        # Selecionar tudo faz a primeira tecla substituir o texto atual
        self.after(1, lambda: self.entry.select_range(0, "end"))

    def _ao_digitar(self, event):
        if event.keysym in TECLAS_SEM_TEXTO:
            return

        self.visiveis = self.buscar(self.get())
        self._mostrar()
        if self.visiveis and self.command:
            self.command(self.visiveis[0])

    def _ao_confirmar(self, event=None):
        if self.popup and self.visiveis:
            self._escolher(self.lista.curselection()[0] if self.lista.curselection() else 0)
        return "break"

    def _ao_perder_foco(self, event=None):
        # O clique na lista também tira o foco do campo, então confere depois
        self.after(150, self._conferir_foco)

    def _conferir_foco(self):
        if not self.popup or not self.winfo_exists():
            return
        try:
            foco = self.focus_displayof()
        except KeyError:
            foco = None
        if foco not in (self.entry._entry, self.lista):
            self.fechar()

    def _rolar(self, event):
        if self.popup:
            self.lista.yview_scroll(-1 if event.delta > 0 else 1, "units")
            return "break"

    def _mover(self, passo):
        if not self.popup:
            self.abrir()
            return "break"

        if self.visiveis:
            atual = self.lista.curselection()
            indice = max(0, min(len(self.visiveis) - 1, (atual[0] if atual else -1) + passo))
            self._marcar(indice)
        return "break"

    # -------------------------------------------------------------
    # LISTA SUSPENSA
    # -------------------------------------------------------------
    def alternar(self):
        if self.popup:
            self.fechar()
        else:
            self.entry.focus_set()
            self.abrir()

    def abrir(self):
        self.visiveis = self.rotulos()
        self._mostrar()
        if self.get() in self.visiveis:
            self._marcar(self.visiveis.index(self.get()))

    def fechar(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.lista = None
        if SeletorBusca.aberto is self:
            SeletorBusca.aberto = None

    def destroy(self):
        self.fechar()
        super().destroy()

    def _criar_popup(self):
        if SeletorBusca.aberto:
            SeletorBusca.aberto.fechar()
        SeletorBusca.aberto = self

        # Filho da janela, não do campo: assim a roda do mouse não rola o formulário junto
        self.popup = tk.Toplevel(self.winfo_toplevel(), bg=tema.BORDA_FORTE)
        # Não usar transient aqui: junto com overrideredirect a janela fica invisível no Tk 8.6
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)

        moldura = tk.Frame(self.popup, bg=tema.SUPERFICIE)
        moldura.pack(fill="both", expand=True, padx=1, pady=1)

        self.barra = ttk.Scrollbar(moldura, orient="vertical")
        self.lista = tk.Listbox(
            moldura,
            bg=tema.SUPERFICIE,
            fg=tema.TEXTO,
            selectbackground=tema.BORDA_FORTE,
            selectforeground=tema.TEXTO,
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            exportselection=False,
            yscrollcommand=self.barra.set
        )
        self.barra.configure(command=self.lista.yview)
        self.lista.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)

        self.lista.bind("<Motion>", lambda e: self._marcar(self.lista.nearest(e.y), rolar=False))
        self.lista.bind("<ButtonRelease-1>", lambda e: self._escolher(self.lista.nearest(e.y)))

    def _mostrar(self):
        if not self.popup:
            self._criar_popup()

        self.lista.delete(0, "end")
        if self.visiveis:
            self.lista.configure(fg=tema.TEXTO)
            for rotulo in self.visiveis:
                self.lista.insert("end", rotulo)
            self._marcar(0)
        else:
            self.lista.configure(fg=tema.TEXTO_FRACO)
            self.lista.insert("end", "Nenhum equipamento encontrado")

        linhas = min(max(len(self.visiveis), 1), LINHAS_VISIVEIS)
        self.lista.configure(height=linhas)
        if len(self.visiveis) > LINHAS_VISIVEIS:
            self.barra.pack(side="right", fill="y", pady=4)
        else:
            self.barra.pack_forget()

        self.popup.update_idletasks()
        altura = self.popup.winfo_reqheight()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        if y + altura > self.winfo_screenheight():
            y = self.entry.winfo_rooty() - altura - 2
        self.popup.geometry(f"{self.winfo_width()}x{altura}+{x}+{y}")

    def _marcar(self, indice, rolar=True):
        if not self.visiveis:
            return
        self.lista.selection_clear(0, "end")
        self.lista.selection_set(indice)
        if rolar:
            self.lista.see(indice)

    def _escolher(self, indice):
        if not self.visiveis:
            return

        rotulo = self.visiveis[indice]
        self.set(rotulo)
        self.fechar()
        self.entry.focus_set()
        if self.command:
            self.command(rotulo)
