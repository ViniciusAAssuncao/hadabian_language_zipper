import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import threading
import time

from ui.lexicon import LexiconTab
from ui.profile import ProfileTab
from ui.spinner import LoadingOverlay


class ConHabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ConHab")
        self.root.geometry("900x750")
        self.root.minsize(800, 600)

        self.colors = {
            "bg_main": "#1e1e1e",
            "bg_sec": "#252526",
            "fg_primary": "#e0e0e0",
            "fg_secondary": "#aaaaaa",
            "text": "#000000",
            "accent": "#007acc",
            "accent_hover": "#0098ff",
            "input_bg": "#2d2d2d",
            "success": "#4ec9b0",
            "error": "#f44747"
        }

        self.engine = None
        self.setup_styles()
        self.setup_ui()

        self.loading_overlay = LoadingOverlay(self.root, self.colors)

        self.load_conlangs()

    def setup_styles(self):
        self.root.configure(bg=self.colors["bg_main"])
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            ".", background=self.colors["bg_main"], foreground=self.colors["fg_primary"], font=("Segoe UI", 10))
        style.configure("TFrame", background=self.colors["bg_main"])
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"),
                        foreground=self.colors["fg_primary"], background=self.colors["bg_sec"], padding=15)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"),
                        foreground=self.colors["fg_secondary"], background=self.colors["bg_main"], padding=(0, 10, 0, 5))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"),
                        background=self.colors["accent"], foreground="white", borderwidth=0, focuscolor=self.colors["bg_main"], padding=(20, 10))
        style.map("Accent.TButton", background=[
                  ("active", self.colors["accent_hover"])], relief=[("pressed", "flat")])
        style.configure("Secondary.TButton", font=("Segoe UI", 9), background=self.colors["bg_sec"], foreground=self.colors[
                        "fg_primary"], borderwidth=1, bordercolor=self.colors["input_bg"], focuscolor=self.colors["bg_sec"], padding=(10, 5))
        style.map("Secondary.TButton", background=[
                  ("active", self.colors["input_bg"])])
        style.configure("TCombobox", fieldbackground=self.colors["input_bg"], background=self.colors["bg_sec"],
                        foreground=self.colors["fg_primary"], arrowcolor=self.colors["fg_primary"], bordercolor=self.colors["bg_main"], padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", self.colors["input_bg"])], selectbackground=[
                  ("readonly", self.colors["input_bg"])], selectforeground=[("readonly", self.colors["fg_primary"])])
        style.configure("Horizontal.TProgressbar", troughcolor=self.colors["input_bg"], background=self.colors["accent"],
                        bordercolor=self.colors["bg_main"], lightcolor=self.colors["accent"], darkcolor=self.colors["accent"])
        style.configure(
            "TNotebook", background=self.colors["bg_main"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["bg_sec"], foreground=self.colors["fg_secondary"], padding=(
            15, 5), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", self.colors["accent"]), ("active", self.colors["input_bg"])], foreground=[
                  ("selected", "white"), ("active", self.colors["fg_primary"])])
        style.configure("Treeview", background=self.colors["input_bg"], fieldbackground=self.colors[
                        "input_bg"], foreground=self.colors["fg_primary"], borderwidth=0, rowheight=25)
        style.configure("Treeview.Heading", background=self.colors["bg_sec"], foreground=self.colors["fg_primary"], relief="flat", font=(
            "Segoe UI", 10, "bold"))
        style.map("Treeview.Heading", background=[
                  ("active", self.colors["bg_sec"])])

    def setup_ui(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X)
        header_bg = tk.Frame(header_frame, bg=self.colors["bg_sec"], height=60)
        header_bg.pack(fill=tk.BOTH, expand=True)
        header_bg.pack_propagate(False)
        ttk.Label(header_bg, text="ConHab",
                  style="Header.TLabel").pack(side=tk.LEFT, padx=20)

        main_container = ttk.Frame(self.root, padding=30)
        main_container.pack(fill=tk.BOTH, expand=True)

        config_frame = ttk.Frame(main_container)
        config_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(config_frame, text="PERFIL LINGUÍSTICO",
                  style="SubHeader.TLabel").pack(anchor="w")

        controls_row = ttk.Frame(config_frame)
        controls_row.pack(fill=tk.X, pady=5)

        self.cl_selector = ttk.Combobox(
            controls_row, state="readonly", width=40, font=("Segoe UI", 10))
        self.cl_selector.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        self.cl_selector.bind("<<ComboboxSelected>>", self.on_profile_selected)

        ttk.Button(controls_row, text="↻ Recarregar Perfis",
                   style="Secondary.TButton", command=self.load_conlangs).pack(side=tk.LEFT)

        self.status_lbl = ttk.Label(
            controls_row, text="", foreground=self.colors["fg_secondary"])
        self.status_lbl.pack(side=tk.LEFT, padx=20)

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_translation = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_translation, text="Tradução")
        self.setup_translation_tab()

        self.lexicon_widget = LexiconTab(self.notebook, self.colors)
        self.notebook.add(self.lexicon_widget, text="Léxico")

        self.profile_widget = ProfileTab(self.notebook, self.colors)
        self.notebook.add(self.profile_widget, text="Editor JSON")

    def setup_translation_tab(self):
        content_pane = ttk.PanedWindow(
            self.tab_translation, orient=tk.VERTICAL)
        content_pane.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.Frame(content_pane)
        content_pane.add(input_frame, weight=1)
        ttk.Label(input_frame, text="ENTRADA (Linguagem Natural)",
                  style="SubHeader.TLabel").pack(anchor="w")

        self.ln_input = self.create_styled_text(input_frame, height=8)
        self.ln_input.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        action_frame = ttk.Frame(input_frame)
        action_frame.pack(fill=tk.X, pady=(0, 15))

        self.btn_process = ttk.Button(action_frame, text="PROCESSAR CONVERSÃO",
                                      style="Accent.TButton", cursor="hand2", command=self.process_language)
        self.btn_process.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(
            action_frame, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X,
                               expand=True, padx=(20, 0))

        output_frame = ttk.Frame(content_pane)
        content_pane.add(output_frame, weight=1)
        ttk.Label(output_frame, text="SAÍDA (Conlang)",
                  style="SubHeader.TLabel").pack(anchor="w")

        self.cl_output = self.create_styled_text(output_frame, height=8)
        self.cl_output.pack(fill=tk.BOTH, expand=True)

    def create_styled_text(self, parent, height):
        return scrolledtext.ScrolledText(
            parent, height=height, wrap=tk.WORD,
            bg=self.colors["input_bg"], fg=self.colors["fg_primary"],
            insertbackground=self.colors["accent"], font=("Consolas", 11),
            borderwidth=0, highlightthickness=1,
            highlightbackground=self.colors["bg_sec"], highlightcolor=self.colors["accent"]
        )

    def load_conlangs(self):
        path = Path("./conlangs")
        path.mkdir(exist_ok=True)
        files = sorted([f.name for f in path.glob("*.json")])
        self.cl_selector['values'] = files
        if files:
            current = self.cl_selector.get()
            if not current or current not in files:
                self.cl_selector.current(0)
                self.on_profile_selected(None)
        else:
            self.status_lbl.config(
                text="Nenhum perfil encontrado.", foreground=self.colors["error"])

    def on_profile_selected(self, event):
        selection = self.cl_selector.get()
        if selection:
            self.loading_overlay.show("Carregando e indexando vocabulário...")

            profile_path = Path("./conlangs") / selection
            self.profile_widget.load_profile(profile_path)

            thread = threading.Thread(
                target=self._async_load_engine, args=(selection,))
            thread.daemon = True
            thread.start()

    def _async_load_engine(self, selection):
        try:
            from engine import OriginalLanguageEngine
            profile_path = Path("./conlangs") / selection

            new_engine = OriginalLanguageEngine(profile_path)
            stats = new_engine.get_statistics()

            self.root.after(
                0, lambda: self._on_engine_loaded(new_engine, stats))
        except Exception as e:
            self.root.after(0, lambda: self._on_load_error(e))

    def _on_engine_loaded(self, engine, stats):
        self.engine = engine
        self.status_lbl.config(
            text=f"Carregado: {stats.get('profile_id')} | Vocabulário: {stats.get('cached_words')} palavras",
            foreground=self.colors["success"]
        )
        self.lexicon_widget.refresh(self.engine)
        self.loading_overlay.hide()

    def _on_load_error(self, error):
        self.loading_overlay.hide()
        self.status_lbl.config(
            text="Erro ao carregar perfil", foreground=self.colors["error"])
        messagebox.showerror(
            "Erro Crítico", f"Falha ao inicializar motor: {str(error)}")

    def process_language(self):
        if not self.engine:
            messagebox.showwarning(
                "Aviso", "Selecione um perfil de linguagem primeiro.")
            return

        text = self.ln_input.get("1.0", tk.END).strip()
        if not text:
            return

        self.btn_process['state'] = 'disabled'
        self.cl_output.delete("1.0", tk.END)
        self.cl_output.insert("1.0", "Processando...")

        self.progress_var = tk.IntVar()
        self.progress_bar['variable'] = self.progress_var
        self.progress_bar['maximum'] = 100
        self.progress_var.set(0)

        thread = threading.Thread(target=self._process_async, args=(text,))
        thread.daemon = True
        thread.start()

    def _process_async(self, text):
        try:
            sentences = self._split_into_sentences(text)
            results = []
            total = len(sentences)
            update_interval = max(1, total // 20)

            for i, sentence in enumerate(sentences):
                result = self.engine.process_text(sentence)
                results.append(result)

                if (i + 1) % update_interval == 0 or i == total - 1:
                    progress = int((i + 1) / total * 100)
                    self.root.after(
                        0, lambda p=progress: self.progress_var.set(p))

            final_result = ' '.join(results)
            self.root.after(0, lambda: self._on_processing_done(final_result))

        except Exception as e:
            self.root.after(0, lambda: self._on_processing_error(e))

    def _on_processing_done(self, result):
        self.cl_output.delete("1.0", tk.END)
        self.cl_output.insert("1.0", result)
        self.btn_process['state'] = 'normal'
        self.progress_var.set(100)
        self.lexicon_widget.refresh(self.engine)

    def _on_processing_error(self, error):
        self.cl_output.delete("1.0", tk.END)
        messagebox.showerror(
            "Erro de Processamento", f"Ocorreu uma falha durante a conversão: {str(error)}")
        self.btn_process['state'] = 'normal'
        self.progress_var.set(0)

    def _split_into_sentences(self, text):
        import re
        sentence_endings = r'[.!?]+(?:\s+|$)'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]


if __name__ == "__main__":
    root = tk.Tk()
    app = ConHabApp(root)
    root.mainloop()
