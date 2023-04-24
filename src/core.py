"""
Defines the base classes for the AAIS framework.
"""

from abc import ABC, abstractmethod, abstractstaticmethod
from typing import Self, Any, List, Tuple, Dict, Optional, Iterable, Set, Type, Sequence
from dataclasses import dataclass
from enum import Enum
import asyncio


class AAISThinkingLanguageContent(ABC):
    @abstractmethod
    @property
    def isEmpty(self) -> bool: pass


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
        Fills in a template with the given arguments.
        """

        pass


class AAISSystemServer(ABC):

    def __init__(self, thinkingLanguageServerClass: Type[AAISThinkingLanguageServer]):
        self.thinkingLanguageServer = thinkingLanguageServerClass()


class AAISMessageType(Enum):
    communication = 0
    endProcess = 1


@dataclass
class AAISMessage(ABC):
    messageType: AAISMessageType
    content: Any


@dataclass
class AAISReferenceTableEntry:
    metadata: Any
    context: Any
    # TODO: The type here should be AAISProcess.
    # However, Any is used because currently I don't know
    # how to use a class before it is defined.
    referee: Any


@dataclass
class AAISReferenceTable:
    metadata: Any
    entries: Set[AAISReferenceTableEntry]


class AAISProcess(ABC):

    def __init__(self, systemHandle: AAISSystemServer):
        self.referenceTable = AAISReferenceTable(metadata=None, entries=set())
        self.systemHandle = systemHandle

    @abstractmethod
    async def handleMessage(self, message: AAISMessage):
        pass
