import pandas as pd
from sqlalchemy import create_engine
import os
from datetime import datetime, timedelta
from typing import Tuple
from aws_lambda_powertools.utilities.typing import LambdaContext

ENDPOINT = os.environ['ENDPOINT']
USER = os.environ['USER']
DBPW = os.environ['PW']
DBNAME = os.environ['DBNAME']

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    parsing_obj = Parsing(event)

    emaDF = parsing_obj.get_initial_data()

    substance_area_raw_df = parsing_obj.parse_raw_data(emaDF)

    if parsing_obj.updates:
        substanceDF, areaDF = parsing_obj.get_additional_data()

        parsing_obj.parse_substance_data(substance_area_raw_df, substanceDF)
          
        parsing_obj.parse_area_data(substance_area_raw_df, areaDF) 
        
        parsing_obj.parse_substance_area_data(substance_area_raw_df, substanceDF, areaDF)

        parsing_obj.close_con()

        return {
            'statusCode': 200,
            'body': {
                'number_of_updates_substances': parsing_obj.loaded_substances,
                'number_of_updates_areas': parsing_obj.loaded_areas,
                'number_of_updates_substance_area': parsing_obj.loaded_substance_areas
                }
        }
    return {
            'statusCode': 200,
            'body': {'Informative message': 'No updates found'}
        }


class Parsing():
    def __init__(self, event: dict) -> None:
        self.event = event
        self._initiate_db_connection()
        
    def _initiate_db_connection(self) -> None:
        self.engine = create_engine("mysql+pymysql://" + USER + ":" + DBPW + "@" + ENDPOINT + "/" + DBNAME)
        self.connection = self.engine.raw_connection()
        self.cursor = self.connection.cursor()

    def get_initial_data(self) -> pd.DataFrame:
        string = f"""where Revision_date like '{(datetime.now() - timedelta(1)).strftime("%Y-%m-%d")}'""" if self.event['type'] == 'daily' else ''
        sql = f"""Select * from MARKETING_AUTHORISATION {string}"""
        return pd.read_sql(sql, self.engine)

    def parse_raw_data(self, emaDF: pd.DataFrame) -> pd.DataFrame:
        self.updates = True

        if emaDF.shape[0] == 0:
            self.updates = False
            return None

        hash_map = {}
        for row in emaDF[['ID', 'Active_substance', 'Therapeutic_area']].itertuples():
            if row[2] != None and row[3] != None:
                for substance in row[2].split(", "):
                    exists = False
                    for area in row[3].split("; "):
                        if not exists:
                            if substance.capitalize() not in hash_map:
                                hash_map[substance.capitalize()] = {'ID': set([]), 'Therapeturic_Area': set([])}
                            exists = True
                        hash_map[substance.capitalize()]['Therapeturic_Area'].add(area.strip())
                        hash_map[substance.capitalize()]['ID'].add(row[1])

        data = []
        for key, value in hash_map.items():
            for area in value['Therapeturic_Area']:
                for id in value['ID']:
                    data.append([id, key, area])

        return pd.DataFrame(data, columns=['ID', 'Substance', 'Therapeutic_area'])

    def get_additional_data(self) -> Tuple(pd.DataFrame, pd.DataFrame):
        return pd.read_sql("Select * from SUBSTANCE", self.engine), \
            pd.read_sql("Select * from THERAPEUTIC_AREA",self.engine)

    def parse_substance_data(self, df: pd.DataFrame, substanceDF: pd.DataFrame) -> None:
        unique_substanceDF = pd.Series(df.Substance.unique())
        unique_substanceDF = unique_substanceDF[~unique_substanceDF.str.contains("A/victoria/2570/2019")]
        if self.event['type'] == "daily":
            unique_substanceDF = unique_substanceDF[~unique_substanceDF.isin(substanceDF.Substance)]

        values_substance = tuple(unique_substanceDF)
        self.loaded_substances = len(values_substance)
        if self.loaded_substances != 0:
            query = '''Insert into SUBSTANCE (Substance) VALUES'''
            placeholders = '(%s),' * self.loaded_substances
            query += placeholders
            self.cursor.execute(query[:-1], values_substance)
            self.connection.commit()

    def parse_area_data(self, df: pd.DataFrame, areaDF: pd.DataFrame) -> None:
        unique_areaDF = pd.Series(df.Therapeutic_area.unique())
        if self.event['type'] == "daily":
            unique_areaDF = unique_areaDF[~unique_areaDF.isin(areaDF.Area)]

        values_area = tuple(unique_areaDF)
        self.loaded_areas = len(values_area)
        if self.loaded_areas  != 0:
            query = '''Insert into THERAPEUTIC_AREA (Area) VALUES'''
            placeholders = '(%s),' * self.loaded_areas 
            query += placeholders
            self.cursor.execute(query[:-1], values_area)
            self.connection.commit()

    def parse_substance_area_data(self,
        dailyDF: pd.DataFrame,
        substanceDF: pd.DataFrame,
        areaDF: pd.DataFrame) -> None:
        if self.loaded_substances != 0 or self.loaded_areas  != 0:
            substanceDF = pd.read_sql("Select * from SUBSTANCE", self.engine)
            areaDF = pd.read_sql("Select * from THERAPEUTIC_AREA", self.engine)

        substance_areaDF = dailyDF.merge(substanceDF, on='Substance', validate="many_to_one")
        dailyDF = substance_areaDF.merge(areaDF, left_on='Therapeutic_area', right_on='Area', validate="many_to_one")

        dailyDF = dailyDF[['ID_x', 'ID_y', 'ID']].rename(columns={
            'ID_x': 'Parent_ID',
            'ID_y': 'Substance_ID',
            'ID': 'Area_ID'})
        substance_areaDF = pd.read_sql("Select * from SUBSTANCE_AREA", self.engine, index_col='ID')

        dailyDF = dailyDF.set_index(['Parent_ID','Substance_ID', 'Area_ID'])
        substance_areaDF = substance_areaDF.set_index(['Parent_ID','Substance_ID', 'Area_ID'])

        dailyDF = dailyDF[~dailyDF.index.isin(substance_areaDF.index)].reset_index()

        self.loaded_substance_areas = dailyDF.shape[0]
        self.df = dailyDF

        if self.loaded_substance_areas != 0:
            values_substance_area = tuple(dailyDF[['Parent_ID', 'Substance_ID', 'Area_ID']].values.tolist())
            query = '''Insert into SUBSTANCE_AREA (Parent_ID, Substance_ID, Area_ID) VALUES '''
            placeholders = '(%s, %s, %s),' * len(values_substance_area)
            query += placeholders
            self.cursor.execute(query[:-1], tuple([x for xs in values_substance_area for x in xs]))
            self.connection.commit()
    
    def close_con(self) -> None:
        self.cursor.close()
        self.connection.close()