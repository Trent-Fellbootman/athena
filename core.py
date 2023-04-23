from abc import ABC, abstractclassmethod, abstractmethod
from typing import Any, List, Tuple, Dict, Iterable, Self
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
class ProcessTableEntryMetadata:
    
    """The metadata of a process handle of a `ProcessTableEntry`.
    
    Fields:
        isCommunication: True if the subscriber is subscribed to messages sent by the process
            when the process is still running.
        isTerminal: True if the subscriber indicates that it wishes to receive the message sent
            by the process when the process ends (i.e., whether to receive the `EndProcessMessage`).
    """
    
    isCommunication: bool
    isTerminal: bool
    
@dataclass
class ProcessTableEntry:
    
    """Represents a single entry in a **subscriber table** of a process.
    
    Fields:
        label: The label of the subscriber. Usually describes what would happen
            if the subscriber is called, in the AAIS system's **thinking language**.
        metadata: The metadata of the subscriber, contains information such as which messages should be
            sent to this subscriber (for example, whether the subscriber subscribes to all the messages,
            or just the `EndProcessMessage` sent when the process ends).
        subscriber: The subscriber process.
        # TODO
        `Subscriber` should be of type AAISProcess; using `Any` in
            type annotation is due to Python's limitations.
    """

    label: Any
    metadata: ProcessTableEntryMetadata
    process: Any

@dataclass
class InterProcessMessage:
    
    """Represents an inter-process message, usually sent across processes.
    
    Fields:
        message: The message, usually in the AAIS system's **thinking language**.
    """
    
    message: Any

class ProcessTable:
    
    """Represents a subscriber table that is kept by every process in an AAIS system.
    """
    
    def __init__(self):
        self.entries = set()
    
    def addSubscribers(self, entries: Iterable[ProcessTableEntry]):
        """Adds entries to the subscriber table.

        Args:
            entries (Iterable[SubscriberTableEntry]): The entries to add to the subscriber table.
        """
        
        self.entries.update(entries)
    
    def removeSubscribers(self, subscribers: Iterable[Any]):
        """Removes entries from the subscriber table.
        
        Args:
            subscribers (Iterable[AAISProcess]): The subscribers to remove from the subscriber table.
        
        # TODO: `subscribers` should be of type Iterable[AAISProcess]; using Iterable[Any] in type annotation is due to
        # Python's limitations.
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
        self._subscriberTable = ProcessTable()

    @abstractmethod
    # TODO: Determine argument types
    def start(self, *args, **kwargs):
        pass

    @abstractmethod
    # TODO: Determine argument types
    def end(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def addSubscriber(
        self, label: Any, subscriber: Self,
        subscribeToCommunication: bool, subscribeToTerminal: bool):
        
        """Add a subscriber to this process.

        Args:
            label (Any): The label of the subscriber which will be used in the subscriber table entry.
                This is usually a description of what would happen if the subscriber is called, written
                in the AAIS's **thinking language**.
                
            subscriberHandle (callable): The callable handle of the subscriber.
            
            subscribeToCommunication (bool): Whether this subscriber wishes to receive communication messages
                sent by the current process.
                
            subscribeTerminal (bool): Whether this subscriber wishes to receive the end-process message
                sent when the current process ends.
        """
        
        new_entry = ProcessTableEntry(
            label=label,
            metadata=ProcessTableEntryMetadata(isCommunication=subscribeToCommunication, isTerminal=subscribeToTerminal),
            process=subscriber)
        
        self._subscriberTable.addSubscribers([new_entry])

    @abstractmethod
    def handleCommunicationMessage(self, message: InterProcessMessage):
        
        """Handles a communication message sent by a running process that the current process
        subscribes to.

        Args:
            message (InterProcessMessage): The message sent to this process.
        """
        
        pass
    
    @abstractmethod
    def handleEndProcessMessage(self, message: EndProcessMessage):
        
        """Handles an end-process message sent by a process that just ended running
        (whether successfully or not) and that the current process subscribes to.

        Args:
            message (EndProcessMessage): The end-process message sent to this process.
        """
        
        pass
    
class WorkerProcess(AAISProcess):
    pass

class PlannerProcess(AAISProcess):
    pass