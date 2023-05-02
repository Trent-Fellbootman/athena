from typing import Iterable, Self, Any

from ..core import AAISThinkingLanguageContent
from ..core.thinking_language import AAISThinkingLanguageTranslationResult


class AAISText(AAISThinkingLanguageContent):
    """
    Thinking language content as text.

    This thinking language is compatible with most LLMs (e.g. ChatGPT).

    Formatting of this thinking language uses Python's default formatting,
    i.e., `str.format()`.
    """

    def __init__(self, content: str):
        super().__init__()

        self._content = content

    @property
    def getContent(self) -> str:
        return self._content

    # override
    @property
    def isEmpty(self) -> bool:
        return self._content == ""

    # override
    @staticmethod
    def makeEmpty() -> Any:
        return AAISText("")

    # override
    @staticmethod
    async def translateFrom(content: "AAISThinkingLanguageContent") -> AAISThinkingLanguageTranslationResult:
        # TODO
        raise NotImplementedError()

    # override
    def add(self, other) -> Self:
        return AAISText(self._content + other.content)

    # override
    def format(self, args: Iterable[Self]) -> Self:
        return AAISText(self._content.format(*[arg.content for arg in args]))

    # override
    def astype(self, targetType: type):
        if targetType == str:
            return self._content
        elif targetType == int:
            return int(self._content)
        elif targetType == float:
            return float(self._content)
        else:
            raise TypeError(f"Cannot convert AAISText to {targetType}")
