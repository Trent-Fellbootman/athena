from ..base import AAISAPIHub
from ..specialized_classes import AAISAPIHubWithFunctionalBackend
from ...backend_abstractions import AAISAIBackend, AAISChatAPI
from ...functional import atomic_functionals as atomic, compositors
from ...thinking_languages.text import AAISText
from ...core import AAISException

from typing import Optional


class AAISDefaultAPIHub(AAISAPIHubWithFunctionalBackend):
    """
    Default implementation of an API hub.
    """

    def __init__(self, backend: AAISAIBackend):
        """
        Constructs a default API hub server process.

        Arguments:
            backend:
                The AI backend to use for the API hub.
                Currently, only the chat backend is supported.

        Additional Arguments (kwargs):
        --------
        For chat backend, the following additional arguments are supported:
            native_language: The "native natural language" of the chat backend.
                Prompts are generated differently depending on the native language.
                With good AI backends, the API hub should work correctly even if
                the native language is different from the language of the messages
                received. However, it is still recommended to make the chat backend
                work in the same language as the messages received.

                This argument is case-insensitive, and should be set to a natural
                human language like "English". Currently, pre-written default
                prompt templates are available for English only, which means the
                only valid value for this argument is "English".
        """

        super().__init__(AAISDefaultAPIHub._make_default_backend(backend))

    supported_native_languages = ["English"]

    @staticmethod
    def _make_default_backend(backend: AAISAIBackend, **kwargs) \
            -> AAISAPIHubWithFunctionalBackend.Backend:

        # TODO: add error handling for all selectors.
        #  Perhaps wrap them in `AAISSupervisedFunctional`s.

        if isinstance(backend, AAISChatAPI):
            language = kwargs.get("native_language", "English")
            match language.lower():
                case "english":
                    def message_type_determiner_lambda(response: AAISText):
                        if response.content == "REQUEST":
                            return AAISDefaultAPIHub.APIServerMessageType.REQUEST
                        elif response.content == "REPORT":
                            return AAISDefaultAPIHub.APIServerMessageType.RETURN_MESSAGE
                        else:
                            raise AAISException()

                    def errorMessageFormatter(errorType: AAISAPIHub.ErrorType,
                                              errorMessage: Optional[AAISText]) -> AAISText:
                        # TODO: finetune these error messages for LLM-intelligibility.
                        match errorType:
                            case AAISAPIHub.ErrorType.FAILED_TO_DETERMINE_CHILD_SERVER_RETURN_RESULT_TYPE:
                                return AAISText("""
I dispatched your API call request to a child server and the child server has returned a result,
but I was unable to determine if the result is successful or not.
""")
                            case AAISAPIHub.ErrorType.FAILED_TO_DETERMINE_MESSAGE_TYPE:
                                return AAISText("""
I am unable to determine the type of the message you sent.

I am an API Hub server and I am supposed to receive API call requests and report messages from API servers.

It seems that you neither requested an API call, nor reported the result of an API call.
""")
                            case AAISAPIHub.ErrorType.FAILED_TO_FIND_HANDLER:
                                return AAISText("""
It seems that no API call I support can handle your request.
""")
                            case AAISAPIHub.ErrorType.EXECUTION_ERROR:
                                return_message = AAISText("""
There was an error executing the API call.
""")
                                if errorMessage is not None:
                                    return_message += AAISText(f"""

The error message is as follows:

{errorMessage.content}

""")
                            case AAISAPIHub.ErrorType.FAILED_TO_MATCH_API_CALL_RECORD:
                                # TODO: do we need to include the API call ID here?
                                return AAISText("""
I am unable to find the API call record pertaining to your report.

It seems that the specific API call operation that your report pertains to
does not exist in my records.
""")

                    def return_message_type_determiner_lambda(response: AAISText) -> AAISAPIHub.APICallReturnResultType:
                        if response.content == "SUCCESS":
                            return AAISDefaultAPIHub.APICallReturnResultType.SUCCESS
                        elif response.content == "FAILURE":
                            return AAISDefaultAPIHub.APICallReturnResultType.FAILURE
                        else:
                            raise AAISException()

                    return AAISAPIHubWithFunctionalBackend.Backend(
                        requestSummarizer=atomic.AAISTransformer(
                            backend=backend,
                            template=AAISText("""
The user has made an API call request. The request is as follows:

"{}"

Summarize the request and return the summary. Output the summary ONLY and NOTHING ELSE.

For example, if the user says "I want to search the internet", your response should be "search the internet".""")
                        ),

                        messageTypeDeterminer=compositors.AAISSequentialFunctional(
                            functionals=[
                                atomic.AAISTransformer(
                                    backend=backend,
                                    template=AAISText("""
I want you to determine if a message is an API call request or a "report message" from an API server.

API call requests are messages that requests an API call; this could be either natural language or command.

Examples of API call request messages:

"Search the internet for cats."
"bash -c 'echo hello world'"

Report messages are messages that are sent by an API server to report the result of an API call.
These could be either successful reports or error messages.

If a message is an API call request, you should output "REQUEST" only, and NOTHING ELSE.

Examples of report messages:

"API call request with ID 057e has completed; generated image was saved to `/var/tmp/koala.png`."
"Assertion error at line 54: type(x) == int"

If a message is a report message, you should output "REPORT" only, and NOTHING ELSE.

If a message is neither a report message nor an API call request, you should output "INVALID" only, and NOTHING ELSE.

Example of "INVALID" messages:

"Koalas are so cute!"

Now, here is a message:

"{}"

Determine if this message is an API call request or a report message.
As mentioned earlier, output "REQUEST", "REPORT", or "INVALID" only, and NOTHING ELSE.

For example, if the message is "koalas are so cute", your response should be "INVALID", and NOTHING ELSE.

DO NOT PROVIDE ANY EXPLANATION.""")),
                                atomic.AAISLambda(
                                    function=message_type_determiner_lambda)
                            ]),
                        handlerSelector=atomic.AAISSelector(
                            backend=backend,
                            prompt_template=AAISText("""
There are several available APIs. Their functionalities are described as follows:

{0}


Now, the user has made an API request. The request is as follows:

"{1}"

Please output the index of the API that best matches the request. If no match can be found, output "-1".

Output the index ONLY and NOTHING ELSE. DO NOT PROVIDE ANY EXPLANATIONS.
"""),
                            item_formatter=lambda index, item: f"API {index}: {item}",
                            separator="\n\n",
                        ),
                        errorMessageFormatter=atomic.AAISLambda(
                            function=errorMessageFormatter
                        ),
                        # FIXME: using such a prompt would result in the header
                        #  (e.g., "API call has returned") to be repeated many times.
                        #  fix this.
                        #  Perhaps use a Transformer instead of a Lambda?
                        #  Also, should we include the API call ID here?
                        parentReturnMessageGenerator=atomic.AAISLambda(
                            function=lambda returnMessage, apiCallDescription: AAISText(f"""
The API call has returned. The return message is as follows:

{returnMessage.content}

""")
                        ),
                        # TODO: do we need to use a transformer to transform the request intelligently?
                        childServerRequestGenerator=atomic.AAISLambda(
                            function=lambda request, description: request
                        ),
                        returnResultTypeDeterminer=compositors.AAISSequentialFunctional(
                            functionals=[
                                atomic.AAISTransformer(
                                    backend=backend,
                                    template=AAISText("""
A job has just finished and its result have been reported. I want you to determine if the result is successful or not.

The result is as follows:

{}

If the result is successful, output "SUCCESS" only, and NOTHING ELSE;
if the result is unsuccessful, output "FAILURE" only, and NOTHING ELSE;
if you are unable to determine if the result is successful or not, output "UNKNOWN" only, and NOTHING ELSE.

DO NOT PROVIDE ANY EXPLANATIONS.
""")
                                ),
                                atomic.AAISLambda(
                                    function=return_message_type_determiner_lambda
                                )
                            ]
                        )
                    )
                case _:
                    raise NotImplementedError(
                        f"Default implementation does not support {language}. " +
                        f"Supported native languages: {AAISDefaultAPIHub.supported_native_languages}")

        else:
            raise NotImplementedError(f"Default implementation does not support {type(backend).__name__}")
