import sys
import datetime
import requests as rq
import logging
import json
try:
    from Crypto.Cipher import AES
    from Crypto import Random
    import hashlib
    import base64
    CRYPTO_AVAILABLE=True
except Exception, CRYPTO_EXCEPTION:
    CRYPTO_AVAILABLE=False


if sys.version_info[0] < 3:
    def only_strings_in(iterable):
        return all((isinstance(x, (str, unicode)) for x in iterable))
else:
    def only_strings_in(iterable):
        return all((isinstance(x, str) for x in iterable))


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


def check_json_response(response):
    '''
    Translate errorful responses to python exceptions
    '''
    if isinstance(response, dict) and not response['success']:
        raise ValueError(response['message'])


class Phant(object):
    '''
    Main class to manage Phant connections
    '''
    def __init__(self, public_key, own_key=None, fields=[], private_key=None, delete_key=None, base_url='http://data.sparkfun.com'):
        """
        *fields* is a tuple containg the field names of the stream identified by *public_key*. 
        Can additionally contain the *private_key*, the
        *delete_key* and an alternative *base_url*.
        """
        if not only_strings_in(fields):
            raise ValueError("String type expected for *fields")
        self.public_key = public_key
        self.private_key = private_key
        self.own_key = own_key
        if own_key:
            if not CRYPTO_AVAILABLE:
                raise CRYPTO_EXCEPTION
            self.own_key = hashlib.sha256(own_key).digest()
            BS = 16
            self.pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
            self.unpad = lambda s : s[:-ord(s[len(s)-1:])]
        self.delete_key = delete_key
        self.base_url = base_url
        self._session = rq.Session()
        # If no fieds explicitly given, try to guess.
        if len(fields) == 0:
            self._fields = self.get_fields()
        else:
            self._fields = fields
        self._extended_fields = ['timestamp']
        self._extended_fields.extend(self._fields)
        self._stats = None
        self._last_headers = None

    def serialize(self, value):
        '''
        Convert sent values to json serializable objects
        '''
        message = json.dumps(value, default=default_encode, ensure_ascii=True, encoding="ascii")
        if self.own_key is not None:
            message=self.pad(message)
            IV = Random.new().read( AES.block_size )
            encryption_suite = AES.new(self.own_key, AES.MODE_CBC, IV)
            message = base64.b64encode( IV + encryption_suite.encrypt(message) )
        return message

    def deserialize(self, key, value):
        '''
        Translate back json serializable objects.
        '''
        if key != 'timestamp':
            if self.own_key is not None:
                enc = base64.b64decode(value)
                IV = enc[:16]
                encryption_suite = AES.new(self.own_key, AES.MODE_CBC, IV)
                value = self.unpad( encryption_suite.decrypt( enc[16:] ) )
            try:
                value = json.loads(value, object_hook=default_decode)
            except TypeError:
                logging.debug('Unable to deserialize %s of type %s' %
                              (value, type(value)))
        return value

    def get_fields(self):
        '''
        Gets required parameters from a first dummy request.
        The way we get the parameters is a little bit tricky 
        but works.
        '''
        self._check_private_key("log data")
        response = self._session.post(self._get_url('input'), params={
                                      'private_key': self.private_key})
        return map(lambda x: x.strip(), response.json()['message'].split('missing from sent data. \n\nexpecting:')[1].split(','))

    def log(self, *args):
        """
        Log arguments. args must match the fields and the object must be
        created with a *private_key*.
        """
        self._check_private_key("log data")
        params = {'private_key': self.private_key}
        params.update(dict((k, self.serialize(v))
                           for k, v in zip(self._fields, args)))
        response = self._session.post(self._get_url('input'), params=params)
        check_json_response(response.json())

        self._last_headers = response.headers
        self._stats = None

    def clear(self):
        """
        Clear data from stream. Object must be created with a *private_key*.
        """
        self._check_private_key("clear data")
        headers = {'Phant-Private-Key': self.private_key}
        self._session.delete(self._get_url('input', ext=''), headers=headers)

    def _check_limit_tuple(self, limit_tuple):
        if not isinstance(limit_tuple, tuple):
            raise ValueError("Limit argument must be a tuple")

        if len(limit_tuple) != 2:
            raise ValueError(
                "Limit tuple must be of len() == 2.  Got {}".format(len(limit_tuple)))

        if not isinstance(limit_tuple[0], (str, basestring, unicode)):
            raise ValueError("Field name must be a string")

        if not isinstance(limit_tuple[1], (str, basestring, unicode)):
            raise ValueError("Field limit must be a string")

        if limit_tuple[0] not in self._extended_fields:
            raise ValueError("Field \'{}\' not in the known list of fields: {}".format(
                limit_tuple[0], self._fields))

        return True

    def get(self, limit=None, offset=None, sample=None, timezone=None, grep=None, eq=None, ne=None, gt=None, lt=None, gte=None, lte=None, convert_timestamp=True, sort_by=None):
        """
        Return the data as a list of dictionaries.

        If *convert_timestamp* is False, the timestamps will not be converted to
        datetime.datetime objects.

        :param limit: Limits how many entries will be returned.
        :type limit: int
        :param offset: Skip offset records before returning normally.  Implemented server side
        :type offset: int
        :param sample: Only return every N samples.  Implemented server side
        :type sample: int
        :param timezone: Convert timestamp to specified timezone. See https://www.iana.org/time-zones for definition or
                         https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a convenient list of string.
                         Implemented server side
        :type timezone: str
        :param grep: Expects a tuple of (field,limit) to limit on.  Includes if values in field match the regular express supplied in limit
        :type grep: tuple
        :param eq: Expects a tuple of (field,limit) to limit on.  Includes if values in field == the value supplied in limit
        :type eq: tuple
        :param ne: Expects a tuple of (field,limit) to limit on.  Includes if values in field is != to the value supplied in limit
        :type ne: tuple
        :param gt: Expects a tuple of (field,limit) to limit on.  Includes if values in field > the value supplied in limit
        :type gt: tuple
        :param lt: Expects a tuple of (field,limit) to limit on.  Includes if values in field < the value supplied in limit
        :type lt: tuple
        :param gte: Expects a tuple of (field,limit) to limit on.  Includes if values in field >= the value supplied in limit
        :type gte: tuple
        :param lte: Expects a tuple of (field,limit) to limit on.  Includes if values in field <= the value supplied in limit
        :type lte: tuple
        :param sort_by: Expects a key to sort entries (defaults to None for unsorted output)
        :type sort_by: str
        """

        params = {}
        if limit:
            if not isinstance(limit, int):
                raise ValueError("Limit must be an int")
            params['limit'] = limit

        if offset:
            if not isinstance(offset, int):
                raise ValueError("Offset must be an int")
            params['offset'] = offset

        if sample:
            if not isinstance(sample, int):
                raise ValueError("Sample must be an int")
            params['sample'] = sample

        if timezone:
            if not isinstance(timezone, str):
                raise ValueError("Timezone must be a str")
            params['timezone'] = timezone

        if grep and self._check_limit_tuple(eq):
            logging.debug("Found grep limit")
            params['{}[{}]'.format('grep', grep[0])] = grep[1]

        if eq and self._check_limit_tuple(eq):
            logging.debug("Found eq limit")
            params['{}[{}]'.format('eq', eq[0])] = eq[1]

        if ne and self._check_limit_tuple(ne):
            logging.debug("Found ne limit")
            params['{}[{}]'.format('ne', ne[0])] = ne[1]

        if gt and self._check_limit_tuple(gt):
            logging.debug("Found gt limit")
            params['{}[{}]'.format('gt', gt[0])] = gt[1]

        if lt and self._check_limit_tuple(lt):
            logging.debug("Found lt limit")
            params['{}[{}]'.format('lt', lt[0])] = lt[1]

        if gte and self._check_limit_tuple(gte):
            logging.debug("Found gte limit")
            params['{}[{}]'.format('gte', gte[0])] = gte[1]

        if lte and self._check_limit_tuple(lte):
            logging.debug("Found lte limit")
            params['{}[{}]'.format('lte', lte[0])] = lte[1]

        """
        TODO:

        This is kind of a hack, because the current version of the Phant server doesn't properly handle url encoded
        strings in the query params.  The requests library always urlencodes them, and with the goofy grep[fielname]=regex syntax that
        Phant expects, it gets wonky.  This hack creates a string thats NOT encoded that requests is willing to just pass along blindly,
        where normally you'd pass a dictionary.
        """
        payload_str = "&".join("%s=%s" % (k, v) for k, v in params.items())
        response = self._session.get(self._get_url(
            'output'), params=payload_str).json()
        check_json_response(response)
        if convert_timestamp:
            if timezone:
                pattern = '%Y-%m-%dT%H:%M:%S'
            else:
                pattern = '%Y-%m-%dT%H:%M:%S.%fZ'

            for entry in response:
                timestamp = entry['timestamp']
                if timezone:
                    timestamp = timestamp[:-6]
                entry['timestamp'] = datetime.datetime.strptime(
                    timestamp, pattern)
        response = map(lambda r: {k: self.deserialize(k, v)
                                  for k, v in r.items()}, response)
        if sort_by:
            if sort_by not in self._extended_fields:
                raise ValueError("Field \'{}\' not in the known list of fields: {}".format(
                    sort_by, self._fields))
            response = sorted(response, key=lambda x: x[sort_by])
        return response

    @property
    def remaining_requests(self):
        """Number of remaining requests."""
        try:
            return self._get_limit('Remaining')
        except ValueError:
            logging.error(
                "Unable to gather limit statistics until log() has been called. Returning -1")
            return -1

    @property
    def request_limit(self):
        """Request limit."""
        try:
            return self._get_limit('Limit')
        except ValueError:
            logging.error(
                "Unable to gather limit statistics until log() has been called. Returning -1")
            return -1

    @property
    def reset_time(self):
        """Request reset time."""
        try:
            return self._get_limit('Reset')
        except ValueError:
            logging.error(
                "Unable to gather limit statistics until log() has been called. Returning -1")
            return -1

    @property
    def remaining_bytes(self):
        """Number of remaining stream bytes."""
        try:
            return self._get_limit('remaining')
        except ValueError:
            logging.error(
                "Unable to gather limit statistics until log() has been called. Returning -1")
            return -1

    @property
    def used_bytes(self):
        """Used stream bytes."""
        return self._get_stat('used')

    @property
    def cap(self):
        """Stream limit."""
        return self._get_stat('cap')

    def _check_private_key(self, message):
        if not self.private_key:
            raise ValueError(
                "Must create Phant object with private_key to {}".format(message))

    def _get_url(self, command, ext='.json'):
        return '{}/{}/{}{}'.format(self.base_url, command, self.public_key, ext)

    def _get_stat(self, name):
        if not self._stats:
            response = self._session.get(
                self._get_url('output', '/stats.json'))
            self._stats = response.json()

        return self._stats[name]

    def _get_limit(self, name):
        if not self._last_headers:
            raise ValueError("No request made yet")

        return self._last_headers['X-Rate-Limit-{}'.format(name)]
