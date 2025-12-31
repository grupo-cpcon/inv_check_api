from fastapi import FastAPI

def startup_events(app: FastAPI):
    # @app.on_event("startup")
    # async def startup_db_client():
    #     await connect_to_mongo()

    @app.on_event("startup")
    async def collect_public_endpoints():
        app.state.public_endpoints = set()
        for route in app.routes:
            if hasattr(route, "endpoint"):
                endpoint_func = route.endpoint
                if getattr(endpoint_func, "no_auth", False):
                    app.state.public_endpoints.add(endpoint_func)

    @app.on_event("startup")
    async def collect_no_tenant_required_endpoints():
        app.state.no_tenant_required_endpoints = set()
        for route in app.routes:
            if hasattr(route, "endpoint"):
                endpoint_func = route.endpoint
                if getattr(endpoint_func, "no_tenant_required", False):
                    app.state.no_tenant_required_endpoints.add(endpoint_func)
""" def shutdown_events(app: FastAPI):
    @app.on_event("shutdown")
    async def shutdown_db_client():
        await close_mongo_connection() """