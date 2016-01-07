import json
import logging


def default_encode(o):
    '''
    Encode complex numbers to json serializable objects
    '''
    if type(o) == complex:
        return {'__complex__': True, 'real': o.real, 'imag': o.imag}
    return o


def default_decode(o):
    '''
    Decode complex numbers from json serializable objects
    '''
    if isinstance(o, dict):
        if '__complex__' in o:
            return complex(o['real'], o['imag'])
    return o


def serialize(value):
    '''
    Convert sent values to json serializable objects
    '''
    return json.dumps(value, default=default_encode)


def deserialize(key, value):
    '''
    Translate back json serializable objects.
    '''
    if key != 'timestamp':
        try:
            return json.loads(value, object_hook=default_decode)
        except TypeError:
            logging.debug('Unable to deserialize %s of type %s' %
                          (value, type(value)))
    return value
