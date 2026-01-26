from engine import OriginalLanguageEngine


engine = OriginalLanguageEngine('./conlangs/mabadi_language.json')

engine.word_cache['livro'] = {
    "lemma": "livro",
    "default": "banal",
    "synsets": [{"word": "banal", "tags": ["common"], "affinity": 1.0}]
}

plural_form = engine.broken_plural_handler.apply_plural("banal", "Number=Plur", "NOUN")
print(f"Singular: banal -> Plural: {plural_form}")

plural_form_reg = engine.broken_plural_handler.apply_plural("ba", "Number=Plur", "NOUN")
print(f"Singular: ba -> Plural: {plural_form_reg}")