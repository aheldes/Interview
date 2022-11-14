
from django.urls import path
from .views import (
    SubstanceListApiView,
    SubstanceDetailApiView,
    TherapeuticAreaListApiView,
    TherapeuticAreaDetailApiView,
    MarketingAuthorisationListApiView,
    MarketingAuthorisationDetailApiView,
)

app_name = 'api'

urlpatterns = [
    path('substances/', SubstanceListApiView.as_view(), name='substance'),
    path('substances/<pk>/', SubstanceDetailApiView.as_view()),
    path('therapeutic-area/', TherapeuticAreaListApiView.as_view()),
    path('therapeutic-area/<pk>/', TherapeuticAreaDetailApiView.as_view()),
    path('marketing-authorisation/', MarketingAuthorisationListApiView.as_view()),
    path('marketing-authorisation/<pk>/', MarketingAuthorisationDetailApiView.as_view()),
]