import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading


class ProfileTab(ttk.Frame):
    def __init__(self, parent, colors):
        super().__init__(parent)
        self.colors = colors
        self.file_path = None
        self.engine = None
        self.setup_ui()

    def setup_ui(self):
        toolbar = ttk.Frame(self, padding=(0, 0, 0, 10))
        toolbar.pack(fill=tk.X)

        self.btn_save = ttk.Button(
            toolbar,
            text="💾 Salvar JSON",
            style="Secondary.TButton",
            command=self.save_json,
            state="disabled"
        )
        self.btn_save.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_revert = ttk.Button(
            toolbar,
            text="↺ Reverter",
            style="Secondary.TButton",
            command=self.reload_json,
            state="disabled"
        )
        self.btn_revert.pack(side=tk.LEFT)

        self.lbl_status = ttk.Label(
            toolbar,
            text="",
            font=("Segoe UI", 9),
            foreground=self.colors["fg_secondary"]
        )
        self.lbl_status.pack(side=tk.LEFT, padx=15)

        self.main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        editor_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(editor_frame, weight=3)

        self.text_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            bg=self.colors["input_bg"],
            fg=self.colors["fg_primary"],
            insertbackground=self.colors["accent"],
            font=("Consolas", 11),
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors["bg_sec"],
            highlightcolor=self.colors["accent"]
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)

        h_scroll = ttk.Scrollbar(
            editor_frame, orient=tk.HORIZONTAL, command=self.text_editor.xview)
        self.text_editor.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(fill=tk.X)

        self.analysis_frame = ttk.LabelFrame(
            self.main_pane, text="Diagnóstico Fonológico", padding=10)
        self.main_pane.add(self.analysis_frame, weight=1)

        self._setup_analysis_ui()

    def _setup_analysis_ui(self):
        top_bar = ttk.Frame(self.analysis_frame)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        self.btn_reanalyze = ttk.Button(
            top_bar,
            text="Reanalisar",
            style="Secondary.TButton",
            command=self.run_analysis
        )
        self.btn_reanalyze.pack(side=tk.LEFT)

        self.lbl_analysis_status = ttk.Label(
            top_bar,
            text="",
            foreground=self.colors["fg_secondary"]
        )
        self.lbl_analysis_status.pack(side=tk.LEFT, padx=10)

        content_frame = ttk.Frame(self.analysis_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        scores_frame = ttk.Frame(content_frame)
        scores_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        ttk.Label(scores_frame, text="Dispersão Vocálica:").pack(anchor="w")
        self.vowel_prog = ttk.Progressbar(
            scores_frame, length=150, mode="determinate")
        self.vowel_prog.pack(anchor="w", pady=(2, 2))
        self.lbl_vowel_score = ttk.Label(scores_frame, text="0%")
        self.lbl_vowel_score.pack(anchor="w", pady=(0, 10))

        ttk.Label(scores_frame, text="Dispersão Consonantal:").pack(anchor="w")
        self.cons_prog = ttk.Progressbar(
            scores_frame, length=150, mode="determinate")
        self.cons_prog.pack(anchor="w", pady=(2, 2))
        self.lbl_cons_score = ttk.Label(scores_frame, text="0%")
        self.lbl_cons_score.pack(anchor="w")

        lists_frame = ttk.Frame(content_frame)
        lists_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(lists_frame, text="Avisos:", font=(
            "Segoe UI", 9, "bold")).pack(anchor="w")
        self.list_warnings = tk.Listbox(
            lists_frame,
            height=4,
            bg=self.colors["input_bg"],
            fg=self.colors["error"],
            borderwidth=1,
            relief="solid"
        )
        self.list_warnings.pack(fill=tk.X, pady=(2, 10))

        ttk.Label(lists_frame, text="Sugestões de Fonemas:",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.list_suggestions = tk.Listbox(
            lists_frame,
            height=3,
            bg=self.colors["input_bg"],
            fg=self.colors["success"],
            borderwidth=1,
            relief="solid"
        )
        self.list_suggestions.pack(fill=tk.X, pady=(2, 0))

    def update_engine(self, engine):
        self.engine = engine
        self.run_analysis()

    def run_analysis(self):
        if not hasattr(self, 'engine') or not self.engine:
            return

        raw_content = self.text_editor.get("1.0", tk.END).strip()
        if not raw_content:
            return

        try:
            profile_data = json.loads(raw_content)
        except json.JSONDecodeError:
            self.lbl_analysis_status.config(text="JSON Inválido")
            return

        self.lbl_analysis_status.config(text="Calculando...")
        self.btn_reanalyze.config(state="disabled")

        threading.Thread(target=self._analysis_worker,
                         args=(profile_data,), daemon=True).start()

    def _analysis_worker(self, profile_data):
        try:
            from handlers.typology import PhonologicalDispersion
            dispersion = PhonologicalDispersion(self.engine.phoneme_feature_db)
            analysis = dispersion.analyze_inventory(profile_data)
            self.after(0, lambda: self._on_analysis_success(analysis))
        except Exception as e:
            self.after(0, lambda: self._on_analysis_error(str(e)))

    def _on_analysis_success(self, analysis):
        self.lbl_analysis_status.config(text="Concluído")
        self.btn_reanalyze.config(state="normal")

        v_score = int(analysis.get("vowel_dispersion", 0) * 100)
        c_score = int(analysis.get("consonant_dispersion", 0) * 100)

        self.vowel_prog["value"] = v_score
        self.lbl_vowel_score.config(text=f"{v_score}%")

        self.cons_prog["value"] = c_score
        self.lbl_cons_score.config(text=f"{c_score}%")

        self.list_warnings.delete(0, tk.END)
        for w in analysis.get("warnings", []):
            self.list_warnings.insert(tk.END, w)

        self.list_suggestions.delete(0, tk.END)
        suggestions = analysis.get("suggestions", {})
        v_sug = ", ".join(suggestions.get("vowels", []))
        c_sug = ", ".join(suggestions.get("consonants", []))
        if v_sug:
            self.list_suggestions.insert(tk.END, f"Vogais: {v_sug}")
        if c_sug:
            self.list_suggestions.insert(tk.END, f"Consoantes: {c_sug}")

    def _on_analysis_error(self, error_msg):
        self.lbl_analysis_status.config(text="Erro na análise")
        self.btn_reanalyze.config(state="normal")

    def load_profile(self, path):
        self.file_path = path
        self.reload_json()

    def reload_json(self):
        if not self.file_path:
            return

        self.lbl_status.config(text="Carregando arquivo...")
        self.btn_save.config(state="disabled")
        self.btn_revert.config(state="disabled")
        self.text_editor.delete("1.0", tk.END)

        threading.Thread(target=self._read_file_worker, daemon=True).start()

    def _read_file_worker(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.after(0, lambda: self._on_load_success(content))
        except Exception as e:
            self.after(0, lambda: self._on_load_error(str(e)))

    def _on_load_success(self, content):
        self.text_editor.insert("1.0", content)
        self.lbl_status.config(
            text=f"Arquivo carregado: {self.file_path.name}")
        self.btn_save.config(state="normal")
        self.btn_revert.config(state="normal")

    def _on_load_error(self, error_msg):
        self.lbl_status.config(
            text="Erro ao carregar arquivo", foreground=self.colors["error"])
        messagebox.showerror(
            "Erro de Leitura", f"Não foi possível ler o arquivo:\n{error_msg}")

    def save_json(self):
        if not self.file_path:
            return

        raw_content = self.text_editor.get("1.0", tk.END).strip()

        try:
            json_data = json.loads(raw_content)
            formatted_content = json.dumps(
                json_data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            messagebox.showerror(
                "JSON Inválido", f"Erro de sintaxe:\n{str(e)}")
            return

        self.lbl_status.config(text="Salvando...")
        self.btn_save.config(state="disabled")

        threading.Thread(
            target=self._save_file_worker,
            args=(formatted_content,),
            daemon=True
        ).start()

    def _save_file_worker(self, content):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.after(0, lambda: self._on_save_success(content))
        except Exception as e:
            self.after(0, lambda: self._on_save_error(str(e)))

    def _on_save_success(self, content):
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", content)
        self.lbl_status.config(text="Salvo com sucesso!",
                               foreground=self.colors["success"])
        self.btn_save.config(state="normal")
        self.after(3000, lambda: self.lbl_status.config(
            text=f"Arquivo: {self.file_path.name}", foreground=self.colors["fg_secondary"]))

    def _on_save_error(self, error_msg):
        self.lbl_status.config(text="Erro ao salvar",
                               foreground=self.colors["error"])
        self.btn_save.config(state="normal")
        messagebox.showerror(
            "Erro de Gravação", f"Não foi possível salvar o arquivo:\n{error_msg}")
