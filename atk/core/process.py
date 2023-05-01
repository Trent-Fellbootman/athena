from dataclasses import dataclass
from typing import Set
from abc import ABC, abstractmethod

from .thinking_language import AAISThinkingLanguageContent
from .message import AAISMessagePacket


class AAISProcess(ABC):

    class ReferenceTable:
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

        @dataclass
        class Entry:
            """
            Represents an entry in the reference table, a table kept
            by every process in the AAIS system.
            """

            @dataclass
            class Context:
                """
                Represents the context of a reference table entry.
                This typically includes basic information about the referee,
                as well as the relationship between the referee and the current
                process (e.g., what the referee sends and expects to receive).
                """

                refereeDescription: AAISThinkingLanguageContent
                # TODO: add more fields

            @dataclass
            class Metadata(ABC):
                """
                The metadata of a reference table entry.
                """

                # TODO: add more fields if needed

            # metadata
            metadata: Metadata

            # provides contextual information about this referee. E.g., what it does.
            context: Context

            # the handle to the referenced process
            referee: "AAISProcess"

        def __init__(self):
            self._entries: Set[AAISProcess.ReferenceTable.Entry] = set()

    def __init__(self):
        self.referenceTable = self.ReferenceTable()

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
