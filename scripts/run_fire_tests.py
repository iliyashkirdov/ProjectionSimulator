import math
import sys
from pprint import pprint

sys.path.insert(0, '.')
from calculations import run_projection
import csv
import os


def approx(a, b, tol=1e-6):
    return abs(a-b) <= tol


def ensure_defaults(assumptions: dict):
    # run_projection expects certain keys; tests set most, but ensure this default
    assumptions.setdefault('monthly_rent', 0)
    return assumptions


def test_brokerage_withdrawal():
    assumptions = {
        'start_year': 2026,
        'end_year': 2028,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 100000,
        'current_crypto': 0,
        'current_401k': 0,
        'current_roth_balance': 0,
        'portfolio_return': 0.10,
        'dividend_yield': 0.0,
    }
    events = [{'type': 'Withdraw from Brokerage', 'year': 2026, 'amount': 50000}]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    p0 = df.iloc[0]['Portfolio']
    p1 = df.iloc[1]['Portfolio']
    # After withdrawing 50k, portfolio should be 50k then grow 10% => 55k at end of 2026
    # Then grow another 10% => 60.5k at end of 2027
    assert math.isclose(p0, 50000 * 1.10, rel_tol=1e-6), f"p0 {p0} != expected {50000*1.10}"
    assert math.isclose(p1, 50000 * 1.10 * 1.10, rel_tol=1e-6), f"p1 {p1} != expected {50000*1.10*1.10}"
    print('test_brokerage_withdrawal: PASS')


def test_crypto_withdrawal():
    assumptions = {
        'start_year': 2026,
        'end_year': 2028,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 0,
        'current_crypto': 100000,
        'current_401k': 0,
        'current_roth_balance': 0,
        'crypto_return': 0.20,
        'portfolio_return': 0.0,
        'dividend_yield': 0.0,
    }
    events = [{'type': 'Withdraw from Crypto', 'year': 2026, 'amount': 25000}]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    c0 = df.iloc[0]['Crypto']
    c1 = df.iloc[1]['Crypto']
    # After withdrawing 25k, crypto = 75k grows at 20% => 90k; then 108k
    assert math.isclose(c0, 75000 * 1.20, rel_tol=1e-6)
    assert math.isclose(c1, 75000 * 1.20 * 1.20, rel_tol=1e-6)
    print('test_crypto_withdrawal: PASS')


def test_roth_conversion_behavior():
    assumptions = {
        'start_year': 2026,
        'end_year': 2027,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 0,
        'current_crypto': 0,
        'current_401k': 100000,
        'current_roth_balance': 10000,
        'portfolio_return': 0.10,
        'dividend_yield': 0.0,
    }
    events = [{'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2026, 'amount': 20000}]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    ro0 = df.iloc[0]['Roth_Balance']
    tr0 = df.iloc[0]['Trad_Retirement']
    # Conversion should move 20k from trad to roth, then roth grows at 10% this year
    expected_roth = (10000 + 20000) * 1.10
    expected_trad = (100000 - 20000) * 1.10  # trad also grows on remaining
    assert math.isclose(ro0, expected_roth, rel_tol=1e-6), f"ro0 {ro0} != {expected_roth}"
    assert math.isclose(tr0, expected_trad, rel_tol=1e-6), f"tr0 {tr0} != {expected_trad}"
    print('test_roth_conversion_behavior: PASS')


def test_401k_withdrawal_penalty():
    assumptions = {
        'start_year': 2026,
        'end_year': 2026,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 0,
        'current_crypto': 0,
        'current_401k': 50000,
        'current_roth_balance': 0,
        'portfolio_return': 0.0,
        'dividend_yield': 0.0,
    }
    events = [{'type': 'Withdraw from 401k/IRA', 'year': 2026, 'amount': 10000}]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    penalties = df.iloc[0]['Event_Penalties_Paid']
    # Under age 59.5 (age 36), penalty should be 10% of withdrawal = 1000
    assert math.isclose(penalties, 1000.0, rel_tol=1e-6)
    print('test_401k_withdrawal_penalty: PASS')


def test_percent_based_withdrawal():
    assumptions = {
        'start_year': 2026,
        'end_year': 2028,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 200000,
        'current_crypto': 0,
        'current_401k': 0,
        'current_roth_balance': 0,
        'portfolio_return': 0.05,
        'dividend_yield': 0.0,
    }
    # 25% withdrawal in 2026 (percent-based)
    events = [{'type': 'Withdraw from Brokerage', 'year': 2026, 'amount_pct': 25}]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    p0 = df.iloc[0]['Portfolio']
    # starting portfolio 200k - 25% = 150k, grows 5% => 157.5k
    assert math.isclose(p0, 150000 * 1.05, rel_tol=1e-6)
    print('test_percent_based_withdrawal: PASS')


def test_conversion_ladder():
    assumptions = {
        'start_year': 2026,
        'end_year': 2028,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 0,
        'current_crypto': 0,
        'current_401k': 100000,
        'current_roth_balance': 0,
        'portfolio_return': 0.05,
        'dividend_yield': 0.0,
    }
    events = [
        {'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2026, 'amount': 20000},
        {'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2027, 'amount': 10000},
    ]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    ro0 = df.iloc[0]['Roth_Balance']
    ro1 = df.iloc[1]['Roth_Balance']
    # After 2026: (0+20k)*1.05 = 21k; After 2027: (21k + 10k)*1.05 = 32,550
    assert math.isclose(ro0, 20000 * 1.05, rel_tol=1e-6)
    assert math.isclose(ro1, 32550.0, rel_tol=1e-6)
    print('test_conversion_ladder: PASS')


def test_percent_recurring_withdrawals():
    assumptions = {
        'start_year': 2026,
        'end_year': 2028,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 100000,
        'current_crypto': 0,
        'current_401k': 0,
        'current_roth_balance': 0,
        'portfolio_return': 0.05,
        'dividend_yield': 0.0,
    }
    # 10% percent withdrawal each year 2026-2028
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2026, 'amount_pct': 10},
        {'type': 'Withdraw from Brokerage', 'year': 2027, 'amount_pct': 10},
        {'type': 'Withdraw from Brokerage', 'year': 2028, 'amount_pct': 10},
    ]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    p0 = df.iloc[0]['Portfolio']
    # 100k -> 90k -> *1.05 => 94.5k
    assert math.isclose(p0, 90000 * 1.05, rel_tol=1e-6)
    print('test_percent_recurring_withdrawals: PASS')


def test_brokerage_then_401k_ordering():
    assumptions = {
        'start_year': 2026,
        'end_year': 2026,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 50000,
        'current_crypto': 0,
        'current_401k': 50000,
        'current_roth_balance': 0,
        'portfolio_return': 0.0,
        'dividend_yield': 0.0,
    }
    # Withdraw brokerage then 401k in same year
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2026, 'amount': 30000},
        {'type': 'Withdraw from 401k/IRA', 'year': 2026, 'amount': 20000},
    ]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    portfolio_end = df.iloc[0]['Portfolio']
    trad_end = df.iloc[0]['Trad_Retirement']
    penalties = df.iloc[0]['Event_Penalties_Paid']
    # portfolio should be 20k, trad retirement 30k, penalty 10% of 20k = 2000
    assert math.isclose(portfolio_end, 20000.0, rel_tol=1e-6)
    assert math.isclose(trad_end, 30000.0, rel_tol=1e-6)
    assert math.isclose(penalties, 2000.0, rel_tol=1e-6)
    print('test_brokerage_then_401k_ordering: PASS')


def test_mixed_income_streams():
    assumptions = {
        'start_year': 2026,
        'end_year': 2027,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 80000,
        'current_crypto': 40000,
        'current_401k': 0,
        'current_roth_balance': 0,
        'portfolio_return': 0.05,
        'crypto_return': 0.20,
        'dividend_yield': 0.0,
    }
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2026, 'amount': 20000},
        {'type': 'Withdraw from Crypto', 'year': 2026, 'amount': 10000},
    ]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    p0 = df.iloc[0]['Portfolio']
    c0 = df.iloc[0]['Crypto']
    assert math.isclose(p0, 60000 * 1.05, rel_tol=1e-6)
    assert math.isclose(c0, 30000 * 1.20, rel_tol=1e-6)
    print('test_mixed_income_streams: PASS')


def test_safe_withdrawal_4percent():
    assumptions = {
        'start_year': 2026,
        'end_year': 2026,
        'retirement_year': 2050,
        'birth_year': 1990,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 250000,
        'current_crypto': 0,
        'current_401k': 0,
        'current_roth_balance': 0,
        'portfolio_return': 0.0,
        'dividend_yield': 0.0,
    }
    # 4% safe withdrawal as percent
    events = [{'type': 'Withdraw from Brokerage', 'year': 2026, 'amount_pct': 4}]
    ensure_defaults(assumptions)
    df = run_projection(assumptions, [], [], financial_events=events)
    p0 = df.iloc[0]['Portfolio']
    assert math.isclose(p0, 250000 * 0.96, rel_tol=1e-6)
    print('test_safe_withdrawal_4percent: PASS')


def parse_range_samples(s):
    s = str(s).strip()
    if '-' in s:
        a, b = s.split('-', 1)
        try:
            a_f = float(a)
            b_f = float(b)
            mid = (a_f + b_f) / 2.0
            return [int(a_f), int(mid), int(b_f)]
        except ValueError:
            return [s]
    else:
        try:
            v = int(float(s))
            return [v]
        except ValueError:
            return [s]


def test_scenarios_catalog():
    path = os.path.join('data', 'fire_scenarios.csv')
    if not os.path.exists(path):
        print('test_scenarios_catalog: SKIPPED (no scenarios file - this is optional)')
        return
    rows = []
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)

    count = 0
    for r in rows:
        # build up to 3 sample variants per row by sampling ranges
        port_samples = parse_range_samples(r['Current_Portfolio'])
        sal_samples = parse_range_samples(r['Current_Salary'])
        exp_samples = parse_range_samples(r['Annual_Expenses'])
        ret_samples = parse_range_samples(r['Portfolio_Return'])
        infl_samples = parse_range_samples(r['Inflation'])

        n = max(len(port_samples), len(sal_samples), len(exp_samples), len(ret_samples), len(infl_samples))
        n = min(n, 3)
        for i in range(n):
            cp = port_samples[min(i, len(port_samples)-1)]
            cs = sal_samples[min(i, len(sal_samples)-1)]
            ae = exp_samples[min(i, len(exp_samples)-1)]
            pr = float(ret_samples[min(i, len(ret_samples)-1)])
            inf = float(infl_samples[min(i, len(infl_samples)-1)])

            assumptions = {
                'start_year': 2026,
                'end_year': 2026,
                'retirement_year': 2050,
                'birth_year': 1990,
                'current_salary': cs,
                'salary_growth': 0.0,
                'contrib_401k': 0,
                'contrib_roth': 0,
                'contrib_hsa': 0,
                'contrib_brokerage': 0,
                'contrib_crypto': 0,
                'annual_expenses': ae,
                'inflation': inf,
                'current_cash': 0,
                'current_portfolio': cp,
                'current_crypto': 0,
                'current_401k': 0,
                'current_roth_balance': 0,
                'portfolio_return': pr,
                'dividend_yield': 0.0,
            }
            ensure_defaults(assumptions)
            df = run_projection(assumptions, [], [], financial_events=[])
            assert df.shape[0] > 0
            count += 1
    print(f'test_scenarios_catalog: PASS - ran {count} scenario checks')


def run_all():
    test_brokerage_withdrawal()
    test_crypto_withdrawal()
    test_roth_conversion_behavior()
    test_401k_withdrawal_penalty()
    test_percent_based_withdrawal()
    test_conversion_ladder()
    test_percent_recurring_withdrawals()
    test_brokerage_then_401k_ordering()
    test_mixed_income_streams()
    test_safe_withdrawal_4percent()
    test_scenarios_catalog()
    print('\nALL TESTS PASSED')

if __name__ == '__main__':
    run_all()
