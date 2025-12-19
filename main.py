import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
from pathlib import Path
from zipper_engine import ZipperEngine
from language_profile_manager import LanguageProfileManager, ProfileValidator


class LanguageZipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hadabian Language Zipper v1.0")
        self.root.geometry("1200x800")
        
        self.profile_manager = LanguageProfileManager()
        
        self.current_profile_id = None
        self.base_texts = []
        
        self.setup_ui()
        self.refresh_profile_list()
    
    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tab_generator = ttk.Frame(notebook)
        self.tab_profiles = ttk.Frame(notebook)
        self.tab_editor = ttk.Frame(notebook)
        self.tab_batch = ttk.Frame(notebook)
        
        notebook.add(self.tab_generator, text="Generator")
        notebook.add(self.tab_profiles, text="Profile Manager")
        notebook.add(self.tab_editor, text="Profile Editor")
        notebook.add(self.tab_batch, text="Batch Processing")
        
        self.setup_generator_tab()
        self.setup_profiles_tab()
        self.setup_editor_tab()
        self.setup_batch_tab()
    
    def setup_generator_tab(self):
        main_frame = ttk.Frame(self.tab_generator)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        profile_frame = ttk.LabelFrame(main_frame, text="Language Profile Selection", padding=10)
        profile_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(profile_frame, text="Select Profile:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.gen_profile_var = tk.StringVar()
        self.gen_profile_combo = ttk.Combobox(profile_frame, textvariable=self.gen_profile_var, state='readonly', width=40)
        self.gen_profile_combo.grid(row=0, column=1, sticky=tk.W)
        self.gen_profile_combo.bind('<<ComboboxSelected>>', self.on_generator_profile_selected)
        
        ttk.Button(profile_frame, text="Refresh Profiles", command=self.refresh_generator_profiles).grid(row=0, column=2, padx=(10, 0))
        
        self.gen_profile_info = tk.Text(profile_frame, height=4, width=80, wrap=tk.WORD, state=tk.DISABLED)
        self.gen_profile_info.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)
        
        input_frame = ttk.LabelFrame(main_frame, text="Base Texts Input", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.input_text_frames = []
        self.input_text_widgets = []
        
        for i in range(4):
            frame = ttk.Frame(input_frame)
            frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            label = ttk.Label(frame, text=f"Base Language {i+1}:")
            label.pack(anchor=tk.W)
            
            text_widget = scrolledtext.ScrolledText(frame, height=6, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            self.input_text_frames.append(frame)
            self.input_text_widgets.append(text_widget)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Generate", command=self.generate_language, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_generator, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Output", command=self.save_output, width=15).pack(side=tk.LEFT, padx=5)
        
        output_frame = ttk.LabelFrame(main_frame, text="Generated Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_profiles_tab(self):
        main_frame = ttk.Frame(self.tab_profiles)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_frame, text="Available Profiles:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
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
        
        ttk.Button(button_frame, text="New Profile", command=self.new_profile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Profile", command=self.delete_profile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Duplicate", command=self.duplicate_profile).pack(side=tk.LEFT, padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(right_frame, text="Profile Details:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        self.profile_details_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        self.profile_details_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_editor_tab(self):
        main_frame = ttk.Frame(self.tab_editor)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Edit Profile:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.edit_profile_var = tk.StringVar()
        self.edit_profile_combo = ttk.Combobox(header_frame, textvariable=self.edit_profile_var, state='readonly', width=40)
        self.edit_profile_combo.pack(side=tk.LEFT)
        self.edit_profile_combo.bind('<<ComboboxSelected>>', self.load_profile_to_editor)
        
        ttk.Button(header_frame, text="Refresh", command=self.refresh_editor_profiles).pack(side=tk.LEFT, padx=(10, 0))
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        basic_frame = ttk.Frame(notebook, padding=10)
        fusion_frame = ttk.Frame(notebook, padding=10)
        phono_frame = ttk.Frame(notebook, padding=10)
        ortho_frame = ttk.Frame(notebook, padding=10)
        
        notebook.add(basic_frame, text="Basic Info")
        notebook.add(fusion_frame, text="Fusion Rules")
        notebook.add(phono_frame, text="Phonotactics")
        notebook.add(ortho_frame, text="Orthography")
        
        self.setup_basic_editor(basic_frame)
        self.setup_fusion_editor(fusion_frame)
        self.setup_phono_editor(phono_frame)
        self.setup_ortho_editor(ortho_frame)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save Changes", command=self.save_profile_changes, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset", command=self.reset_editor, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Validate", command=self.validate_current_profile, width=15).pack(side=tk.LEFT, padx=5)
    
    def setup_basic_editor(self, parent):
        row = 0
        
        ttk.Label(parent, text="Profile ID:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_id = ttk.Entry(parent, width=40)
        self.edit_id.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_name = ttk.Entry(parent, width=40)
        self.edit_name.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Description:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_description = scrolledtext.ScrolledText(parent, height=4, width=40)
        self.edit_description.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Base Languages (comma-separated):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_bases = ttk.Entry(parent, width=40)
        self.edit_bases.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Fusion Weights (comma-separated):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_weights = ttk.Entry(parent, width=40)
        self.edit_weights.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Global Seed:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_seed = ttk.Entry(parent, width=40)
        self.edit_seed.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Semantic General:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_semantic = ttk.Combobox(parent, values=["neutral", "formal", "informal", "archaic", "technical"], width=37, state='readonly')
        self.edit_semantic.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_semantic.set("neutral")
    
    def setup_fusion_editor(self, parent):
        row = 0
        
        ttk.Label(parent, text="Minimum Cut Point (0.0-1.0):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_min_cut = ttk.Entry(parent, width=20)
        self.edit_min_cut.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_min_cut.insert(0, "0.4")
        row += 1
        
        self.edit_preserve_caps = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Preserve Capitalization", variable=self.edit_preserve_caps).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        self.edit_preserve_accents = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Preserve Accents", variable=self.edit_preserve_accents).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Contraction Handling:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_contractions = ttk.Combobox(parent, values=["separate", "maintain", "expand"], width=37, state='readonly')
        self.edit_contractions.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_contractions.set("separate")
    
    def setup_phono_editor(self, parent):
        row = 0
        
        ttk.Label(parent, text="Vowels:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_vowels = ttk.Entry(parent, width=60)
        self.edit_vowels.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_vowels.insert(0, "aeiouàâäèéêëìíîïòóôöùúûü")
        row += 1
        
        ttk.Label(parent, text="Forbidden Final Consonants (comma-separated):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_forbidden = ttk.Entry(parent, width=60)
        self.edit_forbidden.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(parent, text="Max Consonant Cluster:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_max_cons = ttk.Entry(parent, width=20)
        self.edit_max_cons.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_max_cons.insert(0, "3")
        row += 1
        
        ttk.Label(parent, text="Max Vowel Cluster:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_max_vowel = ttk.Entry(parent, width=20)
        self.edit_max_vowel.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_max_vowel.insert(0, "2")
    
    def setup_ortho_editor(self, parent):
        row = 0
        
        ttk.Label(parent, text="Long Vowel Mapping (JSON format):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_long_vowels = scrolledtext.ScrolledText(parent, height=6, width=60)
        self.edit_long_vowels.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_long_vowels.insert(1.0, '{"a": "ä", "o": "ö", "u": "ü"}')
        row += 1
        
        ttk.Label(parent, text="Primary Accent:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.edit_accent = ttk.Combobox(parent, values=["none", "acute", "grave", "circumflex", "diaeresis"], width=57, state='readonly')
        self.edit_accent.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.edit_accent.set("diaeresis")
        row += 1
        
        self.edit_s_cedilla = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Transform S to Cedilla (ç)", variable=self.edit_s_cedilla).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
    
    def setup_batch_tab(self):
        main_frame = ttk.Frame(self.tab_batch)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        config_frame = ttk.LabelFrame(main_frame, text="Batch Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(config_frame, text="Profile:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.batch_profile_var = tk.StringVar()
        self.batch_profile_combo = ttk.Combobox(config_frame, textvariable=self.batch_profile_var, state='readonly', width=40)
        self.batch_profile_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Button(config_frame, text="Refresh", command=self.refresh_batch_profiles).grid(row=0, column=2, padx=(10, 0))
        
        ttk.Label(config_frame, text="Input Files (one per base language):").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.batch_files = []
        self.batch_file_labels = []
        
        for i in range(4):
            frame = ttk.Frame(config_frame)
            frame.grid(row=2+i, column=0, columnspan=3, sticky=tk.W, pady=2)
            
            label = ttk.Label(frame, text=f"Base {i+1}: No file selected", width=60, anchor=tk.W)
            label.pack(side=tk.LEFT)
            
            ttk.Button(frame, text="Browse", command=lambda idx=i: self.browse_batch_file(idx)).pack(side=tk.LEFT, padx=(5, 0))
            
            self.batch_file_labels.append(label)
            self.batch_files.append(None)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Process Batch", command=self.process_batch, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Files", command=self.clear_batch_files, width=15).pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="Batch Processing Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.batch_log = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.batch_log.pack(fill=tk.BOTH, expand=True)
    
    def refresh_profile_list(self):
        self.profile_manager.load_all_profiles()
        self.profile_listbox.delete(0, tk.END)
        for profile_id in self.profile_manager.get_all_profile_ids():
            profile = self.profile_manager.get_profile(profile_id)
            display_name = f"{profile.get('name', profile_id)} ({profile_id})"
            self.profile_listbox.insert(tk.END, display_name)
    
    def refresh_generator_profiles(self):
        self.profile_manager.load_all_profiles()
        profile_ids = self.profile_manager.get_all_profile_ids()
        self.gen_profile_combo['values'] = profile_ids
        if profile_ids and not self.gen_profile_var.get():
            self.gen_profile_var.set(profile_ids[0])
            self.on_generator_profile_selected(None)
    
    def refresh_editor_profiles(self):
        self.profile_manager.load_all_profiles()
        profile_ids = self.profile_manager.get_all_profile_ids()
        self.edit_profile_combo['values'] = profile_ids
    
    def refresh_batch_profiles(self):
        self.profile_manager.load_all_profiles()
        profile_ids = self.profile_manager.get_all_profile_ids()
        self.batch_profile_combo['values'] = profile_ids
    
    def on_profile_selected(self, event):
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        item_text = self.profile_listbox.get(idx)
        profile_id = item_text.split('(')[-1].rstrip(')')
        
        profile = self.profile_manager.get_profile(profile_id)
        if profile:
            self.profile_details_text.delete(1.0, tk.END)
            self.profile_details_text.insert(1.0, json.dumps(profile, indent=2, ensure_ascii=False))
            self.current_profile_id = profile_id
    
    def on_generator_profile_selected(self, event):
        profile_id = self.gen_profile_var.get()
        if not profile_id:
            return
        
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            return
        
        self.gen_profile_info.config(state=tk.NORMAL)
        self.gen_profile_info.delete(1.0, tk.END)
        
        info_text = f"Name: {profile.get('name', 'N/A')}\n"
        info_text += f"Bases: {', '.join(profile.get('bases', []))}\n"
        info_text += f"Description: {profile.get('description', 'N/A')}\n"
        
        self.gen_profile_info.insert(1.0, info_text)
        self.gen_profile_info.config(state=tk.DISABLED)
        
        bases = profile.get('bases', [])
        for i, widget in enumerate(self.input_text_widgets):
            if i < len(bases):
                parent = widget.master
                for child in parent.winfo_children():
                    if isinstance(child, ttk.Label):
                        child.config(text=f"Base Language {i+1} ({bases[i]}):")
                parent.pack(fill=tk.BOTH, expand=True, pady=5)
            else:
                widget.master.pack_forget()
    
    def new_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Profile")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="Profile ID:").pack(pady=(20, 5))
        id_entry = ttk.Entry(dialog, width=40)
        id_entry.pack()
        
        ttk.Label(dialog, text="Profile Name:").pack(pady=(10, 5))
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack()
        
        def create():
            profile_id = id_entry.get().strip()
            profile_name = name_entry.get().strip()
            
            if not profile_id:
                messagebox.showerror("Error", "Profile ID is required")
                return
            
            if profile_id in self.profile_manager.get_all_profile_ids():
                messagebox.showerror("Error", "Profile ID already exists")
                return
            
            new_profile = {
                "id": profile_id,
                "name": profile_name or profile_id,
                "description": "",
                "bases": ["en"],
                "fusion_weights": [1.0],
                "fusion_rules": {},
                "phonotactics": {
                    "vowels": "aeiou",
                    "forbidden_final_consonants": [],
                    "max_consonant_cluster": 3,
                    "max_vowel_cluster": 2
                },
                "orthography": {},
                "global_seed": 12345
            }
            
            self.profile_manager.create_profile(new_profile)
            self.refresh_profile_list()
            dialog.destroy()
            messagebox.showinfo("Success", f"Profile '{profile_id}' created successfully")
        
        ttk.Button(dialog, text="Create", command=create).pack(pady=(20, 0))
    
    def delete_profile(self):
        if not self.current_profile_id:
            messagebox.showwarning("Warning", "No profile selected")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete profile '{self.current_profile_id}'?"):
            self.profile_manager.delete_profile(self.current_profile_id)
            self.refresh_profile_list()
            self.profile_details_text.delete(1.0, tk.END)
            self.current_profile_id = None
            messagebox.showinfo("Success", "Profile deleted")
    
    def duplicate_profile(self):
        if not self.current_profile_id:
            messagebox.showwarning("Warning", "No profile selected")
            return
        
        original = self.profile_manager.get_profile(self.current_profile_id)
        if not original:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Duplicate Profile")
        dialog.geometry("400x150")
        
        ttk.Label(dialog, text="New Profile ID:").pack(pady=(20, 5))
        id_entry = ttk.Entry(dialog, width=40)
        id_entry.pack()
        id_entry.insert(0, f"{self.current_profile_id}_copy")
        
        def create_duplicate():
            new_id = id_entry.get().strip()
            
            if not new_id:
                messagebox.showerror("Error", "Profile ID is required")
                return
            
            if new_id in self.profile_manager.get_all_profile_ids():
                messagebox.showerror("Error", "Profile ID already exists")
                return
            
            duplicate = original.copy()
            duplicate['id'] = new_id
            duplicate['name'] = f"{duplicate.get('name', '')} (Copy)"
            
            self.profile_manager.create_profile(duplicate)
            self.refresh_profile_list()
            dialog.destroy()
            messagebox.showinfo("Success", f"Profile duplicated as '{new_id}'")
        
        ttk.Button(dialog, text="Duplicate", command=create_duplicate).pack(pady=(20, 0))
    
    def load_profile_to_editor(self, event):
        profile_id = self.edit_profile_var.get()
        if not profile_id:
            return
        
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            return
        
        self.edit_id.delete(0, tk.END)
        self.edit_id.insert(0, profile.get('id', ''))
        
        self.edit_name.delete(0, tk.END)
        self.edit_name.insert(0, profile.get('name', ''))
        
        self.edit_description.delete(1.0, tk.END)
        self.edit_description.insert(1.0, profile.get('description', ''))
        
        self.edit_bases.delete(0, tk.END)
        self.edit_bases.insert(0, ', '.join(profile.get('bases', [])))
        
        self.edit_weights.delete(0, tk.END)
        weights = profile.get('fusion_weights', [])
        self.edit_weights.insert(0, ', '.join(str(w) for w in weights))
        
        self.edit_seed.delete(0, tk.END)
        self.edit_seed.insert(0, str(profile.get('global_seed', 12345)))
        
        self.edit_semantic.set(profile.get('semantic_general', 'neutral'))
        
        fusion_rules = profile.get('fusion_rules', {})
        self.edit_min_cut.delete(0, tk.END)
        self.edit_min_cut.insert(0, str(fusion_rules.get('min_cut_point', 0.4)))
        
        self.edit_preserve_caps.set(fusion_rules.get('preserve_caps', True))
        self.edit_preserve_accents.set(fusion_rules.get('preserve_accents', False))
        self.edit_contractions.set(fusion_rules.get('contraction_handling', 'separate'))
        
        phono = profile.get('phonotactics', {})
        self.edit_vowels.delete(0, tk.END)
        self.edit_vowels.insert(0, phono.get('vowels', 'aeiou'))
        
        self.edit_forbidden.delete(0, tk.END)
        forbidden = phono.get('forbidden_final_consonants', [])
        self.edit_forbidden.insert(0, ', '.join(forbidden))
        
        self.edit_max_cons.delete(0, tk.END)
        self.edit_max_cons.insert(0, str(phono.get('max_consonant_cluster', 3)))
        
        self.edit_max_vowel.delete(0, tk.END)
        self.edit_max_vowel.insert(0, str(phono.get('max_vowel_cluster', 2)))
        
        ortho = profile.get('orthography', {})
        self.edit_long_vowels.delete(1.0, tk.END)
        long_vowel_map = ortho.get('long_vowel_mapping', {})
        self.edit_long_vowels.insert(1.0, json.dumps(long_vowel_map, ensure_ascii=False))
        
        self.edit_accent.set(ortho.get('primary_accent', 'none'))
        self.edit_s_cedilla.set(ortho.get('transform_s_to_cedilla', False))
    
    def save_profile_changes(self):
        profile_id = self.edit_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Warning", "No profile selected")
            return
        
        try:
            bases = [b.strip() for b in self.edit_bases.get().split(',') if b.strip()]
            weights = [float(w.strip()) for w in self.edit_weights.get().split(',') if w.strip()]
            
            if len(weights) != len(bases):
                messagebox.showerror("Error", "Number of weights must match number of bases")
                return
            
            try:
                long_vowel_json = self.edit_long_vowels.get(1.0, tk.END).strip()
                long_vowel_map = json.loads(long_vowel_json) if long_vowel_json else {}
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON in long vowel mapping")
                return
            
            forbidden = [c.strip() for c in self.edit_forbidden.get().split(',') if c.strip()]
            
            profile = {
                "id": self.edit_id.get().strip(),
                "name": self.edit_name.get().strip(),
                "description": self.edit_description.get(1.0, tk.END).strip(),
                "bases": bases,
                "fusion_weights": weights,
                "fusion_rules": {
                    "min_cut_point": float(self.edit_min_cut.get()),
                    "preserve_caps": self.edit_preserve_caps.get(),
                    "preserve_accents": self.edit_preserve_accents.get(),
                    "contraction_handling": self.edit_contractions.get()
                },
                "phonotactics": {
                    "vowels": self.edit_vowels.get(),
                    "forbidden_final_consonants": forbidden,
                    "max_consonant_cluster": int(self.edit_max_cons.get()),
                    "max_vowel_cluster": int(self.edit_max_vowel.get())
                },
                "orthography": {
                    "long_vowel_mapping": long_vowel_map,
                    "primary_accent": self.edit_accent.get(),
                    "transform_s_to_cedilla": self.edit_s_cedilla.get()
                },
                "semantic_general": self.edit_semantic.get(),
                "global_seed": int(self.edit_seed.get())
            }
            
            valid, errors = ProfileValidator.validate_profile(profile)
            if not valid:
                messagebox.showerror("Validation Error", "\n".join(errors))
                return
            
            self.profile_manager.update_profile(profile_id, profile)
            self.refresh_profile_list()
            messagebox.showinfo("Success", "Profile saved successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def reset_editor(self):
        profile_id = self.edit_profile_var.get()
        if profile_id:
            self.load_profile_to_editor(None)
    
    def validate_current_profile(self):
        profile_id = self.edit_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Warning", "No profile selected")
            return
        
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            return
        
        valid, errors = ProfileValidator.validate_profile(profile)
        
        if valid:
            messagebox.showinfo("Validation", "Profile is valid!")
        else:
            messagebox.showerror("Validation Errors", "\n".join(errors))
    
    def generate_language(self):
        profile_id = self.gen_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Warning", "Please select a profile")
            return
        
        profile_path = self.profile_manager.get_profile_path(profile_id)
        if not profile_path:
            messagebox.showerror("Error", "Profile file not found")
            return
        
        profile = self.profile_manager.get_profile(profile_id)
        num_bases = len(profile.get('bases', []))
        
        base_texts = []
        for i in range(num_bases):
            text = self.input_text_widgets[i].get(1.0, tk.END).strip()
            if not text:
                messagebox.showwarning("Warning", f"Base text {i+1} is empty")
                return
            base_texts.append(text)
        
        try:
            engine = ZipperEngine(str(profile_path))
            result = engine.process_texts(base_texts)
            
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, result)
            
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {str(e)}")
    
    def clear_generator(self):
        for widget in self.input_text_widgets:
            widget.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)
    
    def save_output(self):
        content = self.output_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "No output to save")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Output saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def browse_batch_file(self, index):
        filename = filedialog.askopenfilename(
            title=f"Select file for Base Language {index+1}",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            self.batch_files[index] = filename
            self.batch_file_labels[index].config(text=f"Base {index+1}: {Path(filename).name}")
    
    def clear_batch_files(self):
        for i in range(len(self.batch_files)):
            self.batch_files[i] = None
            self.batch_file_labels[i].config(text=f"Base {i+1}: No file selected")
    
    def process_batch(self):
        profile_id = self.batch_profile_var.get()
        if not profile_id:
            messagebox.showwarning("Warning", "Please select a profile")
            return
        
        profile_path = self.profile_manager.get_profile_path(profile_id)
        if not profile_path:
            messagebox.showerror("Error", "Profile file not found")
            return
        
        profile = self.profile_manager.get_profile(profile_id)
        num_bases = len(profile.get('bases', []))
        
        selected_files = [f for f in self.batch_files[:num_bases] if f]
        if len(selected_files) != num_bases:
            messagebox.showwarning("Warning", f"Please select exactly {num_bases} input files")
            return
        
        self.batch_log.delete(1.0, tk.END)
        self.batch_log.insert(tk.END, f"Starting batch processing with profile: {profile_id}\n")
        self.batch_log.insert(tk.END, f"Expected {num_bases} base files\n\n")
        
        try:
            base_texts = []
            for i, filepath in enumerate(selected_files):
                self.batch_log.insert(tk.END, f"Reading file {i+1}: {Path(filepath).name}\n")
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    base_texts.append(content)
            
            self.batch_log.insert(tk.END, "\nProcessing...\n")
            self.root.update()
            
            engine = ZipperEngine(str(profile_path))
            result = engine.process_texts(base_texts)
            
            output_filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"{profile_id}_output.txt"
            )
            
            if output_filename:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                self.batch_log.insert(tk.END, f"\nSuccess! Output saved to: {output_filename}\n")
                self.batch_log.insert(tk.END, f"Generated {len(result.split())} words\n")
            else:
                self.batch_log.insert(tk.END, "\nProcessing completed but output not saved\n")
            
        except Exception as e:
            self.batch_log.insert(tk.END, f"\nError: {str(e)}\n")
            messagebox.showerror("Error", f"Batch processing failed: {str(e)}")


def main():
    root = tk.Tk()
    app = LanguageZipperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()