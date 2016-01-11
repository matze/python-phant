import json
import logging


def serialize(value):
    '''
    Convert sent values to json serializable objects
    '''
    return json.dumps(value)


def deserialize(key, value):
    '''
    Translate back json serializable objects.
    '''
    if key != 'timestamp':
        try:
            return json.loads(value)
        except TypeError:
            logging.debug('Unable to deserialize %s of type %s' %
                          (value, type(value)))
    return value
