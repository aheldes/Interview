from aws_lambda_powertools.utilities.typing import LambdaContext
import pandas as pd
import datetime
from sqlalchemy import create_engine
import smart_open
import os
import numpy as np
from typing import Optional

ENDPOINT = os.environ['ENDPOINT']
PORT = os.environ['PORT']
USER = os.environ['USER']

REGION = os.environ['REGION']
DBNAME = os.environ['DBNAME']
DBPW = os.environ['PW']

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    fileHref = 'https://www.ema.europa.eu/sites/default/files/Medicines_output_european_public_assessment_reports.xlsx'
    try:
        with smart_open.open(fileHref, 'rb',buffering=0) as f:
            file = f
    except:
        return {
            'statusCode': 500,
            'body': 'Data was not loaded correctly.'
        }

    data = pd.read_excel(file, sheet_name=0, skiprows=8, engine="openpyxl")
    data = data.replace(np.nan, None)
    data['Date of refusal of marketing authorisation'] = data['Date of refusal of marketing authorisation'] \
        .astype(object) \
        .where(
            data['Date of refusal of marketing authorisation'].notnull(),
            None)
        
    data['First published'] = pd.to_datetime(data['First published'])
    data['Revision date'] = pd.to_datetime(data['Revision date'])
    data['Marketing authorisation date'] = pd.to_datetime(data['Marketing authorisation date'])

    if event['type'] == "daily":    
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        data = data[(data['Revision date'].dt.date == yesterday) | (data['First published'].dt.date == yesterday)]

    data = rename_columns(data)

    if data.shape[0] != 0:
        pc = PublishChanges()
        data.apply(lambda row: pc.commit_data(row), axis=1)
        pc.commit_and_close()

    return {
        'statusCode': 200,
        'body': {'number_of_updates': data.shape[0]}
    }

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        'Medicine name': 'Medicine_name',
        'Therapeutic area': 'Therapeutic_area',
        'International non-proprietary name (INN) / common name': 'International_non_proprietary_name',
        'Active substance': 'Active_substance',
        'Product number': 'Product_number',
        'Patient safety': 'Patient_safety',
        'Authorisation status': 'Authorisation_status',
        'ATC code': 'ATC_code',
        'Additional monitoring': 'Additional_monitoring',
        'Generic': 'Generic',
        'Biosimilar': 'Biosimilar',
        'Conditional approval': 'Conditional_approval',
        'Exceptional circumstances': 'Exceptional_circumstances',
        'Accelerated assessment': 'Accelerated_assessment',
        'Orphan medicine': 'Orphan_medicine',
        'Marketing authorisation date': 'Marketing_authorisation_date',
        'Date of refusal of marketing authorisation': 'Refusal_date',
        'Marketing authorisation holder/company name': 'Marketing_authorisation_name',
        'Human pharmacotherapeutic group': 'Human_pharmacotherapeutic_group',
        'Vet pharmacotherapeutic group': 'Vet_pharmacotherapeutic_group',
        'Date of opinion': 'Date_of_opinion',
        'Decision date': 'Decision_date',
        'Revision number': 'Revision_number',
        'Condition / indication': 'Condition_indication',
        'Species': 'Species',
        'ATCvet code': 'ATCvet_code',
        'First published': 'First_published',
        'Revision date': 'Revision_date',
        'URL': 'URL'})

class PublishChanges():
    def __init__(self) -> None:
        self._init_db()
        self.cursor.execute(
            'select Product_number, ID from MARKETING_AUTHORISATION')
        self.alreadyLoaded = self.cursor.fetchall()
        self.insert1, self.insert2, self.update = self._get_queries()
        

    def commit_data(self, row: pd.Series) -> None:
        data = row.tolist()
        product_number = data[5]
        
        exists = False
        id = None
        for loaded in self.alreadyLoaded:
             if product_number in loaded[0]:
                exists = True
                id = loaded[1]
                break
        if exists:
            update_sql = '''SET SQL_SAFE_UPDATES = 0;'''
            self.cursor.execute(update_sql)
            data_copy = data[:]
            data_copy.append(product_number)
            del data_copy[5]
            self.cursor.execute(self.update, tuple(data_copy))
        else:
            self.cursor.execute(self.insert1, tuple(data))
            id = self.cursor.lastrowid

        data.insert(0, id)
        self.cursor.execute(self.insert2, tuple(data))

    def _init_db(self) -> None:
        engine = create_engine("mysql+pymysql://" + USER + ":" + DBPW + "@" + ENDPOINT + "/" + DBNAME)
        self.connection = engine.raw_connection()
        self.cursor = self.connection.cursor()

    def _get_queries(self) -> tuple(str, str, str):
        def get_insert_queries(table: str,
            id_string: Optional[str] = '',
            parameters: Optional[int]=30) -> str:
            placeholders = ''.join('%s, ' * parameters)
            query = f'''Insert into {table} (
                {id_string}
                Category, 
                Medicine_name, 
                Therapeutic_area,
                International_non_proprietary_name, 
                Active_substance,
                Product_number,
                Patient_safety,
                Authorisation_status,
                ATC_code,
                Additional_monitoring,
                Generic,
                Biosimilar,
                Conditional_approval,
                Exceptional_circumstances,
                Accelerated_assessment,
                Orphan_medicine,
                Marketing_authorisation_date, 
                Refusal_date, 
                Marketing_authorisation_name, 
                Human_pharmacotherapeutic_group, 
                Vet_pharmacotherapeutic_group, 
                Date_of_opinion,
                Decision_date,
                Revision_number,
                Condition_indication,
                Species,
                ATCvet_code,
                First_published,
                Revision_date, 
                URL)
                VALUES ({placeholders[:-2]})'''
            return query

        def get_update_query() -> str:
            return '''Update MARKETING_AUTHORISATION SET
                Category = %s,  
                Medicine_name = %s, 
                Therapeutic_area = %s, 
                International_non_proprietary_name = %s, 
                Active_substance = %s, 
                Patient_safety = %s, 
                Authorisation_status = %s, 
                ATC_code = %s, 
                Additional_monitoring = %s, 
                Generic = %s, 
                Biosimilar = %s, 
                Conditional_approval = %s, 
                Exceptional_circumstances = %s, 
                Accelerated_assessment = %s, 
                Orphan_medicine = %s, 
                Marketing_authorisation_date = %s, 
                Refusal_date = %s, 
                Marketing_authorisation_name = %s, 
                Human_pharmacotherapeutic_group = %s, 
                Vet_pharmacotherapeutic_group = %s,  
                Date_of_opinion = %s, 
                Decision_date = %s, 
                Revision_number = %s, 
                Condition_indication = %s, 
                Species = %s, 
                ATCvet_code = %s, 
                First_published = %s, 
                Revision_date = %s, 
                URL = %s
                where Product_number like %s'''
        insert1 = get_insert_queries('MARKETING_AUTHORISATION')
        insert2 = get_insert_queries('MARKETING_AUTHORISATION_HISTORY', 'ID,', 31)
        update = get_update_query()
        return insert1, insert2, update
        
    def commit_and_close(self) -> None:
        self.cursor.close()
        self.connection.commit()
        self.connection.close()