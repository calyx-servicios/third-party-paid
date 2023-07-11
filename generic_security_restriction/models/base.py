import logging

from odoo import models, api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):

        res = super(Base, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if self._uid == SUPERUSER_ID:
            return res

        if res.get('toolbar', {}).get('print', []):

            hidden_reports = self.env.user.hidden_reports_ids
            hidden_reports += self.env.user.groups_id.mapped(
                'hidden_report_ids')

            new_print_actions = []
            for act in res['toolbar']['print']:

                if act['id'] not in hidden_reports.ids:
                    # Remove field that contains user or groups restrictions to
                    # avoid passing it to js client.
                    act.pop('hide_for_user_ids', False)
                    act.pop('hide_for_group_ids', False)
                    new_print_actions += [act]
            res['toolbar']['print'] = new_print_actions

        # Remove restricted actions from view
        if res.get('toolbar', {}).get('action', []):

            hidden_actions = self.env.user.hidden_actions_ids
            hidden_actions += self.env.user.groups_id.mapped(
                'hidden_actions_ids')
            # check hided server actions
            hidden_server_actions = self.env.user.hidden_server_actions_ids
            hidden_server_actions += self.env.user.groups_id.mapped(
                'hidden_server_actions_ids')
            new_window_actions = []
            for act in res['toolbar']['action']:

                if act['id'] not in (
                        hidden_actions.ids + hidden_server_actions.ids):
                    act.pop('restrict_group_ids', False)
                    act.pop('hide_from_user_ids', False)
                    new_window_actions += [act]
            res['toolbar']['action'] = new_window_actions

        if res.get('toolbar', {}).get('relate', []):

            hidden_actions = self.env.user.hidden_actions_ids
            hidden_actions += self.env.user.groups_id.mapped(
                'hidden_actions_ids')
            # check hided server actions related
            hidden_server_actions = self.env.user.hidden_server_actions_ids
            hidden_server_actions += self.env.user.groups_id.mapped(
                'hidden_server_actions_ids')
            new_related_actions = []
            for act in res['toolbar']['relate']:

                if act['id'] not in (
                        hidden_actions.ids + hidden_server_actions.ids):
                    act.pop('restrict_group_ids', False)
                    act.pop('hide_from_user_ids', False)
                    new_related_actions += [act]
            res['toolbar']['relate'] = new_related_actions

        return res
