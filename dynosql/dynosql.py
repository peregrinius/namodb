#!env/bin/python3

# import botocore
# import botocore.session
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s:%(name)s:%(lineno)s:%(levelname)s - %(message)s",
                    level="INFO")

from dynosql.dyno_table import DynoTable
from dynosql.adapters.botocore import BotocoreAdapter


class Dynosql(object):
    """ Base class for Dyno project initiates a session with DynamoDB then
        through the call method creates a table reference
    """

    def __init__(self, endpoint_url='http://localhost:8000/'):
        self.adapter = BotocoreAdapter(endpoint_url=endpoint_url)
        # session = botocore.session.get_session()
        # self.client = session.create_client('dynamodb', endpoint_url=endpoint_url)

    def __call__(self, table_name, partition_key=None, sort_key=None, **attributes):
        """ After Dyno is initiated it can be called to create a table

        Parameters:
        table_name (string):
        partition_key (tuple):
        sort_key (tuple):
        attributes (dict):

        Returns:
        DynoTable: 
        """
        logger.info('creating table: %s' % table_name)
        return DynoTable(self.adapter, table_name, partition_key, sort_key, **attributes)

    # def __delitem__(self, key):
    #     self.client.delete_table(TableName=key)
    #     del self.__dict__[key]

    def list_tables(self):
        """ Fetches a list of table names from database

        Parameters:
        None

        Returns:
        list: of tablenames in database
        """
        table_list = self.adapter.list_tables()
        logger.info(table_list)
        return table_list


