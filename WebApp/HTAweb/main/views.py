from django.http import HttpResponseNotFound, HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import *
from .new_model import *
from api.models import MatchesPDF, MarketingAuthorisation
import boto3
import json
from copy import deepcopy
from .keys import access_key, secret_key

def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'main/home.html')

def search_page(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('main:home')
        
    if request.method == "POST":
        selected = request.POST.get('choice', False)
        searched = request.POST.get('searched', False)

        searchOBJ = ParseSearchedValue(searched)
        ID = searchOBJ.get_ID()

        if ID is not None:
            return redirect('main:substance', id=ID)

        search_page = True
        data = my_custom_sql(selected, searched)
    else:
        data = my_custom_sql()
        search_page = False
    page_number = int(request.GET.get('page', 1))
    per_page = 20
    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request,'main/search.html', {'paginator': paginator, 'page_obj':page_obj, 'searched': search_page})

def substance(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return render(request, 'main/home.html')
    else:
        substance = SubstanceData(id)
        medicines = MarketingAuthorisation.objects.using('analytics').filter(active_substance=substance.name)
        areas, pdf = substance.get_data()
        pdfs = []
        for file in pdf:
            new_values = list(deepcopy(file))
            pdf_name = file[2]

            name = f"{pdf_name[pdf_name.index('/')+1:pdf_name.index('.pdf')]}.txt"
            bucket_name_pdf = 'api-ai-text'
            try:
                client = boto3.client('s3', aws_access_key_id = access_key, aws_secret_access_key = secret_key)
                fileobj = client.get_object(
                    Bucket=bucket_name_pdf,
                    Key= name
                ) 
                new_values.append(json.load(fileobj['Body']))
                pdfs.append(tuple(new_values))
            except:
                pass

        return render(
            request,'main/substance.html',
            {'medicines': medicines,
            'areas': areas,
            'pdfs': tuple(pdfs),
            'name': substance.name})

def pdf_result(request: HttpRequest, id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return render(request, 'main/home.html')
    else:
        pdf = MatchesPDF.objects.using('analytics').filter(id=id).first()
        name = f"{pdf.pdf_name[pdf.pdf_name.index('/')+1:pdf.pdf_name.index('.pdf')]}.txt"
        
        bucket_name_text = 'api-ai-text'
        client = boto3.client('s3', aws_access_key_id = access_key, aws_secret_access_key = secret_key)
        fileobj = client.get_object(
            Bucket=bucket_name_text,
            Key= name
        ) 
        file = fileobj['Body']

        raw_nlp = client.generate_presigned_url('get_object',
            Params={'Bucket': bucket_name_text,
                    'Key': name},
            ExpiresIn=180)

        bucket_name_pdf = f"{pdf.agency.lower()}pdf"
        key = pdf.pdf_name

        raw_pdf = client.generate_presigned_url('get_object',
            Params={'Bucket': bucket_name_pdf,
                    'Key': key},
            ExpiresIn=180)
        
        return render(
            request,'main/pdf_result.html',
            {'pdf': pdf,
            'raw_pdf': raw_pdf,
            'raw_NLP': raw_nlp,
            'AI': json.load(file)})

def medicine_result(request: HttpRequest, id: int) -> HttpResponse:
    medicine = MarketingAuthorisation.objects.using('analytics').filter(id=id).first()
    return render(request, 'main/medicine.html', {'medicine': medicine})

def error_404(request: HttpRequest, exceptions: Exception) -> HttpResponseNotFound:
    return HttpResponseNotFound('main/404.html')

def error_500(request: HttpRequest) -> HttpResponseNotFound:
    return render(request, 'main/500.html')