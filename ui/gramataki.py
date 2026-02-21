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
        self.option_add('*TCombobox*Listbox.foreground',
                        self.colors.get("text", "black"))

        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_generator = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_generator, text="Gerador Onomástico")

        self.tab_nativizer = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_nativizer, text="Nativização & Livre")

        self.tab_editor = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_editor, text="Editor Cultural")

        self._build_generator_tab()
        self._build_nativizer_tab()
        self._build_editor_tab()

    def _build_generator_tab(self):
        main_pane = ttk.PanedWindow(self.tab_generator, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(
            main_pane, text="Configurações e Parâmetros", padding=20)
        main_pane.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Fórmula Onomástica:", font=("Segoe UI", 10, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        self.formula_var = tk.StringVar()
        self.formula_cb = ttk.Combobox(left_frame, textvariable=self.formula_var, state="readonly", font=(
            "Segoe UI", 11), foreground=self.colors.get("text", "black"))
        self.formula_cb.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(left_frame, text="Gênero:", font=("Segoe UI", 10, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        self.gender_var = tk.StringVar(value="Masculino")
        self.gender_cb = ttk.Combobox(left_frame, textvariable=self.gender_var, values=[
                                      "Masculino", "Feminino", "Neutro"], state="readonly", font=("Segoe UI", 11), foreground=self.colors.get("text", "black"))
        self.gender_cb.pack(fill=tk.X, pady=(0, 30))

        self.btn_generate = ttk.Button(
            left_frame, text="✨ Gerar Nome Nativo", style="Accent.TButton", command=self.generate_name)
        self.btn_generate.pack(fill=tk.X, pady=(10, 0))

        right_frame = ttk.LabelFrame(
            main_pane, text="Resultado e Etimologia", padding=20)
        main_pane.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Nome Gerado:", font=("Segoe UI", 10, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        self.entry_name = tk.Entry(right_frame, font=("Segoe UI", 32, "bold"), fg=self.colors.get(
            "text", "black"), bg=self.colors.get("input_bg", "#ffffff"), justify="center", relief="solid", borderwidth=1)
        self.entry_name.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(right_frame, text="Glossário Etimológico:", font=("Segoe UI", 10, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))

        text_frame = ttk.Frame(right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text_etymology = tk.Text(text_frame, height=12, bg=self.colors.get("input_bg", "#ffffff"), fg=self.colors.get(
            "text", "black"), font=("Consolas", 11), borderwidth=1, relief="solid", padx=10, pady=10)
        self.text_etymology.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.text_etymology.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_etymology.config(yscrollcommand=scrollbar.set)
        self.text_etymology.configure(state="disabled")

        save_frame = ttk.Frame(right_frame)
        save_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Label(save_frame, text="Classificação Cultural:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))

        self.name_type_var = tk.StringVar(value="nome_proprio")
        self.name_type_cb = ttk.Combobox(save_frame, textvariable=self.name_type_var,
                                         values=[
                                             "nome_proprio", "nome_e_sobrenome", "sobrenome", "alcunha", "ancestor_names", "house_names"],
                                         state="normal", width=15)
        self.name_type_cb.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(save_frame, text="💾 Salvar no Cachê",
                   command=self.save_generated_name).pack(side=tk.LEFT)

    def _build_nativizer_tab(self):
        container = ttk.Frame(self.tab_nativizer, padding=40)
        container.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(
            container, text="Ajuste e Nativização", padding=25)
        input_frame.pack(fill=tk.X, pady=(0, 30))

        ttk.Label(input_frame, text="Nome Terrestre (Base):", font=("Segoe UI", 11, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        self.entry_nativize_base = ttk.Entry(input_frame, font=(
            "Segoe UI", 14), foreground=self.colors.get("text", "black"))
        self.entry_nativize_base.pack(fill=tk.X, pady=(0, 20))

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="🔄 Nativizar Nome", style="Accent.TButton",
                   command=self.nativize_name).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        ttk.Button(btn_frame, text="🎲 Gerar Aleatório (Sem Significado)", command=self.generate_random_name).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 0))

        output_frame = ttk.LabelFrame(container, text="Resultado", padding=25)
        output_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(output_frame, text="Nome Adaptado / Gerado:", font=("Segoe UI", 11,
                  "bold"), foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 10))
        self.entry_nativize_result = tk.Entry(output_frame, font=("Segoe UI", 36, "bold"), fg=self.colors.get(
            "text", "black"), bg=self.colors.get("input_bg", "#ffffff"), justify="center", relief="solid", borderwidth=1)
        self.entry_nativize_result.pack(fill=tk.X, expand=True)

    def _build_editor_tab(self):
        editor_notebook = ttk.Notebook(self.tab_editor)
        editor_notebook.pack(fill=tk.BOTH, expand=True, pady=5)

        self.pool_tab = ttk.Frame(editor_notebook, padding=20)
        editor_notebook.add(
            self.pool_tab, text="Gerenciador de Pools Unificados")

        pool_top = ttk.Frame(self.pool_tab)
        pool_top.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(pool_top, text="Pool Selecionado:", font=(
            "Segoe UI", 11, "bold"), foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT)

        self.pool_var = tk.StringVar()
        self.pool_cb = ttk.Combobox(pool_top, textvariable=self.pool_var, state="readonly", font=(
            "Segoe UI", 11), foreground=self.colors.get("fg_secondary", "black"))
        self.pool_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15)
        self.pool_cb.bind("<<ComboboxSelected>>", self.on_pool_select)

        ttk.Button(pool_top, text="➕ Novo Pool",
                   command=self.create_new_pool).pack(side=tk.RIGHT)

        list_frame = ttk.Frame(self.pool_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.pool_listbox = tk.Listbox(list_frame, bg=self.colors.get("input_bg", "#ffffff"), fg=self.colors.get(
            "text", "black"), selectbackground=self.colors.get("accent", "#0078D7"), font=("Segoe UI", 12), relief="solid", borderwidth=1)
        self.pool_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.pool_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pool_listbox.config(yscrollcommand=scrollbar.set)

        pool_bot = ttk.Frame(self.pool_tab)
        pool_bot.pack(fill=tk.X)
        self.new_word_var = tk.StringVar()
        entry_new_word = ttk.Entry(pool_bot, textvariable=self.new_word_var, font=(
            "Segoe UI", 12), foreground=self.colors.get("text", "black"))
        entry_new_word.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(pool_bot, text="Adicionar",
                   command=self.add_to_pool).pack(side=tk.LEFT, padx=5)
        ttk.Button(pool_bot, text="Remover Selecionado",
                   command=self.remove_from_pool).pack(side=tk.LEFT, padx=5)
        ttk.Button(pool_bot, text="💾 Salvar Cultura", style="Accent.TButton",
                   command=self.save_culture_file).pack(side=tk.RIGHT, padx=(20, 0))

        self.json_tab = ttk.Frame(editor_notebook, padding=20)
        editor_notebook.add(self.json_tab, text="Avançado (JSON Completo)")

        json_frame = ttk.Frame(self.json_tab)
        json_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.json_text = tk.Text(json_frame, bg=self.colors.get("input_bg", "#ffffff"), fg=self.colors.get("text", "black"), font=(
            "Consolas", 11), insertbackground=self.colors.get("text", "black"), relief="solid", borderwidth=1, padx=10, pady=10)
        self.json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        json_scroll = ttk.Scrollbar(
            json_frame, orient="vertical", command=self.json_text.yview)
        json_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.json_text.config(yscrollcommand=json_scroll.set)

        ttk.Button(self.json_tab, text="✔️ Validar e Salvar JSON",
                   style="Accent.TButton", command=self.save_json_file).pack(pady=10, ipadx=20)

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

        if self.engine and hasattr(self.engine.gramataki_manager, 'unified_pools'):
            pools = list(self.engine.gramataki_manager.unified_pools.keys())
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
        if pool_name and self.engine and hasattr(self.engine.gramataki_manager, 'unified_pools'):
            if pool_name in self.engine.gramataki_manager.unified_pools:
                items = self.engine.gramataki_manager.unified_pools[pool_name]
                for item in items:
                    self.pool_listbox.insert(tk.END, item)

    def create_new_pool(self):
        if not self.engine:
            return
        new_pool = simpledialog.askstring(
            "Novo Pool", "Nome do novo pool semântico:")
        if new_pool:
            if new_pool not in self.engine.gramataki_manager.unified_pools:
                self.engine.gramataki_manager.unified_pools[new_pool] = []
                self.engine.gramataki_manager.save_unified_pools()
                self.update_ui_from_culture()
                self.pool_var.set(new_pool)
                self.on_pool_select()

    def add_to_pool(self):
        if not self.engine:
            return
        pool_name = self.pool_var.get()
        word = self.new_word_var.get().strip()
        if pool_name and word:
            if word not in self.engine.gramataki_manager.unified_pools[pool_name]:
                self.engine.gramataki_manager.unified_pools[pool_name].append(
                    word)
                self.engine.gramataki_manager.save_unified_pools()
                self.on_pool_select()
                self.new_word_var.set("")

    def remove_from_pool(self):
        if not self.engine:
            return
        pool_name = self.pool_var.get()
        selection = self.pool_listbox.curselection()
        if pool_name and selection:
            idx = selection[0]
            word = self.pool_listbox.get(idx)
            self.engine.gramataki_manager.unified_pools[pool_name].remove(word)
            self.engine.gramataki_manager.save_unified_pools()
            self.on_pool_select()

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

    def save_generated_name(self):
        if not self.engine:
            return
        name = self.entry_name.get().strip()
        name_type = self.name_type_var.get().strip()
        if name and name_type:
            self.engine.gramataki_manager.save_culture_name(name, name_type)
            messagebox.showinfo(
                "Sucesso", f"Nome '{name}' salvo no cachê como '{name_type}'.")

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
