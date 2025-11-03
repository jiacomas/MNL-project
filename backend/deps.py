from __future__ import annotations


# Minimal stub for local development.
# TODO: Replace with real auth (JWT/session) later.
def get_current_user_id() -> str:
    '''Return a fixed user id for local testing.'''
    return "demo_user"
