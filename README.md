## python-phant

A Python client library for Phant. See
[data.sparkfun.com](https://data.sparkfun.com/) for more information.


### Installation

Either

* copy the `phant` module into you source tree or
* run `python setup.py install` or
* install with `pip install phant`.


### Usage

A basic example of connecting and logging data.  Note that collecting some of the information around API rate limits only works after a `log()` command

```python
import sys
from phant import Phant
p = Phant(publicKey='xyzpublickey', fields=['temp', 'humid'], privateKey='abcprivatekey')

t = 33.4
h = 10.2
p.log(t, h)
print(p.remaining_bytes, p.cap)

data = p.get()
print(data['temp'])
```

Additionally, the json file generated during stream creation can be provided to the constructor:

```python

import phant
p=phant.Phant(jsonPath='/path/to/my/keys_xyzpublickey.json')
```

Another example, this time limiting to 10 results, and only if the temperature was '9'.

```python

p.get(
    eq=("temp","9"),
    limit=10
)

```

#### Encoders

By default, data is serialiced in order to be stored using json format.

Other encoders can be defined in order to provide support for more complex data structures. Take a look at `phant.encoders.complex` to see a simple example implementing serialization of complex numbers.

To use this feature:

```python

import phant
import phant.encoders.complex

p=phant.Phant(jsonPath='python-phant/keys.json', encoder=phant.encoders.complex)

p.log(1,2,3,4+6j)

p.get(limit=1)

[{u't': 1,
  u'timestamp': datetime.datetime(2016, 1, 7, 15, 47, 56, 420000),
  u'x': 2,
  u'y': 3,
  u'z': (4+6j)}]
´´´

As you can see, complex numbers are correctly logged and got.

If now we try to get  the same values using the default encoder (`plain_json`):
 
´´´python

p=phant.Phant(jsonPath='python-phant/keys.json')

p.get(limit=1)
 
[{u't': 1,
  u'timestamp': datetime.datetime(2016, 1, 7, 15, 47, 56, 420000),
  u'x': 2,
  u'y': 3,
  u'z': {u'__complex__': True, u'imag': 6.0, u'real': 4.0}}]
```

We get a dictionary with the encoded complex number. 

Additionally, trying with no encoders at all you'll notice everything is stored just as plain strings:

```python

import phant.encoders.null

p=phant.Phant(jsonPath='python-phant/keys.json', encoder=phant.encoders.null)

p.get(limit=1)
 
[{u't': u'1',
  u'timestamp': datetime.datetime(2016, 1, 7, 15, 47, 56, 420000),
  u'x': u'2',
  u'y': u'3',
  u'z': u'{"real": 4.0, "imag": 6.0, "__complex__": true}'}]
```

Note you won't be able to log a complex number with neither ´plain_json´ or ´null´ encoders, getting a `TypeError` exception. Same thing happens if you try to log a list or a dictionary with `null` encoder.
