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

        self.title("Editar Palavra")
        self.geometry("450x550")
        self.configure(bg=self.colors["bg_main"])
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

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
            main_frame,
            text=f"Editando: {self.lemma}",
            font=("Segoe UI", 14, "bold"),
            foreground=self.colors["accent"]
        ).pack(anchor="w", pady=(0, 20))

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
            ("Fonotática (Padrão)", "phonotactics"),
            ("Sistema de Raízes", "triconsonantal_system"),
            ("Composição/Derivação", "derived"),
            ("Nativizar", "nativization"),
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
            input_str = f"{clean_lemma}_manual_fallback_{self.generation_counter}_{self.engine.global_seed}"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)
            word = self.engine._generate_word_from_seed(clean_lemma, hash_val)
            if self.engine.phonology_handler:
                word = self.engine.phonology_handler.apply_monophthongization(
                    word)
            return word

        if strategy_key == "phonotactics":
            input_str = f"{clean_lemma}_manual_gen_{self.generation_counter}_{self.engine.global_seed}"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)

            new_word = self.engine._generate_word_from_seed(
                clean_lemma, hash_val)
            if self.engine.phonology_handler:
                new_word = self.engine.phonology_handler.apply_monophthongization(
                    new_word)

        elif strategy_key == "triconsonantal_system":
            if self.engine.root_handler and self.engine.root_handler.enabled:
                root = self.engine.root_handler.generate_root(self.lemma)

                binyanim = self.engine.root_handler.binyanim
                pattern_def = None
                if binyanim:
                    rng_seed = self.engine.global_seed + self.generation_counter
                    rng = random.Random(rng_seed)
                    pattern_def = rng.choice(binyanim)

                if pattern_def:
                    new_word = self.engine.root_handler.apply_pattern(
                        root, pattern_def)
                else:
                    new_word = "".join(root)
            else:
                new_word = generate_fallback()

        elif strategy_key == "derived":
            if self.engine.affix_handler:
                base_gen = self.engine._generate_word_from_seed(
                    self.lemma,
                    self.engine.global_seed + self.generation_counter
                )

                suffixes = self.engine.affix_handler.source_suffixes
                if suffixes:
                    rng = random.Random(
                        self.engine.global_seed + self.generation_counter)
                    rule = rng.choice(suffixes)
                    affix = rule.get('replacement', 'enc')
                    new_word = f"{base_gen}{affix}"
                else:
                    new_word = generate_fallback()
            else:
                new_word = generate_fallback()

        elif strategy_key == "nativization":
            if self.engine.phonology_handler:
                base_nat = self.engine.phonology_handler.nativize_word(
                    self.lemma)

                if self.generation_counter > 1:
                    seed = self.engine.global_seed + self.generation_counter
                    if hasattr(self.engine, '_mutate_word'):
                        new_word = self.engine._mutate_word(base_nat, seed)
                    else:
                        new_word = base_nat
                else:
                    new_word = base_nat
            else:
                new_word = generate_fallback()

        if new_word:
            self.entry_word.delete(0, tk.END)
            self.entry_word.insert(0, new_word)
            self.entry_origin.delete(0, tk.END)
            self.entry_origin.insert(0, origin_tag)

    def save(self):
        new_word = self.entry_word.get().strip()
        new_origin = self.entry_origin.get().strip()

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

        self.title(f"Editar Variação: {lemma}")
        self.geometry("450x650")
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
            ("Fonotática (Padrão)", "phonotactics"),
            ("Sistema de Raízes", "triconsonantal_system"),
            ("Composição/Derivação", "derived"),
            ("Nativizar", "nativization"),
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
            input_str = f"{clean_lemma}_synset_fallback_{self.generation_counter}_{self.engine.global_seed}"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)
            word = self.engine._generate_word_from_seed(clean_lemma, hash_val)
            if self.engine.phonology_handler:
                word = self.engine.phonology_handler.apply_monophthongization(
                    word)
            return word

        if strategy_key == "phonotactics":
            input_str = f"{clean_lemma}_manual_gen_{self.generation_counter}_{self.engine.global_seed}"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)

            new_word = self.engine._generate_word_from_seed(
                clean_lemma, hash_val)
            if self.engine.phonology_handler:
                new_word = self.engine.phonology_handler.apply_monophthongization(
                    new_word)

        elif strategy_key == "triconsonantal_system":
            if self.engine.root_handler and self.engine.root_handler.enabled:
                root = self.engine.root_handler.generate_root(self.lemma)

                binyanim = self.engine.root_handler.binyanim
                pattern_def = None
                if binyanim:
                    rng_seed = self.engine.global_seed + self.generation_counter
                    rng = random.Random(rng_seed)
                    pattern_def = rng.choice(binyanim)

                if pattern_def:
                    new_word = self.engine.root_handler.apply_pattern(
                        root, pattern_def)
                else:
                    new_word = "".join(root)
            else:
                new_word = generate_fallback()

        elif strategy_key == "derived":
            if self.engine.affix_handler:
                base_gen = self.engine._generate_word_from_seed(
                    self.lemma,
                    self.engine.global_seed + self.generation_counter
                )

                suffixes = self.engine.affix_handler.source_suffixes
                if suffixes:
                    rng = random.Random(
                        self.engine.global_seed + self.generation_counter)
                    rule = rng.choice(suffixes)
                    affix = rule.get('replacement', 'enc')
                    new_word = f"{base_gen}{affix}"
                else:
                    new_word = generate_fallback()
            else:
                new_word = generate_fallback()

        elif strategy_key == "nativization":
            if self.engine.phonology_handler:
                base_nat = self.engine.phonology_handler.nativize_word(
                    self.lemma)

                if self.generation_counter > 1:
                    seed = self.engine.global_seed + self.generation_counter
                    if hasattr(self.engine, '_mutate_word'):
                        new_word = self.engine._mutate_word(base_nat, seed)
                    else:
                        new_word = base_nat
                else:
                    new_word = base_nat
            else:
                new_word = generate_fallback()

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
