# Hierarchical API server design

## Introduction

The basic idea is, when looking at inputs / outputs,
there is no difference between an API server
(whether terminal or hub) and an ordinary process.
Both send / receive messages the same way, and
message sending does not block for reasons other than
network issues (i.e., the message sending coroutine
completes as long as the message is **received**, but not
necessarily **processed**).

The difference between an API server and a regular process
lies in the internal structure & prompting methods being used.
Such a difference enables API servers to exhibit different behavior,
e.g., discriminating between API requests and return messages from
child API servers, forwarding return messages to the correct parent, etc.

## API Hubs

There are two capabilities specific to API hub servers:

1. Discriminating between API requests and return messages from child API servers;
2. Forwarding return messages to the correct parent.

Achieving the first one is easy: just use an LLM to identify the nature
of the messages.

The second one is a bit more complicated.
The idea is to keep a table of all received API requests as well as
information associated with each of them.
In a typical implementation,
each entry in the table should store the following information:

1. A summary of what the request is about (what the caller wants to do)
2. A local ID that uniquely identifies the request in the table.
3. The address of the request's sender (this could be either the
caller or the parent API server from which the request is forwarded).
4. The status of the message (e.g., running, completed, failed, etc.).

The whole life cycle of an API request at an API hub server
is as follows:

1. Hub server receives an API request from a client.
2. The hub server determines the nature of the message (a request), and
creates a new entry in the table for it.
The entry is filled as follows:
   1. The hub server summarizes the request and fills the summary field.
   2. The hub server calls a local ID generator (typically non-intelligent)
   and assigns the generated ID to the ID field.
   3. The metadata field of the received message typically contains
   the sender's address, which is copied to the address field.
   4. The status field is set to "unhandled".
3. The hub server forwards the request to the correct child API server
and sets the status field to "running".
4. When the child API server returns a message and the message
is determined to be about the request, the hub server sets the status
field to "completed" (or failed, etc.) and forwards the message to the client.

## Setting Up New Communication Channels

In some cases, completing an API call requires settings up new
communication channels for the caller by modifying its reference table.

In such cases, the "instructions" to set up the communication channel
are embedded in the message returned to the caller.
E.g., the hub server may return to the caller a message like this:

*"I have spawned a new process that will guide you through completing
this API call.
The process is listening on port 12345 and you can connect to it."*
