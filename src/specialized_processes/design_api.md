# API Server Design

## Design Principles

An API server is just like any process in an AAIS system.
A process is able to call the API as long as it has a reference
to the API server process stored in its reference table, and it
makes an API call by sending a message to the API server.
A process can also have references to multiple API server processes
in its reference table at the same time; in this way, it can forward
calls of different APIs, or different classes of APIs to the
appropriate API server.

Caller processes are unaware of the internal structure or
implementations of the API server.
The API server appears to the caller process as one coherent
entity with the ability to call one or multiple APIs.

## API Server Hierarchy

API servers are composable, meaning that small, specialized
API servers can be combined to form a larger, more complex API server
with multiple capabilities.
In this way, an API server is actually a tree structure, with
the leaves being the "terminal API servers" (i.e., API servers
that have access to only one, "atomic" API, such as DALL E 2).
When a process calls this API server, what actually happens is that
the request gets passed down and dispatched at each level of the tree,
until it reaches the terminal API server.
Similarly, when a terminal API server reports the status of an API
call to the caller, the status gets passed back up the tree
until it reaches the root, and then the caller process.

## Timing and Synchronization

One special type of API calls are those that set up communication
channels between the caller and another process.
When this is the case, the caller first needs to know that a new
communication channel will be set up; only then can the new "contact"
start sending messages to the caller.

In these scenarios, the API call actually consists of two parts:
the first part involves things like parsing arguments and checking
for validity, which does not interfere with the caller process and
can happen before the caller is notified of the status of the API
call; the second part involves setting up the communication channel,
which can only happen after the caller is notified of the status of
the API call.

To handle these cases, the `handleMessage` method of an API server
needs to be customized.
It first determines whether the message is a request to make an API
call or a response from one of its sub-servers (typically by checking
the type of the message or some special metadata fields).
In the former case, the message is considered to be "handled" when
it is received by the current server (NOT when it reaches the leaf
node, since it is possible that the request is inappropriate and
the API server is unable to find a sub-server that can do the job),
so there is nothing that needs to be awaited;
in the latter case, the message is considered to be "handled" only
when it reaches the original caller, so the API server needs to
call the `handleMessage` method of its parent (if any.
Here, "parent" means the process from which the API call
corresponding to the process is dispatched) and await on it.
If the parent is the caller process, then `handleMessage` method
would complete when the caller process receives the message;
if the parent is another "higher-level" API server, then a
call to its `handleMessage` method would invoke the same procedure,
until the caller process is reached.
The result is a stack of calls to `handleMessage`, completed only
when the caller receives the message.

When the `handleMessage` method completes, the API server is certain
that the caller has received the message, and it can proceed to
the part of the API call which can only happen after the caller
is notified of the status of the API call, such as setting up
the communication channel.
