from odoo import models, fields, api

class CalorieManagers(models.Model):
    """ 
    Model for managers of the calorie app
    """
    _name = "calories.managers"
    _description = "Managers of the calorie recommendation app"

    name = fields.Char(required=True, string="Full name")
    recommendations_ids = fields.One2many("calories.users", "manager_id", string="Recommendations")
    total_calories = fields.Float(compute="_get_total_calories")

    @api.depends('recommendations_ids.calories')
    def _get_total_calories(self):
        for rec in self:
            rec.total_calories = sum(rec.recommendations_ids.mapped("calories"))