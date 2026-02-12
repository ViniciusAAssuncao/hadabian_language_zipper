import tkinter as tk
from tkinter import ttk, messagebox


class IdiomTab(ttk.Frame):
    def __init__(self, parent, colors, engine=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.manager = engine.idiom_manager if engine else None
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

        edit_frame = ttk.LabelFrame(
            self.paned, text="Editor de Expressão", padding=10)
        self.paned.add(edit_frame, weight=1)

        ttk.Label(edit_frame, text="Expressão Original (ex: 'cair do cavalo'):").pack(
            anchor="w")
        self.entry_expr = ttk.Entry(edit_frame, foreground="black")
        self.entry_expr.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(edit_frame, text="Traduzir como (Lema único):").pack(
            anchor="w")
        self.entry_target = ttk.Entry(edit_frame, foreground="black")
        self.entry_target.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(edit_frame, text="Isso buscará este lema no dicionário da Conlang.",
                  font=("Segoe UI", 8), foreground="gray").pack(anchor="w", pady=(0, 10))

        ttk.Label(edit_frame, text="Tags/Contexto (opcional):").pack(anchor="w")
        self.entry_tags = ttk.Entry(edit_frame, foreground="black")
        self.entry_tags.pack(fill=tk.X, pady=(0, 10))

        btn_frame = ttk.Frame(edit_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_save = ttk.Button(
            btn_frame, text="Salvar / Adicionar", command=self.save_idiom, style="Secondary.TButton")
        self.btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_delete = ttk.Button(
            btn_frame, text="Excluir", command=self.delete_idiom)
        self.btn_delete.pack(side=tk.RIGHT, padx=(5, 0))
        self.btn_delete.state(['disabled'])

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

        self.entry_expr.delete(0, tk.END)
        self.entry_target.delete(0, tk.END)
        self.entry_tags.delete(0, tk.END)
        self.btn_delete.state(['disabled'])

    def delete_idiom(self):
        if not self.manager:
            messagebox.showwarning(
                "Aviso", "Carregue um perfil de linguagem primeiro.")
            return

        expr = self.entry_expr.get().strip()
        if expr:
            self.manager.delete_idiom(expr)
            self.refresh_list()
            self.entry_expr.delete(0, tk.END)
            self.entry_target.delete(0, tk.END)
            self.entry_tags.delete(0, tk.END)
            self.btn_delete.state(['disabled'])
