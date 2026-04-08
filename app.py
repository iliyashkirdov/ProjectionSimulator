import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

from calculations import (
    calculate_mortgage_payment,
    get_remaining_balance,
    calculate_federal_tax,
    calculate_sc_state_tax,
    calculate_fica_tax,
    get_projected_balances,
    run_projection,
)
from scenarios import (
    save_scenario,
    load_scenario,
    delete_scenario,
    get_saved_scenarios,
)
from charts import (
    render_net_worth_tab,
    render_cash_flow_tab,
    render_retirement_tab,
    render_real_estate_tab,
    render_taxes_tab,
    render_fi_progress_tab,
    render_debt_payoff_tab,
    render_withdrawals_tab,
    render_full_data_tab,
)

st.set_page_config('Financial Projection Simulator', '💰', 'wide')

# ============================================
# WELCOME GUIDE
# ============================================
if 'seen_welcome' not in st.session_state:
    with st.expander('👋 Welcome! Click here for a quick start guide', True):
        st.markdown("""
        ### Welcome to the Financial Projection Simulator
        
        This tool helps you plan your path to **Financial Independence (FI)** — the point where 
        your investments and passive income cover all your living expenses, giving you the freedom 
        to work because you *want* to, not because you *have* to.
        
        ---
        
        #### 🔥 What is FIRE?
        **Financial Independence, Retire Early** is a movement focused on aggressive saving and 
        investing so you can retire decades earlier than traditional retirement age. There are 
        several approaches:
        
        | Strategy | Description | Typical Savings Rate |
        |----------|-------------|---------------------|
        | **Lean FIRE** | Retire on a minimalist budget ($25-40K/year) | 50-70% |
        | **Traditional FIRE** | Maintain a moderate lifestyle ($40-80K/year) | 40-60% |
        | **Fat FIRE** | Retire with a comfortable/luxury budget ($100K+/year) | 30-50% |
        | **Coast FIRE** | Save enough early that compound growth handles the rest, then work a low-stress job | Variable |
        | **Barista FIRE** | Semi-retire with a part-time job for benefits while investments grow | Variable |
        
        **This simulator lets you model any of these strategies** by adjusting your income, expenses, 
        savings, and investment assumptions.
        
        ---
        
        #### 🚀 Quick Setup (5 minutes)
        
        1. **📊 Sidebar (left)** — Enter your current financial situation
           - Personal info (birth year, tax filing status, state)
           - Income and annual contributions to each account type
           - Current account balances
        
        2. **🏠 Properties** — Add any planned property purchases
           - A primary residence replaces your rent expense
           - Rental properties generate passive income toward FI
        
        3. **📅 Financial Events** — Plan how you'll access your money in retirement
           - Roth conversions to build a tax-free withdrawal ladder
           - Withdrawals from different accounts at different ages
        
        4. **📈 View Results** — See your projected net worth, FI ratio, and cash flow
        
        ---
        
        #### 💡 Tips
        - **Start simple**: Just fill in the sidebar to see a basic projection
        - **Save your work**: Use *Save Scenario* so you don't lose your inputs
        - **Try the sample**: Import `sample_scenario.json` to see an example setup
        - **Compare strategies**: Save different scenarios (e.g., "Lean FIRE" vs "With Rental Property") and compare results
        - **Scroll down**: The best insights are in the chart tabs — especially FI Progress and Withdrawals
        
        *Click below to close this guide. You won't see it again.*
        """)
        if st.button("Got it! Don't show this again"):
            st.session_state.seen_welcome = True
            st.rerun()

# ============================================
# TITLE & SESSION STATE
# ============================================
st.title('💰 Financial Projection Simulator')
st.markdown('*Plan your path to financial independence*')

if 'properties' not in st.session_state:
    st.session_state.properties = []

if 'debts' not in st.session_state:
    st.session_state.debts = []

if 'financial_events' not in st.session_state:
    st.session_state.financial_events = []

if 'editing_property_idx' not in st.session_state:
    st.session_state.editing_property_idx = None

if 'just_imported' not in st.session_state:
    st.session_state.just_imported = False

# ============================================
# SAVE / LOAD SCENARIOS
# ============================================
def loadAssumptions(a):
    for key, widget_key in [
        ('filing_status', 'w_filing_status'), ('state', 'w_state'),
        ('birth_year', 'w_birth_year'), ('current_salary', 'w_salary'),
        ('salary_growth', 'w_salary_growth'), ('contrib_401k', 'w_401k_contrib'),
        ('employer_401k', 'w_401k_employer'), ('contrib_roth', 'w_roth_contrib'),
        ('contrib_hsa', 'w_hsa_contrib'), ('employer_hsa', 'w_hsa_employer'),
        ('contrib_brokerage', 'w_brokerage_contrib'), ('contrib_crypto', 'w_crypto_contrib'),
        ('annual_expenses', 'w_expenses'), ('monthly_rent', 'w_rent'),
        ('cash_savings_rate', 'w_cash_savings'),
        ('current_cash', 'w_cash'), ('current_portfolio', 'w_portfolio'),
        ('current_crypto', 'w_crypto'), ('current_401k', 'w_401k'),
        ('current_roth_balance', 'w_roth_balance'),
        ('current_roth_contributions', 'w_roth_contributions'),
        ('roth_first_contrib_year', 'w_roth_first_year'),
        ('current_hsa', 'w_hsa'),
        ('portfolio_return', 'w_portfolio_return'), ('crypto_return', 'w_crypto_return'),
        ('dividend_yield', 'w_dividend_yield'),
        ('property_appreciation', 'w_appreciation'), ('rent_growth', 'w_rent_growth'),
        ('start_year', 'w_start_year'), ('end_year', 'w_end_year'),
        ('retirement_year', 'w_retirement_year'),
    ]:
        if key in a:
            val = a[key]
            if key in ('salary_growth', 'inflation', 'portfolio_return', 'dividend_yield',
                        'property_appreciation', 'rent_growth', 'crypto_return'):
                val = val * 100 if val < 1 else val
            if key == 'cash_savings_rate':
                val = int(val * 100) if val < 1 else int(val)
            if key == 'inflation':
                val = val * 100 if val < 1 else val
            st.session_state[widget_key] = val        

with st.expander('💾 Save / Load Scenarios', False):
    col1, col2, col3 = st.columns((2, 2, 2))
    
    with col1:
        st.markdown('**Save Current Scenario**')
        save_name = st.text_input('Scenario Name', 'My Scenario', key='save_name')
        if st.button('💾 Save Scenario', type='primary'):
            st.session_state.pending_save = save_name
    
    saved_scenarios = get_saved_scenarios()
    
    with col2:
        st.markdown('**Load Saved Scenario**')
        if saved_scenarios:
            selected_scenario = st.selectbox('Select Scenario', [''] + saved_scenarios)
            if st.button('📂 Load Scenario'):
                if selected_scenario:
                    loaded = load_scenario(selected_scenario)
                    if loaded:
                        if 'assumptions' in loaded:
                            loadAssumptions(loaded['assumptions'])
                        if 'properties' in loaded:
                            st.session_state.properties = loaded['properties']
                        if 'debts' in loaded:
                            st.session_state.debts = loaded['debts']
                        if 'financial_events' in loaded:
                            st.session_state.financial_events = loaded['financial_events']
                        st.success(f"Loaded '{selected_scenario}'!")
                        st.rerun()
        else:
            st.info('No saved scenarios yet')
    
    with col3:
        st.markdown('**Manage Scenarios**')
        if saved_scenarios:
            delete_scenario_name = st.selectbox('Select to Delete', [''] + saved_scenarios, key='delete_select')
            if st.button('🗑️ Delete Scenario'):
                if delete_scenario_name:
                    delete_scenario(delete_scenario_name)
                    st.success(f"Deleted '{delete_scenario_name}'")
                    st.rerun()
    
    st.markdown('---')
    col_exp, col_imp = st.columns(2)
    
    with col_exp:
        st.markdown('**📤 Export Scenario (Download)**')
        if st.session_state.get('export_json'):
            st.download_button(
                label='📥 Download Scenario JSON',
                data=st.session_state.export_json,
                file_name=f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime='application/json',
                key='download_export'
            )
        if st.button('📤 Export Scenario'):
            st.session_state.show_export = True
    
    with col_imp:
        st.markdown('**📥 Import Scenario (Upload)**')
        uploaded_file = st.file_uploader('Upload JSON file', ['json'], key='import_file')
        if st.button('📥 Import Uploaded File'):
            if uploaded_file:
                try:
                    loaded = json.load(uploaded_file)
                    if 'assumptions' in loaded and 'properties' in loaded:
                        st.session_state.import_data = loaded
                        st.session_state.just_imported = True
                        st.rerun()
                    else:
                        st.error('Invalid scenario file format')
                except Exception as e:
                    st.error(f'Error loading file: {e}')
    
    if st.session_state.get('just_imported'):
        st.success('✅ Scenario imported! Check sidebar for updated values.')

# Apply imported data
if st.session_state.get('just_imported'):
    if 'import_data' in st.session_state:
        loaded = st.session_state.import_data
        a = loaded.get('assumptions', {})
        loadAssumptions(a)
        
        if 'properties' in loaded:
            st.session_state.properties = loaded['properties']
        if 'debts' in loaded:
            st.session_state.debts = loaded['debts']
        if 'financial_events' in loaded:
            st.session_state.financial_events = loaded['financial_events']
        
        del st.session_state.import_data
        st.session_state.just_imported = False

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header('📊 Your Current Situation')
    
    with st.expander('📚 Understanding Your Inputs', False):
        st.markdown("""
        **Why these inputs matter:**
        
        💰 **Tax-Advantaged Accounts** (401k, Roth IRA, HSA) grow tax-free or 
        tax-deferred, which can save you tens of thousands over time. Maxing 
        these out is usually the #1 priority for reaching FI.
        
        📊 **Taxable Brokerage** accounts are flexible — no withdrawal restrictions 
        or penalties — making them ideal for bridging the gap between early 
        retirement and age 59½ when retirement accounts unlock.
        
        🏦 **Cash Savings** act as your emergency fund and buffer for large purchases 
        like property down payments. Most advisors recommend 3-6 months of expenses.
        
        📈 **Investment Returns**: The default 7% stock return reflects the historical 
        average *after* inflation. Actual returns vary widely year to year, but over 
        20-30 year periods, this is a reasonable planning assumption.
        """)
    
    st.subheader('👤 Personal Info')
    birth_year = st.number_input('Birth Year', min_value=1950, max_value=2010, value=1990, key='w_birth_year')
    
    filing_options = ('Single', 'Married Filing Jointly', 'Married Filing Separately', 'Head of Household')
    filing_status = st.selectbox('Tax Filing Status', filing_options, index=1, key='w_filing_status')
    
    state_options = ('SC', 'No Income Tax (TX, FL, WA, etc.)', 'Other')
    state = st.selectbox('State', state_options, index=0, key='w_state')
    
    if state == 'No Income Tax (TX, FL, WA, etc.)':
        state_tax_rate = 0
        st.info('🎉 No state income tax! (TX, FL, WA, NV, WY, SD, AK, NH, TN)')
    elif state == 'Other':
        state_tax_rate = st.slider('State Income Tax Rate (%)', 0.0, 13.0, 5.0, 0.5, key='w_state_tax') / 100
    else:
        state_tax_rate = 0
        st.info('🌴 SC Tax: 0% up to \$3,560, 3% to \$17,830, then 6% (2026+)')
    
    st.subheader('💼 Income')
    current_salary = st.number_input('Annual Gross Salary ($)', value=75000, step=5000, key='w_salary')
    salary_growth = st.slider('Expected Salary Growth (%)', 0.0, 10.0, 3.0, 0.5, key='w_salary_growth') / 100
    
    st.subheader('💰 Tax-Advantaged Contributions')
    st.markdown('*Annual contribution amounts*')
    contrib_401k = st.number_input('Your 401(k) Contribution ($)', value=10000, step=500, key='w_401k_contrib')
    employer_401k = st.number_input('Employer 401(k) Match ($)', value=0, step=500, key='w_401k_employer')
    contrib_roth = st.number_input('Roth IRA Contribution ($)', value=0, step=500, key='w_roth_contrib')
    contrib_hsa = st.number_input('Your HSA Contribution ($)', value=0, step=100, key='w_hsa_contrib')
    employer_hsa = st.number_input('Employer HSA Contribution ($)', value=0, step=100, key='w_hsa_employer')
    
    st.subheader('📊 Taxable Contributions')
    st.markdown('*Annual amounts saved to taxable accounts*')
    contrib_brokerage = st.number_input('Brokerage Contribution ($)', value=0, step=1000, key='w_brokerage_contrib')
    contrib_crypto = st.number_input('Crypto Contribution ($)', value=0, step=500, key='w_crypto_contrib')
    
    st.subheader('💸 Expenses & Savings')
    annual_expenses = st.number_input('Annual Living Expenses ($)', value=48000, step=1000, key='w_expenses')
    monthly_rent = st.number_input('Current Monthly Rent ($)', value=1500, step=100, key='w_rent')
    cash_savings_rate = st.slider('Additional Cash Savings (% of net)', 0, 50, 10, 5, key='w_cash_savings')
    inflation = st.slider('Expected Inflation (%)', 0.0, 6.0, 2.5, 0.5, key='w_inflation') / 100
    
    st.subheader('🏦 Current Assets')
    current_cash = st.number_input('Cash/Emergency Fund ($)', value=10000, step=1000, key='w_cash')
    current_portfolio = st.number_input('Taxable Brokerage ($)', value=0, step=1000, key='w_portfolio')
    current_crypto = st.number_input('Crypto Holdings ($)', value=0, step=1000, key='w_crypto')
    
    st.markdown('**Retirement Accounts**')
    current_401k = st.number_input('401(k)/Traditional IRA ($)', value=50000, step=5000, key='w_401k')
    current_roth_balance = st.number_input('Roth IRA Balance ($)', value=0, step=1000, key='w_roth_balance')
    current_roth_contributions = st.number_input('Roth IRA Contributions Basis ($)', value=0, step=1000, key='w_roth_contributions')
    roth_first_contrib_year = st.number_input('Year of First Roth Contribution', value=2020, min_value=2000, max_value=2030, key='w_roth_first_year')
    current_hsa = st.number_input('HSA Balance ($)', value=0, step=1000, key='w_hsa')
    
    st.subheader('📈 Investment Assumptions')
    portfolio_return = st.slider('Brokerage Return (%)', 3.0, 12.0, 7.0, 0.5, key='w_portfolio_return') / 100
    crypto_return = st.slider('Crypto Return (%)', -10.0, 30.0, 10.0, 1.0, key='w_crypto_return') / 100
    dividend_yield = st.slider('Dividend Yield (%)', 0.0, 6.0, 2.0, 0.5, key='w_dividend_yield') / 100
    
    st.subheader('🏠 Real Estate Assumptions')
    property_appreciation = st.slider('Property Appreciation (%)', 0.0, 8.0, 3.0, 0.5, key='w_appreciation') / 100
    rent_growth = st.slider('Rent Growth (%)', 0.0, 8.0, 3.0, 0.5, key='w_rent_growth') / 100
    
    st.subheader('📅 Timeline')
    start_year = st.number_input('Start Year', value=2026, min_value=2020, max_value=2040, key='w_start_year')
    end_year = st.number_input('End Year', value=2050, min_value=2030, max_value=2080, key='w_end_year')
    retirement_year = st.number_input('Planned Retirement Year', value=2040, min_value=2025, max_value=2070, key='w_retirement_year')

# ============================================
# BUILD ASSUMPTIONS DICT
# ============================================
assumptions = {
    'birth_year': birth_year,
    'filing_status': filing_status,
    'state': state,
    'state_tax_rate': state_tax_rate,
    'current_salary': current_salary,
    'salary_growth': salary_growth,
    'contrib_401k': contrib_401k,
    'employer_401k': employer_401k,
    'contrib_roth': contrib_roth,
    'contrib_hsa': contrib_hsa,
    'employer_hsa': employer_hsa,
    'contrib_brokerage': contrib_brokerage,
    'contrib_crypto': contrib_crypto,
    'annual_expenses': annual_expenses,
    'monthly_rent': monthly_rent,
    'cash_savings_rate': cash_savings_rate / 100,
    'inflation': inflation,
    'current_cash': current_cash,
    'current_portfolio': current_portfolio,
    'current_crypto': current_crypto,
    'current_401k': current_401k,
    'current_roth_balance': current_roth_balance,
    'current_roth_contributions': current_roth_contributions,
    'roth_first_contrib_year': roth_first_contrib_year,
    'current_hsa': current_hsa,
    'portfolio_return': portfolio_return,
    'crypto_return': crypto_return,
    'dividend_yield': dividend_yield,
    'property_appreciation': property_appreciation,
    'rent_growth': rent_growth,
    'start_year': start_year,
    'end_year': end_year,
    'retirement_year': retirement_year,
}

# Handle pending save
if 'pending_save' in st.session_state and st.session_state.pending_save:
    save_name = st.session_state.pending_save
    save_scenario(save_name, assumptions, st.session_state.properties, st.session_state.debts, st.session_state.financial_events)
    st.success(f"✅ Saved scenario '{save_name}'!")
    st.session_state.pending_save = None

# Handle pending export
if st.session_state.get('show_export', False):
    export_data = {
        'assumptions': assumptions,
        'properties': st.session_state.properties,
        'debts': st.session_state.debts,
        'financial_events': st.session_state.financial_events,
    }
    st.session_state.export_json = json.dumps(export_data, indent=2, default=str)
    st.session_state.show_export = False
    st.rerun()

# ============================================
# PROPERTIES SECTION
# ============================================
st.header('🏠 Properties')

with st.expander('📚 Why Real Estate in Your Financial Plan?', False):
    st.markdown("""
    Real estate can play two powerful roles on your path to financial independence:
    
    #### 🏡 Primary Residence
    - **Eliminates rent**: Once you buy, your housing cost becomes a fixed mortgage payment 
      instead of rent that increases every year
    - **Builds equity**: Each mortgage payment builds ownership. After 15-30 years, you own 
      your home outright — drastically reducing expenses in retirement
    - **Tax benefits**: Mortgage interest and property taxes may be deductible, reducing 
      your tax bill (the simulator calculates this automatically)
    - **Appreciation**: Historically, home values grow 3-4% per year
    
    #### 🏢 Rental Properties
    - **Passive income**: Rental income counts toward your FI ratio — it can help you reach 
      financial independence faster
    - **Key metrics the simulator tracks**:
      - **Cash-on-Cash ROI**: Annual cash flow ÷ total cash invested. Above 8% is good
      - **Cap Rate**: Net operating income ÷ property value. Measures property profitability
      - **1% Rule**: Monthly rent should be ≥ 1% of purchase price for good cash flow
      - **Cash Flow**: What's left after mortgage, taxes, insurance, CapEx, and management
    
    #### ⚖️ Trade-offs to Consider
    - Real estate ties up large amounts of cash (down payment + closing costs)
    - Properties require management time and unexpected repairs
    - Less liquid than stocks — you can't sell a fraction of a house
    - Leverage (mortgages) amplifies both gains AND losses
    
    **Start with the sidebar inputs first**, then come back here to model property purchases.
    """)

st.markdown('Add properties you plan to purchase. Your rent expense will stop once you buy a primary residence.')

with st.expander('➕ Add New Property', expanded=len(st.session_state.properties) == 0):
    new_is_primary = st.checkbox('This is my primary residence', True, key='prop_is_primary')
    
    if new_is_primary:
        # Primary residence form
        st.subheader('🏡 Primary Residence Details')
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input('Property Name', 'My Home')
            new_purchase_year = st.number_input('Purchase Year', value=2028, min_value=start_year, max_value=end_year)
            new_purchase_price = st.number_input('Purchase Price ($)', value=350000, step=10000)
            new_closing_costs = st.number_input('Closing Costs ($)', value=8000, step=500, help='Buyer closing costs')
        
        with col2:
            new_down_payment = st.slider('Down Payment (%)', 5, 50, 20, 5)
            new_mortgage_rate = st.number_input('Mortgage Rate (%)', value=6.5, step=0.25) / 100
            new_mortgage_years = st.selectbox('Mortgage Term', [15, 20, 30], index=2)
            new_property_tax_rate = st.number_input('Property Tax Rate (%)', value=1.2, step=0.1, help='Annual property tax as % of value') / 100
        
        if st.button('Add Primary Residence', type='primary'):
            st.session_state.properties.append({
                'name': new_name,
                'is_primary': True,
                'purchase_year': new_purchase_year,
                'purchase_price': new_purchase_price,
                'down_payment_pct': new_down_payment / 100,
                'mortgage_rate': new_mortgage_rate,
                'mortgage_years': new_mortgage_years,
                'property_tax_rate': new_property_tax_rate,
                'closing_costs': new_closing_costs,
                'vacancy_rate': 0,
                'avg_tenant_stay': 0,
            })
            st.rerun()
    else:
        # Rental property form
        st.subheader('🏢 Rental Property Analysis')
        tab1, tab2, tab3, tab4 = st.tabs(('📋 Purchase Details', '💰 Financing', '📈 Revenue', '💸 Expenses'))
        
        with tab1:
            st.markdown('**Property Information**')
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input('Property Name', 'Rental Property')
                new_purchase_year = st.number_input('Purchase Year', value=2028, min_value=start_year, max_value=end_year, key='rental_year')
                new_purchase_price = st.number_input('Purchase Price ($)', value=200000, step=5000, key='rental_price')
                new_arv = st.number_input('After Repair Value (ARV) ($)', value=220000, step=5000, help='Expected value after repairs')
            with col2:
                new_closing_costs = st.number_input('Purchase Closing Costs ($)', value=5000, step=500, key='rental_closing')
                new_repair_cost = st.number_input('Repair/Rehab Cost ($)', value=15000, step=1000, help='Initial repair investment')
        
        with tab2:
            st.markdown('**Financing Details**')
            col1, col2 = st.columns(2)
            with col1:
                new_down_payment = st.slider('Down Payment (%)', 5, 50, 25, 5, key='rental_dp')
                new_mortgage_rate = st.number_input('Loan Interest Rate (%)', value=7.0, step=0.25, key='rental_rate') / 100
                new_pmi_rate = st.number_input('PMI Rate (% annual)', value=0.5, step=0.1, help='Private Mortgage Insurance if < 20% down') / 100
            with col2:
                new_mortgage_years = st.selectbox('Mortgage Term', [15, 20, 30], index=2, key='rental_term')
                new_lender_points = st.number_input('Lender Points ($)', value=2000, step=500, help='Points paid to reduce rate')
                new_other_fees = st.number_input('Other Financing Fees ($)', value=500, step=100)
        
        with tab3:
            st.markdown('**Revenue Assumptions**')
            col1, col2 = st.columns(2)
            with col1:
                new_rent_per_unit = st.number_input('Rent per Unit ($/month)', value=1500, step=50)
                new_num_units = st.number_input('Number of Units', value=1, min_value=1, max_value=20)
                new_vacancy_rate = st.slider('Vacancy Rate (%)', 0, 20, 5, 1, key='rental_vacancy') / 100
            with col2:
                new_avg_tenant_stay = st.number_input('Avg Tenant Stay (years)', value=2.0, step=0.5, help='For turnover cost estimation')
                new_other_monthly_income = st.number_input('Other Monthly Income ($)', value=0, step=50, help='Laundry, parking, etc.')
            
            gross_monthly = new_rent_per_unit * new_num_units + new_other_monthly_income
            effective_monthly = gross_monthly * (1 - new_vacancy_rate)
            st.info(f'**Gross Monthly:** ${gross_monthly:,.0f} | **Effective (after vacancy):** ${effective_monthly:,.0f}')
        
        with tab4:
            st.markdown('**Monthly Expenses**')
            col1, col2 = st.columns(2)
            with col1:
                new_property_tax_rate = st.number_input('Property Tax Rate (% annual)', value=1.2, step=0.1, key='rental_tax') / 100
                new_insurance_monthly = st.number_input('Insurance ($/month)', value=100, step=25)
                new_capex_rate = st.slider('Capital Expenditure (%)', 0, 15, 5, 1, help='% of rent for future repairs') / 100
                new_management_rate = st.slider('Property Management (%)', 0, 15, 8, 1, help='% of rent for management') / 100
            with col2:
                new_hoa_monthly = st.number_input('HOA Fees ($/month)', value=0, step=25)
                new_utilities_monthly = st.number_input('Utilities ($/month)', value=0, step=25, help='Water, sewer, electric if landlord pays')
                new_other_expenses = st.number_input('Other Expenses ($/month)', value=50, step=25, help='Lawn, garbage, misc')
        
        # Deal Analysis Preview
        st.markdown('---')
        st.subheader('📊 Deal Analysis Preview')
        
        loan_amount = new_purchase_price * (1 - new_down_payment / 100)
        monthly_pi = calculate_mortgage_payment(loan_amount, new_mortgage_rate, new_mortgage_years)
        monthly_pmi = (loan_amount * new_pmi_rate / 12) if new_down_payment < 20 else 0
        monthly_tax = new_purchase_price * new_property_tax_rate / 12
        
        capex_reserve = effective_monthly * new_capex_rate
        mgmt_fee = effective_monthly * new_management_rate
        total_monthly_expense = monthly_pi + monthly_pmi + monthly_tax + new_insurance_monthly + capex_reserve + mgmt_fee + new_hoa_monthly + new_utilities_monthly + new_other_expenses
        
        monthly_cash_flow = effective_monthly - total_monthly_expense
        annual_cash_flow = monthly_cash_flow * 12
        
        total_cash_needed = (new_purchase_price * new_down_payment / 100) + new_closing_costs + new_repair_cost + new_lender_points + new_other_fees
        cash_on_cash = (annual_cash_flow / total_cash_needed * 100) if total_cash_needed > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric('Monthly Cash Flow', f'${monthly_cash_flow:,.0f}')
        with col2:
            st.metric('Annual Cash Flow', f'${annual_cash_flow:,.0f}')
        with col3:
            st.metric('Cash Needed', f'${total_cash_needed:,.0f}')
        with col4:
            st.metric('Cash-on-Cash ROI', f'{cash_on_cash:.1f}%')
        
        with st.expander('See Expense Breakdown'):
            st.markdown(f"""
            | Expense | Monthly |
            |---------|---------|
            | P&I | ${monthly_pi:,.0f} |
            | PMI | ${monthly_pmi:,.0f} |
            | Property Tax | ${monthly_tax:,.0f} |
            | Insurance | ${new_insurance_monthly:,.0f} |
            | CapEx Reserve | ${capex_reserve:,.0f} |
            | Management | ${mgmt_fee:,.0f} |
            | HOA | ${new_hoa_monthly:,.0f} |
            | Utilities | ${new_utilities_monthly:,.0f} |
            | Other | ${new_other_expenses:,.0f} |
            | **Total** | **${total_monthly_expense:,.0f}** |
            """)
        
        if st.button('Add Rental Property', type='primary'):
            st.session_state.properties.append({
                'name': new_name,
                'is_primary': False,
                'purchase_year': new_purchase_year,
                'purchase_price': new_purchase_price,
                'arv': new_arv,
                'down_payment_pct': new_down_payment / 100,
                'mortgage_rate': new_mortgage_rate,
                'mortgage_years': new_mortgage_years,
                'property_tax_rate': new_property_tax_rate,
                'closing_costs': new_closing_costs,
                'repair_cost': new_repair_cost,
                'rent_per_unit': new_rent_per_unit,
                'num_units': new_num_units,
                'vacancy_rate': new_vacancy_rate,
                'avg_tenant_stay': new_avg_tenant_stay,
                'other_monthly_income': new_other_monthly_income,
                'insurance_monthly': new_insurance_monthly,
                'capex_rate': new_capex_rate,
                'management_rate': new_management_rate,
                'hoa_monthly': new_hoa_monthly,
                'utilities_monthly': new_utilities_monthly,
                'other_monthly_expenses': new_other_expenses,
                'pmi_rate': new_pmi_rate,
                'lender_points': new_lender_points,
                'other_fees': new_other_fees,
            })
            st.rerun()

# Display existing properties
if st.session_state.properties:
    st.subheader('Your Planned Properties')
    
    for i, prop in enumerate(st.session_state.properties):
        loan = prop['purchase_price'] * (1 - prop.get('down_payment_pct', 0.2))
        monthly_pmt = calculate_mortgage_payment(loan, prop.get('mortgage_rate', 0.065), prop.get('mortgage_years', 30))
        
        col1, col2, col3, col4, col5, col6 = st.columns((3, 2, 2, 0.5, 0.5, 0.5))
        with col1:
            if prop.get('is_primary'):
                prop_type = '🏡 Primary'
            else:
                prop_type = f"🏢 Rental ({prop.get('num_units', 1)} unit)"
            st.markdown(f"**{prop['name']}** ({prop_type})")
        with col2:
            st.markdown(f"${prop['purchase_price']:,} in {prop['purchase_year']}")
        with col3:
            st.markdown(f"${monthly_pmt:,.0f}/mo P&I")
            if not prop.get('is_primary'):
                monthly_rent_display = prop.get('rent_per_unit', prop.get('monthly_rent', 0)) * prop.get('num_units', 1)
                st.markdown(f"${monthly_rent_display:,}/mo rent")
        with col4:
            if st.button('✏️', key=f'edit_{i}', help='Edit property'):
                st.session_state.editing_property_idx = i
                st.rerun()
        with col5:
            if st.button('📋', key=f'dup_{i}', help='Duplicate property'):
                new_prop = prop.copy()
                new_prop['name'] = f"{prop['name']} (Copy)"
                st.session_state.properties.append(new_prop)
                st.rerun()
        with col6:
            if st.button('🗑️', key=f'del_{i}', help='Delete property'):
                st.session_state.properties.pop(i)
                if st.session_state.editing_property_idx == i:
                    st.session_state.editing_property_idx = None
                st.rerun()
        
        # Edit form for this property
        if st.session_state.editing_property_idx == i:
            with st.container():
                st.markdown('---')
                st.markdown(f"### ✏️ Editing: {prop['name']}")
                
                if prop.get('is_primary'):
                    # Primary residence edit
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        edit_name = st.text_input('Property Name', prop['name'], key=f'edit_name_{i}')
                        edit_year = st.number_input('Purchase Year', value=prop['purchase_year'], min_value=start_year, max_value=end_year, key=f'edit_year_{i}')
                        edit_price = st.number_input('Purchase Price ($)', value=prop['purchase_price'], step=10000, key=f'edit_price_{i}')
                        edit_closing = st.number_input('Closing Costs ($)', value=prop.get('closing_costs', 8000), step=500, key=f'edit_closing_{i}')
                    with edit_col2:
                        edit_dp = st.slider('Down Payment (%)', 5, 50, int(prop.get('down_payment_pct', 0.2) * 100), key=f'edit_dp_{i}')
                        edit_rate = st.number_input('Mortgage Rate (%)', value=prop.get('mortgage_rate', 0.065) * 100, step=0.25, key=f'edit_rate_{i}')
                        edit_term = st.selectbox('Mortgage Term', [15, 20, 30], index=[15, 20, 30].index(prop.get('mortgage_years', 30)), key=f'edit_term_{i}')
                        edit_tax_rate = st.number_input('Property Tax Rate (%)', value=prop.get('property_tax_rate', 0.012) * 100, step=0.1, key=f'edit_tax_{i}')
                    
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button('💾 Save Changes', key=f'save_edit_{i}', type='primary'):
                            st.session_state.properties[i].update({
                                'name': edit_name,
                                'purchase_year': edit_year,
                                'purchase_price': edit_price,
                                'closing_costs': edit_closing,
                                'down_payment_pct': edit_dp / 100,
                                'mortgage_rate': edit_rate / 100,
                                'mortgage_years': edit_term,
                                'property_tax_rate': edit_tax_rate / 100,
                            })
                            st.session_state.editing_property_idx = None
                            st.rerun()
                    with btn_col2:
                        if st.button('❌ Cancel', key=f'cancel_edit_{i}'):
                            st.session_state.editing_property_idx = None
                            st.rerun()
                else:
                    # Rental property edit
                    edit_tabs = st.tabs(('📋 Basic', '💰 Financing', '📈 Revenue', '💸 Expenses'))
                    
                    with edit_tabs[0]:
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            edit_name = st.text_input('Property Name', prop['name'], key=f'edit_name_{i}')
                            edit_year = st.number_input('Purchase Year', value=prop['purchase_year'], min_value=start_year, max_value=end_year, key=f'edit_year_{i}')
                            edit_price = st.number_input('Purchase Price ($)', value=prop['purchase_price'], step=5000, key=f'edit_price_{i}')
                        with edit_col2:
                            edit_arv = st.number_input('ARV ($)', value=prop.get('arv', prop['purchase_price']), step=5000, key=f'edit_arv_{i}')
                            edit_closing = st.number_input('Closing Costs ($)', value=prop.get('closing_costs', 5000), step=500, key=f'edit_closing_{i}')
                            edit_repair = st.number_input('Repair Cost ($)', value=prop.get('repair_cost', 0), step=1000, key=f'edit_repair_{i}')
                    
                    with edit_tabs[1]:
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            edit_dp = st.slider('Down Payment (%)', 5, 50, int(prop.get('down_payment_pct', 0.25) * 100), key=f'edit_dp_{i}')
                            edit_rate = st.number_input('Mortgage Rate (%)', value=prop.get('mortgage_rate', 0.07) * 100, step=0.25, key=f'edit_rate_{i}')
                            edit_pmi = st.number_input('PMI Rate (%)', value=prop.get('pmi_rate', 0) * 100, step=0.1, key=f'edit_pmi_{i}')
                        with edit_col2:
                            edit_term = st.selectbox('Mortgage Term', [15, 20, 30], index=[15, 20, 30].index(prop.get('mortgage_years', 30)), key=f'edit_term_{i}')
                            edit_points = st.number_input('Lender Points ($)', value=prop.get('lender_points', 0), step=500, key=f'edit_points_{i}')
                            edit_other_fees = st.number_input('Other Fees ($)', value=prop.get('other_fees', 0), step=100, key=f'edit_fees_{i}')
                    
                    with edit_tabs[2]:
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            edit_rent = st.number_input('Rent per Unit ($/mo)', value=prop.get('rent_per_unit', prop.get('monthly_rent', 1500)), step=50, key=f'edit_rent_{i}')
                            edit_units = st.number_input('Number of Units', value=prop.get('num_units', 1), min_value=1, max_value=20, key=f'edit_units_{i}')
                        with edit_col2:
                            edit_vacancy = st.slider('Vacancy Rate (%)', 0, 20, int(prop.get('vacancy_rate', 0.05) * 100), key=f'edit_vacancy_{i}')
                            edit_other_income = st.number_input('Other Monthly Income ($)', value=prop.get('other_monthly_income', 0), step=50, key=f'edit_income_{i}')
                    
                    with edit_tabs[3]:
                        edit_col1, edit_col2 = st.columns(2)
                        with edit_col1:
                            edit_tax_rate = st.number_input('Property Tax Rate (%)', value=prop.get('property_tax_rate', 0.012) * 100, step=0.1, key=f'edit_tax_{i}')
                            edit_insurance = st.number_input('Insurance ($/mo)', value=prop.get('insurance_monthly', 100), step=25, key=f'edit_ins_{i}')
                            edit_capex = st.slider('CapEx (%)', 0, 15, int(prop.get('capex_rate', 0.05) * 100), key=f'edit_capex_{i}')
                        with edit_col2:
                            edit_mgmt = st.slider('Management (%)', 0, 15, int(prop.get('management_rate', 0.08) * 100), key=f'edit_mgmt_{i}')
                            edit_hoa = st.number_input('HOA ($/mo)', value=prop.get('hoa_monthly', 0), step=25, key=f'edit_hoa_{i}')
                            edit_utilities = st.number_input('Utilities ($/mo)', value=prop.get('utilities_monthly', 0), step=25, key=f'edit_util_{i}')
                            edit_other_exp = st.number_input('Other Expenses ($/mo)', value=prop.get('other_monthly_expenses', 50), step=25, key=f'edit_other_{i}')
                    
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button('💾 Save Changes', key=f'save_edit_{i}', type='primary'):
                            st.session_state.properties[i].update({
                                'name': edit_name,
                                'purchase_year': edit_year,
                                'purchase_price': edit_price,
                                'arv': edit_arv,
                                'closing_costs': edit_closing,
                                'repair_cost': edit_repair,
                                'down_payment_pct': edit_dp / 100,
                                'mortgage_rate': edit_rate / 100,
                                'pmi_rate': edit_pmi / 100,
                                'mortgage_years': edit_term,
                                'lender_points': edit_points,
                                'other_fees': edit_other_fees,
                                'rent_per_unit': edit_rent,
                                'num_units': edit_units,
                                'vacancy_rate': edit_vacancy / 100,
                                'other_monthly_income': edit_other_income,
                                'property_tax_rate': edit_tax_rate / 100,
                                'insurance_monthly': edit_insurance,
                                'capex_rate': edit_capex / 100,
                                'management_rate': edit_mgmt / 100,
                                'hoa_monthly': edit_hoa,
                                'utilities_monthly': edit_utilities,
                                'other_monthly_expenses': edit_other_exp,
                            })
                            st.session_state.editing_property_idx = None
                            st.rerun()
                    with btn_col2:
                        if st.button('❌ Cancel', key=f'cancel_edit_{i}'):
                            st.session_state.editing_property_idx = None
                            st.rerun()
    
    st.markdown('---')
else:
    st.info('No properties added yet. Add your first property above!')

# ============================================
# DEBTS SECTION
# ============================================
st.header('💳 Debts')
st.markdown('Add existing debts like mortgages, car loans, student loans, etc. These will be tracked and paid down over time.')

with st.expander('➕ Add New Debt', expanded=len(st.session_state.debts) == 0 and len(st.session_state.properties) > 0):
    col1, col2 = st.columns(2)
    
    with col1:
        debt_name = st.text_input('Debt Name', 'Car Loan', key='debt_name')
        debt_type = st.selectbox('Debt Type', ['Mortgage', 'Car Loan', 'Student Loan', 'Personal Loan', 'Credit Card', 'Other'])
        original_balance = st.number_input('Original Loan Amount ($)', value=25000, step=1000, key='debt_orig')
        current_balance = st.number_input('Current Balance ($)', value=20000, step=1000, key='debt_curr')
    
    with col2:
        debt_rate = st.number_input('Interest Rate (%)', value=6.0, step=0.25, key='debt_rate') / 100
        debt_term = st.number_input('Original Loan Term (years)', value=5, min_value=1, max_value=30, key='debt_term')
        debt_start_year = st.number_input('Year Loan Started', value=2024, min_value=2010, max_value=start_year, key='debt_start')
        debt_monthly_pmt = calculate_mortgage_payment(original_balance, debt_rate, debt_term)
        st.markdown(f'**Monthly Payment:** ${debt_monthly_pmt:,.0f}')
    
    # Estimate months already paid
    if original_balance > 0 and current_balance < original_balance:
        months_paid_est = 0
        test_balance = original_balance
        monthly_rate = debt_rate / 12
        for m in range(debt_term * 12):
            if test_balance <= current_balance:
                months_paid_est = m
                break
            interest = test_balance * monthly_rate
            principal = debt_monthly_pmt - interest
            test_balance -= principal
        else:
            months_paid_est = debt_term * 12
    else:
        months_paid_est = 0
    
    if st.button('Add Debt', type='primary', key='add_debt'):
        st.session_state.debts.append({
            'name': debt_name,
            'type': debt_type,
            'original_balance': original_balance,
            'current_balance': current_balance,
            'interest_rate': debt_rate,
            'term_years': debt_term,
            'start_year': debt_start_year,
            'months_already_paid': months_paid_est,
        })
        st.rerun()

# Display existing debts
if st.session_state.debts:
    st.subheader('Your Current Debts')
    
    total_debt_balance = 0
    total_monthly_debt = 0
    
    for i, debt in enumerate(st.session_state.debts):
        monthly_pmt = calculate_mortgage_payment(debt['original_balance'], debt['interest_rate'], debt['term_years'])
        total_debt_balance += debt['current_balance']
        total_monthly_debt += monthly_pmt
        
        total_months = debt['term_years'] * 12
        months_remaining = total_months - debt.get('months_already_paid', 0)
        years_remaining = months_remaining / 12
        payoff_year = start_year + int(years_remaining)
        
        col1, col2, col3, col4, col5 = st.columns((2, 2, 2, 2, 1))
        with col1:
            icon = {'Mortgage': '🏠', 'Car Loan': '🚗', 'Student Loan': '🎓', 'Personal Loan': '💳', 'Credit Card': '💳', 'Other': '📋'}.get(debt['type'], '📋')
            st.markdown(f"**{icon} {debt['name']}**")
            st.caption(debt['type'])
        with col2:
            st.markdown(f"Balance: **${debt['current_balance']:,}**")
            st.caption(f"Original: ${debt['original_balance']:,}")
        with col3:
            st.markdown(f"${monthly_pmt:,.0f}/mo")
            st.caption(f"{debt['interest_rate'] * 100:.1f}% rate")
        with col4:
            st.markdown(f"Payoff: **{payoff_year}**")
            st.caption(f"{years_remaining:.1f} years left")
        with col5:
            if st.button('🗑️', key=f'del_debt_{i}'):
                st.session_state.debts.pop(i)
                st.rerun()
    
    st.markdown(f"**Total Debt:** ${total_debt_balance:,} | **Monthly Payments:** ${total_monthly_debt:,.0f}")
else:
    st.info('No debts added. If you have existing loans, add them above to track payoff.')

# ============================================
# FINANCIAL EVENTS SECTION
# ============================================
st.header('📅 Financial Events')

with st.expander('📚 Early Retirement Withdrawal Strategies', False):
    st.markdown("""
    The biggest challenge of early retirement is **accessing your money before age 59½** 
    without paying huge penalties. Here are the main strategies:
    
    ---
    
    #### 🔄 The Roth Conversion Ladder (Most Popular for Early Retirees)
    
    **The Problem**: Your 401(k) has the most money, but withdrawing before 59½ 
    means a **10% penalty + income tax**.
    
    **The Solution**: Convert 401(k) money to a Roth IRA each year, pay income tax 
    (but NO penalty), then withdraw it **tax-free and penalty-free after 5 years**.
    
    **How it works:**
    ```
    Year 1 (retire): Convert $40K from 401k → Roth (pay ~$4-6K tax)
    Year 2: Convert another $40K → Roth
    Year 3: Convert another $40K → Roth
    ...
    Year 6: Withdraw Year 1's conversion TAX-FREE ✅
    Year 7: Withdraw Year 2's conversion TAX-FREE ✅
    ```
    
    **The key insight**: Convert just enough to fill up the low tax brackets (10-12%) 
    each year. In early retirement with no salary, your conversions may be taxed at 
    only 10-12% instead of 22-24% while working!
    
    ---
    
    #### 💜 Roth IRA Contributions (The Bridge)
    
    **Your Roth contributions (not earnings) can be withdrawn anytime**, tax-free, 
    penalty-free — no age requirement. This is your **bridge money** while waiting 
    for Roth conversions to season.
    
    **Example**: If you've contributed $50K to your Roth over the years, that $50K 
    is available day one of retirement. Earnings stay in the account until age 59½.
    
    ---
    
    #### 📈 Taxable Brokerage (The Flexible Account)
    
    - No age restrictions or penalties
    - Only pay **capital gains tax** (~15%) on the *gains portion* 
    - Often the first account early retirees draw from
    - Pairs well with the Roth conversion ladder as bridge funding
    
    ---
    
    #### 🎯 Putting It Together: A Common Early Retirement Plan
    
    | Years 1-5 | Strategy |
    |-----------|----------|
    | **Living expenses** | Roth contributions + Brokerage withdrawals |
    | **Meanwhile** | Convert 401k → Roth at low tax brackets each year |
    
    | Years 6+ | Strategy |
    |-----------|----------|
    | **Living expenses** | Seasoned Roth conversions (tax-free!) |
    | **Meanwhile** | Continue converting from 401k at low brackets |
    
    | Age 59½+ | Strategy |
    |-----------|----------|
    | **All accounts unlocked** | 401k, Roth, and HSA all penalty-free |
    
    **Use the event planner below to model your own withdrawal strategy!**
    """)

st.markdown('Plan withdrawals and Roth conversions for early retirement.')

# Get projected balances for preview
projected_balances = get_projected_balances(assumptions, st.session_state.properties, st.session_state.debts)

EVENT_TYPES = (
    'Roth Conversion (401k/IRA → Roth)',
    'Withdraw from Roth',
    'Withdraw from Brokerage',
    'Withdraw from Crypto',
    'Withdraw from 401k/IRA',
)

with st.expander('➕ Add Financial Event', expanded=len(st.session_state.financial_events) == 0):
    event_type = st.selectbox('Event Type', EVENT_TYPES, key='event_type')
    
    col1, col2 = st.columns(2)
    
    with col1:
        event_year = st.number_input('Year', value=start_year + 1, min_value=start_year, max_value=end_year, key='event_year')
        
        if event_type == 'Withdraw from Roth':
            amount_options = ['Absolute ($)', 'Percent of account (%)']
        else:
            amount_options = ['Absolute ($)', 'Percent of account (%)']
        amount_type = st.selectbox('Amount Type', amount_options, key='event_amount_type')
        if amount_type == 'Absolute ($)':
            event_amount = st.number_input('Amount ($)', value=40000, step=5000, key='event_amount')
            event_amount_pct = None
        else:
            event_amount_pct = st.number_input('Percent of account (%)', value=10.0, step=0.5, key='event_amount_pct')
            event_amount = None
    
    with col2:
        event_recurring = st.checkbox('Repeat every year until end year', False, key='event_recurring')
        if event_recurring:
            event_end_year = st.number_input('Until Year', value=end_year, min_value=event_year, max_value=end_year, key='event_end')
        else:
            event_end_year = event_year
    
    # Determine source account
    if 'Roth Conversion' in event_type:
        source_account = 'trad_retirement'
        account_name = '401k/IRA'
    elif event_type == 'Withdraw from Roth':
        source_account = 'roth_balance'
        account_name = 'Roth IRA'
    elif event_type == 'Withdraw from Brokerage':
        source_account = 'portfolio'
        account_name = 'Brokerage'
    elif event_type == 'Withdraw from Crypto':
        source_account = 'crypto'
        account_name = 'Crypto'
    else:
        source_account = 'trad_retirement'
        account_name = '401k/IRA'
    
    # Preview
    st.markdown('---')
    if event_recurring:
        years_to_show = list(range(event_year, event_end_year + 1))
    else:
        years_to_show = [event_year]
    
    # Calculate existing draws from other events
    existing_draws = {}
    for e in st.session_state.financial_events:
        e_year = e['year']
        e_type = e['type']
        
        if 'amount' in e:
            e_amt = e['amount']
        elif 'amount_pct' in e:
            pct = e['amount_pct']
            if pct > 1:
                pct = pct / 100.0
            
            if 'Roth Conversion' in e_type or e_type == 'Withdraw from 401k/IRA':
                base = projected_balances.get(e_year, {}).get('trad_retirement', 0)
            elif e_type == 'Withdraw from Roth':
                base = projected_balances.get(e_year, {}).get('roth_balance', 0)
            elif e_type == 'Withdraw from Brokerage':
                base = projected_balances.get(e_year, {}).get('portfolio', 0)
            elif e_type == 'Withdraw from Crypto':
                base = projected_balances.get(e_year, {}).get('crypto', 0)
            else:
                base = 0
            e_amt = base * pct
        else:
            e_amt = 0
        
        # Determine source for this existing event
        if 'Roth Conversion' in e_type:
            e_source = 'trad_retirement'
        elif e_type == 'Withdraw from Roth':
            e_source = 'roth_balance'
        elif e_type == 'Withdraw from Brokerage':
            e_source = 'portfolio'
        elif e_type == 'Withdraw from Crypto':
            e_source = 'crypto'
        elif e_type == 'Withdraw from 401k/IRA':
            e_source = 'trad_retirement'
        else:
            e_source = None
        
        if e_source == source_account:
            existing_draws[e_year] = existing_draws.get(e_year, 0) + e_amt
    
    # Build preview data
    preview_data = []
    cumulative = 0
    has_shortfall = False
    
    for yr in years_to_show:
        if yr in projected_balances:
            bal = projected_balances[yr]
            age = yr - birth_year
            account_bal = bal.get(source_account, 0)
            
            if source_account == 'roth_balance':
                roth_contrib = bal.get('roth_contributions', 0)
            else:
                roth_contrib = 0
            
            if event_amount is not None:
                requested = event_amount
            else:
                pct = event_amount_pct if event_amount_pct else 0
                if pct > 1:
                    pct = pct / 100.0
                requested = account_bal * pct
            
            prior_draws = sum(existing_draws.get(y, 0) for y in range(start_year, yr))
            this_year_existing = existing_draws.get(yr, 0)
            
            available = max(0, account_bal - cumulative - prior_draws - this_year_existing)
            will_use = min(requested, available)
            shortfall = requested - will_use
            
            if shortfall > 0:
                has_shortfall = True
            
            # Tax notes
            notes = []
            if event_type == 'Withdraw from Roth':
                if roth_contrib >= requested:
                    notes.append('✅ From contributions (tax-free)')
                elif roth_contrib > 0:
                    gains_portion = max(0, requested - roth_contrib)
                    if age < 59.5:
                        notes.append(f'⚠️ ${gains_portion:,.0f} from earnings = taxed + 10% penalty')
                    else:
                        notes.append('✅ Age 59½+ (tax-free)')
                else:
                    if age < 59.5:
                        notes.append('⚠️ All earnings = taxed + 10% penalty')
                    else:
                        notes.append('✅ Age 59½+ (tax-free)')
            elif event_type == 'Withdraw from 401k/IRA':
                if age < 59.5:
                    notes.append('⚠️ Income tax + 10% penalty')
                else:
                    notes.append('✅ Age 59½+ (income tax only)')
            elif 'Roth Conversion' in event_type:
                notes.append('📝 Taxed as income (no penalty)')
            elif event_type in ('Withdraw from Brokerage', 'Withdraw from Crypto'):
                notes.append('📝 ~15% cap gains on gains portion')
            
            preview_data.append({
                'Year': yr,
                'Age': age,
                'Account Balance': f'${account_bal:,.0f}',
                'Requested': f'${requested:,.0f}',
                'Available': f'${available:,.0f}',
                'Will Use': f'${will_use:,.0f}',
                'Notes': '; '.join(notes) if notes else (f'⚠️ Shortfall: ${shortfall:,.0f}' if shortfall > 0 else ''),
            })
            
            cumulative += will_use
    
    if preview_data:
        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
    
    if has_shortfall:
        total_possible = 0
        for yr in years_to_show:
            base = projected_balances.get(yr, {}).get(source_account, 0)
            if event_amount is not None:
                req = event_amount
            else:
                pct = event_amount_pct if event_amount_pct else 0
                if pct > 1:
                    pct = pct / 100.0
                req = base * pct
            total_possible += min(req, base)
        if len(years_to_show) > 0:
            max_per_year = total_possible / len(years_to_show)
        else:
            max_per_year = 0
        st.warning(f'⚠️ Insufficient balance. Suggest ~${max_per_year:,.0f}/year for {len(years_to_show)} years.')
    
    if st.button('Add Event', type='primary'):
        if event_recurring:
            years_to_add = list(range(event_year, event_end_year + 1))
        else:
            years_to_add = [event_year]
        for yr in years_to_add:
            if event_amount is not None:
                st.session_state.financial_events.append({'type': event_type, 'year': yr, 'amount': event_amount})
            else:
                pct_val = event_amount_pct if event_amount_pct else 0
                if pct_val > 1:
                    pct_val = pct_val / 100.0
                st.session_state.financial_events.append({'type': event_type, 'year': yr, 'amount_pct': pct_val})
        st.rerun()

# Display scheduled events
if st.session_state.financial_events:
    st.subheader('📋 Scheduled Events')
    
    event_rows = []
    cumulative_by_account = {'trad_retirement': 0, 'roth_balance': 0, 'portfolio': 0, 'crypto': 0}
    
    for event in sorted(st.session_state.financial_events, key=lambda e: e['year']):
        yr = event['year']
        e_type = event['type']
        
        if 'amount' in event:
            e_amt = event['amount']
            display_amt = f'${e_amt:,.0f}'
        elif 'amount_pct' in event:
            pct = event['amount_pct']
            if pct > 1:
                pct_norm = pct / 100.0
            else:
                pct_norm = pct
            
            if 'Roth Conversion' in e_type or e_type == 'Withdraw from 401k/IRA':
                base = projected_balances.get(yr, {}).get('trad_retirement', 0)
            elif e_type == 'Withdraw from Roth':
                base = projected_balances.get(yr, {}).get('roth_balance', 0)
            elif e_type == 'Withdraw from Brokerage':
                base = projected_balances.get(yr, {}).get('portfolio', 0)
            elif e_type == 'Withdraw from Crypto':
                base = projected_balances.get(yr, {}).get('crypto', 0)
            else:
                base = 0
            e_amt = base * pct_norm
            display_amt = f'{pct * 100 if pct <= 1 else pct:.1f}% (~${e_amt:,.0f})'
        else:
            e_amt = 0
            display_amt = '$0'
        
        age = yr - birth_year
        
        # Determine source and icon
        if 'Roth Conversion' in e_type:
            source = 'trad_retirement'
            icon = '🔄'
        elif e_type == 'Withdraw from Roth':
            source = 'roth_balance'
            icon = '💜'
        elif e_type == 'Withdraw from Brokerage':
            source = 'portfolio'
            icon = '📈'
        elif e_type == 'Withdraw from Crypto':
            source = 'crypto'
            icon = '🪙'
        else:
            source = 'trad_retirement'
            icon = '💰'
        
        proj_bal = projected_balances.get(yr, {}).get(source, 0)
        available = max(0, proj_bal - cumulative_by_account.get(source, 0))
        will_use = min(e_amt, available)
        
        # Tax note
        if e_type == 'Withdraw from Roth':
            roth_contrib = projected_balances.get(yr, {}).get('roth_contributions', 0)
            if age >= 59.5:
                tax_note = 'Tax-free (59½+)'
            elif roth_contrib >= e_amt:
                tax_note = 'Tax-free (contributions)'
            else:
                tax_note = 'Earnings taxed + 10% pen'
        elif e_type == 'Withdraw from 401k/IRA':
            tax_note = 'Income tax' + (' + 10% pen' if age < 59.5 else '')
        elif 'Roth Conversion' in e_type:
            tax_note = 'Income tax (no penalty)'
        else:
            tax_note = '~15% cap gains'
        
        status = '✅' if will_use >= e_amt else '⚠️ Partial'
        
        event_rows.append({
            'Year': yr,
            'Age': age,
            'Type': f'{icon} {e_type}',
            'Amount': display_amt,
            'Projected Balance': f'${proj_bal:,.0f}',
            'Available': f'${available:,.0f}',
            'Tax Impact': tax_note,
            'Status': status,
        })
        
        cumulative_by_account[source] = cumulative_by_account.get(source, 0) + will_use
    
    event_df = pd.DataFrame(event_rows)
    st.dataframe(event_df, use_container_width=True, hide_index=True)
    
    # Delete/manage events
    col1, col2 = st.columns([3, 1])
    with col1:
        event_options = [f"{i}: {e['type']} - {e['year']} - {'$' + str(e.get('amount', '')) if 'amount' in e else str(e.get('amount_pct', '')) + '%'}" for i, e in enumerate(st.session_state.financial_events)]
        event_to_delete = st.selectbox('Select event to remove', range(len(event_options)), format_func=lambda x: event_options[x], key='event_delete_select')
    with col2:
        if st.button('🗑️ Remove', key='remove_selected_event'):
            st.session_state.financial_events.pop(event_to_delete)
            st.rerun()
    
    if st.button('🗑️ Clear All Events'):
        st.session_state.financial_events = []
        st.rerun()
    
    # Totals
    total_conversions = 0
    total_withdrawals = 0
    for e in st.session_state.financial_events:
        yr = e['year']
        et = e['type']
        if 'amount' in e:
            val = e['amount']
        elif 'amount_pct' in e:
            pct = e['amount_pct']
            if pct > 1:
                pct = pct / 100.0
            if 'Roth Conversion' in et or et == 'Withdraw from 401k/IRA':
                base = projected_balances.get(yr, {}).get('trad_retirement', 0)
            elif et == 'Withdraw from Roth':
                base = projected_balances.get(yr, {}).get('roth_balance', 0)
            elif et == 'Withdraw from Brokerage':
                base = projected_balances.get(yr, {}).get('portfolio', 0)
            elif et == 'Withdraw from Crypto':
                base = projected_balances.get(yr, {}).get('crypto', 0)
            else:
                base = 0
            val = base * pct
        else:
            val = 0
        
        if 'Roth Conversion' in et:
            total_conversions += val
        elif 'Withdraw' in et:
            total_withdrawals += val
    
    st.caption(f"**Total Conversions:** ${total_conversions:,} | **Total Withdrawals:** ${total_withdrawals:,}")
else:
    st.info('No events scheduled. Add Roth conversions or withdrawals to plan early retirement cash flow.')

# ============================================
# RENTAL PROPERTY ANALYZER
# ============================================
st.header('🔍 Rental Property Analyzer')

with st.expander('📚 Real Estate Investing 101: Key Metrics Explained', False):
    st.markdown("""
    Evaluating a rental property deal? Here's what each metric means and what 
    to look for:
    
    | Metric | What It Measures | Good Target |
    |--------|------------------|-------------|
    | **Cash-on-Cash ROI** | Annual cash flow ÷ total cash invested | 8%+ |
    | **Cap Rate** | Net operating income ÷ property value (ignores financing) | 6-10% |
    | **GRM** | Purchase price ÷ annual gross rent (lower = better) | Under 15 |
    | **1% Rule** | Monthly rent ≥ 1% of purchase price | 1%+ |
    | **Cash Flow** | Money left after ALL expenses | $200+/unit/month |
    
    #### 💡 Quick Rules of Thumb
    - **The 50% Rule**: Roughly half of rent goes to expenses (not including mortgage). 
      If rent is $1,500/mo, expect ~$750/mo in expenses before your mortgage payment.
    - **CapEx Reserve**: Budget 5-10% of rent for future capital expenditures (roof, HVAC, 
      appliances). These costs WILL come — it's not a matter of if, but when.
    - **Vacancy**: Budget at least 5% — that's roughly 2-3 weeks per year without a tenant.
    - **Property Management**: Even if you self-manage, budget 8-10% so your numbers work 
      if you ever want to hire a manager.
    
    #### ⚠️ Common Beginner Mistakes
    - Underestimating expenses (especially CapEx and vacancy)
    - Not budgeting for property management
    - Focusing only on cash flow and ignoring total return (appreciation + equity paydown)
    - Buying in a bad location just because the numbers look good on paper
    """)

st.markdown('Analyze a potential rental deal without adding it to your portfolio. Great for quick deal analysis!')

with st.expander('📊 Quick Deal Analyzer', False):
    st.markdown('**Enter deal details to see key metrics**')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('**Purchase**')
        anal_price = st.number_input('Purchase Price', value=200000, step=5000, key='anal_price')
        anal_arv = st.number_input('After Repair Value', value=220000, step=5000, key='anal_arv')
        anal_closing = st.number_input('Closing Costs', value=5000, step=500, key='anal_closing')
        anal_repair = st.number_input('Repair Costs', value=15000, step=1000, key='anal_repair')
    
    with col2:
        st.markdown('**Financing**')
        anal_dp = st.slider('Down Payment %', 5, 50, 25, 5, key='anal_dp')
        anal_rate = st.number_input('Interest Rate %', value=7.0, step=0.25, key='anal_rate') / 100
        anal_term = st.selectbox('Loan Term', [15, 20, 30], index=2, key='anal_term')
        anal_pmi = st.number_input('PMI % (annual)', value=0.5, step=0.1, key='anal_pmi') / 100
    
    with col3:
        st.markdown('**Income & Expenses**')
        anal_rent = st.number_input('Monthly Rent', value=1800, step=50, key='anal_rent')
        anal_vacancy = st.slider('Vacancy %', 0, 20, 5, 1, key='anal_vacancy') / 100
        anal_tax_rate = st.number_input('Property Tax %', value=1.2, step=0.1, key='anal_tax_rate') / 100
        anal_expenses = st.number_input('Other Monthly Expenses', value=300, step=50, key='anal_expenses')
    
    # Calculate metrics
    anal_loan = anal_price * (1 - anal_dp / 100)
    anal_monthly_pi = calculate_mortgage_payment(anal_loan, anal_rate, anal_term)
    anal_monthly_pmi = (anal_loan * anal_pmi / 12) if anal_dp < 20 else 0
    anal_monthly_tax = anal_price * anal_tax_rate / 12
    
    anal_effective_rent = anal_rent * (1 - anal_vacancy)
    anal_total_expense = anal_monthly_pi + anal_monthly_pmi + anal_monthly_tax + anal_expenses
    anal_monthly_cf = anal_effective_rent - anal_total_expense
    anal_annual_cf = anal_monthly_cf * 12
    
    anal_cash_needed = (anal_price * anal_dp / 100) + anal_closing + anal_repair
    anal_coc = (anal_annual_cf / anal_cash_needed * 100) if anal_cash_needed > 0 else 0
    
    anal_noi = (anal_effective_rent * 12) - (anal_monthly_tax * 12) - (anal_expenses * 12)
    anal_cap_rate = (anal_noi / anal_price * 100) if anal_price > 0 else 0
    
    anal_grm = (anal_price / (anal_rent * 12)) if anal_rent > 0 else 0
    
    one_pct_rule = (anal_rent / anal_price * 100) if anal_price > 0 else 0
    
    fifty_pct_cf = anal_rent * 0.5 - anal_monthly_pi
    
    st.markdown('---')
    st.subheader('📈 Deal Metrics')
    
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric('Monthly Cash Flow', f'${anal_monthly_cf:,.0f}')
    with m2:
        st.metric('Cash-on-Cash ROI', f'{anal_coc:.1f}%')
    with m3:
        st.metric('Cap Rate', f'{anal_cap_rate:.1f}%')
    with m4:
        st.metric('GRM', f'{anal_grm:.1f}')
    with m5:
        one_pct_pass = '✅' if one_pct_rule >= 1.0 else '❌'
        st.metric('1% Rule', f'{one_pct_rule:.2f}% {one_pct_pass}')
    
    st.markdown('---')
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown('**💰 Cash Required**')
        dp_amount = anal_price * anal_dp / 100
        st.markdown(f"""
        - Down Payment: ${dp_amount:,.0f}
        - Closing Costs: ${anal_closing:,.0f}
        - Repairs: ${anal_repair:,.0f}
        - **Total: ${anal_cash_needed:,.0f}**
        """)
    
    with col_right:
        st.markdown('**📊 Monthly Breakdown**')
        st.markdown(f"""
        - Effective Rent: ${anal_effective_rent:,.0f}
        - P&I: -${anal_monthly_pi:,.0f}
        - Tax: -${anal_monthly_tax:,.0f}
        - PMI: -${anal_monthly_pmi:,.0f}
        - Other: -${anal_expenses:,.0f}
        - **Cash Flow: ${anal_monthly_cf:,.0f}**
        """)
    
    st.markdown('---')
    
    # Deal Rating
    score = 0
    feedback = []
    
    if anal_coc >= 10:
        score += 3
        feedback.append('✅ Excellent Cash-on-Cash (10%+)')
    elif anal_coc >= 8:
        score += 2
        feedback.append('✅ Good Cash-on-Cash (8%+)')
    elif anal_coc >= 5:
        score += 1
        feedback.append('⚠️ Moderate Cash-on-Cash (5-8%)')
    else:
        feedback.append('❌ Low Cash-on-Cash (<5%)')
    
    if one_pct_rule >= 1.0:
        score += 2
        feedback.append('✅ Passes 1% Rule')
    else:
        feedback.append('❌ Fails 1% Rule')
    
    if anal_monthly_cf >= 200:
        score += 2
        feedback.append('✅ Good monthly cash flow ($200+)')
    elif anal_monthly_cf >= 100:
        score += 1
        feedback.append('⚠️ Modest cash flow ($100-200)')
    else:
        feedback.append('❌ Low/negative cash flow')
    
    if anal_cap_rate >= 8:
        score += 2
        feedback.append('✅ Strong Cap Rate (8%+)')
    elif anal_cap_rate >= 6:
        score += 1
        feedback.append('⚠️ Average Cap Rate (6-8%)')
    else:
        feedback.append('❌ Low Cap Rate (<6%)')
    
    if score >= 8:
        rating = '🌟 EXCELLENT'
    elif score >= 5:
        rating = '✅ GOOD'
    elif score >= 3:
        rating = '⚠️ FAIR'
    else:
        rating = '❌ PASS'
    
    st.markdown(f'### Deal Rating: {rating}')
    for fb in feedback:
        st.markdown(fb)

# ============================================
# PROJECTION RESULTS
# ============================================
st.header('📈 Projection Results')

with st.expander('📚 Understanding Your Results', False):
    st.markdown("""
    #### Key Metrics Explained
    
    - **Net Worth** = Total assets (cash + investments + property equity) minus total debts. 
      This is your overall financial scoreboard.
    
    - **FI Ratio** = Passive Income ÷ Annual Expenses. When this hits **100%**, your 
      investments generate enough income to cover your living costs — you're **financially independent**.
      At 50%, you've reached **Coast FI** — you could stop saving aggressively and still reach full FI.
    
    - **Accessible Liquid** = Money you can access *right now* without major penalties. 
      This includes cash, brokerage, Roth contributions, and seasoned Roth conversions. 
      This number matters more than net worth for early retirees, since 401(k) money 
      is locked until 59½.
    
    - **Passive Income** = Dividends + net rental income. This is income that comes in 
      whether or not you work.
    
    #### 📊 Chart Tabs Guide
    - **Net Worth**: See how each account grows over time (stacked view)
    - **Cash Flow**: Income vs. expenses — watch for years where cash goes negative
    - **Retirement**: 401k, Roth, and HSA growth with withdrawal availability
    - **Real Estate**: Property equity building as you pay down mortgages
    - **Taxes**: See where your money goes and how pre-tax contributions save you money
    - **FI Progress**: The most important chart — track when passive income exceeds expenses
    - **Withdrawals**: Visualize your Roth conversion ladder and withdrawal strategy
    - **Full Data**: Download everything for your own analysis
    """)

results = run_projection(assumptions, st.session_state.properties, st.session_state.debts, st.session_state.financial_events)

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

final = results.iloc[-1]
start_row = results.iloc[0]

with col1:
    st.metric('Final Net Worth', f"${final['Net_Worth']:,.0f}")
with col2:
    st.metric('Final Passive Income', f"${final['Passive_Income']:,.0f}/yr")
with col3:
    st.metric('Final FI Ratio', f"{final['FI_Ratio']:.0%}")
with col4:
    fi_years = results[results['FI_Ratio'] >= 1.0]
    if len(fi_years) > 0:
        fi_year = fi_years['Year'].min()
        st.metric('FI Reached', f'{int(fi_year)}', '🎉')
    else:
        st.metric('FI Reached', 'Not yet', f"Max: {results['FI_Ratio'].max():.0%}")

col5, col6, col7, col8 = st.columns(4)
with col5:
    st.metric('Final Accessible Liquid', f"${final.get('Accessible_Liquid', 0):,.0f}")
with col6:
    st.metric('Final Brokerage', f"${final['Portfolio']:,.0f}")
with col7:
    st.metric('Final Crypto', f"${final['Crypto']:,.0f}")
with col8:
    st.metric('Final Cash', f"${final['Cash']:,.0f}")

if st.session_state.debts or st.session_state.properties:
    col9, col10 = st.columns(2)
    with col9:
        st.metric('Current Total Debt', f"${start_row.get('Total_Debt', 0):,.0f}")
    with col10:
        debt_free_years = results[results['Total_Debt'] <= 0]
        if len(debt_free_years) > 0:
            debt_free_year = debt_free_years['Year'].min()
            st.metric('Debt Free Year', f'{int(debt_free_year)}', '🎉')
        else:
            st.metric('Final Debt', f"${final.get('Total_Debt', 0):,.0f}")

# ============================================
# CHART TABS
# ============================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    '💰 Net Worth', '💵 Cash Flow', '🏦 Retirement', '🏠 Real Estate',
    '📊 Taxes', '🎯 FI Progress', '💳 Debt Payoff', '📅 Withdrawals', '📋 Full Data'
])

with tab1:
    render_net_worth_tab(results, retirement_year)

with tab2:
    render_cash_flow_tab(results)

with tab3:
    render_retirement_tab(results, start_year, end_year, birth_year, retirement_year)

with tab4:
    render_real_estate_tab(results, st.session_state.properties)

with tab5:
    render_taxes_tab(results, assumptions)

with tab6:
    render_fi_progress_tab(results, retirement_year)

with tab7:
    render_debt_payoff_tab(results, st.session_state.properties, st.session_state.debts, start_year)

with tab8:
    render_withdrawals_tab(results, retirement_year, st.session_state.financial_events)

with tab9:
    render_full_data_tab(results)


# ============================================
# DATA EXPORT CENTER
# ============================================
with st.expander("📦 Export Data", expanded=False):
    st.markdown("### Export All Data for Analysis & Debugging")
    
    # ---- FINANCIAL EVENTS EXPORT ----
    st.markdown("#### 📅 Financial Events")
    if st.session_state.financial_events:
        events_df = pd.DataFrame(st.session_state.financial_events)
        events_df = events_df.sort_values('year')
        st.dataframe(events_df, use_container_width=True, hide_index=True)
        
        events_csv = events_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Events CSV",
            data=events_csv,
            file_name=f"financial_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="export_events"
        )
    else:
        st.info("No financial events scheduled.")
    
    st.markdown("---")
    
    # ---- TAB DATA EXPORTS ----
    st.markdown("#### 📊 Export Tab Data")
    
    # Define data for each tab
    tab_exports = {}
    
    # Net Worth tab data
    net_worth_cols = ['Year', 'Age', 'Cash', 'Portfolio', 'Crypto', 'Trad_Retirement', 
                      'Roth_Balance', 'HSA_Balance', 'Property_Equity', 'Property_Debt', 
                      'Other_Debt', 'Total_Debt', 'Net_Worth']
    tab_exports['Net Worth'] = results[[c for c in net_worth_cols if c in results.columns]]
    
    # Cash Flow tab data
    cashflow_cols = ['Year', 'Age', 'Gross_Salary', 'Total_Tax', 'Net_Income', 
                     'Total_Expenses', 'Dividends', 'Net_Rental', 'Passive_Income',
                     'Cash_Savings', 'Cash']
    tab_exports['Cash Flow'] = results[[c for c in cashflow_cols if c in results.columns]]
    
    # Retirement Accounts tab data
    retirement_cols = ['Year', 'Age', 'Trad_Retirement', 'Roth_Balance', 'Roth_Contributions',
                       'Roth_Earnings', 'Roth_Available', 'HSA_Balance', 'Seasoned_Conversions_Avail',
                       'Event_Roth_Conversion', 'Event_401k_WD', 'Event_Roth_WD']
    tab_exports['Retirement'] = results[[c for c in retirement_cols if c in results.columns]]
    
    # Real Estate tab data
    realestate_cols = ['Year', 'Age', 'Property_Value', 'Property_Debt', 'Property_Equity',
                       'Rental_Income', 'Rental_Expenses', 'Net_Rental', 'Property_Purchase_Costs']
    tab_exports['Real Estate'] = results[[c for c in realestate_cols if c in results.columns]]
    
    # Taxes tab data
    taxes_cols = ['Year', 'Age', 'Gross_Salary', 'Federal_Tax', 'State_Tax', 'FICA_Tax',
                  'Total_Tax', 'Effective_Tax_Rate']
    tab_exports['Taxes'] = results[[c for c in taxes_cols if c in results.columns]]
    
    # FI Progress tab data
    fi_cols = ['Year', 'Age', 'Net_Worth', 'Accessible_Liquid', 'Accessible_Portfolio',
               'Accessible_Crypto', 'FI_Ratio', 'Passive_Income', 'Total_Expenses']
    tab_exports['FI Progress'] = results[[c for c in fi_cols if c in results.columns]]
    
    # Withdrawals tab data
    withdrawals_cols = ['Year', 'Age', 'Event_Roth_Conversion', 'Event_Roth_WD',
                        'Event_Brokerage_WD', 'Event_Crypto_WD', 'Event_401k_WD',
                        'Event_Taxes_Paid', 'Event_Penalties_Paid', 'Roth_Note']
    tab_exports['Withdrawals'] = results[[c for c in withdrawals_cols if c in results.columns]]
    
    # Individual tab exports
    col1, col2, col3 = st.columns(3)
    tab_names = list(tab_exports.keys())
    
    for i, (tab_name, tab_df) in enumerate(tab_exports.items()):
        col = [col1, col2, col3][i % 3]
        with col:
            csv_data = tab_df.to_csv(index=False)
            st.download_button(
                label=f"📥 {tab_name}",
                data=csv_data,
                file_name=f"{tab_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"export_{tab_name}"
            )
    
    st.markdown("---")
    
    # ---- EXPORT ALL AT ONCE ----
    st.markdown("#### 📦 Export Everything")
    
    # Create a comprehensive export with all data
    all_data_export = {
        'metadata': {
            'exported_at': datetime.now().isoformat(),
            'start_year': start_year,
            'end_year': end_year,
            'retirement_year': retirement_year,
            'total_years': len(results),
        },
        'assumptions': assumptions,
        'properties': st.session_state.properties,
        'debts': st.session_state.debts,
        'financial_events': st.session_state.financial_events,
        'projection_data': results.to_dict(orient='records')
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Full JSON export
        all_json = json.dumps(all_data_export, indent=2, default=str)
        st.download_button(
            label="📥 Export All (JSON)",
            data=all_json,
            file_name=f"full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="export_all_json"
        )
    
    with col2:
        # Full CSV (all columns)
        full_csv = results.to_csv(index=False)
        st.download_button(
            label="📥 Full Projection (CSV)",
            data=full_csv,
            file_name=f"full_projection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="export_all_csv"
        )
    
    with col3:
        # Create combined text report with all sections
        combined_data = []
        combined_data.append("=== ASSUMPTIONS ===")
        for key, val in assumptions.items():
            combined_data.append(f"{key},{val}")
        combined_data.append("")
        combined_data.append("=== PROPERTIES ===")
        if st.session_state.properties:
            props_df = pd.DataFrame(st.session_state.properties)
            combined_data.append(props_df.to_csv(index=False))
        combined_data.append("")
        combined_data.append("=== DEBTS ===")
        if st.session_state.debts:
            debts_df = pd.DataFrame(st.session_state.debts)
            combined_data.append(debts_df.to_csv(index=False))
        combined_data.append("")
        combined_data.append("=== FINANCIAL EVENTS ===")
        if st.session_state.financial_events:
            events_df = pd.DataFrame(st.session_state.financial_events)
            combined_data.append(events_df.to_csv(index=False))
        combined_data.append("")
        combined_data.append("=== FULL PROJECTION ===")
        combined_data.append(results.to_csv(index=False))
        
        combined_text = "\n".join(combined_data)
        st.download_button(
            label="📥 Combined Report (TXT)",
            data=combined_text,
            file_name=f"combined_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key="export_combined"
        )
    
    st.markdown("---")
    
    # ---- DEBUG INFO ----
    st.markdown("#### 🔧 Debug Info")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Starting Assets:**")
        st.text(f"401k/IRA: ${assumptions.get('current_401k', 0):,.0f}")
        st.text(f"Roth Balance: ${assumptions.get('current_roth_balance', 0):,.0f}")
        st.text(f"Roth Basis: ${assumptions.get('current_roth_contributions', 0):,.0f}")
        st.text(f"Brokerage: ${assumptions.get('current_portfolio', 0):,.0f}")
        st.text(f"Crypto: ${assumptions.get('current_crypto', 0):,.0f}")
        st.text(f"Cash: ${assumptions.get('current_cash', 0):,.0f}")
        st.text(f"HSA: ${assumptions.get('current_hsa', 0):,.0f}")
    with col2:
        st.markdown("**Annual Contributions:**")
        st.text(f"401k: ${assumptions.get('contrib_401k', 0):,.0f}")
        st.text(f"Employer 401k: ${assumptions.get('employer_401k', 0):,.0f}")
        st.text(f"Roth IRA: ${assumptions.get('contrib_roth', 0):,.0f}")
        st.text(f"HSA: ${assumptions.get('contrib_hsa', 0):,.0f}")
        st.text(f"Brokerage: ${assumptions.get('contrib_brokerage', 0):,.0f}")
        st.text(f"Crypto: ${assumptions.get('contrib_crypto', 0):,.0f}")
    with col3:
        st.markdown("**Other Settings:**")
        st.text(f"Birth Year: {assumptions.get('birth_year', 'N/A')}")
        st.text(f"Salary: ${assumptions.get('current_salary', 0):,.0f}")
        st.text(f"Portfolio Return: {assumptions.get('portfolio_return', 0)*100:.1f}%")
        st.text(f"Inflation: {assumptions.get('inflation', 0)*100:.1f}%")
        st.text(f"Retirement Year: {assumptions.get('retirement_year', 'N/A')}")
    
    # Show first few years
    st.markdown("**First 5 Years - Key Columns:**")
    key_cols = ['Year', 'Age', 'Gross_Salary', 'Trad_Retirement', 'Roth_Balance', 
                'Portfolio', 'Crypto', 'Cash', 'Net_Worth']
    available_cols = [c for c in key_cols if c in results.columns]
    st.dataframe(results[available_cols].head(5), use_container_width=True, hide_index=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
**📖 Getting the Most Out of This Tool:**

1. **Start with the sidebar** — enter your income, expenses, and current account balances
2. **Add debts** you currently have (car loans, student loans, etc.) to see their impact on cash flow
3. **Add properties** to model buying a home (stops rent) or rental properties (generates passive income)
4. **Plan your withdrawal strategy** using Financial Events — this is key for early retirement planning
5. **Check the FI Progress tab** to see when your passive income will cover your expenses
6. **Save and compare scenarios** — try "aggressive savings" vs. "buy rental property" vs. "lean FIRE budget"

*The best way to learn is to experiment — change one variable at a time and see how it affects your projection!*
""")

st.caption("""
**Disclaimer:** This tool is for educational and informational purposes only and does not constitute financial, 
tax, or investment advice. Projections are based on simplified models and assumptions that may not reflect actual 
market conditions, tax law changes, or your individual circumstances. Always consult a qualified financial advisor 
before making significant financial decisions. The authors make no guarantees about the accuracy or completeness 
of the calculations.
""")
