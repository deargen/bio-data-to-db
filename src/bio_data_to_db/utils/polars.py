from collections.abc import Callable
from typing import Any

import tqdm


def w_pbar(pbar: tqdm.std.tqdm, func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Apply progress bar when using `map_elements` in `polars`.

    Examples:
        >>> with tqdm(total=len(df)) as pbar:  # doctest: +SKIP
        ...     df = df.with_columns(
        ...         pl.col("in_col")
        ...         .map_elements(w_pbar(pbar, lambda x: x + 1), return_dtype=pl.Int64)
        ...     )

    Reference:
        - https://stackoverflow.com/questions/75550124/python-polars-how-to-add-a-progress-bars-to-apply-loops
    """

    def foo(*args, **kwargs):
        pbar.update(1)
        return func(*args, **kwargs)

    return foo
