from tokenize import String
from django.db import connections
from typing import List, Tuple

def my_custom_sql(filterType:String = None, filterValue:String = None) -> List(List):
    with connections['analytics'].cursor() as cursor:
        where = ''
        if filterType != None:
            field = 's.Substance' if filterType == 'active_substance' else 'ma.Medicine_name'
            where = f"""where {field} like '%{filterValue}%' or {field} like '{filterValue}%' or {field} like '%{filterValue}'"""

        sql = f'''SELECT  
                    s.ID, 
                    s.Substance, 
                    COUNT(DISTINCT ma.Medicine_name) AS Medicine_Products, 
                    COUNT(DISTINCT ms.ID_PDF)  AS PDF_Matches,
                    MIN(ma.Revision_date) AS First_Auth_Date
                FROM SUBSTANCE s
                LEFT JOIN MARKETING_AUTHORISATION ma ON s.Substance = ma.Active_substance
                LEFT JOIN MATCHES_SUBSTANCES ms ON s.ID = ms.ID_Substance 
                {where} GROUP BY s.ID 
                ORDER BY Medicine_Products DESC;'''

        if filterType != None:
            cursor.execute(sql)
        else: cursor.execute(sql)  
           
        row = cursor.fetchall()

    return row

class ParseSearchedValue():
    def __init__(self, substance: str) -> None:
        self.substance = substance
        
    def get_ID(self) -> int:
        with connections['analytics'].cursor() as cursor:
            sql = '''
                    SELECT ID
                    FROM SUBSTANCE
                    where Substance = %s'''
            cursor.execute(sql, (self.substance,))     
            row = cursor.fetchall()
            return row[0][0] if len(row) != 0 else None

class SubstanceData():
    def __init__(self, id: int) -> None:
        self.id = id
        self.connection = connections['analytics']
        self.cursor = self.connection.cursor()
        self.name = self._get_name()

    def _get_name(self) -> str:
        sql = 'select Substance from SUBSTANCE where ID = %s'
        self.cursor.execute(sql, (self.id,))
        return self.cursor.fetchall()[0][0]

    def get_data(self) -> Tuple(List(List), List(List)):
        sql1, sql2 = self._get_queries()

        # self.cursor.execute(sql1,(self.name,))     
        # results1 = self.cursor.fetchall()

        self.cursor.execute(sql1, (self.id,))     
        results1 = self.cursor.fetchall()

        self.cursor.execute(sql2, (self.id,))     
        results2 = self.cursor.fetchall()

        return results1, results2

    def _get_queries(self) -> Tuple(str, str):
        query1 = '''select distinct 
            ma.ID_PDF, ta.Area 
            from MATCHES_AREAS ma
            join THERAPEUTIC_AREA ta on ta.ID = ma.ID_Area
            join MATCHES_PDF mp on mp.ID = ma.ID_PDF
            join SUBSTANCE_AREA sa on sa.Substance_ID = %s and sa.Area_ID = ma.ID_Area
            join MATCHES_SUBSTANCES ms on ms.ID_Substance = sa.Substance_ID and ms.ID_PDF = ma.ID_PDF'''
        query2 = '''SELECT 
                mp.ID,
                mp.Name,
                mp.PDF_Name,
                mp.Agency,
                mp.Last_Update_Date
                FROM MATCHES_SUBSTANCES ms
                JOIN MATCHES_PDF mp on mp.ID = ms.ID_PDF
                WHERE ms.ID_Substance = %s
                group by mp.ID;'''
        return query1, query2
