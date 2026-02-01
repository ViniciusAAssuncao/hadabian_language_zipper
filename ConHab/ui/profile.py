import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading


class ProfileTab(ttk.Frame):
    def __init__(self, parent, colors):
        super().__init__(parent)
        self.colors = colors
        self.file_path = None
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

        self.text_editor = scrolledtext.ScrolledText(
            self,
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
            self, orient=tk.HORIZONTAL, command=self.text_editor.xview)
        self.text_editor.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(fill=tk.X)

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
