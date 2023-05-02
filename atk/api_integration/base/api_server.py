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

    class APICallRecordTable:

        @dataclass
        class Record:
            class APICallStatus(Enum):
                UNHANDLED = 0
                RUNNING = 1
                SUCCESS = 2
                FAILURE = 3

            description: AAISThinkingLanguageContent
            id: Any  # TODO
            senderAddress: AAISProcessAddress
            status: APICallStatus

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self._records: Set[AAISAPIServer.APICallRecordTable.Record] = set()

        @property
        def records(self) -> Set[Record]:
            return self._records

        def createEntry(self) -> Record:
            """
            Generates a new ID, creates an entry with the ID,
            adds the entry to the table, and returns the reference to the entry.
            """

            # TODO

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._apiCallRecords = self.APICallRecordTable()

    @property
    def apiCallRecordTable(self) -> APICallRecordTable:
        return self._apiCallRecords
