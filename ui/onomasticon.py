import tkinter as tk
from tkinter import ttk, messagebox


class OnomasticonTab(ttk.Frame):
    def __init__(self, parent, colors):
        super().__init__(parent)
        self.colors = colors
        self.engine = None
        self.setup_ui()

    def setup_ui(self):
        self.main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.config_frame = ttk.Frame(self.main_pane, padding=10)
        self.main_pane.add(self.config_frame, weight=1)

        ttk.Label(self.config_frame, text="Configuração de Geração",
                  font=("Segoe UI", 11, "bold"), foreground=self.colors["fg_primary"]).pack(anchor="w", pady=(0, 15))

        self._create_combobox(self.config_frame, "Tipo:", [
                              "Pessoa", "Lugar", "Organização"], "type_var")
        self._create_combobox(self.config_frame, "Gênero:", [
                              "Masculino", "Feminino", "Neutro"], "gender_var")
        self._create_combobox(self.config_frame, "Origem:", [
                              "Nativo", "Tradução Real"], "origin_var")

        ttk.Label(self.config_frame, text="Input de Tradução:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(15, 5))

        self.input_entry = ttk.Entry(self.config_frame, font=("Segoe UI", 10))
        self.input_entry.pack(fill=tk.X, pady=(0, 15))
        self.input_entry.insert(0, "Digite um nome (ex: Peter)")
        self.input_entry.config(foreground=self.colors["text"])
        self.input_entry.bind("<FocusIn>", self._clear_placeholder)

        self.btn_generate = ttk.Button(
            self.config_frame, text="Gerar", style="Accent.TButton",
            command=self.on_generate
        )
        self.btn_generate.pack(fill=tk.X, pady=10)

        self.results_frame = ttk.Frame(self.main_pane, padding=10)
        self.main_pane.add(self.results_frame, weight=3)

        ttk.Label(self.results_frame, text="Nomes Gerados",
                  font=("Segoe UI", 11, "bold"), foreground=self.colors["fg_primary"]).pack(anchor="w", pady=(0, 10))

        cols = ("name", "meaning", "roots")
        self.results_tree = ttk.Treeview(
            self.results_frame, columns=cols, show="headings", style="Treeview", selectmode="browse"
        )

        self.results_tree.heading("name", text="Nome Gerado")
        self.results_tree.heading("meaning", text="Significado Literal")
        self.results_tree.heading("roots", text="Raízes Usadas")

        self.results_tree.column("name", width=150)
        self.results_tree.column("meaning", width=200)
        self.results_tree.column("roots", width=150)

        scrollbar = ttk.Scrollbar(
            self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_bar = ttk.Frame(self.results_frame, padding=(0, 10, 0, 0))
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_add_lexicon = ttk.Button(
            btn_bar, text="Adicionar", style="Secondary.TButton",
            command=self.on_add_to_lexicon
        )
        self.btn_add_lexicon.pack(side=tk.RIGHT)

    def _create_combobox(self, parent, label_text, values, attr_name):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text=label_text,
                  foreground=self.colors["fg_secondary"], width=10).pack(side=tk.LEFT)
        cb = ttk.Combobox(frame, values=values, state="readonly")
        cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cb.current(0)
        setattr(self, attr_name, cb)

    def _clear_placeholder(self, event):
        if self.input_entry.get() == "Digite um nome (ex: Peter)":
            self.input_entry.delete(0, tk.END)
            self.input_entry.config(foreground=self.colors["text"])

    def on_generate(self):
        if not self.engine:
            return

        name_input = self.input_entry.get().strip()
        if not name_input or name_input == "Digite um nome (ex: Peter)":
            return

        origin_mode = self.origin_var.get()
        mode_key = "translation" if origin_mode == "Tradução Real" else "native"

        result = self.engine.generate_entity_name(name_input, mode=mode_key)

        self.results_tree.insert("", tk.END, values=(
            result['name'], result['meaning'], result['roots']))

    def on_add_to_lexicon(self):
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Aviso", "Selecione um nome gerado para adicionar ao léxico.")
            return

        item = self.results_tree.item(selected)
        values = item['values']
        name = values[0]

        # Lógica para adicionar ao dicionário principal pode ser implementada aqui
        # Por enquanto, apenas feedback visual
        messagebox.showinfo("Sucesso", f"O nome '{name}' foi processado.")
