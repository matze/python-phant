## python-phant

A Python client library for Phant. See
[data.sparkfun.com](https://data.sparkfun.com/) for more information.


### Usage

```python
p = Phant('xyzpublickey', 'temp', 'humid', private_key='abcprivatekey')

p.log(33.4, 10.2)
print(p.remaining_bytes, p.cap)

data = p.get()
print(data['temp'])
```
