from abc import ABC, abstractmethod

from .message import AAISMessagePacket
from .address import AAISProcessAddress


class AAISSystemServer(ABC):

    __doc__ = """
    Represents a system server of an AAIS system.
    
    The system server is responsible for:
    
    - Managing the processes in the system;
    - Assigning addresses to processes;
    - Providing interface for sys calls (e.g., spawning a new process)
    - Providing interface for inter-process communication (e.g., sending a message)
    """

    @abstractmethod
    async def sendMessage(self, message: AAISMessagePacket, receiver: AAISProcessAddress):
        """
        Sends `message` to its receiver.

        This message is awaitable; it completes when the message is
        received by the receiver.
        """
        pass

