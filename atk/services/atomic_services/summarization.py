from ..pure_function import AAISPureFunction, inputType
from typing import TypeVar

from ...backend_abstractions import AAISAIBackend
from ...core import AAISThinkingLanguageContent
from ...backend_abstractions import AAISChatAPI


T = TypeVar('T', bound=AAISThinkingLanguageContent)


class AAISSummarizer(AAISPureFunction[T, T]):
    """
    A pure function task that takes in a long content and summarizes it.
    """

    def __init__(self, backend: AAISAIBackend, **kwargs):
        """
        Initialize this summarization task with the given backend.

        Args:
            backend: The backend to use for this summarization task.
            kwargs: Any additional arguments to pass to the backend.
                These will differ based on the type of the backend.

                For AAISChatBackend, the only additional argument is
                `template`, which will be used to format the content
                to summarize when the summarizer is called.

                An example `template` is:

                "The user has made an API call request. The request is: {0}.
                Summarize the request and return the summary.
                Output the summary ONLY and NOTHING ELSE."
        """

        if isinstance(backend, AAISChatAPI):
            self._backend = backend

            match kwargs.get("template"):
                case None:
                    raise ValueError("AAISChatBackend requires a template to be specified.")
                case template:
                    self._template: T = template
        else:
            raise NotImplementedError(f"Summarization task is not implemented for backend: {type(backend)}")

    async def call(self, inputs: inputType)\
            -> AAISPureFunction.InvocationResult:
        if isinstance(self._backend, AAISChatAPI):
            # Format the content to summarize with the template.
            prompt = AAISChatAPI.Message(
                senderType=AAISChatAPI.Message.SenderType.PROMPTER,
                content=self._template.format(inputs)
            )

            return_message = await self._backend.generateResponse([prompt])

            return AAISPureFunction.InvocationResult(
                success=True,
                output=return_message.content,
                errorMessage=None
            )
        else:
            raise NotImplementedError(f"Summarization task is not implemented for backend: {type(self._backend)}")
