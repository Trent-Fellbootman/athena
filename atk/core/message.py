from dataclasses import dataclass
from enum import Enum
from abc import ABC

from .thinking_language import AAISThinkingLanguageContent
from .address import AAISProcessAddress


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
        senderAddress: AAISProcessAddress

    header: Header
    content: AAISThinkingLanguageContent
