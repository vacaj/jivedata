from flask import session, render_template, url_for, redirect, flash
from jivedata.webapp import app
from jivedata.webapp.views.utils import make_api_request, store_cik
from jinja2 import Template


@app.route('/financials/', defaults={'cik': None})
@app.route('/financials/<cik>/')
def financials(cik):
    """ View the financials """
    if cik is None and 'ticker' in session and session['ticker'] != {}:
        return redirect(url_for('financials', cik=session['ticker']['cik']))
    if cik is not None:
        store_cik(cik)
        if session['ticker'] == {}:
            flash('Invalid ticker', 'danger')
            return redirect('/financials/')

    if cik is None:
        return render_template('financials.jinja2', cik=None)

    if app.config['test_data'] == True:
        if cik != '1288776':
            return redirect('/financials/1288776/')

    params = {'ticker': cik, 'length': -5, 'frequency': 12}
    financials = ['sales', 'ebit', 'adj_ebit', 'ebitda', 'adj_ebitda', 'cfo_minus_capex']
    margins = ['gross_profit_margin', 'adj_ebit_margin',
               'adj_ebitda_margin', 'adj_pretax_income_margin',
               'net_income_margin', 'dividend_yield']
    ratios = ['net_debt_to_adj_ebitda', 'debt_to_assets',
              'debt_to_equity', 'debt_to_interest_expense',
              'return_on_invested_capital']
    multiples = ['cev_to_sales', 'cev_to_adj_ebitda',
                 'price_to_earnings', 'price_to_tangible_book_value']

    all_elements = financials + margins + ratios + multiples
    params['elements'] = ','.join(all_elements)

    response = make_api_request('/financials/detail/', params)

    dates = []
    valid = []
    # get rid of dates with length of 0
    for i, date in enumerate(response['_results_']['_dates_']):
        if 'length' in date and date['length'] != 0:
            valid.append(i)
            dates.append(date)

    results = {'_labels_': response['_results_']['_labels_']}
    for key, values in response['_results_'].iteritems():
        if key not in ['_dates_', '_labels_']:
            if '_total_' in values:
                results[key] = [x for i, x in enumerate(values['_total_']) if
                                i in valid]

    html = generate_financials_template()
    financials = html.render(elements=financials, results=results)
    margins = html.render(elements=margins, results=results)
    ratios = html.render(elements=ratios, results=results)
    multiples = html.render(elements=multiples, results=results)

    return render_template('financials.jinja2', detail='true', dates=dates,
                           financials=financials, margins=margins,
                           ratios=ratios, multiples=multiples)


def generate_financials_template():
    h = Template(u'''
    {% for el in elements %}
      {% if el in results %}
        {% set values_set = results[el] | list_to_set %}
        {% if values_set != [''] %}
        <tr>
          <td>
            <span style="color:#999;"><small>{{ el }}</small></span>
            <br>{{ results['_labels_'][el] }}
          </td>
          {% for value in results[el] %}
          <td style="text-align: right;">
            {{ value['formatted'] | format_blanks }}
          </td>
          {% endfor %}
        </tr>
        {% endif %}
      {% endif %}
    {% endfor %}
    ''')
    return h
