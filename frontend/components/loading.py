from contextlib import contextmanager
from typing import Callable, TypeVar

import streamlit as st

T = TypeVar("T")


def with_loading(message: str = "Processing…") -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            with st.spinner(message):
                return func(*args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def loading_context(message: str = "Processing…"):
    with st.spinner(message):
        yield
