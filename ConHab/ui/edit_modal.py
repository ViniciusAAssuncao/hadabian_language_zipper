import tkinter as tk
from tkinter import ttk


class EditWordModal(tk.Toplevel):
    def __init__(self, parent, colors, lemma, current_data, on_save):
        super().__init__(parent)
        self.colors = colors
        self.lemma = lemma
        self.current_data = current_data
        self.on_save = on_save

        self.title("Editar Palavra")
        self.geometry("400x350")
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

        self.entry_word = ttk.Entry(main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
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

        self.entry_origin = ttk.Entry(main_frame, font=("Segoe UI", 11), foreground=self.colors["text"])
        self.entry_origin.pack(fill=tk.X, pady=(0, 15))

        initial_origin = self.current_data.get("origin", "") if isinstance(
            self.current_data, dict) else "custom"
        self.entry_origin.insert(0, initial_origin)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="Cancelar",
            style="Secondary.TButton",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame,
            text="Salvar Alterações",
            style="Accent.TButton",
            command=self.save
        ).pack(side=tk.RIGHT)

    def save(self):
        new_word = self.entry_word.get().strip()
        new_origin = self.entry_origin.get().strip()

        if not new_word:
            return

        updated_data = {
            "default": new_word,
            "origin": new_origin,
            "synsets": self.current_data.get("synsets", []) if isinstance(self.current_data, dict) else []
        }

        self.on_save(self.lemma, updated_data)
        self.destroy()
