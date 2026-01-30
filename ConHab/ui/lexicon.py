import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import math
import threading
from ui.edit_modal import EditWordModal
from ui.create_word_modal import CreateWordModal
from ui.mass_edit_modal import MassEditModal


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

        self.btn_create = ttk.Button(
            search_container,
            text="+ Nova",
            style="Secondary.TButton",
            command=self.on_create_click
        )
        self.btn_create.pack(side=tk.LEFT, padx=(10, 0))

        self.btn_edit = ttk.Button(
            search_container,
            text="✎ Editar",
            style="Secondary.TButton",
            command=self.on_edit_click,
            state="disabled"
        )
        self.btn_edit.pack(side=tk.LEFT, padx=(5, 0))

        self.btn_mass_edit = ttk.Button(
            search_container,
            text="✎ Massa",
            style="Secondary.TButton",
            command=self.on_mass_edit_click,
            state="disabled"
        )
        self.btn_mass_edit.pack(side=tk.LEFT, padx=(5, 0))

        self.btn_delete = ttk.Button(
            search_container,
            text="🗑 Excluir",
            style="Secondary.TButton",
            command=self.on_delete_click,
            state="disabled"
        )
        self.btn_delete.pack(side=tk.LEFT, padx=(5, 0))

        main_content = ttk.Frame(self)
        main_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        columns = ("lemma", "word", "pos", "origin", "tags")
        self.tree = ttk.Treeview(
            main_content, columns=columns, show="headings", style="Treeview"
        )

        self.tree.heading("lemma", text="Lema (Origem)")
        self.tree.heading("word", text="Palavra (Conlang)")
        self.tree.heading("pos", text="POS")
        self.tree.heading("origin", text="Origem")
        self.tree.heading("tags", text="Tags")

        self.tree.column("lemma", width=150)
        self.tree.column("word", width=150)
        self.tree.column("pos", width=80)
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

        self.loading_overlay = tk.Label(
            self,
            text="Processando...",
            font=("Segoe UI", 14, "bold"),
            bg="#222222",
            fg="white"
        )
        self.loading_bg = tk.Frame(self, bg="black")

    def toggle_loading(self, show=True, text="Processando..."):
        if show:
            self.loading_bg.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.loading_bg.lift()
            self.loading_bg.configure(bg="#222222")
            self.loading_overlay.config(text=text, bg="#222222")
            self.loading_overlay.place(relx=0.5, rely=0.5, anchor="center")
            self.loading_overlay.lift()
            self.update_idletasks()
        else:
            self.loading_overlay.place_forget()
            self.loading_bg.place_forget()

    def refresh(self, engine):
        self.engine = engine
        self.toggle_loading(True, "Carregando Léxico...")
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        new_items = []
        if self.engine and self.engine.word_cache:
            for lemma, entry in self.engine.word_cache.items():
                if isinstance(entry, dict):
                    word = entry.get("default", "")
                    origin = entry.get("origin", "")
                    pos = entry.get("pos", "")
                    tags = ""
                    if "synsets" in entry:
                        all_tags = []
                        for s in entry["synsets"]:
                            all_tags.extend(s.get("tags", []))
                        tags = ", ".join(set(all_tags))
                else:
                    word = str(entry)
                    origin = "legacy/unknown"
                    pos = ""
                    tags = ""

                new_items.append((lemma, word, pos, origin, tags))

            new_items.sort(key=lambda x: x[0].lower())

        self.after(0, lambda: self._finish_refresh(new_items))

    def _finish_refresh(self, items):
        self.all_items = items
        self.on_search()
        self.toggle_loading(False)

    def on_search(self, event=None):
        query = self.search_var.get().strip().lower()

        if not query:
            self.filtered_items = list(self.all_items)
        else:
            self.filtered_items = [
                item for item in self.all_items
                if query in item[0].lower() or
                query in item[1].lower() or
                query in item[4].lower()
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
        self.btn_mass_edit.state(["disabled"])
        self.btn_delete.state(["disabled"])

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
            self.btn_delete.state(["!disabled"])
            if len(selected) == 1:
                self.btn_edit.state(["!disabled"])
                self.btn_mass_edit.state(["disabled"])
            else:
                self.btn_edit.state(["disabled"])
                self.btn_mass_edit.state(["!disabled"])
        else:
            self.btn_edit.state(["disabled"])
            self.btn_mass_edit.state(["disabled"])
            self.btn_delete.state(["disabled"])

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.open_edit_modal()

    def on_edit_click(self):
        self.open_edit_modal()

    def on_create_click(self):
        if self.engine:
            CreateWordModal(self, self.colors, self.engine,
                            self.handle_save_word)

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

    def on_delete_click(self):
        selected = self.tree.selection()
        if not selected:
            return

        count = len(selected)
        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir {count} palavra(s)?\nEssa ação não pode ser desfeita."
        )
        if not confirm:
            return

        lemmas_to_delete = []
        for item_id in selected:
            val = self.tree.item(item_id)['values']
            lemmas_to_delete.append(val[0])

        self.toggle_loading(True, "Excluindo...")
        threading.Thread(
            target=self._delete_worker,
            args=(lemmas_to_delete,),
            daemon=True
        ).start()

    def _delete_worker(self, lemmas):
        if not self.engine:
            return

        for lemma in lemmas:
            if lemma in self.engine.word_cache:
                del self.engine.word_cache[lemma]

        self.engine.save_word_cache()
        self.after(0, lambda: self.refresh(self.engine))

    def on_mass_edit_click(self):
        selected = self.tree.selection()
        if not selected:
            return

        lemmas_selected = []
        for item_id in selected:
            val = self.tree.item(item_id)['values']
            lemmas_selected.append(val[0])

        MassEditModal(
            self,
            self.colors,
            len(lemmas_selected),
            lambda updates: self.execute_mass_update(lemmas_selected, updates)
        )

    def execute_mass_update(self, lemmas, updates):
        self.toggle_loading(True, "Aplicando alterações...")
        threading.Thread(
            target=self._mass_update_worker,
            args=(lemmas, updates),
            daemon=True
        ).start()

    def _mass_update_worker(self, lemmas, updates):
        if not self.engine:
            return

        for lemma in lemmas:
            if lemma not in self.engine.word_cache:
                continue

            entry = self.engine.word_cache[lemma]

            if "default" in updates:
                entry["default"] = updates["default"]
                if "synsets" in entry:
                    for s in entry["synsets"]:
                        s["word"] = updates["default"]

            if "origin" in updates:
                entry["origin"] = updates["origin"]
                if "synsets" in entry:
                    for s in entry["synsets"]:
                        if "tags" not in s:
                            s["tags"] = []
                        s["tags"].append(updates["origin"])

            if "pos" in updates:
                entry["pos"] = updates["pos"]
                if "synsets" in entry:
                    for s in entry["synsets"]:
                        s["pos"] = updates["pos"]

            if "tags" in updates:
                if "synsets" in entry:
                    for s in entry["synsets"]:
                        s["tags"] = list(updates["tags"])
                        if "origin" in entry:
                            s["tags"].append(entry["origin"])

        self.engine.save_word_cache()
        self.after(0, lambda: self.refresh(self.engine))

    def handle_save_word(self, lemma, new_data):
        if self.engine:
            self.engine.word_cache[lemma] = new_data
            self.engine.save_word_cache()
            self.refresh(self.engine)
