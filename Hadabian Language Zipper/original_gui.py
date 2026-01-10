#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
from pathlib import Path
from typing import Optional

from original_language_engine import (
    OriginalLanguageEngine,
    OriginalLanguageProfile,
    OriginalLanguageProfileManager
)


class OriginalLanguageGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Idiomas Originais v1.0")
        self.root.geometry("1400x900")
        
        self.profile_manager = OriginalLanguageProfileManager()
        self.current_engine: Optional[OriginalLanguageEngine] = None
        self.current_profile_id: Optional[str] = None
        
        self.setup_ui()
        self.refresh_profile_list()
    
    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tab_translate = ttk.Frame(notebook)
        self.tab_profiles = ttk.Frame(notebook)
        self.tab_vocabulary = ttk.Frame(notebook)
        self.tab_analysis = ttk.Frame(notebook)
        
        notebook.add(self.tab_translate, text="Tradutor")
        notebook.add(self.tab_profiles, text="Gerenciar Perfis")
        notebook.add(self.tab_vocabulary, text="Vocabulário")
        notebook.add(self.tab_analysis, text="Análise")
        
        self.setup_translate_tab()
        self.setup_profiles_tab()
        self.setup_vocabulary_tab()
        self.setup_analysis_tab()
    
    def setup_translate_tab(self):
        main_frame = ttk.Frame(self.tab_translate)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        profile_frame = ttk.LabelFrame(main_frame, text="Seleção de Idioma", padding=10)
        profile_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(profile_frame, text="Perfil:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.translate_profile_var = tk.StringVar()
        self.translate_profile_combo = ttk.Combobox(
            profile_frame, 
            textvariable=self.translate_profile_var,
            state='readonly',
            width=40
        )
        self.translate_profile_combo.grid(row=0, column=1, sticky=tk.W)
        self.translate_profile_combo.bind('<<ComboboxSelected>>', self.on_translate_profile_selected)
        
        ttk.Button(profile_frame, text="Atualizar", command=self.refresh_translate_profiles).grid(
            row=0, column=2, padx=(10, 0)
        )
        
        self.translate_profile_info = tk.Text(
            profile_frame, 
            height=3, 
            width=80,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.translate_profile_info.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        
        input_frame = ttk.LabelFrame(main_frame, text="Texto Original", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=12, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Traduzir", command=self.translate_text, width=15).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Limpar", command=self.clear_translate, width=15).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Carregar Arquivo", command=self.load_input_file, width=15).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Salvar Tradução", command=self.save_translation, width=15).pack(
            side=tk.LEFT, padx=5
        )
        
        output_frame = ttk.LabelFrame(main_frame, text="Texto Traduzido", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=12, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_profiles_tab(self):
        main_frame = ttk.Frame(self.tab_profiles)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_frame, text="Perfis Disponíveis:", font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, pady=(0, 5)
        )
        
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.profile_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.profile_listbox.yview)
        
        self.profile_listbox.bind('<<ListboxSelect>>', self.on_profile_selected)
        
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Novo Perfil", command=self.new_profile).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Duplicar", command=self.duplicate_profile).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Deletar", command=self.delete_profile).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(right_frame, text="Detalhes do Perfil:", font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, pady=(0, 5)
        )
        
        self.profile_details_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        self.profile_details_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_vocabulary_tab(self):
        main_frame = ttk.Frame(self.tab_vocabulary)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Perfil:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.vocab_profile_var = tk.StringVar()
        self.vocab_profile_combo = ttk.Combobox(
            header_frame,
            textvariable=self.vocab_profile_var,
            state='readonly',
            width=40
        )
        self.vocab_profile_combo.pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="Atualizar", command=self.refresh_vocab_profiles).pack(
            side=tk.LEFT, padx=(10, 0)
        )
        
        options_frame = ttk.LabelFrame(main_frame, text="Opções de Geração", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.include_numbers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Incluir números (0-99)",
            variable=self.include_numbers_var
        ).pack(anchor=tk.W)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Gerar Vocabulário Básico",
            command=self.generate_vocabulary,
            width=25
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Exportar JSON",
            command=lambda: self.export_vocabulary('json'),
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Exportar CSV",
            command=lambda: self.export_vocabulary('csv'),
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        vocab_frame = ttk.LabelFrame(main_frame, text="Vocabulário Gerado", padding=10)
        vocab_frame.pack(fill=tk.BOTH, expand=True)
        
        self.vocab_text = scrolledtext.ScrolledText(vocab_frame, wrap=tk.WORD)
        self.vocab_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_analysis_tab(self):
        main_frame = ttk.Frame(self.tab_analysis)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Perfil:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.analysis_profile_var = tk.StringVar()
        self.analysis_profile_combo = ttk.Combobox(
            header_frame,
            textvariable=self.analysis_profile_var,
            state='readonly',
            width=40
        )
        self.analysis_profile_combo.pack(side=tk.LEFT)
        
        ttk.Button(
            header_frame,
            text="Atualizar",
            command=self.refresh_analysis_profiles
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(
            header_frame,
            text="Analisar",
            command=self.analyze_language
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(
            header_frame,
            text="Exportar Estatísticas",
            command=self.export_statistics
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        analysis_frame = ttk.LabelFrame(main_frame, text="Análise Detalhada", padding=10)
        analysis_frame.pack(fill=tk.BOTH, expand=True)
        
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD)
        self.analysis_text.pack(fill=tk.BOTH, expand=True)
    
    def refresh_profile_list(self):
        self.profile_listbox.delete(0, tk.END)
        profiles = self.profile_manager.list_profiles()
        
        for profile_id in sorted(profiles):
            self.profile_listbox.insert(tk.END, profile_id)
    
    def refresh_translate_profiles(self):
        profiles = self.profile_manager.list_profiles()
        self.translate_profile_combo['values'] = sorted(profiles)
        
        if profiles and not self.translate_profile_var.get():
            self.translate_profile_var.set(sorted(profiles)[0])
            self.on_translate_profile_selected(None)
    
    def refresh_vocab_profiles(self):
        profiles = self.profile_manager.list_profiles()
        self.vocab_profile_combo['values'] = sorted(profiles)
    
    def refresh_analysis_profiles(self):
        profiles = self.profile_manager.list_profiles()
        self.analysis_profile_combo['values'] = sorted(profiles)
    
    def on_profile_selected(self, event):
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        
        profile_id = self.profile_listbox.get(selection[0])
        profile = self.profile_manager.load_profile(profile_id)
        
        if profile:
            self.profile_details_text.delete(1.0, tk.END)
            details = json.dumps(profile.to_dict(), indent=2, ensure_ascii=False)
            self.profile_details_text.insert(1.0, details)
            self.current_profile_id = profile_id
    
    def on_translate_profile_selected(self, event):
        profile_id = self.translate_profile_var.get()
        if not profile_id:
            return
        
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            return
        
        self.translate_profile_info.config(state=tk.NORMAL)
        self.translate_profile_info.delete(1.0, tk.END)
        
        info = f"Nome: {profile.name}\n"
        info += f"Seed: {profile.seed} | Complexidade: {profile.complexity}\n"
        
        if profile.phoneme_inventory:
            info += f"Fonologia: {len(profile.phoneme_inventory['vowels'])} vogais, "
            info += f"{len(profile.phoneme_inventory['consonants'])} consoantes"
        
        self.translate_profile_info.insert(1.0, info)
        self.translate_profile_info.config(state=tk.DISABLED)
        
        self.current_engine = OriginalLanguageEngine(profile)
    
    def new_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Novo Perfil de Idioma")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="ID do Perfil:").pack(pady=(20, 5))
        id_entry = ttk.Entry(dialog, width=40)
        id_entry.pack()
        
        ttk.Label(dialog, text="Nome do Idioma:").pack(pady=(10, 5))
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack()
        
        ttk.Label(dialog, text="Seed (opcional):").pack(pady=(10, 5))
        seed_entry = ttk.Entry(dialog, width=40)
        seed_entry.pack()
        
        ttk.Label(dialog, text="Complexidade:").pack(pady=(10, 5))
        complexity_var = tk.StringVar(value='medium')
        complexity_combo = ttk.Combobox(
            dialog,
            textvariable=complexity_var,
            values=['simple', 'medium', 'complex'],
            state='readonly',
            width=37
        )
        complexity_combo.pack()
        
        initialize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            dialog,
            text="Inicializar fonologia imediatamente",
            variable=initialize_var
        ).pack(pady=(20, 10))
        
        def create():
            profile_id = id_entry.get().strip()
            profile_name = name_entry.get().strip()
            seed_text = seed_entry.get().strip()
            
            if not profile_id:
                messagebox.showerror("Erro", "ID do perfil é obrigatório")
                return
            
            if profile_id in self.profile_manager.list_profiles():
                messagebox.showerror("Erro", "Este ID já existe")
                return
            
            seed = None
            if seed_text:
                try:
                    seed = int(seed_text)
                except ValueError:
                    messagebox.showerror("Erro", "Seed deve ser um número inteiro")
                    return
            
            profile = self.profile_manager.create_profile(
                profile_id=profile_id,
                name=profile_name or profile_id,
                seed=seed,
                complexity=complexity_var.get()
            )
            
            if initialize_var.get():
                engine = OriginalLanguageEngine(profile)
                self.profile_manager.save_profile(profile)
                
                msg = f"Perfil '{profile_id}' criado e inicializado!\n\n"
                msg += f"Vogais: {len(profile.phoneme_inventory['vowels'])}\n"
                msg += f"Consoantes: {len(profile.phoneme_inventory['consonants'])}\n"
                msg += f"Ditongos: {len(profile.phoneme_inventory.get('diphthongs', []))}"
                
                messagebox.showinfo("Sucesso", msg)
            else:
                messagebox.showinfo("Sucesso", f"Perfil '{profile_id}' criado!")
            
            self.refresh_profile_list()
            dialog.destroy()
        
        ttk.Button(dialog, text="Criar", command=create).pack(pady=(10, 0))
    
    def delete_profile(self):
        if not self.current_profile_id:
            messagebox.showwarning("Aviso", "Nenhum perfil selecionado")
            return
        
        if messagebox.askyesno("Confirmar", f"Deletar perfil '{self.current_profile_id}'?"):
            self.profile_manager.delete_profile(self.current_profile_id)
            self.refresh_profile_list()
            self.profile_details_text.delete(1.0, tk.END)
            self.current_profile_id = None
            messagebox.showinfo("Sucesso", "Perfil deletado")
    
    def duplicate_profile(self):
        if not self.current_profile_id:
            messagebox.showwarning("Aviso", "Nenhum perfil selecionado")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Duplicar Perfil")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="Novo ID:").pack(pady=(20, 5))
        id_entry = ttk.Entry(dialog, width=40)
        id_entry.pack()
        id_entry.insert(0, f"{self.current_profile_id}_copia")
        
        ttk.Label(dialog, text="Nova Seed (opcional):").pack(pady=(10, 5))
        seed_entry = ttk.Entry(dialog, width=40)
        seed_entry.pack()
        
        def create_duplicate():
            new_id = id_entry.get().strip()
            seed_text = seed_entry.get().strip()
            
            if not new_id:
                messagebox.showerror("Erro", "ID é obrigatório")
                return
            
            if new_id in self.profile_manager.list_profiles():
                messagebox.showerror("Erro", "Este ID já existe")
                return
            
            new_seed = None
            if seed_text:
                try:
                    new_seed = int(seed_text)
                except ValueError:
                    messagebox.showerror("Erro", "Seed deve ser um número inteiro")
                    return
            
            duplicate = self.profile_manager.duplicate_profile(
                source_id=self.current_profile_id,
                new_id=new_id,
                new_seed=new_seed
            )
            
            if duplicate:
                msg = f"Perfil duplicado como '{new_id}'"
                if new_seed:
                    msg += "\n\nNova fonologia será gerada no primeiro uso"
                messagebox.showinfo("Sucesso", msg)
                self.refresh_profile_list()
                dialog.destroy()
            else:
                messagebox.showerror("Erro", "Falha ao duplicar perfil")
        
        ttk.Button(dialog, text="Duplicar", command=create_duplicate).pack(pady=(20, 0))
    
    def translate_text(self):
        if not self.current_engine:
            messagebox.showwarning("Aviso", "Selecione um perfil primeiro")
            return
        
        source_text = self.input_text.get(1.0, tk.END).strip()
        if not source_text:
            messagebox.showwarning("Aviso", "Digite um texto para traduzir")
            return
        
        translated = self.current_engine.translate_text(source_text)
        
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(1.0, translated)
        
        self.current_engine.save_learning_data()
    
    def clear_translate(self):
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)
    
    def load_input_file(self):
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(1.0, content)
    
    def save_translation(self):
        content = self.output_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Aviso", "Nenhuma tradução para salvar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Sucesso", f"Tradução salva em {filename}")
    
    def generate_vocabulary(self):
        profile_id = self.vocab_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Aviso", "Selecione um perfil")
            return
        
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            messagebox.showerror("Erro", "Perfil não encontrado")
            return
        
        engine = OriginalLanguageEngine(profile)
        
        self.vocab_text.delete(1.0, tk.END)
        self.vocab_text.insert(tk.END, "Gerando vocabulário...\n\n")
        self.root.update()
        
        vocabulary = engine.generate_core_vocabulary(
            include_numbers=self.include_numbers_var.get()
        )
        
        self.vocab_text.delete(1.0, tk.END)
        self.vocab_text.insert(tk.END, f"Vocabulário Básico ({len(vocabulary)} palavras)\n")
        self.vocab_text.insert(tk.END, "=" * 60 + "\n\n")
        
        for concept, word in sorted(vocabulary.items()):
            self.vocab_text.insert(tk.END, f"{concept:30} → {word}\n")
        
        engine.save_learning_data()
        
        messagebox.showinfo("Sucesso", f"{len(vocabulary)} palavras geradas!")
    
    def export_vocabulary(self, format_type):
        profile_id = self.vocab_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Aviso", "Selecione um perfil")
            return
        
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            messagebox.showerror("Erro", "Perfil não encontrado")
            return
        
        engine = OriginalLanguageEngine(profile)
        
        ext = 'json' if format_type == 'json' else 'csv'
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(f"Arquivos {ext.upper()}", f"*.{ext}"), ("Todos os arquivos", "*.*")],
            initialfile=f"{profile_id}_vocabulario.{ext}"
        )
        
        if filename:
            count = engine.export_dictionary(filename, format=format_type)
            messagebox.showinfo("Sucesso", f"{count} palavras exportadas para {filename}")
    
    def analyze_language(self):
        profile_id = self.analysis_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Aviso", "Selecione um perfil")
            return
        
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            messagebox.showerror("Erro", "Perfil não encontrado")
            return
        
        engine = OriginalLanguageEngine(profile)
        stats = engine.get_statistics()
        
        self.analysis_text.delete(1.0, tk.END)
        
        self.analysis_text.insert(tk.END, "ANÁLISE DE IDIOMA\n")
        self.analysis_text.insert(tk.END, "=" * 80 + "\n\n")
        
        self.analysis_text.insert(tk.END, "--- PERFIL ---\n")
        self.analysis_text.insert(tk.END, f"ID: {stats['profile']['id']}\n")
        self.analysis_text.insert(tk.END, f"Nome: {stats['profile']['name']}\n")
        self.analysis_text.insert(tk.END, f"Seed: {stats['profile']['seed']}\n\n")
        
        self.analysis_text.insert(tk.END, "--- FONOLOGIA ---\n")
        self.analysis_text.insert(tk.END, f"Vogais: {stats['phonology']['vowel_count']}\n")
        self.analysis_text.insert(tk.END, f"Consoantes: {stats['phonology']['consonant_count']}\n")
        self.analysis_text.insert(tk.END, f"Ditongos: {stats['phonology']['diphthong_count']}\n")
        self.analysis_text.insert(tk.END, f"Templates silábicos: {stats['phonology']['syllable_templates']}\n\n")
        
        self.analysis_text.insert(tk.END, "--- LÉXICO ---\n")
        self.analysis_text.insert(tk.END, f"Total de palavras: {stats['lexicon']['total_words']}\n")
        self.analysis_text.insert(tk.END, f"Palavras únicas: {stats['lexicon']['unique_words']}\n")
        self.analysis_text.insert(tk.END, f"Qualidade média: {stats['lexicon']['average_quality']:.2f}\n")
        self.analysis_text.insert(tk.END, f"Comprimento médio: {stats['lexicon']['average_word_length']:.1f}\n\n")
        
        if stats['lexicon']['most_common_phonemes']:
            self.analysis_text.insert(tk.END, "Fonemas mais comuns:\n")
            for phoneme, count in stats['lexicon']['most_common_phonemes'][:10]:
                self.analysis_text.insert(tk.END, f"  {phoneme}: {count}\n")
            self.analysis_text.insert(tk.END, "\n")
        
        self.analysis_text.insert(tk.END, "--- DISTRIBUIÇÃO ---\n")
        self.analysis_text.insert(tk.END, f"Entropia: {stats['distribution']['entropy']:.2f}\n")
        self.analysis_text.insert(tk.END, f"Uniformidade: {stats['distribution']['uniformity']:.2f}\n\n")
        
        if stats.get('recommendations'):
            self.analysis_text.insert(tk.END, "--- RECOMENDAÇÕES ---\n")
            for rec in stats['recommendations']:
                self.analysis_text.insert(tk.END, f"• {rec}\n")
    
    def export_statistics(self):
        profile_id = self.analysis_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Aviso", "Selecione um perfil")
            return
        
        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            messagebox.showerror("Erro", "Perfil não encontrado")
            return
        
        engine = OriginalLanguageEngine(profile)
        stats = engine.get_statistics()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")],
            initialfile=f"{profile_id}_estatisticas.json"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Sucesso", f"Estatísticas exportadas para {filename}")


def main():
    root = tk.Tk()
    app = OriginalLanguageGeneratorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
