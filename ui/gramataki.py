import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path
import random
import hashlib


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

        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            self.main_container,
            textvariable=self.status_var,
            foreground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 9, "italic")
        )
        self.status_label.pack(side=tk.BOTTOM, anchor="w", pady=(5, 0))

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

    def show_status(self, message, duration=3000):
        self.status_var.set(message)
        self.after(duration, lambda: self.status_var.set(""))

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

        ttk.Button(
            left_frame, text="🔍 Montar / Derivar Nome", command=self.open_name_assembly_modal
        ).pack(fill=tk.X, pady=(10, 0))

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
        ttk.Button(btn_frame, text="➕ Gerar Mais Variantes",
                   command=self.nativize_name_more).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        ttk.Button(btn_frame, text="🎲 Gerar Aleatório (Sem Significado)", command=self.generate_random_name).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 0))

        output_frame = ttk.LabelFrame(
            container, text="Sugestões Nativizadas", padding=25)
        output_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(output_frame, text="Variantes Geradas (duplo-clique para usar):", font=("Segoe UI", 11,
                  "bold"), foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 10))

        list_frame = ttk.Frame(output_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.listbox_nativize_results = tk.Listbox(
            list_frame,
            font=("Segoe UI", 16, "bold"),
            fg=self.colors.get("text", "black"),
            bg=self.colors.get("input_bg", "#ffffff"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            relief="solid",
            borderwidth=1,
            height=10
        )
        self.listbox_nativize_results.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox_nativize_results.bind(
            "<Double-Button-1>", self._on_nativize_double_click)

        nativize_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.listbox_nativize_results.yview)
        nativize_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_nativize_results.config(
            yscrollcommand=nativize_scroll.set)

        nativize_action_frame = ttk.Frame(output_frame)
        nativize_action_frame.pack(fill=tk.X)

        ttk.Label(nativize_action_frame, text="Classificação:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))

        self.nativize_save_type_var = tk.StringVar(value="nome_proprio")
        nativize_type_cb = ttk.Combobox(
            nativize_action_frame,
            textvariable=self.nativize_save_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome",
                    "alcunha", "ancestor_names", "house_names"],
            state="normal",
            width=15
        )
        nativize_type_cb.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(nativize_action_frame, text="💾 Salvar Selecionado",
                   command=self._save_nativize_selection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(nativize_action_frame, text="🗑 Limpar Lista",
                   command=self._clear_nativize_results).pack(side=tk.LEFT)

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
                pools = list(
                    self.engine.gramataki_manager.unified_pools.keys())
                self.pool_cb['values'] = pools
                self.pool_var.set(new_pool)
                self.on_pool_select()
                self.show_status(f"Pool '{new_pool}' criado.")

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
            self.show_status("Cultura salva com sucesso.")

    def save_json_file(self):
        try:
            content = self.json_text.get("1.0", tk.END)
            data = json.loads(content)
            self.culture_data = data
            self.save_culture_file(from_json_editor=True)
            self.update_ui_from_culture()
            self.show_status("JSON validado e sistema cultural atualizado.")
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
            self.show_status(
                f"Nome '{name}' salvo no cachê como '{name_type}'.")

    def nativize_name(self):
        if not self.engine:
            return
        base_name = self.entry_nativize_base.get().strip()
        if not base_name:
            return

        self._clear_nativize_results()
        variants = self.engine.gramataki_manager.nativize_external_name_multiple(
            base_name, count=20)
        for v in variants:
            if v:
                self.listbox_nativize_results.insert(tk.END, v)

    def nativize_name_more(self):
        if not self.engine:
            return
        base_name = self.entry_nativize_base.get().strip()
        if not base_name:
            return

        existing = set(self.listbox_nativize_results.get(0, tk.END))
        variants = self.engine.gramataki_manager.nativize_external_name_multiple(
            base_name, count=20)
        added = 0
        for v in variants:
            if v and v not in existing:
                self.listbox_nativize_results.insert(tk.END, v)
                existing.add(v)
                added += 1
        if added > 0:
            self.show_status(f"{added} novas variantes adicionadas.")
        else:
            self.show_status(
                "Nenhuma nova variante encontrada. Tente novamente.")

    def _on_nativize_double_click(self, event):
        selection = self.listbox_nativize_results.curselection()
        if not selection:
            return
        name = self.listbox_nativize_results.get(selection[0])
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, name)
        self.notebook.select(0)
        self.show_status(f"'{name}' copiado para o campo de nome gerado.")

    def _save_nativize_selection(self):
        if not self.engine:
            return
        selection = self.listbox_nativize_results.curselection()
        if not selection:
            messagebox.showwarning(
                "Aviso", "Selecione uma variante para salvar.")
            return
        name = self.listbox_nativize_results.get(selection[0])
        name_type = self.nativize_save_type_var.get().strip()
        if name and name_type:
            self.engine.gramataki_manager.save_culture_name(name, name_type)
            self.show_status(f"'{name}' salvo no cachê como '{name_type}'.")

    def _clear_nativize_results(self):
        self.listbox_nativize_results.delete(0, tk.END)

    def generate_random_name(self):
        if not self.engine:
            return

        random_name = self.engine.gramataki_manager.generate_random_name()

        self.listbox_nativize_results.insert(0, random_name)
        self.listbox_nativize_results.selection_clear(0, tk.END)
        self.listbox_nativize_results.selection_set(0)
        self.listbox_nativize_results.see(0)

    def open_name_assembly_modal(self):
        if not self.engine:
            messagebox.showwarning("Aviso", "Motor linguístico não carregado.")
            return

        modal = tk.Toplevel(self)
        modal.title("Montagem e Derivação de Nomes")
        modal.geometry("960x680")
        modal.resizable(True, True)
        modal.grab_set()

        modal.configure(bg=self.colors.get("bg", "#f0f0f0"))

        title_lbl = tk.Label(modal, text="Montagem e Derivação de Nomes",
                             font=("Segoe UI", 13, "bold"),
                             fg=self.colors.get("accent", "#0078D7"),
                             bg=self.colors.get("bg", "#f0f0f0"))
        title_lbl.pack(pady=(15, 5))

        pane = ttk.PanedWindow(modal, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        left_panel = ttk.LabelFrame(pane, text="Cachê de Nomes", padding=12)
        pane.add(left_panel, weight=1)

        filter_frame = ttk.Frame(left_panel)
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(filter_frame, text="Tipo:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT)

        modal_type_var = tk.StringVar(value="(todos)")
        all_types = ["(todos)", "nome_proprio", "nome_e_sobrenome", "sobrenome",
                     "alcunha", "ancestor_names", "house_names"]
        modal_type_cb = ttk.Combobox(filter_frame, textvariable=modal_type_var,
                                     values=all_types, state="readonly", width=14)
        modal_type_cb.pack(side=tk.LEFT, padx=(5, 8))

        ttk.Label(filter_frame, text="Busca:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT)
        modal_search_var = tk.StringVar()
        modal_search_entry = ttk.Entry(
            filter_frame, textvariable=modal_search_var, width=14)
        modal_search_entry.pack(side=tk.LEFT, padx=(5, 0))

        cache_list_frame = ttk.Frame(left_panel)
        cache_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        cache_listbox = tk.Listbox(
            cache_list_frame,
            bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 11),
            relief="solid",
            borderwidth=1,
            height=18
        )
        cache_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cache_scroll = ttk.Scrollbar(
            cache_list_frame, orient="vertical", command=cache_listbox.yview)
        cache_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        cache_listbox.config(yscrollcommand=cache_scroll.set)

        def refresh_cache_list(*args):
            cache_listbox.delete(0, tk.END)
            search_str = modal_search_var.get().strip().lower()
            type_filter = modal_type_var.get()
            names_data = self.engine.gramataki_manager.culture_names
            for n_type, names in names_data.items():
                if type_filter not in ("(todos)", n_type):
                    continue
                for name in names:
                    if search_str and search_str not in name.lower():
                        continue
                    cache_listbox.insert(tk.END, f"{name}  [{n_type}]")

        modal_type_var.trace_add("write", refresh_cache_list)
        modal_search_var.trace_add("write", refresh_cache_list)
        refresh_cache_list()

        right_panel = ttk.Frame(pane, padding=5)
        pane.add(right_panel, weight=2)

        assembly_lf = ttk.LabelFrame(
            right_panel, text="Componentes Selecionados", padding=12)
        assembly_lf.pack(fill=tk.X, pady=(0, 10))

        selected_components = []

        comp_list_frame = ttk.Frame(assembly_lf)
        comp_list_frame.pack(fill=tk.X, pady=(0, 8))

        comp_listbox = tk.Listbox(
            comp_list_frame,
            bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 12),
            relief="solid",
            borderwidth=1,
            height=4
        )
        comp_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        comp_scroll = ttk.Scrollbar(
            comp_list_frame, orient="vertical", command=comp_listbox.yview)
        comp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        comp_listbox.config(yscrollcommand=comp_scroll.set)

        comp_btn_frame = ttk.Frame(assembly_lf)
        comp_btn_frame.pack(fill=tk.X)

        def add_from_cache():
            sel = cache_listbox.curselection()
            if not sel:
                return
            raw = cache_listbox.get(sel[0])
            name_only = raw.split("  [")[0].strip()
            selected_components.append(name_only)
            comp_listbox.insert(tk.END, name_only)
            update_assembled()

        def remove_from_comp():
            sel = comp_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            comp_listbox.delete(idx)
            if idx < len(selected_components):
                selected_components.pop(idx)
            update_assembled()

        def clear_components():
            selected_components.clear()
            comp_listbox.delete(0, tk.END)
            update_assembled()

        ttk.Button(comp_btn_frame, text="➕ Adicionar do Cachê",
                   command=add_from_cache).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_btn_frame, text="✖ Remover Selecionado",
                   command=remove_from_comp).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(comp_btn_frame, text="🗑 Limpar Tudo",
                   command=clear_components).pack(side=tk.LEFT)

        assembled_lf = ttk.LabelFrame(
            right_panel, text="Nome Montado", padding=12)
        assembled_lf.pack(fill=tk.X, pady=(0, 10))

        assembled_var = tk.StringVar()
        assembled_entry = tk.Entry(
            assembled_lf,
            textvariable=assembled_var,
            font=("Segoe UI", 22, "bold"),
            fg=self.colors.get("text", "black"),
            bg=self.colors.get("input_bg", "#ffffff"),
            justify="center",
            relief="solid",
            borderwidth=1
        )
        assembled_entry.pack(fill=tk.X, pady=(0, 10))

        def update_assembled():
            assembled_var.set(" ".join(selected_components))

        assembled_save_frame = ttk.Frame(assembled_lf)
        assembled_save_frame.pack(fill=tk.X)

        ttk.Label(assembled_save_frame, text="Salvar como:",
                  font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))

        assembled_type_var = tk.StringVar(value="nome_e_sobrenome")
        assembled_type_cb = ttk.Combobox(
            assembled_save_frame,
            textvariable=assembled_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome",
                    "alcunha", "ancestor_names", "house_names"],
            state="normal",
            width=15
        )
        assembled_type_cb.pack(side=tk.LEFT, padx=(0, 10))

        def save_assembled():
            name = assembled_var.get().strip()
            n_type = assembled_type_var.get().strip()
            if not name:
                messagebox.showwarning(
                    "Aviso", "Nenhum nome montado para salvar.", parent=modal)
                return
            self.engine.gramataki_manager.save_culture_name(name, n_type)
            self.show_status(f"'{name}' salvo como '{n_type}'.")
            refresh_cache_list()

        def use_as_generated():
            name = assembled_var.get().strip()
            if name:
                self.entry_name.delete(0, tk.END)
                self.entry_name.insert(0, name)
                self.show_status(f"'{name}' definido como nome gerado.")

        ttk.Button(assembled_save_frame, text="💾 Salvar no Cachê",
                   command=save_assembled).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(assembled_save_frame, text="📋 Usar como Nome Gerado",
                   command=use_as_generated).pack(side=tk.LEFT)

        derivation_lf = ttk.LabelFrame(
            right_panel, text="Derivação de Formas", padding=12)
        derivation_lf.pack(fill=tk.BOTH, expand=True)

        deriv_top = ttk.Frame(derivation_lf)
        deriv_top.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(deriv_top, text="Base para derivação:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))

        deriv_base_var = tk.StringVar()
        deriv_base_entry = ttk.Entry(deriv_top, textvariable=deriv_base_var, width=20,
                                     font=("Segoe UI", 11))
        deriv_base_entry.pack(side=tk.LEFT, padx=(0, 8))

        def fill_deriv_from_cache():
            sel = cache_listbox.curselection()
            if not sel:
                return
            raw = cache_listbox.get(sel[0])
            name_only = raw.split("  [")[0].strip()
            deriv_base_var.set(name_only)

        def fill_deriv_from_assembled():
            name = assembled_var.get().strip()
            if name:
                deriv_base_var.set(name)

        ttk.Button(deriv_top, text="← Do Cachê",
                   command=fill_deriv_from_cache).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(deriv_top, text="← Do Montado",
                   command=fill_deriv_from_assembled).pack(side=tk.LEFT)

        deriv_result_frame = ttk.Frame(derivation_lf)
        deriv_result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        deriv_listbox = tk.Listbox(
            deriv_result_frame,
            bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 14, "bold"),
            relief="solid",
            borderwidth=1,
            height=6
        )
        deriv_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        deriv_scroll = ttk.Scrollbar(
            deriv_result_frame, orient="vertical", command=deriv_listbox.yview)
        deriv_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        deriv_listbox.config(yscrollcommand=deriv_scroll.set)

        def generate_derivations():
            base = deriv_base_var.get().strip()
            if not base:
                messagebox.showwarning(
                    "Aviso", "Informe uma base para derivar.", parent=modal)
                return
            deriv_listbox.delete(0, tk.END)
            results = self.engine.gramataki_manager.generate_derived_forms(
                base, count=15)
            for r in results:
                deriv_listbox.insert(tk.END, r)

        def generate_more_derivations():
            base = deriv_base_var.get().strip()
            if not base:
                return
            existing = set(deriv_listbox.get(0, tk.END))
            results = self.engine.gramataki_manager.generate_derived_forms(
                base, count=15)
            added = 0
            for r in results:
                if r not in existing:
                    deriv_listbox.insert(tk.END, r)
                    existing.add(r)
                    added += 1

        deriv_action_frame = ttk.Frame(derivation_lf)
        deriv_action_frame.pack(fill=tk.X)

        ttk.Button(deriv_action_frame, text="✨ Gerar Derivadas", style="Accent.TButton",
                   command=generate_derivations).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(deriv_action_frame, text="➕ Mais Derivadas",
                   command=generate_more_derivations).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(deriv_action_frame, text="Salvar derivada como:",
                  font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))

        deriv_save_type_var = tk.StringVar(value="nome_proprio")
        deriv_save_type_cb = ttk.Combobox(
            deriv_action_frame,
            textvariable=deriv_save_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome",
                    "alcunha", "ancestor_names", "house_names"],
            state="normal",
            width=14
        )
        deriv_save_type_cb.pack(side=tk.LEFT, padx=(0, 8))

        def save_derivation():
            sel = deriv_listbox.curselection()
            if not sel:
                messagebox.showwarning(
                    "Aviso", "Selecione uma forma derivada.", parent=modal)
                return
            name = deriv_listbox.get(sel[0])
            n_type = deriv_save_type_var.get().strip()
            self.engine.gramataki_manager.save_culture_name(name, n_type)
            self.show_status(f"Derivada '{name}' salva como '{n_type}'.")
            refresh_cache_list()

        def use_derivation_as_component():
            sel = deriv_listbox.curselection()
            if not sel:
                return
            name = deriv_listbox.get(sel[0])
            selected_components.append(name)
            comp_listbox.insert(tk.END, name)
            update_assembled()

        ttk.Button(deriv_action_frame, text="💾 Salvar Selecionada",
                   command=save_derivation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(deriv_action_frame, text="➕ Usar como Componente",
                   command=use_derivation_as_component).pack(side=tk.LEFT)

        bottom_bar = ttk.Frame(modal, padding=(15, 8))
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(bottom_bar, text="Fechar",
                   command=modal.destroy).pack(side=tk.RIGHT)


class GramatakiManager:
    def __init__(self, profile, engine_ref):
        self.profile = profile
        self.engine = engine_ref
        self.profile_id = profile.get('id', 'unknown')
        self.dictionary = {}
        self.storage_path = Path(
            f"./gramatakis/{self.profile_id}_gramataki.json")

        self.caches_dir = Path("./cultures/caches")
        self.caches_dir.mkdir(parents=True, exist_ok=True)
        self.unified_pools_path = self.caches_dir / \
            f"{self.profile_id}_pools_cache.json"
        self.culture_names_path = self.caches_dir / \
            f"{self.profile_id}_names.json"
        self.unified_pools = {}
        self.culture_names = {}

        self.load_dictionary()
        self.load_culture_caches()

    def load_dictionary(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.dictionary = json.load(f)
            except Exception:
                self.dictionary = {}
        else:
            self.dictionary = {}

    def load_culture_caches(self):
        self.unified_pools = {}
        if self.unified_pools_path.exists():
            try:
                with open(self.unified_pools_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.unified_pools = data.get(self.profile_id, {})
            except:
                pass
        if self.culture_names_path.exists():
            try:
                with open(self.culture_names_path, 'r', encoding='utf-8') as f:
                    self.culture_names = json.load(f)
            except:
                pass

    def save_dictionary(self):
        if not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.dictionary, f, indent=2, ensure_ascii=False)

    def save_unified_pools(self):
        all_pools = {}
        if self.unified_pools_path.exists():
            try:
                with open(self.unified_pools_path, 'r', encoding='utf-8') as f:
                    all_pools = json.load(f)
            except:
                pass
        all_pools[self.profile_id] = self.unified_pools
        with open(self.unified_pools_path, 'w', encoding='utf-8') as f:
            json.dump(all_pools, f, indent=4, ensure_ascii=False)

    def save_culture_name(self, name, name_type):
        if name_type not in self.culture_names:
            self.culture_names[name_type] = []
        if name not in self.culture_names[name_type]:
            self.culture_names[name_type].append(name)
            with open(self.culture_names_path, 'w', encoding='utf-8') as f:
                json.dump(self.culture_names, f, indent=4, ensure_ascii=False)

    def save_entry(self, entry):
        lemma = entry.get('lemma')
        if lemma:
            self.dictionary[lemma] = entry
            self.save_dictionary()

    def _get_pool_words(self, pool_key, culture):
        words = set()
        if pool_key in culture.get('semantic_pools', {}):
            words.update(culture['semantic_pools'][pool_key])
        if pool_key in self.unified_pools:
            words.update(self.unified_pools[pool_key])
        if pool_key in self.culture_names:
            words.update(self.culture_names[pool_key])
        return list(words)

    def generate_onomastic_name(self, culture, formula_id, gender):
        formula = culture.get('formulas', {}).get(formula_id, [])
        components_rules = culture.get('components_rules', {})
        filters = culture.get('phonological_filters', {})
        generated_parts = []
        etymology = []
        for comp_name in formula:
            rule = components_rules.get(comp_name)
            if not rule:
                continue
            comp_result = self._generate_component(
                comp_name, rule, culture, gender)
            if comp_result and comp_result.get('word'):
                generated_parts.append(comp_result['word'])
                etymology.append({
                    'component': comp_result['word'],
                    'meaning': comp_result.get('meaning', ''),
                    'type': comp_name
                })
        final_name = self._apply_phonological_filters(generated_parts, filters)
        return {
            'name': final_name,
            'etymology': etymology
        }

    def _generate_component(self, comp_name, rule, culture, gender):
        if comp_name in self.culture_names and random.random() < 0.25:
            w1 = random.choice(self.culture_names[comp_name])
            return {'word': w1, 'meaning': f"{w1} (Tradicional)"}

        strategies = rule.get('generation_strategies', [])
        if strategies:
            weights = [s.get('weight', 1.0) for s in strategies]
            strategy = random.choices(strategies, weights=weights, k=1)[0]
            stype = strategy.get('type')
            if stype == 'compound':
                p1_words = self._get_pool_words(
                    strategy.get('pool_1'), culture)
                p2_words = self._get_pool_words(
                    strategy.get('pool_2'), culture)
                if p1_words and p2_words:
                    w1 = random.choice(p1_words)
                    w2 = random.choice(p2_words)
                    cw1 = self.engine._get_word_form(w1, skip_cache=True)
                    cw2 = self.engine._get_word_form(w2, skip_cache=True)
                    if self.engine.compounding_handler.enabled:
                        final_w = self.engine.compounding_handler.construct_compound(
                            [cw1, cw2], self.engine)
                    else:
                        final_w = cw1 + cw2
                    return {'word': final_w, 'meaning': f"{w1} + {w2}"}
            elif stype == 'verbal_sentence':
                pattern = strategy.get('pattern', [])
                if len(pattern) >= 2:
                    p1_words = self._get_pool_words(pattern[0], culture)
                    p2_words = self._get_pool_words(pattern[1], culture)
                    if p1_words and p2_words:
                        w1 = random.choice(p1_words)
                        w2 = random.choice(p2_words)
                        cw1 = self.engine._get_word_form(
                            w1, pos='VERB', skip_cache=True)
                        cw2 = self.engine._get_word_form(
                            w2, pos='NOUN', skip_cache=True)
                        return {'word': cw1 + cw2, 'meaning': f"{w1} {w2}"}
            elif stype == 'abstract_derivation':
                pool_key = strategy.get('pool', 'concept_noun')
                p_words = self._get_pool_words(pool_key, culture)
                if p_words:
                    w1 = random.choice(p_words)
                    cw1 = self.engine._get_word_form(w1, skip_cache=True)
                    if self.engine.affix_handler.enabled:
                        der_rule = self.engine.affix_handler.get_derivation_rule(
                            "NOUN", "NOUN", strategy.get('derivation_type', 'abstract_noun'))
                        if der_rule:
                            cw1 = self.engine.affix_handler.apply_affix(
                                cw1, der_rule)
                    return {'word': cw1, 'meaning': f"{w1} (Abstrato)"}

        rel_type = rule.get('type')
        if rel_type == 'relational':
            target = rule.get('target')
            connector = rule.get('connector', '')

            gender_connectors = rule.get('gender_connectors', {})
            if gender and gender in gender_connectors:
                connector = gender_connectors[gender]
            elif gender == 'Feminino' and 'connector_female' in rule:
                connector = rule.get('connector_female')

            target_rule = culture.get('components_rules', {}).get(target)
            if target_rule:
                target_res = self._generate_component(
                    target, target_rule, culture, gender)
                if target_res and target_res.get('word'):
                    final_w = f"{connector} {target_res['word']}" if connector else target_res['word']
                    meaning_str = f"{connector} ({target_res['meaning']})" if connector else target_res['meaning']
                    return {'word': final_w.strip(), 'meaning': meaning_str.strip()}

        elif rel_type == 'pool_selection':
            target_pool = rule.get('pool')
            p_words = self._get_pool_words(target_pool, culture)
            if p_words:
                w1 = random.choice(p_words)
                cw1 = self.engine._get_word_form(w1, skip_cache=True)
                return {'word': cw1, 'meaning': w1}

        elif rel_type == 'affixation':
            target_pool = rule.get('target')
            affix_rule = rule.get('affix_rule', {})
            p_words = self._get_pool_words(target_pool, culture)
            if p_words:
                w1 = random.choice(p_words)
                cw1 = self.engine._get_word_form(w1, skip_cache=True)
                final_w = cw1
                if affix_rule:
                    affix = affix_rule.get('affix', '')
                    pos = affix_rule.get('position', 'suffix')
                    if pos == 'suffix':
                        final_w = cw1 + affix.replace('-', '')
                    else:
                        final_w = affix.replace('-', '') + cw1
                return {'word': final_w, 'meaning': f"{w1} ({affix_rule.get('description', '')})"}

        elif rel_type == 'trait_derivation':
            target_pool = rule.get('target')
            degree = rule.get('degree')
            p_words = self._get_pool_words(target_pool, culture)
            if p_words:
                w1 = random.choice(p_words)
                cw1 = self.engine._get_word_form(w1, skip_cache=True)
                if self.engine.degree_handler.enabled and degree:
                    cw1 = self.engine.degree_handler.apply_degree(cw1, degree)
                return {'word': cw1, 'meaning': f"{w1} ({degree})"}

        all_words = []
        for pool_key in self.unified_pools:
            all_words.extend(self.unified_pools[pool_key])
        if 'semantic_pools' in culture:
            for p in culture['semantic_pools'].values():
                all_words.extend(p)
        if all_words:
            w1 = random.choice(all_words)
            return {'word': self.engine._get_word_form(w1, skip_cache=True), 'meaning': w1}

        return {'word': self.engine._generate_word_from_seed(comp_name, self.engine.global_seed + random.randint(1, 1000)), 'meaning': 'Desconhecido'}

    def _apply_phonological_filters(self, name_parts, filters):
        raw_name = " ".join(name_parts)
        if filters.get('apply_sandhi_between_components', False) and self.engine.sandhi_handler.enabled:
            final_name = self.engine.sandhi_handler.apply_sandhi(raw_name)
        else:
            final_name = raw_name
        if filters.get('force_capitalization', True):
            final_name = " ".join(part.capitalize()
                                  for part in final_name.split())
        return final_name

    def generate_candidates(self, meaning, options):
        candidates = []
        is_abstract = options.get('abstract', False)
        force_loan = options.get('force_loan', False)
        register = options.get('register', 'Neutro')

        clean_meaning = "".join(
            c for c in meaning if c.isalnum() or c.isspace()).strip()

        salt = options.get('salt', '')
        seed_str = f"{clean_meaning}_{self.engine.global_seed}_gramataki_{salt}"
        seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)

        generated_word = ""
        gloss = meaning

        if force_loan:
            generated_word = self.engine.loanword_handler.nativize_reserved_term(
                clean_meaning.split()[0])
            gloss = f"Empréstimo de: {clean_meaning}"

        elif self.engine.compounding_handler.enabled and " " in clean_meaning:
            parts = clean_meaning.split()
            keywords = [w for w in parts if len(w) > 3]
            if len(keywords) < 2:
                keywords = parts[:2]

            sub_words = []
            for kw in keywords:
                sub_word = self.engine._generate_word_from_seed(
                    kw,
                    int(hashlib.sha256(
                        f"{kw}_{seed}".encode()).hexdigest(), 16)
                )
                sub_words.append(sub_word)

            generated_word = self.engine.compounding_handler.construct_compound(
                sub_words, self.engine)
            if self.engine.sandhi_handler.enabled:
                generated_word = self.engine.sandhi_handler.apply_sandhi(
                    generated_word)
            gloss = f"Composto de: {', '.join(keywords)}"

        else:
            if self.engine.root_handler.enabled:
                root = self.engine.root_handler.generate_root(clean_meaning)
                pattern = self.engine.root_handler.get_binyan_by_meaning(
                    'basic')
                generated_word = self.engine.root_handler.apply_pattern(
                    root, pattern)
                gloss = f"Raiz: {'-'.join(root)}"
            else:
                generated_word = self.engine._generate_word_from_seed(
                    clean_meaning, seed)
                gloss = "Geração fonotática simples"

        if is_abstract and self.engine.affix_handler.enabled:
            rule = self.engine.affix_handler.get_derivation_rule(
                "ADJ", "NOUN", "abstract_noun")
            if not rule:
                rule = self.engine.affix_handler.get_derivation_rule(
                    "VERB", "NOUN", "verbal_noun")

            if rule:
                generated_word = self.engine.affix_handler.apply_affix(
                    generated_word, rule)
                gloss += " + Derivação Abstrata"

        if register != "Neutro":
            generated_word = self.engine.phonology_handler.apply_rules(
                generated_word, register.lower())
            gloss += f" ({register})"

        if self.engine.special_mechanics_handler.enabled:
            generated_word = self.engine.special_mechanics_handler.apply_mechanics(
                generated_word, clean_meaning, self.engine.global_seed)

        candidates.append({
            'lemma': generated_word,
            'pos': 'NOUN' if is_abstract else 'UNK',
            'score': 100,
            'gloss': gloss
        })

        return candidates

    def nativize_external_name(self, name):
        if not name:
            return ""
        parts = name.split()
        nativized_parts = []
        for part in parts:
            nativized = self.engine.phonology_handler.nativize_word(part)
            if nativized:
                nativized_parts.append(nativized.capitalize())
        final_name = " ".join(nativized_parts)
        if self.engine.sandhi_handler.enabled:
            final_name = self.engine.sandhi_handler.apply_sandhi(final_name)
        return final_name

    def nativize_external_name_multiple(self, name, count=20):
        if not name:
            return []

        ph = self.engine.phonology_handler
        parts = name.strip().split()
        results = []
        seen = set()

        base = self.nativize_external_name(name)
        if base and base not in seen:
            results.append(base)
            seen.add(base)

        vowels_list = list(ph.vowels) if ph.vowels else list("aeiou")
        consonants_list = list(ph.consonants) if ph.consonants else []

        attempts = 0
        max_attempts = count * 8

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            seed_val = int(hashlib.sha256(
                f"{name}_multi_{attempts}_{len(results)}".encode()
            ).hexdigest(), 16)
            rng = random.Random(seed_val)

            deviation = 0.15 + (attempts / max_attempts) * 0.55

            nativized_parts = []
            for part in parts:
                nativized_chars = []
                for char in part.lower():
                    char_norm = char
                    is_vowel = char_norm in "aeiouyäëïöü"

                    base_phoneme = ph.get_closest_phoneme(char_norm)

                    if rng.random() < deviation:
                        pool = vowels_list if is_vowel else consonants_list
                        if pool:
                            chosen = rng.choice(pool)
                        else:
                            chosen = base_phoneme
                    else:
                        chosen = base_phoneme

                    nativized_chars.append(chosen)

                raw = "".join(nativized_chars)
                raw = ph.apply_monophthongization(raw)

                if raw and not ph.is_valid_final(raw[-1]):
                    valid_finals = [
                        c for c in consonants_list if ph.is_valid_final(c)] + vowels_list
                    if valid_finals:
                        raw = raw[:-1] + rng.choice(valid_finals)

                if raw:
                    nativized_parts.append(raw.capitalize())

            candidate = " ".join(nativized_parts)
            if self.engine.sandhi_handler.enabled:
                candidate = self.engine.sandhi_handler.apply_sandhi(candidate)

            if candidate and candidate not in seen:
                results.append(candidate)
                seen.add(candidate)

        return results

    def generate_derived_forms(self, name, count=15):
        if not name:
            return []

        ph = self.engine.phonology_handler
        vowels_list = list(ph.vowels) if ph.vowels else list("aeiou")
        consonants_list = list(ph.consonants) if ph.consonants else []

        results = []
        seen = set()
        seen.add(name)

        strategies = [
            "change_suffix_vowel",
            "change_suffix_consonant",
            "swap_internal_vowel",
            "add_vowel_suffix",
            "add_consonant_suffix",
            "truncate_and_extend",
            "swap_final_consonant",
            "insert_medial_vowel",
            "change_initial_cluster",
            "double_final_vowel",
        ]

        attempts = 0
        max_attempts = count * 10

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            seed_val = int(hashlib.sha256(
                f"{name}_deriv_{attempts}".encode()
            ).hexdigest(), 16)
            rng = random.Random(seed_val)

            strategy = rng.choice(strategies)
            base = name.lower().strip()
            candidate = base

            if strategy == "change_suffix_vowel" and len(base) >= 2:
                stem = base[:-1]
                if vowels_list:
                    new_end = rng.choice(vowels_list)
                    candidate = stem + new_end

            elif strategy == "change_suffix_consonant" and len(base) >= 2:
                if consonants_list:
                    valid = [
                        c for c in consonants_list if ph.is_valid_final(c)]
                    if valid:
                        candidate = base[:-1] + rng.choice(valid)

            elif strategy == "swap_internal_vowel" and len(base) >= 3:
                vowel_idxs = [i for i, c in enumerate(
                    base) if c in (ph.vowels or "aeiou")]
                if vowel_idxs and vowels_list and len(vowels_list) > 1:
                    idx = rng.choice(vowel_idxs)
                    current = base[idx]
                    options = [v for v in vowels_list if v != current]
                    if options:
                        chars = list(base)
                        chars[idx] = rng.choice(options)
                        candidate = "".join(chars)

            elif strategy == "add_vowel_suffix" and vowels_list:
                candidate = base + rng.choice(vowels_list)

            elif strategy == "add_consonant_suffix" and consonants_list:
                valid = [c for c in consonants_list if ph.is_valid_final(c)]
                if valid and not (base and base[-1] in (ph.consonants or "")):
                    candidate = base + rng.choice(valid)

            elif strategy == "truncate_and_extend" and len(base) >= 3:
                trunc_at = rng.randint(max(1, len(base) - 2), len(base) - 1)
                stem = base[:trunc_at]
                if vowels_list:
                    candidate = stem + rng.choice(vowels_list)
                    if consonants_list and rng.random() < 0.4:
                        valid = [
                            c for c in consonants_list if ph.is_valid_final(c)]
                        if valid:
                            candidate = candidate + rng.choice(valid)

            elif strategy == "swap_final_consonant" and len(base) >= 2:
                if base[-1] in (ph.consonants or "") and consonants_list:
                    valid = [c for c in consonants_list if ph.is_valid_final(
                        c) and c != base[-1]]
                    if valid:
                        candidate = base[:-1] + rng.choice(valid)

            elif strategy == "insert_medial_vowel" and len(base) >= 2 and vowels_list:
                insert_pos = rng.randint(1, len(base) - 1)
                candidate = base[:insert_pos] + \
                    rng.choice(vowels_list) + base[insert_pos:]

            elif strategy == "change_initial_cluster" and len(base) >= 2 and consonants_list:
                if base[0] in (ph.consonants or ""):
                    options = [c for c in consonants_list if c != base[0]]
                    if options:
                        candidate = rng.choice(options) + base[1:]

            elif strategy == "double_final_vowel" and len(base) >= 1:
                if base[-1] in (ph.vowels or "") and vowels_list:
                    candidate = base + base[-1]

            candidate = ph.apply_monophthongization(candidate)

            if candidate and not ph.is_valid_final(candidate[-1]):
                valid_finals = [
                    c for c in consonants_list if ph.is_valid_final(c)] + vowels_list
                if valid_finals:
                    candidate = candidate[:-1] + rng.choice(valid_finals)

            if candidate:
                candidate = candidate.capitalize()
                if self.engine.sandhi_handler.enabled:
                    candidate = self.engine.sandhi_handler.apply_sandhi(
                        candidate)

            if candidate and candidate not in seen and len(candidate) >= 2:
                results.append(candidate)
                seen.add(candidate)

        return results

    def generate_random_name(self):
        seed = random.randint(0, 9999999)
        word = self.engine._generate_word_from_seed(
            f"rand_{seed}", seed, is_derived=False)
        if word and self.engine.sandhi_handler.enabled:
            word = self.engine.sandhi_handler.apply_sandhi(word)
        return word.capitalize() if word else ""
