import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path


class GramatakiTab(ttk.Frame):
    def __init__(self, parent, colors, engine=None):
        super().__init__(parent)
        self.colors = colors
        self.engine = engine
        self.culture_data = {}
        self.setup_ui()
        self.load_cultures()

    def update_engine(self, new_engine):
        self.engine = new_engine

    def setup_ui(self):
        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(
            self.main_container, text="Forja Onomástica", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(control_frame, text="Perfil Cultural:", foreground=self.colors["fg_secondary"]).grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.culture_var = tk.StringVar()
        self.culture_cb = ttk.Combobox(
            control_frame, textvariable=self.culture_var, state="readonly")
        self.culture_cb.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        self.culture_cb.bind("<<ComboboxSelected>>", self.on_culture_select)

        ttk.Label(control_frame, text="Fórmula:", foreground=self.colors["fg_secondary"]).grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.formula_var = tk.StringVar()
        self.formula_cb = ttk.Combobox(
            control_frame, textvariable=self.formula_var, state="readonly")
        self.formula_cb.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)

        ttk.Label(control_frame, text="Gênero:", foreground=self.colors["fg_secondary"]).grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.gender_var = tk.StringVar(value="Masculino")
        self.gender_cb = ttk.Combobox(control_frame, textvariable=self.gender_var, values=[
                                      "Masculino", "Feminino", "Neutro"], state="readonly")
        self.gender_cb.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=5)

        control_frame.columnconfigure(1, weight=1)

        self.btn_generate = ttk.Button(
            control_frame, text="Gerar Nome Nativo", style="Accent.TButton", command=self.generate_name)
        self.btn_generate.grid(row=3, column=0, columnspan=2, pady=15)

        output_frame = ttk.LabelFrame(
            self.main_container, text="Registro", padding=15)
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.lbl_name = ttk.Label(output_frame, text="", font=(
            "Segoe UI", 26, "bold"), foreground=self.colors["accent"], anchor="center")
        self.lbl_name.pack(fill=tk.X, pady=15)

        ttk.Label(output_frame, text="Glossário Etimológico:", font=(
            "Segoe UI", 11, "bold"), foreground=self.colors["fg_primary"]).pack(anchor="w", pady=(10, 5))

        self.text_etymology = tk.Text(output_frame, height=12, bg=self.colors["input_bg"], fg=self.colors["fg_primary"], font=(
            "Consolas", 11), borderwidth=0, relief="flat", padx=10, pady=10)
        self.text_etymology.pack(fill=tk.BOTH, expand=True)
        self.text_etymology.configure(state="disabled")

    def load_cultures(self):
        path = Path("./cultures")
        path.mkdir(exist_ok=True)
        files = list(path.glob("*.json"))
        self.culture_data.clear()
        cb_values = []
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    cid = data.get("culture_id", f.stem)
                    self.culture_data[cid] = data
                    cb_values.append(cid)
            except:
                pass
        self.culture_cb['values'] = cb_values
        if cb_values:
            self.culture_cb.current(0)
            self.on_culture_select()

    def on_culture_select(self, event=None):
        cid = self.culture_var.get()
        data = self.culture_data.get(cid, {})
        formulas = list(data.get("formulas", {}).keys())
        self.formula_cb['values'] = formulas
        if formulas:
            self.formula_cb.current(0)

    def generate_name(self):
        if not self.engine:
            messagebox.showwarning(
                "Aviso", "Motor linguístico principal não carregado.")
            return

        cid = self.culture_var.get()
        data = self.culture_data.get(cid)
        if not data:
            return

        formula = self.formula_var.get()
        gender = self.gender_var.get()

        result = self.engine.gramataki_manager.generate_onomastic_name(
            data, formula, gender)

        self.lbl_name.config(text=result['name'])

        self.text_etymology.configure(state="normal")
        self.text_etymology.delete("1.0", tk.END)

        for etym in result['etymology']:
            line = f"{etym['component']}: \"{etym['meaning']}\" ({etym['type']})\n"
            self.text_etymology.insert(tk.END, line)

        self.text_etymology.configure(state="disabled")
