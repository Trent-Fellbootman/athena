"""
Abstraction for a chat backend (e.g., ChatGPT)
"""

from abc import abstractmethod
from typing import Iterable
from dataclasses import dataclass
from enum import Enum

from .base import AAISAIBackend
from ..core import AAISThinkingLanguageContent

from typing import TypeVar, Generic


prompterType = TypeVar('prompterType', bound=AAISThinkingLanguageContent)
AIType = TypeVar('AIType', bound=AAISThinkingLanguageContent)


class AAISChatAPI(AAISAIBackend, Generic[prompterType, AIType]):
    """
    Abstraction for a chat backend server (e.g., ChatGPT)
    where two parties (prompter & AI) participate in each conversation.

    The two parties do not need to send messages turn by turn;
    it is possible that one party sends multiple messages before
    another party replies.

    When the API is prompted, it ALWAYS returns a message sent by the party
    "AI", and there will ALWAYS be ONE message ONLY, instead of multiple messages.

    Users may choose to merge multiple messages sent by one party in
    a turn into one message, or to prompt the API without merging.

    One server can have multiple sessions and does not
    store the message history for any of them.

    When text continuation is requested for a session,
    all contextual information needed needs to be passed in.

    Think of this of OpenAI's Chat API.
    """

    @dataclass
    class Message:
        class SenderType(Enum):
            # the message is sent by the prompter.
            # prompter is not necessarily a human;
            # in automated prompting systems,
            # the prompter is typically a non-intelligent program
            # that formats a template with parsed information
            PROMPTER = 0
            # AI sender.
            # the AI sender is typically intelligent,
            # using LLM as backend.
            AI = 1

        senderType: SenderType
        content: prompterType | AIType

    @abstractmethod
    async def generateResponse(self, messages: Iterable[Message]) -> Message:
        """
        Generates a response given the message history.

        The generated response will ALWAYS have senderType AI and content type AIType.
        """

        pass
