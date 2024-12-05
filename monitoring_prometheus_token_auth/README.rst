.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

==================================================
Monitoring: Prometheus metrics with API token auth
==================================================

Add an endpoint */metrics* to allow a Prometheus server to fetch application metrics.

In order to protect sensitive metrics, an API token is used for authentication.

```
curl -v -H "Authorization: Bearer f7e0d0ce6723da9ffd2b59cbfad57a5257cd7f13" https://odoo.yourdomain.com/metrics
```

To obtain an API token, create a new user in Odoo (i.e. 'Metrics'), and assign them appropriate read permissions to resources you will be providing metrics for. Then, as that user, go to 'Preferences', and create a new API key.

To monitor specific resources, create metrics controllers like the following:


```python
from prometheus_client import Gauge, generate_latest

from odoo.http import Controller, route, request

import time

class PrometheusController(Controller):
    _g1 = Gauge('exchange_rate', 'Exchange rate compared to THB', ['name'])
    _g2 = Gauge('exchange_rate_date', 'Exchange rate last updated', ['name'])

    @route("/metrics", auth='token')
    def metrics(self, **kw):
        currencies = request.env['res.currency'].search([
            ('active', '=', 'true')
        ])
        for c in currencies:
            if not c['date']:
                continue
            t = time.mktime(c['date'].timetuple()) 
            self._g1.labels(c['name']).set(c['rate'])
            self._g2.labels(c['name']).set(t)

        headers = {'Content-Type': 'text/plain'}
        return request.make_response(generate_latest(), headers=headers)
```