def make_errors(field_loc, field_name, msg, wrap = False):
    base = {
        'loc': [field_loc, field_name],
        'msg': msg
    }
    if wrap:
        return {"detail": base}
    return base
