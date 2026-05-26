import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path
import random
import hashlib
import re


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

        left_outer = ttk.Frame(main_pane)
        main_pane.add(left_outer, weight=1)

        canvas = tk.Canvas(left_outer, bg=self.colors.get(
            "bg", "#f0f0f0"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            left_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(canvas, padding=15)
        canvas_window = canvas.create_window(
            (0, 0), window=left_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        left_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        ttk.Label(left_frame, text="FÓRMULA ONOMÁSTICA", font=("Segoe UI", 9, "bold"),
                  foreground=self.colors.get("accent", "#0078D7")).pack(anchor="w", pady=(0, 4))

        self.formula_var = tk.StringVar()
        self.formula_cb = ttk.Combobox(left_frame, textvariable=self.formula_var, state="readonly",
                                       font=("Segoe UI", 11), foreground=self.colors.get("text", "black"))
        self.formula_cb.pack(fill=tk.X, pady=(0, 8))

        self.gender_var = tk.StringVar(value="Masculino")
        gender_frame = ttk.Frame(left_frame)
        gender_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(gender_frame, text="Gênero:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 6))
        self.gender_cb = ttk.Combobox(gender_frame, textvariable=self.gender_var,
                                      values=["Masculino",
                                              "Feminino", "Neutro"],
                                      state="readonly", font=("Segoe UI", 11),
                                      foreground=self.colors.get("text", "black"), width=12)
        self.gender_cb.pack(side=tk.LEFT)

        btn_row1 = ttk.Frame(left_frame)
        btn_row1.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btn_row1, text="✨ Gerar Nome Nativo", style="Accent.TButton",
                   command=self.generate_name).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(btn_row1, text="🔍 Montar / Derivar",
                   command=self.open_name_assembly_modal).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(left_frame, orient="horizontal").pack(fill=tk.X, pady=12)

        ttk.Label(left_frame, text="CONCEITO → NOME", font=("Segoe UI", 9, "bold"),
                  foreground=self.colors.get("accent", "#0078D7")).pack(anchor="w", pady=(0, 4))
        ttk.Label(left_frame, text="Digite um conceito ou frase (ex: 'o guerreiro do escudo'):",
                  font=("Segoe UI", 8), foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.concept_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.concept_var, font=("Segoe UI", 11),
                  foreground=self.colors.get("text", "black")).pack(fill=tk.X, pady=(4, 6))
        btn_row2 = ttk.Frame(left_frame)
        btn_row2.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btn_row2, text="⚡ Gerar do Conceito", style="Accent.TButton",
                   command=self.generate_from_concept).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(btn_row2, text="➕ Mais Variantes",
                   command=lambda: self.generate_from_concept(more=True)).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(left_frame, orient="horizontal").pack(fill=tk.X, pady=12)

        ttk.Label(left_frame, text="MESCLAGEM DE POOLS", font=("Segoe UI", 9, "bold"),
                  foreground=self.colors.get("accent", "#0078D7")).pack(anchor="w", pady=(0, 4))
        ttk.Label(left_frame, text="Pool Base:",
                  font=("Segoe UI", 8), foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.blend_pool1_var = tk.StringVar()
        self.blend_pool1_cb = ttk.Combobox(left_frame, textvariable=self.blend_pool1_var,
                                           state="readonly", font=("Segoe UI", 10),
                                           foreground=self.colors.get("text", "black"))
        self.blend_pool1_cb.pack(fill=tk.X, pady=(2, 6))

        ttk.Label(left_frame, text="Pool Secundário (sufixo / modificador):",
                  font=("Segoe UI", 8), foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.blend_pool2_var = tk.StringVar()
        self.blend_pool2_cb = ttk.Combobox(left_frame, textvariable=self.blend_pool2_var,
                                           state="readonly", font=("Segoe UI", 10),
                                           foreground=self.colors.get("text", "black"))
        self.blend_pool2_cb.pack(fill=tk.X, pady=(2, 6))

        self.blend_mode_var = tk.StringVar(value="composto")
        blend_mode_frame = ttk.Frame(left_frame)
        blend_mode_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(blend_mode_frame, text="Modo:", font=("Segoe UI", 8),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(blend_mode_frame, text="Composto", variable=self.blend_mode_var,
                        value="composto").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Radiobutton(blend_mode_frame, text="Base + sufixo)", variable=self.blend_mode_var,
                        value="basesuffixe").pack(side=tk.LEFT)

        btn_row3 = ttk.Frame(left_frame)
        btn_row3.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(btn_row3, text="🔀 Gerar por Mesclagem", style="Accent.TButton",
                   command=self.generate_blend_names).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        ttk.Button(btn_row3, text="➕ Mais",
                   command=lambda: self.generate_blend_names(more=True)).pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Separator(left_frame, orient="horizontal").pack(fill=tk.X, pady=12)

        ttk.Label(left_frame, text="SUGESTÕES DO CACHÊ", font=("Segoe UI", 9, "bold"),
                  foreground=self.colors.get("accent", "#0078D7")).pack(anchor="w", pady=(0, 4))
        ttk.Label(left_frame, text="Tipo de nome:",
                  font=("Segoe UI", 8), foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.cache_browse_type_var = tk.StringVar(value="(todos)")
        self.cache_browse_type_cb = ttk.Combobox(
            left_frame, textvariable=self.cache_browse_type_var,
            values=["(todos)", "nome_proprio", "nome_e_sobrenome", "sobrenome", "alcunha",
                    "toponimo", "cidade", "regiao", "geografico", "ancestor_names", "house_names"],
            state="readonly", font=("Segoe UI", 10), foreground=self.colors.get("text", "black"))
        self.cache_browse_type_cb.pack(fill=tk.X, pady=(2, 6))
        self.cache_browse_type_var.trace_add(
            "write", lambda *a: self._refresh_cache_suggestions())

        cache_list_frame = ttk.Frame(left_frame)
        cache_list_frame.pack(fill=tk.X, pady=(0, 4))
        self.cache_suggest_listbox = tk.Listbox(
            cache_list_frame, font=("Segoe UI", 11), fg=self.colors.get("text", "black"),
            bg=self.colors.get("input_bg", "#ffffff"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            relief="solid", borderwidth=1, height=6)
        self.cache_suggest_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cache_scroll_sug = ttk.Scrollbar(cache_list_frame, orient="vertical",
                                         command=self.cache_suggest_listbox.yview)
        cache_scroll_sug.pack(side=tk.RIGHT, fill=tk.Y)
        self.cache_suggest_listbox.config(yscrollcommand=cache_scroll_sug.set)
        self.cache_suggest_listbox.bind(
            "<Double-Button-1>", self._on_cache_suggest_double_click)

        right_frame = ttk.LabelFrame(
            main_pane, text="Resultado e Etimologia", padding=20)
        main_pane.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Nome Gerado:", font=("Segoe UI", 10, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        self.entry_name = tk.Entry(right_frame, font=("Segoe UI", 32, "bold"),
                                   fg=self.colors.get("text", "black"),
                                   bg=self.colors.get("input_bg", "#ffffff"),
                                   justify="center", relief="solid", borderwidth=1)
        self.entry_name.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(right_frame, text="Candidatos Gerados (duplo-clique para usar):",
                  font=("Segoe UI", 9, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 4))
        candidates_frame = ttk.Frame(right_frame)
        candidates_frame.pack(fill=tk.X, pady=(0, 12))
        self.candidates_listbox = tk.Listbox(
            candidates_frame, font=("Segoe UI", 13, "bold"),
            fg=self.colors.get("text", "black"),
            bg=self.colors.get("input_bg", "#ffffff"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            relief="solid", borderwidth=1, height=6)
        self.candidates_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cand_scroll = ttk.Scrollbar(candidates_frame, orient="vertical",
                                    command=self.candidates_listbox.yview)
        cand_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.candidates_listbox.config(yscrollcommand=cand_scroll.set)
        self.candidates_listbox.bind(
            "<Double-Button-1>", self._on_candidate_double_click)

        ttk.Label(right_frame, text="Glossário Etimológico:", font=("Segoe UI", 10, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        text_frame = ttk.Frame(right_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        self.text_etymology = tk.Text(text_frame, height=7, bg=self.colors.get("input_bg", "#ffffff"),
                                      fg=self.colors.get("text", "black"),
                                      font=("Consolas", 11), borderwidth=1, relief="solid",
                                      padx=10, pady=10)
        self.text_etymology.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.text_etymology.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_etymology.config(yscrollcommand=scrollbar.set)
        self.text_etymology.configure(state="disabled")

        save_frame = ttk.Frame(right_frame)
        save_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(save_frame, text="Classificação Cultural:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        self.name_type_var = tk.StringVar(value="nome_proprio")
        self.name_type_cb = ttk.Combobox(
            save_frame, textvariable=self.name_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome", "alcunha", "toponimo",
                    "cidade", "regiao", "geografico", "ancestor_names", "house_names"],
            state="normal", width=15)
        self.name_type_cb.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(save_frame, text="💾 Salvar no Cachê",
                   command=self.save_generated_name).pack(side=tk.LEFT)
        ttk.Button(save_frame, text="🗑 Limpar Candidatos",
                   command=self._clear_candidates).pack(side=tk.LEFT, padx=(10, 0))

    def _build_nativizer_tab(self):
        container = ttk.Frame(self.tab_nativizer, padding=40)
        container.pack(fill=tk.BOTH, expand=True)
        input_frame = ttk.LabelFrame(
            container, text="Ajuste e Nativização", padding=25)
        input_frame.pack(fill=tk.X, pady=(0, 30))
        ttk.Label(input_frame, text="Nome Terrestre (Base):", font=("Segoe UI", 11, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))
        self.entry_nativize_base = ttk.Entry(input_frame, font=("Segoe UI", 14),
                                             foreground=self.colors.get("text", "black"))
        self.entry_nativize_base.pack(fill=tk.X, pady=(0, 20))
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="🔄 Nativizar Nome", style="Accent.TButton",
                   command=self.nativize_name).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        ttk.Button(btn_frame, text="➕ Gerar Mais Variantes",
                   command=self.nativize_name_more).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        ttk.Button(btn_frame, text="🎲 Gerar Aleatório (Sem Significado)",
                   command=self.generate_random_name).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(10, 0))
        output_frame = ttk.LabelFrame(
            container, text="Sugestões Nativizadas", padding=25)
        output_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(output_frame, text="Variantes Geradas (duplo-clique para usar):",
                  font=("Segoe UI", 11, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 10))
        list_frame = ttk.Frame(output_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.listbox_nativize_results = tk.Listbox(
            list_frame, font=("Segoe UI", 16, "bold"),
            fg=self.colors.get("text", "black"),
            bg=self.colors.get("input_bg", "#ffffff"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            relief="solid", borderwidth=1, height=10)
        self.listbox_nativize_results.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox_nativize_results.bind(
            "<Double-Button-1>", self._on_nativize_double_click)
        nativize_scroll = ttk.Scrollbar(list_frame, orient="vertical",
                                        command=self.listbox_nativize_results.yview)
        nativize_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox_nativize_results.config(
            yscrollcommand=nativize_scroll.set)
        nativize_action_frame = ttk.Frame(output_frame)
        nativize_action_frame.pack(fill=tk.X)
        ttk.Label(nativize_action_frame, text="Classificação:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        self.nativize_save_type_var = tk.StringVar(value="nome_proprio")
        nativize_type_cb = ttk.Combobox(
            nativize_action_frame, textvariable=self.nativize_save_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome", "alcunha", "toponimo",
                    "cidade", "regiao", "geografico", "ancestor_names", "house_names"],
            state="normal", width=15)
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
        ttk.Label(pool_top, text="Pool Selecionado:", font=("Segoe UI", 11, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT)
        self.pool_var = tk.StringVar()
        self.pool_cb = ttk.Combobox(pool_top, textvariable=self.pool_var, state="readonly",
                                    font=("Segoe UI", 11),
                                    foreground=self.colors.get("fg_secondary", "black"))
        self.pool_cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15)
        self.pool_cb.bind("<<ComboboxSelected>>", self.on_pool_select)
        ttk.Button(pool_top, text="➕ Novo Pool",
                   command=self.create_new_pool).pack(side=tk.RIGHT)
        list_frame = ttk.Frame(self.pool_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.pool_listbox = tk.Listbox(
            list_frame, bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 12), relief="solid", borderwidth=1)
        self.pool_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.pool_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pool_listbox.config(yscrollcommand=scrollbar.set)
        pool_bot = ttk.Frame(self.pool_tab)
        pool_bot.pack(fill=tk.X)
        self.new_word_var = tk.StringVar()
        entry_new_word = ttk.Entry(pool_bot, textvariable=self.new_word_var,
                                   font=("Segoe UI", 12),
                                   foreground=self.colors.get("text", "black"))
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
        self.json_text = tk.Text(
            json_frame, bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"), font=("Consolas", 11),
            insertbackground=self.colors.get("text", "black"),
            relief="solid", borderwidth=1, padx=10, pady=10)
        self.json_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        json_scroll = ttk.Scrollbar(
            json_frame, orient="vertical", command=self.json_text.yview)
        json_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.json_text.config(yscrollcommand=json_scroll.set)
        ttk.Button(self.json_tab, text="✔️ Validar e Salvar JSON", style="Accent.TButton",
                   command=self.save_json_file).pack(pady=10, ipadx=20)

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
            self.blend_pool1_cb['values'] = pools
            self.blend_pool2_cb['values'] = pools
            if pools:
                self.pool_cb.current(0)
                self.blend_pool1_cb.current(0)
                if len(pools) > 1:
                    self.blend_pool2_cb.current(1)
                else:
                    self.blend_pool2_cb.current(0)
            else:
                self.pool_var.set("")

        self.on_pool_select()
        self._refresh_cache_suggestions()

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

    def _refresh_cache_suggestions(self):
        if not hasattr(self, 'cache_suggest_listbox'):
            return
        self.cache_suggest_listbox.delete(0, tk.END)
        if not self.engine:
            return
        type_filter = self.cache_browse_type_var.get()
        names_data = self.engine.gramataki_manager.culture_names
        for n_type, names in names_data.items():
            if type_filter not in ("(todos)", n_type):
                continue
            for name in names:
                self.cache_suggest_listbox.insert(
                    tk.END, f"{name}  [{n_type}]")

    def _on_cache_suggest_double_click(self, event):
        sel = self.cache_suggest_listbox.curselection()
        if not sel:
            return
        raw = self.cache_suggest_listbox.get(sel[0])
        name = raw.split("  [")[0].strip()
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, name)
        self.show_status(f"'{name}' copiado para o campo de nome gerado.")

    def _on_candidate_double_click(self, event):
        sel = self.candidates_listbox.curselection()
        if not sel:
            return
        raw = self.candidates_listbox.get(sel[0])
        name = raw.split("  —")[0].strip()
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, name)
        self.show_status(f"'{name}' selecionado como nome gerado.")

    def _clear_candidates(self):
        self.candidates_listbox.delete(0, tk.END)

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
                self.blend_pool1_cb['values'] = pools
                self.blend_pool2_cb['values'] = pools
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
        if result['name'] and result['name'] not in [self.candidates_listbox.get(i).split("  —")[0].strip()
                                                     for i in range(self.candidates_listbox.size())]:
            etym_summary = " + ".join(e['meaning']
                                      for e in result['etymology'][:3])
            self.candidates_listbox.insert(
                0, f"{result['name']}  — {etym_summary}")

    def generate_from_concept(self, more=False):
        if not self.engine:
            messagebox.showwarning("Aviso", "Motor linguístico não carregado.")
            return
        concept = self.concept_var.get().strip()
        if not concept:
            messagebox.showwarning(
                "Aviso", "Digite um conceito para gerar o nome.")
            return
        existing = set(self.candidates_listbox.get(i).split("  —")[0].strip()
                       for i in range(self.candidates_listbox.size()))
        results = self.engine.gramataki_manager.generate_names_from_concept(
            concept, culture=self.culture_data, count=8)
        added = 0
        first_new = None
        for r in results:
            name = r['name']
            if name and name not in existing:
                self.candidates_listbox.insert(
                    tk.END, f"{name}  — {r.get('etymology', concept)}")
                existing.add(name)
                added += 1
                if first_new is None:
                    first_new = name
        if first_new and not more:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, first_new)
            self.text_etymology.configure(state="normal")
            self.text_etymology.delete("1.0", tk.END)
            self.text_etymology.insert(tk.END, f"Conceito: \"{concept}\"\n")
            first_result = next(
                (r for r in results if r['name'] == first_new), None)
            if first_result and first_result.get('components'):
                for comp in first_result['components']:
                    self.text_etymology.insert(
                        tk.END, f"  {comp['keyword']} → {comp['form']}\n")
            self.text_etymology.configure(state="disabled")
        if added > 0:
            self.show_status(
                f"{added} nome(s) gerado(s) do conceito '{concept}'.")
        else:
            self.show_status(
                "Nenhum novo nome gerado. Tente reformular o conceito.")

    def generate_blend_names(self, more=False):
        if not self.engine:
            messagebox.showwarning("Aviso", "Motor linguístico não carregado.")
            return
        pool1 = self.blend_pool1_var.get()
        pool2 = self.blend_pool2_var.get()
        mode = self.blend_mode_var.get()
        if not pool1:
            messagebox.showwarning("Aviso", "Selecione ao menos um pool base.")
            return
        existing = set(self.candidates_listbox.get(i).split("  —")[0].strip()
                       for i in range(self.candidates_listbox.size()))
        if mode == "basesuffixe":
            results_raw = self.engine.gramataki_manager.generate_basesuffixe_style_names(
                pool1, pool2, self.culture_data, count=12)
            results = [{'name': n, 'etymology': f"{pool1} + {pool2}"}
                       for n in results_raw]
        else:
            pools = [pool1]
            if pool2 and pool2 != pool1:
                pools.append(pool2)
            results = self.engine.gramataki_manager.generate_word_blend_names(
                pools, self.culture_data, count=12)
        added = 0
        first_new = None
        for r in results:
            name = r['name']
            etym = r.get('etymology', '')
            if name and name not in existing:
                self.candidates_listbox.insert(tk.END, f"{name}  — {etym}")
                existing.add(name)
                added += 1
                if first_new is None:
                    first_new = name
        if first_new and not more:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, first_new)
            self.text_etymology.configure(state="normal")
            self.text_etymology.delete("1.0", tk.END)
            self.text_etymology.insert(
                tk.END, f"Modo: {mode}\nPool base: {pool1}\nPool secundário: {pool2}\n")
            self.text_etymology.configure(state="disabled")
        if added > 0:
            self.show_status(f"{added} nome(s) gerado(s) por mesclagem.")
        else:
            self.show_status(
                "Nenhum novo nome gerado. Tente pools diferentes.")

    def save_generated_name(self):
        if not self.engine:
            return
        name = self.entry_name.get().strip()
        name_type = self.name_type_var.get().strip()
        if name and name_type:
            self.engine.gramataki_manager.save_culture_name(name, name_type)
            self._refresh_cache_suggestions()
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
            self._refresh_cache_suggestions()
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
        modal.title("Montagem, Derivação e Gênero de Nomes")
        modal.geometry("1100x740")
        modal.resizable(True, True)
        modal.grab_set()
        modal.configure(bg=self.colors.get("bg", "#f0f0f0"))

        title_lbl = tk.Label(modal, text="Montagem, Derivação e Gênero de Nomes",
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
                     "alcunha", "toponimo", "cidade", "regiao", "geografico", "ancestor_names", "house_names"]
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
            cache_list_frame, bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 11), relief="solid", borderwidth=1, height=18)
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

        right_notebook = ttk.Notebook(right_panel)
        right_notebook.pack(fill=tk.BOTH, expand=True)

        assembly_tab = ttk.Frame(right_notebook, padding=10)
        right_notebook.add(assembly_tab, text="Montagem")

        gender_tab = ttk.Frame(right_notebook, padding=10)
        right_notebook.add(gender_tab, text="Derivação de Gênero / Forma")

        assembly_lf = ttk.LabelFrame(
            assembly_tab, text="Componentes Selecionados", padding=12)
        assembly_lf.pack(fill=tk.X, pady=(0, 10))
        selected_components = []
        comp_list_frame = ttk.Frame(assembly_lf)
        comp_list_frame.pack(fill=tk.X, pady=(0, 8))
        comp_listbox = tk.Listbox(
            comp_list_frame, bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 12), relief="solid", borderwidth=1, height=4)
        comp_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        comp_scroll = ttk.Scrollbar(
            comp_list_frame, orient="vertical", command=comp_listbox.yview)
        comp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        comp_listbox.config(yscrollcommand=comp_scroll.set)
        comp_btn_frame = ttk.Frame(assembly_lf)
        comp_btn_frame.pack(fill=tk.X)

        assembled_lf = ttk.LabelFrame(
            assembly_tab, text="Nome Montado", padding=12)
        assembled_lf.pack(fill=tk.X, pady=(0, 10))
        assembled_var = tk.StringVar()
        assembled_entry = tk.Entry(
            assembled_lf, textvariable=assembled_var, font=(
                "Segoe UI", 22, "bold"),
            fg=self.colors.get("text", "black"), bg=self.colors.get("input_bg", "#ffffff"),
            justify="center", relief="solid", borderwidth=1)
        assembled_entry.pack(fill=tk.X, pady=(0, 10))

        def update_assembled():
            assembled_var.set(" ".join(selected_components))

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

        assembled_save_frame = ttk.Frame(assembled_lf)
        assembled_save_frame.pack(fill=tk.X)
        ttk.Label(assembled_save_frame, text="Salvar como:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        assembled_type_var = tk.StringVar(value="nome_e_sobrenome")
        assembled_type_cb = ttk.Combobox(
            assembled_save_frame, textvariable=assembled_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome", "alcunha", "toponimo",
                    "cidade", "regiao", "geografico", "ancestor_names", "house_names"],
            state="normal", width=15)
        assembled_type_cb.pack(side=tk.LEFT, padx=(0, 10))

        def save_assembled():
            name = assembled_var.get().strip()
            n_type = assembled_type_var.get().strip()
            if not name:
                messagebox.showwarning(
                    "Aviso", "Nenhum nome montado para salvar.", parent=modal)
                return
            self.engine.gramataki_manager.save_culture_name(name, n_type)
            self._refresh_cache_suggestions()
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
            assembly_tab, text="Derivação de Formas Fonológicas", padding=12)
        derivation_lf.pack(fill=tk.BOTH, expand=True)
        deriv_top = ttk.Frame(derivation_lf)
        deriv_top.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(deriv_top, text="Base para derivação:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        deriv_base_var = tk.StringVar()
        deriv_base_entry = ttk.Entry(
            deriv_top, textvariable=deriv_base_var, width=20, font=("Segoe UI", 11))
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

        ttk.Button(deriv_top, text="← Do Cachê", command=fill_deriv_from_cache).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(deriv_top, text="← Do Montado",
                   command=fill_deriv_from_assembled).pack(side=tk.LEFT)

        deriv_result_frame = ttk.Frame(derivation_lf)
        deriv_result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        deriv_listbox = tk.Listbox(
            deriv_result_frame, bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 14, "bold"), relief="solid", borderwidth=1, height=5)
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
        ttk.Label(deriv_action_frame, text="Salvar como:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        deriv_save_type_var = tk.StringVar(value="nome_proprio")
        deriv_save_type_cb = ttk.Combobox(
            deriv_action_frame, textvariable=deriv_save_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome", "alcunha", "toponimo",
                    "cidade", "regiao", "geografico", "ancestor_names", "house_names"],
            state="normal", width=14)
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
            self._refresh_cache_suggestions()
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

        gender_top_frame = ttk.LabelFrame(
            gender_tab, text="Base para Derivação de Gênero", padding=12)
        gender_top_frame.pack(fill=tk.X, pady=(0, 10))

        gender_base_row = ttk.Frame(gender_top_frame)
        gender_base_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(gender_base_row, text="Nome base:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 6))
        gender_base_var = tk.StringVar()
        gender_base_entry = ttk.Entry(gender_base_row, textvariable=gender_base_var,
                                      font=("Segoe UI", 13), width=22)
        gender_base_entry.pack(side=tk.LEFT, padx=(0, 8))

        def fill_gender_from_cache():
            sel = cache_listbox.curselection()
            if not sel:
                return
            raw = cache_listbox.get(sel[0])
            gender_base_var.set(raw.split("  [")[0].strip())

        def fill_gender_from_assembled():
            name = assembled_var.get().strip()
            if name:
                gender_base_var.set(name)

        def fill_gender_from_main():
            name = self.entry_name.get().strip()
            if name:
                gender_base_var.set(name)

        ttk.Button(gender_base_row, text="← Do Cachê",
                   command=fill_gender_from_cache).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(gender_base_row, text="← Do Montado",
                   command=fill_gender_from_assembled).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(gender_base_row, text="← Nome Gerado",
                   command=fill_gender_from_main).pack(side=tk.LEFT)

        gender_rules_info = ttk.LabelFrame(
            gender_top_frame, text="Regras de Gênero da Cultura", padding=8)
        gender_rules_info.pack(fill=tk.X, pady=(4, 0))
        self._gender_rules_text = tk.Text(
            gender_rules_info, height=3, bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"), font=("Consolas", 9),
            relief="flat", state="disabled")
        self._gender_rules_text.pack(fill=tk.X)
        self._update_gender_rules_display()

        gender_buttons_lf = ttk.LabelFrame(
            gender_tab, text="Gerar Formas", padding=12)
        gender_buttons_lf.pack(fill=tk.X, pady=(0, 10))

        gender_btn_row = ttk.Frame(gender_buttons_lf)
        gender_btn_row.pack(fill=tk.X, pady=(0, 8))

        gender_result_listbox_ref = [None]

        def generate_gender_form(target_gender):
            base = gender_base_var.get().strip()
            if not base:
                messagebox.showwarning(
                    "Aviso", "Informe um nome base.", parent=modal)
                return
            lb = gender_result_listbox_ref[0]
            if lb is None:
                return
            existing = set(lb.get(0, tk.END))
            results = self.engine.gramataki_manager.derive_gender_form(
                base, target_gender, self.culture_data)
            added = 0
            for r in results:
                tag = f"{r}  [{target_gender}]"
                if tag not in existing:
                    lb.insert(tk.END, tag)
                    existing.add(tag)
                    added += 1
            if added == 0:
                self.show_status("Nenhuma nova forma derivada.")

        def generate_custom_gender_form():
            custom = simpledialog.askstring("Gênero Personalizado",
                                            "Nome do gênero/forma personalizada:", parent=modal)
            if custom:
                generate_gender_form(custom)

        ttk.Button(gender_btn_row, text="♂ Masculino", style="Accent.TButton",
                   command=lambda: generate_gender_form("Masculino")).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(gender_btn_row, text="♀ Feminino",
                   command=lambda: generate_gender_form("Feminino")).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(gender_btn_row, text="⚬ Neutro",
                   command=lambda: generate_gender_form("Neutro")).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(gender_btn_row, text="✦ Personalizado",
                   command=generate_custom_gender_form).pack(side=tk.LEFT)

        suffix_row = ttk.Frame(gender_buttons_lf)
        suffix_row.pack(fill=tk.X)
        ttk.Label(suffix_row, text="Aplicar sufixo direto:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 6))
        suffix_input_var = tk.StringVar()
        ttk.Entry(suffix_row, textvariable=suffix_input_var, font=(
            "Segoe UI", 11), width=10).pack(side=tk.LEFT, padx=(0, 6))
        suffix_pos_var = tk.StringVar(value="suffix")
        ttk.Radiobutton(suffix_row, text="Sufixo", variable=suffix_pos_var,
                        value="suffix").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Radiobutton(suffix_row, text="Prefixo", variable=suffix_pos_var,
                        value="prefix").pack(side=tk.LEFT, padx=(0, 8))

        def apply_direct_suffix():
            base = gender_base_var.get().strip()
            suf = suffix_input_var.get().strip()
            lb = gender_result_listbox_ref[0]
            if not base or not suf or lb is None:
                return
            suf_clean = suf.replace('-', '')
            if suffix_pos_var.get() == "prefix":
                result = suf_clean + base
            else:
                result = base + suf_clean
            ph = self.engine.phonology_handler
            result = ph.apply_monophthongization(result)
            if self.engine.sandhi_handler.enabled:
                result = self.engine.sandhi_handler.apply_sandhi(result)
            result = result.capitalize()
            tag = f"{result}  [sufixo: {suf}]"
            existing = set(lb.get(0, tk.END))
            if tag not in existing:
                lb.insert(tk.END, tag)
                self.show_status(f"'{result}' adicionado.")

        ttk.Button(suffix_row, text="Aplicar",
                   command=apply_direct_suffix).pack(side=tk.LEFT)

        gender_result_lf = ttk.LabelFrame(
            gender_tab, text="Formas Derivadas", padding=12)
        gender_result_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        gender_res_frame = ttk.Frame(gender_result_lf)
        gender_res_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        gender_result_listbox = tk.Listbox(
            gender_res_frame, bg=self.colors.get("input_bg", "#ffffff"),
            fg=self.colors.get("text", "black"),
            selectbackground=self.colors.get("accent", "#0078D7"),
            font=("Segoe UI", 14, "bold"), relief="solid", borderwidth=1, height=10)
        gender_result_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        gender_result_listbox_ref[0] = gender_result_listbox
        gender_res_scroll = ttk.Scrollbar(gender_res_frame, orient="vertical",
                                          command=gender_result_listbox.yview)
        gender_res_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        gender_result_listbox.config(yscrollcommand=gender_res_scroll.set)

        gender_action_frame = ttk.Frame(gender_result_lf)
        gender_action_frame.pack(fill=tk.X)
        ttk.Label(gender_action_frame, text="Salvar como:", font=("Segoe UI", 9),
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        gender_save_type_var = tk.StringVar(value="nome_proprio")
        ttk.Combobox(
            gender_action_frame, textvariable=gender_save_type_var,
            values=["nome_proprio", "nome_e_sobrenome", "sobrenome", "alcunha", "toponimo",
                    "cidade", "regiao", "geografico", "ancestor_names", "house_names"],
            state="normal", width=14).pack(side=tk.LEFT, padx=(0, 8))

        def save_gender_form():
            sel = gender_result_listbox.curselection()
            if not sel:
                messagebox.showwarning(
                    "Aviso", "Selecione uma forma derivada.", parent=modal)
                return
            raw = gender_result_listbox.get(sel[0])
            name = raw.split("  [")[0].strip()
            n_type = gender_save_type_var.get().strip()
            self.engine.gramataki_manager.save_culture_name(name, n_type)
            self._refresh_cache_suggestions()
            self.show_status(f"'{name}' salvo como '{n_type}'.")
            refresh_cache_list()

        def use_gender_form_as_base():
            sel = gender_result_listbox.curselection()
            if not sel:
                return
            raw = gender_result_listbox.get(sel[0])
            name = raw.split("  [")[0].strip()
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, name)
            self.show_status(f"'{name}' definido como nome gerado.")

        def use_gender_as_component():
            sel = gender_result_listbox.curselection()
            if not sel:
                return
            raw = gender_result_listbox.get(sel[0])
            name = raw.split("  [")[0].strip()
            selected_components.append(name)
            comp_listbox.insert(tk.END, name)
            update_assembled()
            right_notebook.select(0)

        ttk.Button(gender_action_frame, text="💾 Salvar",
                   command=save_gender_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gender_action_frame, text="📋 Usar como Nome Gerado",
                   command=use_gender_form_as_base).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gender_action_frame, text="➕ Usar como Componente",
                   command=use_gender_as_component).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gender_action_frame, text="🗑 Limpar Lista",
                   command=lambda: gender_result_listbox.delete(0, tk.END)).pack(side=tk.LEFT)

        bottom_bar = ttk.Frame(modal, padding=(15, 8))
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(bottom_bar, text="Fechar",
                   command=modal.destroy).pack(side=tk.RIGHT)

    def _update_gender_rules_display(self):
        if not hasattr(self, '_gender_rules_text'):
            return
        self._gender_rules_text.configure(state="normal")
        self._gender_rules_text.delete("1.0", tk.END)
        rules = self.culture_data.get("gender_derivation", {})
        if rules:
            for gender, rule in rules.items():
                affix = rule.get('affix', '')
                pos = rule.get('position', 'suffix')
                strip = rule.get('strip_final_vowel', False)
                line = f"{gender}: afixo='{affix}' posição={pos}"
                if strip:
                    line += " (remove vogal final)"
                self._gender_rules_text.insert(tk.END, line + "\n")
        else:
            self._gender_rules_text.insert(
                tk.END,
                "Nenhuma regra de gênero definida na cultura.\n"
                "Adicione 'gender_derivation' ao JSON da cultura para regras explícitas.\n"
                "Exemplo: {\"Feminino\": {\"position\": \"suffix\", \"affix\": \"ia\", \"strip_final_vowel\": true}}"
            )
        self._gender_rules_text.configure(state="disabled")


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
        return {'name': final_name, 'etymology': etymology}

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
        if rel_type == 'literal':
            val = rule.get('value', '')
            return {'word': val, 'meaning': rule.get('meaning', val)}
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
        return {
            'word': self.engine._generate_word_from_seed(
                comp_name, self.engine.global_seed + random.randint(1, 1000)),
            'meaning': 'Desconhecido'
        }

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

    def generate_names_from_concept(self, concept_phrase, culture=None, count=8):
        stop_words = {
            'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das',
            'um', 'uma', 'uns', 'umas', 'em', 'no', 'na', 'nos', 'nas',
            'por', 'para', 'com', 'que', 'e', 'ou', 'the', 'of', 'and',
            'a', 'an', 'in', 'on', 'at', 'for', 'to', 'by', 'is', 'são',
            'é', 'ser', 'estar', 'se'
        }
        results = []
        seen = set()

        if culture and 'dynamic_patterns' in culture:
            for pat in culture['dynamic_patterns']:
                match = re.match(pat.get('pattern', ''),
                                 concept_phrase, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    fmt = pat.get('format', '')
                    for attempt in range(count * 4):
                        translated_groups = []
                        all_comp_info = []
                        for g in groups:
                            g_words = re.split(r'[\s\-_]+', g.strip())
                            g_kws = [re.sub(r'[^\w]', '', w) for w in g_words if w and re.sub(
                                r'[^\w]', '', w).lower() not in stop_words]
                            if not g_kws:
                                g_kws = [g.strip()]
                            rng = random.Random(
                                int(hashlib.sha256(f"{g}_{attempt}".encode()).hexdigest(), 16))
                            num_kw = rng.randint(
                                1, min(3, len(g_kws))) if len(g_kws) > 0 else 0
                            chosen_kw = rng.sample(g_kws, num_kw) if len(
                                g_kws) >= num_kw else g_kws[:]
                            parts = []
                            for kw in chosen_kw:
                                form = self.engine._get_word_form(
                                    kw, skip_cache=True)
                                if form:
                                    parts.append(form)
                                    all_comp_info.append(
                                        {'keyword': kw, 'form': form})
                            if self.engine.compounding_handler.enabled and len(parts) > 1:
                                g_trans = self.engine.compounding_handler.construct_compound(
                                    parts, self.engine)
                            else:
                                g_trans = "".join(parts)
                            translated_groups.append(g_trans.capitalize())
                        final_str = fmt.format(*translated_groups)
                        if self.engine.sandhi_handler.enabled:
                            final_str = self.engine.sandhi_handler.apply_sandhi(
                                final_str)
                        final_name = " ".join(p.capitalize()
                                              for p in final_str.split())
                        if final_name not in seen and len(final_name) > 1:
                            results.append({
                                'name': final_name,
                                'etymology': pat.get('description', 'Padrão Dinâmico') + " (" + " + ".join(c['keyword'] for c in all_comp_info) + ")",
                                'components': all_comp_info
                            })
                            seen.add(final_name)
                        if len(results) >= count:
                            break
                    if results:
                        return results

        words = re.split(r'[\s\-_]+', concept_phrase.lower().strip())
        keywords = [re.sub(r'[^\w]', '', w) for w in words
                    if w and re.sub(r'[^\w]', '', w) not in stop_words
                    and len(re.sub(r'[^\w]', '', w)) > 1]
        if not keywords:
            keywords = [re.sub(r'[^\w]', '', concept_phrase.lower().strip())]
        keywords = keywords[:4]

        for attempt in range(count * 4):
            rng = random.Random(int(hashlib.sha256(
                f"{concept_phrase}_concept_{attempt}".encode()).hexdigest(), 16))
            num_kw = rng.randint(1, min(3, len(keywords)))
            chosen_kw = rng.sample(keywords, num_kw) if len(
                keywords) >= num_kw else keywords[:]
            conlang_parts = []
            component_info = []
            for kw in chosen_kw:
                form = self.engine._get_word_form(kw, skip_cache=True)
                if form:
                    conlang_parts.append(form)
                    component_info.append({'keyword': kw, 'form': form})
            if not conlang_parts:
                continue
            if self.engine.compounding_handler.enabled and len(conlang_parts) > 1:
                result_word = self.engine.compounding_handler.construct_compound(
                    conlang_parts, self.engine)
            else:
                result_word = "".join(conlang_parts)
            if self.engine.sandhi_handler.enabled:
                result_word = self.engine.sandhi_handler.apply_sandhi(
                    result_word)
            result_word = result_word.capitalize()
            if result_word and result_word not in seen and len(result_word) >= 2:
                results.append({
                    'name': result_word,
                    'etymology': " + ".join(c['keyword'] for c in component_info),
                    'components': component_info
                })
                seen.add(result_word)
            if len(results) >= count:
                break
        return results

    def generate_basesuffixe_style_names(self, base_pool_key, suffix_pool_key, culture=None, count=12):
        base_words = []
        suffix_entries = []
        if culture:
            base_words = self._get_pool_words(base_pool_key, culture)
            cultural_suffixes = culture.get('cultural_suffixes', {})
            if suffix_pool_key in cultural_suffixes:
                suffix_entries = cultural_suffixes[suffix_pool_key]
            else:
                suffix_entries = self._get_pool_words(suffix_pool_key, culture)
        if not base_words:
            base_words = list(self.unified_pools.get(base_pool_key, []))
        if not suffix_entries:
            suffix_entries = list(self.unified_pools.get(suffix_pool_key, []))

        if not base_words and not suffix_entries:
            return []

        results = []
        seen = set()
        ph = self.engine.phonology_handler
        attempts = 0
        max_attempts = count * 12

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            rng = random.Random(int(hashlib.sha256(
                f"ashk_{base_pool_key}_{suffix_pool_key}_{attempts}".encode()).hexdigest(), 16))

            base_word = rng.choice(base_words) if base_words else ""
            suffix_raw = rng.choice(suffix_entries) if suffix_entries else ""

            if base_word:
                conlang_base = self.engine._get_word_form(
                    base_word, skip_cache=True)
            else:
                conlang_base = ""

            if suffix_raw:
                suf_clean = suffix_raw.replace('-', '').strip()
                if len(suf_clean) <= 6 or suffix_raw.startswith('-'):
                    conlang_suffix = suf_clean
                else:
                    conlang_suffix = self.engine._get_word_form(
                        suffix_raw, skip_cache=True)
            else:
                conlang_suffix = ""

            if not conlang_base and not conlang_suffix:
                continue

            parts = [p for p in [conlang_base, conlang_suffix] if p]

            if self.engine.compounding_handler.enabled and len(parts) > 1:
                result = self.engine.compounding_handler.construct_compound(
                    parts, self.engine)
            else:
                result = "".join(parts)

            result = ph.apply_monophthongization(result)
            if self.engine.sandhi_handler.enabled:
                result = self.engine.sandhi_handler.apply_sandhi(result)
            result = result.capitalize()

            if result and result not in seen and len(result) >= 2:
                results.append(result)
                seen.add(result)

        return results

    def generate_word_blend_names(self, pool_keys, culture=None, count=12):
        all_pool_words = []
        for pk in pool_keys:
            if culture:
                words = self._get_pool_words(pk, culture)
            else:
                words = list(self.unified_pools.get(pk, []))
            all_pool_words.extend([(w, pk) for w in words])

        if not all_pool_words:
            return []

        results = []
        seen = set()
        ph = self.engine.phonology_handler
        attempts = 0
        max_attempts = count * 15

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            rng = random.Random(int(hashlib.sha256(
                f"blend_{'_'.join(pool_keys)}_{attempts}".encode()).hexdigest(), 16))

            num_parts = rng.randint(2, min(3, len(all_pool_words)))
            chosen = rng.sample(all_pool_words, num_parts)

            conlang_parts = []
            meanings = []
            for word, pool in chosen:
                form = self.engine._get_word_form(word, skip_cache=True)
                if form:
                    conlang_parts.append(form)
                    meanings.append(word)

            if len(conlang_parts) < 1:
                continue

            if self.engine.compounding_handler.enabled and len(conlang_parts) > 1:
                result = self.engine.compounding_handler.construct_compound(
                    conlang_parts, self.engine)
            else:
                result = "".join(conlang_parts)

            result = ph.apply_monophthongization(result)
            if self.engine.sandhi_handler.enabled:
                result = self.engine.sandhi_handler.apply_sandhi(result)
            result = result.capitalize()

            if result and result not in seen and len(result) >= 3:
                results.append(
                    {'name': result, 'etymology': ' + '.join(meanings)})
                seen.add(result)

        return results

    def derive_gender_form(self, name, target_gender, culture=None):
        results = []
        seen = set()
        seen.add(name)
        ph = self.engine.phonology_handler
        vowels_list = list(ph.vowels) if ph.vowels else list("aeiou")
        consonants_list = list(ph.consonants) if ph.consonants else []

        gender_rules = {}
        if culture:
            gender_rules = culture.get('gender_derivation', {})

        if target_gender in gender_rules:
            rule = gender_rules[target_gender]
            affix = rule.get('affix', '')
            position = rule.get('position', 'suffix')
            strip_vowel = rule.get('strip_final_vowel', False)
            base = name
            if strip_vowel and base and base[-1].lower() in (ph.vowels or 'aeiou'):
                base = base[:-1]
            if position == 'suffix':
                candidate = base + affix
            elif position == 'prefix':
                candidate = affix + base
            else:
                candidate = base + affix
            candidate = ph.apply_monophthongization(candidate)
            if self.engine.sandhi_handler.enabled:
                candidate = self.engine.sandhi_handler.apply_sandhi(candidate)
            candidate = candidate.capitalize()
            if candidate and candidate not in seen:
                results.append(candidate)
                seen.add(candidate)

        gender_vowel_pools = {
            'Feminino': [v for v in vowels_list if v in 'aáéiíy'] or vowels_list[:max(1, len(vowels_list)//2)],
            'Masculino': [v for v in vowels_list if v in 'ouóú'] or vowels_list[max(0, len(vowels_list)//2):],
            'Neutro': vowels_list
        }
        target_vowels = gender_vowel_pools.get(target_gender, vowels_list)
        if not target_vowels:
            target_vowels = vowels_list

        gender_suffix_pools = {
            'Feminino': ['a', 'ia', 'ina', 'ina', 'elle', 'ette', 'issa'],
            'Masculino': ['os', 'us', 'or', 'an', 'on', 'ar'],
            'Neutro': ['e', 'en', 'im', 'um', 'al']
        }
        base_suffixes = gender_suffix_pools.get(target_gender, ['a'])

        phonologically_valid = [s for s in base_suffixes
                                if not s or ph.is_valid_final(s[-1])]
        if not phonologically_valid:
            phonologically_valid = base_suffixes

        strategies = [
            'replace_final_vowel',
            'add_gender_suffix',
            'replace_final_vowel',
            'strip_and_add_suffix',
            'change_internal_vowel',
            'add_gender_suffix',
            'strip_and_add_suffix',
            'replace_final_cluster',
        ]

        attempts = 0
        max_attempts = 60

        while len(results) < 12 and attempts < max_attempts:
            attempts += 1
            rng = random.Random(int(hashlib.sha256(
                f"{name}_gender_{target_gender}_{attempts}".encode()).hexdigest(), 16))

            strategy = rng.choice(strategies)
            base = name.lower().strip()
            candidate = base

            if strategy == 'replace_final_vowel' and target_vowels:
                stem = base.rstrip(
                    ''.join(ph.vowels or 'aeiou')) if base else base
                if not stem:
                    stem = base[:-1] if len(base) > 1 else base
                candidate = stem + rng.choice(target_vowels)

            elif strategy == 'add_gender_suffix' and phonologically_valid:
                suf = rng.choice(phonologically_valid)
                stem = base.rstrip(
                    ''.join(ph.vowels or 'aeiou')) if base else base
                if not stem:
                    stem = base
                candidate = stem + suf

            elif strategy == 'strip_and_add_suffix' and len(base) >= 3 and phonologically_valid:
                cut = rng.randint(max(1, len(base) - 2), len(base) - 1)
                stem = base[:cut]
                suf = rng.choice(phonologically_valid)
                candidate = stem + suf

            elif strategy == 'change_internal_vowel' and len(base) >= 3:
                vowel_idxs = [i for i, c in enumerate(
                    base) if c in (ph.vowels or 'aeiou')]
                if vowel_idxs and target_vowels:
                    idx = rng.choice(
                        vowel_idxs[:-1] if len(vowel_idxs) > 1 else vowel_idxs)
                    opts = [v for v in target_vowels if v != base[idx]]
                    if opts:
                        chars = list(base)
                        chars[idx] = rng.choice(opts)
                        candidate = "".join(chars)

            elif strategy == 'replace_final_cluster' and len(base) >= 3:
                stem = base[:-2] if len(base) > 2 else base[:-1]
                suf = rng.choice(phonologically_valid) if phonologically_valid else rng.choice(
                    target_vowels)
                candidate = stem + suf

            candidate = ph.apply_monophthongization(candidate)
            if candidate and not ph.is_valid_final(candidate[-1]):
                valid_finals = [
                    c for c in consonants_list if ph.is_valid_final(c)] + vowels_list
                if valid_finals:
                    candidate = candidate[:-1] + rng.choice(valid_finals)

            if self.engine.sandhi_handler.enabled:
                candidate = self.engine.sandhi_handler.apply_sandhi(candidate)

            candidate = candidate.capitalize() if candidate else ''

            if candidate and candidate not in seen and len(candidate) >= 2:
                results.append(candidate)
                seen.add(candidate)

        return results

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
                    kw, int(hashlib.sha256(f"{kw}_{seed}".encode()).hexdigest(), 16))
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
                f"{name}_multi_{attempts}_{len(results)}".encode()).hexdigest(), 16)
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
            "change_suffix_vowel", "change_suffix_consonant", "swap_internal_vowel",
            "add_vowel_suffix", "add_consonant_suffix", "truncate_and_extend",
            "swap_final_consonant", "insert_medial_vowel", "change_initial_cluster",
            "double_final_vowel",
        ]
        attempts = 0
        max_attempts = count * 10
        while len(results) < count and attempts < max_attempts:
            attempts += 1
            seed_val = int(hashlib.sha256(
                f"{name}_deriv_{attempts}".encode()).hexdigest(), 16)
            rng = random.Random(seed_val)
            strategy = rng.choice(strategies)
            base = name.lower().strip()
            candidate = base
            if strategy == "change_suffix_vowel" and len(base) >= 2:
                stem = base[:-1]
                if vowels_list:
                    candidate = stem + rng.choice(vowels_list)
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
