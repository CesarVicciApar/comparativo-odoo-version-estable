from odoo import api, fields, models
import requests
from datetime import date
from bs4 import BeautifulSoup
import logging

_logger = logging.getLogger(__name__)

try:
    import urllib3

    urllib3.disable_warnings()
    pool = urllib3.PoolManager()
except ImportError:
    _logger.warning("no se ha cargado urllib3")

month_array = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

url = 'https://www.sii.cl/valores_y_fechas/'

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def prepare_scrapping_vals_from_sii(self, data, month_today, year_str, month, currency):
        soup = BeautifulSoup(data.content, "html.parser")
        content_current_month = soup.find(id="mes_%s" % month)
        content_current_month_div = content_current_month.find_all("div", class_='table-responsive')[0]
        content_current_month_table = \
        content_current_month_div.find_all("table", class_='table table-hover table-bordered')[0]
        content_current_month_days = content_current_month_table.find_all("strong")
        content_current_month_rates = content_current_month_div.find_all("td")
        days = []
        rates = []
        rates1 = []
        for th in content_current_month_days:
            if th.text:
                days.append(th.text)
        for td in content_current_month_rates:
            if td.text:
                rates.append(td.text)
        values = []
        if len(rates) == 31:
            for x in range(0, len(rates)):
                rate = rates[x]
                if rate != '':
                    month_today_fill = str(month_today).zfill(2)
                    day_fill = days[x].zfill(2)
                    fecha = year_str + '-' + str(month_today_fill) + '-' + day_fill
                    amount_str = rates[x].replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                    rate = 1 / amount if amount else 1
                    vals = {
                        'currency_id': currency.id,
                        'name': fecha,
                        'rate': rate
                    }
                    values.append(vals)
        else:
            for td in content_current_month_rates:
                rates1.append(td.text)
            for x in range(0, len(days)):
                rate = rates1[x]
                if rate != '':
                    month_today_fill = str(month_today).zfill(2)
                    day_fill = days[x].zfill(2)
                    fecha = year_str + '-' + str(month_today_fill) + '-' + day_fill
                    amount_str = rates1[x].replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                    rate = 1 / amount if amount else 1
                    vals = {
                        'currency_id': currency.id,
                        'name': fecha,
                        'rate': rate
                    }
                    values.append(vals)
        return values

    def create_rate_uf(self):
        CurrencyRate = self.env['res.currency.rate']
        for record in self.search([('active', '=', True), ('name', '=', 'UF')]):
            months = []
            currency_name = record.name.lower()
            if date.today().day >= 9:
                month_today = date.today().month
                next_month = month_today + 1
                year_str = str(date.today().year)
                month_str = month_array[month_today]
                months.append((month_str, month_today))
                next_month_str = month_array[next_month]
                months.append((next_month_str, next_month))
                data = requests.get(url + currency_name + '/' + currency_name + year_str + '.htm')
                if data.status_code == 200:
                    for month in months:
                        values = self.prepare_scrapping_vals_from_sii(data, month[1], year_str, month[0], record)
                        for val in values:
                            exist = CurrencyRate.search([('name', '=', val['name']), ('currency_id', '=', record.id)])
                            if not exist:
                                CurrencyRate.create(val)
            else:
                month_today = date.today().month
                before_month = month_today - 1
                year_str = str(date.today().year)
                before_month_str = month_array[before_month]
                months.append((before_month_str, before_month))
                month_str = month_array[month_today]
                months.append((month_str, month_today))
                data = requests.get(url + currency_name + '/' + currency_name + year_str + '.htm')
                if data.status_code == 200:
                    for month in months:
                        values = self.prepare_scrapping_vals_from_sii(data, month[1], year_str, month[0], record)
                        for val in values:
                            exist = CurrencyRate.search([('name', '=', val['name']), ('currency_id', '=', record.id)])
                            if not exist:
                                CurrencyRate.create(val)

