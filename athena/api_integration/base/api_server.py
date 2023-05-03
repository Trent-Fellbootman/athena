from ...core import (
    AAISThinkingLanguageContent, AAISProcess, AAISProcessAddress, AAISResult
)

from enum import Enum
from abc import ABC
from dataclasses import dataclass
from typing import Any, Set, Optional


class AAISAPIServer(AAISProcess, ABC):

    class APIServerMessageType(Enum):
        REQUEST = 0
        RETURN_MESSAGE = 1

    class APICallRecordTable:

        @dataclass
        class Record:
            class APICallStatus(Enum):
                UNHANDLED = 0
                RUNNING = 1
                SUCCESS = 2
                FAILURE = 3

            description: AAISThinkingLanguageContent
            # identifier of the API call record in the record table of the current process
            identifier: Any  # TODO
            # identifier of the API call record in the record table of the parent process
            # (i.e., the process that dispatched the API call)
            # it is possible for this field to be None, as the parent process may not have
            # a record table.
            parentIdentifier: Optional[Any]  # TODO
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

        def findRecordWithID(self, identifier: Any) -> AAISResult[Record, AAISThinkingLanguageContent]:
            # TODO
            pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._apiCallRecords = self.APICallRecordTable()

    @property
    def apiCallRecordTable(self) -> APICallRecordTable:
        return self._apiCallRecords
