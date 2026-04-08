import pandas as pd
import numpy_financial as npf


def calculate_mortgage_payment(loan_amount, annual_rate, years):
    """Calculate monthly mortgage payment"""
    if loan_amount <= 0 or annual_rate <= 0:
        return 0
    return -npf.pmt(annual_rate/12, years*12, loan_amount)

def get_remaining_balance(loan_amount, annual_rate, years, months_paid):
    """Get remaining mortgage balance after N months"""
    if loan_amount <= 0 or months_paid <= 0:
        return loan_amount
    monthly_rate = annual_rate / 12
    total_months = years * 12
    if months_paid >= total_months:
        return 0
    # Calculate remaining balance using FV formula
    # pmt from npf.pmt is negative (payment out), which is correct for fv calculation
    monthly_payment = npf.pmt(monthly_rate, total_months, loan_amount)
    remaining = npf.fv(monthly_rate, months_paid, monthly_payment, loan_amount)
    return abs(remaining)  # Return positive balance

def calculate_federal_tax(taxable_income, filing_status):
    """Calculate federal income tax based on 2026 IRS brackets"""
    if taxable_income <= 0:
        return 0
    
    # 2026 federal tax brackets (IRS inflation-adjusted)
    brackets = {
        "Single": [
            (12400, 0.10),
            (50400, 0.12),
            (105700, 0.22),
            (201775, 0.24),
            (256225, 0.32),
            (640600, 0.35),
            (float('inf'), 0.37)
        ],
        "Married Filing Jointly": [
            (24800, 0.10),
            (100800, 0.12),
            (211400, 0.22),
            (403550, 0.24),
            (512450, 0.32),
            (768700, 0.35),
            (float('inf'), 0.37)
        ],
        "Married Filing Separately": [
            (12400, 0.10),
            (50400, 0.12),
            (105700, 0.22),
            (201775, 0.24),
            (256225, 0.32),
            (384350, 0.35),
            (float('inf'), 0.37)
        ],
        "Head of Household": [
            (17700, 0.10),
            (67450, 0.12),
            (105700, 0.22),
            (201750, 0.24),
            (256200, 0.32),
            (640600, 0.35),
            (float('inf'), 0.37)
        ]
    }
    
    tax_brackets = brackets.get(filing_status, brackets["Single"])
    
    tax = 0
    prev_limit = 0
    for limit, rate in tax_brackets:
        if taxable_income > prev_limit:
            taxable_in_bracket = min(taxable_income, limit) - prev_limit
            tax += taxable_in_bracket * rate
            prev_limit = limit
        else:
            break
    
    return tax


def calculate_sc_state_tax(taxable_income, year):
    """
    Calculate South Carolina state income tax.
    SC uses federal taxable income as starting point.
    Tax rates are being phased down over time (6.2% in 2025, dropping to 6% in 2026+)
    """
    if taxable_income <= 0:
        return 0
    
    # SC tax brackets (same for all filing statuses)
    # These brackets are indexed for inflation annually
    # Using 2025 brackets as baseline
    if year <= 2024:
        top_rate = 0.065  # 6.5% for 2024 and prior
    elif year == 2025:
        top_rate = 0.062  # 6.2% for 2025
    else:
        top_rate = 0.060  # 6.0% for 2026+ (scheduled reduction)
    
    # SC 2025 brackets (adjusted annually for inflation)
    # $0 - $3,560: 0%
    # $3,560 - $17,830: 3%
    # $17,830+: top_rate (6.2% in 2025, 6% in 2026+)
    
    bracket1 = 3560  # 0% bracket
    bracket2 = 17830  # 3% bracket ends
    
    tax = 0
    
    if taxable_income > bracket2:
        # Tax on income over $17,830 at top rate
        tax += (taxable_income - bracket2) * top_rate
        # Tax on $3,560 to $17,830 at 3%
        tax += (bracket2 - bracket1) * 0.03
        # $0 to $3,560 is 0%
    elif taxable_income > bracket1:
        # Tax on income from $3,560 to taxable_income at 3%
        tax += (taxable_income - bracket1) * 0.03
        # $0 to $3,560 is 0%
    # else: income is in 0% bracket
    
    return tax

def calculate_ma_state_tax(taxable_income, year):
    """
    Calculate Massachusetts state income tax.
    """
    if taxable_income <= 0:
        return 0
    
    # MA tax rates from 2025 (same for all filing statuses)
    normal_rate = 0.05
    millionaires_surtax = 0.04
    
    # MA 2025 brackets
    # $0 - $8,000        : 0%
    # $8,000 - $1,083,150: 5% (upper end varies by year)
    # $1,083,150+        : 9%
    bracket1 = 8000 
    
    bracket2 = 0
    if year == 2023:
        bracket2 = 1000000
    elif year == 2024:
        bracket2 = 1053750
    elif year >= 2025:
        bracket2 = 1083150
    
    tax = 0
    
    if (taxable_income > bracket2) and (year >= 2023):
        # Income > bracket2 at highest rate
        tax += (taxable_income - bracket2) * (millionaires_surtax + normal_rate)
        # Income in bracket1 at normal rate
        tax += (bracket2 - bracket1) * normal_rate
    elif taxable_income > bracket1:
        # Income in bracket1 at normal rate at normal rate
        tax += (taxable_income - bracket1) * normal_rate
    # else: income is in 0% bracket
    
    return tax

def calculate_fica_tax(gross_income):
    """Calculate Social Security and Medicare taxes - returns (ss_tax, medicare_tax, total)"""
    ss_limit = 176100  # 2025 SS wage base (adjusted annually by SSA)
    ss_rate = 0.062
    medicare_rate = 0.0145
    additional_medicare_threshold = 200000
    additional_medicare_rate = 0.009
    
    ss_tax = min(gross_income, ss_limit) * ss_rate
    medicare_tax = gross_income * medicare_rate
    
    if gross_income > additional_medicare_threshold:
        medicare_tax += (gross_income - additional_medicare_threshold) * additional_medicare_rate
    
    return ss_tax, medicare_tax, ss_tax + medicare_tax


def get_projected_balances(assumptions, properties, debts):
    """
    Run a quick projection WITHOUT financial events to get baseline account balances.
    Returns a dict of {year: {account: balance}} for planning withdrawals/conversions.
    """
    # Run projection without events
    df = run_projection(assumptions, properties, debts, financial_events=[])
    
    # Extract relevant balances by year
    balances = {}
    for _, row in df.iterrows():
        year = int(row['Year'])
        balances[year] = {
            'trad_retirement': row['Trad_Retirement'],
            'roth_balance': row['Roth_Balance'],
            'roth_contributions': row['Roth_Contributions'],
            'portfolio': row['Portfolio'],
            'crypto': row['Crypto'],
            'hsa': row['HSA_Balance'],
            'cash': row['Cash'],
            'age': row['Age'],
            'gross_salary': row.get('Gross_Salary', 0),
        }
    return balances


def run_projection(assumptions, properties, debts, financial_events=None):
    """Run the full financial projection with detailed Roth/HSA/Tax tracking and crypto"""
    if financial_events is None:
        financial_events = []
    
    years = list(range(assumptions['start_year'], assumptions['end_year'] + 1))
    results = []
    
    # Initialize from assumptions
    cash = assumptions['current_cash']
    portfolio = assumptions['current_portfolio']
    crypto = assumptions.get('current_crypto', 0)
    
    # Cost basis tracking for capital gains calculations
    brokerage_cost_basis = assumptions['current_portfolio']  # Tracks cumulative contributions
    crypto_cost_basis = assumptions.get('current_crypto', 0)
    
    # Traditional retirement (401k/IRA)
    trad_retirement = assumptions.get('current_401k', assumptions.get('current_retirement', 100000))
    
    # Roth IRA tracking
    roth_balance = assumptions.get('current_roth_balance', 0)
    roth_contributions = assumptions.get('current_roth_contributions', 0)  # Basis - withdrawable anytime
    roth_first_year = assumptions.get('roth_first_contrib_year', assumptions['start_year'])
    
    # Roth Conversion Ladder tracking - dict of {conversion_year: amount}
    # After 5 years, these become accessible penalty-free
    roth_conversions = {}  # {year: amount} - tracks each year's conversions
    
    # HSA tracking
    hsa_balance = assumptions.get('current_hsa', 0)
    
    for year in years:
        year_idx = year - assumptions['start_year']
        is_working = year < assumptions['retirement_year']
        age = year - assumptions.get('birth_year', 1990)
        
        # === INCOME & CONTRIBUTIONS ===
        if is_working:
            gross_salary = assumptions['current_salary'] * ((1 + assumptions['salary_growth']) ** year_idx)
            contrib_401k = assumptions.get('contrib_401k', assumptions.get('retirement_contribution', 23000))
            employer_401k = assumptions.get('employer_401k', 0)
            contrib_roth = assumptions.get('contrib_roth', 7000)
            contrib_hsa = assumptions.get('contrib_hsa', 4150)
            employer_hsa = assumptions.get('employer_hsa', 0)
            contrib_brokerage = assumptions.get('contrib_brokerage', 0)
            contrib_crypto = assumptions.get('contrib_crypto', 0)
        else:
            gross_salary = 0
            contrib_401k = 0
            employer_401k = 0
            contrib_roth = 0
            contrib_hsa = 0
            employer_hsa = 0
            contrib_brokerage = 0
            contrib_crypto = 0
        
        # Total employee contributions (deducted from income)
        total_contributions = contrib_401k + contrib_roth + contrib_hsa + contrib_brokerage + contrib_crypto
        # Total 401k and HSA contributions including employer (for account growth)
        total_401k_contrib = contrib_401k + employer_401k
        total_hsa_contrib = contrib_hsa + employer_hsa
        
        # === EXPENSES (calculate first, needed for tax deductions) ===
        base_expenses = assumptions['annual_expenses'] * ((1 + assumptions['inflation']) ** year_idx)
        
        # Rent (only if not owning primary residence)
        owns_primary = any(
            p['is_primary'] and year >= p['purchase_year'] 
            for p in properties
        )
        if owns_primary:
            rent_expense = 0
        else:
            rent_expense = assumptions['monthly_rent'] * 12 * ((1 + assumptions['inflation']) ** year_idx)
        
        total_living_expenses = base_expenses + rent_expense
        
        # === REAL ESTATE (calculate before taxes - need mortgage interest for deductions) ===
        total_rent_income = 0
        total_property_expenses = 0
        total_debt_service = 0
        total_property_value = 0
        total_property_debt = 0
        property_purchase_costs = 0
        primary_mortgage_payment = 0
        primary_property_tax = 0
        primary_mortgage_interest = 0  # Track interest for itemized deductions
        
        for prop in properties:
            if year == prop['purchase_year']:
                down_payment = prop['purchase_price'] * prop['down_payment_pct']
                closing_costs = prop.get('closing_costs', 0)
                repair_cost = prop.get('repair_cost', 0)
                lender_points = prop.get('lender_points', 0)
                other_fees = prop.get('other_fees', 0)
                property_purchase_costs += down_payment + closing_costs + repair_cost + lender_points + other_fees
            
            if year >= prop['purchase_year']:
                years_owned = year - prop['purchase_year']
                months_owned = years_owned * 12 + 6
                
                base_value = prop.get('arv', prop['purchase_price'])
                prop_value = base_value * ((1 + assumptions['property_appreciation']) ** years_owned)
                total_property_value += prop_value
                
                loan_amount = prop['purchase_price'] * (1 - prop['down_payment_pct'])
                monthly_payment = calculate_mortgage_payment(loan_amount, prop['mortgage_rate'], prop['mortgage_years'])
                
                # Calculate approximate mortgage interest for the year
                # Early in loan, most payment is interest; this is a simplified approximation
                remaining_balance = max(0, get_remaining_balance(loan_amount, prop['mortgage_rate'], prop['mortgage_years'], months_owned))
                annual_interest = remaining_balance * prop['mortgage_rate']  # Approximate annual interest
                
                pmi_rate = prop.get('pmi_rate', 0)
                if prop['down_payment_pct'] < 0.20 and pmi_rate > 0:
                    equity_pct = (prop_value - remaining_balance) / prop_value if prop_value > 0 else 0
                    monthly_pmi = (loan_amount * pmi_rate / 12) if equity_pct < 0.20 else 0
                else:
                    monthly_pmi = 0
                
                annual_payment = (monthly_payment + monthly_pmi) * 12
                total_property_debt += remaining_balance
                
                prop_tax_rate = prop.get('property_tax_rate', assumptions.get('property_tax_rate', 0.012))
                annual_prop_tax = prop_value * prop_tax_rate
                
                if prop['is_primary']:
                    primary_mortgage_payment += annual_payment
                    primary_property_tax += annual_prop_tax
                    primary_mortgage_interest += annual_interest  # For itemized deduction
                else:
                    vacancy_rate = prop.get('vacancy_rate', assumptions.get('vacancy_rate', 0.05))
                    rent_per_unit = prop.get('rent_per_unit', prop.get('monthly_rent', 0))
                    num_units = prop.get('num_units', 1)
                    other_income = prop.get('other_monthly_income', 0) * 12
                    
                    gross_rent = (rent_per_unit * num_units * 12 + other_income) * ((1 + assumptions['rent_growth']) ** years_owned)
                    effective_rent = gross_rent * (1 - vacancy_rate)
                    
                    insurance = prop.get('insurance_monthly', prop_value * assumptions.get('insurance_rate', 0.005) / 12) * 12
                    capex = effective_rent * prop.get('capex_rate', assumptions.get('maintenance_rate', 0.05))
                    management = effective_rent * prop.get('management_rate', assumptions.get('management_fee', 0.08))
                    hoa = prop.get('hoa_monthly', 0) * 12
                    utilities = prop.get('utilities_monthly', 0) * 12
                    other_exp = prop.get('other_monthly_expenses', 0) * 12
                    
                    # Rental expenses include mortgage interest (deductible against rental income)
                    prop_expenses = annual_prop_tax + insurance + capex + management + hoa + utilities + other_exp
                    
                    total_rent_income += effective_rent
                    total_property_expenses += prop_expenses + annual_interest  # Interest is deductible for rentals
                    total_debt_service += annual_payment - annual_interest  # Principal portion only
        
        net_rental_income = total_rent_income - total_property_expenses - total_debt_service
        total_equity = total_property_value - total_property_debt
        
        # === PROCESS FINANCIAL EVENTS (before tax calc so conversions are taxed properly) ===
        # Track event impacts for this year
        event_roth_conversion = 0
        event_roth_withdrawal = 0
        event_brokerage_withdrawal = 0
        event_crypto_withdrawal = 0
        event_401k_withdrawal = 0
        event_capital_gains_tax = 0
        event_penalties_paid = 0
        event_cash_inflow = 0  # Net cash from withdrawals (after taxes)
        event_roth_earnings_taxed = 0  # Track Roth earnings that are taxed
        
        # Get events for this year
        year_events = [e for e in financial_events if e['year'] == year]
        
        for event in year_events:
            event_type = event['type']
            # Support both absolute `amount` and percentage-based `amount_pct`.
            # `amount_pct` can be provided as a decimal (0.05) or percent (5 -> treated as 5%).
            amount = event.get('amount', 0)
            if 'amount_pct' in event:
                pct = event.get('amount_pct', 0)
                # Accept either 0.05 or 5 -> normalize to 0.05
                if pct > 1:
                    pct = pct / 100.0
                # Derive base amount from the relevant account depending on event type
                if "Roth Conversion" in event_type:
                    amount = trad_retirement * pct
                elif event_type == "Withdraw from Roth":
                    amount = roth_balance * pct
                elif event_type == "Withdraw from Brokerage":
                    amount = portfolio * pct
                elif event_type == "Withdraw from Crypto":
                    amount = crypto * pct
                elif event_type == "Withdraw from 401k/IRA":
                    amount = trad_retirement * pct
                else:
                    # leave amount as-is for unsupported event types
                    amount = event.get('amount', 0)
            
            if "Roth Conversion" in event_type:
                # Convert from 401k/IRA to Roth - this is TAXABLE as ordinary income
                actual_amount = min(amount, trad_retirement)
                if actual_amount > 0:
                    trad_retirement -= actual_amount
                    roth_balance += actual_amount
                    # Track conversion year for 5-year rule
                    if year not in roth_conversions:
                        roth_conversions[year] = 0
                    roth_conversions[year] += actual_amount
                    event_roth_conversion += actual_amount
                    # Tax will be calculated below as part of AGI
                    
            elif event_type == "Withdraw from Roth":
                # Roth withdrawal - contributions first (tax-free), then earnings
                actual_amount = min(amount, roth_balance)
                if actual_amount > 0:
                    # First use contributions (tax-free, penalty-free)
                    from_contributions = min(actual_amount, roth_contributions)
                    remaining = actual_amount - from_contributions
                    
                    # Then use seasoned conversions (5+ years old, tax-free, penalty-free)
                    seasoned_available = sum(
                        amt for conv_year, amt in roth_conversions.items() 
                        if year - conv_year >= 5
                    )
                    from_seasoned = min(remaining, seasoned_available)
                    remaining -= from_seasoned
                    
                    # Reduce seasoned conversion tracking
                    if from_seasoned > 0:
                        temp_remaining = from_seasoned
                        for conv_year in sorted(roth_conversions.keys()):
                            if year - conv_year >= 5 and temp_remaining > 0:
                                use = min(temp_remaining, roth_conversions[conv_year])
                                roth_conversions[conv_year] -= use
                                temp_remaining -= use
                    
                    # Any remaining comes from earnings (taxed + penalty if under 59.5)
                    from_earnings = remaining
                    
                    # Update balances
                    roth_contributions -= from_contributions
                    roth_balance -= actual_amount
                    event_roth_withdrawal += actual_amount
                    
                    # Tax on earnings portion if under 59.5
                    if from_earnings > 0 and age < 59.5:
                        # Earnings are taxed as ordinary income + 10% penalty
                        event_roth_earnings_taxed += from_earnings
                        penalty = from_earnings * 0.10
                        event_penalties_paid += penalty
                        event_cash_inflow += actual_amount - penalty  # Tax deducted via AGI
                    else:
                        event_cash_inflow += actual_amount  # Full amount, no tax
                    
            elif event_type == "Withdraw from Brokerage":
                # Withdraw from brokerage - capital gains tax on gains portion
                actual_amount = min(amount, portfolio)
                if actual_amount > 0:
                    portfolio -= actual_amount
                    # Calculate gains based on actual cost basis
                    gains_ratio = max(0, (portfolio + actual_amount - brokerage_cost_basis) / (portfolio + actual_amount)) if (portfolio + actual_amount) > 0 else 0
                    gains_portion = actual_amount * gains_ratio
                    cap_gains_tax = gains_portion * 0.15
                    # Reduce cost basis proportionally
                    brokerage_cost_basis -= actual_amount * (1 - gains_ratio)
                    brokerage_cost_basis = max(0, brokerage_cost_basis)
                    event_capital_gains_tax += cap_gains_tax
                    event_brokerage_withdrawal += actual_amount
                    event_cash_inflow += actual_amount - cap_gains_tax
                    
            elif event_type == "Withdraw from Crypto":
                # Withdraw from crypto - capital gains tax
                actual_amount = min(amount, crypto)
                if actual_amount > 0:
                    crypto -= actual_amount
                    # Calculate gains based on actual cost basis
                    gains_ratio = max(0, (crypto + actual_amount - crypto_cost_basis) / (crypto + actual_amount)) if (crypto + actual_amount) > 0 else 0
                    gains_portion = actual_amount * gains_ratio
                    cap_gains_tax = gains_portion * 0.15
                    # Reduce cost basis proportionally
                    crypto_cost_basis -= actual_amount * (1 - gains_ratio)
                    crypto_cost_basis = max(0, crypto_cost_basis)
                    event_capital_gains_tax += cap_gains_tax
                    event_crypto_withdrawal += actual_amount
                    event_cash_inflow += actual_amount - cap_gains_tax
                    
            elif event_type == "Withdraw from 401k/IRA":
                # 401k/IRA withdrawal - ordinary income + 10% penalty if under 59.5
                actual_amount = min(amount, trad_retirement)
                if actual_amount > 0:
                    trad_retirement -= actual_amount
                    event_401k_withdrawal += actual_amount
                    # Penalty if under 59.5
                    penalty = actual_amount * 0.10 if age < 59.5 else 0
                    event_penalties_paid += penalty
                    # Tax will be calculated below as part of AGI
                    # Cash inflow is amount minus penalty (income tax calculated below)
                    event_cash_inflow += actual_amount - penalty
        
        # Calculate total seasoned conversions available for display
        seasoned_conversions_available = sum(
            amt for conv_year, amt in roth_conversions.items() 
            if year - conv_year >= 5
        )
        
        # === TAX CALCULATIONS ===
        # 2026 Standard deductions (IRS)
        std_deduction_base = {
            "Single": 15000,
            "Married Filing Jointly": 30000,
            "Married Filing Separately": 15000,
            "Head of Household": 22500
        }.get(assumptions.get('filing_status', 'Married Filing Jointly'), 30000)
        
        # Adjust standard deduction for inflation from base year
        base_year = 2026
        if year > base_year:
            std_deduction_base = std_deduction_base * ((1 + assumptions['inflation']) ** (year - base_year))
        
        # Pre-tax deductions (reduce federal & state taxable income, but NOT FICA wages)
        pre_tax_deductions = contrib_401k + contrib_hsa
        
        # AGI includes: salary + Roth conversions + 401k withdrawals + taxable Roth earnings + taxable rental income
        taxable_event_income = event_roth_conversion + event_401k_withdrawal + event_roth_earnings_taxed
        # Taxable rental income: rent - expenses - interest (excludes mortgage principal, which is not deductible)
        taxable_rental_income = total_rent_income - total_property_expenses
        # Calculate dividends early (needed for dividend tax in total_tax)
        dividends = portfolio * assumptions['dividend_yield']
        agi = gross_salary - pre_tax_deductions + taxable_event_income + taxable_rental_income
        
        # === ITEMIZED vs STANDARD DEDUCTION ===
        # Itemized deductions for W-2 employee:
        # 1. Mortgage interest on primary residence (up to $750k loan)
        # 2. SALT (State & Local Tax) - capped at $10,000
        # 3. Charitable donations (we won't track this - too complex)
        
        # Calculate state tax for SALT (estimate using prior year's rate)
        state = assumptions.get('state', 'SC')
        if state == 'SC':
            est_state_tax = calculate_sc_state_tax(max(0, agi - std_deduction_base), year)
        elif state == 'MA':
            est_state_tax = calculate_ma_state_tax(max(0, agi - std_deduction_base), year)
        else:
            est_state_tax = max(0, agi - std_deduction_base) * assumptions.get('state_tax_rate', 0.05)
        
        # SALT deduction = state income tax + property tax (primary), capped at $10,000
        salt_deduction = min(10000, est_state_tax + primary_property_tax)
        
        # Itemized total
        itemized_deductions = primary_mortgage_interest + salt_deduction
        
        # Use whichever is higher
        if itemized_deductions > std_deduction_base:
            actual_deduction = itemized_deductions
            using_itemized = True
        else:
            actual_deduction = std_deduction_base
            using_itemized = False
        
        # Taxable income after deduction
        taxable_income = max(0, agi - actual_deduction)
        
        # Federal tax (based on taxable income after deductions)
        federal_tax = calculate_federal_tax(taxable_income, assumptions.get('filing_status', 'Married Filing Jointly'))
        
        # State tax - South Carolina uses federal taxable income as starting point
        if state == 'SC':
            state_tax = calculate_sc_state_tax(taxable_income, year)
        elif state == 'MA':
            state_tax = calculate_ma_state_tax(taxable_income, year)
        else:
            state_tax = max(0, taxable_income) * assumptions.get('state_tax_rate', 0.05)
        
        # FICA (Social Security + Medicare) - based on GROSS salary only, NOT on Roth conversions
        if is_working:
            ss_tax, medicare_tax, fica_tax = calculate_fica_tax(gross_salary)
        else:
            ss_tax, medicare_tax, fica_tax = 0, 0, 0
        
        # Total tax includes: income tax (federal + state) + FICA + capital gains + penalties + dividend tax
        total_income_tax = federal_tax + state_tax + fica_tax
        total_event_tax = event_capital_gains_tax + event_penalties_paid
        dividend_tax = dividends * 0.15  # Qualified dividends taxed at LTCG rate
        total_tax = total_income_tax + total_event_tax + dividend_tax
        
        # Calculate tax specifically on event income (for reporting)
        # This is the additional tax due to conversions/withdrawals
        if taxable_event_income > 0:
            # Tax without events (but WITH rental income since that's not an event)
            agi_without_events = gross_salary - pre_tax_deductions + taxable_rental_income
            taxable_without_events = max(0, agi_without_events - actual_deduction)
            federal_without_events = calculate_federal_tax(taxable_without_events, assumptions.get('filing_status', 'Married Filing Jointly'))
            if state == 'SC':
                state_without_events = calculate_sc_state_tax(taxable_without_events, year)
            elif state == 'MA':
                state_without_events = calculate_ma_state_tax(taxable_without_events, year)
            else:
                state_without_events = taxable_without_events * assumptions.get('state_tax_rate', 0.05)
            event_income_tax = (federal_tax - federal_without_events) + (state_tax - state_without_events)
        else:
            event_income_tax = 0
        
        # Total taxes from events (income tax on conversions + cap gains + penalties)
        event_taxes_paid = event_income_tax + event_capital_gains_tax + event_penalties_paid
        
        # Calculate tax savings from pre-tax contributions + itemizing
        taxable_without_pretax = max(0, gross_salary + taxable_rental_income - std_deduction_base)
        federal_without_pretax = calculate_federal_tax(taxable_without_pretax, assumptions.get('filing_status', 'Married Filing Jointly'))
        if state == 'SC':
            state_without_pretax = calculate_sc_state_tax(taxable_without_pretax, year)
        elif state == 'MA':
            state_without_pretax = calculate_ma_state_tax(taxable_without_pretax, year)
        else:
            state_without_pretax = taxable_without_pretax * assumptions.get('state_tax_rate', 0.05)
        tax_savings_from_pretax = (federal_without_pretax - federal_without_events if taxable_event_income > 0 else federal_without_pretax - federal_tax) + (state_without_pretax - (state_without_events if taxable_event_income > 0 else state_tax))
        
        # Net income after taxes and pre-tax contributions (from salary only)
        net_income = gross_salary - pre_tax_deductions - total_income_tax - contrib_roth
        
        # === INVESTMENTS & GROWTH ===
        # portfolio_return is total return (e.g. 7%); dividends come FROM it, not on top
        # Note: dividends already calculated above (before tax section)
        portfolio_growth = portfolio * max(0, assumptions['portfolio_return'] - assumptions['dividend_yield'])
        crypto_growth = crypto * assumptions.get('crypto_return', 0.10)
        
        trad_retirement_growth = trad_retirement * assumptions['portfolio_return']
        roth_growth = roth_balance * assumptions['portfolio_return']
        hsa_growth = hsa_balance * assumptions['portfolio_return']
        
        # === EXISTING DEBTS ===
        total_other_debt = 0
        total_debt_payments = 0
        
        for debt in debts:
            if debt['start_year'] <= assumptions['start_year']:
                months_into_debt = (year - assumptions['start_year']) * 12 + debt['months_already_paid']
            else:
                if year < debt['start_year']:
                    continue
                months_into_debt = (year - debt['start_year']) * 12 + 6
            
            total_months = debt['term_years'] * 12
            if months_into_debt >= total_months:
                continue
            
            remaining = max(0, get_remaining_balance(
                debt['original_balance'], debt['interest_rate'], debt['term_years'], months_into_debt
            ))
            total_other_debt += remaining
            
            monthly_pmt = calculate_mortgage_payment(debt['original_balance'], debt['interest_rate'], debt['term_years'])
            months_left_on_loan = total_months - months_into_debt
            months_paying_this_year = min(12, months_left_on_loan)
            annual_pmt = monthly_pmt * months_paying_this_year
            total_debt_payments += annual_pmt
        
        # === CASH FLOW CALCULATION ===
        # Income includes: salary net income + dividends (after tax) + rental cash flow + withdrawal event cash
        # Note: rental income tax is already included in total_income_tax (via AGI), reducing net_income
        cash_inflow = net_income + (dividends - dividend_tax) + max(0, net_rental_income) + event_cash_inflow
        
        # Expenses (includes ALL contributions as outflows)
        housing_cost = primary_mortgage_payment + primary_property_tax if owns_primary else 0
        # Note: Taxable contributions (brokerage, crypto) come from cash flow
        taxable_contributions = contrib_brokerage + contrib_crypto
        # Include property purchase costs (down payments, closing costs, repairs) in outflow
        # Note: Income tax on Roth conversions / 401k withdrawals is already deducted from net_income (via total_income_tax)
        cash_outflow = (total_living_expenses + housing_cost + total_debt_payments + 
                        taxable_contributions + property_purchase_costs)
        
        if net_rental_income < 0:
            cash_outflow += abs(net_rental_income)
        
        # Discretionary cash can be negative when buying property
        discretionary_cash = cash_inflow - cash_outflow
        
        # Cash savings only when discretionary cash is positive
        cash_savings = max(0, discretionary_cash * assumptions.get('cash_savings_rate', 0.10)) if (is_working and discretionary_cash > 0) else 0
        
        # Net cash flow (can be negative in property purchase years)
        net_cash_flow = discretionary_cash - cash_savings
        
        # === UPDATE ACCOUNT BALANCES ===
        
        # Update cash - allow it to go negative (indicates need for financing)
        cash = cash + net_cash_flow
        
        # Update retirement accounts (include employer contributions)
        # Note: trad_retirement already had conversions/withdrawals deducted above
        trad_retirement = trad_retirement + trad_retirement_growth + total_401k_contrib
        
        # Note: roth_balance already had conversions added and withdrawals deducted above
        roth_balance = roth_balance + roth_growth + contrib_roth
        roth_contributions = roth_contributions + contrib_roth  # Track contribution basis
        
        # Recalculate earnings (balance - contributions - unseasoned conversions)
        total_conversions_remaining = sum(roth_conversions.values())
        roth_earnings = max(0, roth_balance - roth_contributions - total_conversions_remaining)
        
        # HSA includes employer contribution
        hsa_balance = hsa_balance + hsa_growth + total_hsa_contrib
        
        # Update taxable accounts (already had withdrawals deducted above)
        portfolio = portfolio + portfolio_growth + contrib_brokerage
        crypto = crypto + crypto_growth + contrib_crypto
        
        # Update cost bases (contributions increase basis, growth does not)
        brokerage_cost_basis += contrib_brokerage
        crypto_cost_basis += contrib_crypto
        
        # === ROTH IRA WITHDRAWAL AVAILABILITY ===
        # Contributions: Always available tax/penalty free
        roth_contrib_available = roth_contributions
        
        # 5-year rule check
        years_since_first_contrib = year - roth_first_year
        five_year_rule_met = years_since_first_contrib >= 5
        
        # Earnings availability
        age_59_5 = age >= 59.5
        
        if age_59_5 and five_year_rule_met:
            # Qualified distribution - all earnings available tax/penalty free
            roth_earnings_available = roth_earnings
            roth_withdrawal_note = "Qualified: All funds accessible tax-free"
        elif age_59_5 and not five_year_rule_met:
            # Over 59.5 but 5-year not met - earnings taxable but no penalty
            roth_earnings_available = roth_earnings  # Available but taxable
            roth_withdrawal_note = f"Earnings taxable (5-yr rule in {roth_first_year + 5})"
        else:
            # Under 59.5 - only contributions accessible penalty-free
            roth_earnings_available = 0
            roth_withdrawal_note = f"Only contributions accessible until age 59½"
        
        roth_total_available = roth_contrib_available + roth_earnings_available + seasoned_conversions_available
        
        # === HSA AVAILABILITY ===
        # HSA is always available for qualified medical expenses
        # After 65, available for anything (taxed like traditional IRA)
        hsa_medical_available = hsa_balance
        hsa_any_purpose_available = hsa_balance if age >= 65 else 0
        
        # === NET WORTH ===
        total_debt = total_property_debt + total_other_debt
        net_worth = (cash + portfolio + crypto + trad_retirement + roth_balance + hsa_balance + 
                     total_property_value - total_debt)
        
        # === ACCESSIBLE FUNDS (what you can actually use) ===
        # Cash + Taxable Portfolio (95%) + Crypto (80%) + Roth Contributions + (Roth Earnings if qualified) + HSA (if 65+)
        accessible_portfolio = portfolio * 0.95  # 5% tax drag
        accessible_crypto = crypto * 0.80  # 20% tax drag for crypto
        accessible_liquid = cash + accessible_portfolio + accessible_crypto + roth_contrib_available
        if age_59_5 and five_year_rule_met:
            accessible_liquid += roth_earnings
        if age >= 65:
            accessible_liquid += hsa_balance
        
        # === FI RATIO ===
        passive_income = dividends + max(0, net_rental_income)
        # Total expenses includes property purchase costs for cash flow tracking
        total_annual_expenses = total_living_expenses + housing_cost + total_debt_payments + property_purchase_costs
        # FI ratio uses recurring expenses only (exclude one-time property purchase costs)
        recurring_expenses = total_living_expenses + housing_cost + total_debt_payments
        fi_ratio = passive_income / recurring_expenses if recurring_expenses > 0 else 0
        
        results.append({
            'Year': year,
            'Age': age,
            'Working': is_working,
            'Gross_Salary': gross_salary,
            'Pre_Tax_Deductions': pre_tax_deductions,
            'AGI': agi,
            'Std_Deduction': std_deduction_base,
            'Itemized_Deduction': itemized_deductions,
            'Using_Itemized': using_itemized,
            'Actual_Deduction': actual_deduction,
            'Mortgage_Interest': primary_mortgage_interest,
            'SALT_Deduction': salt_deduction,
            'Taxable_Income': taxable_income,
            'Federal_Tax': federal_tax,
            'State_Tax': state_tax,
            'SS_Tax': ss_tax,
            'Medicare_Tax': medicare_tax,
            'FICA_Tax': fica_tax,
            'Dividend_Tax': dividend_tax,
            'Total_Tax': total_tax,
            'Tax_Savings_PreTax': tax_savings_from_pretax,
            'Effective_Tax_Rate': (total_tax / gross_salary * 100) if gross_salary > 0 else 0,
            'Net_Income': net_income,
            'Contrib_401k': contrib_401k,
            'Employer_401k': employer_401k,
            'Total_401k_Contrib': total_401k_contrib,
            'Contrib_Roth': contrib_roth,
            'Contrib_HSA': contrib_hsa,
            'Employer_HSA': employer_hsa,
            'Total_HSA_Contrib': total_hsa_contrib,
            'Contrib_Brokerage': contrib_brokerage,
            'Contrib_Crypto': contrib_crypto,
            'Total_Contributions': total_contributions,
            'Living_Expenses': total_living_expenses,
            'Housing_Cost': housing_cost,
            'Debt_Payments': total_debt_payments,
            'Total_Expenses': total_annual_expenses,
            'Discretionary_Cash': discretionary_cash,
            'Net_Cash_Flow': net_cash_flow,
            'Cash_Savings': cash_savings,
            'Dividends': dividends,
            'Rental_Income': total_rent_income,
            'Rental_Expenses': total_property_expenses + total_debt_service,
            'Net_Rental': net_rental_income,
            'Passive_Income': passive_income,
            'Property_Purchase_Costs': property_purchase_costs,
            # Financial Events
            'Event_Roth_Conversion': event_roth_conversion,
            'Event_Roth_WD': event_roth_withdrawal,
            'Event_Brokerage_WD': event_brokerage_withdrawal,
            'Event_Crypto_WD': event_crypto_withdrawal,
            'Event_401k_WD': event_401k_withdrawal,
            'Event_Taxes_Paid': event_taxes_paid,
            'Event_Penalties_Paid': event_penalties_paid,
            'Seasoned_Conversions_Avail': seasoned_conversions_available,
            # Account Balances
            'Cash': cash,
            'Portfolio': portfolio,
            'Crypto': crypto,
            'Accessible_Portfolio': accessible_portfolio,
            'Accessible_Crypto': accessible_crypto,
            'Trad_Retirement': trad_retirement,
            'Roth_Balance': roth_balance,
            'Roth_Contributions': roth_contributions,
            'Roth_Earnings': roth_earnings,
            'Roth_Available': roth_total_available,
            'Roth_Note': roth_withdrawal_note,
            'HSA_Balance': hsa_balance,
            'Property_Value': total_property_value,
            'Property_Debt': total_property_debt,
            'Property_Equity': total_equity,
            'Other_Debt': total_other_debt,
            'Total_Debt': total_debt,
            'Net_Worth': net_worth,
            'Accessible_Liquid': accessible_liquid,
            'FI_Ratio': fi_ratio
        })
    
    return pd.DataFrame(results)
