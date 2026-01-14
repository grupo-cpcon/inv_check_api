from fastapi import Request
from fastapi.routing import APIRoute
from starlette.routing import Match
from functools import lru_cache


@lru_cache
def route_has_decorator(endpoint, decorator: str) -> bool:
    return bool(getattr(endpoint, decorator, False))


def handle_decorator(decorator: str, request: Request) -> bool:
    for route in request.app.routes:
        if isinstance(route, APIRoute):
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                endpoint_func = route.endpoint
                if getattr(endpoint_func, decorator, False):
                    return True
    return False