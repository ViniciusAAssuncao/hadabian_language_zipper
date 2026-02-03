import tkinter as tk
from tkinter import ttk
import hashlib
import random
import threading


class LemmaSearchDialog(tk.Toplevel):
    def __init__(self, parent, colors, word_cache, callback):
        super().__init__(parent)
        self.colors = colors
        self.word_cache = word_cache
        self.callback = callback
        self.title("Selecionar Lema")
        self.geometry("400x500")
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
        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Buscar:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        entry = ttk.Entry(search_frame, textvariable=self.search_var)
        entry.foreground = self.colors["text"]
        entry.pack(fill=tk.X, pady=(0, 5))
        entry.focus()

        list_frame = ttk.Frame(self, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            bg=self.colors.get("bg_entry", "#ffffff"),
            fg=self.colors["text"],
            selectbackground=self.colors["accent"],
            selectforeground="white",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors.get("border", "#cccccc")
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.bind("<Double-Button-1>", self.on_select)
        self.listbox.bind("<Return>", self.on_select)

        self.full_list = sorted(self.word_cache.keys())
        self.update_list(self.full_list)

    def filter_list(self, *args):
        search_term = self.search_var.get().lower()
        filtered = [w for w in self.full_list if search_term in w.lower()]
        self.update_list(filtered)

    def update_list(self, items):
        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, item)

    def on_select(self, event=None):
        selection = self.listbox.curselection()
        if selection:
            lemma = self.listbox.get(selection[0])
            self.callback(lemma)
            self.destroy()


class CreateWordModal(tk.Toplevel):
    def __init__(self, parent, colors, engine, on_save):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.on_save = on_save
        self.generation_counter = 0
        self.is_generating = False

        self.title("Criar Nova Palavra")
        self.geometry("600x750")
        self.configure(bg=self.colors["bg_main"])
        self.transient(parent)
        self.grab_set()

        self.lemma_a_data = None
        self.lemma_b_data = None

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
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_simple = ttk.Frame(self.notebook, padding=15)
        self.tab_compound = ttk.Frame(self.notebook, padding=15)

        self.notebook.add(self.tab_simple, text="Geração Simples")
        self.notebook.add(self.tab_compound, text="Aglutinação/Composição")

        self.setup_simple_tab()
        self.setup_compound_tab()

    def create_action_buttons(self, parent, mode):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Salvar Palavra", command=lambda: self.save(
            mode)).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="Cancelar",
                   command=self.destroy).pack(fill=tk.X)

    def setup_simple_tab(self):
        footer_frame = ttk.Frame(self.tab_simple)
        footer_frame.pack(side="bottom", fill="x")
        self.create_action_buttons(footer_frame, "simple")

        body_frame = ttk.Frame(self.tab_simple)
        body_frame.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(
            body_frame, bg=self.colors["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            body_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

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

        ttk.Label(gen_frame, text="Estratégia:",
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

        self.btn_gen = ttk.Button(gen_frame, text="⚡ Gerar Sugestão",
                                  style="Secondary.TButton", command=self.start_generation)
        self.btn_gen.pack(fill=tk.X)

        self.setup_common_fields(scrollable_frame, "simple")

    def setup_compound_tab(self):
        footer_frame = ttk.Frame(self.tab_compound)
        footer_frame.pack(side="bottom", fill="x")
        self.create_action_buttons(footer_frame, "compound")

        body_frame = ttk.Frame(self.tab_compound)
        body_frame.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(
            body_frame, bg=self.colors["bg_main"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            body_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        parts_frame = ttk.LabelFrame(
            scrollable_frame, text="Componentes da Aglutinação", padding=15)
        parts_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(parts_frame, text="Parte A (Modificador/Cabeça):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        frame_a = ttk.Frame(parts_frame)
        frame_a.pack(fill=tk.X, pady=(5, 10))
        self.lbl_part_a = ttk.Label(frame_a, text="[Nenhum selecionado]", font=(
            "Segoe UI", 10, "italic"), foreground=self.colors["fg_secondary"])
        self.lbl_part_a.pack(side="left", fill=tk.X, expand=True)
        ttk.Button(frame_a, text="Buscar", width=10,
                   command=lambda: self.open_search("A")).pack(side="right")
        ttk.Label(parts_frame, text="Parte B (Modificador/Cabeça):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        frame_b = ttk.Frame(parts_frame)
        frame_b.pack(fill=tk.X, pady=(5, 5))
        self.lbl_part_b = ttk.Label(frame_b, text="[Nenhum selecionado]", font=(
            "Segoe UI", 10, "italic"), foreground=self.colors["fg_secondary"])
        self.lbl_part_b.pack(side="left", fill=tk.X, expand=True)
        ttk.Button(frame_b, text="Buscar", width=10,
                   command=lambda: self.open_search("B")).pack(side="right")
        preview_frame = ttk.LabelFrame(
            scrollable_frame, text="Resultado da Aglutinação", padding=15)
        preview_frame.pack(fill=tk.X, pady=(0, 15))
        self.btn_agglutinate = ttk.Button(
            preview_frame, text="⚙️ Processar Aglutinação", command=self.process_agglutination)
        self.btn_agglutinate.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(preview_frame, text="Lema Composto:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_compound_lemma = ttk.Entry(preview_frame, font=(
            "Segoe UI", 11), foreground=self.colors["text"])
        self.entry_compound_lemma.pack(fill=tk.X, pady=(5, 10))
        ttk.Label(preview_frame, text="Palavra Resultante:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_compound_word = ttk.Entry(preview_frame, font=(
            "Segoe UI", 11, "bold"), foreground=self.colors["text"])
        self.entry_compound_word.pack(fill=tk.X, pady=(5, 5))
        self.setup_common_fields(scrollable_frame, "compound")

    def setup_common_fields(self, parent, prefix):
        details_frame = ttk.LabelFrame(parent, text="Detalhes", padding=15)
        details_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(details_frame, text="Classe Gramatical (POS):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        entry_pos = ttk.Entry(details_frame, foreground=self.colors["text"])
        entry_pos.pack(fill=tk.X, pady=(5, 10))
        setattr(self, f"entry_pos_{prefix}", entry_pos)

        ttk.Label(details_frame, text="Definição / Descrição:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        text_def = tk.Text(details_frame, height=3, font=("Segoe UI", 10), bg=self.colors.get("bg_entry", "#ffffff"),
                           fg=self.colors["text"], relief="flat", highlightthickness=1, highlightbackground=self.colors.get("border", "#cccccc"))
        text_def.pack(fill=tk.X, pady=(5, 10))
        setattr(self, f"text_def_{prefix}", text_def)

        ttk.Label(details_frame, text="Origem / Etimologia:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        entry_origin = ttk.Entry(details_frame, foreground=self.colors["text"])
        entry_origin.pack(fill=tk.X, pady=(5, 10))
        entry_origin.insert(0, "compound" if prefix ==
                            "compound" else "custom")
        setattr(self, f"entry_origin_{prefix}", entry_origin)

        ttk.Label(details_frame, text="Tags (separadas por vírgula):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        entry_tags = ttk.Entry(details_frame, foreground=self.colors["text"])
        entry_tags.pack(fill=tk.X, pady=(5, 5))
        setattr(self, f"entry_tags_{prefix}", entry_tags)

    def open_search(self, target):
        def callback(lemma):
            entry = self.engine.word_cache.get(lemma)
            default_word = entry.get("default", lemma) if isinstance(
                entry, dict) else entry

            label_text = f"{lemma} ({default_word})"
            if target == "A":
                self.lbl_part_a.config(text=label_text)
                self.lemma_a_data = (lemma, default_word)
            else:
                self.lbl_part_b.config(text=label_text)
                self.lemma_b_data = (lemma, default_word)

            if self.lemma_a_data and self.lemma_b_data:
                combined_lemma = f"{self.lemma_a_data[0]}-{self.lemma_b_data[0]}"
                self.entry_compound_lemma.delete(0, tk.END)
                self.entry_compound_lemma.insert(0, combined_lemma)

        LemmaSearchDialog(self, self.colors, self.engine.word_cache, callback)

    def process_agglutination(self):
        if not self.lemma_a_data or not self.lemma_b_data:
            return

        lemma_a = self.lemma_a_data[0]
        lemma_b = self.lemma_b_data[0]

        final_word = self.engine.generate_compound([lemma_a, lemma_b])

        self.entry_compound_word.delete(0, tk.END)
        self.entry_compound_word.insert(0, final_word)

    def start_generation(self):
        if self.is_generating:
            return

        lemma = self.entry_lemma.get().strip()
        if not lemma:
            self.entry_lemma.focus()
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
                input_str = f"{clean_lemma}_fallback_{self.generation_counter}_{self.engine.global_seed}"
                h = int(hashlib.sha256(input_str.encode()).hexdigest(), 16)
                w = self.engine._generate_word_from_seed(clean_lemma, h)
                if self.engine.phonology_handler:
                    w = self.engine.phonology_handler.apply_monophthongization(
                        w)
                return w

            if strategy_key == "phonotactics":
                input_str = f"{clean_lemma}_gen_{self.generation_counter}"
                h = int(hashlib.sha256(input_str.encode()).hexdigest(), 16)
                new_word = self.engine._generate_word_from_seed(clean_lemma, h)
                if self.engine.phonology_handler:
                    new_word = self.engine.phonology_handler.apply_monophthongization(
                        new_word)

            elif strategy_key == "triconsonantal_system":
                if self.engine.root_handler and self.engine.root_handler.enabled:
                    root = self.engine.root_handler.generate_root(lemma)
                    binyanim = self.engine.root_handler.binyanim
                    if binyanim:
                        rng = random.Random(
                            self.generation_counter + len(lemma))
                        pat = rng.choice(binyanim)
                        new_word = self.engine.root_handler.apply_pattern(
                            root, pat)
                    else:
                        new_word = "".join(root)
                else:
                    new_word = generate_fallback()

            elif strategy_key == "derived":
                if self.engine.affix_handler and self.engine.affix_handler.source_suffixes:
                    base = self.engine._generate_word_from_seed(
                        lemma, self.generation_counter)
                    rng = random.Random(self.generation_counter)
                    rule = rng.choice(
                        self.engine.affix_handler.source_suffixes)
                    affix = rule.get('replacement', 'enc')
                    new_word = f"{base}{affix}"
                else:
                    new_word = generate_fallback()

            elif strategy_key == "nativization":
                if self.engine.phonology_handler:
                    new_word = self.engine.phonology_handler.nativize_word(
                        lemma)
                else:
                    new_word = generate_fallback()

            self.after(0, lambda: self._update_ui_after_gen(
                new_word, strategy_key))
        except Exception as e:
            print(f"Gen Error: {e}")
            self.after(0, lambda: self._update_ui_after_gen("Error", "error"))

    def _update_ui_after_gen(self, word, origin):
        self.entry_word.delete(0, tk.END)
        self.entry_word.insert(0, word)
        entry_origin = getattr(self, "entry_origin_simple")
        entry_origin.delete(0, tk.END)
        entry_origin.insert(0, origin)
        self.is_generating = False
        self.btn_gen.config(text="↻ Gerar Nova Sugestão", state="normal")

    def save(self, mode):
        if mode == "simple":
            lemma = self.entry_lemma.get().strip()
            word = self.entry_word.get().strip()
        else:
            lemma = self.entry_compound_lemma.get().strip()
            word = self.entry_compound_word.get().strip()

        pos = getattr(self, f"entry_pos_{mode}").get().strip()
        definition = getattr(self, f"text_def_{mode}").get(
            "1.0", tk.END).strip()
        origin = getattr(self, f"entry_origin_{mode}").get().strip()
        tags_str = getattr(self, f"entry_tags_{mode}").get().strip()

        if not lemma or not word:
            return

        tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
        if origin and origin not in tags_list:
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
