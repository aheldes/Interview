from rest_framework import serializers
from .models import Substance, TherapeuticArea, MarketingAuthorisation

class SubstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Substance
        fields = ['id', 'substance']

class TherapeuticAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapeuticArea
        fields = ['id', 'area']

class MarketingAuthorisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingAuthorisation
        fields = [
            'id',
            'category',
            'medicine_name',
            'therapeutic_area',
            'international_non_proprietary_name',
            'active_substance',
            'product_number',
            'patient_safety',
            'authorisation_status',
            'ATC_code',
            'additional_monitoring',
            'generic',
            'biosimilar',
            'conditional_approval',
            'exceptional_circumstances',
            'accelerated_assessment',
            'orphan_medicine',
            'marketing_authorisation_date',
            'refusal_date',
            'marketing_authorisation_name',
            'human_pharmacotherapeutic_group', 
            'vet_pharmacotherapeutic_group',
            'date_of_opinion',
            'decision_date',
            'revision_number',
            'condition_indication',
            'species',
            'ATCvet_code',
            'first_published',
            'revision_date',
            'url'
        ]

