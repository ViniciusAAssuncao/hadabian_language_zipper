import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import threading
import json
import os

from ui.lexicon import LexiconTab
from ui.profile import ProfileTab
from ui.gramataki import GramatakiTab
from ui.spinner import LoadingOverlay


class ProfileSelectorDialog(tk.Toplevel):
    def __init__(self, parent, colors, on_select_callback):
        super().__init__(parent)
        self.colors = colors
        self.on_select_callback = on_select_callback
        self.selected_file = None
        self.profiles_data = []

        self.title("Biblioteca de Conlangs")
        self.geometry("800x600")
        self.configure(bg=self.colors["bg_main"])
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.load_profile_list()

        self.center_window()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(header_frame, text="Selecione um Perfil Linguístico",
                  style="Header.TLabel", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)

        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Buscar:", foreground=self.colors["fg_secondary"]).pack(
            side=tk.LEFT, padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     bg=self.colors["input_bg"], fg=self.colors["fg_primary"],
                                     insertbackground=self.colors["fg_primary"], relief="flat", borderwidth=5)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.focus_set()

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "id", "author", "filename")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Nome da Língua")
        self.tree.heading("id", text="ID")
        self.tree.heading("author", text="Autor")
        self.tree.heading("filename", text="Arquivo")

        self.tree.column("name", width=200, anchor="w")
        self.tree.column("id", width=100, anchor="center")
        self.tree.column("author", width=150, anchor="w")
        self.tree.column("filename", width=150, anchor="e")

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_double_click)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="Cancelar", style="Secondary.TButton",
                   command=self.destroy).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(btn_frame, text="Carregar Perfil Selecionado", style="Accent.TButton",
                   command=self.confirm_selection).pack(side=tk.RIGHT)

    def load_profile_list(self):
        path = Path("./conlangs")
        path.mkdir(exist_ok=True)
        files = sorted([f for f in path.glob("*.json")])

        self.profiles_data = []

        for file_path in files:
            meta = self._extract_metadata(file_path)
            self.profiles_data.append(meta)

        self.populate_tree(self.profiles_data)

    def _extract_metadata(self, path):
        default_meta = {
            "name": "Desconhecido",
            "id": "N/A",
            "author": "-",
            "filename": path.name,
            "sort_key": path.name.lower()
        }

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                metadata = data.get('metadata', {})

                name = metadata.get('name', data.get('id', path.stem))
                p_id = data.get('id', 'unknown')
                author = metadata.get('author', '-')

                return {
                    "name": name,
                    "id": p_id,
                    "author": author,
                    "filename": path.name,
                    "sort_key": name.lower()
                }
        except Exception:
            return default_meta

    def populate_tree(self, data):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for item in data:
            self.tree.insert("", tk.END, values=(
                item["name"],
                item["id"],
                item["author"],
                item["filename"]
            ))

    def filter_list(self, *args):
        query = self.search_var.get().lower()
        if not query:
            self.populate_tree(self.profiles_data)
            return

        filtered = []
        for item in self.profiles_data:
            if (query in item["name"].lower() or
                query in item["id"].lower() or
                query in item["author"].lower() or
                    query in item["filename"].lower()):
                filtered.append(item)

        self.populate_tree(filtered)

    def on_double_click(self, event):
        self.confirm_selection()

    def confirm_selection(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item_values = self.tree.item(selected_item[0])['values']
        filename = item_values[3]

        self.selected_file = filename
        self.on_select_callback(filename)
        self.destroy()


class ConHabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ConHab")
        self.root.geometry("1024x768")
        self.root.minsize(900, 700)

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
            "error": "#f44747",
            "card_bg": "#333333",
        }

        self.engine = None
        self.current_profile_name = "Nenhum Selecionado"
        self.current_profile_file = None

        self.setup_styles()
        self.setup_ui()

        self.loading_overlay = LoadingOverlay(self.root, self.colors)

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
        style.configure("Card.TLabel", font=(
            "Segoe UI", 12), foreground=self.colors["fg_primary"], background=self.colors["card_bg"])
        style.configure("Card.TFrame", background=self.colors["card_bg"])

        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"),
                        background=self.colors["accent"], foreground="white", borderwidth=0, focuscolor=self.colors["bg_main"], padding=(20, 10))

        style.map("Accent.TButton",
                  background=[("active", self.colors["accent_hover"])],
                  foreground=[("!active", "white"), ("active", "white")],
                  relief=[("pressed", "flat")])

        style.configure("Secondary.TButton", font=("Segoe UI", 9), background=self.colors["bg_sec"], foreground=self.colors["fg_primary"],
                        borderwidth=1, bordercolor=self.colors["input_bg"], focuscolor=self.colors["bg_sec"], padding=(10, 5))
        style.map("Secondary.TButton", background=[
                  ("active", self.colors["input_bg"])])

        style.configure("Horizontal.TProgressbar", troughcolor=self.colors["input_bg"], background=self.colors["accent"],
                        bordercolor=self.colors["bg_main"], lightcolor=self.colors["accent"], darkcolor=self.colors["accent"])

        style.configure(
            "TNotebook", background=self.colors["bg_main"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["bg_sec"], foreground=self.colors["fg_secondary"], padding=(
            15, 5), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", self.colors["accent"]), ("active", self.colors["input_bg"])], foreground=[
                  ("selected", "white"), ("active", self.colors["fg_primary"])])

        style.configure("Treeview", background=self.colors["input_bg"], fieldbackground=self.colors["input_bg"], foreground=self.colors["fg_primary"],
                        borderwidth=0, rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=self.colors["bg_sec"], foreground=self.colors["fg_primary"], relief="flat", font=(
            "Segoe UI", 10, "bold"), padding=10)
        style.map("Treeview", background=[
                  ("selected", self.colors["accent"])], foreground=[("selected", "white")])
        style.map("Treeview.Heading", background=[
                  ("active", self.colors["bg_sec"])])

        style.configure("Switch.TCheckbutton",
                        background=self.colors["card_bg"], foreground=self.colors["fg_primary"])

    def setup_ui(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X)
        header_bg = tk.Frame(header_frame, bg=self.colors["bg_sec"], height=60)
        header_bg.pack(fill=tk.BOTH, expand=True)
        header_bg.pack_propagate(False)
        ttk.Label(header_bg, text="ConHab", style="Header.TLabel").pack(
            side=tk.LEFT, padx=20)

        main_container = ttk.Frame(self.root, padding=30)
        main_container.pack(fill=tk.BOTH, expand=True)

        config_frame = ttk.Frame(main_container)
        config_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(config_frame, text="PERFIL ATIVO",
                  style="SubHeader.TLabel").pack(anchor="w")

        profile_card = ttk.Frame(config_frame, style="Card.TFrame", padding=15)
        profile_card.pack(fill=tk.X, pady=5)

        info_box = ttk.Frame(profile_card, style="Card.TFrame")
        info_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.lbl_profile_name = ttk.Label(info_box, text="Nenhum perfil carregado",
                                          font=("Segoe UI", 14, "bold"), style="Card.TLabel")
        self.lbl_profile_name.pack(anchor="w")

        self.lbl_profile_file = ttk.Label(info_box, text="Selecione um arquivo para começar",
                                          font=("Segoe UI", 10, "italic"), foreground=self.colors["fg_secondary"], background=self.colors["card_bg"])
        self.lbl_profile_file.pack(anchor="w", pady=(2, 0))

        actions_box = ttk.Frame(profile_card, style="Card.TFrame")
        actions_box.pack(side=tk.RIGHT)

        ttk.Button(actions_box, text="SELECIONAR PERFIL", style="Secondary.TButton",
                   command=self.open_profile_selector).pack(side=tk.LEFT, padx=(0, 10))

        self.btn_reload = ttk.Button(actions_box, text="⟳ Recarregar", style="Secondary.TButton",
                                     command=self.reload_current_profile, state="disabled")
        self.btn_reload.pack(side=tk.LEFT)

        self.status_lbl = ttk.Label(
            config_frame, text="", foreground=self.colors["fg_secondary"])
        self.status_lbl.pack(anchor="e", pady=(5, 0))

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_translation = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_translation, text="Tradução")
        self.setup_translation_tab()

        self.lexicon_widget = LexiconTab(self.notebook, self.colors)
        self.notebook.add(self.lexicon_widget, text="Léxico")

        self.gramataki_widget = GramatakiTab(
            self.notebook, self.colors, self.engine)
        self.notebook.add(self.gramataki_widget, text="Gramataki")

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

        self.btn_process = ttk.Button(
            input_frame, text="PROCESSAR TEXTO", style="Accent.TButton", command=self.process_language
        )
        self.btn_process.pack(anchor="e", pady=(0, 10))

        self.ln_input = self.create_styled_text(input_frame, height=8)
        self.ln_input.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        action_frame = ttk.Frame(input_frame)
        action_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress_bar = ttk.Progressbar(
            action_frame, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, expand=True)

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

    def open_profile_selector(self):
        ProfileSelectorDialog(self.root, self.colors,
                              self.on_profile_selected_from_dialog)

    def on_profile_selected_from_dialog(self, filename):
        if filename:
            self.loading_overlay.show(f"Carregando {filename}...")

            profile_path = Path("./conlangs") / filename
            self.profile_widget.load_profile(profile_path)

            self.current_profile_file = filename

            thread = threading.Thread(
                target=self._async_load_engine, args=(filename,))
            thread.daemon = True
            thread.start()

    def reload_current_profile(self):
        if self.current_profile_file:
            self.on_profile_selected_from_dialog(self.current_profile_file)

    def _async_load_engine(self, selection):
        try:
            from engine import OriginalLanguageEngine
            profile_path = Path("./conlangs") / selection

            new_engine = OriginalLanguageEngine(profile_path)
            stats = new_engine.get_statistics()

            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('metadata', {})
                    display_name = meta.get('name', data.get('id', selection))
            except:
                display_name = selection

            self.root.after(0, lambda: self._on_engine_loaded(
                new_engine, stats, display_name))
        except Exception as e:
            self.root.after(0, self._on_load_error, e)

    def _on_engine_loaded(self, engine, stats, display_name):
        self.engine = engine
        self.current_profile_name = display_name

        self.lbl_profile_name.config(text=display_name)
        self.lbl_profile_file.config(
            text=f"Arquivo: {self.current_profile_file}")
        self.btn_reload.config(state="normal")

        self.status_lbl.config(
            text=f"ID: {stats.get('profile_id')} | Vocabulário: {stats.get('cached_words')} palavras | Status: Pronto",
            foreground=self.colors["success"]
        )
        self.lexicon_widget.refresh(self.engine)
        self.gramataki_widget.update_engine(self.engine)
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
            self.root.after(0, self._on_processing_error, e)

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
