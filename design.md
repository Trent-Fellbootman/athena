# Core Design

## Process

An `AAISProcess` represents a process in an AAIS system. It can be either intelligent or not.
This is the base class for all processes in the system.

### Shared Properties

Every process in an AAIS system keeps two tables: one for processes that subscribe to the
current process, and the other for the process that the current process subscribes to.

### Reference Tables

The reference table is a dynamic database that every process maintains.
It contains handles to processes that the current process references, as well as a description of each referee.
The description is typically used by an LLM to infer which referees to send messages to,
as well as to provide context information when a referee sends a message to the current process,
so it typically contains information such as:

1. What the referee does.
2. What the referee wants from the current process (e.g., what messages the referee wants to receive).
3. What the referee can provide to the current process (e.g., what messages the referee can send).

### Message Passing

Processes can send messages to each other. There are two types of messages that a process can
send: communication messages, sent when the process is running; and end-process messages, sent
when the process terminates (either successfully or with an error).

When a process sends a message, it does the following things:

1. Decide the content of the message. The content is consistent across messages received by
all subscribers; different subscribers receive the same message, but handle it differently.

2. Decide which subscribers to send the message to. This is usually done by prompting an LLM,
letting the LLM to decide which subscribers should receive the message, based on the description
of each subscriber (stored in the process table).

3. Send the message to the subscribers. This involves calling the message handling methods
of each subscriber. Message handling methods are a consistent interface for all subscribers,
but different process classes may override these methods for customized behavior.

There are other ways to implement message passing; for example, instead of sending the same message to all subscribers and let the subscribers handle the message in a customized way, one may choose to customize the message before sending it to a subscriber.
