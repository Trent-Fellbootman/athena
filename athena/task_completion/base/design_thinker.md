# Thinker Process Design

# Introduction

A thinker process is a process that performs high-level thinking and
that communicates and cooperates with other processes through
sending and receiving messages, typically to accomplish a certain task.

# Design

A thinker process is designed to do thinking step by step.
At each step, it may send messages to other processes, or to do some thinking,
or to terminate itself. At the end of each step, it may choose
either to continue thinking or to wait until receiving a message.

The thinking material (typically in thinking language) produced by thinking
is parsed and interpreted by an **interpreter**. The interpreter reads
the thoughts produced in this step, determines whether the process wishes
to send messages to other processes, and if so, which processes to send
to and what messages to send. The interpreter also determines whether the
process wishes to terminate itself and whether the process wishes to
continue thinking or to wait until receiving a message.

## The Thinking Step

In each thinking step, the thinker does the following:

- Determine whether to continue thinking or to wait until receiving a message
from a process (optionally, the process to wait on might be specified)
- Decide whether to send messages to certain processes.
There might be multiple messages sent to multiple processes.
- Handle unhandled messages received from other processes.
- Modify the reference table.

One thinking step may incorporate multiple rounds of prompting & responses
(e.g., when the thinker uses a chat API as its backend).

One way to implement the thinking step is to use a state machine.
At the start of a thinking step, a state is initialized.
This state hosts all the information in this thinking step
(initially all empty) in its fields, e.g., the choice of
whether to wait, the message sending operations, modifications to
the reference table, etc.
Then, several sub-steps (basically one sub-step corresponds to one
step of prompting) are run.
At each sub-step, the prompt is generated based on the current state;
when the thinking-step-completion-condition (basically that all fields
of the state variable have been filled in) is satisfied, the thinking
step completes, the "instructions" parsed and stored into the state variable
are committed (e.g., the message sending operations are performed, the
reference table is modified, etc.), and the next thinking step starts
at the moment specified by the state variable (e.g., when a message
from a certain process is received).

Alternatively, "instructions" can be committed as soon as they are parsed,
e.g., the reference table might be modified before the current thinking step
completes.

Each sub-step begins with generating a prompt based on the current state
of the state variable.
For example, if the only information that is not known is the message
sending operations, the generated prompt may ask the thinker what
messages it wants to send, and to whom.
At each sub-step, the process may choose to perform certain actions.
Performing an action will possibly modify the state variable, and will
return a report (on success) or an error message (on failure).
After the action is performed, the report or the error message
is reported, and a new sub-step starts.

An example state variable may include:

- A current operation field, determining what is being done in the
current thinking step (e.g., sending messages to other processes,
modifying the reference table, determining whether to wait for a message,
etc.).
This is useful for determining what the next prompt should be.
- A message sending operation field consisting of the message sending operations
specified by the thinker so far, and a boolean indicating whether those
are all the message sending operations that the process intends to perform.
- A reference table modification field consisting of new connections to set up,
old connections to remove, and whether "that's all" (similar to the previous field).
- A wait field, including both a boolean denoting whether to wait for a message
before starting another thinking step, and which process to wait on (if any).


## Concurrency

In a thinking process, thinking happens serially; that is, one
thinking step can only be performed after the previous step is
completed.

However, messages can be received at any time.
When a message is received, it is added to a message buffer.
Later when a thinking step completes, the thinking process
extracts all messages from the buffer and processes them,
and then performs another thinking step.
Even if new messages are received when the previous messages are being
processed, those messages are simply added to the buffer and will be
processed when the next thinking step completes.