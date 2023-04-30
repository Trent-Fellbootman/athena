"""
Defines the base classes for the AAIS framework.
"""

from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional, Self
from dataclasses import dataclass
from enum import Enum


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

    Note that two pieces of information with the same encoding
    are not necessarily of the same type of "ThinkingLanguageContent".
    For example, Python, XML and natural language can all be encoded
    as string; however, they are not of the same type of ThinkingLanguageContent.
    Chinese and English are both natural languages; they are not the same type, either.

    Such a difference should be reflected in the type of the content.
    For example, Chinese content is of type "ChineseThinkingLanguageContent";
    English content is of type "EnglishThinkingLanguageContent".
    It is not recommended to use the same type for both Chinese and English content
    (e.g., "NaturalLanguageContent" or "TextContent").

    If the types of two objects are the same, they are assumed to have semantically
    the same type (e.g., both Chinese).
    """

    @abstractmethod
    @property
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

    @abstractmethod
    @property
    async def isValid(self) -> bool:
        """
        Returns true if the content is valid.

        This is useful for checking semantic types.
        E.g., if the content is English, but the type is Chinese,
        this method should return false.
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


class AAISMessageType(Enum):

    """
    Represents which type a message is of.

    Possible values:
        communication: A message sent when a process is running.
        endProcess: A message sent when a process terminates.
    """

    communication = 0
    endProcess = 1


@dataclass
class AAISMessageHeader:
    """
    Represents metadata that all messages have.

    This is not a base class; DO NOT subclass this class
    to create specialized messages, e.g., API call return messages.
    """

    messageType: AAISMessageType
    sender: "AAISProcess"


@dataclass
class AAISMessagePacket(ABC):
    header: AAISMessageHeader
    content: AAISThinkingLanguageContent

    async def send(self, process: "AAISProcess"):
        """
        Sends this message to `process`.

        This method is just a wrapper around the `handleMessage` method
        of processes in the AAIS system, to make the semantics of sending
        a message more natural.
        Under the hood, this method calls and awaits the abstract method
        `handleMessage` on `process`.
        I.e., basically, the implementation of this method is:

        `await process.handleMessage(self)`

        This method is awaitable; it completes when the message is
        successfully handled by `process`.


        The exact meaning that "the message has been handled" may
        depend on the specific types of the process and the message.
        For regular inter-process communication, it typically means
        that the message has been added to the receiver's message history
        (think about ChatGPT);
        For API calls, the return message is considered
        "handled" only when the caller successfully receives the message.
        It is NOT considered "handled" when the message is forwarded to
        the parent API server, but has not yet been received by the caller.
        """

        await process.handleMessage(self)


@dataclass
class AAISReferenceTableEntryContext:
    """
    Represents the context of a reference table entry.
    This typically includes basic information about the referee,
    as well as the relationship between the referee and the current
    process (e.g., what the referee sends and expects to receive).
    """

    refereeDescription: AAISThinkingLanguageContent
    # TODO: add more fields


@dataclass
class AAISReferenceTableEntryMetadata(ABC):
    """
    The metadata of a reference table entry.
    """

    # TODO: add more fields if needed


@dataclass
class AAISReferenceTableEntry:
    """
    Represents an entry in the reference table, a table kept
    by every process in the AAIS system.
    """

    # metadata
    metadata: AAISReferenceTableEntryMetadata

    # provides contextual information about this referee. E.g., what it does.
    context: AAISReferenceTableEntryContext

    # the handle to the referenced process
    referee: "AAISProcess"


@dataclass
class AAISReferenceTable:
    """
    Represents the reference table, a table kept by every process
    in the AAIS system.

    In each process, a reference table keeps track of all the processes
    that the process has reference to.
    Each process can only send messages to or receive messages from
    processes in its reference table.

    The reference table provides contextual information about each referee.
    This information helps the process to decide which referees to send
    messages to when it decides to send a message, and also provides
    contextual information when a message from a referee is received.
    """

    # metadata
    metadata: Any

    # the entries in the table
    entries: Iterable[AAISReferenceTableEntry]


class AAISProcess(ABC):

    def __init__(self):
        self.referenceTable = AAISReferenceTable(metadata=None, entries=set())

    @abstractmethod
    async def handleMessage(self, message: AAISMessagePacket):
        """
        This method is called when a message is sent to the process.

        When a process sends a message via `message.send`, this method
        is called on the receiver process under the hood.

        This method is awaitable; it completes when the message is
        handled by the process.

        The exact meaning that "the message has been handled" may
        depend on the specific types of the process and the message.
        For regular inter-process communication, it typically means
        that the message has been added to the receiver's message history
        (think about ChatGPT);
        For API calls, the return message is considered
        "handled" only when the caller successfully receives the message.
        It is not considered "handled" when the message is forwarded to
        the parent API server, but has not yet been received by the caller.
        """

        pass
