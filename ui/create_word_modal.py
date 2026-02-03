import tkinter as tk
from tkinter import ttk
import hashlib
import random
import threading


class CreateWordModal(tk.Toplevel):
    def __init__(self, parent, colors, engine, on_save):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.on_save = on_save
        self.generation_counter = 0
        self.is_generating = False

        self.title("Criar Nova Palavra")
        self.geometry("500x700")
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
        main_canvas = tk.Canvas(
            self, bg=self.colors["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas, padding=20)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(
                scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw", width=480)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(
            scrollable_frame,
            text="Criar Nova Entrada",
            font=("Segoe UI", 16, "bold"),
            foreground=self.colors["accent"]
        ).pack(anchor="w", pady=(0, 20))

        info_frame = ttk.LabelFrame(
            scrollable_frame, text="Informações Básicas", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(info_frame, text="Lema / Conceito (Entrada):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_lemma = ttk.Entry(info_frame, font=(
            "Segoe UI", 11), foreground=self.colors["text"])
        self.entry_lemma.pack(fill=tk.X, pady=(5, 15))

        ttk.Label(info_frame, text="Palavra na Conlang (Saída):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_word = ttk.Entry(info_frame, font=(
            "Segoe UI", 11, "bold"), foreground=self.colors["text"])
        self.entry_word.pack(fill=tk.X, pady=(5, 5))

        gen_frame = ttk.LabelFrame(
            scrollable_frame, text="Gerador Determinístico", padding=15)
        gen_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(gen_frame, text="Estratégia de Geração:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")

        self.strategy_var = tk.StringVar(value="phonotactics")
        strategies = [
            ("Fonotática Padrão", "phonotactics"),
            ("Sistema de Raízes (Triconsonantal)", "triconsonantal_system"),
            ("Derivação (Sufixação)", "derived"),
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

        self.btn_gen = ttk.Button(
            gen_frame,
            text="⚡ Gerar Sugestão",
            style="Secondary.TButton",
            command=self.start_generation
        )
        self.btn_gen.pack(fill=tk.X)

        details_frame = ttk.LabelFrame(
            scrollable_frame, text="Detalhes Avançados", padding=15)
        details_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(details_frame, text="Classe Gramatical (POS):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_pos = ttk.Entry(
            details_frame, foreground=self.colors["text"])
        self.entry_pos.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(details_frame, text="Definição / Descrição:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.text_def = tk.Text(details_frame, height=3, font=("Segoe UI", 10), bg=self.colors.get(
            "bg_entry", "#ffffff"), fg=self.colors["text"], relief="flat", highlightthickness=1, highlightbackground=self.colors.get("border", "#cccccc"))
        self.text_def.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(details_frame, text="Origem / Etimologia:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_origin = ttk.Entry(
            details_frame, foreground=self.colors["text"])
        self.entry_origin.pack(fill=tk.X, pady=(5, 10))
        self.entry_origin.insert(0, "custom")

        ttk.Label(details_frame, text="Tags (separadas por vírgula):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_tags = ttk.Entry(
            details_frame, foreground=self.colors["text"])
        self.entry_tags.pack(fill=tk.X, pady=(5, 5))

        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="Criar Palavra",
            command=self.save
        ).pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self.destroy
        ).pack(fill=tk.X)

    def start_generation(self):
        if self.is_generating:
            return

        lemma = self.entry_lemma.get().strip()
        if not lemma:
            self.entry_lemma.config(background="#ffe6e6")
            self.after(1000, lambda: self.entry_lemma.config(
                background=self.colors.get("bg_entry", "white")))
            return

        self.is_generating = True
        self.btn_gen.config(text="Gerando...", state="disabled")

        threading.Thread(target=self._run_generation,
                         args=(lemma,), daemon=True).start()

    def _run_generation(self, lemma):
        try:
            display_strat = self.combo_strategy.get()
            strategy_key = self.map_strategy.get(display_strat, "phonotactics")

            self.generation_counter += 1
            new_word = ""

            clean_lemma = "".join(filter(str.isalpha, lemma.lower()))

            def generate_fallback():
                input_str = f"{clean_lemma}_fallback_gen_{self.generation_counter}_{self.engine.global_seed}"
                hash_obj = hashlib.sha256(input_str.encode())
                hash_val = int(hash_obj.hexdigest(), 16)
                word = self.engine._generate_word_from_seed(
                    clean_lemma, hash_val)
                if self.engine.phonology_handler:
                    word = self.engine.phonology_handler.apply_monophthongization(
                        word)
                return word

            if strategy_key == "phonotactics":
                input_str = f"{clean_lemma}_create_gen_{self.generation_counter}_{self.engine.global_seed}"
                hash_obj = hashlib.sha256(input_str.encode())
                hash_val = int(hash_obj.hexdigest(), 16)

                new_word = self.engine._generate_word_from_seed(
                    clean_lemma, hash_val)
                if self.engine.phonology_handler:
                    new_word = self.engine.phonology_handler.apply_monophthongization(
                        new_word)

            elif strategy_key == "triconsonantal_system":
                if self.engine.root_handler and self.engine.root_handler.enabled:
                    root = self.engine.root_handler.generate_root(lemma)
                    binyanim = self.engine.root_handler.binyanim
                    pattern_def = None
                    if binyanim:
                        rng_seed = self.engine.global_seed + \
                            self.generation_counter + len(lemma)
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
                        lemma,
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
                        lemma)

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

            self.after(0, lambda: self._update_ui_after_gen(
                new_word, strategy_key))

        except Exception as e:
            print(f"Error generation: {e}")
            self.after(0, lambda: self._update_ui_after_gen("Error", "error"))

    def _update_ui_after_gen(self, word, origin):
        self.entry_word.delete(0, tk.END)
        self.entry_word.insert(0, word)

        self.entry_origin.delete(0, tk.END)
        self.entry_origin.insert(0, origin)

        self.is_generating = False
        self.btn_gen.config(text="↻ Gerar Nova Sugestão", state="normal")

    def save(self):
        lemma = self.entry_lemma.get().strip()
        word = self.entry_word.get().strip()
        pos = self.entry_pos.get().strip()
        definition = self.text_def.get("1.0", tk.END).strip()
        origin = self.entry_origin.get().strip()
        tags_str = self.entry_tags.get().strip()

        if not lemma:
            self.entry_lemma.focus()
            return

        if not word:
            self.entry_word.focus()
            return

        tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
        if not origin:
            origin = "manual_create"
        tags_list.insert(0, origin)

        new_data = {
            "lemma": lemma,
            "default": word,
            "origin": origin,
            "pos": pos,
            "definition": definition,
            "synsets": [{
                "word": word,
                "tags": tags_list,
                "affinity": 1.0,
                "pos": pos
            }]
        }

        self.on_save(lemma, new_data)
        self.destroy()
