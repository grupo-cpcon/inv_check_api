def no_tenant_required(func):
    func.no_tenant_required = True
    return func
