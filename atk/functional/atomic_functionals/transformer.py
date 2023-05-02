from ..functional import AAISFunctional, inputType
from typing import TypeVar

from ...backend_abstractions import AAISAIBackend
from ...core import AAISThinkingLanguageContent, AAISResult
from ...backend_abstractions import AAISChatAPI


T = TypeVar('T', bound=AAISThinkingLanguageContent)


class AAISTransformer(AAISFunctional[T, T]):
    """
    A functional that transforms the input to produce output.

    This "Transformer" is NOT the "Transformer" in "Attention is All You Need"
    (For those who haven't read the paper: "Attention is All You Need" is the
    paper that proposed the transformer architecture, the backbone of many
    LLMs, such as ChatGPT).

    Both the input and output are a single AAISThinkingLanguageContent.

    The "transformer" functional can represent a wide range of tasks, e.g.,
    summarization, translation, code production, planning, etc.
    """

    def __init__(self, backend: AAISAIBackend, **kwargs):
        """
        Create a transformer functional with the given backend.

        Args:
            backend: The backend to use for this summarization task.
            kwargs: Any additional arguments to pass to the backend.
                These will differ based on the type of the backend.

                For AAISChatBackend, the only additional argument is
                `template`, which will be used to format the content
                in order to produce the prompt.

                An example `template` is:

                "The user has made an API call request. The request is: {0}.
                Summarize the request and return the summary.
                Output the summary ONLY and NOTHING ELSE."

                By applying this template, the constructed functional is
                effectively a summarizer.
        """

        if isinstance(backend, AAISChatAPI):
            self._backend = backend

            match kwargs.get("template"):
                case None:
                    raise ValueError("AAISChatBackend requires a template to be specified.")
                case template:
                    self._template: T = template
        else:
            raise NotImplementedError(f"Transformer functional is not implemented for backend: {type(backend)}")

    async def call(self, inputs: inputType)\
            -> AAISResult[T, AAISThinkingLanguageContent]:
        if isinstance(self._backend, AAISChatAPI):
            # Format the content to summarize with the template.
            prompt = AAISChatAPI.Message(
                senderType=AAISChatAPI.Message.SenderType.PROMPTER,
                content=self._template.format(inputs)
            )

            return_message = await self._backend.generateResponse([prompt])

            return AAISResult(
                success=True,
                value=return_message.content,
                errorMessage=None
            )
        else:
            raise NotImplementedError(f"Transformer functional is not implemented for backend: {type(self._backend)}")
