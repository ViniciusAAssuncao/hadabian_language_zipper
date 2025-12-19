import difflib
text1 = """Miadelto

Søk gødne gobuid 18-e30 jarige omtuĉi sla
Labuĉmajstero

Vogdiaŭ mitmøt renkontas ’nyoron mener
Hiuwal migrø verslindĝegad
Sagtdele anmaldolaĵoj stuke
Stansor laspaskortkarto vermeld

Ĉarjy eswata jaĝaĵo vret
Kajvile wetwat ditobeteken estas
Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Miadelto (ne)

Lastamplakra bendogødne kajregt
Ekblød verskeriklik, valsiek sentas malbone
Selfssa ekten flatali vuesveno
Itplu krampendewē vurtkramfoj

Disse giedbone incitprae geflember flamita
Kajmet lafdmeme sorporsenlan benvita
’nuneguei bynaino sagtkerslinkat kandelumo
Ja, ekvat miated, diormat kulturo desesti

Ĉarjy eswata jaĝaĵo vret
Kajvile wetwat ditobeteken estas
Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Es, it'smy Dela (nao) (ne)

’nioskre alna diehemel ja
Dar sengele-skares snānĝelaj armeoj
Vanwalkedak vultegment vaerpluisvl plumviando
Sormia jeugfanaĝon metgiekrot

Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Miadelto (ne)

Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Es, it'smy Dela (nao) (ne)
"""

text2 = """Miadelto

Søk gødne gobuid 18-e30 jarige omtuĉi sla
Labuĉmajstero

Vogdiaŭ mitmøt renkontas ’nyoron mener
Hiuwal migrø verslindĝegad
Sagtdele anmaldolaĵoj stuke
Stansor laspaskortkarto vermeld

Ĉarjy eswata jaĝaĵo vret
Kajvile wetwat ditobeteken estas
Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Miadelto (ne)

Lastamplakra bendogødne kajregt
Ekblød verskeriklik, valsiek sentas malbone
Selfssa ekten flatali vuesveno
Itplu krampendewē vurtkramfoj

Disse giedbone incitprae geflember flamita
Kajmet lafdmeme sorporsenlan benvita
’nuneguei bynaino sagtkerslinkat kandelumo
Ja, ekvat miated, diormat kulturo desesti

Ĉarjy eswata jaĝaĵo vret
Kajvile wetwat ditobeteken estas
Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Es, it'smy Dela (nao) (ne)

’nioskre alna diehemel ja
Dar sengele-skares snānĝelaj armeoj
Vanwalkedak vultegment vaerpluisvl plumviando
Sormia jeugfanaĝon metgiekrot

Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Miadelto (ne)

Dismy Dela (nao) (ne)
Miadelto (ne)
Ja, ditøs Miadelto (ne)
Es, it'smy Dela (nao) (ne)
"""


def compare_texts(t1, t2):
    if t1 == t2:
        return "Os textos são idênticos."
    else:
        diff = difflib.ndiff(t1.splitlines(), t2.splitlines())
        return '\n'.join(diff)


result = compare_texts(text1, text2)
print(result)
