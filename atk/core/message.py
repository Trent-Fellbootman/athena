from dataclasses import dataclass
from enum import Enum
from abc import ABC

from .thinking_language import AAISThinkingLanguageContent
from .process import AAISProcess


@dataclass
class AAISMessagePacket(ABC):

    @dataclass
    class Header:
        """
        Represents metadata that all messages have.

        This is not a base class; DO NOT subclass this class
        to create specialized messages, e.g., API call return messages.
        """

        class MessageType(Enum):
            """
            Represents which type a message is of.

            Possible values:
                communication: A message sent when a process is running.
                endProcess: A message sent when a process terminates.
            """

            communication = 0
            endProcess = 1

        messageType: MessageType
        sender: AAISProcess

    header: Header
    content: AAISThinkingLanguageContent

    async def send(self, process: AAISProcess):
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
