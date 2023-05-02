from ..functional import AAISFunctional
from ...core import AAISThinkingLanguageContent, AAISResult
from ...backend_abstractions import AAISAIBackend, AAISChatAPI

from typing import TypeVar, Collection


T = TypeVar('T', bound=AAISThinkingLanguageContent)


class AAISParser(AAISFunctional[T, Collection[T]]):
    """
    A parser that parses ThinkingLanguageContent, extracts the information contained,
    and returns the extracted information in separated form.

    The indices of the items are assumed to be 0-based; keep this in mind when writing prompt templates.

    Note that this functional does not check the validity of inputs before parsing them,
    as this is an atomic functional.
    Check the input validity with another functional if that should be done.

    The input type of this functional is ThinkingLanguageContent;
    the output is a collection of ThinkingLanguageContent.

    This functional is useful in scenarios such as parsing an API call request in natural language
    into a list of arguments that can be readily fed into the API.
    """

    def __init__(self, backend: AAISAIBackend, **kwargs):
        """
        Args:
            backend: The backend to use for this summarization task.
            kwargs: Any additional arguments to pass to the backend.
                These arguments are detailed as follows.

        ADDITIONAL ARGUMENT (kwargs)
        --------

        The additional argument `item_count` (int),
         which denotes the number of items that should be produced from each parsing operation,
         is required for all backends.

        In case of using a chat backend, the parsing happens in multiple turns,
        and the chat backend produces one item at a time.
        Hence, the following additional arguments are required:

        - `initial_prompt_template`: The template used to format the input
         (i.e., content to be parsed) and generate the initial prompt.
        - `per_turn_prompt_generator`: This is callable that generates
         the prompt to feed into the chat backend for each turn.
         It takes 2 arguments: the index of the item to be yielded (0-based),
         as well as whether the item to be yielded is the last item (bool,
         True if it is the last item); and outputs the prompt for the current turn
         as a ThinkingLanguageContent.

        An example of the arguments is as follows:

        - `item_count`: 3
        - `initial_prompt_template`: "I want you to parse an API call request written
        in natural language into arguments.

        The syntax of the API call is: api <argument 0> <argument 1> <argument 2>

        Now, the user has submitted an API call request.
        The request is as follows:

        {}

        Please parse the request into the arguments.
        Output one argument at a time, in order.
        Now, output argument 0.
        Remember, you should output the argument ONLY and NOTHING ELSE."

        - `per_turn_prompt_generator`: lambda index, is_last: f"Now, output argument {index}.
        Remember, you should output the argument ONLY and NOTHING ELSE."
        if not is_last else "Now, output the last argument.
        Remember, you should output the argument ONLY and NOTHING ELSE."
        """

        self._item_count: int = kwargs['item_count']

        if isinstance(backend, AAISChatAPI):
            self._backend = backend

            self._initial_prompt_template: AAISThinkingLanguageContent = kwargs['initial_prompt_template']
            self._per_turn_prompt_generator: callable = kwargs['per_turn_prompt_generator']

        else:
            raise NotImplementedError(f"AI backend {backend} is not supported for this functional!")

    async def call(self, inputs: T) -> AAISResult[Collection[T], AAISThinkingLanguageContent]:
        if isinstance(self._backend, AAISChatAPI):
            current_argument_index = 0
            message_history = []
            parsed_items = []

            # Generate the initial prompt
            initial_prompt = self._initial_prompt_template.format(inputs)

            message_history.append(initial_prompt)

            while current_argument_index < self._item_count:
                response = await self._backend.generateResponse(message_history)
                message_history.append(response)
                parsed_items.append(response.content)

                current_argument_index += 1

                if current_argument_index == self._item_count:
                    break

                new_prompt = self._per_turn_prompt_generator(
                    current_argument_index, current_argument_index == self._item_count - 1)

                message_history.append(new_prompt)

                return AAISResult(
                    success=True,
                    output=parsed_items,
                    errorMessage=None
                )

        else:
            raise NotImplementedError()
