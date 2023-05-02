from ..core import AAISThinkingLanguageContent

from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

T = TypeVar('T')


@dataclass
class AAISResult(Generic[T]):
    success: bool
    output: Optional[T]
    errorMessage: Optional[AAISThinkingLanguageContent]
