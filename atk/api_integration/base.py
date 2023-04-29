from ..core.core import AAISThinkingLanguageContent, AAISProcess

from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Set, Self


class AAISAPIServer(ABC, AAISProcess):

    class APIServerMessageType(Enum):
        request = 0
        returnMessage = 1

    class APICallTable:

        @dataclass
        class Entry:
            class APIStatus(Enum):
                UNHANDLED = 0
                RUNNING = 1
                SUCCESS = 2
                FAILURE = 3

            summary: AAISThinkingLanguageContent
            id: Any  # TODO
            sender: AAISProcess
            status: APIStatus

        def __init__(self):
            self.entries: Set[Self.Entry] = set()

        def createEntry(self) -> Entry:
            """
            Generates a new ID, creates an entry with the ID,
            adds the entry to the table, and returns the reference to the entry.
            """

            # TODO

    def __init__(self):
        self.apiCallTable = self.APICallTable()
