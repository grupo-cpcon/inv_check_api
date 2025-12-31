def no_auth(func):
    func.no_auth = True
    return func
