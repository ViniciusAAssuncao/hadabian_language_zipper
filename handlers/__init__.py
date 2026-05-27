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
from .lexicon import (
    ConceptHandler,
    FalseCognateHandler,
    LexicalConfluenceHandler,
    LoanwordHandler,
    PolysemyHandler,
    SemanticFieldHandler,
    SynonymHandler
)
from .discourse import (
    AllomorphyHandler,
    CliticHandler,
    DemonstrativeHandler,
    PossessiveHandler,
    PrepositionHandler
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