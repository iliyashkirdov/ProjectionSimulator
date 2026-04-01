"""
Integration/edge-case tests that exercise run_projection with realistic scenarios
including properties, debts, financial events, and data export column validation.
"""
import sys
import json
import math

sys.path.insert(0, '.')
from calculations import run_projection, calculate_mortgage_payment


def approx(a, b, tol=0.01):
    return abs(a - b) <= tol


passed = 0
failed = 0
errors = []


def run_test(name, func):
    global passed, failed
    try:
        func()
        print(f"{name}: PASS")
        passed += 1
    except AssertionError as e:
        print(f"{name}: FAIL - {e}")
        failed += 1
        errors.append((name, str(e)))
    except Exception as e:
        print(f"{name}: ERROR - {type(e).__name__}: {e}")
        failed += 1
        errors.append((name, f"{type(e).__name__}: {e}"))


# ============================================================
# HELPER: Base assumptions builder
# ============================================================
def base_assumptions(**overrides):
    defaults = {
        'start_year': 2026, 'end_year': 2030, 'retirement_year': 2045,
        'birth_year': 1990, 'filing_status': 'Single',
        'state': 'No Income Tax (TX, FL, WA, etc.)', 'state_tax_rate': 0,
        'current_salary': 75000, 'salary_growth': 0.03,
        'contrib_401k': 10000, 'employer_401k': 5000,
        'contrib_roth': 5000, 'contrib_hsa': 3000, 'employer_hsa': 1000,
        'contrib_brokerage': 5000, 'contrib_crypto': 0,
        'annual_expenses': 36000, 'monthly_rent': 1200, 'inflation': 0.03,
        'current_cash': 20000, 'current_portfolio': 50000, 'current_crypto': 0,
        'current_401k': 80000, 'current_roth_balance': 20000,
        'current_roth_contributions': 15000, 'roth_first_contrib_year': 2020,
        'current_hsa': 5000,
        'portfolio_return': 0.07, 'crypto_return': 0.10, 'dividend_yield': 0.02,
        'property_appreciation': 0.03, 'rent_growth': 0.03,
        'cash_savings_rate': 0.10,
    }
    defaults.update(overrides)
    return defaults


# ============================================================
# TEST: Sample scenario JSON runs without errors
# ============================================================
def test_sample_scenario_runs():
    with open('sample_scenario.json') as f:
        data = json.load(f)
    assumptions = data['assumptions']
    properties = data.get('properties', [])
    debts = data.get('debts', [])
    events = data.get('financial_events', [])
    results = run_projection(assumptions, properties, debts, events)
    assert len(results) > 0, "No results returned"
    assert 'Year' in results.columns, "Missing Year column"
    assert 'Net_Worth' in results.columns, "Missing Net_Worth column"
    # Should have one row per year
    expected_years = assumptions['end_year'] - assumptions['start_year'] + 1
    assert len(results) == expected_years, f"Expected {expected_years} rows, got {len(results)}"

run_test("test_sample_scenario_runs", test_sample_scenario_runs)


# ============================================================
# TEST: Primary residence replaces rent
# ============================================================
def test_primary_home_replaces_rent():
    a = base_assumptions(monthly_rent=1500)
    props = [{
        'name': 'My Home', 'is_primary': True, 'purchase_year': 2027,
        'purchase_price': 300000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.065, 'mortgage_years': 30,
        'closing_costs': 8000, 'property_tax_rate': 0.012,
        'monthly_rent': 0, 'arv': 300000, 'repair_cost': 0,
        'pmi_rate': 0, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 0, 'num_units': 1, 'vacancy_rate': 0,
        'avg_tenant_stay': 0, 'other_monthly_income': 0,
        'insurance_monthly': 150, 'capex_rate': 0,
        'management_rate': 0, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }]
    results = run_projection(a, props, [])
    # 2026: no home yet → living expenses should include rent
    row_2026 = results[results['Year'] == 2026].iloc[0]
    # Living expenses include base expenses + rent
    assert row_2026['Living_Expenses'] > a['annual_expenses'], "Living expenses should include rent in 2026"
    # 2027: home purchased → housing cost replaces rent
    row_2027 = results[results['Year'] == 2027].iloc[0]
    # With a primary home, the housing cost should be the mortgage/taxes, not rent
    assert row_2027['Property_Value'] > 0, "Property value should be nonzero after purchase"
    assert row_2027['Housing_Cost'] > 0, "Housing cost should reflect mortgage/taxes"

run_test("test_primary_home_replaces_rent", test_primary_home_replaces_rent)


# ============================================================
# TEST: Rental property generates income
# ============================================================
def test_rental_income():
    a = base_assumptions()
    rental = {
        'name': 'Rental A', 'is_primary': False, 'purchase_year': 2026,
        'purchase_price': 200000, 'down_payment_pct': 0.25,
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'closing_costs': 5000, 'property_tax_rate': 0.01,
        'monthly_rent': 1400, 'arv': 200000, 'repair_cost': 0,
        'pmi_rate': 0, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 1400, 'num_units': 1, 'vacancy_rate': 0.05,
        'avg_tenant_stay': 24, 'other_monthly_income': 0,
        'insurance_monthly': 100, 'capex_rate': 0.05,
        'management_rate': 0.08, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }
    results = run_projection(a, [rental], [])
    row = results[results['Year'] == 2026].iloc[0]
    assert row['Rental_Income'] > 0, "Rental income should be positive"
    assert row['Rental_Expenses'] > 0, "Rental expenses should be positive"

run_test("test_rental_income", test_rental_income)


# ============================================================
# TEST: Debt payoff tracked correctly
# ============================================================
def test_debt_tracking():
    a = base_assumptions(end_year=2035)
    debts = [{
        'name': 'Car Loan', 'original_balance': 20000, 'interest_rate': 0.06,
        'term_years': 5, 'start_year': 2024, 'months_already_paid': 24,
    }]
    results = run_projection(a, [], debts)
    # First year should have debt balance
    row_first = results[results['Year'] == 2026].iloc[0]
    assert row_first['Total_Debt'] > 0, "Should have debt in 2026"
    # Debt should decrease over time
    row_last = results[results['Year'] == 2035].iloc[0]
    assert row_last['Total_Debt'] < row_first['Total_Debt'], "Debt should decrease"

run_test("test_debt_tracking", test_debt_tracking)


# ============================================================
# TEST: Financial events - Roth conversion
# ============================================================
def test_roth_conversion_event():
    a = base_assumptions(current_401k=200000, retirement_year=2026)
    events = [
        {'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2027, 'amount': 30000}
    ]
    results = run_projection(a, [], [], events)
    row_2027 = results[results['Year'] == 2027].iloc[0]
    assert row_2027['Event_Roth_Conversion'] == 30000, f"Expected 30000 conversion, got {row_2027['Event_Roth_Conversion']}"
    # 401k should decrease by conversion amount (minus growth)
    row_2026 = results[results['Year'] == 2026].iloc[0]
    # Roth balance should increase
    assert row_2027['Roth_Balance'] > row_2026['Roth_Balance'], "Roth should increase from conversion"

run_test("test_roth_conversion_event", test_roth_conversion_event)


# ============================================================
# TEST: Brokerage withdrawal event
# ============================================================
def test_brokerage_withdrawal_event():
    a = base_assumptions(current_portfolio=100000, retirement_year=2026)
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2027, 'amount': 20000}
    ]
    results = run_projection(a, [], [], events)
    row = results[results['Year'] == 2027].iloc[0]
    assert row['Event_Brokerage_WD'] == 20000, f"Expected 20000 withdrawal, got {row['Event_Brokerage_WD']}"

run_test("test_brokerage_withdrawal_event", test_brokerage_withdrawal_event)


# ============================================================
# TEST: 401k withdrawal with early penalty
# ============================================================
def test_401k_early_withdrawal_penalty():
    a = base_assumptions(birth_year=2000, current_401k=200000, retirement_year=2026)
    events = [
        {'type': 'Withdraw from 401k/IRA', 'year': 2027, 'amount': 50000}
    ]
    results = run_projection(a, [], [], events)
    row = results[results['Year'] == 2027].iloc[0]
    assert row['Event_401k_WD'] == 50000
    # Age in 2027 = 2027-2000 = 27, so penalty should apply
    assert row['Event_Penalties_Paid'] > 0, "Should have 10% penalty under 59.5"
    assert row['Total_Tax'] > 0, "Should have taxes on 401k withdrawal"

run_test("test_401k_early_withdrawal_penalty", test_401k_early_withdrawal_penalty)


# ============================================================
# TEST: Percent-based recurring withdrawals
# ============================================================
def test_percent_recurring_withdrawal():
    a = base_assumptions(current_portfolio=500000, retirement_year=2026, end_year=2028)
    # App creates one event per year with amount_pct for recurring % withdrawals
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2027, 'amount_pct': 0.04},
        {'type': 'Withdraw from Brokerage', 'year': 2028, 'amount_pct': 0.04},
    ]
    results = run_projection(a, [], [], events)
    # Both years should have withdrawals
    wd_2027 = results[results['Year'] == 2027].iloc[0]['Event_Brokerage_WD']
    wd_2028 = results[results['Year'] == 2028].iloc[0]['Event_Brokerage_WD']
    assert wd_2027 > 0, "Should withdraw in 2027"
    assert wd_2028 > 0, "Should withdraw in 2028"

run_test("test_percent_recurring_withdrawal", test_percent_recurring_withdrawal)


# ============================================================
# TEST: Crypto withdrawal event
# ============================================================
def test_crypto_withdrawal_event():
    a = base_assumptions(current_crypto=50000, retirement_year=2026)
    events = [
        {'type': 'Withdraw from Crypto', 'year': 2027, 'amount': 10000}
    ]
    results = run_projection(a, [], [], events)
    row = results[results['Year'] == 2027].iloc[0]
    assert row['Event_Crypto_WD'] == 10000

run_test("test_crypto_withdrawal_event", test_crypto_withdrawal_event)


# ============================================================
# TEST: Multiple properties (primary + rental)
# ============================================================
def test_multiple_properties():
    a = base_assumptions(end_year=2032)
    primary = {
        'name': 'Home', 'is_primary': True, 'purchase_year': 2027,
        'purchase_price': 350000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.065, 'mortgage_years': 30,
        'closing_costs': 10000, 'property_tax_rate': 0.012,
        'monthly_rent': 0, 'arv': 350000, 'repair_cost': 0,
        'pmi_rate': 0, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 0, 'num_units': 1, 'vacancy_rate': 0,
        'avg_tenant_stay': 0, 'other_monthly_income': 0,
        'insurance_monthly': 150, 'capex_rate': 0,
        'management_rate': 0, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }
    rental = {
        'name': 'Rental B', 'is_primary': False, 'purchase_year': 2029,
        'purchase_price': 250000, 'down_payment_pct': 0.25,
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'closing_costs': 6000, 'property_tax_rate': 0.01,
        'monthly_rent': 1600, 'arv': 250000, 'repair_cost': 0,
        'pmi_rate': 0, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 1600, 'num_units': 1, 'vacancy_rate': 0.05,
        'avg_tenant_stay': 24, 'other_monthly_income': 0,
        'insurance_monthly': 120, 'capex_rate': 0.05,
        'management_rate': 0.10, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }
    results = run_projection(a, [primary, rental], [])
    # Before any purchase
    r2026 = results[results['Year'] == 2026].iloc[0]
    assert r2026['Property_Value'] == 0, "No property before purchase"
    # After primary purchase
    r2028 = results[results['Year'] == 2028].iloc[0]
    assert r2028['Property_Value'] > 0
    # Rent should be zero when owning primary (Living_Expenses = base expenses only, no rent)
    assert r2028['Housing_Cost'] > 0, "Should have housing cost (mortgage + taxes) with primary home"
    # After rental purchase
    r2030 = results[results['Year'] == 2030].iloc[0]
    assert r2030['Rental_Income'] > 0, "Rental should generate income"
    assert r2030['Property_Value'] > r2028['Property_Value'], "2 properties > 1 property value"

run_test("test_multiple_properties", test_multiple_properties)


# ============================================================
# TEST: Multiple debts
# ============================================================
def test_multiple_debts():
    a = base_assumptions(end_year=2035)
    debts = [
        {'name': 'Car Loan', 'original_balance': 15000, 'interest_rate': 0.05,
         'term_years': 5, 'start_year': 2025, 'months_already_paid': 12},
        {'name': 'Student Loan', 'original_balance': 30000, 'interest_rate': 0.04,
         'term_years': 10, 'start_year': 2022, 'months_already_paid': 48},
    ]
    results = run_projection(a, [], debts)
    r2026 = results[results['Year'] == 2026].iloc[0]
    assert r2026['Total_Debt'] > 0, "Should have debt balance"
    assert r2026['Debt_Payments'] > 0, "Should make debt payments"

run_test("test_multiple_debts", test_multiple_debts)


# ============================================================
# TEST: SC state tax
# ============================================================
def test_sc_state_tax_integration():
    a = base_assumptions(state='SC', state_tax_rate=0)
    results = run_projection(a, [], [])
    row = results[results['Year'] == 2026].iloc[0]
    assert row['State_Tax'] > 0, "SC should have state tax"

run_test("test_sc_state_tax_integration", test_sc_state_tax_integration)


# ============================================================
# TEST: Other state flat tax
# ============================================================
def test_other_state_flat_tax():
    a = base_assumptions(state='Other', state_tax_rate=0.05)
    results = run_projection(a, [], [])
    row = results[results['Year'] == 2026].iloc[0]
    assert row['State_Tax'] > 0, "Other state with 5% rate should have tax"

run_test("test_other_state_flat_tax", test_other_state_flat_tax)


# ============================================================
# TEST: All expected DataFrame columns exist
# ============================================================
def test_all_export_columns_exist():
    """Verify that the columns referenced in app.py export section actually exist"""
    a = base_assumptions(current_crypto=5000)
    props = [{
        'name': 'Home', 'is_primary': True, 'purchase_year': 2027,
        'purchase_price': 300000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.065, 'mortgage_years': 30,
        'closing_costs': 8000, 'property_tax_rate': 0.012,
        'monthly_rent': 0, 'arv': 300000, 'repair_cost': 0,
        'pmi_rate': 0, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 0, 'num_units': 1, 'vacancy_rate': 0,
        'avg_tenant_stay': 0, 'other_monthly_income': 0,
        'insurance_monthly': 150, 'capex_rate': 0,
        'management_rate': 0, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }]
    debts = [{'name': 'Loan', 'original_balance': 10000, 'interest_rate': 0.05,
              'term_years': 5, 'start_year': 2024, 'months_already_paid': 24}]
    events = [
        {'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2027, 'amount': 10000},
        {'type': 'Withdraw from Brokerage', 'year': 2028, 'amount': 5000},
    ]
    results = run_projection(a, props, debts, events)

    # Columns from app.py export section (the authoritative list)
    expected_columns = [
        # Net Worth tab
        'Year', 'Age', 'Net_Worth', 'Cash', 'Portfolio', 'Crypto',
        'Trad_Retirement', 'Roth_Balance', 'HSA_Balance',
        'Property_Equity',
        # Cash Flow tab
        'Gross_Salary', 'Net_Income', 'Total_Expenses',
        'Net_Cash_Flow', 'Debt_Payments',
        # Retirement tab
        'Roth_Contributions', 'Event_Roth_Conversion',
        'Event_401k_WD', 'Event_Roth_WD',
        # Real Estate tab
        'Property_Value', 'Property_Debt',
        'Rental_Income', 'Rental_Expenses', 'Net_Rental',
        'Property_Purchase_Costs',
        # Taxes tab
        'Federal_Tax', 'State_Tax', 'FICA_Tax',
        'Total_Tax', 'Effective_Tax_Rate',
        # FI Progress tab
        'Accessible_Liquid', 'Accessible_Portfolio', 'Accessible_Crypto',
        'FI_Ratio', 'Passive_Income',
        # Withdrawals tab
        'Event_Brokerage_WD', 'Event_Crypto_WD',
        # Additional columns
        'Housing_Cost', 'Dividends', 'Living_Expenses',
        'Total_Debt', 'Other_Debt',
    ]

    missing = [c for c in expected_columns if c not in results.columns]
    assert len(missing) == 0, f"Missing columns in results: {missing}"

run_test("test_all_export_columns_exist", test_all_export_columns_exist)


# ============================================================
# TEST: Zero-income retirement scenario
# ============================================================
def test_zero_income_retirement():
    a = base_assumptions(
        current_salary=0, retirement_year=2020,
        current_portfolio=500000, current_401k=300000, current_roth_balance=100000,
        current_roth_contributions=80000,
    )
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2026, 'amount': 40000},
    ]
    results = run_projection(a, [], [], events)
    row = results[results['Year'] == 2026].iloc[0]
    assert row['Gross_Salary'] == 0
    assert row['Event_Brokerage_WD'] == 40000
    assert row['FICA_Tax'] == 0, "No FICA on investment withdrawals"

run_test("test_zero_income_retirement", test_zero_income_retirement)


# ============================================================
# TEST: Very long projection (30+ years)
# ============================================================
def test_long_projection():
    a = base_assumptions(start_year=2026, end_year=2065)
    results = run_projection(a, [], [])
    assert len(results) == 40, f"Expected 40 rows, got {len(results)}"
    # Net worth should generally increase over 40 years of working + saving
    first_nw = results.iloc[0]['Net_Worth']
    last_nw = results.iloc[-1]['Net_Worth']
    assert last_nw > first_nw, "Net worth should grow over 40 years"

run_test("test_long_projection", test_long_projection)


# ============================================================
# TEST: Property with PMI
# ============================================================
def test_property_with_pmi():
    a = base_assumptions()
    prop = {
        'name': 'Low Down Home', 'is_primary': True, 'purchase_year': 2026,
        'purchase_price': 300000, 'down_payment_pct': 0.05,  # Only 5% down
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'closing_costs': 8000, 'property_tax_rate': 0.012,
        'monthly_rent': 0, 'arv': 300000, 'repair_cost': 0,
        'pmi_rate': 0.005, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 0, 'num_units': 1, 'vacancy_rate': 0,
        'avg_tenant_stay': 0, 'other_monthly_income': 0,
        'insurance_monthly': 150, 'capex_rate': 0,
        'management_rate': 0, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }
    results = run_projection(a, [prop], [])
    # Should have property purchase costs in year 2026
    row = results[results['Year'] == 2026].iloc[0]
    assert row['Property_Purchase_Costs'] > 0, "Should have purchase costs"
    assert row['Property_Value'] > 0

run_test("test_property_with_pmi", test_property_with_pmi)


# ============================================================
# TEST: HSA withdrawal after 65
# ============================================================
def test_hsa_after_65():
    a = base_assumptions(birth_year=1960, retirement_year=2020, end_year=2028)
    # Age in 2026 = 66 (over 65)
    results = run_projection(a, [], [])
    row = results[results['Year'] == 2026].iloc[0]
    assert row['HSA_Balance'] >= 0, "HSA should still track"

run_test("test_hsa_after_65", test_hsa_after_65)


# ============================================================
# TEST: Empty everything (minimal assumptions)
# ============================================================
def test_empty_everything():
    a = base_assumptions(
        current_salary=0, current_cash=0, current_portfolio=0,
        current_crypto=0, current_401k=0, current_roth_balance=0,
        current_roth_contributions=0, current_hsa=0,
        contrib_401k=0, employer_401k=0, contrib_roth=0,
        contrib_hsa=0, employer_hsa=0, contrib_brokerage=0,
        contrib_crypto=0, annual_expenses=0, monthly_rent=0,
    )
    results = run_projection(a, [], [])
    row = results[results['Year'] == 2026].iloc[0]
    assert row['Net_Worth'] == 0, "Everything zero should have zero net worth"
    assert row['Total_Tax'] == 0
    assert row['FICA_Tax'] == 0

run_test("test_empty_everything", test_empty_everything)


# ============================================================
# TEST: Withdrawal exceeding balance doesn't go negative
# ============================================================
def test_withdrawal_capped_at_balance():
    a = base_assumptions(current_portfolio=5000, retirement_year=2026)
    events = [
        {'type': 'Withdraw from Brokerage', 'year': 2027, 'amount': 999999}
    ]
    results = run_projection(a, [], [], events)
    row = results[results['Year'] == 2027].iloc[0]
    assert row['Portfolio'] >= 0, "Portfolio should not go negative"

run_test("test_withdrawal_capped_at_balance", test_withdrawal_capped_at_balance)


# ============================================================
# TEST: Combined scenario - full kitchen sink
# ============================================================
def test_kitchen_sink():
    """Run a full realistic scenario with everything enabled"""
    a = base_assumptions(
        current_salary=120000, salary_growth=0.03,
        contrib_401k=23000, employer_401k=6000,
        contrib_roth=7000, contrib_hsa=4150, employer_hsa=1000,
        contrib_brokerage=15000, contrib_crypto=2000,
        annual_expenses=48000, monthly_rent=1800, inflation=0.03,
        current_cash=30000, current_portfolio=80000, current_crypto=10000,
        current_401k=150000, current_roth_balance=40000,
        current_roth_contributions=30000, current_hsa=12000,
        state='SC', state_tax_rate=0,
        start_year=2026, end_year=2060, retirement_year=2048,
    )
    primary = {
        'name': 'House', 'is_primary': True, 'purchase_year': 2028,
        'purchase_price': 400000, 'down_payment_pct': 0.20,
        'mortgage_rate': 0.065, 'mortgage_years': 30,
        'closing_costs': 12000, 'property_tax_rate': 0.012,
        'monthly_rent': 0, 'arv': 400000, 'repair_cost': 0,
        'pmi_rate': 0, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 0, 'num_units': 1, 'vacancy_rate': 0,
        'avg_tenant_stay': 0, 'other_monthly_income': 0,
        'insurance_monthly': 180, 'capex_rate': 0,
        'management_rate': 0, 'hoa_monthly': 200,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }
    rental = {
        'name': 'Rental', 'is_primary': False, 'purchase_year': 2032,
        'purchase_price': 280000, 'down_payment_pct': 0.25,
        'mortgage_rate': 0.07, 'mortgage_years': 30,
        'closing_costs': 7000, 'property_tax_rate': 0.01,
        'monthly_rent': 1800, 'arv': 280000, 'repair_cost': 0,
        'pmi_rate': 0, 'lender_points': 0, 'other_fees': 0,
        'rent_per_unit': 1800, 'num_units': 1, 'vacancy_rate': 0.05,
        'avg_tenant_stay': 24, 'other_monthly_income': 50,
        'insurance_monthly': 130, 'capex_rate': 0.05,
        'management_rate': 0.10, 'hoa_monthly': 0,
        'utilities_monthly': 0, 'other_monthly_expenses': 0,
    }
    debts = [
        {'name': 'Student Loan', 'original_balance': 25000, 'interest_rate': 0.045,
         'term_years': 10, 'start_year': 2023, 'months_already_paid': 36},
    ]
    events = [
        {'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2049, 'amount': 40000},
        {'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2050, 'amount': 40000},
        {'type': 'Roth Conversion (401k/IRA → Roth)', 'year': 2051, 'amount': 40000},
        {'type': 'Withdraw from Brokerage', 'year': 2049, 'amount': 30000},
        {'type': 'Withdraw from Brokerage', 'year': 2054, 'amount_pct': 0.04},
        {'type': 'Withdraw from Brokerage', 'year': 2055, 'amount_pct': 0.04},
        {'type': 'Withdraw from Brokerage', 'year': 2056, 'amount_pct': 0.04},
        {'type': 'Withdraw from Brokerage', 'year': 2057, 'amount_pct': 0.04},
        {'type': 'Withdraw from Brokerage', 'year': 2058, 'amount_pct': 0.04},
        {'type': 'Withdraw from Brokerage', 'year': 2059, 'amount_pct': 0.04},
        {'type': 'Withdraw from Brokerage', 'year': 2060, 'amount_pct': 0.04},
    ]
    results = run_projection(a, [primary, rental], debts, events)
    assert len(results) == 35, f"Expected 35 years, got {len(results)}"
    
    # Key sanity checks
    last = results.iloc[-1]
    assert last['Net_Worth'] > 0, "Should have positive net worth after 35 years of saving"
    assert last['Total_Debt'] == 0 or last['Other_Debt'] == 0, "Student loan should be paid off"
    assert last['Property_Value'] > 0, "Should have property"
    assert last['Roth_Balance'] > 0, "Should have Roth balance"
    
    # FI ratio should be tracked
    assert 'FI_Ratio' in results.columns
    # Retirement year row
    r2048 = results[results['Year'] == 2048].iloc[0]
    assert r2048['Gross_Salary'] == 0, "Should stop working at retirement"
    
    # Conversion events
    r2049 = results[results['Year'] == 2049].iloc[0]
    assert r2049['Event_Roth_Conversion'] == 40000

run_test("test_kitchen_sink", test_kitchen_sink)


# ============================================================
# SUMMARY
# ============================================================
print(f"\n{passed}/{passed+failed} TESTS PASSED")
if errors:
    print("\nFAILURES:")
    for name, msg in errors:
        print(f"  {name}: {msg}")
    print("\nSOME TESTS FAILED")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
