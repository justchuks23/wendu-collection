from rest_framework.response import Response
from rest_framework.views import exception_handler


def safe_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response
    return Response(
        {"detail": "An internal error occurred.", "code": "internal_error"},
        status=500,
    )
