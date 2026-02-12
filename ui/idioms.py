import tkinter as tk
from tkinter import ttk, messagebox
import threading
import hashlib
import random


class IdiomTab(ttk.Frame):
    def __init__(self, parent, colors, engine=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.manager = engine.idiom_manager if engine else None
        self.generation_counter = 0
        self.is_generating = False
        self.setup_ui()
        if self.manager:
            self.refresh_list()

    def setup_ui(self):
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        list_frame = ttk.Frame(self.paned)
        self.paned.add(list_frame, weight=1)

        columns = ("expression", "target", "type")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("expression", text="Expressão (Entrada)")
        self.tree.heading("target", text="Alvo (Conceito/Lema)")
        self.tree.heading("type", text="Tipo")
        self.tree.column("expression", width=200)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Delete>", lambda e: self.delete_idiom())

        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=1)

        edit_frame = ttk.LabelFrame(
            right_frame, text="Editor de Expressão", padding=15)
        edit_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(edit_frame, text="Expressão Original (ex: 'cair do cavalo'):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_expr = ttk.Entry(edit_frame, font=(
            "Segoe UI", 10), foreground="black")
        self.entry_expr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(edit_frame, text="Traduzir como (Lema único):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")

        target_frame = ttk.Frame(edit_frame)
        target_frame.pack(fill=tk.X, pady=(0, 10))

        self.entry_target = ttk.Entry(target_frame, font=(
            "Segoe UI", 10, "bold"), foreground="black")
        self.entry_target.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(edit_frame, text="Tags/Contexto (opcional):",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")
        self.entry_tags = ttk.Entry(edit_frame, font=(
            "Segoe UI", 10), foreground="black")
        self.entry_tags.pack(fill=tk.X, pady=(0, 10))

        gen_frame = ttk.LabelFrame(
            right_frame, text="Gerador de Sugestões", padding=15)
        gen_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(gen_frame, text="Estratégia de Geração:",
                  foreground=self.colors["fg_secondary"]).pack(anchor="w")

        self.strategy_var = tk.StringVar(value="phonotactics")
        strategies = [
            ("Fonotática (Padrão)", "phonotactics"),
            ("Sistema de Raízes (Triconsonantal)", "triconsonantal_system"),
            ("Derivação (Sufixação)", "derived"),
            ("Nativizar Expressão", "nativization"),
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

        self.btn_gen = ttk.Button(gen_frame, text="✨ Gerar Sugestão",
                                  style="Secondary.TButton", command=self.start_generation)
        self.btn_gen.pack(fill=tk.X)

        action_frame = ttk.Frame(right_frame, padding=5)
        action_frame.pack(fill=tk.X, pady=10)

        self.btn_save = ttk.Button(
            action_frame, text="Salvar Expressão", command=self.save_idiom)
        self.btn_save.pack(fill=tk.X, pady=(0, 5))

        self.btn_delete = ttk.Button(
            action_frame, text="Excluir Selecionada", command=self.delete_idiom)
        self.btn_delete.pack(fill=tk.X)
        self.btn_delete.state(['disabled'])

        self.btn_clear = ttk.Button(
            action_frame, text="Limpar Campos", command=self.clear_fields)
        self.btn_clear.pack(fill=tk.X, pady=(5, 0))

    def refresh_list(self):
        if not self.manager:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for expr, data in self.manager.idioms.items():
            self.tree.insert("", tk.END, values=(
                expr, data['target'], data.get('type', 'lexical')))

    def on_select(self, event):
        if not self.manager:
            return

        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        expr = item['values'][0]
        data = self.manager.idioms.get(expr)

        if data:
            self.entry_expr.delete(0, tk.END)
            self.entry_expr.insert(0, expr)

            self.entry_target.delete(0, tk.END)
            self.entry_target.insert(0, data['target'])

            self.entry_tags.delete(0, tk.END)
            self.entry_tags.insert(0, ",".join(data.get('tags', [])))

            self.btn_delete.state(['!disabled'])
            self.generation_counter = 0

    def clear_fields(self):
        self.entry_expr.delete(0, tk.END)
        self.entry_target.delete(0, tk.END)
        self.entry_tags.delete(0, tk.END)
        self.btn_delete.state(['disabled'])
        self.tree.selection_remove(self.tree.selection())
        self.generation_counter = 0

    def start_generation(self):
        if self.is_generating or not self.engine:
            return

        expression_seed = self.entry_expr.get().strip()
        if not expression_seed:
            messagebox.showinfo(
                "Informação", "Digite uma expressão primeiro para usar como base.")
            self.entry_expr.focus()
            return

        self.is_generating = True
        self.btn_gen.config(text="Gerando...", state="disabled")
        threading.Thread(target=self._run_generation,
                         args=(expression_seed,), daemon=True).start()

    def _run_generation(self, seed_text):
        display_strat = self.combo_strategy.get()
        strategy_key = self.map_strategy.get(display_strat, "phonotactics")

        self.generation_counter += 1
        new_word = ""

        clean_seed = "".join(filter(str.isalpha, seed_text.lower()))

        def generate_fallback():
            input_str = f"{clean_seed}_idiom_gen_{self.generation_counter}_{self.engine.global_seed}"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)
            word = self.engine._generate_word_from_seed(clean_seed, hash_val)
            if self.engine.phonology_handler:
                word = self.engine.phonology_handler.apply_monophthongization(
                    word)
            return word

        if strategy_key == "phonotactics":
            input_str = f"{clean_seed}_create_gen_{self.generation_counter}_{self.engine.global_seed}"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)
            new_word = self.engine._generate_word_from_seed(
                clean_seed, hash_val)
            if self.engine.phonology_handler:
                new_word = self.engine.phonology_handler.apply_monophthongization(
                    new_word)

        elif strategy_key == "triconsonantal_system":
            if self.engine.root_handler and self.engine.root_handler.enabled:
                root = self.engine.root_handler.generate_root(seed_text)
                binyanim = self.engine.root_handler.binyanim
                pattern_def = None
                if binyanim:
                    rng_seed = self.engine.global_seed + \
                        self.generation_counter + len(seed_text)
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
                    seed_text,
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
                words = seed_text.split()
                target_to_nativize = max(
                    words, key=len) if words else seed_text

                base_nat = self.engine.phonology_handler.nativize_word(
                    target_to_nativize)

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
                new_word, clean_seed, seed_to_use)

        self.after(0, lambda: self._update_ui_after_gen(new_word))

    def _update_ui_after_gen(self, word):
        self.entry_target.delete(0, tk.END)
        self.entry_target.insert(0, word)
        self.is_generating = False
        self.btn_gen.config(text="✨ Gerar Sugestão", state="normal")

    def save_idiom(self):
        if not self.manager:
            messagebox.showwarning(
                "Aviso", "Carregue um perfil de linguagem primeiro.")
            return

        expr = self.entry_expr.get().strip()
        target = self.entry_target.get().strip()
        tags_str = self.entry_tags.get().strip()

        if not expr or not target:
            messagebox.showwarning("Aviso", "Preencha a expressão e o alvo.")
            return

        tags = [t.strip() for t in tags_str.split(',')] if tags_str else []

        self.manager.add_idiom(expr, target, tags=tags)
        self.refresh_list()
        self.clear_fields()

    def delete_idiom(self):
        if not self.manager:
            return

        expr = self.entry_expr.get().strip()
        if not expr:
            selected = self.tree.selection()
            if selected:
                item = self.tree.item(selected[0])
                expr = item['values'][0]

        if expr:
            if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir a expressão:\n'{expr}'?"):
                self.manager.delete_idiom(expr)
                self.refresh_list()
                self.clear_fields()
