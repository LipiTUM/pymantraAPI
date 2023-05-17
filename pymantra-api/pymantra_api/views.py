from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.decorators import api_view


@api_view(['GET'])
def verify_connection(request: Request) -> HttpResponse:
    return HttpResponse("pymantradb connection verified")
