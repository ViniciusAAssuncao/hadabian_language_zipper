import tkinter as tk
from tkinter import ttk


class MassEditModal(tk.Toplevel):
    def __init__(self, parent, colors, selected_count, on_apply):
        super().__init__(parent)
        self.colors = colors
        self.selected_count = selected_count
        self.on_apply = on_apply

        self.title(f"Edição em Massa ({selected_count} itens)")
        self.geometry("500x600")
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
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        warning_frame = tk.Frame(main_frame, bg="#ff4444", padx=10, pady=10)
        warning_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            warning_frame,
            text="⚠️ CUIDADO: MODO DOOMSDAY",
            font=("Segoe UI", 12, "bold"),
            bg="#ff4444",
            fg="white"
        ).pack(anchor="w")

        tk.Label(
            warning_frame,
            text=f"As alterações abaixo substituirão os valores de TODOS os {self.selected_count} itens selecionados.",
            font=("Segoe UI", 10),
            bg="#ff4444",
            fg="white",
            wraplength=440,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))

        self.vars = {
            "default": tk.BooleanVar(),
            "origin": tk.BooleanVar(),
            "pos": tk.BooleanVar(),
            "tags": tk.BooleanVar()
        }

        self.create_field(main_frame, "Tradução (Conlang)", "default")
        self.create_field(main_frame, "Origem", "origin")
        self.create_field(main_frame, "POS (Classe Gramatical)", "pos")
        self.create_field(main_frame, "Tags (substituir todas)", "tags")

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))

        ttk.Button(
            btn_frame,
            text=f"APLICAR EM {self.selected_count} ITENS",
            style="Secondary.TButton",
            command=self.apply
        ).pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self.destroy
        ).pack(fill=tk.X)

    def create_field(self, parent, label_text, key):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10)

        header = ttk.Frame(frame)
        header.pack(fill=tk.X, pady=(0, 5))

        cb = ttk.Checkbutton(
            header,
            text=label_text,
            variable=self.vars[key],
            command=lambda k=key: self.toggle_entry(k)
        )
        cb.pack(side=tk.LEFT)

        entry = ttk.Entry(frame, font=("Segoe UI", 11), state="disabled")
        entry.pack(fill=tk.X)

        setattr(self, f"entry_{key}", entry)

    def toggle_entry(self, key):
        entry = getattr(self, f"entry_{key}")
        if self.vars[key].get():
            entry.config(state="normal")
        else:
            entry.config(state="disabled")

    def apply(self):
        updates = {}
        if self.vars["default"].get():
            updates["default"] = self.entry_default.get().strip()
        if self.vars["origin"].get():
            updates["origin"] = self.entry_origin.get().strip()
        if self.vars["pos"].get():
            updates["pos"] = self.entry_pos.get().strip()
        if self.vars["tags"].get():
            tags_str = self.entry_tags.get().strip()
            updates["tags"] = [t.strip()
                               for t in tags_str.split(",") if t.strip()]

        if updates:
            self.on_apply(updates)
        self.destroy()
