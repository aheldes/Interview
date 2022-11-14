from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Substance, TherapeuticArea, MarketingAuthorisation
from .serializers import SubstanceSerializer, TherapeuticAreaSerializer, MarketingAuthorisationSerializer

class SubstanceListApiView(ListAPIView):
    queryset = Substance.objects.using('analytics').all()
    serializer_class = SubstanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    #pagination_class = PageNumberPagination


class SubstanceDetailApiView(RetrieveAPIView):
    queryset = Substance.objects.using('analytics').all()
    serializer_class = SubstanceSerializer


class TherapeuticAreaListApiView(ListAPIView):
    queryset = TherapeuticArea.objects.using('analytics').all()
    serializer_class = TherapeuticAreaSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination


class TherapeuticAreaDetailApiView(RetrieveAPIView):
    queryset = TherapeuticArea.objects.using('analytics').all()
    serializer_class = TherapeuticAreaSerializer


class MarketingAuthorisationListApiView(ListAPIView):
    queryset = MarketingAuthorisation.objects.using('analytics').all()
    serializer_class = MarketingAuthorisationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination


class MarketingAuthorisationDetailApiView(RetrieveAPIView):
    queryset = MarketingAuthorisation.objects.using('analytics').all()
    serializer_class = MarketingAuthorisationSerializer