import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import json
from pathlib import Path
from handlers.typology import PhonologicalDistance


class IntelligibilityTab(ttk.Frame):
    def __init__(self, parent, colors, engine=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.engines_dict = {}
        self.file_map = {}
        self.phonological_distance = None
        if self.engine and hasattr(self.engine, 'phoneme_feature_db'):
            self.phonological_distance = PhonologicalDistance(
                self.engine.phoneme_feature_db)
        self.setup_ui()
        self.load_available_conlangs()

    def setup_ui(self):
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)

        sel_frame = ttk.LabelFrame(
            left_frame, text="Seleção de Conlangs", padding=15)
        sel_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(sel_frame, text="Conlang A (Base):", foreground=self.colors.get(
            "fg_secondary", "black")).pack(anchor="w")
        self.cb_conlang_a = ttk.Combobox(
            sel_frame, state="readonly", font=("Segoe UI", 10), foreground="black")
        self.cb_conlang_a.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(sel_frame, text="Conlang B (Alvo):", foreground=self.colors.get(
            "fg_secondary", "black")).pack(anchor="w")
        self.cb_conlang_b = ttk.Combobox(
            sel_frame, state="readonly", font=("Segoe UI", 10), foreground="black")
        self.cb_conlang_b.pack(fill=tk.X, pady=(0, 15))

        self.btn_compare = ttk.Button(
            sel_frame, text="Calcular Inteligibilidade", style="Accent.TButton", command=self.on_calculate_click)
        self.btn_compare.pack(fill=tk.X)

        cfg_frame = ttk.LabelFrame(
            left_frame, text="Configurações de Análise", padding=15)
        cfg_frame.pack(fill=tk.X, pady=(0, 10))

        self.var_lexical = tk.BooleanVar(value=True)
        ttk.Checkbutton(cfg_frame, text="Análise Lexical e Cognatos",
                        variable=self.var_lexical).pack(anchor="w", pady=2)

        self.var_phonetic = tk.BooleanVar(value=True)
        ttk.Checkbutton(cfg_frame, text="Aproximação de Lavert (Fonética)",
                        variable=self.var_phonetic).pack(anchor="w", pady=2)

        self.var_morphosyntax = tk.BooleanVar(value=True)
        ttk.Checkbutton(cfg_frame, text="Divergência Morfossintática",
                        variable=self.var_morphosyntax).pack(anchor="w", pady=2)

        self.var_phonotactic = tk.BooleanVar(value=True)
        ttk.Checkbutton(cfg_frame, text="Compatibilidade Fonotática",
                        variable=self.var_phonotactic).pack(anchor="w", pady=2)

        stats_frame = ttk.LabelFrame(
            left_frame, text="Estatísticas Detalhadas", padding=15)
        stats_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_stats = ttk.Treeview(stats_frame, columns=(
            "metric", "value"), show="headings", height=8)
        self.tree_stats.heading("metric", text="Métrica")
        self.tree_stats.heading("value", text="Valor")
        self.tree_stats.column("metric", width=150)
        self.tree_stats.column("value", width=60, anchor="center")

        scroll_stats = ttk.Scrollbar(
            stats_frame, orient="vertical", command=self.tree_stats.yview)
        self.tree_stats.configure(yscroll=scroll_stats.set)

        self.tree_stats.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_stats.pack(side=tk.RIGHT, fill=tk.Y)

        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=3)

        res_frame = ttk.LabelFrame(
            right_frame, text="Índice de Inteligibilidade Mútua", padding=15)
        res_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_percentage = tk.Label(
            res_frame,
            text="--%",
            font=("Segoe UI", 48, "bold"),
            fg=self.colors.get("accent", "#0078D7"),
            bg=self.colors.get("bg_main", "#ffffff")
        )
        self.lbl_percentage.pack(pady=10)

        self.lbl_summary = ttk.Label(
            res_frame,
            text="Selecione as linguagens e clique em calcular para gerar o índice.",
            font=("Segoe UI", 11),
            justify="center",
            foreground=self.colors.get("fg_secondary", "black")
        )
        self.lbl_summary.pack(pady=(0, 10))

        self.progress_bar = ttk.Progressbar(
            res_frame, mode="determinate", length=400)
        self.progress_bar.pack(pady=(10, 5))

        dict_frame = ttk.LabelFrame(
            right_frame, text="Dicionário de Proximidade (Cognatos e Correspondências)", padding=15)
        dict_frame.pack(fill=tk.BOTH, expand=True)

        toolbar_dict = ttk.Frame(dict_frame)
        toolbar_dict.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar_dict, text="Filtrar por similaridade mínima (%):", foreground=self.colors.get(
            "fg_secondary", "black")).pack(side=tk.LEFT, padx=(0, 5))
        self.spin_filter = ttk.Spinbox(
            toolbar_dict, from_=0, to=100, width=5, command=self.apply_dict_filter, foreground="black")
        self.spin_filter.set(0)
        self.spin_filter.pack(side=tk.LEFT)
        self.spin_filter.bind("<Return>", lambda e: self.apply_dict_filter())

        self.btn_export = ttk.Button(
            toolbar_dict, text="Exportar Dicionário", state="disabled", command=self.on_export_click)
        self.btn_export.pack(side=tk.RIGHT)

        cols = ("lemma", "word_a", "word_b", "distance_classic",
                "distance_phono", "similarity")
        self.tree_words = ttk.Treeview(
            dict_frame, columns=cols, show="headings", style="Treeview")

        self.tree_words.heading("lemma", text="Conceito / Lema")
        self.tree_words.heading("word_a", text="Palavra em A")
        self.tree_words.heading("word_b", text="Palavra em B")
        self.tree_words.heading("distance_classic", text="Dist. Clássica")
        self.tree_words.heading("distance_phono", text="Dist. Fonológica")
        self.tree_words.heading("similarity", text="Similaridade (%)")

        self.tree_words.column("lemma", width=120)
        self.tree_words.column("word_a", width=130)
        self.tree_words.column("word_b", width=130)
        self.tree_words.column("distance_classic", width=100, anchor="center")
        self.tree_words.column("distance_phono", width=110, anchor="center")
        self.tree_words.column("similarity", width=110, anchor="center")

        scroll_words = ttk.Scrollbar(
            dict_frame, orient="vertical", command=self.tree_words.yview)
        self.tree_words.configure(yscroll=scroll_words.set)

        self.tree_words.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_words.pack(side=tk.RIGHT, fill=tk.Y)

        self.current_word_data = []

    def load_available_conlangs(self):
        path = Path("./conlangs")
        path.mkdir(exist_ok=True)
        files = sorted([f for f in path.glob("*.json")])
        names = []
        self.file_map = {}
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    name = data.get('metadata', {}).get(
                        'name', data.get('id', f.stem))
                    names.append(name)
                    self.file_map[name] = f
            except:
                pass
        self.cb_conlang_a['values'] = names
        self.cb_conlang_b['values'] = names
        if len(names) >= 2:
            self.cb_conlang_a.set(names[0])
            self.cb_conlang_b.set(names[1])
        elif len(names) == 1:
            self.cb_conlang_a.set(names[0])
            self.cb_conlang_b.set(names[0])

    def update_conlang_lists(self, engines_dict):
        self.engines_dict.update(engines_dict)
        self.load_available_conlangs()

    def levenshtein_distance_classic(self, s1, s2):
        if len(s1) < len(s2):
            return self.levenshtein_distance_classic(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                ins = prev_row[j + 1] + 1
                dl = curr_row[j] + 1
                sub = prev_row[j] + (c1 != c2)
                curr_row.append(min(ins, dl, sub))
            prev_row = curr_row
        return prev_row[-1]

    def _extract_word(self, entry):
        if isinstance(entry, dict):
            return entry.get('default', '')
        return str(entry)

    def calculate_lavert_approximation(self, prof_a, prof_b, words_a, words_b):
        inv_a = set(prof_a.get('phonotactics', {}).get(
            'consonants', '') + prof_a.get('phonotactics', {}).get('vowels', ''))
        inv_b = set(prof_b.get('phonotactics', {}).get(
            'consonants', '') + prof_b.get('phonotactics', {}).get('vowels', ''))

        if not inv_a or not inv_b:
            return 0.0

        cooccurrences = {char: {} for char in inv_a}

        for wa, wb in zip(words_a, words_b):
            wa_clean = wa.lower()
            wb_clean = wb.lower()
            limit = min(len(wa_clean), len(wb_clean))
            for i in range(limit):
                ca = wa_clean[i]
                cb = wb_clean[i]
                if ca in cooccurrences:
                    cooccurrences[ca][cb] = cooccurrences[ca].get(cb, 0) + 1

        mapped_a = set()
        for ca, mappings in cooccurrences.items():
            if mappings:
                best_match_count = max(mappings.values())
                if best_match_count > 0:
                    mapped_a.add(ca)

        unmapped_a = len(inv_a - mapped_a)

        inv_b_used = set()
        for mappings in cooccurrences.values():
            inv_b_used.update(mappings.keys())

        unmapped_b = len(inv_b - inv_b_used)

        penalty = (unmapped_a + unmapped_b) / (len(inv_a) + len(inv_b))
        base_score = len(mapped_a) / len(inv_a)

        lavert_score = max(0.0, base_score - (penalty * 1.5))
        return min(1.0, lavert_score)

    def calculate_morphosyntax(self, prof_a, prof_b):
        agg_a = prof_a.get('agglutination_strength', 0.5)
        agg_b = prof_b.get('agglutination_strength', 0.5)
        agg_sim = max(0.0, 1.0 - abs(agg_a - agg_b))

        wo_a = prof_a.get('word_order', 'SVO')
        wo_b = prof_b.get('word_order', 'SVO')
        if wo_a == wo_b:
            wo_sim = 1.0
        else:
            shared_positions = sum(1 for i in range(
                min(len(wo_a), len(wo_b))) if wo_a[i] == wo_b[i])
            wo_sim = shared_positions / max(len(wo_a), len(wo_b))

        cases_a = set(prof_a.get('case_system', {}).get('cases', []))
        cases_b = set(prof_b.get('case_system', {}).get('cases', []))
        if not cases_a and not cases_b:
            case_sim = 1.0
        else:
            intersection = len(cases_a.intersection(cases_b))
            union = len(cases_a.union(cases_b))
            case_sim = intersection / union if union > 0 else 0.0

        genders_a = set(prof_a.get('gender_system', {}).get('genders', []))
        genders_b = set(prof_b.get('gender_system', {}).get('genders', []))
        if not genders_a and not genders_b:
            gen_sim = 1.0
        else:
            intersection = len(genders_a.intersection(genders_b))
            union = len(genders_a.union(genders_b))
            gen_sim = intersection / union if union > 0 else 0.0

        return (agg_sim * 0.3) + (wo_sim * 0.4) + (case_sim * 0.15) + (gen_sim * 0.15)

    def calculate_phonotactics(self, prof_a, prof_b):
        syl_a = set(prof_a.get('phonotactics', {}).get(
            'syllable_templates', []))
        syl_b = set(prof_b.get('phonotactics', {}).get(
            'syllable_templates', []))

        if not syl_a and not syl_b:
            syl_sim = 1.0
        else:
            inter = len(syl_a.intersection(syl_b))
            union = len(syl_a.union(syl_b))
            syl_sim = inter / union if union > 0 else 0.0

        mc_a = prof_a.get('phonotactics', {}).get('max_consonant_cluster', 2)
        mc_b = prof_b.get('phonotactics', {}).get('max_consonant_cluster', 2)
        max_c = max(mc_a, mc_b)
        mc_sim = 1.0 - (abs(mc_a - mc_b) / max_c) if max_c > 0 else 1.0

        return (syl_sim * 0.7) + (mc_sim * 0.3)

    def on_calculate_click(self):
        name_a = self.cb_conlang_a.get()
        name_b = self.cb_conlang_b.get()

        if not name_a or not name_b:
            return

        def get_engine(name):
            if name in self.engines_dict:
                return self.engines_dict[name]
            if hasattr(self, 'file_map') and name in self.file_map:
                from engine import OriginalLanguageEngine
                eng = OriginalLanguageEngine(str(self.file_map[name]))
                self.engines_dict[name] = eng
                return eng
            return None

        engine_a = get_engine(name_a)
        engine_b = get_engine(name_b)

        if not engine_a or not engine_b:
            return

        if not self.phonological_distance and hasattr(engine_a, 'phoneme_feature_db'):
            self.phonological_distance = PhonologicalDistance(
                engine_a.phoneme_feature_db)

        self.progress_bar['value'] = 0
        self.update_idletasks()

        cache_a = engine_a.word_cache
        cache_b = engine_b.word_cache
        prof_a = engine_a.profile
        prof_b = engine_b.profile

        shared_lemmas = set(cache_a.keys()).intersection(set(cache_b.keys()))

        lexical_similarities = []
        words_a_lavert = []
        words_b_lavert = []
        self.current_word_data = []

        total_lemmas = len(shared_lemmas)
        step = max(1, total_lemmas // 100) if total_lemmas > 0 else 1

        for i, lemma in enumerate(shared_lemmas):
            wa = self._extract_word(cache_a[lemma])
            wb = self._extract_word(cache_b[lemma])

            dist_classic = self.levenshtein_distance_classic(wa, wb)

            if self.phonological_distance:
                dist_phono = self.phonological_distance.weighted_edit_distance(
                    wa, wb)
                sim = self.phonological_distance.normalized_similarity(wa, wb)
            else:
                dist_phono = float(dist_classic)
                m_len = max(len(wa), len(wb))
                sim = 1.0 - (dist_classic / m_len) if m_len > 0 else 0.0

            lexical_similarities.append(sim)
            words_a_lavert.append(wa)
            words_b_lavert.append(wb)

            self.current_word_data.append({
                "lemma": lemma,
                "wa": wa,
                "wb": wb,
                "dist_classic": dist_classic,
                "dist_phono": round(dist_phono, 2),
                "sim": round(sim * 100, 2)
            })

            if i % step == 0:
                self.progress_bar['value'] = (i / total_lemmas) * 40
                self.update_idletasks()

        lexical_score = sum(lexical_similarities) / \
            len(lexical_similarities) if lexical_similarities else 0.0
        self.progress_bar['value'] = 50

        lavert_score = 0.0
        if self.var_phonetic.get():
            lavert_score = self.calculate_lavert_approximation(
                prof_a, prof_b, words_a_lavert, words_b_lavert)
        self.progress_bar['value'] = 70
        self.update_idletasks()

        morph_score = 0.0
        if self.var_morphosyntax.get():
            morph_score = self.calculate_morphosyntax(prof_a, prof_b)
        self.progress_bar['value'] = 85
        self.update_idletasks()

        phono_score = 0.0
        if self.var_phonotactic.get():
            phono_score = self.calculate_phonotactics(prof_a, prof_b)
        self.progress_bar['value'] = 100
        self.update_idletasks()

        w_lex = 0.40 if self.var_lexical.get() else 0.0
        w_pho = 0.25 if self.var_phonetic.get() else 0.0
        w_mor = 0.20 if self.var_morphosyntax.get() else 0.0
        w_tac = 0.15 if self.var_phonotactic.get() else 0.0

        total_weight = w_lex + w_pho + w_mor + w_tac
        if total_weight == 0:
            final_score = 0.0
        else:
            final_score = ((lexical_score * w_lex) + (lavert_score * w_pho) +
                           (morph_score * w_mor) + (phono_score * w_tac)) / total_weight

        for item in self.tree_stats.get_children():
            self.tree_stats.delete(item)

        stats = [
            ("Sobreposição Lexical", f"{lexical_score*100:.1f}%"),
            ("Aproximação Fonética (Lavert)", f"{lavert_score*100:.1f}%"),
            ("Divergência Morfossintática", f"{morph_score*100:.1f}%"),
            ("Compatibilidade Fonotática", f"{phono_score*100:.1f}%"),
            ("Lemas Compartilhados Analisados", f"{total_lemmas}")
        ]

        for k, v in stats:
            self.tree_stats.insert("", tk.END, values=(k, v))

        self.lbl_percentage.config(text=f"{final_score*100:.1f}%")

        if final_score > 0.85:
            diag = "Inteligibilidade altíssima. Dialetos contíguos."
        elif final_score > 0.60:
            diag = "Inteligibilidade moderada. Comunicação requer esforço."
        elif final_score > 0.30:
            diag = "Inteligibilidade baixa. Falsos cognatos e barreiras gramaticais."
        else:
            diag = "Inteligibilidade nula. Troncos isolados ou mutações extremas."

        self.lbl_summary.config(text=f"Análise concluída. {diag}")

        self.btn_export.config(state="normal")
        self.apply_dict_filter()

    def apply_dict_filter(self):
        try:
            min_sim = float(self.spin_filter.get())
        except:
            min_sim = 0.0

        for item in self.tree_words.get_children():
            self.tree_words.delete(item)

        sorted_data = sorted(self.current_word_data,
                             key=lambda x: x['sim'], reverse=True)

        for row in sorted_data:
            if row['sim'] >= min_sim:
                self.tree_words.insert("", tk.END, values=(
                    row['lemma'], row['wa'], row['wb'], row['dist_classic'], row['dist_phono'], f"{row['sim']}%"))

    def on_export_click(self):
        if not self.current_word_data:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Exportar Dicionário de Proximidade"
        )

        if file_path:
            try:
                with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["Conceito", "Palavra A", "Palavra B", "Distancia Classica", "Distancia Fonologica", "Similaridade (%)"])
                    for row in self.current_word_data:
                        writer.writerow(
                            [row['lemma'], row['wa'], row['wb'], row['dist_classic'], row['dist_phono'], row['sim']])
                messagebox.showinfo(
                    "Sucesso", "Dicionário exportado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar: {str(e)}")

    def update_engine(self, engine):
        self.engine = engine
        if engine and hasattr(engine, 'phoneme_feature_db'):
            self.phonological_distance = PhonologicalDistance(
                engine.phoneme_feature_db)
