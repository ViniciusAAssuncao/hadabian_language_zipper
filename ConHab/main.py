import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
from pathlib import Path
from engine import OriginalLanguageEngine

class ConHabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ConHab")
        self.root.geometry("800x600")
        
        self.engine = None
        self.setup_ui()
        self.load_conlangs()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        selection_frame = ttk.LabelFrame(main_frame, text="Configuração de Linguagem", padding="10")
        selection_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(selection_frame, text="Selecione a CL (Conlang):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.cl_selector = ttk.Combobox(selection_frame, state="readonly", width=30)
        self.cl_selector.pack(side=tk.LEFT, padx=(0, 10))
        self.cl_selector.bind("<<ComboboxSelected>>", self.on_profile_selected)
        
        ttk.Button(selection_frame, text="Atualizar", command=self.load_conlangs).pack(side=tk.LEFT)

        input_frame = ttk.LabelFrame(main_frame, text="Entrada: Linguagem Natural (LN)", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.ln_input = scrolledtext.ScrolledText(input_frame, height=8, wrap=tk.WORD)
        self.ln_input.pack(fill=tk.BOTH, expand=True)

        self.btn_process = ttk.Button(main_frame, text="CONVERTER PARA CL", command=self.process_language)
        self.btn_process.pack(pady=10)

        output_frame = ttk.LabelFrame(main_frame, text="Saída: Conlang (CL)", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.cl_output = scrolledtext.ScrolledText(output_frame, height=8, wrap=tk.WORD)
        self.cl_output.pack(fill=tk.BOTH, expand=True)

    def load_conlangs(self):
        path = Path("./conlangs")
        if not path.exists():
            os.makedirs(path)
        
        files = [f.name for f in path.glob("*.json")]
        self.cl_selector['values'] = files
        if files:
            self.cl_selector.current(0)
            self.on_profile_selected(None)

    def on_profile_selected(self, event):
        selection = self.cl_selector.get()
        if selection:
            try:
                profile_path = Path("./conlangs") / selection
                self.engine = OriginalLanguageEngine(profile_path)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar perfil: {str(e)}")

    def process_language(self):
        if not self.engine:
            messagebox.showwarning("Aviso", "Selecione um perfil de linguagem primeiro.")
            return

        text = self.ln_input.get("1.0", tk.END).strip()
        if not text:
            return

        try:
            result = self.engine.process_text(text)
            self.cl_output.delete("1.0", tk.END)
            self.cl_output.insert("1.0", result)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no processamento: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConHabApp(root)
    root.mainloop()