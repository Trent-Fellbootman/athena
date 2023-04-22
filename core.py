from abc import ABC, abstractclassmethod, abstractmethod
from typing import Any, List, Tuple, Map, Dict, Iterable
from dataclasses import dataclass
from enum import Enum

@dataclass
class EndProcessMessage:
    
    """Represents a message returned by a process
    when a process ends (either successfully or with an error)

    Fields:
        message: The message to return, in the AAIS system's **thinking language**
        isSuccess: A boolean value indicating whether the process ended successfully or with an error
    """
    
    message: Any
    isSuccess: bool
    
@dataclass
class SubscriberMetadata:
    
    """The metadata of a subscriber handle of a `SubscriberTableEntry`.
    
    Fields:
        isCommunication: True if the subscriber is subscribed to messages sent by the process
            when the process is still running.
        isTerminal: True if the subscriber indicates that it wishes to receive the message sent
            by the process when the process ends (i.e., whether to receive the `EndProcessMessage`).
    """
    
    isCommunication: bool
    isTerminal: bool
    
@dataclass
class SubscriberTableEntry:
    
    """Represents a single entry in a **subscriber table** of a process.
    
    Fields:
        label: The label of the subscriber. Usually describes what would happen
            if the subscriber is called, in the AAIS system's **thinking language**.
        metadata: The metadata of the subscriber, contains information such as which messages should be
            sent to this subscriber (for example, whether the subscriber subscribes to all the messages,
            or just the `EndProcessMessage` sent when the process ends).
        subscriber: The subscriber handle that can be called.
    """

    label: Any
    metadata: SubscriberMetadata
    subscriber: callable

@dataclass
class InterProcessMessage:
    
    """Represents an inter-process message, usually sent across processes.
    
    Fields:
        message: The message, usually in the AAIS system's **thinking language**.
    """
    
    message: Any

class SubscriberTable:
    
    """Represents a subscriber table that is kept by every process in an AAIS system.
    """
    
    def __init__(self):
        self.entries = set()
    
    def addSubscribers(self, entries: Iterable[SubscriberTableEntry]):
        """Adds entries to the subscriber table.

        Args:
            entries (Iterable[SubscriberTableEntry]): The entries to add to the subscriber table.
        """
        
        self.entries.update(entries)
    
    def removeSubscribers(self, subscribers: Iterable[callable]):
        """Removes entries from the subscriber table.
        
        Args:
            subscribers (Iterable[callable]): The subscribers to remove from the subscriber table.
        """
        
        
        entries_to_remove = {entry for entry in self.entries if entry.subscriber in subscribers}
        
        for entry in entries_to_remove:
            self.entries.remove(entry)

class AAISProcess(ABC):
    
    """The base class for all processes in an AAIS system.
    
    The lifecycle of a process (either worker or planner) is as follows:
    
    1. Ready: The process is ready to start after being spawned.
    2. Running: The process is started and running.
    3. Ended: The process has finished running and is ended (either successfully or with an error).

    Each process starts in the ready state after the constructor is called.
    When `start` is called, the process begins running.
    When the process finishes (whether successfully or not), the process transitions from the "running" state
    to the "end" state, and sends an `EndProcessMessage` to all of its `terminalSubscribers`.
    """
    
    def __init__(self):
        self._subscriberTable = SubscriberTable()

    @abstractmethod
    # TODO: Determine argument types
    def start(self, *args, **kwargs):
        pass

    @abstractmethod
    # TODO: Determine argument types
    def end(self, *args, **kwargs):
        pass
    
    @abstractmethod
    # TODO: determine argument types
    def addSubscriber(self, *args, **kwargs):
        pass
    
class WorkerProcess(AAISProcess):
    pass

class PlannerProcess(AAISProcess):
    pass