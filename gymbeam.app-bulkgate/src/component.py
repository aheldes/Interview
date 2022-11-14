"""
Template Component main class.

"""
import csv
from dataclasses import dataclass
from datetime import datetime
import logging
import pandas as pd
import requests
import sys

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException

# credentials variables
KEY_CREDENTIALS = 'credentials'
KEY_CREDENTIALS_APPLICATION_ID = '#application_id'
KEY_CREDENTIALS_APPLICATION_TOKEN = '#application_token'

# settings variables
KEY_SETTINGS = 'settings'
KEY_SETTINGS_SENDER_ID = 'sender_id'
KEY_SETTINGS_MESSAGE_TYPE = 'message_type'
KEY_SETTINGS_VIBER = 'viber'
KEY_SETTINGS_VIBER_SENDER = 'viber_sender'

# set urls
PROMOTIONAL_URL = "https://portal.bulkgate.com/api/2.0/advanced/promotional"
TRANSACTIONAL_URL = "https://portal.bulkgate.com/api/2.0/advanced/transactional"


@dataclass
class Credentials:
    """
    Credentials dataclass.
    """
    application_id: str
    application_token: str


@dataclass
class Settings:
    """
    Settings dataclass.
    """
    sender_id: str
    message_type: str
    viber: bool
    viber_sender: str


class Component(ComponentBase):
    """
        Extends base class for general Python components. Initializes the CommonInterface
        and performs configuration validation.

        For easier debugging the data folder is picked up by default from `../data` path,
        relative to working directory.

        If `debug` parameter is present in the `config.json`, the default logger is set to verbose DEBUG mode.
    """

    def __init__(self) -> None:
        super().__init__()

    def run(self):
        """
        Main execution code
        """

        # Parse credentials
        _credentials_object = self._parse_credentials_parameters()
        _settings_object = self._parse_settings_parameters()

        # Parse table
        _data_in = self._parse_table()

        # Get url and body
        _url = self._get_url(_settings_object)
        _body = self._get_body(_credentials_object, _settings_object)

        # Send messages
        self._send_messages(_url, _body, _data_in)

        # Close files and manifes data
        self._close_and_manifest_files()

    def _parse_credentials_parameters(self) -> Credentials:
        """
        Parses credentials parameters from the configuration.
        """

        # Get credentials
        credentials = self.configuration.parameters.get(KEY_CREDENTIALS, {})
        if credentials == {}:
            logging.exception("Credentials configuration not specified.")
            sys.exit(1)

        try:
            # Set credentials object
            credentials_obj = Credentials(
                credentials[KEY_CREDENTIALS_APPLICATION_ID],
                credentials[KEY_CREDENTIALS_APPLICATION_TOKEN]
                )
        except KeyError as e:
            logging.exception(f"Missing mandatory field {e} in credentials.")
            sys.exit(1)

        return credentials_obj

    def _parse_settings_parameters(self) -> Settings:
        """
        Parses settings parameters from the configuration.
        """

        # Get settings
        settings = self.configuration.parameters.get(KEY_SETTINGS, {})
        if settings == {}:
            logging.exception("Settings configuration not specified.")
            sys.exit(1)

        try:
            # Set settings object
            settings_obj = Settings(
                settings[KEY_SETTINGS_SENDER_ID],
                settings[KEY_SETTINGS_MESSAGE_TYPE],
                settings[KEY_SETTINGS_VIBER],
                settings[KEY_SETTINGS_VIBER_SENDER]
                )

            # Validate settings
            if settings_obj.viber and settings_obj.viber_sender == '':
                logging.exception(
                    f"Missing mandatory field {KEY_SETTINGS_VIBER_SENDER} in settings. "
                    f"Please specify {KEY_SETTINGS_VIBER_SENDER} for Viber."
                    )
                sys.exit(1)

        except KeyError as e:
            logging.exception(f"Missing mandatory field {e} in settings.")
            sys.exit(1)

        return settings_obj

    def _parse_table(self) -> pd.DataFrame:
        """
        Parses the data table.
        """

        # Get tables configuration
        in_tables = self.configuration.tables_input_mapping

        if len(in_tables) == 0:
            logging.exception('There is no table specified on the input mapping! You must provide one input table!')
            sys.exit(1)
        elif len(in_tables) > 1:
            logging.exception(
                'There is more than one table specified on the input mapping! You must provide one input table!')
            sys.exit(1)

        # Get table
        table = in_tables[0]

        # Get table data
        logging.info(f'Processing input table: {table["destination"]}')
        df = pd.read_csv(f'{self.tables_in_path}/{table["destination"]}', dtype=str)

        # Return error if there is no data
        if df.empty:
            logging.exception(f'Input table {table["destination"]} is empty!')
            exit(1)

        return df

    def _get_url(self, settings: Settings) -> str:
        """
        Returns the url for the request.
        """
        if settings.message_type == 'Promotional':
            return PROMOTIONAL_URL
        return TRANSACTIONAL_URL

    def _get_body(self, credentials: Credentials, settings: Settings) -> dict:
        """
        Returns the body for the request.
        """

        # Set channels
        channels = {}
        if settings.viber:
            channels['viber'] = {"sender": settings.viber_sender}

        channels['sms'] = {
            "sender_id": "gProfile",
            "sender_id_value": str(settings.sender_id)
            }

        return {"application_id": credentials.application_id,
                "application_token": credentials.application_token,
                "number": [],
                "channel": channels
                }

    def _send_messages(self, url: str, body: dict, data: pd.DataFrame) -> None:
        """
        Send messages to the specified recipients
        """
        # Get unique timestamps
        timestamps = data.timestamp.unique()
        runs = 0

        for time in timestamps:
            # Get the recipients and messages for the current timestamp
            number = []
            for message in data.loc[data.timestamp == time].to_dict('records'):
                number.append({"number": message['number'], "text": message['text']})
            body['number'] = number

            # Set schedule if present
            if time != "0":
                body['schedule'] = time

            # Send the request
            response = requests.post(url, json=body)

            # Return error if the request fails
            if response.status_code != 200:
                logging.error(f'There was an error calling Bulkgate API due to {response.reason}')
                sys.exit(1)

            # Save response
            if runs == 0:
                runs += 1
                self._create_tables_definitions()
            self._save_response(response.json())

    def _create_tables_definitions(self) -> None:
        """
        Creates the tables definitions for output tables.
        """

        # Create tables definitions
        self._stats_table = self.create_out_table_definition('stats.csv', incremental=True, primary_key=['timestamp'])
        self._messages_table = self.create_out_table_definition(
            'messages.csv', incremental=True, primary_key=['message_id'])
        self._messages_parts_table = self.create_out_table_definition(
            'messages_parts.csv', incremental=True, primary_key=['part_id'])

        # Open stats file, set headers, writer and write headers
        self._stats_file = open(self._stats_table.full_path, 'wt', encoding='UTF-8', newline='')
        stats_fields = [
                'timestamp', 'sent', 'accepted', 'scheduled',
                'error', 'blacklisted', 'invalid_number', 'invalid_sender'
                ]
        self._stats_writer = csv.DictWriter(self._stats_file, fieldnames=stats_fields)
        self._stats_writer.writeheader()

        # Open messages file, set headers, writer and write headers
        self._messages_file = open(self._messages_table.full_path, 'wt', encoding='UTF-8', newline='')
        messages_fields = ['message_id', 'status', 'number', 'channel', 'timestamp']
        self._messages_writer = csv.DictWriter(self._messages_file, fieldnames=messages_fields)
        self._messages_writer.writeheader()

        # Open messages parts file, set headers, writer and write headers
        self._messages_parts_file = open(self._messages_parts_table.full_path, 'wt', encoding='UTF-8', newline='')
        messages_parts_fields = ['part_id', 'message_id']
        self._messages_parts_writer = csv.DictWriter(self._messages_parts_file, fieldnames=messages_parts_fields)
        self._messages_parts_writer.writeheader()

    def _save_response(self, response: dict) -> None:
        """
        Save response to the output table
        """
        current_time = datetime.now().isoformat()

        # Parse stats data
        stats = response['data']['total']['status']
        stats['timestamp'] = current_time

        # Load stats data
        self._stats_writer.writerow(stats)

        # Parse messages data and load
        for message in response['data']['response']:
            message['timestamp'] = current_time

            # Load messages parts data
            for part in message['part_id']:
                self._messages_parts_writer.writerow({
                    'part_id': part,
                    'message_id': message['message_id']
                })

            # Load messages data
            message.pop('part_id', None)
            self._messages_writer.writerow(message)

    def _close_and_manifest_files(self) -> None:
        """
        Close and manifest files
        """
        # Close files
        self._stats_file.close()
        self._messages_file.close()
        self._messages_parts_file.close()

        # Manifest files
        self.write_manifests([self._stats_table, self._messages_table, self._messages_parts_table])


"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        # this triggers the run method by default and is controlled by the configuration.action parameter
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
