from django.db import models

# Create your models here.
class Substance(models.Model):
    id = models.IntegerField(primary_key=True, db_column='ID')
    substance = models.CharField(db_column='Substance', max_length=255)

    class Meta:
        db_table = "SUBSTANCE"
        managed = False

    def __str__(self):
        return self.substance

class TherapeuticArea(models.Model):
    id = models.IntegerField(primary_key=True, db_column='ID')
    area = models.CharField(db_column='Area', max_length=255)

    class Meta:
        db_table = "THERAPEUTIC_AREA"
        managed = False

    def __str__(self):
        return self.area

class MarketingAuthorisation(models.Model):
    id = models.IntegerField(primary_key=True, db_column='ID')
    category = models.CharField(db_column='Category', max_length=255)
    medicine_name = models.CharField(db_column='Medicine_name', max_length=255)
    therapeutic_area = models.CharField(db_column='Therapeutic_area', max_length=255)
    international_non_proprietary_name = models.CharField(db_column='International_non_proprietary_name', max_length=255)
    active_substance = models.CharField(db_column='Active_substance', max_length=255)
    product_number = models.CharField(db_column='Product_number', max_length=255)
    patient_safety = models.BooleanField(db_column='Patient_safety')
    authorisation_status = models.CharField(db_column='Authorisation_status', max_length=255)
    ATC_code = models.CharField(db_column='ATC_code', max_length=255)
    additional_monitoring = models.BooleanField(db_column='Additional_monitoring')
    generic = models.BooleanField(db_column='Generic')
    biosimilar = models.BooleanField(db_column='Biosimilar')
    conditional_approval = models.BooleanField(db_column='Conditional_approval')
    exceptional_circumstances = models.BooleanField(db_column='Exceptional_circumstances')
    accelerated_assessment = models.BooleanField(db_column='Accelerated_assessment')
    orphan_medicine = models.BooleanField(db_column='Orphan_medicine')
    marketing_authorisation_date = models.DateField(db_column='Marketing_authorisation_date')
    refusal_date = models.DateField(db_column='Refusal_date')
    marketing_authorisation_name = models.CharField(db_column='Marketing_authorisation_name', max_length=255)
    human_pharmacotherapeutic_group = models.CharField(db_column='Human_pharmacotherapeutic_group', max_length=255)
    vet_pharmacotherapeutic_group = models.CharField(db_column='Vet_pharmacotherapeutic_group', max_length=255)
    date_of_opinion = models.DateField(db_column='Date_of_opinion')
    decision_date = models.DateField(db_column='Decision_date')
    revision_number = models.IntegerField(db_column='Revision_number')
    condition_indication = models.CharField(db_column='Condition_indication', max_length=255)
    species = models.CharField(db_column='Species', max_length=255)
    ATCvet_code = models.CharField(db_column='ATCvet_code', max_length=255)
    first_published = models.DateField(db_column='First_published')
    revision_date = models.DateField(db_column='Revision_date')
    url = models.CharField(db_column='URL', max_length=255)

    class Meta:
        db_table = "MARKETING_AUTHORISATION"
        managed = False

    def __str__(self):
        return self.medicine_name

class MatchesPDF(models.Model):
    id = models.IntegerField(primary_key=True, db_column='ID')
    agency = models.CharField(db_column='Agency', max_length=255)
    name = models.CharField(db_column='Name', max_length=255)
    pdf_name = models.CharField(db_column='PDF_Name', max_length=255)
    date = models.DateField(db_column='Date')
    last_update_date = models.DateField(db_column='Last_Update_Date')

    class Meta:
        db_table = "MATCHES_PDF"
        managed = False

    def __str__(self):
        return self.name