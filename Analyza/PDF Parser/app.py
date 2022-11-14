# Built in libraries
import copy
from datetime import datetime
from io import BytesIO
import os

# Other libraries
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
import fitz
import mysql.connector

ACCESS_KEY = os.environ['ACCESS_KEY']
SECRET_KEY = os.environ['secret_key']

ENDPOINT = os.environ['ENDPOINT']
PORT = os.environ['PORT']
USER = os.environ['USER']
PW = os.environ['PW']
REGION = os.environ['REGION']
DBNAME = os.environ['DBNAME']

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    connection = get_connection()
    mycursor = connection.cursor()

    indication_name, entry_terms, substences = DataForMatching(mycursor).get_data()

    s3 = boto3.resource('s3')
    bucket_name_pdf = 'nicepdf'
    bucket_pdf = s3.Bucket(bucket_name_pdf)

    client = boto3.client('s3', aws_access_key_id = ACCESS_KEY, aws_secret_access_key = SECRET_KEY)

    today = datetime.now().date()
    number_of_updates = 0
    for obj in bucket_pdf.objects.all():
        if event['type'] == "daily":
            if obj.last_modified.date() != today:
                continue
        number_of_updates += 1
        pdfParser = PDFParser(obj, client, 'Nice', mycursor, connection)
        pdfParser.match_terms(indication_name, 'indication')
        pdfParser.match_terms(entry_terms, 'entry_term')
        pdfParser.match_terms(substences, 'substances')
        pdfParser.load_to_sql()

    mycursor.close()
    connection.commit()
    connection.close()

    return {
        'statusCode': 200,
        'body': {'number_of_updates': number_of_updates}
    }

def get_connection() -> mysql.connector.connection.MySQLConnection:
    return mysql.connector.connect(
        host=ENDPOINT, database=DBNAME, user=USER, password=PW)

class DataForMatching():
    def __init__(self, cursor: mysql.connector.cursor.MySQLCursor) -> None:
        self.cursor = cursor

    def get_data(self) -> tuple(list, list, list):
        queryM, queryMT, querySA = self._get_queries()

        self.cursor.execute(queryM)
        indication_name = [[i[0].split(), i[1]] for i in self.cursor.fetchall()]

        self.cursor.execute(queryMT)
        entry_terms = [[i[0].split(), i[1], i[2]] for i in self.cursor.fetchall()]

        self.cursor.execute(querySA)
        substences = [[i[0].split(), i[1]] for i in self.cursor.fetchall()]

        return indication_name, entry_terms, substences

    def _get_queries(self) -> tuple(str, str, str):
        queryM = 'SELECT distinct Indication_name, ID FROM MESH'
        queryMT = 'SELECT distinct Entry_Term, ID, ID_Parent FROM MESH_TERMS'
        querySA = 'SELECT Substance, ID FROM SUBSTANCE'
        return queryM, queryMT, querySA

class PDFParser():

    def __init__(self,
        obj: boto3.object,
        client: boto3.client,
        agency: str,
        cursor: mysql.connector.cursor.MySQLCursor,
        connection: mysql.connector.connection.MySQLConnection) -> None:

        self.pdf_name = obj.key
        self._parseName(obj.key[obj.key.index('/')+1:obj.key.index('-pdf')])
        self.last_update_date = obj.last_modified.date()
        self.doc = fitz.open(stream=BytesIO(obj.get()['Body'].read()))
        self.agency = agency
        self.found = {}
        self.result = []
        self.s3_client = client
        self.cursor = cursor
        self.connection = connection
        self._parsePages()

    def match_terms(self, names: list, type: str) -> None:
        def is_close_by(name, index):
            searched_index = self.hash_map[name[index]]
            indexes_before = self.found[name[index-1]]
            if len([si for si in searched_index for ib in indexes_before if si-ib==1]):
                return True

        hash_map = self.first_page if type == 'substances' else self.hash_map

        for obj in names:
            id = obj[1]
            name = obj[0]
            parent = obj[2] if len(obj) == 3 else None
            number_of_words = len(name) - 1
            for index, word in enumerate(name):
                    if index == 0:
                        if word in hash_map:
                            if word not in self.found:
                                self.found[word] = hash_map[word]
                            if index == number_of_words:
                                self._create_match(id, word, type, parent)
                            continue
                        break
                    else:
                        if word in hash_map and is_close_by(name, index):
                            if word not in self.found:
                                self.found[word] = hash_map[word]
                            if index == number_of_words:
                                self._create_match(id, word, type, parent) 
                            continue
                        break      

    def load_to_sql(self) -> None:
        sql_find, sql_match, sql_match_words_delete, sql_match_words, sql_match_words_text_delete, sql_match_words_text, \
            sql_substance_delete, sql_substance = self._get_sql_statements()

        self.cursor.execute(sql_find, params=(self.name,))
        
        data = self.cursor.fetchall()

        exists = True if len(data) != 0 else False
        
        if exists:
            update_sql = '''SET SQL_SAFE_UPDATES = 0;'''
            self.cursor.execute(update_sql)
            sql_match = '''Update MATCHES_PDF SET Date = %s, Last_Update_Date = %s where name like %s'''
            values_match = (self.date, self.last_update_date, self.name)  
        else:
            values_match = (self.agency, self.name, self.pdf_name, self.date, self.last_update_date)

        self.cursor.execute(sql_match, values_match)

        last_match_ID = data[0][0] if exists else self._get_last_loaded_ID() 
        if exists:
            self.cursor.execute(sql_match_words_text_delete, params=(last_match_ID,))
            self.cursor.execute(sql_match_words_delete, params=(last_match_ID,))

            self.cursor.execute(sql_substance_delete, params=(last_match_ID,))

        for match in self.result:
            if match['substances'] == False:
                values_match_words = (
                    last_match_ID,
                    match['id'],
                    match['match'],
                    match['synonym'],
                    match['parent'])
                self.cursor.execute(sql_match_words, values_match_words)

                last_match_words_ID = self._get_last_loaded_ID()
                
                for text in match['text']:
                    values_match_words_text = (
                        last_match_words_ID,
                        text
                    )
                    self.cursor.execute(sql_match_words_text, values_match_words_text)
            else:
                values_substance = (
                    last_match_ID,
                    match['id'],
                    match['match'])
                self.cursor.execute(sql_substance, values_substance)

    def _get_sql_statements(self) -> tuple(str, str, str, str, str, str, str, str):
        sql = """SELECT ID from MATCHES_PDF where Name = %s"""
        sql1 = '''
            INSERT INTO MATCHES_PDF (Agency, Name, PDF_Name, Date, Last_Update_Date) 
            VALUES (%s, %s, %s, %s, %s)'''
        sql2 = "DELETE FROM MATCHES WHERE ID_PDF = %s"
        sql3 = '''
            INSERT INTO MATCHES (ID_PDF, Word_ID, Word_Text, Word_Syn, Parent_of_Syn) 
            VALUES (%s, %s, %s, %s, %s)
        '''
        sql4 = "DELETE FROM MATCHES_TEXT WHERE ID_Match IN (SELECT ID FROM MATCHES WHERE ID_PDF = %s)"
        sql5 = '''
            INSERT INTO MATCHES_TEXT (ID_Match, Text) 
            VALUES (%s, %s)
        '''
        sql6 = "DELETE FROM MATCHES_SUBSTANCES WHERE ID_PDF = %s"
        sql7 = '''
            INSERT INTO MATCHES_SUBSTANCES (ID_PDF, ID_Substance, Substance) 
            VALUES (%s, %s, %s)
        '''
        return sql, sql1, sql2, sql3, sql4, sql5, sql6, sql7

    def _get_last_loaded_ID(self) -> int:
        return self.cursor.lastrowid

    def _create_match(self, id: int, word: str, type: str, parent) -> None:
        synonym = False
        substance = False

        if type == 'entry_term':
            synonym = True

        near_by_text = []
        
        if type =='substances':
            substance = True
        else:
            for index in self.found[word]:
                spam = 20
                start = index-spam if index-spam >= 0 else 0
                end = index+spam if index+spam <= len(self.words_list) else len(self.words_list)                                

                near_by_text.append(' '.join(self.words_list[start:end]))
            
        parent = parent
        self.result.append({'match': word,
            'id': id,
            'synonym': synonym,
            'parent': parent,
            'substances': substance,
            'text': near_by_text})

    def _parseName(self, name: str) -> None:
        self.name = ' '.join(name.split('-')).capitalize()

    def _parsePages(self) -> None:
        text = ""
        words_list = []
        accumulative_index = 0

        self.hash_map = {}

        for index, page in enumerate(self.doc):
            page_text = page.get_text()
            page_text = page_text.replace('\n', '')
            
            if '...................' not in page_text:
                text += page_text

                words = page_text.split(" ")
                words_list.extend(words)
                
                for indexw, word in enumerate(words):
                    if word in self.hash_map:
                        self.hash_map[word].append(indexw+accumulative_index)
                    else:
                        self.hash_map[word] = [indexw+accumulative_index]

                if index == 0:
                    self.first_page = copy.deepcopy(self.hash_map)
                    published_index = words.index("Published:") if 'Published:' in words else False
                    if published_index:
                        date = f'{words[published_index+1]}/{words[published_index+2]}/{words[published_index+3]}'
                        self.date = datetime.strptime(date, '%d/%B/%Y').strftime('%Y-%m-%d')
                    else: self.date = None

                accumulative_index += len(words) 
    
        self.text = text
        self.words_list = words_list
        self.s3_client.put_object(Body=self.text, Bucket='pdf-text-output', Key=f'{self.agency}/{self.name}.txt')