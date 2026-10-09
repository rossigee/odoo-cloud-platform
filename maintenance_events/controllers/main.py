# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http


class MaintenanceEvents(http.Controller):

    @http.route(['/maintenance/events'], type='json', auth='user', cors='*')
    def get_events(self, **kwargs):
        return {'events': []}
