import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from glyph_generator import GlyphGenerator
from glyph_exporter import GlyphExporter
import string

class ConscriadabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conscriadab")
        self.root.geometry("1000x700")
        
        self.current_glyphs = {}
        self.current_preview_char = None
        self.exporter = GlyphExporter()
        
        self._create_widgets()
    
    def _create_widgets(self):
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(3, weight=1)
        
        control_frame = ttk.LabelFrame(main_container, text="Configurações", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Seed:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.seed_var = tk.StringVar(value="12345")
        seed_entry = ttk.Entry(control_frame, textvariable=self.seed_var, width=20)
        seed_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(control_frame, text="Estilo:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.style_var = tk.StringVar(value="geometric")
        style_combo = ttk.Combobox(control_frame, textvariable=self.style_var, 
                                   values=["geometric", "curvilinear", "angular", "mixed"],
                                   state="readonly", width=15)
        style_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(control_frame, text="Caracteres:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.chars_var = tk.StringVar(value="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        chars_entry = ttk.Entry(control_frame, textvariable=self.chars_var, width=50)
        chars_entry.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(control_frame, text="Complexidade:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.complexity_var = tk.IntVar(value=5)
        complexity_scale = ttk.Scale(control_frame, from_=2, to=10, variable=self.complexity_var, 
                                     orient=tk.HORIZONTAL, length=200)
        complexity_scale.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        self.complexity_label = ttk.Label(control_frame, text="5")
        self.complexity_label.grid(row=2, column=2, sticky=tk.W, padx=(5, 0), pady=(10, 0))
        complexity_scale.config(command=self._update_complexity_label)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(15, 0))
        
        self.generate_btn = ttk.Button(button_frame, text="Gerar Alfabeto", command=self._generate_alphabet)
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(button_frame, text="Exportar Tudo (PNG)", 
                                     command=self._export_all, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_single_btn = ttk.Button(button_frame, text="Exportar Atual", 
                                            command=self._export_current, state=tk.DISABLED)
        self.export_single_btn.pack(side=tk.LEFT, padx=5)
        
        preview_frame = ttk.LabelFrame(main_container, text="Preview", padding="10")
        preview_frame.grid(row=1, column=0, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(preview_frame, width=512, height=512, bg="white")
        self.canvas.grid(row=0, column=0)
        
        self.preview_label = ttk.Label(preview_frame, text="Nenhum glifo selecionado", 
                                       font=('Arial', 12, 'bold'))
        self.preview_label.grid(row=1, column=0, pady=(10, 0))
        
        gallery_frame = ttk.LabelFrame(main_container, text="Galeria de Glifos", padding="10")
        gallery_frame.grid(row=1, column=1, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        gallery_frame.columnconfigure(0, weight=1)
        gallery_frame.rowconfigure(0, weight=1)
        
        gallery_scroll = ttk.Scrollbar(gallery_frame, orient=tk.VERTICAL)
        gallery_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.gallery_canvas = tk.Canvas(gallery_frame, yscrollcommand=gallery_scroll.set, bg="white")
        self.gallery_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        gallery_scroll.config(command=self.gallery_canvas.yview)
        
        self.gallery_frame_interior = ttk.Frame(self.gallery_canvas)
        self.gallery_canvas.create_window((0, 0), window=self.gallery_frame_interior, anchor=tk.NW)
        
        self.gallery_frame_interior.bind('<Configure>', 
                                         lambda e: self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all")))
        
        status_frame = ttk.Frame(main_container)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Pronto para gerar glifos", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X)
    
    def _update_complexity_label(self, value):
        self.complexity_label.config(text=str(int(float(value))))
    
    def _generate_alphabet(self):
        try:
            seed = self.seed_var.get()
            style = self.style_var.get()
            chars = self.chars_var.get()
            complexity = self.complexity_var.get()
            
            if not seed or not chars:
                messagebox.showwarning("Aviso", "Preencha a seed e os caracteres")
                return
            
            self.status_label.config(text=f"Gerando {len(chars)} glifos...")
            self.root.update()
            
            generator = GlyphGenerator(seed=seed, style=style)
            
            complexity_map = {char: complexity for char in chars}
            self.current_glyphs = generator.generate_alphabet(chars, complexity_map)
            
            self._update_gallery()
            
            self.export_btn.config(state=tk.NORMAL)
            self.status_label.config(text=f"✓ {len(chars)} glifos gerados com sucesso (seed: {seed})")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar glifos: {str(e)}")
            self.status_label.config(text="Erro na geração")
    
    def _update_gallery(self):
        for widget in self.gallery_frame_interior.winfo_children():
            widget.destroy()
        
        thumb_size = 80
        cols = 6
        
        for idx, (char, img) in enumerate(self.current_glyphs.items()):
            row = idx // cols
            col = idx % cols
            
            thumb = img.copy()
            thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(thumb)
            
            frame = ttk.Frame(self.gallery_frame_interior, relief=tk.RAISED, borderwidth=1)
            frame.grid(row=row, column=col, padx=5, pady=5)
            
            btn = tk.Button(frame, image=photo, command=lambda c=char: self._show_preview(c))
            btn.image = photo
            btn.pack()
            
            label = ttk.Label(frame, text=char, font=('Arial', 10, 'bold'))
            label.pack()
    
    def _show_preview(self, char):
        if char not in self.current_glyphs:
            return
        
        self.current_preview_char = char
        img = self.current_glyphs[char]
        
        self.canvas.delete("all")
        
        display_size = 512
        photo = ImageTk.PhotoImage(img)
        self.canvas.image = photo
        self.canvas.create_image(256, 256, image=photo)
        
        self.preview_label.config(text=f"Glifo: {char}")
        self.export_single_btn.config(state=tk.NORMAL)
    
    def _export_current(self):
        if not self.current_preview_char or self.current_preview_char not in self.current_glyphs:
            messagebox.showwarning("Aviso", "Nenhum glifo selecionado para exportar")
            return
        
        try:
            seed = self.seed_var.get()
            char = self.current_preview_char
            img = self.current_glyphs[char]
            
            filepath = self.exporter.export_glyph(img, char, seed)
            messagebox.showinfo("Sucesso", f"Glifo exportado:\n{filepath}")
            self.status_label.config(text=f"✓ Glifo '{char}' exportado")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
    
    def _export_all(self):
        if not self.current_glyphs:
            messagebox.showwarning("Aviso", "Nenhum glifo para exportar")
            return
        
        try:
            seed = self.seed_var.get()
            self.status_label.config(text="Exportando todos os glifos...")
            self.root.update()
            
            exported = self.exporter.export_alphabet(self.current_glyphs, seed)
            
            messagebox.showinfo("Sucesso", 
                              f"{len(exported)} glifos exportados para:\n{self.exporter.get_output_dir()}")
            self.status_label.config(text=f"✓ {len(exported)} glifos exportados com sucesso")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
            self.status_label.config(text="Erro na exportação")

def main():
    root = tk.Tk()
    app = ConscriadabApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
