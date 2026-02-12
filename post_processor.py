import re
from typing import Dict, List, Optional


def polish_output(output: str, profile: Dict, original_input: str, functions_info: Optional[List[Dict]] = None) -> str:
    cleaned = output.strip()

    replacements = {
        '؛': ';',
        '،': ',',
        '؟': '?'
    }
    for k, v in replacements.items():
        cleaned = cleaned.replace(k, v)

    cleaned = re.sub(r'\s+([,;:.!?])', r'\1', cleaned)

    dynamic_prefixes = set(profile.get(
        'morphology', {}).get('joining_prefixes', []))

    det_sys = profile.get('determiner_system', {})
    def_art = det_sys.get('definite_article', {})
    if def_art.get('procliticizes'):
        base_art = def_art.get('form', '').replace('-', '')
        if base_art:
            dynamic_prefixes.add(base_art + '-')

            case_sys = profile.get('case_system', {})
            if case_sys.get('enabled'):
                for _, marker_data in case_sys.get('markers', {}).items():
                    marker = marker_data.get('marker', '')
                    if marker.startswith('-'):
                        clean_marker = marker.replace('-', '')
                        combined = f"{base_art}{clean_marker}"
                        dynamic_prefixes.add(combined + '-')

    interrogative_particles = []
    for p in profile.get('interrogative_system', {}).get('question_particles', []):
        particle_str = p.get('particle', '')
        if particle_str:
            interrogative_particles.append({'marker': particle_str})

    systems_to_scan = [
        profile.get('negation_system', {}).get('strategies', []),
        profile.get('tam_system', {}).get('rules', []),
        interrogative_particles
    ]

    for system in systems_to_scan:
        for rule in system:
            marker = rule.get('marker', '')
            if isinstance(marker, str) and marker.endswith('-'):
                dynamic_prefixes.add(marker)

    adp_sys = profile.get('adposition_system', {}).get(
        'inflected_prepositions', {})
    if adp_sys.get('enabled'):
        for prep in adp_sys.get('forms', {}).keys():
            dynamic_prefixes.add(prep + '-')

    sorted_prefixes = sorted(list(dynamic_prefixes), key=len, reverse=True)

    for prefix in sorted_prefixes:
        clean_prefix = prefix.replace('-', '')
        if len(clean_prefix) < 2:
            continue

        pattern = fr'\b({re.escape(clean_prefix)})\s*-\s*(\w+)'
        cleaned = re.sub(pattern, r'\1-\2', cleaned, flags=re.IGNORECASE)

        pattern_direct = fr'\b({re.escape(clean_prefix)})\s+(\w+)'

        matches = re.finditer(pattern_direct, cleaned, flags=re.IGNORECASE)
        for match in matches:
            p_word = match.group(1)
            next_word = match.group(2)
            if p_word.lower() == next_word.lower() and len(p_word) < 3:
                continue
            cleaned = re.sub(pattern_direct, r'\1-\2',
                             cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r'(\w+)-\s+(\w+)', r'\1-\2', cleaned)

    sandhi_rules = profile.get('phonotactics', {}).get(
        'sandhi', {}).get('rules', [])
    for rule in sandhi_rules:
        pattern = rule.get('pattern')
        replacement = rule.get('replacement')
        if pattern and replacement:
            flags = re.IGNORECASE if rule.get('ignore_case') else 0
            try:
                cleaned = re.sub(pattern, replacement, cleaned, flags=flags)
            except re.error:
                continue

    cleaned = re.sub(r'([,;:.!?])(?=[^\s])', r'\1 ', cleaned)

    if cleaned:
        cleaned = re.sub(r'[,;:\-–—\s]+$', '', cleaned)
        last_char = cleaned[-1] if cleaned else ''
        if last_char not in ['.', '!', '?', '"', "'", ')']:
            cleaned += '.'

    output_words = cleaned.split()
    final_words = []

    for i, word in enumerate(output_words):
        current_word = word
        clean_current = re.sub(r'[^\w\-]', '', word)

        should_capitalize = False

        is_start = (i == 0)
        if not is_start and i > 0:
            prev_word = output_words[i-1]
            if prev_word.endswith(('.', '!', '?')):
                should_capitalize = True

        if is_start:
            should_capitalize = True

        if not should_capitalize and functions_info:
            for sent_info in functions_info:
                for func in sent_info.get('functions', []):
                    if func.get('pos') == 'PROPN' and func.get('word', '').lower() in clean_current.lower():
                        should_capitalize = True
                        break

        if should_capitalize and current_word:
            if current_word[0].isalpha():
                current_word = current_word[0].upper() + current_word[1:]
            elif len(current_word) > 1 and not current_word[0].isalnum():
                for j in range(len(current_word)):
                    if current_word[j].isalpha():
                        current_word = current_word[:j] + \
                            current_word[j].upper() + current_word[j+1:]
                        break

        final_words.append(current_word)

    cleaned = ' '.join(final_words)
    cleaned = re.sub(r'\s+([,;:.!?])', r'\1', cleaned)

    return cleaned
