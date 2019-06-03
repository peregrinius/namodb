import botocore
import logging

logger = logging.getLogger(__name__)

from dynosql.dyno_record import DynoRecord
from dynosql.helper_methods import DYNAMODB_DATATYPES_LOOKUP
from dynosql.helper_methods import DYNAMODB_DATATYPES_LOOKUP2
from dynosql.helper_methods import DYNAMODB_DATATYPES_REVERSE_LOOKUP
from dynosql.helper_methods import UNFLUFF

class DynoTable(object):
    """ DynoTable is a wrapper class around botocore. Each instance references a table in DynamoDB
        and mimics the behaviour python dict for simple opperations such as:
         * inserting records
         * retrieving records by id
         * deleting records

        More advanced features are handled more like list functions:
         * filtering by non primary key attributes
         * bulk inserting or updates

    """
    def __init__(self, client, table_name, partition_key=None, sort_key=None, **attributes):
        self.client = client
        self.table_name = table_name
        self.partition_key = partition_key
        self.sort_key = sort_key
        self.descrbe = None
        self.record = {}

        KeySchema = []
        AttributeDefinitions = []

        if partition_key:
            KeySchema.append({ 'AttributeName': partition_key[0], 'KeyType': 'HASH' })
            AttributeDefinitions.append(
                {
                    'AttributeName': partition_key[0],
                    'AttributeType': DYNAMODB_DATATYPES_LOOKUP[partition_key[1]]
                }
            )
        if sort_key:
            KeySchema.append({ 'AttributeName': sort_key[0], 'KeyType': 'RANGE' })
            AttributeDefinitions.append(
                {
                    'AttributeName': sort_key[0],
                    'AttributeType': DYNAMODB_DATATYPES_LOOKUP[sort_key[1]]
                }
            )
        logger.debug(KeySchema)
        logger.debug(AttributeDefinitions)

        try:
            description = self.client.create_table(
                TableName=table_name,
                KeySchema=KeySchema,
                AttributeDefinitions=AttributeDefinitions,
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                },
            )
            description['Table'] = description['TableDescription']
            del description['TableDescription']
            self.describe = description
        except Exception as e:
            description = self.client.describe_table(TableName=table_name)
            logger.debug(description['Table'])
            self.partition_key = (
                description['Table']['AttributeDefinitions'][0]['AttributeName'],
                DYNAMODB_DATATYPES_LOOKUP2[description['Table']['AttributeDefinitions'][0]['AttributeType']]
            )
            try:
                self.sort_key = (
                    description['Table']['AttributeDefinitions'][1]['AttributeName'],
                    DYNAMODB_DATATYPES_LOOKUP2[description['Table']['AttributeDefinitions'][1]['AttributeType']]
                )
            except IndexError:
                pass
            self.describe = description

    def drop(self):
        """ __del__ isn't very reliable in testing
            backup method for making sure tables are deleted

        Parameters:
        None

        Return:
        None
        """
        try:
            self.client.delete_table(TableName=self.table_name)
            logger.debug('deleted %s' % self.table_name)
        except self.client.exceptions.ResourceNotFoundException:
            # table doesn't exist
            pass

    def __del__(self):
        """ Deletes the referenced table from DynamoDB

        Parameters:
        None

        Return:
        None
        """
        try:
            self.client.delete_table(TableName=self.table_name)
            logger.debug('deleted %s' % self.table_name)
        except ReferenceError:
            # This method is always called when the class is destroyed
            # if it is not called explicitly it will raise a ReferenceError
            pass
        except self.client.exceptions.ResourceNotFoundException:
            # table doesn't exist
            pass

    def __setitem__(self, key, attributes):
        """ Inserts a new record or updates an existing one

        Parameters:
        key (tuple/string): can be a tuple if a composite key is used as primary key
            otherwise a string containing the partition key
        atttributes (dict): additional attributes

        Return:
        None: It is an assignment operator so cannot return a response
        """
        self.record[key] = DynoRecord(self, key, attributes)
        # return self.record[key] # DynoRecord(self, key, attributes)

    def __getitem__(self, key):
        """ Retreive the record from DynamoDB based on the passed key

        Parameters::
        key (tuple/string): can be a tuple if a composite key is used as primary key
            otherwise a string containing the partition key

        Return:
        dict: Returns record from DynamoDB
        """
        logger.info(self.partition_key)
        logger.info(DYNAMODB_DATATYPES_LOOKUP[self.partition_key[1]])
        try:
            partition_key_value, sort_key_value = key
            keys = {
                self.partition_key[0]: { DYNAMODB_DATATYPES_LOOKUP[self.partition_key[1]]: partition_key_value },
                self.sort_key[0]: { DYNAMODB_DATATYPES_LOOKUP[self.sort_key[1]]: sort_key_value }
            }
        except ValueError:
            partition_key_value, sort_key_value = (key, None,)
            keys = {
                self.partition_key[0]: { DYNAMODB_DATATYPES_LOOKUP[self.partition_key[1]]: partition_key_value }
            }
        except TypeError:
            raise KeyError('Table was not defined with a sort key')

        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key=keys
            )
            response = UNFLUFF(response)
        except botocore.exceptions.ClientError as e:
            logger.error(e)
            raise KeyError(str(e))

        logger.info(self.record)
        logger.info(key)

        self.record[key] = response

        return response