import os
from pathlib import Path

class GlyphExporter:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def export_glyph(self, glyph_image, char, seed):
        filename = f"glyph_{char}_seed{seed}.png"
        filepath = os.path.join(self.output_dir, filename)
        glyph_image.save(filepath, "PNG")
        return filepath
    
    def export_alphabet(self, glyphs_dict, seed):
        exported_files = []
        for char, image in glyphs_dict.items():
            filepath = self.export_glyph(image, char, seed)
            exported_files.append(filepath)
        return exported_files
    
    def get_output_dir(self):
        return self.output_dir
