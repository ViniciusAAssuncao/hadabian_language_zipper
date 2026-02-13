import tkinter as tk
from tkinter import ttk
import hashlib
import random
import threading
import json
from pathlib import Path


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

        ttk.Label(search_frame, text="Buscar (Nativo ou Português):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        entry = ttk.Entry(
            search_frame, textvariable=self.search_var, foreground="black")
        entry.pack(fill=tk.X, pady=(0, 5))
        entry.focus()

        list_frame = ttk.Frame(self, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            bg=self.colors.get("bg_entry", "#ffffff"),
            fg="black",
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

        self.data_items = []
        for lemma, entry in self.word_cache.items():
            if isinstance(entry, dict):
                word = entry.get("default", lemma)
            else:
                word = entry

            display_text = f"{word} ({lemma})"
            self.data_items.append((display_text, lemma))

        self.data_items.sort(key=lambda x: x[0].lower())

        self.current_items = self.data_items
        self.update_list(self.data_items)

    def filter_list(self, *args):
        search_term = self.search_var.get().lower()
        filtered = [
            item for item in self.data_items if search_term in item[0].lower()]
        self.current_items = filtered
        self.update_list(filtered)

    def update_list(self, items):
        self.listbox.delete(0, tk.END)
        for item in items:
            self.listbox.insert(tk.END, item[0])

    def on_select(self, event=None):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            lemma_key = self.current_items[index][1]
            self.callback(lemma_key)
            self.destroy()


class CreateWordModal(tk.Toplevel):
    def __init__(self, parent, colors, engine, on_save):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.on_save = on_save
        self.generation_counter = 0
        self.loan_gen_counter = 0
        self.is_generating = False

        self.title("Criar Nova Palavra")
        self.geometry("700x800")
        self.configure(bg=self.colors["bg_main"])
        self.transient(parent)
        self.grab_set()

        self.lemma_a_data = None
        self.lemma_b_data = None
        self.source_engine_cache = None
        self.selected_source_id = None
        self.compound_suggestions = []

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
        self.tab_loan = ttk.Frame(self.notebook, padding=15)

        self.notebook.add(self.tab_simple, text="Geração Simples")
        self.notebook.add(self.tab_compound, text="Aglutinação/Composição")
        self.notebook.add(self.tab_loan, text="Empréstimos")

        self.setup_simple_tab()
        self.setup_compound_tab()
        self.setup_loan_tab()

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
            (0, 0), window=scrollable_frame, anchor="nw", width=650)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        info_frame = ttk.LabelFrame(
            scrollable_frame, text="Informações Básicas", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(info_frame, text="Lema / Conceito (Entrada):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_lemma = ttk.Entry(info_frame, font=(
            "Segoe UI", 11), foreground="black")
        self.entry_lemma.pack(fill=tk.X, pady=(5, 15))

        ttk.Label(info_frame, text="Palavra na Conlang (Saída):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_word = ttk.Entry(info_frame, font=(
            "Segoe UI", 11, "bold"), foreground="black")
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
            state="readonly",
            foreground="black"
        )
        self.combo_strategy.current(0)
        self.combo_strategy.pack(fill=tk.X, pady=(5, 10))
        self.map_strategy = {s[0]: s[1] for s in strategies}

        self.btn_gen = ttk.Button(gen_frame, text="Gerar Sugestão",
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
            (0, 0), window=scrollable_frame, anchor="nw", width=650)
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

        swap_frame = ttk.Frame(parts_frame)
        swap_frame.pack(fill=tk.X, pady=2)
        ttk.Button(swap_frame, text="⇅ Inverter Ordem",
                   command=self.swap_components, style="Secondary.TButton").pack(anchor="center")

        ttk.Label(parts_frame, text="Parte B (Modificador/Cabeça):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        frame_b = ttk.Frame(parts_frame)
        frame_b.pack(fill=tk.X, pady=(5, 5))
        self.lbl_part_b = ttk.Label(frame_b, text="[Nenhum selecionado]", font=(
            "Segoe UI", 10, "italic"), foreground=self.colors["fg_secondary"])
        self.lbl_part_b.pack(side="left", fill=tk.X, expand=True)
        ttk.Button(frame_b, text="Buscar", width=10,
                   command=lambda: self.open_search("B")).pack(side="right")

        suggestion_frame = ttk.LabelFrame(
            scrollable_frame, text="Sugestões Inteligentes", padding=15)
        suggestion_frame.pack(fill=tk.X, pady=(0, 15))

        self.suggestion_list = tk.Listbox(suggestion_frame, height=4, relief="flat",
                                          bg=self.colors.get("bg_entry", "#ffffff"), fg="black",
                                          highlightthickness=1, highlightbackground=self.colors.get("border", "#cccccc"))
        self.suggestion_list.pack(fill=tk.X, pady=(0, 5))
        self.suggestion_list.bind(
            "<<ListboxSelect>>", self.on_suggestion_select)

        ttk.Button(suggestion_frame, text="↻ Regenerar Sugestões",
                   command=self.refresh_compound_suggestions).pack(fill=tk.X)

        preview_frame = ttk.LabelFrame(
            scrollable_frame, text="Resultado da Aglutinação", padding=15)
        preview_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(preview_frame, text="Lema Composto:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_compound_lemma = ttk.Entry(preview_frame, font=(
            "Segoe UI", 11), foreground="black")
        self.entry_compound_lemma.pack(fill=tk.X, pady=(5, 10))
        ttk.Label(preview_frame, text="Palavra Resultante:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_compound_word = ttk.Entry(preview_frame, font=(
            "Segoe UI", 11, "bold"), foreground="black")
        self.entry_compound_word.pack(fill=tk.X, pady=(5, 5))
        self.setup_common_fields(scrollable_frame, "compound")

    def setup_loan_tab(self):
        footer_frame = ttk.Frame(self.tab_loan)
        footer_frame.pack(side="bottom", fill="x")
        self.create_action_buttons(footer_frame, "loan")

        body_frame = ttk.Frame(self.tab_loan)
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
            (0, 0), window=scrollable_frame, anchor="nw", width=650)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        source_frame = ttk.LabelFrame(
            scrollable_frame, text="Fonte de Empréstimo", padding=15)
        source_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(source_frame, text="ID da Conlang Fonte:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")

        source_input_frame = ttk.Frame(source_frame)
        source_input_frame.pack(fill=tk.X, pady=(5, 10))

        self.entry_source_id = ttk.Entry(
            source_input_frame, foreground="black")
        self.entry_source_id.pack(
            side="left", fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(source_input_frame, text="Carregar",
                   command=self.load_source_conlang).pack(side="right")

        preferred = self.engine.profile.get(
            "loanword_policy", {}).get("preferred_sources", [])
        if preferred:
            ttk.Label(source_frame, text=f"Sugeridos: {', '.join(preferred)}",
                      font=("Segoe UI", 9), foreground=self.colors["fg_secondary"]).pack(anchor="w")

        self.lbl_source_status = ttk.Label(
            source_frame, text="", foreground="gray")
        self.lbl_source_status.pack(anchor="w")

        lookup_frame = ttk.LabelFrame(
            scrollable_frame, text="Buscar na Fonte", padding=15)
        lookup_frame.pack(fill=tk.X, pady=(0, 15))

        self.btn_search_source = ttk.Button(lookup_frame, text="Buscar Palavra na Fonte",
                                            command=self.open_source_search, state="disabled")
        self.btn_search_source.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(lookup_frame, text="Palavra Original:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.lbl_original_word = ttk.Label(
            lookup_frame, text="---", font=("Segoe UI", 11, "bold"))
        self.lbl_original_word.pack(anchor="w", pady=(0, 10))

        adapt_frame = ttk.LabelFrame(
            scrollable_frame, text="Adaptação", padding=15)
        adapt_frame.pack(fill=tk.X, pady=(0, 15))

        self.adapt_var = tk.StringVar(value="nativize")

        r1 = tk.Radiobutton(adapt_frame, text="Nativização Fonológica (Adaptar sons)",
                            variable=self.adapt_var, value="nativize",
                            command=self.reset_and_preview_loan,
                            bg=self.colors["bg_main"], fg="white",
                            selectcolor=self.colors["bg_main"],
                            activebackground=self.colors["bg_main"],
                            activeforeground="black")
        r1.pack(anchor="w")

        r2 = tk.Radiobutton(adapt_frame, text="Herança Direta (Raw)",
                            variable=self.adapt_var, value="raw",
                            command=self.reset_and_preview_loan,
                            bg=self.colors["bg_main"], fg="white",
                            selectcolor=self.colors["bg_main"],
                            activebackground=self.colors["bg_main"],
                            activeforeground="black")
        r2.pack(anchor="w")

        self.btn_gen_loan = ttk.Button(
            adapt_frame, text="Gerar Sugestão", command=self.generate_loan_suggestion)
        self.btn_gen_loan.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(adapt_frame, text="Lema (Entrada):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(10, 0))
        self.entry_loan_lemma = ttk.Entry(
            adapt_frame, font=("Segoe UI", 11), foreground="black")
        self.entry_loan_lemma.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(adapt_frame, text="Palavra Adaptada (Saída):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_loan_word = ttk.Entry(
            adapt_frame, font=("Segoe UI", 11, "bold"), foreground="black")
        self.entry_loan_word.pack(fill=tk.X, pady=(5, 5))

        self.setup_common_fields(scrollable_frame, "loan")

    def load_source_conlang(self):
        source_id = self.entry_source_id.get().strip()
        if not source_id:
            return

        self.lbl_source_status.config(text="Carregando...", foreground="blue")
        self.update_idletasks()

        try:
            source_engine = self.engine.get_source_engine(source_id)
            if source_engine:
                self.source_engine_cache = source_engine.word_cache
                self.selected_source_id = source_id
                self.lbl_source_status.config(
                    text=f"Carregado: {len(self.source_engine_cache)} palavras", foreground="green")
                self.btn_search_source.config(state="normal")
            else:
                self.lbl_source_status.config(
                    text="Erro: Conlang não encontrada", foreground="red")
        except Exception as e:
            self.lbl_source_status.config(
                text=f"Erro: {str(e)}", foreground="red")

    def open_source_search(self):
        if not self.source_engine_cache:
            return

        def callback(lemma):
            entry = self.source_engine_cache.get(lemma)
            default_word = entry.get("default", lemma) if isinstance(
                entry, dict) else entry
            self.lbl_original_word.config(text=f"{lemma} ({default_word})")
            self.entry_loan_lemma.delete(0, tk.END)
            self.entry_loan_lemma.insert(0, lemma)

            origin_field = getattr(self, "entry_origin_loan")
            origin_field.delete(0, tk.END)
            origin_field.insert(0, f"loan:{self.selected_source_id}")

            self.loan_gen_counter = 0
            self.preview_loan(default_word)

        LemmaSearchDialog(self, self.colors,
                          self.source_engine_cache, callback)

    def reset_and_preview_loan(self):
        self.loan_gen_counter = 0
        self.preview_loan()

    def generate_loan_suggestion(self):
        self.loan_gen_counter += 1
        self.preview_loan()

    def preview_loan(self, word=None):
        if word is None:
            text = self.lbl_original_word.cget("text")
            if "---" in text:
                return
            if "(" in text:
                word = text.split("(")[1].strip(")")
            else:
                word = text

        mode = self.adapt_var.get()
        result = word

        if mode == "nativize":
            base_nat = self.engine.phonology_handler.nativize_word(word)

            if self.loan_gen_counter == 0:
                result = base_nat
            else:
                seed = self.engine.global_seed + \
                    self.loan_gen_counter + sum(ord(c) for c in word)
                if hasattr(self.engine, '_mutate_word'):
                    result = self.engine._mutate_word(base_nat, seed)
                else:
                    result = base_nat

            if self.engine.phonology_handler:
                result = self.engine.phonology_handler.apply_monophthongization(
                    result)

            if hasattr(self.engine, 'special_mechanics_handler') and self.engine.special_mechanics_handler and self.engine.special_mechanics_handler.enabled:
                seed_to_use = self.engine.global_seed + self.loan_gen_counter
                original_lemma = word if word else ""
                result = self.engine.special_mechanics_handler.apply_mechanics(
                    result, original_lemma, seed_to_use)

        self.entry_loan_word.delete(0, tk.END)
        self.entry_loan_word.insert(0, result)

    def setup_common_fields(self, parent, prefix):
        details_frame = ttk.LabelFrame(parent, text="Detalhes", padding=15)
        details_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(details_frame, text="Classe Gramatical (POS):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        entry_pos = ttk.Entry(details_frame, foreground="black")
        entry_pos.pack(fill=tk.X, pady=(5, 10))
        setattr(self, f"entry_pos_{prefix}", entry_pos)

        ttk.Label(details_frame, text="Definição / Descrição:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        text_def = tk.Text(details_frame, height=3, font=("Segoe UI", 10), bg=self.colors.get("bg_entry", "#ffffff"),
                           fg="black", relief="flat", highlightthickness=1, highlightbackground=self.colors.get("border", "#cccccc"))
        text_def.pack(fill=tk.X, pady=(5, 10))
        setattr(self, f"text_def_{prefix}", text_def)

        ttk.Label(details_frame, text="Origem / Etimologia:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        entry_origin = ttk.Entry(details_frame, foreground="black")
        entry_origin.pack(fill=tk.X, pady=(5, 10))
        default_origin = "custom"
        if prefix == "compound":
            default_origin = "compound"
        elif prefix == "loan":
            default_origin = "loanword"
        entry_origin.insert(0, default_origin)
        setattr(self, f"entry_origin_{prefix}", entry_origin)

        ttk.Label(details_frame, text="Tags (separadas por vírgula):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        entry_tags = ttk.Entry(details_frame, foreground="black")
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
                self.refresh_compound_suggestions()

        LemmaSearchDialog(self, self.colors, self.engine.word_cache, callback)

    def swap_components(self):
        if not self.lemma_a_data or not self.lemma_b_data:
            return

        self.lemma_a_data, self.lemma_b_data = self.lemma_b_data, self.lemma_a_data

        txt_a = f"{self.lemma_a_data[0]} ({self.lemma_a_data[1]})"
        txt_b = f"{self.lemma_b_data[0]} ({self.lemma_b_data[1]})"

        self.lbl_part_a.config(text=txt_a)
        self.lbl_part_b.config(text=txt_b)

        combined_lemma = f"{self.lemma_a_data[0]}-{self.lemma_b_data[0]}"
        self.entry_compound_lemma.delete(0, tk.END)
        self.entry_compound_lemma.insert(0, combined_lemma)
        self.refresh_compound_suggestions()

    def refresh_compound_suggestions(self):
        if not self.lemma_a_data or not self.lemma_b_data:
            return

        self.suggestion_list.delete(0, tk.END)
        self.compound_suggestions = []

        suggestions = self.engine.suggest_compounds(
            [self.lemma_a_data[0], self.lemma_b_data[0]])

        for idx, sugg in enumerate(suggestions):
            word = sugg.get('word', '')
            desc = sugg.get('desc', '')
            self.suggestion_list.insert(tk.END, f"{word} [{desc}]")
            self.compound_suggestions.append(word)

        if self.compound_suggestions:
            self.suggestion_list.select_set(0)
            self.entry_compound_word.delete(0, tk.END)
            self.entry_compound_word.insert(0, self.compound_suggestions[0])

    def on_suggestion_select(self, event):
        selection = self.suggestion_list.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.compound_suggestions):
                word = self.compound_suggestions[idx]
                self.entry_compound_word.delete(0, tk.END)
                self.entry_compound_word.insert(0, word)

    def process_agglutination(self):
        self.refresh_compound_suggestions()

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

        if new_word and hasattr(self.engine, 'special_mechanics_handler') and self.engine.special_mechanics_handler and self.engine.special_mechanics_handler.enabled:
            seed_to_use = self.engine.global_seed + self.generation_counter
            new_word = self.engine.special_mechanics_handler.apply_mechanics(
                new_word, clean_lemma, seed_to_use)

        self.after(0, lambda: self._update_ui_after_gen(
            new_word, strategy_key))

    def _update_ui_after_gen(self, word, origin):
        self.entry_word.delete(0, tk.END)
        self.entry_word.insert(0, word)
        entry_origin = getattr(self, "entry_origin_simple")
        entry_origin.delete(0, tk.END)
        entry_origin.insert(0, origin)
        self.is_generating = False
        self.btn_gen.config(text="Gerar Nova Sugestão", state="normal")

    def save(self, mode):
        if mode == "simple":
            lemma = self.entry_lemma.get().strip()
            word = self.entry_word.get().strip()
        elif mode == "compound":
            lemma = self.entry_compound_lemma.get().strip()
            word = self.entry_compound_word.get().strip()
        else:
            lemma = self.entry_loan_lemma.get().strip()
            word = self.entry_loan_word.get().strip()

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
