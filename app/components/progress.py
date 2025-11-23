import streamlit as st
from contextlib import contextmanager

@contextmanager
def step(msg: str):
    with st.spinner(msg):
        yield
