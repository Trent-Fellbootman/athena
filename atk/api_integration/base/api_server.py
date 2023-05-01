from ...core import (
    AAISThinkingLanguageContent, AAISProcess, AAISProcessAddress
)

from enum import Enum
from abc import ABC
from dataclasses import dataclass
from typing import Any, Set, Self


class AAISAPIServer(AAISProcess, ABC):

    class APIServerMessageType(Enum):
        request = 0
        returnMessage = 1

    class APICallTable:

        @dataclass
        class Entry:
            class APICallStatus(Enum):
                UNHANDLED = 0
                RUNNING = 1
                SUCCESS = 2
                FAILURE = 3

            summary: AAISThinkingLanguageContent
            id: Any  # TODO
            senderAddress: AAISProcessAddress
            status: APICallStatus

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.entries: Set[Self.Entry] = set()

        def createEntry(self) -> Entry:
            """
            Generates a new ID, creates an entry with the ID,
            adds the entry to the table, and returns the reference to the entry.
            """

            # TODO

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apiCallTable = self.APICallTable()
