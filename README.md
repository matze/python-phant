## python-phant

A Python client library for Phant. See
[data.sparkfun.com](https://data.sparkfun.com/) for more information.


### Installation

Either

* copy the `phant.py` module into you source tree or
* run `python setup.py install` or
* install with `pip install phant`.


### Usage

A basic example of connecting and logging data.  Note that collecting some of the information around API rate limits only works after a `log()` command

```python
import sys
from phant import Phant
p = Phant('xyzpublickey', fields=['temp', 'humid'], private_key='abcprivatekey')

t = 33.4
h = 10.2
p.log(t, h)
print(p.remaining_bytes, p.cap)

data = p.get()
print(data['temp'])
```

Another example, this time limiting to 10 results, and only if the temperature was '9'.

```python

p.get(
    eq=("temp","9"),
    limit=10
)

```
