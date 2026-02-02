import re
from typing import Dict

def polish_output(output: str, profile: Dict, original_input: str) -> str:
    output = re.sub(r'\s*؛\s*', '; ', output)
    output = re.sub(r'\s{2,}', ' ', output)
    
    output = re.sub(r'(\w+)-\s+', r'\1-', output)
    output = re.sub(r'\s+-(\w+)', r'-\1', output)
    
    original_words = original_input.split()
    output_words = output.split()
    for i, ow in enumerate(output_words):
        if i < len(original_words) and original_words[i][0].isupper():
            output_words[i] = ow.capitalize()
    output = ' '.join(output_words)
    
    if 'sandhi' in profile.get('phonotactics', {}):
        pass
    
    return output