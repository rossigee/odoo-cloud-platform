# Copyright 2012-2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Base FileURL Field",
    "summary": "Implementation of FileURL type fields",
    "version": "17.0.1.0.0",
    "category": "Technical Settings",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/camptocamp/odoo-cloud-platform",
    "license": "AGPL-3",
    "depends": [
        "base_attachment_object_storage",
    ],
    "auto_install": False,
    # Uninstalled by default: the declared dependency
    # base_attachment_object_storage is no longer present on this branch.
    # Matches camptocamp's own 18.0 and 19.0 branches, which drop that
    # module and mark this one installable=False for the same reason.
    "installable": False,
}
