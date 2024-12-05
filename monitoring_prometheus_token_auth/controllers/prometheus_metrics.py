# Copyright 2016-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from prometheus_client import generate_latest

from odoo.http import Controller, route, request

class PrometheusController(Controller):
    @route("/metrics", auth='token')
    def metrics(self, **kw):
        headers = {'Content-Type': 'text/plain'}
        return request.make_response(generate_latest(), headers=headers)
