import tkinter as tk
from tkinter import ttk, messagebox
import random


class GramatakiTab(ttk.Frame):
    def __init__(self, parent, colors, engine=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.setup_ui()

    def update_engine(self, engine):
        self.engine = engine

    def setup_ui(self):
        main_split = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_split.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        input_frame = ttk.Frame(main_split, style="Card.TFrame")
        main_split.add(input_frame, weight=1)

        header_lbl = ttk.Label(
            input_frame,
            text="DEFINIÇÃO SEMÂNTICA",
            style="SubHeader.TLabel",
            background=self.colors["card_bg"]
        )
        header_lbl.pack(fill=tk.X, pady=(10, 5), padx=10)

        lbl_meaning = ttk.Label(
            input_frame,
            text="Intenção / Conceito:",
            background=self.colors["card_bg"],
            foreground=self.colors["fg_secondary"]
        )
        lbl_meaning.pack(anchor="w", padx=10)

        self.txt_meaning = tk.Text(
            input_frame,
            height=4,
            bg=self.colors["input_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            font=("Segoe UI", 10),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["bg_sec"],
            highlightcolor=self.colors["accent"]
        )
        self.txt_meaning.pack(fill=tk.X, padx=10, pady=(0, 10))

        lbl_params = ttk.Label(
            input_frame,
            text="Parâmetros de Construção:",
            background=self.colors["card_bg"],
            foreground=self.colors["fg_secondary"]
        )
        lbl_params.pack(anchor="w", padx=10, pady=(5, 0))

        params_container = ttk.Frame(input_frame, style="Card.TFrame")
        params_container.pack(fill=tk.X, padx=10, pady=5)

        self.var_abstract = tk.BooleanVar()
        chk_abstract = ttk.Checkbutton(
            params_container,
            text="Conceito Abstrato",
            variable=self.var_abstract,
            style="Switch.TCheckbutton"
        )
        chk_abstract.pack(anchor="w", pady=2)

        self.var_force_loan = tk.BooleanVar()
        chk_loan = ttk.Checkbutton(
            params_container,
            text="Forçar Empréstimo",
            variable=self.var_force_loan,
            style="Switch.TCheckbutton"
        )
        chk_loan.pack(anchor="w", pady=2)

        lbl_register = ttk.Label(
            params_container,
            text="Registro / Tom:",
            background=self.colors["card_bg"],
            foreground=self.colors["fg_secondary"],
            font=("Segoe UI", 9)
        )
        lbl_register.pack(anchor="w", pady=(10, 2))

        self.combo_register = ttk.Combobox(
            params_container,
            values=["Neutro", "Formal", "Poético", "Arcaico", "Vulgar"],
            state="readonly"
        )
        self.combo_register.current(0)
        self.combo_register.pack(fill=tk.X)

        btn_container = ttk.Frame(input_frame, style="Card.TFrame")
        btn_container.pack(fill=tk.X, padx=10, pady=20)

        self.btn_generate = ttk.Button(
            btn_container,
            text="⚙ GERAR GRAMATAKI",
            style="Accent.TButton",
            command=self.on_generate
        )
        self.btn_generate.pack(fill=tk.X, pady=5)

        self.btn_clear = ttk.Button(
            btn_container,
            text="Limpar Campos",
            style="Secondary.TButton",
            command=self.on_clear
        )
        self.btn_clear.pack(fill=tk.X)

        output_frame = ttk.Frame(main_split)
        main_split.add(output_frame, weight=2)

        out_header = ttk.Label(
            output_frame,
            text="RESULTADOS E VARIAÇÕES",
            style="SubHeader.TLabel"
        )
        out_header.pack(fill=tk.X, pady=(0, 10))

        tree_container = ttk.Frame(output_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        cols = ("lemma", "pos", "score", "gloss", "raw_meaning")
        self.result_tree = ttk.Treeview(
            tree_container,
            columns=cols,
            displaycolumns=("lemma", "pos", "score", "gloss"),
            show="headings",
            style="Treeview"
        )

        self.result_tree.heading("lemma", text="Lema Gerado")
        self.result_tree.heading("pos", text="POS")
        self.result_tree.heading("score", text="Precisão")
        self.result_tree.heading("gloss", text="Glose / Notas")

        self.result_tree.column(
            "lemma", width=250, minwidth=100, stretch=False)
        self.result_tree.column(
            "pos", width=80, minwidth=50, anchor="center", stretch=False)
        self.result_tree.column(
            "score", width=80, minwidth=50, anchor="center", stretch=False)
        self.result_tree.column(
            "gloss", width=800, minwidth=200, stretch=False)

        v_scrollbar = ttk.Scrollbar(
            tree_container, orient=tk.VERTICAL, command=self.result_tree.yview)
        h_scrollbar = ttk.Scrollbar(
            tree_container, orient=tk.HORIZONTAL, command=self.result_tree.xview)

        self.result_tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.result_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        details_frame = ttk.Frame(output_frame, height=150)
        details_frame.pack(fill=tk.X, pady=(10, 0))

        lbl_details = ttk.Label(
            details_frame,
            text="ANÁLISE ESTRUTURAL",
            style="SubHeader.TLabel"
        )
        lbl_details.pack(anchor="w")

        self.txt_details = tk.Text(
            details_frame,
            height=6,
            bg=self.colors["input_bg"],
            fg=self.colors["fg_primary"],
            relief="flat",
            state="disabled",
            font=("Consolas", 10)
        )
        self.txt_details.pack(fill=tk.BOTH, expand=True, pady=5)

        action_bar = ttk.Frame(output_frame)
        action_bar.pack(fill=tk.X, pady=10)

        self.btn_delete = ttk.Button(
            action_bar,
            text="🗑 Excluir Selecionado",
            style="Secondary.TButton",
            state="disabled",
            command=self.on_delete
        )
        self.btn_delete.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_accept = ttk.Button(
            action_bar,
            text="✔ Incorporar ao Léxico Gramataki",
            style="Accent.TButton",
            state="disabled",
            command=self.on_accept
        )
        self.btn_accept.pack(side=tk.RIGHT)

        self.result_tree.bind("<<TreeviewSelect>>", self.on_select_result)
        self.result_tree.bind("<Delete>", lambda e: self.on_delete())

    def on_generate(self):
        if not self.engine:
            messagebox.showwarning("Aviso", "Motor não inicializado.")
            return

        meaning = self.txt_meaning.get("1.0", "end-1c").strip()
        if not meaning:
            messagebox.showwarning(
                "Aviso", "Por favor, insira um significado ou conceito.")
            return

        for child in self.result_tree.get_children():
            item_meaning = self.result_tree.set(child, "raw_meaning")
            if item_meaning == meaning:
                self.result_tree.delete(child)

        options = {
            'abstract': self.var_abstract.get(),
            'force_loan': self.var_force_loan.get(),
            'register': self.combo_register.get(),
            'salt': random.randint(0, 1000000)
        }

        results = self.engine.generate_gramataki_candidates(meaning, options)

        for res in results:
            self.result_tree.insert("", "end", values=(
                res.get('lemma', '???'),
                res.get('pos', 'UNK'),
                f"{res.get('score', 0)}%",
                res.get('gloss', ''),
                meaning
            ))

    def on_clear(self):
        self.txt_meaning.delete("1.0", tk.END)
        self.var_abstract.set(False)
        self.var_force_loan.set(False)
        self.combo_register.current(0)
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.txt_details.config(state="normal")
        self.txt_details.delete("1.0", tk.END)
        self.txt_details.config(state="disabled")
        self.btn_accept.state(["disabled"])
        self.btn_delete.state(["disabled"])

    def on_select_result(self, event):
        selected = self.result_tree.selection()
        if selected:
            self.btn_accept.state(["!disabled"])
            self.btn_delete.state(["!disabled"])
            item = self.result_tree.item(selected[0])
            values = item['values']

            analysis_text = f"Lema: {values[0]}\nClasse: {values[1]}\nNotas: {values[3]}\nOrigem: Gerado via Gramataki Engine"

            self.txt_details.config(state="normal")
            self.txt_details.delete("1.0", tk.END)
            self.txt_details.insert("1.0", analysis_text)
            self.txt_details.config(state="disabled")
        else:
            self.btn_accept.state(["disabled"])
            self.btn_delete.state(["disabled"])

    def on_delete(self):
        selected_items = self.result_tree.selection()
        if not selected_items:
            return

        for item in selected_items:
            self.result_tree.delete(item)

        self.on_select_result(None)

    def on_accept(self):
        selected = self.result_tree.selection()
        if not selected:
            return

        item = self.result_tree.item(selected[0])
        values = item['values']

        entry = {
            'lemma': values[0],
            'pos': values[1],
            'meaning': self.txt_meaning.get("1.0", "end-1c").strip() or values[3],
            'gloss': values[3],
            'origin': 'gramataki',
            'unique_constraint': 'meaning'
        }

        try:
            self.engine.save_gramataki_entry(entry)
            messagebox.showinfo(
                "Sucesso", f"O termo '{values[0]}' foi processado no dicionário Gramataki.")
            self.on_clear()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar termo: {str(e)}")
