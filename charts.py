import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from calculations import calculate_mortgage_payment


def render_net_worth_tab(results, retirement_year):
    """Tab 1: Net Worth Stacked Area Chart"""
    fig = go.Figure()
    
    # Cash shown as a line (can go negative)
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Cash'],
        name='Cash', mode='lines', line=dict(color='rgba(65, 105, 225, 1)', width=2)
    ))
    
    # Other assets stacked (always positive)
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Portfolio'],
        name='Taxable Brokerage', stackgroup='one', fillcolor='rgba(255, 165, 0, 0.6)'
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Crypto'],
        name='Crypto', stackgroup='one', fillcolor='rgba(255, 215, 0, 0.6)'
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Trad_Retirement'],
        name='401k/Traditional', stackgroup='one', fillcolor='rgba(50, 205, 50, 0.6)'
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Roth_Balance'],
        name='Roth IRA', stackgroup='one', fillcolor='rgba(138, 43, 226, 0.6)'
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['HSA_Balance'],
        name='HSA', stackgroup='one', fillcolor='rgba(0, 191, 255, 0.6)'
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Property_Equity'],
        name='Property Equity', stackgroup='one', fillcolor='rgba(220, 20, 60, 0.6)'
    ))
    
    # Add zero line for reference
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    
    fig.add_vline(x=retirement_year, line_dash="dash", line_color="red", 
                  annotation_text="Retirement")
    
    fig.update_layout(
        title="Net Worth Over Time (Cash can go negative)",
        xaxis_title="Year",
        yaxis_title="Value ($)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_cash_flow_tab(results):
    """Tab 2: Annual Cash Flow Analysis"""
    st.subheader("Annual Cash Flow Analysis")
    
    fig = make_subplots(rows=2, cols=2, 
                        subplot_titles=("Income vs Expenses", "Yearly Cash Savings", 
                                       "Total Cash Balance", "Net Cash Flow"))
    
    # 1. Income vs Expenses (top-left)
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Gross_Salary'],
        name='Gross Salary', line=dict(color='blue', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Net_Income'],
        name='Net Income (after tax)', line=dict(color='green', width=2)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Total_Expenses'],
        name='Total Expenses', line=dict(color='red', width=2)
    ), row=1, col=1)
    
    # Show property purchase years as markers on expenses
    purchase_years = results[results['Property_Purchase_Costs'] > 0]
    if len(purchase_years) > 0:
        fig.add_trace(go.Scatter(
            x=purchase_years['Year'], y=purchase_years['Total_Expenses'],
            mode='markers', name='Property Purchase',
            marker=dict(color='red', size=12, symbol='star')
        ), row=1, col=1)
    
    # 2. Yearly Cash Savings (top-right)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Cash_Savings'],
        name='Cash Savings', marker_color='rgba(50, 205, 50, 0.7)'
    ), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Discretionary_Cash'],
        name='Discretionary Cash', line=dict(color='purple', width=2, dash='dot')
    ), row=1, col=2)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=1, col=2)
    
    # 3. Total Cash Balance (bottom-left)
    cash_colors = ['green' if x >= 0 else 'red' for x in results['Cash']]
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Cash'],
        name='Cash Balance', marker_color=cash_colors
    ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    
    # 4. Net Cash Flow (bottom-right)
    ncf_colors = ['green' if x >= 0 else 'red' for x in results['Net_Cash_Flow']]
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Net_Cash_Flow'],
        name='Net Cash Flow', marker_color=ncf_colors
    ), row=2, col=2)
    fig.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=2)
    
    # Mark property purchases on net cash flow
    if len(purchase_years) > 0:
        fig.add_trace(go.Scatter(
            x=purchase_years['Year'], y=purchase_years['Net_Cash_Flow'],
            mode='markers', name='Property Purchase',
            marker=dict(color='red', size=12, symbol='star'), showlegend=False
        ), row=2, col=2)
    
    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Cash Flow Table
    with st.expander("💰 Detailed Cash Flow Table"):
        cash_flow_df = results[['Year', 'Age', 'Gross_Salary', 'Total_Tax', 'Net_Income', 
                                'Living_Expenses', 'Housing_Cost', 'Property_Purchase_Costs',
                                'Total_Expenses', 'Discretionary_Cash', 'Net_Cash_Flow',
                                'Cash_Savings', 'Cash']].copy()
        cash_flow_df['Gross_Salary'] = cash_flow_df['Gross_Salary'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Total_Tax'] = cash_flow_df['Total_Tax'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Net_Income'] = cash_flow_df['Net_Income'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Living_Expenses'] = cash_flow_df['Living_Expenses'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Housing_Cost'] = cash_flow_df['Housing_Cost'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Property_Purchase_Costs'] = cash_flow_df['Property_Purchase_Costs'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Total_Expenses'] = cash_flow_df['Total_Expenses'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Discretionary_Cash'] = cash_flow_df['Discretionary_Cash'].apply(lambda x: f"${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}")
        cash_flow_df['Net_Cash_Flow'] = cash_flow_df['Net_Cash_Flow'].apply(lambda x: f"${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}")
        cash_flow_df['Cash_Savings'] = cash_flow_df['Cash_Savings'].apply(lambda x: f"${x:,.0f}")
        cash_flow_df['Cash'] = cash_flow_df['Cash'].apply(lambda x: f"${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}")
        st.dataframe(cash_flow_df, use_container_width=True)


def render_retirement_tab(results, start_year, end_year, birth_year, retirement_year):
    """Tab 3: Retirement Account Growth & Availability"""
    st.subheader("🏦 Retirement Account Growth & Availability")
    
    # Account Growth Chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Trad_Retirement'],
        name='401(k)/Traditional IRA', line=dict(color='green', width=2),
        fill='tozeroy', fillcolor='rgba(50, 205, 50, 0.3)'
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Roth_Balance'],
        name='Roth IRA Total', line=dict(color='purple', width=2),
        fill='tozeroy', fillcolor='rgba(138, 43, 226, 0.3)'
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Roth_Contributions'],
        name='Roth Contributions (Accessible)', line=dict(color='purple', width=2, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['HSA_Balance'],
        name='HSA', line=dict(color='deepskyblue', width=2),
        fill='tozeroy', fillcolor='rgba(0, 191, 255, 0.3)'
    ))
    
    fig.add_vline(x=retirement_year, line_dash="dash", line_color="red", 
                  annotation_text="Retirement")
    
    # Add age 59.5 line
    age_59_5_year = birth_year + 60  # Approximate
    if age_59_5_year >= start_year and age_59_5_year <= end_year:
        fig.add_vline(x=age_59_5_year, line_dash="dash", line_color="orange", 
                      annotation_text="Age 59½")
    
    fig.update_layout(
        title="Retirement Account Balances Over Time",
        xaxis_title="Year",
        yaxis_title="Balance ($)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Roth IRA Availability Section
    st.markdown("---")
    st.subheader("📋 Roth IRA Withdrawal Availability")
    
    st.markdown("""
    **Roth IRA Rules:**
    - ✅ **Contributions**: Can be withdrawn anytime, tax-free, penalty-free
    - ⏳ **Conversions**: Subject to 5-year rule per conversion
    - 🔒 **Earnings**: Require age 59½ AND 5-year rule for tax/penalty-free withdrawal
    """)
    
    # Create availability table
    roth_df = results[['Year', 'Age', 'Roth_Balance', 'Roth_Contributions', 'Roth_Earnings', 
                       'Roth_Available', 'Roth_Note']].copy()
    
    # Format for display
    roth_display = roth_df.copy()
    roth_display['Roth_Balance'] = roth_display['Roth_Balance'].apply(lambda x: f"${x:,.0f}")
    roth_display['Roth_Contributions'] = roth_display['Roth_Contributions'].apply(lambda x: f"${x:,.0f}")
    roth_display['Roth_Earnings'] = roth_display['Roth_Earnings'].apply(lambda x: f"${x:,.0f}")
    roth_display['Roth_Available'] = roth_display['Roth_Available'].apply(lambda x: f"${x:,.0f}")
    roth_display.columns = ['Year', 'Age', 'Total Balance', 'Contributions', 'Earnings', 'Available Now', 'Status']
    
    st.dataframe(roth_display, use_container_width=True)
    
    # HSA Section
    st.markdown("---")
    st.subheader("💊 HSA Availability")
    
    st.markdown("""
    **HSA Rules (Triple Tax Advantage):**
    - ✅ **Medical Expenses**: Always available tax-free for qualified medical expenses
    - 🎂 **After Age 65**: Can withdraw for ANY purpose (taxed as income, no penalty)
    - 📈 **Investment Growth**: Tax-free growth forever
    """)
    
    # Find year when HSA becomes unrestricted
    hsa_unrestricted_year = birth_year + 65
    if hsa_unrestricted_year >= start_year and hsa_unrestricted_year <= end_year:
        hsa_at_65 = results[results['Year'] == hsa_unrestricted_year]['HSA_Balance'].values
        if len(hsa_at_65) > 0:
            st.success(f"🎂 At age 65 ({hsa_unrestricted_year}), your HSA balance of **${hsa_at_65[0]:,.0f}** becomes available for any purpose!")


def render_real_estate_tab(results, properties):
    """Tab 4: Real Estate"""
    if properties:
        # Real Estate Chart - Stacked to show debt vs equity clearly
        fig = go.Figure()
        
        # Stacked bar: Debt on bottom, Equity on top = Total Property Value
        fig.add_trace(go.Bar(
            x=results['Year'], y=results['Property_Debt'],
            name='Mortgage Debt', marker_color='rgba(220, 20, 60, 0.8)'
        ))
        fig.add_trace(go.Bar(
            x=results['Year'], y=results['Property_Equity'],
            name='Equity', marker_color='rgba(50, 205, 50, 0.8)'
        ))
        
        # Line showing total property value
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Property_Value'],
            name='Total Property Value', line=dict(color='blue', width=2, dash='dot'),
            mode='lines'
        ))
        
        # Add vertical lines for purchase years
        for prop in properties:
            fig.add_vline(x=prop['purchase_year'], line_dash="dot", line_color="gray",
                         annotation_text=f"Buy: {prop['name']}", annotation_position="top")
        
        fig.update_layout(
            title="Real Estate: Debt vs Equity (Stacked = Property Value)",
            barmode='stack',  # Stack so debt + equity = property value
            xaxis_title="Year",
            yaxis_title="Value ($)",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Property Summary Table
        st.subheader("Property Details")
        prop_data = []
        for prop in properties:
            loan = prop['purchase_price'] * (1 - prop['down_payment_pct'])
            monthly_pmt = calculate_mortgage_payment(loan, prop['mortgage_rate'], prop['mortgage_years'])
            prop_type = "Primary" if prop['is_primary'] else "Rental"
            prop_data.append({
                'Property': prop['name'],
                'Type': prop_type,
                'Purchase Year': prop['purchase_year'],
                'Price': f"${prop['purchase_price']:,}",
                'Down Payment': f"${prop['purchase_price'] * prop['down_payment_pct']:,.0f}",
                'Loan Amount': f"${loan:,.0f}",
                'Monthly Payment': f"${monthly_pmt:,.0f}",
                'Rate': f"{prop['mortgage_rate']*100:.2f}%",
                'Term': f"{prop['mortgage_years']} yrs"
            })
        st.dataframe(pd.DataFrame(prop_data), use_container_width=True, hide_index=True)
        
        # Rental income details
        if any(not p['is_primary'] for p in properties):
            st.subheader("Rental Property Cash Flow")
            rental_cols = ['Year', 'Rental_Income', 'Rental_Expenses', 'Net_Rental']
            st.dataframe(results[rental_cols].style.format({
                'Rental_Income': '${:,.0f}',
                'Rental_Expenses': '${:,.0f}',
                'Net_Rental': '${:,.0f}'
            }), use_container_width=True)
    else:
        st.info("Add properties to see real estate projections here.")


def render_taxes_tab(results, assumptions):
    """Tab 5: Tax Breakdown Analysis"""
    st.subheader("💰 Tax Breakdown Analysis")
    
    # Explanation of tax treatment
    if assumptions.get('state') == 'SC':
        st.markdown("""
        **🌴 South Carolina Tax Info:**
        - **SC uses federal taxable income** as the starting point (after standard deduction)
        - **SC Tax Brackets (2026)**: 0% up to \$3,560 → 3% up to \$17,830 → **6%** above
        - **Federal 2026 Brackets**: 10% → 12% → 22% → 24% → 32% → 35% → 37%
        
        **How Pre-Tax Contributions Work:**
        - **401(k) & HSA** reduce your **Federal & SC state taxable income** (big tax savings!)
        - **FICA taxes** (SS + Medicare) are on **gross salary** - NOT reduced by 401k/HSA
        """)
    else:
        st.markdown("""
        **How Pre-Tax Contributions Work:**
        - **401(k) & HSA** contributions reduce your **Federal & State taxable income** (tax savings!)
        - **FICA taxes** (Social Security & Medicare) are calculated on your **gross salary** - 401k/HSA do NOT reduce FICA
        - Your **effective tax rate** = Total Taxes ÷ Gross Salary
        """)
    
    # Show first year tax savings if working
    first_working = results[results['Working'] == True]
    if len(first_working) > 0:
        first_year = first_working.iloc[0]
        if first_year['Tax_Savings_PreTax'] > 0:
            st.success(f"💰 **Tax Savings from Pre-Tax Contributions**: ${first_year['Tax_Savings_PreTax']:,.0f}/year saved by contributing to 401k & HSA!")
    
    # Itemized vs Standard Deduction Comparison
    st.markdown("---")
    st.subheader("📝 Itemized vs Standard Deduction")
    
    if len(first_working) > 0:
        fy = first_working.iloc[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Standard Deduction", f"${fy['Std_Deduction']:,.0f}")
        with col2:
            st.metric("Itemized Deduction", f"${fy['Itemized_Deduction']:,.0f}", 
                     delta=f"${fy['Itemized_Deduction'] - fy['Std_Deduction']:,.0f}" if fy['Itemized_Deduction'] != fy['Std_Deduction'] else None)
        with col3:
            status = "✅ Itemizing" if fy['Using_Itemized'] else "📋 Standard"
            st.metric("Using", status)
        
        # Breakdown of itemized deductions
        st.markdown("**Itemized Deduction Breakdown:**")
        deduction_data = {
            'Component': ['Mortgage Interest (Primary)', 'SALT (State Tax + Property Tax)', 'Total Itemized'],
            'Amount': [f"${fy['Mortgage_Interest']:,.0f}", f"${fy['SALT_Deduction']:,.0f}", f"${fy['Itemized_Deduction']:,.0f}"]
        }
        st.table(pd.DataFrame(deduction_data))
        
        if fy['Using_Itemized']:
            st.success(f"🏠 **You benefit from itemizing!** Your mortgage interest + SALT exceeds the standard deduction by ${fy['Itemized_Deduction'] - fy['Std_Deduction']:,.0f}.")
        else:
            st.info(f"📋 **Standard deduction is better.** It's ${fy['Std_Deduction'] - fy['Itemized_Deduction']:,.0f} higher than your itemized deductions.")
        
        st.caption("**Note:** SALT (State and Local Tax) deduction is capped at $10,000. Includes state income tax + property tax on primary residence.")
    
    st.markdown("---")
    
    fig = make_subplots(rows=2, cols=2, 
                        subplot_titles=("Tax Breakdown by Type", "FICA Breakdown (SS + Medicare)", 
                                       "Effective Tax Rate Over Time", "Tax Savings from Pre-Tax Contributions"))
    
    # 1. Stacked bar chart for all tax components (top-left)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Federal_Tax'],
        name='Federal Tax', marker_color='rgba(220, 20, 60, 0.7)'
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['State_Tax'],
        name='State Tax', marker_color='rgba(255, 165, 0, 0.7)'
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['SS_Tax'],
        name='Social Security', marker_color='rgba(65, 105, 225, 0.7)'
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Medicare_Tax'],
        name='Medicare', marker_color='rgba(138, 43, 226, 0.7)'
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Dividend_Tax'],
        name='Dividend Tax', marker_color='rgba(0, 128, 128, 0.7)'
    ), row=1, col=1)
    
    # 2. FICA breakdown (top-right)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['SS_Tax'],
        name='Social Security', marker_color='rgba(65, 105, 225, 0.7)', showlegend=False
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Medicare_Tax'],
        name='Medicare', marker_color='rgba(138, 43, 226, 0.7)', showlegend=False
    ), row=1, col=2)
    
    # 3. Effective tax rate line (bottom-left)
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Effective_Tax_Rate'],
        name='Effective Rate %', line=dict(color='purple', width=2), fill='tozeroy',
        fillcolor='rgba(138, 43, 226, 0.2)'
    ), row=2, col=1)
    
    # 4. Tax savings from pre-tax contributions (bottom-right)
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['Tax_Savings_PreTax'],
        name='Tax Savings', marker_color='rgba(50, 205, 50, 0.7)'
    ), row=2, col=2)
    
    fig.update_layout(height=600, barmode='stack', showlegend=True)
    fig.update_yaxes(title_text="Tax Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="FICA ($)", row=1, col=2)
    fig.update_yaxes(title_text="Rate (%)", row=2, col=1)
    fig.update_yaxes(title_text="Savings ($)", row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed Tax Calculation Table
    with st.expander("📊 Detailed Tax Calculation Table", expanded=True):
        st.markdown("""
        **Column Explanations:**
        - **Pre-Tax Ded.**: 401k + HSA contributions (reduce federal/state tax, NOT FICA)
        - **AGI**: Adjusted Gross Income = Gross Salary - Pre-Tax Deductions
        - **Deduction**: Actual deduction used (Standard or Itemized, whichever is higher)
        - **Taxable Inc.**: AGI - Deduction (what federal tax is calculated on)
        - **SS Tax**: Social Security tax (6.2% up to $168,600 wage base)
        - **Medicare**: Medicare tax (1.45% + 0.9% additional over $200k)
        """)
        
        tax_df = results[['Year', 'Age', 'Gross_Salary', 'Pre_Tax_Deductions', 'AGI', 
                          'Actual_Deduction', 'Using_Itemized', 'Taxable_Income', 
                          'Federal_Tax', 'State_Tax', 'SS_Tax', 
                          'Medicare_Tax', 'Total_Tax', 'Tax_Savings_PreTax',
                          'Effective_Tax_Rate']].copy()
        
        # Convert using_itemized to display text
        tax_df['Using_Itemized'] = tax_df['Using_Itemized'].apply(lambda x: 'Item.' if x else 'Std.')
        
        # Rename columns for display
        tax_df.columns = ['Year', 'Age', 'Gross Salary', 'Pre-Tax Ded.', 'AGI', 
                          'Deduction', 'Type', 'Taxable Inc.', 'Federal', 'State', 'SS Tax', 
                          'Medicare', 'Total Tax', 'Tax Savings',
                          'Eff. Rate %']
        
        st.dataframe(tax_df.style.format({
            'Gross Salary': '${:,.0f}',
            'Pre-Tax Ded.': '${:,.0f}',
            'AGI': '${:,.0f}',
            'Deduction': '${:,.0f}',
            'Taxable Inc.': '${:,.0f}',
            'Federal': '${:,.0f}',
            'State': '${:,.0f}',
            'SS Tax': '${:,.0f}',
            'Medicare': '${:,.0f}',
            'Total Tax': '${:,.0f}',
            'Tax Savings': '${:,.0f}',
            'Eff. Rate %': '{:.1f}%'
        }), use_container_width=True)


def render_fi_progress_tab(results, retirement_year):
    """Tab 6: Financial Independence Progress"""
    st.subheader("🎯 Financial Independence Progress")
    
    fig = make_subplots(rows=1, cols=2, 
                        subplot_titles=("FI Ratio Over Time", "Passive Income vs Expenses"))
    
    # FI Ratio progress
    colors = ['green' if x >= 1 else 'orange' if x >= 0.5 else 'red' for x in results['FI_Ratio']]
    fig.add_trace(go.Bar(
        x=results['Year'], y=results['FI_Ratio'],
        name='FI Ratio', marker_color=colors
    ), row=1, col=1)
    fig.add_hline(y=1.0, line_dash="dash", line_color="green", row=1, col=1,
                  annotation_text="FI Target (100%)")
    fig.add_hline(y=0.5, line_dash="dot", line_color="orange", row=1, col=1,
                  annotation_text="Coast FI (50%)")
    
    # Passive income vs expenses comparison
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Passive_Income'],
        name='Passive Income', line=dict(color='green', width=2)
    ), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=results['Year'], y=results['Total_Expenses'],
        name='Total Expenses', line=dict(color='red', width=2)
    ), row=1, col=2)
    
    # Add retirement marker
    fig.add_vline(x=retirement_year, line_dash="dash", line_color="blue", row=1, col=1,
                  annotation_text="Retirement")
    fig.add_vline(x=retirement_year, line_dash="dash", line_color="blue", row=1, col=2)
    
    fig.update_layout(height=400, showlegend=True)
    fig.update_yaxes(title_text="FI Ratio", row=1, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=1, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # FI milestones
    fi_crossed = results[results['FI_Ratio'] >= 1.0]
    if len(fi_crossed) > 0:
        fi_year = fi_crossed['Year'].min()
        fi_age = fi_crossed['Age'].min()
        st.success(f"🎉 You reach Financial Independence in **{int(fi_year)}** at age **{int(fi_age)}**!")
    else:
        max_fi = results['FI_Ratio'].max()
        st.warning(f"📈 Peak FI Ratio: **{max_fi:.1%}** - Consider increasing savings or reducing expenses to reach FI.")
    
    # Detailed FI progress table
    with st.expander("📊 FI Progress Details"):
        fi_df = results[['Year', 'Age', 'Passive_Income', 'Total_Expenses', 'FI_Ratio', 
                         'Accessible_Liquid', 'Net_Worth']].copy()
        fi_df['Passive_Income'] = fi_df['Passive_Income'].apply(lambda x: f"${x:,.0f}")
        fi_df['Total_Expenses'] = fi_df['Total_Expenses'].apply(lambda x: f"${x:,.0f}")
        fi_df['FI_Ratio'] = fi_df['FI_Ratio'].apply(lambda x: f"{x:.1%}")
        fi_df['Accessible_Liquid'] = fi_df['Accessible_Liquid'].apply(lambda x: f"${x:,.0f}")
        fi_df['Net_Worth'] = fi_df['Net_Worth'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(fi_df, use_container_width=True)


def render_debt_payoff_tab(results, properties, debts, start_year):
    """Tab 7: Debt Payoff Chart"""
    if debts or properties:
        fig = go.Figure()
        
        # Total debt over time
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Total_Debt'],
            name='Total Debt', fill='tozeroy',
            line=dict(color='red', width=2),
            fillcolor='rgba(220, 20, 60, 0.3)'
        ))
        
        # Property debt
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Property_Debt'],
            name='Property Mortgages', line=dict(color='orange', width=2, dash='dash')
        ))
        
        # Other debt
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Other_Debt'],
            name='Other Debts', line=dict(color='purple', width=2, dash='dot')
        ))
        
        # Add vertical lines for property purchases
        for prop in properties:
            loan = prop['purchase_price'] * (1 - prop['down_payment_pct'])
            fig.add_vline(x=prop['purchase_year'], line_dash="dot", line_color="blue",
                         annotation_text=f"+${loan/1000:.0f}K: {prop['name']}", 
                         annotation_position="top")
        
        # Debt-free line
        debt_free_year = results[results['Total_Debt'] <= 0]['Year'].min()
        if pd.notna(debt_free_year):
            fig.add_vline(x=debt_free_year, line_dash="dash", line_color="green",
                         annotation_text=f"Debt Free! ({int(debt_free_year)})")
        
        fig.update_layout(
            title="Debt Payoff Over Time",
            xaxis_title="Year",
            yaxis_title="Debt Balance ($)",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show all debts summary
        st.subheader("All Debts Summary")
        all_debts = []
        
        # Add property mortgages
        for prop in properties:
            loan = prop['purchase_price'] * (1 - prop['down_payment_pct'])
            monthly_pmt = calculate_mortgage_payment(loan, prop['mortgage_rate'], prop['mortgage_years'])
            payoff_year = prop['purchase_year'] + prop['mortgage_years']
            all_debts.append({
                'Debt': f"🏠 {prop['name']}",
                'Type': 'Mortgage',
                'Start Year': prop['purchase_year'],
                'Original Amount': f"${loan:,.0f}",
                'Monthly Payment': f"${monthly_pmt:,.0f}",
                'Rate': f"{prop['mortgage_rate']*100:.1f}%",
                'Payoff Year': payoff_year
            })
        
        # Add other debts
        for debt in debts:
            monthly_pmt = calculate_mortgage_payment(debt['original_balance'], debt['interest_rate'], debt['term_years'])
            months_remaining = (debt['term_years'] * 12) - debt['months_already_paid']
            payoff_year = start_year + int(months_remaining / 12)
            icon = {"Mortgage": "🏠", "Car Loan": "🚗", "Student Loan": "🎓", 
                   "Personal Loan": "💵", "Credit Card": "💳", "Other": "📄"}.get(debt['type'], "📄")
            all_debts.append({
                'Debt': f"{icon} {debt['name']}",
                'Type': debt['type'],
                'Start Year': debt['start_year'],
                'Original Amount': f"${debt['original_balance']:,}",
                'Monthly Payment': f"${monthly_pmt:,.0f}",
                'Rate': f"{debt['interest_rate']*100:.1f}%",
                'Payoff Year': payoff_year
            })
        
        if all_debts:
            st.dataframe(pd.DataFrame(all_debts), use_container_width=True, hide_index=True)
        
        # Annual debt payments breakdown
        st.subheader("Annual Debt Payments")
        debt_cols = ['Year', 'Housing_Cost', 'Debt_Payments', 'Property_Debt', 'Other_Debt', 'Total_Debt']
        st.dataframe(results[debt_cols].style.format({
            'Housing_Cost': '${:,.0f}',
            'Debt_Payments': '${:,.0f}',
            'Property_Debt': '${:,.0f}',
            'Other_Debt': '${:,.0f}',
            'Total_Debt': '${:,.0f}'
        }), use_container_width=True)
    else:
        st.info("Add properties or debts to see debt payoff projections here.")


def render_withdrawals_tab(results, retirement_year, financial_events):
    """Tab 8: Withdrawal Strategy & Roth Ladder"""
    st.subheader("🔄 Withdrawal Strategy & Roth Ladder")
    
    # Check if there are any financial events
    has_events = len(financial_events) > 0
    has_event_data = results['Event_Roth_Conversion'].sum() > 0 or results['Event_Brokerage_WD'].sum() > 0
    
    if has_events or has_event_data:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_conversions = results['Event_Roth_Conversion'].sum()
        total_withdrawals = (results['Event_Roth_WD'].sum() +
                            results['Event_Brokerage_WD'].sum() +
                            results['Event_Crypto_WD'].sum() +
                            results['Event_401k_WD'].sum())
        total_event_taxes = results['Event_Taxes_Paid'].sum()
        total_penalties = results['Event_Penalties_Paid'].sum()
        
        with col1:
            st.metric("Total Roth Conversions", f"${total_conversions:,.0f}")
        with col2:
            st.metric("Total Withdrawals", f"${total_withdrawals:,.0f}")
        with col3:
            st.metric("Taxes Paid on Events", f"${total_event_taxes:,.0f}")
        with col4:
            st.metric("Penalties Paid", f"${total_penalties:,.0f}", 
                     delta=None if total_penalties == 0 else "Avoid if possible!")
        
        st.markdown("---")
        
        # Roth Ladder Visualization
        st.subheader("📊 Roth Conversion Ladder")
        
        fig = make_subplots(rows=2, cols=2, 
                            subplot_titles=("Roth Conversions by Year", "Seasoned Conversions Available",
                                           "Withdrawal Sources", "Account Balances with Withdrawals"))
        
        # 1. Roth Conversions over time
        fig.add_trace(go.Bar(
            x=results['Year'], y=results['Event_Roth_Conversion'],
            name='Roth Conversion', marker_color='rgba(138, 43, 226, 0.7)'
        ), row=1, col=1)
        
        # 2. Seasoned conversions available (5+ years old)
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Seasoned_Conversions_Avail'],
            name='Seasoned (5yr) Available', fill='tozeroy',
            line=dict(color='green'), fillcolor='rgba(50, 205, 50, 0.3)'
        ), row=1, col=2)
        
        # Add retirement line
        fig.add_vline(x=retirement_year, line_dash="dash", line_color="red", 
                      annotation_text="Retirement", row=1, col=1)
        fig.add_vline(x=retirement_year, line_dash="dash", line_color="red", row=1, col=2)
        
        # 3. Stacked withdrawal sources
        fig.add_trace(go.Bar(
            x=results['Year'], y=results['Event_Roth_WD'],
            name='Roth Withdrawal', marker_color='rgba(138, 43, 226, 0.5)'
        ), row=2, col=1)
        fig.add_trace(go.Bar(
            x=results['Year'], y=results['Event_Brokerage_WD'],
            name='Brokerage', marker_color='rgba(255, 165, 0, 0.7)'
        ), row=2, col=1)
        fig.add_trace(go.Bar(
            x=results['Year'], y=results['Event_Crypto_WD'],
            name='Crypto', marker_color='rgba(255, 215, 0, 0.7)'
        ), row=2, col=1)
        fig.add_trace(go.Bar(
            x=results['Year'], y=results['Event_401k_WD'],
            name='401k Withdrawal', marker_color='rgba(220, 20, 60, 0.7)'
        ), row=2, col=1)
        
        # 4. Account balances
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Trad_Retirement'],
            name='401k/IRA', line=dict(color='green')
        ), row=2, col=2)
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Roth_Balance'],
            name='Roth Total', line=dict(color='purple')
        ), row=2, col=2)
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Roth_Contributions'],
            name='Roth Basis', line=dict(color='purple', dash='dot')
        ), row=2, col=2)
        fig.add_trace(go.Scatter(
            x=results['Year'], y=results['Portfolio'],
            name='Brokerage', line=dict(color='orange')
        ), row=2, col=2)
        
        fig.update_layout(height=600, barmode='stack', showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed event table
        with st.expander("📋 Detailed Event Data by Year"):
            event_cols = ['Year', 'Age', 'Event_Roth_Conversion', 'Event_Roth_WD', 
                         'Event_Brokerage_WD', 'Event_Crypto_WD',
                         'Event_401k_WD', 'Event_Taxes_Paid', 'Event_Penalties_Paid',
                         'Seasoned_Conversions_Avail', 'Cash']
            
            event_df = results[event_cols].copy()
            event_df.columns = ['Year', 'Age', 'Roth Conv.', 'Roth WD',
                               'Brokerage WD', 'Crypto WD', '401k WD', 'Taxes', 'Penalties',
                               'Seasoned Avail', 'Cash']
            
            # Only show years with events
            event_df_filtered = event_df[
                (event_df['Roth Conv.'] > 0) | 
                (event_df['Roth WD'] > 0) |
                (event_df['Brokerage WD'] > 0) |
                (event_df['Crypto WD'] > 0) |
                (event_df['401k WD'] > 0)
            ]
            
            if len(event_df_filtered) > 0:
                st.dataframe(event_df_filtered.style.format({
                    'Roth Conv.': '${:,.0f}',
                    'Roth WD': '${:,.0f}',
                    'Brokerage WD': '${:,.0f}',
                    'Crypto WD': '${:,.0f}',
                    '401k WD': '${:,.0f}',
                    'Taxes': '${:,.0f}',
                    'Penalties': '${:,.0f}',
                    'Seasoned Avail': '${:,.0f}',
                    'Cash': '${:,.0f}'
                }), use_container_width=True)
            else:
                st.info("No events in the selected years.")
        
        # Strategy tips
        st.markdown("---")
        st.subheader("💡 Roth Ladder Strategy Tips")
        
        st.markdown("""
        **The Roth Conversion Ladder works like this:**
        
        1. 🔄 **Convert** money from 401k/Traditional IRA to Roth IRA
        2. 💰 **Pay income tax** on the conversion (ideally at a low bracket in early retirement)
        3. ⏳ **Wait 5 years** - the converted amount "seasons"
        4. ✅ **Withdraw seasoned conversions** tax-free and penalty-free!
        
        **Optimal Strategy:**
        - Start conversions **5 years before** you need the money
        - Convert enough to fill up **low tax brackets** (10%, 12%, 22%)
        - Use **Roth contributions** and **brokerage** to bridge the 5-year gap
        - Avoid 401k early withdrawals (10% penalty + income tax)
        
        **Tax Brackets to Consider (2026 MFJ):**
        - 10%: $0 - $23,850
        - 12%: $23,850 - $96,950
        - 22%: $96,950 - $206,700
        
        Converting to fill the 12% bracket while retired can save significant taxes vs. withdrawing at a higher bracket later!
        """)
        
    else:
        st.info("""
        **No financial events scheduled.**
        
        Add Roth conversions or withdrawals in the **Financial Events** section above to:
        - Plan your Roth conversion ladder
        - Visualize how you'll access your money in early retirement
        - Understand tax implications of different withdrawal strategies
        
        **Common early retirement strategy:**
        1. Retire and live off **brokerage + Roth contributions** 
        2. Do **Roth conversions** each year (pay tax at low bracket)
        3. After 5 years, **withdraw seasoned conversions** tax-free
        4. Repeat until 59.5 when all retirement accounts are accessible
        """)


def render_full_data_tab(results):
    """Tab 9: Full Projection Data"""
    st.subheader("Full Projection Data")
    
    # Format for display
    display_cols = ['Year', 'Age', 'Working', 'Gross_Salary', 'Total_Tax', 'Net_Income', 'Total_Expenses', 
                    'Cash', 'Portfolio', 'Trad_Retirement', 'Roth_Balance', 'HSA_Balance',
                    'Property_Equity', 'Total_Debt', 'Net_Worth', 'Accessible_Liquid', 'FI_Ratio']
    
    formatted = results[display_cols].copy()
    
    st.dataframe(formatted.style.format({
        'Gross_Salary': '${:,.0f}',
        'Total_Tax': '${:,.0f}',
        'Net_Income': '${:,.0f}',
        'Total_Expenses': '${:,.0f}',
        'Cash': '${:,.0f}',
        'Portfolio': '${:,.0f}',
        'Trad_Retirement': '${:,.0f}',
        'Roth_Balance': '${:,.0f}',
        'HSA_Balance': '${:,.0f}',
        'Property_Equity': '${:,.0f}',
        'Total_Debt': '${:,.0f}',
        'Net_Worth': '${:,.0f}',
        'Accessible_Liquid': '${:,.0f}',
        'FI_Ratio': '{:.1%}'
    }), use_container_width=True, height=400)
    
    # Download button
    csv = results.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Data (CSV)",
        data=csv,
        file_name="financial_projection.csv",
        mime="text/csv"
    )
