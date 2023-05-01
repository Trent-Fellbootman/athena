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

    @property
    def isEmpty(self) -> bool:
        return self._content == ""

    @staticmethod
    def makeEmpty() -> Any:
        return AAISText("")

    @staticmethod
    async def translateFrom(content: "AAISThinkingLanguageContent") -> AAISThinkingLanguageTranslationResult:
        # TODO
        raise NotImplementedError()

    def add(self, other) -> Self:
        return AAISText(self._content + other.content)

    def format(self, args: Iterable[Self]) -> Self:
        return AAISText(self._content.format(*[arg.content for arg in args]))
