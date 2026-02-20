import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path


class GramatakiTab(ttk.Frame):
    def __init__(self, parent, colors, engine=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.culture_data = {}
        self.setup_ui()
        self.load_current_culture()

    def update_engine(self, new_engine):
        self.engine = new_engine
        self.load_current_culture()

    def setup_ui(self):
        self.option_add('*TCombobox*Listbox.foreground', self.colors['text'])

        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_generator = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_generator, text="Gerador Onomástico")

        self.tab_nativizer = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_nativizer, text="Nativização & Livre")

        self.tab_editor = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_editor, text="Editor Cultural")

        self._build_generator_tab()
        self._build_nativizer_tab()
        self._build_editor_tab()

    def _build_generator_tab(self):
        control_frame = ttk.LabelFrame(
            self.tab_generator, text="Fórmula Onomástica", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(control_frame, text="Fórmula:", foreground=self.colors["fg_secondary"]).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.formula_var = tk.StringVar()
        self.formula_cb = ttk.Combobox(
            control_frame, textvariable=self.formula_var, state="readonly", foreground=self.colors["text"])
        self.formula_cb.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)

        ttk.Label(control_frame, text="Gênero:", foreground=self.colors["fg_secondary"]).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.gender_var = tk.StringVar(value="Masculino")
        self.gender_cb = ttk.Combobox(control_frame, textvariable=self.gender_var, values=[
                                      "Masculino", "Feminino", "Neutro"], state="readonly", foreground=self.colors["text"])
        self.gender_cb.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)

        control_frame.columnconfigure(1, weight=1)

        self.btn_generate = ttk.Button(
            control_frame, text="Gerar Nome Nativo", style="Accent.TButton", command=self.generate_name)
        self.btn_generate.grid(row=2, column=0, columnspan=2, pady=15)

        output_frame = ttk.LabelFrame(
            self.tab_generator, text="Registro", padding=15)
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.entry_name = tk.Entry(output_frame, font=(
            "Segoe UI", 26, "bold"), fg=self.colors["accent"], bg=self.colors["input_bg"], justify="center", relief="flat")
        self.entry_name.pack(fill=tk.X, pady=15)

        ttk.Label(output_frame, text="Glossário Etimológico:", font=(
            "Segoe UI", 11, "bold"), foreground=self.colors["fg_primary"]).pack(anchor="w", pady=(10, 5))

        self.text_etymology = tk.Text(output_frame, height=12, bg=self.colors["input_bg"], fg=self.colors["fg_primary"], font=(
            "Consolas", 11), borderwidth=0, relief="flat", padx=10, pady=10)
        self.text_etymology.pack(fill=tk.BOTH, expand=True)
        self.text_etymology.configure(state="disabled")

    def _build_nativizer_tab(self):
        frame = ttk.Frame(self.tab_nativizer, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Nome Terrestre (Base):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        self.entry_nativize_base = ttk.Entry(frame, font=("Segoe UI", 12))
        self.entry_nativize_base.pack(fill=tk.X, pady=(0, 15))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Nativizar Nome", style="Accent.TButton",
                   command=self.nativize_name).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(btn_frame, text="Gerar Aleatório (Sem Significado)",
                   command=self.generate_random_name).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        ttk.Label(frame, text="Resultado:", foreground=self.colors["fg_secondary"]).pack(
            anchor="w", pady=(20, 5))
        self.entry_nativize_result = tk.Entry(frame, font=(
            "Segoe UI", 26, "bold"), fg=self.colors["accent"], bg=self.colors["input_bg"], justify="center", relief="flat")
        self.entry_nativize_result.pack(fill=tk.X, pady=5)

    def _build_editor_tab(self):
        editor_notebook = ttk.Notebook(self.tab_editor)
        editor_notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.pool_tab = ttk.Frame(editor_notebook, padding=10)
        editor_notebook.add(self.pool_tab, text="Gerenciador de Pools")

        pool_top = ttk.Frame(self.pool_tab)
        pool_top.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(pool_top, text="Pool Selecionado:").pack(side=tk.LEFT)
        self.pool_var = tk.StringVar()
        self.pool_cb = ttk.Combobox(
            pool_top, textvariable=self.pool_var, state="readonly")
        self.pool_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.pool_cb.bind("<<ComboboxSelected>>", self.on_pool_select)

        ttk.Button(pool_top, text="Novo Pool",
                   command=self.create_new_pool).pack(side=tk.RIGHT)

        self.pool_listbox = tk.Listbox(
            self.pool_tab, bg=self.colors["input_bg"], fg=self.colors["text"], selectbackground=self.colors["accent"])
        self.pool_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        pool_bot = ttk.Frame(self.pool_tab)
        pool_bot.pack(fill=tk.X)
        self.new_word_var = tk.StringVar()
        entry_new_word = ttk.Entry(pool_bot, textvariable=self.new_word_var)
        entry_new_word.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(pool_bot, text="Adicionar",
                   command=self.add_to_pool).pack(side=tk.LEFT, padx=2)
        ttk.Button(pool_bot, text="Remover", command=self.remove_from_pool).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(pool_bot, text="Salvar Cultura", style="Accent.TButton",
                   command=self.save_culture_file).pack(side=tk.RIGHT, padx=5)

        self.json_tab = ttk.Frame(editor_notebook, padding=10)
        editor_notebook.add(self.json_tab, text="Avançado (JSON Completo)")
        self.json_text = tk.Text(self.json_tab, bg=self.colors["input_bg"], fg=self.colors["text"], font=(
            "Consolas", 10), insertbackground=self.colors["text"])
        self.json_text.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(self.json_tab, text="Validar e Salvar JSON",
                   style="Accent.TButton", command=self.save_json_file).pack(pady=5)

    def load_current_culture(self):
        if not self.engine:
            self.culture_data = {}
            return

        profile_id = self.engine.profile_id
        path = Path(f"./cultures/{profile_id}_culture.json")
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    self.culture_data = json.load(file)
            except:
                self.culture_data = self._create_default_culture(profile_id)
        else:
            self.culture_data = self._create_default_culture(profile_id)

        self.update_ui_from_culture()

    def _create_default_culture(self, profile_id):
        return {
            "culture_id": f"{profile_id}_culture",
            "linked_profile": profile_id,
            "description": "Sistema onomástico auto-gerado.",
            "formulas": {},
            "components_rules": {},
            "semantic_pools": {},
            "phonological_filters": {
                "force_capitalization": True,
                "apply_sandhi_between_components": True
            }
        }

    def update_ui_from_culture(self):
        formulas = list(self.culture_data.get("formulas", {}).keys())
        self.formula_cb['values'] = formulas
        if formulas:
            self.formula_cb.current(0)
        else:
            self.formula_var.set("")

        pools = list(self.culture_data.get("semantic_pools", {}).keys())
        self.pool_cb['values'] = pools
        if pools:
            self.pool_cb.current(0)
        else:
            self.pool_var.set("")
        self.on_pool_select()

        self.json_text.delete("1.0", tk.END)
        self.json_text.insert("1.0", json.dumps(
            self.culture_data, indent=4, ensure_ascii=False))

    def on_pool_select(self, event=None):
        self.pool_listbox.delete(0, tk.END)
        pool_name = self.pool_var.get()
        if pool_name and pool_name in self.culture_data.get("semantic_pools", {}):
            items = self.culture_data["semantic_pools"][pool_name]
            for item in items:
                self.pool_listbox.insert(tk.END, item)

    def create_new_pool(self):
        new_pool = simpledialog.askstring(
            "Novo Pool", "Nome do novo pool semântico:")
        if new_pool:
            if "semantic_pools" not in self.culture_data:
                self.culture_data["semantic_pools"] = {}
            if new_pool not in self.culture_data["semantic_pools"]:
                self.culture_data["semantic_pools"][new_pool] = []
                self.update_ui_from_culture()
                self.pool_var.set(new_pool)
                self.on_pool_select()

    def add_to_pool(self):
        pool_name = self.pool_var.get()
        word = self.new_word_var.get().strip()
        if pool_name and word:
            if word not in self.culture_data["semantic_pools"][pool_name]:
                self.culture_data["semantic_pools"][pool_name].append(word)
                self.on_pool_select()
                self.new_word_var.set("")
                self.json_text.delete("1.0", tk.END)
                self.json_text.insert("1.0", json.dumps(
                    self.culture_data, indent=4, ensure_ascii=False))

    def remove_from_pool(self):
        pool_name = self.pool_var.get()
        selection = self.pool_listbox.curselection()
        if pool_name and selection:
            idx = selection[0]
            word = self.pool_listbox.get(idx)
            self.culture_data["semantic_pools"][pool_name].remove(word)
            self.on_pool_select()
            self.json_text.delete("1.0", tk.END)
            self.json_text.insert("1.0", json.dumps(
                self.culture_data, indent=4, ensure_ascii=False))

    def save_culture_file(self, from_json_editor=False):
        if not self.engine:
            return
        profile_id = self.engine.profile_id
        path = Path("./cultures")
        path.mkdir(exist_ok=True)
        file_path = path / f"{profile_id}_culture.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.culture_data, f, indent=4, ensure_ascii=False)
        if not from_json_editor:
            messagebox.showinfo("Sucesso", "Cultura salva com sucesso.")

    def save_json_file(self):
        try:
            content = self.json_text.get("1.0", tk.END)
            data = json.loads(content)
            self.culture_data = data
            self.save_culture_file(from_json_editor=True)
            self.update_ui_from_culture()
            messagebox.showinfo(
                "Sucesso", "JSON validado e sistema cultural atualizado.")
        except Exception as e:
            messagebox.showerror("Erro", f"JSON Inválido:\n{str(e)}")

    def generate_name(self):
        if not self.engine:
            messagebox.showwarning("Aviso", "Motor linguístico não carregado.")
            return

        if not self.culture_data or not self.culture_data.get("formulas"):
            messagebox.showwarning(
                "Aviso", "A cultura não possui fórmulas onomásticas definidas.")
            return

        formula = self.formula_var.get()
        gender = self.gender_var.get()

        if not formula:
            return

        result = self.engine.gramataki_manager.generate_onomastic_name(
            self.culture_data, formula, gender)

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, result['name'])

        self.text_etymology.configure(state="normal")
        self.text_etymology.delete("1.0", tk.END)

        for etym in result['etymology']:
            line = f"{etym['component']}: \"{etym['meaning']}\" ({etym['type']})\n"
            self.text_etymology.insert(tk.END, line)

        self.text_etymology.configure(state="disabled")

    def nativize_name(self):
        if not self.engine:
            return
        base_name = self.entry_nativize_base.get().strip()
        if not base_name:
            return

        nativized = self.engine.gramataki_manager.nativize_external_name(
            base_name)

        self.entry_nativize_result.delete(0, tk.END)
        self.entry_nativize_result.insert(0, nativized)

    def generate_random_name(self):
        if not self.engine:
            return

        random_name = self.engine.gramataki_manager.generate_random_name()

        self.entry_nativize_result.delete(0, tk.END)
        self.entry_nativize_result.insert(0, random_name)
