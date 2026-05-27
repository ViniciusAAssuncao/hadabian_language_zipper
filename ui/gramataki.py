import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path
import random
import hashlib
import re
from constants import PORTUGUESE_STOP_WORDS


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