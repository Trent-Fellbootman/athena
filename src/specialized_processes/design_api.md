# API Server Design

## Thinking Language Translation

Each module server is responsible for translating the info / warning /
error messages to the thinking language of the AAIS system.

For avoiding boilerplate code, default translators should be available.

For translation between API-intelligible language (which basically
means commands that the underlying intelligent or non-intelligent API
can be fed directly without further translation. E.g., for a
terminal API, this could be bash commands) and the AAIS's
thinking language, the API module server should implement the
following additional methods:

- `checkForValidityAndParseArguments`: Takes in the message
written in the thinking language, checks for validity of the
request and parses the arguments. Since this method is
- `makeReturnMessage`: Takes the output of the underlying
actual API and formats it into a message written in the
thinking language. This method typically formats INFO, WARNING and
ERROR logs, as well as the final output into a single message. This
method is also responsible for filtering and summarizing the logs,
returning only what the caller needs to know.

The underlying actual API (e.g., the bash terminal) is
thinking-language-agnostic. To make the actual API call,
the API module server implements the following additional method:

- `makeAPICall`: Takes in the arguments parsed by `checkForValidityAndParseArguments`
and makes the actual API call. This method is awaitable; it
completes when the API call is completed or terminated with an error.
It returns the output of the API call, as well as the logs (if any).
This method typically involves no artificial intelligence (except
when the API itself is intelligent, e.g., if the API is DALL E 2).

## Establishing New Communication Channels

An API call is not completely a regular inter-process communication.
Special methods are implemented on the API hub & API module server
to handle the peculiarities of API calls.

The API hub implements the following additional methods:
- `callAPI`, which forwards the caller process's request to the
API module server, and returns the response to the caller process.
- `reportToCaller`, which is called by the API module server.
This method forwards the API module server's reports regarding
the status of the API call and is awaitable; it completes when
the API hub server confirms that the caller has received the
message.

When an API module server receives a request from the API hub,
it does the following:

1. Check for validity and parse the arguments with `checkForValidityAndParseArguments`.
2. Make the API call with `makeAPICall`, or return an error message
if the request is invalid.
3. Wait until **the part that can happen before the caller is
acknowledged about the status of the call**, is completed. For non-interactive
API calls, this is the end of the API call; for interactive
API calls, this is the time when the interactive session is spawned,
the spawned process is notified of the existence of the caller,
and what follows is the matter between the caller and the spawned
session, which is none of the API module server's business.
4. Forward the call status to the caller via the API hub's
`reportToCaller` method. Wait until it is confirmed that
the caller has received the message.
5. Interactive API calls only: do the remaining part of the API call
that can only happen after the caller is notified. For interactive
sessions, this typically means setting up the communication channel
between the caller and the spawned session.
