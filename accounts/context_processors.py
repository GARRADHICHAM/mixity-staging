def mail_validated(request):
    if not request.user.is_authenticated:
        validated = True
    else:
        validated = request.user.is_confirmed
    return {"mail_validated": validated}
