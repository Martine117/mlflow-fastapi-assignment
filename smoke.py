"""Verify a running image using only Python's standard library."""
import json
import time
import urllib.request
import urllib.error

for attempt in range(60):
    try:
        request = urllib.request.Request('http://127.0.0.1:8000/predict',
            data=json.dumps({'instances': [[0]*64]}).encode(),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=2) as response:
            result = json.load(response)
        assert len(result['predictions']) == 1
        assert type(result['predictions'][0]) is int
        assert result['predictions'][0] in range(10)
        break
    except (urllib.error.URLError, TimeoutError):
        time.sleep(1)
else:
    raise RuntimeError('Container did not serve predictions')
print('Container prediction passed')
