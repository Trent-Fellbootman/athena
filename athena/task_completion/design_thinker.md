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