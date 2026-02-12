import tkinter as tk
from tkinter import ttk
import hashlib
import random


class EditWordModal(tk.Toplevel):
    def __init__(self, parent, colors, lemma, current_data, engine, on_save):
        super().__init__(parent)
        self.colors = colors
        self.lemma = lemma
        self.current_data = current_data
        self.engine = engine
        self.on_save = on_save
        self.generation_counter = 0
        self.source_engine = None
        self.source_id = None
        self.parent_word_data = None
        self.rng = random.Random()

        self.title("Editar Palavra")
        self.geometry("500x750")
        self.configure(bg=self.colors["bg_main"])
        self.transient(parent)
        self.grab_set()

        self._detect_confluence()
        self.setup_ui()

        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

    def _detect_confluence(self):
        origin = self.current_data.get("origin", "")
        if origin.startswith("confluence_"):
            self.source_id = origin.replace("confluence_", "")
        else:
            tags = []
            synsets = self.current_data.get("synsets", [])
            for s in synsets:
                tags.extend(s.get("tags", []))
            for t in tags:
                if t.startswith("source:"):
                    self.source_id = t.split(":")[1]
                    break

        if self.source_id:
            self.engine._fetch_source_word(self.source_id, self.lemma)
            if self.source_id in self.engine.source_engines:
                self.source_engine = self.engine.source_engines[self.source_id]
                if self.lemma in self.source_engine.word_cache:
                    self.parent_word_data = self.source_engine.word_cache[self.lemma]
                else:
                    parent_word = self.source_engine._get_word_form(self.lemma)
                    self.source_engine.save_word_cache()
                    self.parent_word_data = {
                        "lemma": self.lemma,
                        "default": parent_word,
                        "synsets": [{"word": parent_word, "tags": ["auto_gen"], "affinity": 1.0}]
                    }

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text=f"Editando: {self.lemma}",
            font=("Segoe UI", 14, "bold"),
            foreground=self.colors["accent"]
        ).pack(anchor="w", pady=(0, 20))

        if self.source_engine:
            self._setup_parent_ui(main_frame)

        ttk.Label(
            main_frame,
            text="Tradução (Conlang):",
            font=("Segoe UI", 10),
            foreground=self.colors["fg_secondary"]
        ).pack(anchor="w", pady=(0, 5))

        self.entry_word = ttk.Entry(
            main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
        self.entry_word.pack(fill=tk.X, pady=(0, 15))

        initial_word = self.current_data.get("default", "") if isinstance(
            self.current_data, dict) else str(self.current_data)
        self.entry_word.insert(0, initial_word)

        ttk.Label(
            main_frame,
            text="Origem Etimológica:",
            font=("Segoe UI", 10),
            foreground=self.colors["fg_secondary"]
        ).pack(anchor="w", pady=(0, 5))

        self.entry_origin = ttk.Entry(
            main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
        self.entry_origin.pack(fill=tk.X, pady=(0, 15))

        initial_origin = self.current_data.get("origin", "") if isinstance(
            self.current_data, dict) else "custom"
        self.entry_origin.insert(0, initial_origin)

        gen_frame = ttk.LabelFrame(
            main_frame, text="Gerar Nova Sugestão", padding=15)
        gen_frame.pack(fill=tk.X, pady=(10, 20))

        ttk.Label(gen_frame, text="Método de Geração:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")

        self.strategy_var = tk.StringVar(value="phonotactics")
        strategies = [
            ("Fonotática (Aleatório)", "phonotactics"),
            ("Sistema de Raízes", "triconsonantal_system"),
            ("Derivação (Afixos)", "derived"),
            ("Nativizar Lemma", "nativization"),
            ("Mutação (Evolução)", "mutation"),
            ("Semântica (Conceito)", "semantic"),
        ]

        self.combo_strategy = ttk.Combobox(
            gen_frame,
            textvariable=self.strategy_var,
            values=[s[0] for s in strategies],
            state="readonly"
        )
        self.combo_strategy.current(0)
        self.combo_strategy.pack(fill=tk.X, pady=(5, 10))

        self.map_strategy = {s[0]: s[1] for s in strategies}

        ttk.Button(
            gen_frame,
            text="↻ Gerar Nova Palavra",
            style="Secondary.TButton",
            command=self.generate_new_suggestion
        ).pack(fill=tk.X)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0), side=tk.BOTTOM)

        ttk.Button(
            btn_frame,
            text="Salvar Alterações",
            command=self.save
        ).pack(fill=tk.X)

        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self.destroy
        ).pack(fill=tk.X, pady=(10, 0))

    def _setup_parent_ui(self, parent_frame):
        parent_group = ttk.LabelFrame(
            parent_frame, text=f"Palavra Mãe (Origem: {self.source_id.upper()})", padding=10)
        parent_group.pack(fill=tk.X, pady=(0, 20))

        row = ttk.Frame(parent_group)
        row.pack(fill=tk.X)

        self.entry_parent = ttk.Entry(row, font=(
            "Segoe UI", 11), foreground=self.colors["text"])
        self.entry_parent.pack(side=tk.LEFT, fill=tk.X,
                               expand=True, padx=(0, 5))

        parent_val = self.parent_word_data.get("default", "") if isinstance(
            self.parent_word_data, dict) else str(self.parent_word_data)
        self.entry_parent.insert(0, parent_val)

        ttk.Button(row, text="↻", width=3,
                   command=self.generate_parent_suggestion).pack(side=tk.RIGHT)

    def generate_parent_suggestion(self):
        if not self.source_engine:
            return

        self.generation_counter += 1
        seed_to_use = self.rng.randint(0, 999999)
        new_parent = self.source_engine._generate_word_from_seed(
            self.lemma,
            seed_to_use
        )

        if hasattr(self.source_engine, 'special_mechanics_handler') and self.source_engine.special_mechanics_handler and self.source_engine.special_mechanics_handler.enabled:
            new_parent = self.source_engine.special_mechanics_handler.apply_mechanics(
                new_parent, self.lemma, seed_to_use)

        self.entry_parent.delete(0, tk.END)
        self.entry_parent.insert(0, new_parent)

    def generate_new_suggestion(self):
        if not self.engine:
            return

        display_strat = self.combo_strategy.get()
        strategy_key = self.map_strategy.get(display_strat, "phonotactics")

        self.generation_counter += 1
        new_word = ""
        origin_tag = strategy_key

        clean_lemma = "".join(filter(str.isalpha, self.lemma.lower()))

        def generate_fallback():
            seed = self.rng.randint(0, 9999999)
            word = self.engine._generate_word_from_seed(clean_lemma, seed)
            if self.engine.phonology_handler:
                word = self.engine.phonology_handler.apply_monophthongization(
                    word)
            return word

        if self.source_engine and self.entry_parent.get() and strategy_key == "nativization":
            parent_word = self.entry_parent.get()
            nativized = self.engine.phonology_handler.nativize_word(
                parent_word)

            if self.generation_counter > 0:
                mutation_seed = self.rng.randint(0, 999999)
                nativized = self.engine._mutate_word(nativized, mutation_seed)

            new_word = nativized
            origin_tag = f"confluence_{self.source_id}"

        elif strategy_key == "phonotactics":
            seed = self.rng.randint(0, 9999999)
            new_word = self.engine._generate_word_from_seed(clean_lemma, seed)
            if self.engine.phonology_handler:
                new_word = self.engine.phonology_handler.apply_monophthongization(
                    new_word)

        elif strategy_key == "triconsonantal_system":
            if self.engine.root_handler and self.engine.root_handler.enabled:
                root = []
                if self.generation_counter % 2 == 0:
                    root = self.engine.root_handler.generate_root(self.lemma)
                else:
                    root = self.engine.root_handler.generate_root(
                        str(self.rng.random()))

                binyanim = self.engine.root_handler.binyanim
                pattern_def = None
                if binyanim:
                    pattern_def = self.rng.choice(binyanim)

                if pattern_def:
                    new_word = self.engine.root_handler.apply_pattern(
                        root, pattern_def)
                else:
                    new_word = "".join(root)
            else:
                new_word = generate_fallback()

        elif strategy_key == "derived":
            if self.engine.affix_handler and self.engine.affix_handler.source_suffixes:
                base_word = self.entry_word.get()
                if not base_word:
                    base_word = generate_fallback()

                rule = self.rng.choice(
                    self.engine.affix_handler.source_suffixes)
                if rule:
                    affix = rule.get('replacement', '')
                    if not affix:
                        affix = rule.get('affix', '')

                    if affix:
                        if self.rng.random() > 0.5:
                            new_word = f"{base_word}{affix}"
                        else:
                            new_word = f"{affix}{base_word}"

                        if self.engine.phonology_handler:
                            new_word = self.engine.phonology_handler.nativize_word(
                                new_word)
                    else:
                        new_word = generate_fallback()
                else:
                    new_word = generate_fallback()
            else:
                new_word = generate_fallback()

        elif strategy_key == "nativization":
            if self.engine.phonology_handler:
                base_nat = self.engine.phonology_handler.nativize_word(
                    self.lemma)
                seed = self.rng.randint(0, 999999)
                new_word = self.engine._mutate_word(base_nat, seed)
            else:
                new_word = generate_fallback()

        elif strategy_key == "mutation":
            current_val = self.entry_word.get()
            if current_val:
                seed = self.rng.randint(0, 999999)
                new_word = self.engine._mutate_word(current_val, seed)
            else:
                new_word = generate_fallback()

        elif strategy_key == "semantic":
            if self.engine.concept_handler and self.engine.concept_handler.enabled:
                res = self.engine.concept_handler.resolve_concept(
                    self.lemma, self.engine)
                if res:
                    new_word = res[0]
                    origin_tag = res[1]
                else:
                    new_word = generate_fallback()
            else:
                new_word = generate_fallback()

        if new_word and hasattr(self.engine, 'special_mechanics_handler') and self.engine.special_mechanics_handler and self.engine.special_mechanics_handler.enabled:
            seed_to_use = self.engine.global_seed + self.generation_counter
            new_word = self.engine.special_mechanics_handler.apply_mechanics(
                new_word, clean_lemma, seed_to_use)

        if new_word:
            self.entry_word.delete(0, tk.END)
            self.entry_word.insert(0, new_word)
            self.entry_origin.delete(0, tk.END)
            self.entry_origin.insert(0, origin_tag)

    def save(self):
        new_word = self.entry_word.get().strip()
        new_origin = self.entry_origin.get().strip()

        if self.source_engine:
            parent_val = self.entry_parent.get().strip()
            if parent_val:
                parent_entry = {
                    "lemma": self.lemma,
                    "default": parent_val,
                    "synsets": [{"word": parent_val, "tags": ["manual_edit"], "affinity": 1.0}]
                }
                self.source_engine.word_cache[self.lemma] = parent_entry
                self.source_engine.save_word_cache()

        if not new_word:
            return

        updated_data = {
            "lemma": self.lemma,
            "default": new_word,
            "origin": new_origin,
            "synsets": [{"word": new_word, "tags": ["manual_edit", new_origin], "affinity": 1.0}]
        }

        self.on_save(self.lemma, updated_data)
        self.destroy()


class EditSynsetModal(tk.Toplevel):
    def __init__(self, parent, colors, lemma, synset_data, engine, on_save):
        super().__init__(parent)
        self.colors = colors
        self.lemma = lemma
        self.synset_data = synset_data
        self.engine = engine
        self.on_save = on_save
        self.generation_counter = 0
        self.rng = random.Random()

        self.title(f"Editar Variação: {lemma}")
        self.geometry("450x700")
        self.configure(bg=self.colors["bg_main"])
        self.transient(parent)
        self.grab_set()

        self.setup_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame, text="Palavra (Variação):",
            foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))

        self.entry_word = ttk.Entry(
            main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
        self.entry_word.pack(fill=tk.X, pady=(0, 15))
        self.entry_word.insert(0, self.synset_data.get("word", ""))

        ttk.Label(
            main_frame, text="Afinidade (0.0 a 1.0):",
            foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))

        self.entry_affinity = ttk.Entry(
            main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
        self.entry_affinity.pack(fill=tk.X, pady=(0, 15))
        self.entry_affinity.insert(
            0, str(self.synset_data.get("affinity", 1.0)))

        ttk.Label(
            main_frame, text="Classe Gramatical (POS):",
            foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))

        self.entry_pos = ttk.Entry(
            main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
        self.entry_pos.pack(fill=tk.X, pady=(0, 15))
        self.entry_pos.insert(0, self.synset_data.get("pos", ""))

        ttk.Label(
            main_frame, text="Tags (separadas por vírgula):",
            foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))

        self.entry_tags = ttk.Entry(
            main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
        self.entry_tags.pack(fill=tk.X, pady=(0, 15))

        current_tags = self.synset_data.get("tags", [])
        if isinstance(current_tags, list):
            self.entry_tags.insert(0, ", ".join(current_tags))
        else:
            self.entry_tags.insert(0, str(current_tags))

        gen_frame = ttk.LabelFrame(
            main_frame, text="Gerar Sugestão", padding=15)
        gen_frame.pack(fill=tk.X, pady=(10, 20))

        ttk.Label(gen_frame, text="Método de Geração:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")

        self.strategy_var = tk.StringVar(value="phonotactics")
        strategies = [
            ("Fonotática (Aleatório)", "phonotactics"),
            ("Sistema de Raízes", "triconsonantal_system"),
            ("Derivação (Afixos)", "derived"),
            ("Nativizar Lemma", "nativization"),
            ("Mutação (Evolução)", "mutation"),
        ]

        self.combo_strategy = ttk.Combobox(
            gen_frame,
            textvariable=self.strategy_var,
            values=[s[0] for s in strategies],
            state="readonly"
        )
        self.combo_strategy.current(0)
        self.combo_strategy.pack(fill=tk.X, pady=(5, 10))

        self.map_strategy = {s[0]: s[1] for s in strategies}

        ttk.Button(
            gen_frame,
            text="↻ Gerar Sugestão de Palavra",
            style="Secondary.TButton",
            command=self.generate_suggestion
        ).pack(fill=tk.X)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0), side=tk.BOTTOM)

        ttk.Button(
            btn_frame, text="Salvar Variação", command=self.save
        ).pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            btn_frame, text="Cancelar", command=self.destroy
        ).pack(fill=tk.X)

    def generate_suggestion(self):
        if not self.engine:
            return

        display_strat = self.combo_strategy.get()
        strategy_key = self.map_strategy.get(display_strat, "phonotactics")

        self.generation_counter += 1
        new_word = ""
        origin_tag = strategy_key

        clean_lemma = "".join(filter(str.isalpha, self.lemma.lower()))

        def generate_fallback():
            seed = self.rng.randint(0, 9999999)
            word = self.engine._generate_word_from_seed(clean_lemma, seed)
            if self.engine.phonology_handler:
                word = self.engine.phonology_handler.apply_monophthongization(
                    word)
            return word

        if strategy_key == "phonotactics":
            seed = self.rng.randint(0, 9999999)
            new_word = self.engine._generate_word_from_seed(clean_lemma, seed)
            if self.engine.phonology_handler:
                new_word = self.engine.phonology_handler.apply_monophthongization(
                    new_word)

        elif strategy_key == "triconsonantal_system":
            if self.engine.root_handler and self.engine.root_handler.enabled:
                root = self.engine.root_handler.generate_root(self.lemma)
                binyanim = self.engine.root_handler.binyanim
                pattern_def = None
                if binyanim:
                    pattern_def = self.rng.choice(binyanim)

                if pattern_def:
                    new_word = self.engine.root_handler.apply_pattern(
                        root, pattern_def)
                else:
                    new_word = "".join(root)
            else:
                new_word = generate_fallback()

        elif strategy_key == "derived":
            if self.engine.affix_handler and self.engine.affix_handler.source_suffixes:
                base_word = self.entry_word.get()
                if not base_word:
                    base_word = generate_fallback()

                rule = self.rng.choice(
                    self.engine.affix_handler.source_suffixes)
                if rule:
                    affix = rule.get(
                        'replacement', '') or rule.get('affix', '')
                    if affix:
                        if self.rng.random() > 0.5:
                            new_word = f"{base_word}{affix}"
                        else:
                            new_word = f"{affix}{base_word}"
                        if self.engine.phonology_handler:
                            new_word = self.engine.phonology_handler.nativize_word(
                                new_word)
                    else:
                        new_word = generate_fallback()
                else:
                    new_word = generate_fallback()
            else:
                new_word = generate_fallback()

        elif strategy_key == "nativization":
            if self.engine.phonology_handler:
                base_nat = self.engine.phonology_handler.nativize_word(
                    self.lemma)
                seed = self.rng.randint(0, 999999)
                new_word = self.engine._mutate_word(base_nat, seed)
            else:
                new_word = generate_fallback()

        elif strategy_key == "mutation":
            current_val = self.entry_word.get()
            if current_val:
                seed = self.rng.randint(0, 999999)
                new_word = self.engine._mutate_word(current_val, seed)
            else:
                new_word = generate_fallback()

        if new_word and hasattr(self.engine, 'special_mechanics_handler') and self.engine.special_mechanics_handler and self.engine.special_mechanics_handler.enabled:
            seed_to_use = self.engine.global_seed + self.generation_counter
            new_word = self.engine.special_mechanics_handler.apply_mechanics(
                new_word, clean_lemma, seed_to_use)

        if new_word:
            self.entry_word.delete(0, tk.END)
            self.entry_word.insert(0, new_word)

        current_tags = self.entry_tags.get()
        if origin_tag not in current_tags:
            if current_tags:
                self.entry_tags.delete(0, tk.END)
                self.entry_tags.insert(0, f"{current_tags}, {origin_tag}")
            else:
                self.entry_tags.insert(0, origin_tag)

    def save(self):
        word = self.entry_word.get().strip()
        if not word:
            return

        try:
            affinity = float(self.entry_affinity.get().strip())
        except ValueError:
            affinity = 1.0

        tags_str = self.entry_tags.get().strip()
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]

        new_data = {
            "word": word,
            "affinity": affinity,
            "pos": self.entry_pos.get().strip(),
            "tags": tags_list
        }

        self.on_save(new_data)
        self.destroy()
