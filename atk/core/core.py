"""
Defines the base classes for the AAIS framework.
"""

from abc import ABC, abstractmethod
from typing import Self, Any, List, Tuple, Dict, Optional, Iterable, Set, Type, Sequence
from dataclasses import dataclass
from enum import Enum
import asyncio


class AAISThinkingLanguageContent(ABC):
    @abstractmethod
    @property
    async def isEmpty(self) -> bool:
        """
        Returns true if the content is empty.
        """

        pass


class AAISThinkingLanguageServer(ABC):
    @abstractmethod
    async def convertToThinkingLanguage(self, content: Any) -> AAISThinkingLanguageContent:
        """
        Converts the given content to the thinking language content.

        Returns:
            The converted content.
        """

        pass

    async def format(self, template: AAISThinkingLanguageContent, *args: Sequence[AAISThinkingLanguageContent]) \
            -> AAISThinkingLanguageContent:
        """
        Fills in `template` with `args`.
        """

        pass


class AAISSystemServer(ABC):

    def __init__(self, thinkingLanguageServerClass: Type[AAISThinkingLanguageServer]):
        self.thinkingLanguageServer = thinkingLanguageServerClass()


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
class AAISMessageMetadata:
    """
    Represents metadata that all messages have.

    This is not a base class; DO NOT subclass this class
    to create specialized messages, e.g., API call return messages.
    """

    messageType: AAISMessageType
    sender: "AAISProcess"


@dataclass
class AAISMessage(ABC):
    metadata: AAISMessageMetadata
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
    entries: Set[AAISReferenceTableEntry]


class AAISProcess(ABC):

    def __init__(self, systemHandle: AAISSystemServer):
        self.referenceTable = AAISReferenceTable(metadata=None, entries=set())
        self.systemHandle = systemHandle

    @abstractmethod
    async def handleMessage(self, message: AAISMessage):
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
