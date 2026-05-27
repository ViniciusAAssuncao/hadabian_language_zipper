from .phonology import PhonologyHandler
from .morphology import (
    AffixHandler,
    BrokenPluralHandler,
    ConstructStateHandler,
    DegreeHandler,
    DualHandler,
    ReduplicationHandler,
    RootSystemHandler
)

__all__ = [
    "PhonologyHandler",
    "AffixHandler",
    "BrokenPluralHandler",
    "ConstructStateHandler",
    "DegreeHandler",
    "DualHandler",
    "ReduplicationHandler",
    "RootSystemHandler",
    "ConceptHandler",
    "FalseCognateHandler",
    "LexicalConfluenceHandler",
    "LoanwordHandler",
    "PolysemyHandler",
    "SemanticFieldHandler",
    "SynonymHandler",
    "AllomorphyHandler",
    "CliticHandler",
    "DemonstrativeHandler",
    "PossessiveHandler",
    "PrepositionHandler"
]