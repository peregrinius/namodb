import botocore
import logging

logger = logging.getLogger(__name__)

from dynosql.dyno_record import DynoRecord
from dynosql.dyno_attribute import DynoAttribute

from dynosql.helper_methods import DYNAMODB_DATATYPES_LOOKUP
from dynosql.helper_methods import DYNAMODB_DATATYPES_LOOKUP2
from dynosql.helper_methods import DYNAMODB_DATATYPES_REVERSE_LOOKUP
from dynosql.helper_methods import UNFLUFF
from dynosql.helper_methods import ATTRIBUTE_VALUES, DYNAMODB_EXPRESSION_LOOKUP


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
    def __init__(self, adapter, table_name, partition_key=None, sort_key=None, **attributes):
        self.adapter = adapter
        self.table_name = table_name
        # self.partition_key = partition_key
        # self.sort_key = sort_key
        self.__info = None
        self.queries = []
        logger.info(partition_key)
        logger.info(sort_key)
        self.__info = self.adapter.create_table(table_name=table_name, partition_key=partition_key, sort_key=sort_key, attributes=attributes)

        ## commented for injection
        # KeySchema = []
        # AttributeDefinitions = []

        # if partition_key:
        #     KeySchema.append({ 'AttributeName': partition_key[0], 'KeyType': 'HASH' })
        #     AttributeDefinitions.append(
        #         {
        #             'AttributeName': partition_key[0],
        #             'AttributeType': DYNAMODB_DATATYPES_LOOKUP[partition_key[1]]
        #         }
        #     )
        # if sort_key:
        #     KeySchema.append({ 'AttributeName': sort_key[0], 'KeyType': 'RANGE' })
        #     AttributeDefinitions.append(
        #         {
        #             'AttributeName': sort_key[0],
        #             'AttributeType': DYNAMODB_DATATYPES_LOOKUP[sort_key[1]]
        #         }
        #     )
        # logger.info(KeySchema)
        # logger.info(AttributeDefinitions)

        # try:
        #     description = self.client.create_table(
        #         TableName=table_name,
        #         KeySchema=KeySchema,
        #         AttributeDefinitions=AttributeDefinitions,
        #         ProvisionedThroughput={
        #             'ReadCapacityUnits': 5,
        #             'WriteCapacityUnits': 5,
        #         },
        #     )
        #     description['Table'] = description['TableDescription']
        #     del description['TableDescription']
        #     self.__info = description
        # except botocore.exceptions.ParamValidationError as e:
        #     description = self.client.describe_table(TableName=table_name)
        #     #logger.info(description['Table'])
        #     self.partition_key = (
        #         description['Table']['AttributeDefinitions'][0]['AttributeName'],
        #         DYNAMODB_DATATYPES_LOOKUP2[description['Table']['AttributeDefinitions'][0]['AttributeType']]
        #     )
        #     try:
        #         self.sort_key = (
        #             description['Table']['AttributeDefinitions'][1]['AttributeName'],
        #             DYNAMODB_DATATYPES_LOOKUP2[description['Table']['AttributeDefinitions'][1]['AttributeType']]
        #         )
        #     except IndexError:
        #         pass
        #     self.__info = description


    def __setitem__(self, key, attributes):
        """ Inserts a new record or replaces an existing one

        Parameters:
        key (tuple/string): can be a tuple if a composite key is used as primary key
            otherwise a string containing the partition key
        atttributes (dict): additional attributes

        Return:
        None: It is an assignment operator so cannot return a response
        """
        logger.info('setitem: %s - %s' % (key, attributes))
        #DynoRecord(self, self._get_keys(key), attributes)
        DynoRecord(self.adapter, self.table_name, key, attributes)


    def __getitem__(self, key):
        """ Retreive record with key

        Parameters:
        key (tuple/string): composite/primary key for the record
            otherwise a string containing the partition key

        Return:
        dict: Returns record from DynamoDB
        """
        logger.info('getitem: %s' % str(key))
        ## migration
        #return DynoRecord(self, self._get_keys(key))
        return DynoRecord(self.adapter, self.table_name, key)


    def __delitem__(self, key):
        """ Delete record from a table

        Parameters:
        key (string/tuple): composite/primary key for the record
        """
        logger.info('delete: %s' % str(key))
        ## migration
        # self.client.delete_item(
        #     TableName=self.table_name,
        #     Key=self._get_keys(key)
        # )
        self.adapter.delete_item(self.table_name, key)


    def __del__(self):
        """ Deletes the referenced table from database

        Parameters:
        None

        Return:
        None
        """
        ## Migration
        # try:
        #     self.client.delete_table(TableName=self.table_name)
        #     logger.debug('deleted %s' % self.table_name)
        # except ReferenceError:
        #     # This method is always called when the class is destroyed
        #     # if it is not called explicitly it will raise a ReferenceError
        #     pass
        # except self.client.exceptions.ResourceNotFoundException:
        #     # table doesn't exist
        #     pass
        self.adapter.delete_table(self.table_name)


    @property
    def info(self):
        return self.__info


    # def _get_keys(self, key):
    #     try:
    #         partition_key_value, sort_key_value = key
    #         keys = {
    #             self.partition_key[0]: { DYNAMODB_DATATYPES_LOOKUP[self.partition_key[1]]: str(partition_key_value) },
    #             self.sort_key[0]: { DYNAMODB_DATATYPES_LOOKUP[self.sort_key[1]]: str(sort_key_value) }
    #         }
    #     except ValueError:
    #         partition_key_value, sort_key_value = (key, None,)
    #         keys = {
    #             self.partition_key[0]: { DYNAMODB_DATATYPES_LOOKUP[self.partition_key[1]]: str(partition_key_value) }
    #         }
    #     except TypeError:
    #         raise KeyError('Table was not defined with a sort key')

    #     return keys

    def __getattr__(self, name):
        logger.info(name)
        #self.queries.append(DynoAttribute(name))
        return DynoAttribute(name) #self.queries[-1]

    def __setattr__(self, name, value):
        logger.info(name)
        logger.info(value)
        super(DynoTable, self).__setattr__(name, value)


    def filter(self, filter_expression):
        # logger.info(self.queries)
        logger.info(filter_expression)
        self.adapter.filter(self.table_name, filter_expression)

        ## Migration
        # import inspect
        # import re

        # #logger.info(self.queries)
        # logger.info(filter_expression)

        # exp_attribute, exp_operator, exp_value = filter_expression

        # filter_expression_values = "{} {} :{}".format(
        #     exp_attribute,
        #     exp_operator,
        #     ATTRIBUTE_VALUES[0]
        # )

        # expression_attribute_values = {
        #     ':{}'.format(ATTRIBUTE_VALUES[0]): {
        #         DYNAMODB_DATATYPES_LOOKUP[type(exp_value).__name__]: str(exp_value)
        #     }
        # }

        # logger.info(filter_expression_values)
        # logger.info(expression_attribute_values)

        # response =  self.client.scan(
        #     TableName=self.table_name,
        #     ExpressionAttributeValues=expression_attribute_values,
        #     FilterExpression=filter_expression_values
        # )
        # logger.info(response)
        # logger.info(UNFLUFF(response))

        # return UNFLUFF(response)


    def drop(self):
        """ __del__ isn't very reliable in testing
            backup method for making sure tables are deleted

        Parameters:
        None

        Return:
        None
        """
        self.adapter.delete_table(self.table_name)
        ## Migration
        # try:
        #     self.client.delete_table(TableName=self.table_name)
        #     logger.debug('deleted %s' % self.table_name)
        # except self.client.exceptions.ResourceNotFoundException:
        #     # table doesn't exist
        #     pass
