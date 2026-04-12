"""
Comprehensive unit tests for the Financial Projection Simulator calculation engine.
Tests cover: tax calculations, mortgage math, investment growth, cash flow, 
cost basis tracking, retirement accounts, rental properties, and financial events.
"""
import math
import sys

sys.path.insert(0, '.')
from calculations import (
    run_projection,
    calculate_federal_tax,
    calculate_sc_state_tax,
    calculate_ma_state_tax,
    calculate_fica_tax,
    calculate_mortgage_payment,
    get_remaining_balance,
)


def make_assumptions(**overrides):
    """Create a minimal valid assumptions dict with all required keys."""
    defaults = {
        'start_year': 2026,
        'end_year': 2026,
        'retirement_year': 2050,
        'birth_year': 1990,
        'filing_status': 'Single',
        'state': 'No Income Tax (TX, FL, WA, etc.)',
        'state_tax_rate': 0,
        'current_salary': 0,
        'salary_growth': 0.0,
        'contrib_401k': 0,
        'employer_401k': 0,
        'contrib_roth': 0,
        'contrib_hsa': 0,
        'employer_hsa': 0,
        'contrib_brokerage': 0,
        'contrib_crypto': 0,
        'annual_expenses': 0,
        'monthly_rent': 0,
        'inflation': 0.0,
        'current_cash': 0,
        'current_portfolio': 0,
        'current_crypto': 0,
        'current_401k': 0,
        'current_roth_balance': 0,
        'current_roth_contributions': 0,
        'roth_first_contrib_year': 2020,
        'current_hsa': 0,
        'portfolio_return': 0.0,
        'crypto_return': 0.0,
        'dividend_yield': 0.0,
        'property_appreciation': 0.03,
        'rent_growth': 0.03,
        'vacancy_rate': 0.05,
        'property_tax_rate': 0.012,
        'insurance_rate': 0.005,
        'maintenance_rate': 0.01,
        'management_fee': 0.08,
        'cash_savings_rate': 0.0,
    }
    defaults.update(overrides)
    return defaults


def close(a, b, tol=0.01):
    """Check if two numbers are approximately equal (default $0.01 tolerance)."""
    return abs(a - b) <= tol


def run1(assumptions, properties=None, debts=None, events=None):
    """Run a single-year projection and return the first row as dict."""
    df = run_projection(assumptions, properties or [], debts or [], financial_events=events or [])
    return df.iloc[0].to_dict()


# ============================================
# FEDERAL TAX BRACKET TESTS
# ============================================

def test_federal_tax_zero_income():
    assert calculate_federal_tax(0, 'Single') == 0
    assert calculate_federal_tax(-1000, 'Single') == 0
    print('test_federal_tax_zero_income: PASS')


def test_federal_tax_single_10pct_bracket():
    # $10,000 taxable income, all in 10% bracket (Single: 0-12,400)
    tax = calculate_federal_tax(10000, 'Single')
    assert close(tax, 10000 * 0.10), f"Expected $1000, got ${tax:.2f}"
    print('test_federal_tax_single_10pct_bracket: PASS')


def test_federal_tax_single_12pct_bracket():
    # $30,000 taxable income: 12,400 @ 10% + 17,600 @ 12%
    tax = calculate_federal_tax(30000, 'Single')
    expected = 12400 * 0.10 + (30000 - 12400) * 0.12
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_federal_tax_single_12pct_bracket: PASS')


def test_federal_tax_single_22pct_bracket():
    # $80,000 taxable: 12,400@10% + (50,400-12,400)@12% + (80,000-50,400)@22%
    tax = calculate_federal_tax(80000, 'Single')
    expected = 12400 * 0.10 + (50400 - 12400) * 0.12 + (80000 - 50400) * 0.22
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_federal_tax_single_22pct_bracket: PASS')


def test_federal_tax_married_jointly():
    # $60,000 taxable (MFJ): 24,800@10% + (60,000-24,800)@12%
    tax = calculate_federal_tax(60000, 'Married Filing Jointly')
    expected = 24800 * 0.10 + (60000 - 24800) * 0.12
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_federal_tax_married_jointly: PASS')


def test_federal_tax_head_of_household():
    # $50,000 taxable (HoH): 17,700@10% + (50,000-17,700)@12%
    tax = calculate_federal_tax(50000, 'Head of Household')
    expected = 17700 * 0.10 + (50000 - 17700) * 0.12
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_federal_tax_head_of_household: PASS')


def test_federal_tax_high_income():
    # $700,000 taxable (Single): tests up through 37% bracket
    tax = calculate_federal_tax(700000, 'Single')
    expected = (12400 * 0.10 + (50400 - 12400) * 0.12 + (105700 - 50400) * 0.22 +
                (201775 - 105700) * 0.24 + (256225 - 201775) * 0.32 +
                (640600 - 256225) * 0.35 + (700000 - 640600) * 0.37)
    assert close(tax, expected, tol=1.0), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_federal_tax_high_income: PASS')


# ============================================
# SC STATE TAX TESTS
# ============================================

def test_sc_tax_zero_bracket():
    # Income below $3,560 = 0%
    assert calculate_sc_state_tax(3000, 2026) == 0
    assert calculate_sc_state_tax(3560, 2026) == 0
    print('test_sc_tax_zero_bracket: PASS')


def test_sc_tax_3pct_bracket():
    # Income $10,000: $3,560 @0% + ($10,000 - $3,560) @3%
    tax = calculate_sc_state_tax(10000, 2026)
    expected = (10000 - 3560) * 0.03
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_sc_tax_3pct_bracket: PASS')


def test_sc_tax_top_bracket_2026():
    # Income $50,000 in 2026 (top rate = 6.0%)
    tax = calculate_sc_state_tax(50000, 2026)
    expected = (17830 - 3560) * 0.03 + (50000 - 17830) * 0.06
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_sc_tax_top_bracket_2026: PASS')


def test_sc_tax_top_bracket_2025():
    # 2025 top rate = 6.2%
    tax = calculate_sc_state_tax(50000, 2025)
    expected = (17830 - 3560) * 0.03 + (50000 - 17830) * 0.062
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_sc_tax_top_bracket_2025: PASS')


# ============================================
# MA STATE TAX TESTS
# ============================================

def test_ma_tax_zero_bracket():
    # Income below $8,000 = 0%
    assert calculate_ma_state_tax(6000, 2026) == 0
    assert calculate_ma_state_tax(8000, 2026) == 0
    print('test_ma_tax_zero_bracket: PASS')


def test_ma_tax_5pct_bracket():
    # Income $10,000: $8,000 @0% + ($10,000 - $8,000) @5%
    tax = calculate_ma_state_tax(10000, 2026)
    expected = (10000 - 8000) * 0.05
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_ma_tax_5pct_bracket: PASS')


def test_ma_tax_top_bracket_2026():
    # Income $2,000,000 in 2026 (top rate = 9.0%)
    tax = calculate_ma_state_tax(2000000, 2026)
    expected = (2000000 - 1083150) * 0.09 + (1083150 - 8000) * 0.05
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_ma_tax_top_bracket_2026: PASS')


def test_ma_tax_top_bracket_2024():
    # Income $2,000,000 in 2025 (top rate = 9.0%)
    tax = calculate_ma_state_tax(2000000, 2024)
    expected = (2000000 - 1053750) * 0.09 + (1053750 - 8000) * 0.05
    assert close(tax, expected), f"Expected ${expected:.2f}, got ${tax:.2f}"
    print('test_sc_tax_top_bracket_2024: PASS')


# ============================================
# FICA TAX TESTS
# ============================================

def test_fica_below_ss_cap():
    ss, med, total = calculate_fica_tax(100000)
    expected_ss = 100000 * 0.062
    expected_med = 100000 * 0.0145
    assert close(ss, expected_ss)
    assert close(med, expected_med)
    assert close(total, expected_ss + expected_med)
    print('test_fica_below_ss_cap: PASS')


def test_fica_above_ss_cap():
    # Income above $176,100 SS cap
    ss, med, total = calculate_fica_tax(200000)
    expected_ss = 176100 * 0.062
    expected_med = 200000 * 0.0145
    assert close(ss, expected_ss)
    assert close(med, expected_med)
    print('test_fica_above_ss_cap: PASS')


def test_fica_additional_medicare():
    # Income above $200,000: additional 0.9% Medicare
    ss, med, total = calculate_fica_tax(300000)
    expected_ss = 176100 * 0.062
    expected_med = 300000 * 0.0145 + (300000 - 200000) * 0.009
    assert close(med, expected_med), f"Expected ${expected_med:.2f}, got ${med:.2f}"
    print('test_fica_additional_medicare: PASS')


# ============================================
# MORTGAGE MATH TESTS
# ============================================

def test_mortgage_payment_basic():
    # $300,000 loan, 7% rate, 30 years
    pmt = calculate_mortgage_payment(300000, 0.07, 30)
    # Expected ~$1,995.91/month
    assert 1990 < pmt < 2000, f"Monthly payment ${pmt:.2f} out of expected range"
    print('test_mortgage_payment_basic: PASS')


def test_mortgage_payment_zero_loan():
    assert calculate_mortgage_payment(0, 0.07, 30) == 0
    print('test_mortgage_payment_zero_loan: PASS')


def test_mortgage_payment_zero_rate():
    assert calculate_mortgage_payment(300000, 0, 30) == 0
    print('test_mortgage_payment_zero_rate: PASS')


def test_remaining_balance_start():
    # At month 0, balance = original loan
    bal = get_remaining_balance(300000, 0.07, 30, 0)
    assert close(bal, 300000), f"Expected $300,000, got ${bal:.2f}"
    print('test_remaining_balance_start: PASS')


def test_remaining_balance_end():
    # After all 360 months, balance = 0
    bal = get_remaining_balance(300000, 0.07, 30, 360)
    assert close(bal, 0, tol=1.0), f"Expected ~$0, got ${bal:.2f}"
    print('test_remaining_balance_end: PASS')


def test_remaining_balance_midpoint():
    # After half the payments, balance should be well above half the loan
    # (front-loaded interest means balance decreases slowly at first)
    bal = get_remaining_balance(300000, 0.07, 30, 180)
    assert 180000 < bal < 260000, f"Midpoint balance ${bal:.2f} out of expected range"
    print('test_remaining_balance_midpoint: PASS')


# ============================================
# SALARY & INCOME GROWTH TESTS
# ============================================

def test_salary_growth_compound():
    a = make_assumptions(current_salary=100000, salary_growth=0.05, end_year=2030)
    df = run_projection(a, [], [], [])
    # Year 2030 = index 4, salary should be 100000 * 1.05^4
    row4 = df.iloc[4]
    expected = 100000 * (1.05 ** 4)
    assert close(row4['Gross_Salary'], expected, tol=1.0), f"Expected ${expected:.0f}, got ${row4['Gross_Salary']:.0f}"
    print('test_salary_growth_compound: PASS')


def test_salary_stops_at_retirement():
    a = make_assumptions(current_salary=100000, retirement_year=2028, end_year=2030)
    df = run_projection(a, [], [], [])
    # 2028 should have 0 salary (retirement year)
    row_2028 = df[df['Year'] == 2028].iloc[0]
    assert close(row_2028['Gross_Salary'], 0), f"Expected $0 salary in retirement, got ${row_2028['Gross_Salary']:.0f}"
    print('test_salary_stops_at_retirement: PASS')


# ============================================
# INFLATION TESTS
# ============================================

def test_expense_inflation():
    a = make_assumptions(annual_expenses=40000, inflation=0.03, end_year=2031)
    df = run_projection(a, [], [], [])
    # Year 2031 = index 5, expenses should be 40000 * 1.03^5
    row5 = df.iloc[5]
    expected = 40000 * (1.03 ** 5)
    assert close(row5['Living_Expenses'], expected, tol=1.0), f"Expected ${expected:.0f}, got ${row5['Living_Expenses']:.0f}"
    print('test_expense_inflation: PASS')


def test_rent_inflation():
    a = make_assumptions(monthly_rent=1500, inflation=0.025, end_year=2029)
    df = run_projection(a, [], [], [])
    # Year 2029 = index 3, rent = 1500 * 12 * 1.025^3
    row3 = df.iloc[3]
    expected = 1500 * 12 * (1.025 ** 3)
    assert close(row3['Living_Expenses'], expected, tol=1.0)
    print('test_rent_inflation: PASS')


# ============================================
# INVESTMENT GROWTH TESTS
# ============================================

def test_portfolio_growth_no_dividends():
    a = make_assumptions(current_portfolio=100000, portfolio_return=0.10, dividend_yield=0.0)
    r = run1(a)
    # Portfolio grows 10%, end of year = 100000 * 1.10
    assert close(r['Portfolio'], 110000, tol=1.0), f"Expected $110,000, got ${r['Portfolio']:.2f}"
    print('test_portfolio_growth_no_dividends: PASS')


def test_portfolio_growth_with_dividends():
    """Total return = portfolio_return. Dividends come FROM it, not on top."""
    a = make_assumptions(current_portfolio=100000, portfolio_return=0.10, dividend_yield=0.03)
    r = run1(a)
    # Growth = 100000 * (0.10 - 0.03) = 7000 (capital appreciation)
    # Dividends = 100000 * 0.03 = 3000 (goes to cash after tax)
    # Portfolio end = 100000 + 7000 = 107000
    assert close(r['Portfolio'], 107000, tol=1.0), f"Expected $107,000, got ${r['Portfolio']:.2f}"
    assert close(r['Dividends'], 3000, tol=1.0), f"Expected $3,000 dividends, got ${r['Dividends']:.2f}"
    print('test_portfolio_growth_with_dividends: PASS')


def test_dividend_tax():
    """Dividends should be taxed at 15%."""
    a = make_assumptions(current_portfolio=200000, portfolio_return=0.10, dividend_yield=0.02)
    r = run1(a)
    expected_div = 200000 * 0.02
    expected_tax = expected_div * 0.15
    assert close(r['Dividends'], expected_div, tol=1.0)
    assert close(r['Dividend_Tax'], expected_tax, tol=1.0)
    print('test_dividend_tax: PASS')


def test_crypto_growth():
    a = make_assumptions(current_crypto=50000, crypto_return=0.20)
    r = run1(a)
    assert close(r['Crypto'], 60000, tol=1.0)
    print('test_crypto_growth: PASS')


def test_401k_growth_with_employer_match():
    a = make_assumptions(
        current_salary=100000, current_401k=50000,
        contrib_401k=10000, employer_401k=5000,
        portfolio_return=0.08,
    )
    r = run1(a)
    # Growth on 50k, then add employee + employer = 10k + 5k
    expected = 50000 * 1.08 + 15000
    assert close(r['Trad_Retirement'], expected, tol=1.0), f"Expected ${expected:.0f}, got ${r['Trad_Retirement']:.0f}"
    print('test_401k_growth_with_employer_match: PASS')


def test_roth_growth_with_contribution():
    a = make_assumptions(
        current_salary=100000, current_roth_balance=20000,
        current_roth_contributions=15000, contrib_roth=7000,
        portfolio_return=0.07,
    )
    r = run1(a)
    # Roth: 20000 * 1.07 + 7000 = 28,400
    expected = 20000 * 1.07 + 7000
    assert close(r['Roth_Balance'], expected, tol=1.0)
    # Contributions basis: 15000 + 7000 = 22000
    assert close(r['Roth_Contributions'], 22000, tol=1.0)
    print('test_roth_growth_with_contribution: PASS')


def test_hsa_growth_with_employer():
    a = make_assumptions(
        current_salary=100000, current_hsa=5000,
        contrib_hsa=3000, employer_hsa=1000,
        portfolio_return=0.06,
    )
    r = run1(a)
    expected = 5000 * 1.06 + 4000
    assert close(r['HSA_Balance'], expected, tol=1.0)
    print('test_hsa_growth_with_employer: PASS')


def test_multi_year_compound_growth():
    """Verify compounding works correctly over multiple years."""
    a = make_assumptions(current_portfolio=100000, portfolio_return=0.10, end_year=2030)
    df = run_projection(a, [], [], [])
    # After 5 years (2026-2030), portfolio = 100000 * 1.10^5
    row4 = df.iloc[4]
    expected = 100000 * (1.10 ** 5)
    assert close(row4['Portfolio'], expected, tol=10.0), f"Expected ${expected:.0f}, got ${row4['Portfolio']:.0f}"
    print('test_multi_year_compound_growth: PASS')


# ============================================
# COST BASIS TRACKING TESTS
# ============================================

def test_cost_basis_initial_no_gains():
    """Initial cost basis = portfolio value, so first withdrawal has 0% gains."""
    a = make_assumptions(current_portfolio=100000, portfolio_return=0.0)
    events = [{'type': 'Withdraw from Brokerage', 'year': 2026, 'amount': 50000}]
    r = run1(a, events=events)
    # No gains (cost basis = portfolio), so no cap gains tax
    assert close(r['Event_Taxes_Paid'], 0, tol=1.0)
    assert close(r['Portfolio'], 50000, tol=1.0)
    print('test_cost_basis_initial_no_gains: PASS')


def test_cost_basis_after_growth():
    """After growth, withdrawals have proportional gains."""
    a = make_assumptions(current_portfolio=100000, portfolio_return=0.50, end_year=2027)
    # Year 1: portfolio grows 50% to 150,000 (cost basis still 100,000)
    # Year 2: withdraw 75,000 — gains ratio = (150000-100000)/150000 = 1/3
    events = [{'type': 'Withdraw from Brokerage', 'year': 2027, 'amount': 75000}]
    df = run_projection(a, [], [], financial_events=events)
    row1 = df.iloc[1]
    # Gains ratio = 50000/150000 = 1/3
    # Gains portion = 75000 * 1/3 = 25000
    # Cap gains tax = 25000 * 0.15 = 3750
    assert close(row1['Event_Taxes_Paid'], 3750, tol=1.0), f"Expected $3750, got ${row1['Event_Taxes_Paid']:.2f}"
    print('test_cost_basis_after_growth: PASS')


def test_cost_basis_with_contributions():
    """Contributions increase cost basis, reducing gains ratio."""
    a = make_assumptions(
        current_salary=200000, current_portfolio=100000,
        portfolio_return=0.0, contrib_brokerage=50000, end_year=2027,
    )
    # Year 1: portfolio = 100000 + 50000 = 150000, cost basis = 100000 + 50000 = 150000
    # Year 2: withdraw 150000 — gains ratio = 0 (basis = value)
    events = [{'type': 'Withdraw from Brokerage', 'year': 2027, 'amount': 150000}]
    df = run_projection(a, [], [], financial_events=events)
    row1 = df.iloc[1]
    assert close(row1['Event_Taxes_Paid'], 0, tol=1.0)
    print('test_cost_basis_with_contributions: PASS')


def test_crypto_cost_basis():
    """Same cost basis logic applies to crypto."""
    a = make_assumptions(current_crypto=50000, crypto_return=1.0, end_year=2027)
    # Year 1: crypto doubles to 100,000 (basis = 50,000)
    # Year 2: withdraw 50,000 — gains ratio = 50000/100000 = 50%
    events = [{'type': 'Withdraw from Crypto', 'year': 2027, 'amount': 50000}]
    df = run_projection(a, [], [], financial_events=events)
    row1 = df.iloc[1]
    gains = 50000 * 0.50
    expected_tax = gains * 0.15
    # Event_Taxes_Paid includes cap gains tax (no penalties for crypto)
    assert close(row1['Event_Taxes_Paid'], expected_tax, tol=1.0), f"Expected ${expected_tax}, got ${row1['Event_Taxes_Paid']:.2f}"
    print('test_crypto_cost_basis: PASS')


# ============================================
# RENTAL PROPERTY TESTS
# ============================================

def test_rental_income_basic():
    """Basic rental property income and expenses."""
    a = make_assumptions(
        current_salary=100000, property_appreciation=0.0, rent_growth=0.0,
        vacancy_rate=0.0, insurance_rate=0.005, maintenance_rate=0.01,
        management_fee=0.0, property_tax_rate=0.01,
    )
    prop = {
        'purchase_price': 200000, 'down_payment_pct': 1.0,  # all cash, no mortgage
        'mortgage_rate': 0.0, 'mortgage_years': 30,
        'is_primary': False, 'purchase_year': 2025,  # already owned
        'rent_per_unit': 1500, 'num_units': 1,
        'other_monthly_income': 0, 'vacancy_rate': 0.0,
        'insurance_monthly': 100, 'capex_rate': 0.05,
        'management_rate': 0.0, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
        'property_tax_rate': 0.01,
    }
    r = run1(a, properties=[prop])
    # Gross rent = 1500 * 12 = 18000
    # Insurance = 100 * 12 = 1200
    # Capex = 18000 * 0.05 = 900
    # Property tax = 200000 * 0.01 = 2000
    # Total expenses (excluding mortgage interest since 100% down) = 1200 + 900 + 2000 = 4100
    # Net rental = 18000 - 4100 = 13900
    assert close(r['Rental_Income'], 18000, tol=1.0), f"Expected $18,000, got ${r['Rental_Income']:.0f}"
    assert close(r['Net_Rental'], 13900, tol=100.0), f"Expected ~$13,900, got ${r['Net_Rental']:.0f}"
    print('test_rental_income_basic: PASS')


def test_rental_income_in_agi():
    """Rental income should be included in AGI and taxed at marginal rates."""
    a = make_assumptions(
        current_salary=100000, filing_status='Single',
        state='No Income Tax (TX, FL, WA, etc.)',
        property_appreciation=0.0, rent_growth=0.0,
    )
    # First run: no rental property
    r_no_rental = run1(a)
    # Second run: with rental property generating $18K net taxable income
    prop = {
        'purchase_price': 200000, 'down_payment_pct': 1.0,
        'mortgage_rate': 0.0, 'mortgage_years': 30,
        'is_primary': False, 'purchase_year': 2025,
        'rent_per_unit': 1500, 'num_units': 1,
        'other_monthly_income': 0, 'vacancy_rate': 0.0,
        'insurance_monthly': 0, 'capex_rate': 0.0,
        'management_rate': 0.0, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
        'property_tax_rate': 0.0,
    }
    r_rental = run1(a, properties=[prop])
    # Rental should increase AGI and therefore increase federal tax
    assert r_rental['AGI'] > r_no_rental['AGI'], "AGI should be higher with rental income"
    assert r_rental['Federal_Tax'] > r_no_rental['Federal_Tax'], "Federal tax should be higher with rental income"
    print('test_rental_income_in_agi: PASS')


def test_primary_residence_replaces_rent():
    """Buying a primary home should eliminate rent expense."""
    a = make_assumptions(monthly_rent=2000)
    r_renting = run1(a)
    prop = {
        'purchase_price': 300000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'is_primary': True, 'purchase_year': 2025,
    }
    r_owning = run1(a, properties=[prop])
    # Renting: living expenses = 2000 * 12 = 24000
    assert close(r_renting['Living_Expenses'], 24000, tol=1.0)
    # Owning: rent = 0, but housing cost includes mortgage + property tax
    assert r_owning['Living_Expenses'] < r_renting['Living_Expenses']
    assert r_owning['Housing_Cost'] > 0
    print('test_primary_residence_replaces_rent: PASS')


# ============================================
# TAX DEDUCTION TESTS
# ============================================

def test_standard_deduction_used():
    """When itemized < standard, standard deduction is used."""
    a = make_assumptions(current_salary=80000, filing_status='Single')
    r = run1(a)
    assert r['Using_Itemized'] == False
    assert close(r['Actual_Deduction'], 15000, tol=1.0)
    print('test_standard_deduction_used: PASS')


def test_itemized_deduction_used():
    """When mortgage interest + SALT > standard, itemized is used."""
    a = make_assumptions(
        current_salary=150000, filing_status='Single',
        state='Other', state_tax_rate=0.06,
    )
    # Primary with big mortgage = big interest deduction
    prop = {
        'purchase_price': 600000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'is_primary': True, 'purchase_year': 2025,
    }
    r = run1(a, properties=[prop])
    # Mortgage interest on ~$480K loan at 7% ≈ ~$33K/year
    # SALT capped at $10K
    # Itemized = ~$33K + $10K = ~$43K > $15K standard
    assert r['Using_Itemized'] == True, f"Expected itemized deduction, got standard. Itemized: ${r['Itemized_Deduction']:,.0f}"
    print('test_itemized_deduction_used: PASS')


def test_salt_cap_10k():
    """SALT deduction should be capped at $10,000."""
    a = make_assumptions(
        current_salary=300000, filing_status='Single',
        state='Other', state_tax_rate=0.10,
    )
    r = run1(a)
    # State tax on $300K income would be way over $10K
    # SALT should be capped at $10K
    assert r['SALT_Deduction'] <= 10000, f"SALT ${r['SALT_Deduction']:,.0f} exceeds $10,000 cap"
    print('test_salt_cap_10k: PASS')


def test_pretax_deductions_reduce_tax():
    """401k and HSA contributions should reduce taxable income."""
    a_no_deductions = make_assumptions(current_salary=100000, filing_status='Single')
    a_with_deductions = make_assumptions(
        current_salary=100000, filing_status='Single',
        contrib_401k=23000, contrib_hsa=4000,
    )
    r_none = run1(a_no_deductions)
    r_pretax = run1(a_with_deductions)
    # Pre-tax deductions should lower AGI and therefore lower tax
    assert r_pretax['AGI'] < r_none['AGI'], "AGI should be lower with pretax deductions"
    assert r_pretax['Federal_Tax'] < r_none['Federal_Tax'], "Federal tax should be lower"
    assert r_pretax['Tax_Savings_PreTax'] > 0, "Should show tax savings from pretax"
    print('test_pretax_deductions_reduce_tax: PASS')


# ============================================
# FINANCIAL EVENT TESTS
# ============================================

def test_roth_conversion_increases_agi():
    """Roth conversion should be taxable as ordinary income."""
    a = make_assumptions(current_401k=200000)
    events_none = []
    events_conv = [{'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2026, 'amount': 50000}]
    r_none = run1(a, events=events_none)
    r_conv = run1(a, events=events_conv)
    assert r_conv['AGI'] == r_none['AGI'] + 50000, "Conversion should add to AGI"
    assert r_conv['Federal_Tax'] > r_none['Federal_Tax']
    print('test_roth_conversion_increases_agi: PASS')


def test_roth_conversion_5year_tracking():
    """Roth conversions should be tracked for 5-year rule."""
    a = make_assumptions(current_401k=100000, portfolio_return=0.0, end_year=2032)
    events = [{'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2026, 'amount': 20000}]
    df = run_projection(a, [], [], financial_events=events)
    # After 5 years (2031), seasoned conversion should be available
    row_2031 = df[df['Year'] == 2031].iloc[0]
    assert row_2031['Seasoned_Conversions_Avail'] >= 20000, "Conversion should be seasoned after 5 years"
    # Before 5 years (2030), not yet seasoned
    row_2030 = df[df['Year'] == 2030].iloc[0]
    assert row_2030['Seasoned_Conversions_Avail'] == 0, "Conversion should NOT be seasoned before 5 years"
    print('test_roth_conversion_5year_tracking: PASS')


def test_roth_withdrawal_contributions_first():
    """Roth withdrawals use contributions first (tax-free)."""
    a = make_assumptions(
        current_roth_balance=50000, current_roth_contributions=30000,
        portfolio_return=0.0,
    )
    events = [{'type': 'Withdraw from Roth', 'year': 2026, 'amount': 20000}]
    r = run1(a, events=events)
    # $20K withdrawal from $30K contributions = $0 tax, $0 penalty
    assert close(r['Event_Penalties_Paid'], 0)
    assert close(r['Roth_Contributions'], 10000, tol=1.0)  # 30k - 20k = 10k remaining
    print('test_roth_withdrawal_contributions_first: PASS')


def test_roth_withdrawal_earnings_taxed_under_59():
    """Withdrawals from Roth earnings under 59.5 are taxed + 10% penalty."""
    a = make_assumptions(
        birth_year=1990,  # age 36 in 2026
        current_roth_balance=50000, current_roth_contributions=10000,
        portfolio_return=0.0,
    )
    # Withdraw more than contributions — remainder comes from earnings
    events = [{'type': 'Withdraw from Roth', 'year': 2026, 'amount': 30000}]
    r = run1(a, events=events)
    # $10K from contributions (tax-free) + $20K from earnings (taxed + penalty)
    # Penalty = $20K * 10% = $2,000
    assert close(r['Event_Penalties_Paid'], 2000, tol=1.0), f"Expected $2000 penalty, got ${r['Event_Penalties_Paid']:.2f}"
    print('test_roth_withdrawal_earnings_taxed_under_59: PASS')


def test_401k_withdrawal_no_penalty_after_59():
    """401k withdrawal after 59.5 has no penalty."""
    a = make_assumptions(
        birth_year=1966,  # age 60 in 2026
        current_401k=200000,
    )
    events = [{'type': 'Withdraw from 401k/IRA', 'year': 2026, 'amount': 50000}]
    r = run1(a, events=events)
    assert close(r['Event_Penalties_Paid'], 0)
    print('test_401k_withdrawal_no_penalty_after_59: PASS')


def test_401k_withdrawal_penalty_under_59():
    """401k withdrawal under 59.5 has 10% penalty."""
    a = make_assumptions(
        birth_year=1990,  # age 36 in 2026
        current_401k=200000,
    )
    events = [{'type': 'Withdraw from 401k/IRA', 'year': 2026, 'amount': 50000}]
    r = run1(a, events=events)
    assert close(r['Event_Penalties_Paid'], 5000, tol=1.0)
    print('test_401k_withdrawal_penalty_under_59: PASS')


def test_percent_withdrawal_normalization():
    """Percentage-based withdrawal: values > 1 treated as percent (e.g., 10 = 10%)."""
    a = make_assumptions(current_portfolio=200000, portfolio_return=0.0)
    # 10 = 10% of portfolio
    events = [{'type': 'Withdraw from Brokerage', 'year': 2026, 'amount_pct': 10}]
    r = run1(a, events=events)
    assert close(r['Portfolio'], 180000, tol=1.0)
    print('test_percent_withdrawal_normalization: PASS')


def test_percent_withdrawal_decimal():
    """Percentage-based withdrawal: values <= 1 treated as fraction (e.g., 0.10 = 10%)."""
    a = make_assumptions(current_portfolio=200000, portfolio_return=0.0)
    events = [{'type': 'Withdraw from Brokerage', 'year': 2026, 'amount_pct': 0.10}]
    r = run1(a, events=events)
    assert close(r['Portfolio'], 180000, tol=1.0)
    print('test_percent_withdrawal_decimal: PASS')


# ============================================
# CASH FLOW INTEGRITY TESTS
# ============================================

def test_cash_flow_balance():
    """net_cash_flow = cash_inflow - cash_outflow - cash_savings (when positive)."""
    a = make_assumptions(
        current_salary=100000, annual_expenses=30000,
        monthly_rent=1500, cash_savings_rate=0.10,
    )
    r = run1(a)
    expected_net = r['Discretionary_Cash'] - r['Cash_Savings']
    assert close(r['Net_Cash_Flow'], expected_net, tol=1.0)
    print('test_cash_flow_balance: PASS')


def test_cash_updates_by_net_cash_flow():
    """Cash balance should change by exactly net_cash_flow each year."""
    a = make_assumptions(
        current_cash=10000, current_salary=100000,
        annual_expenses=30000, monthly_rent=1000,
        end_year=2027,
    )
    df = run_projection(a, [], [], [])
    for i in range(1, len(df)):
        prev_cash = df.iloc[i-1]['Cash']
        curr_cash = df.iloc[i]['Cash']
        net_flow = df.iloc[i]['Net_Cash_Flow']
        # Cash should equal previous cash + this year's net flow
        # (only approximately because cash from year 0 includes initial + first year flow)
        if i > 0:
            assert close(curr_cash, prev_cash + net_flow, tol=1.0), \
                f"Year {df.iloc[i]['Year']}: Cash ${curr_cash:.0f} != prev ${prev_cash:.0f} + flow ${net_flow:.0f}"
    print('test_cash_updates_by_net_cash_flow: PASS')


def test_no_income_no_expenses_zero_cash_flow():
    """With no income and no expenses, cash flow should be zero."""
    a = make_assumptions()
    r = run1(a)
    assert close(r['Net_Cash_Flow'], 0, tol=1.0)
    assert close(r['Cash'], 0, tol=1.0)
    print('test_no_income_no_expenses_zero_cash_flow: PASS')


# ============================================
# NET WORTH TESTS
# ============================================

def test_net_worth_calculation():
    """Net worth = cash + portfolio + crypto + retirement + roth + hsa + property - debt."""
    a = make_assumptions(
        current_cash=10000, current_portfolio=50000,
        current_crypto=5000, current_401k=30000,
        current_roth_balance=20000, current_hsa=3000,
    )
    r = run1(a)
    expected = r['Cash'] + r['Portfolio'] + r['Crypto'] + r['Trad_Retirement'] + \
               r['Roth_Balance'] + r['HSA_Balance'] + r['Property_Value'] - r['Total_Debt']
    assert close(r['Net_Worth'], expected, tol=1.0), f"Net worth ${r['Net_Worth']:.0f} != ${expected:.0f}"
    print('test_net_worth_calculation: PASS')


def test_net_worth_allows_negative_cash():
    """Net worth should reflect actual cash, even if negative."""
    a = make_assumptions(current_cash=5000, annual_expenses=50000)
    r = run1(a)
    # High expenses with no income = negative cash
    assert r['Cash'] < 0, f"Expected negative cash, got ${r['Cash']:.0f}"
    print('test_net_worth_allows_negative_cash: PASS')


# ============================================
# FI RATIO TESTS
# ============================================

def test_fi_ratio_basic():
    """FI ratio = passive_income / recurring_expenses."""
    a = make_assumptions(
        current_portfolio=500000, portfolio_return=0.10,
        dividend_yield=0.04, annual_expenses=20000,
    )
    r = run1(a)
    passive = r['Dividends'] + max(0, r['Net_Rental'])
    recurring = r['Living_Expenses'] + r['Housing_Cost'] + r['Debt_Payments']
    expected_ratio = passive / recurring if recurring > 0 else 0
    assert close(r['FI_Ratio'], expected_ratio, tol=0.01), \
        f"FI ratio {r['FI_Ratio']:.4f} != {expected_ratio:.4f}"
    print('test_fi_ratio_basic: PASS')


def test_fi_ratio_excludes_purchase_costs():
    """FI ratio should not spike down in property purchase years."""
    a = make_assumptions(
        current_salary=100000, current_portfolio=200000,
        portfolio_return=0.10, dividend_yield=0.04,
        annual_expenses=30000, monthly_rent=1500,
    )
    prop = {
        'purchase_price': 300000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'is_primary': True, 'purchase_year': 2026,
    }
    r = run1(a, properties=[prop])
    # FI ratio should be based on recurring expenses, not including down payment
    assert r['FI_Ratio'] > 0, "FI ratio should be positive"
    assert r['Property_Purchase_Costs'] > 0, "Should have purchase costs this year"
    # Verify purchase costs are NOT in the FI denominator
    recurring = r['Living_Expenses'] + r['Housing_Cost'] + r['Debt_Payments']
    assert r['Total_Expenses'] - recurring > 0, "Total expenses should include purchase costs but FI shouldn't"
    print('test_fi_ratio_excludes_purchase_costs: PASS')


# ============================================
# EMPLOYER CONTRIBUTION TESTS
# ============================================

def test_employer_401k_not_deducted_from_salary():
    """Employer 401k match should add to account without reducing salary."""
    a_no_match = make_assumptions(current_salary=100000, contrib_401k=10000)
    a_with_match = make_assumptions(current_salary=100000, contrib_401k=10000, employer_401k=5000)
    r_no = run1(a_no_match)
    r_yes = run1(a_with_match)
    # Net income should be the same (employer match doesn't reduce take-home)
    assert close(r_no['Net_Income'], r_yes['Net_Income'], tol=1.0)
    # But 401k balance should be higher
    assert r_yes['Trad_Retirement'] > r_no['Trad_Retirement']
    print('test_employer_401k_not_deducted_from_salary: PASS')


def test_employer_hsa_not_taxed():
    """Employer HSA contribution shouldn't be taxed or reduce salary."""
    a_no = make_assumptions(current_salary=100000)
    a_yes = make_assumptions(current_salary=100000, employer_hsa=1000)
    r_no = run1(a_no)
    r_yes = run1(a_yes)
    # Net income unchanged
    assert close(r_no['Net_Income'], r_yes['Net_Income'], tol=1.0)
    # HSA balance higher
    assert r_yes['HSA_Balance'] > r_no['HSA_Balance']
    print('test_employer_hsa_not_taxed: PASS')


# ============================================
# DEBT TESTS
# ============================================

def test_debt_payment_schedule():
    """Debt payments should follow amortization schedule."""
    a = make_assumptions(end_year=2028)
    debt = {
        'name': 'Car Loan',
        'original_balance': 30000,
        'interest_rate': 0.06,
        'term_years': 5,
        'start_year': 2026,
        'months_already_paid': 0,
    }
    df = run_projection(a, [], [debt], [])
    # Monthly payment for 30K @ 6% over 5 years
    monthly_pmt = calculate_mortgage_payment(30000, 0.06, 5)
    expected_annual = monthly_pmt * 12
    assert close(df.iloc[0]['Debt_Payments'], expected_annual, tol=10.0), \
        f"Expected ~${expected_annual:.0f}, got ${df.iloc[0]['Debt_Payments']:.0f}"
    print('test_debt_payment_schedule: PASS')


def test_debt_payoff():
    """Debt should disappear after term ends."""
    a = make_assumptions(end_year=2032)
    debt = {
        'name': 'Car',
        'original_balance': 30000,
        'interest_rate': 0.06,
        'term_years': 5,
        'start_year': 2026,
        'months_already_paid': 0,
    }
    df = run_projection(a, [], [debt], [])
    # After 5 years (2031+), debt should be paid off
    row_2032 = df[df['Year'] == 2032].iloc[0]
    assert close(row_2032['Other_Debt'], 0, tol=1.0)
    assert close(row_2032['Debt_Payments'], 0, tol=1.0)
    print('test_debt_payoff: PASS')


# ============================================
# STATE TAX INTEGRATION TESTS
# ============================================

def test_no_income_tax_state():
    """No Income Tax states should have 0 state tax."""
    a = make_assumptions(
        current_salary=100000, state='No Income Tax (TX, FL, WA, etc.)', state_tax_rate=0,
    )
    r = run1(a)
    assert close(r['State_Tax'], 0)
    print('test_no_income_tax_state: PASS')


def test_other_state_flat_rate():
    """Other states use flat rate on taxable income."""
    a = make_assumptions(
        current_salary=100000, filing_status='Single',
        state='Other', state_tax_rate=0.05,
    )
    r = run1(a)
    # State tax = taxable_income * 5%
    expected = r['Taxable_Income'] * 0.05
    assert close(r['State_Tax'], expected, tol=1.0)
    print('test_other_state_flat_rate: PASS')


def test_sc_state_integration():
    """SC state tax in full projection matches standalone calc."""
    a = make_assumptions(
        current_salary=100000, filing_status='Single',
        state='SC', state_tax_rate=0,
    )
    r = run1(a)
    expected = calculate_sc_state_tax(r['Taxable_Income'], 2026)
    assert close(r['State_Tax'], expected, tol=1.0)
    print('test_sc_state_integration: PASS')


def test_ma_state_integration():
    pass
    """MA state tax in full projection matches standalone calc."""
    a = make_assumptions(
        current_salary=100000, filing_status='Single',
        state='MA', state_tax_rate=0,
    )
    r = run1(a)
    expected = calculate_ma_state_tax(r['Taxable_Income'], 2026)
    assert close(r['State_Tax'], expected, tol=1.0)
    print('test_ma_state_integration: PASS')


# ============================================
# EDGE CASE TESTS
# ============================================

def test_zero_everything():
    """Projection with all zeros should not crash."""
    a = make_assumptions()
    r = run1(a)
    assert close(r['Net_Worth'], 0, tol=1.0)
    assert close(r['Total_Tax'], 0, tol=1.0)
    print('test_zero_everything: PASS')


def test_very_high_income():
    """Very high income should hit top tax brackets without errors."""
    a = make_assumptions(current_salary=1000000, filing_status='Single')
    r = run1(a)
    assert r['Federal_Tax'] > 0
    assert r['Effective_Tax_Rate'] > 30
    print('test_very_high_income: PASS')


def test_withdrawal_exceeds_balance():
    """Withdrawing more than available should be capped at balance."""
    a = make_assumptions(current_portfolio=10000, portfolio_return=0.0)
    events = [{'type': 'Withdraw from Brokerage', 'year': 2026, 'amount': 50000}]
    r = run1(a, events=events)
    # Should withdraw max 10K, not 50K
    assert close(r['Event_Brokerage_WD'], 10000, tol=1.0)
    assert close(r['Portfolio'], 0, tol=1.0)
    print('test_withdrawal_exceeds_balance: PASS')


def test_multiple_events_same_year():
    """Multiple events in the same year process sequentially."""
    a = make_assumptions(
        current_portfolio=100000, current_401k=100000,
        portfolio_return=0.0, birth_year=1960,  # age 66, no penalty
    )
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2026, 'amount': 30000},
        {'type': 'Withdraw from 401k/IRA', 'year': 2026, 'amount': 20000},
    ]
    r = run1(a, events=events)
    assert close(r['Event_Brokerage_WD'], 30000, tol=1.0)
    assert close(r['Event_401k_WD'], 20000, tol=1.0)
    print('test_multiple_events_same_year: PASS')


def test_negative_rental_in_cashflow():
    """Negative rental income (expenses > rent) should increase cash outflow."""
    a = make_assumptions(property_appreciation=0.0, rent_growth=0.0)
    prop = {
        'purchase_price': 200000, 'down_payment_pct': 1.0,
        'mortgage_rate': 0.0, 'mortgage_years': 30,
        'is_primary': False, 'purchase_year': 2025,
        'rent_per_unit': 100, 'num_units': 1,
        'other_monthly_income': 0, 'vacancy_rate': 0.0,
        'insurance_monthly': 500, 'capex_rate': 0.0,
        'management_rate': 0.0, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
        'property_tax_rate': 0.05,
    }
    r = run1(a, properties=[prop])
    # Rent: 100*12 = 1200, expenses: 500*12 + 200000*0.05 = 6000+10000 = 16000
    assert r['Net_Rental'] < 0, "Should have negative net rental"
    print('test_negative_rental_in_cashflow: PASS')


def test_fica_not_applied_to_events():
    """FICA should only be on salary, not on 401k withdrawals or conversions."""
    a = make_assumptions(current_401k=200000)
    events = [{'type': 'Withdraw from 401k/IRA', 'year': 2026, 'amount': 50000}]
    r = run1(a, events=events)
    # No salary = no FICA, even though there's $50K in event income
    assert close(r['FICA_Tax'], 0)
    assert close(r['SS_Tax'], 0)
    assert close(r['Medicare_Tax'], 0)
    print('test_fica_not_applied_to_events: PASS')


# ============================================
# PROPERTY PURCHASE YEAR TESTS
# ============================================

def test_property_purchase_costs_in_cashflow():
    """Down payment and closing costs should reduce cash in purchase year."""
    a = make_assumptions(current_cash=100000)
    prop = {
        'purchase_price': 200000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'is_primary': True, 'purchase_year': 2026,
        'closing_costs': 5000, 'repair_cost': 2000,
        'lender_points': 1000, 'other_fees': 500,
    }
    r = run1(a, properties=[prop])
    # Down payment = 200000 * 0.20 = 40000
    # + closing + repair + points + fees = 5000+2000+1000+500 = 8500
    # Total purchase costs = 48500
    assert close(r['Property_Purchase_Costs'], 48500, tol=1.0)
    print('test_property_purchase_costs_in_cashflow: PASS')


# ============================================
# ACCESSIBLE FUNDS TESTS
# ============================================

def test_accessible_funds_under_59():
    """Under 59.5: accessible = cash + 95% portfolio + 80% crypto + roth contributions."""
    a = make_assumptions(
        birth_year=1990,  # age 36
        current_cash=10000, current_portfolio=100000,
        current_crypto=50000, current_roth_balance=30000,
        current_roth_contributions=20000,
    )
    r = run1(a)
    expected = r['Cash'] + r['Portfolio'] * 0.95 + r['Crypto'] * 0.80 + 20000
    assert close(r['Accessible_Liquid'], expected, tol=100.0)
    print('test_accessible_funds_under_59: PASS')


# ============================================
# RUN ALL TESTS
# ============================================

def run_all():
    tests = [
        # Federal tax
        test_federal_tax_zero_income,
        test_federal_tax_single_10pct_bracket,
        test_federal_tax_single_12pct_bracket,
        test_federal_tax_single_22pct_bracket,
        test_federal_tax_married_jointly,
        test_federal_tax_head_of_household,
        test_federal_tax_high_income,
        # SC state tax
        test_sc_tax_zero_bracket,
        test_sc_tax_3pct_bracket,
        test_sc_tax_top_bracket_2026,
        test_sc_tax_top_bracket_2025,
        # MA state tax
        test_ma_tax_zero_bracket,
        test_ma_tax_5pct_bracket,
        test_ma_tax_top_bracket_2026,
        test_ma_tax_top_bracket_2024,
        # FICA
        test_fica_below_ss_cap,
        test_fica_above_ss_cap,
        test_fica_additional_medicare,
        # Mortgage
        test_mortgage_payment_basic,
        test_mortgage_payment_zero_loan,
        test_mortgage_payment_zero_rate,
        test_remaining_balance_start,
        test_remaining_balance_end,
        test_remaining_balance_midpoint,
        # Income & inflation
        test_salary_growth_compound,
        test_salary_stops_at_retirement,
        test_expense_inflation,
        test_rent_inflation,
        # Investment growth
        test_portfolio_growth_no_dividends,
        test_portfolio_growth_with_dividends,
        test_dividend_tax,
        test_crypto_growth,
        test_401k_growth_with_employer_match,
        test_roth_growth_with_contribution,
        test_hsa_growth_with_employer,
        test_multi_year_compound_growth,
        # Cost basis
        test_cost_basis_initial_no_gains,
        test_cost_basis_after_growth,
        test_cost_basis_with_contributions,
        test_crypto_cost_basis,
        # Rental properties
        test_rental_income_basic,
        test_rental_income_in_agi,
        test_primary_residence_replaces_rent,
        # Tax deductions
        test_standard_deduction_used,
        test_itemized_deduction_used,
        test_salt_cap_10k,
        test_pretax_deductions_reduce_tax,
        # Financial events
        test_roth_conversion_increases_agi,
        test_roth_conversion_5year_tracking,
        test_roth_withdrawal_contributions_first,
        test_roth_withdrawal_earnings_taxed_under_59,
        test_401k_withdrawal_no_penalty_after_59,
        test_401k_withdrawal_penalty_under_59,
        test_percent_withdrawal_normalization,
        test_percent_withdrawal_decimal,
        # Cash flow
        test_cash_flow_balance,
        test_cash_updates_by_net_cash_flow,
        test_no_income_no_expenses_zero_cash_flow,
        # Net worth
        test_net_worth_calculation,
        test_net_worth_allows_negative_cash,
        # FI ratio
        test_fi_ratio_basic,
        test_fi_ratio_excludes_purchase_costs,
        # Employer contributions
        test_employer_401k_not_deducted_from_salary,
        test_employer_hsa_not_taxed,
        # Debts
        test_debt_payment_schedule,
        test_debt_payoff,
        # State tax integration
        test_no_income_tax_state,
        test_other_state_flat_rate,
        test_sc_state_integration,
        test_ma_state_integration,
        # Edge cases
        test_zero_everything,
        test_very_high_income,
        test_withdrawal_exceeds_balance,
        test_multiple_events_same_year,
        test_negative_rental_in_cashflow,
        test_fica_not_applied_to_events,
        test_property_purchase_costs_in_cashflow,
        test_accessible_funds_under_59,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except (AssertionError, Exception) as e:
            print(f'{test_fn.__name__}: FAIL - {e}')
            failed += 1

    print(f'\n{passed}/{passed + failed} TESTS PASSED')
    if failed > 0:
        print(f'{failed} TESTS FAILED')
        return False
    else:
        print('ALL TESTS PASSED')
        return True


if __name__ == '__main__':
    success = run_all()
    if not success:
        sys.exit(1)
