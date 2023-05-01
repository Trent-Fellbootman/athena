from abc import ABC, abstractmethod
from dataclasses import dataclass
from ..core import AAISThinkingLanguageContent


@dataclass
class AAISPromptLookupTable(ABC):
    """
    A table of prompt templates that generates prompts
    for performing certain services. Think of this
    as a table of format strings, e.g., "Hello, {}"

    All attributes should have type AAISThinkingLanguageContent
    and should have the same type.
    """

    pass
