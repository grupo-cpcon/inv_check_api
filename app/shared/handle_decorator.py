from fastapi import Request
from fastapi.routing import APIRoute
from starlette.routing import Match

def handle_decorator(decorator, request: Request):
    for route in request.app.routes:
        if isinstance(route, APIRoute):
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                endpoint_func = route.endpoint
                if getattr(endpoint_func, decorator, False):
                    return True
                return False