from dataclasses import dataclass
from typing import Any, Optional, Self, Iterable
from abc import ABC, abstractmethod


@dataclass
class AAISThinkingLanguageTranslationResult:
    """
    Represents the result of a translation.
    """
    success: bool
    # the translated content in the target thinking language.
    translatedContent: Optional[Any]
    # the error message in the target thinking language.
    errorMessage: Optional[Any]


class AAISThinkingLanguageContent(ABC):
    """
    Represents content intelligible to a certain AI.
    For example, for ChatGPT, this is a string;
    for GPT-4, this might be a combination of text and images.
    "ThinkingLanguageContent" is used when an AI is thinking.

    Type consistency does not imply semantic consistency.
    Two pieces of information can have the same `AAISThinkingLanguageContent` type,
    as long as they have the same encoding.
    For example, both natural language and code can be encoded as text;
    they may share the same type (e.g., AAISText).

    It is the user's responsibility to translate the content
    (e.g., from Chinese to English) when needed.
    The framework offers flexibility to mix two pieces of information
    even if they are in different languages semantically.
    """

    @property
    @abstractmethod
    async def isEmpty(self) -> bool:
        """
        Returns true if the content is empty.
        """

        pass

    @staticmethod
    @abstractmethod
    async def makeEmpty() -> Any:
        """
        Makes empty content of this type.

        # TODO: The type should be `Self`, instead of `Any`.
        """

        pass

    @staticmethod
    @abstractmethod
    async def translateFrom(content: "AAISThinkingLanguageContent") -> AAISThinkingLanguageTranslationResult:
        """
        Translates the content from another type of ThinkingLanguageContent.

        Returns the translation result.
        """

        pass

    @abstractmethod
    def add(self, other) -> Self:
        """
        Returns the concatenation of two `ThinkingLanguageContent` pieces.

        This method typically involves no formatting or intelligent stuff,
        and is expected to return quickly and thus not being awaitable.

        The two pieces of content are assumed to be the same type.
        """
        pass

    def __add__(self, other) -> Self:
        # TODO: add error handling
        assert type(self) == type(other)

        return self.add(other)

    @abstractmethod
    def format(self, args: Iterable[Self]) -> Self:
        """
        Uses this content as a template and formats it with the given arguments.

        E.g., 'Hello, {0}!'.format('world') -> 'Hello, world!'
        """
        pass
