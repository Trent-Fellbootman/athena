from typing import TypeVar, Collection, Tuple

from ..functional import AAISFunctional
from ...core import AAISThinkingLanguageContent, AAISResult
from ...backend_abstractions import AAISAIBackend, AAISChatAPI


T = TypeVar('T', bound=AAISThinkingLanguageContent)


class AAISSelector(AAISFunctional[Tuple[Collection[T], T], int]):
    """
    A selector that selects one item from a list of items.

    The input to this pure function is a list of items and a "requirement"
    to match each item against. The output is the index of the selected item.

    As an example, this pure function can be used to select an API interface
    based on a request. A sample prompt would be:

    "There are several available APIs. Their functionalities are described as follows:

    API 1: Text to image.
    API 2: Image to text.
    API 3: Web browser.

    Now, the user has made an API request. The request is as follows:

    "I want to convert text to image."

    Please output the index of the API that best matches the request.
    Output the index ONLY and NOTHING ELSE."

    In the above example, the descriptions of the 3 APIs are the items; the request is the "requirement".
    """

    def __init__(self, backend: AAISAIBackend, **kwargs):
        r"""
        Args:
            backend: The backend to use for this summarization task.
            kwargs: Any additional arguments to pass to the backend. These arguments are detailed as follows.

        ADDITIONAL ARGUMENTS (kwargs)
        --------

        The additional argument `error_message`, which is the error message to return
        when call failed, is required for all backends.

        Note that the call is considered successful as long as the output of the backend can be decoded to int
        and is valid (i.e., the decoded integer is in range(0, len(choices)) or is -1).
        no matter whether a choice is selected or not. This implies that normally no error should be returned,
        even if the input is invalid (i.e., the requirement does not match any of the choices)

        For AAISChatBackend, 3 additional arguments are required:

        - `prompt_template`: The template used to format the choices
        and the requirements to match against. There should be two slots
        in this template: slot 0 for the choices and slot 1 for the requirement.

        - `item_formatter`: A callable used to format each of the choices.
        The input to this callable is <index, item>, where <index>: `int` is the index (0-based)
        of the item among the choices, and item is the choice, in thinking language.

        - `separator`: the separator to insert between two choices.

        For example, if:

        - `prompt_template` == "There are several available APIs.
         Their functionalities are described as follows:

         {0}

         Now, the user has made an API request. The request is as follows:

         {1}

         Please output the index of the API that best matches the request.
         Output the index ONLY and NOTHING ELSE."
        - `item_formatter` == lambda index, item: f"API {index}: {item}"
        - `separator` == "\n"

        Then the generated prompt would be like this:

        "There are several available APIs. Their functionalities are described as follows:

        API 0: Text to image.

        API 1: Image to text.

        API 2: Web browser.

        Now, the user has made an API request. The request is as follows:

        I want to convert text to image.

        Please output the index of the API that best matches the request.
        Output the index ONLY and NOTHING ELSE."

        IMPORTANT NOTICE
        ----------------

        - Generic type `T` must be convertible to `int`. I.e., calling `T.astype(int)` must not throw.

        - Numbering of items: When prompting the AI backend, the indices of the items are assumed to be 0-based;
        The semantic meaning of returning -1 is that no item is selected, i.e., no item fulfills the "requirement".
        Please make sure to follow these guidelines when writing the prompt templates.
        """

        super().__init__()

        self._error_message: T = kwargs.get("error_message", None)

        if isinstance(backend, AAISChatAPI):
            self._backend = backend

            self._prompt_template: T = kwargs.get("prompt_template", None)
            self._item_formatter: callable = kwargs.get("item_formatter", None)
            self._separator: T = kwargs.get("separator", None)

            if self._prompt_template is None or self._item_formatter is None or self._separator is None:
                raise ValueError("prompt_template, item_formatter, and separator must be specified!")

        else:
            raise NotImplementedError(f"Backend {backend} is not supported!")

    async def call(self, inputs: Tuple[Collection[T], T]) -> AAISResult[int, AAISThinkingLanguageContent]:
        if isinstance(self._backend, AAISChatAPI):
            choices, requirement = inputs

            choices_block = self._separator.join(map(self._item_formatter, enumerate(choices)))
            prompt = self._prompt_template.format([choices_block, requirement])
            response = await self._backend.generateResponse([prompt])

            try:
                # The call result is considered successful no matter whether
                # a choice is selected or not
                selected_index = response.content.astype(int)

                if not (selected_index == -1 or (0 <= selected_index < len(choices))):
                    raise ValueError(f"Invalid index {selected_index} returned by the backend!")

                return AAISResult(
                    success=True,
                    value=selected_index,
                    errorMessage=None
                )

            except ValueError:
                return AAISResult(
                    success=False,
                    value=None,
                    errorMessage=self._error_message
                )
        else:
            raise NotImplementedError(f"Backend {self._backend} is not supported!")
