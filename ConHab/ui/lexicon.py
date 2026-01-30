import tkinter as tk
from tkinter import ttk
import math
from ui.edit_modal import EditWordModal


class LexiconTab(ttk.Frame):
    def __init__(self, parent, colors):
        super().__init__(parent)
        self.colors = colors
        self.tree = None
        self.search_var = tk.StringVar()
        self.items_per_page = 25
        self.current_page = 1
        self.total_pages = 1
        self.all_items = []
        self.filtered_items = []
        self.engine = None
        self.setup_ui()

    def setup_ui(self):
        search_frame = ttk.Frame(self)
        search_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        search_container = ttk.Frame(search_frame, style="TFrame")
        search_container.pack(fill=tk.X, expand=True)

        lbl_search = ttk.Label(
            search_container,
            text="Pesquisar:",
            font=("Segoe UI", 10, "bold"),
            foreground=self.colors["fg_secondary"]
        )
        lbl_search.pack(side=tk.LEFT, padx=(0, 10))

        self.entry_search = ttk.Entry(
            search_container,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            foreground=self.colors["text"],
        )
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_search.bind("<KeyRelease>", self.on_search)

        self.btn_edit = ttk.Button(
            search_container,
            text="✎ Editar Palavra",
            style="Secondary.TButton",
            command=self.on_edit_click,
            state="disabled"
        )
        self.btn_edit.pack(side=tk.LEFT, padx=(10, 0))

        main_content = ttk.Frame(self)
        main_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns = ("lemma", "word", "origin", "tags")
        self.tree = ttk.Treeview(
            main_content, columns=columns, show="headings", style="Treeview"
        )

        self.tree.heading("lemma", text="Lema (Origem)")
        self.tree.heading("word", text="Palavra (Conlang)")
        self.tree.heading("origin", text="Origem")
        self.tree.heading("tags", text="Tags")

        self.tree.column("lemma", width=150)
        self.tree.column("word", width=150)
        self.tree.column("origin", width=100)
        self.tree.column("tags", width=200)

        scrollbar = ttk.Scrollbar(
            main_content, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        pagination_frame = ttk.Frame(self)
        pagination_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        container = ttk.Frame(pagination_frame)
        container.pack(anchor="center")

        self.btn_prev = ttk.Button(
            container, text="< Anterior", style="Secondary.TButton",
            command=self.prev_page, state="disabled"
        )
        self.btn_prev.pack(side=tk.LEFT, padx=10)

        self.lbl_page = ttk.Label(
            container, text="Página 0 de 0",
            font=("Segoe UI", 10), foreground=self.colors["fg_secondary"]
        )
        self.lbl_page.pack(side=tk.LEFT, padx=15)

        self.btn_next = ttk.Button(
            container, text="Próxima >", style="Secondary.TButton",
            command=self.next_page, state="disabled"
        )
        self.btn_next.pack(side=tk.LEFT, padx=10)

    def refresh(self, engine):
        self.engine = engine
        self.all_items = []
        if not engine or not engine.word_cache:
            self.filtered_items = []
            self.update_pagination_calc()
            self.update_view()
            return

        for lemma, entry in engine.word_cache.items():
            if isinstance(entry, dict):
                word = entry.get("default", "")
                origin = entry.get("origin", "")
                tags = ""
                if "synsets" in entry:
                    all_tags = []
                    for s in entry["synsets"]:
                        all_tags.extend(s.get("tags", []))
                    tags = ", ".join(set(all_tags))
            else:
                word = str(entry)
                origin = "legacy/unknown"
                tags = ""

            self.all_items.append((lemma, word, origin, tags))

        self.all_items.sort(key=lambda x: x[0].lower())
        self.on_search()

    def on_search(self, event=None):
        query = self.search_var.get().strip().lower()

        if not query:
            self.filtered_items = list(self.all_items)
        else:
            self.filtered_items = [
                item for item in self.all_items
                if query in item[0].lower() or
                query in item[1].lower() or
                query in item[3].lower()
            ]

        self.current_page = 1
        self.update_pagination_calc()
        self.update_view()

    def update_pagination_calc(self):
        total_items = len(self.filtered_items)
        if total_items == 0:
            self.total_pages = 1
        else:
            self.total_pages = math.ceil(total_items / self.items_per_page)

    def update_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.btn_edit.state(["disabled"])

        if not self.filtered_items:
            self.lbl_page.config(text="0 resultados")
            self.btn_prev.state(["disabled"])
            self.btn_next.state(["disabled"])
            return

        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        page_items = self.filtered_items[start_index:end_index]

        for item in page_items:
            self.tree.insert("", tk.END, values=item)

        self.lbl_page.config(
            text=f"Página {self.current_page} de {self.total_pages} ({len(self.filtered_items)} itens)")

        if self.current_page <= 1:
            self.btn_prev.state(["disabled"])
        else:
            self.btn_prev.state(["!disabled"])

        if self.current_page >= self.total_pages:
            self.btn_next.state(["disabled"])
        else:
            self.btn_next.state(["!disabled"])

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_view()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_view()

    def on_selection_change(self, event):
        selected = self.tree.selection()
        if selected:
            self.btn_edit.state(["!disabled"])
        else:
            self.btn_edit.state(["disabled"])

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.open_edit_modal()

    def on_edit_click(self):
        self.open_edit_modal()

    def open_edit_modal(self):
        selected = self.tree.selection()
        if not selected:
            return

        item_values = self.tree.item(selected[0])['values']
        lemma = item_values[0]

        if self.engine and lemma in self.engine.word_cache:
            current_data = self.engine.word_cache[lemma]
            EditWordModal(self, self.colors, lemma,
                          current_data, self.engine, self.handle_save_word)

    def handle_save_word(self, lemma, new_data):
        if self.engine:
            self.engine.word_cache[lemma] = new_data
            self.engine.save_word_cache()
            self.refresh(self.engine)

            for item in self.tree.get_children():
                val = self.tree.item(item)['values']
                if val[0] == lemma:
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    break
