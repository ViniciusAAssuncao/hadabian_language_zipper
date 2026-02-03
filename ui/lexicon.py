import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import math
import threading
from ui.edit_modal import EditWordModal, EditSynsetModal
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
        self.detail_vars = {}
        self.synset_tree = None
        self.current_detail_lemma = None
        self.current_detail_item_id = None
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

        self.main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(list_frame, weight=3)

        columns = ("lemma", "word", "pos", "origin", "tags")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", style="Treeview"
        )

        self.tree.heading("lemma", text="Lema (Origem)")
        self.tree.heading("word", text="Palavra Padrão")
        self.tree.heading("pos", text="POS")
        self.tree.heading("origin", text="Origem")
        self.tree.heading("tags", text="Tags (Geral)")

        self.tree.column("lemma", width=120)
        self.tree.column("word", width=120)
        self.tree.column("pos", width=60)
        self.tree.column("origin", width=80)
        self.tree.column("tags", width=150)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        self.details_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.details_frame, weight=2)
        self.setup_details_panel()

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

    def setup_details_panel(self):
        header_lbl = ttk.Label(
            self.details_frame,
            text="DETALHES DA ENTRADA",
            style="SubHeader.TLabel",
            anchor="center"
        )
        header_lbl.pack(fill=tk.X, pady=(0, 10))

        content_frame = ttk.Frame(self.details_frame, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)

        def create_field(parent, label_text):
            f = ttk.Frame(parent)
            f.pack(fill=tk.X, pady=2)
            lbl = ttk.Label(f, text=label_text, width=15, font=(
                "Segoe UI", 9, "bold"), foreground=self.colors["fg_secondary"])
            lbl.pack(side=tk.LEFT)
            val = tk.StringVar()
            entry = ttk.Entry(f, textvariable=val,
                              state="readonly", font=("Consolas", 10), foreground=self.colors["text"])
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            return val

        self.detail_vars['lemma'] = create_field(content_frame, "Lema:")
        self.detail_vars['default'] = create_field(content_frame, "Padrão:")
        self.detail_vars['origin'] = create_field(content_frame, "Origem:")
        self.detail_vars['root'] = create_field(content_frame, "Raiz:")
        self.detail_vars['desc'] = create_field(content_frame, "Descrição:")

        ttk.Separator(content_frame, orient='horizontal').pack(
            fill='x', pady=15)

        ttk.Label(content_frame, text="Variações / Synsets", font=("Segoe UI", 9, "bold"),
                  foreground=self.colors["fg_secondary"]).pack(anchor="w", pady=(0, 5))

        synset_cols = ("word", "affinity", "tags")
        self.synset_tree = ttk.Treeview(
            content_frame,
            columns=synset_cols,
            show="headings",
            height=8,
            style="Treeview"
        )

        self.synset_tree.heading("word", text="Palavra")
        self.synset_tree.heading("affinity", text="Afinidade")
        self.synset_tree.heading("tags", text="Tags")

        self.synset_tree.column("word", width=120)
        self.synset_tree.column("affinity", width=60, anchor="center")
        self.synset_tree.column("tags", width=150)

        self.synset_tree.pack(fill=tk.BOTH, expand=True)
        self.synset_tree.bind("<<TreeviewSelect>>", self.on_synset_select)

        btn_toolbar = ttk.Frame(content_frame)
        btn_toolbar.pack(fill=tk.X, pady=(5, 0))

        self.btn_add_synset = ttk.Button(
            btn_toolbar, text="+ Var", style="Secondary.TButton",
            command=self.on_add_synset, state="disabled"
        )
        self.btn_add_synset.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_edit_synset = ttk.Button(
            btn_toolbar, text="✎ Var", style="Secondary.TButton",
            command=self.on_edit_synset, state="disabled"
        )
        self.btn_edit_synset.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_del_synset = ttk.Button(
            btn_toolbar, text="🗑 Var", style="Secondary.TButton",
            command=self.on_delete_synset, state="disabled"
        )
        self.btn_del_synset.pack(side=tk.LEFT)

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
                        tags = ", ".join(sorted(list(set(all_tags))))
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

        self.clear_details()
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

    def clear_details(self):
        self.current_detail_lemma = None
        self.current_detail_item_id = None
        for key in self.detail_vars:
            self.detail_vars[key].set("")
        for item in self.synset_tree.get_children():
            self.synset_tree.delete(item)
        self.btn_add_synset.state(["disabled"])
        self.btn_edit_synset.state(["disabled"])
        self.btn_del_synset.state(["disabled"])

    def on_selection_change(self, event):
        selected = self.tree.selection()
        if selected:
            self.btn_delete.state(["!disabled"])
            if len(selected) == 1:
                self.btn_edit.state(["!disabled"])
                self.btn_mass_edit.state(["disabled"])
                self.populate_details(selected[0])
            else:
                self.btn_edit.state(["disabled"])
                self.btn_mass_edit.state(["!disabled"])
                self.clear_details()
        else:
            self.btn_edit.state(["disabled"])
            self.btn_mass_edit.state(["disabled"])
            self.btn_delete.state(["disabled"])
            self.clear_details()

    def populate_details(self, item_id):
        self.clear_details()
        self.current_detail_item_id = item_id
        item_values = self.tree.item(item_id)['values']
        lemma = item_values[0]
        self.current_detail_lemma = lemma

        if not self.engine or lemma not in self.engine.word_cache:
            return

        data = self.engine.word_cache[lemma]

        self.detail_vars['lemma'].set(lemma)
        self.btn_add_synset.state(["!disabled"])

        if isinstance(data, dict):
            self.detail_vars['default'].set(data.get('default', ''))
            self.detail_vars['origin'].set(data.get('origin', ''))
            self.detail_vars['root'].set(data.get('root', '-'))
            self.detail_vars['desc'].set(data.get('description', ''))

            if 'synsets' in data:
                for s in data['synsets']:
                    w = s.get('word', '')
                    aff = str(s.get('affinity', '1.0'))
                    tags = ", ".join(s.get('tags', []))
                    self.synset_tree.insert("", tk.END, values=(w, aff, tags))
        else:
            self.detail_vars['default'].set(str(data))
            self.detail_vars['origin'].set("legacy")

    def on_synset_select(self, event):
        selected = self.synset_tree.selection()
        if selected:
            self.btn_edit_synset.state(["!disabled"])
            self.btn_del_synset.state(["!disabled"])
        else:
            self.btn_edit_synset.state(["disabled"])
            self.btn_del_synset.state(["disabled"])

    def on_add_synset(self):
        if not self.current_detail_lemma:
            return

        initial_data = {
            "word": "",
            "affinity": 1.0,
            "tags": [],
            "pos": self.detail_vars['pos'].get() if 'pos' in self.detail_vars else ""
        }

        EditSynsetModal(
            self, self.colors, self.current_detail_lemma, initial_data, self.engine,
            lambda data: self.handle_synset_save(data, -1)
        )

    def on_edit_synset(self):
        selected = self.synset_tree.selection()
        if not selected or not self.current_detail_lemma:
            return

        index = self.synset_tree.index(selected[0])
        data = self.engine.word_cache[self.current_detail_lemma]
        if "synsets" not in data or index >= len(data["synsets"]):
            return

        synset_data = data["synsets"][index]
        EditSynsetModal(
            self, self.colors, self.current_detail_lemma, synset_data, self.engine,
            lambda new_data: self.handle_synset_save(new_data, index)
        )

    def on_delete_synset(self):
        selected = self.synset_tree.selection()
        if not selected or not self.current_detail_lemma:
            return

        if not messagebox.askyesno("Confirmar", "Excluir esta variação?"):
            return

        index = self.synset_tree.index(selected[0])
        data = self.engine.word_cache[self.current_detail_lemma]

        if "synsets" in data:
            del data["synsets"][index]
            self.engine.save_word_cache()
            self.populate_details(self.current_detail_item_id)
            self.refresh(self.engine)

    def handle_synset_save(self, new_data, index):
        if not self.current_detail_lemma or self.current_detail_lemma not in self.engine.word_cache:
            return

        entry = self.engine.word_cache[self.current_detail_lemma]
        if "synsets" not in entry:
            entry["synsets"] = []

        if index == -1:
            entry["synsets"].append(new_data)
        else:
            if index < len(entry["synsets"]):
                entry["synsets"][index] = new_data

        self.engine.save_word_cache()
        self.populate_details(self.current_detail_item_id)
        self.refresh(self.engine)

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
