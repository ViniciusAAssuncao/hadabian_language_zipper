import tkinter as tk
from tkinter import ttk


class IntelligibilityTab(ttk.Frame):
    def __init__(self, parent, colors, engine=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.target_engine = None
        self.setup_ui()

    def update_engine(self, engine):
        self.engine = engine
        if self.engine:
            self.lbl_source_lang.config(
                text=f"Conlang Base (A): {self.engine.profile_id}")
        else:
            self.lbl_source_lang.config(text="Conlang Base (A): Nenhuma")

    def setup_ui(self):
        top_frame = ttk.Frame(self, padding=15)
        top_frame.pack(fill=tk.X)

        self.lbl_source_lang = ttk.Label(top_frame, text="Conlang Base (A): Nenhuma", font=(
            "Segoe UI", 11, "bold"), foreground=self.colors["accent"])
        self.lbl_source_lang.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(top_frame, text="ID Conlang Alvo (B):",
                  foreground=self.colors["fg_secondary"]).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_target_id = ttk.Entry(
            top_frame, font=("Segoe UI", 10), width=20)
        self.entry_target_id.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_load_target = ttk.Button(
            top_frame, text="Carregar Alvo", style="Secondary.TButton")
        self.btn_load_target.pack(side=tk.LEFT)

        self.lbl_target_status = ttk.Label(
            top_frame, text="[Aguardando...]", foreground=self.colors["fg_secondary"])
        self.lbl_target_status.pack(side=tk.LEFT, padx=(10, 0))

        config_frame = ttk.LabelFrame(
            self, text="Parâmetros da Equação", padding=15)
        config_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Label(config_frame, text="Peso Léxico (λL):").pack(
            side=tk.LEFT, padx=(0, 5))
        self.weight_l = ttk.Entry(config_frame, width=5)
        self.weight_l.insert(0, "0.8")
        self.weight_l.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(config_frame, text="Peso Sintático (λS):").pack(
            side=tk.LEFT, padx=(0, 5))
        self.weight_s = ttk.Entry(config_frame, width=5)
        self.weight_s.insert(0, "0.1")
        self.weight_s.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(config_frame, text="Peso Morfológico (λM):").pack(
            side=tk.LEFT, padx=(0, 5))
        self.weight_m = ttk.Entry(config_frame, width=5)
        self.weight_m.insert(0, "0.1")
        self.weight_m.pack(side=tk.LEFT, padx=(0, 20))

        self.btn_calculate = ttk.Button(
            config_frame, text="⟳ Processar Equação de Lebe-Naiul", style="Accent.TButton")
        self.btn_calculate.pack(side=tk.RIGHT)

        result_frame = ttk.Frame(self, padding=15)
        result_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Label(result_frame, text="Índice de Inteligibilidade Interlinguística:", font=(
            "Segoe UI", 12)).pack(anchor="center")
        self.lbl_final_score = ttk.Label(result_frame, text="0.00%", font=(
            "Segoe UI", 36, "bold"), foreground=self.colors["success"])
        self.lbl_final_score.pack(anchor="center", pady=10)

        self.progress_score = ttk.Progressbar(
            result_frame, orient="horizontal", mode="determinate", length=400)
        self.progress_score.pack(anchor="center")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.tab_metrics = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_metrics, text="Métricas Globais")
        self.setup_metrics_tab()

        self.tab_lexical = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_lexical, text="Análise Léxico-Fonética")
        self.setup_lexical_tab()

        self.tab_cognates = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_cognates, text="Matriz & Falsos Cognatos")
        self.setup_cognates_tab()

    def setup_metrics_tab(self):
        frame_s = ttk.Frame(self.tab_metrics)
        frame_s.pack(fill=tk.X, pady=5)
        ttk.Label(frame_s, text="Similaridade Sintática (S):",
                  width=30).pack(side=tk.LEFT)
        self.lbl_score_s = ttk.Label(
            frame_s, text="0.00%", font=("Segoe UI", 10, "bold"))
        self.lbl_score_s.pack(side=tk.LEFT)

        frame_m = ttk.Frame(self.tab_metrics)
        frame_m.pack(fill=tk.X, pady=5)
        ttk.Label(frame_m, text="Similaridade Morfológica (M):",
                  width=30).pack(side=tk.LEFT)
        self.lbl_score_m = ttk.Label(
            frame_m, text="0.00%", font=("Segoe UI", 10, "bold"))
        self.lbl_score_m.pack(side=tk.LEFT)

        frame_l = ttk.Frame(self.tab_metrics)
        frame_l.pack(fill=tk.X, pady=5)
        ttk.Label(frame_l, text="Similaridade Léxica Agregada (L):",
                  width=30).pack(side=tk.LEFT)
        self.lbl_score_l = ttk.Label(
            frame_l, text="0.00%", font=("Segoe UI", 10, "bold"))
        self.lbl_score_l.pack(side=tk.LEFT)

        frame_h = ttk.Frame(self.tab_metrics)
        frame_h.pack(fill=tk.X, pady=5)
        ttk.Label(frame_h, text="Fator Histórico Médio (β):",
                  width=30).pack(side=tk.LEFT)
        self.lbl_score_h = ttk.Label(
            frame_h, text="1.00", font=("Segoe UI", 10, "bold"))
        self.lbl_score_h.pack(side=tk.LEFT)

    def setup_lexical_tab(self):
        columns = ("concept", "word_a", "word_b",
                   "dist_fon", "morf_factor", "final_sim")
        self.tree_lexical = ttk.Treeview(
            self.tab_lexical, columns=columns, show="headings", style="Treeview")

        self.tree_lexical.heading("concept", text="Conceito Semântico")
        self.tree_lexical.heading("word_a", text="Palavra (A)")
        self.tree_lexical.heading("word_b", text="Palavra (B)")
        self.tree_lexical.heading("dist_fon", text="Distância Fonética (φ)")
        self.tree_lexical.heading(
            "morf_factor", text="Corresp. Morfológica (α)")
        self.tree_lexical.heading("final_sim", text="Similaridade Final")

        self.tree_lexical.column("concept", width=150)
        self.tree_lexical.column("word_a", width=120)
        self.tree_lexical.column("word_b", width=120)
        self.tree_lexical.column("dist_fon", width=120, anchor="center")
        self.tree_lexical.column("morf_factor", width=150, anchor="center")
        self.tree_lexical.column("final_sim", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(
            self.tab_lexical, orient=tk.VERTICAL, command=self.tree_lexical.yview)
        self.tree_lexical.configure(yscroll=scrollbar.set)

        self.tree_lexical.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_cognates_tab(self):
        self.text_cognates = tk.Text(self.tab_cognates, bg=self.colors["input_bg"], fg=self.colors["fg_primary"], font=(
            "Consolas", 10), borderwidth=0, highlightthickness=1)
        self.text_cognates.pack(fill=tk.BOTH, expand=True)
        self.text_cognates.insert(
            "1.0", "Aguardando cálculo para gerar matriz de confusão fonética e falsos cognatos...")
        self.text_cognates.config(state="disabled")
