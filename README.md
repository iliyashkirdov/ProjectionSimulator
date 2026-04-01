# 💰 Financial Projection Simulator

A comprehensive financial planning tool for modeling your path to **Financial Independence / Retire Early (FIRE)**. Built with Streamlit, this interactive simulator helps you visualize and plan your financial future with detailed projections for investments, real estate, taxes, and retirement withdrawals.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### 📊 Comprehensive Financial Modeling
- **Multi-account tracking**: 401(k), Roth IRA, HSA, taxable brokerage, and crypto
- **Real-time tax calculations**: Federal and state taxes with SC-specific brackets, no-income-tax states (TX, FL, WA, etc.), or custom flat rate
- **Itemized vs. standard deduction**: Automatically calculates the better option
- **FICA taxes**: Social Security and Medicare calculations

### 🏠 Real Estate Analysis
- **Primary residence modeling**: Track your home purchase with mortgage, taxes, and equity
- **Rental property analysis**: Full cash flow projections with vacancy, CapEx, and management
- **Deal analyzer tool**: Quick analysis of potential investment properties
- **Key metrics**: Cash-on-cash ROI, cap rate, GRM, 1% rule

### 💼 Retirement Planning
- **Roth Conversion Ladder**: Plan tax-efficient conversions from 401(k) to Roth
- **5-year rule tracking**: Know when your converted funds become accessible
- **Withdrawal planning**: Understand tax implications at different ages
- **Early retirement support**: Navigate the 59½ age rules

### 📈 Investment Growth
- **Portfolio projections**: Model growth with customizable return rates
- **Dividend income**: Track passive income from investments
- **Crypto tracking**: Separate modeling for cryptocurrency holdings
- **Inflation adjustments**: All projections account for inflation

### 💾 Scenario Management
- **Save/Load scenarios**: Store and compare different financial plans
- **Export/Import**: Share scenarios as JSON files
- **Compare strategies**: Save different approaches and compare their outcomes

### 📚 Built-In Education
- **FIRE strategy overview**: Learn about Lean, Fat, Coast, and Barista FIRE
- **Real estate investing guides**: Understand cash flow, cap rates, and key metrics
- **Roth conversion ladder explained**: Step-by-step walkthrough with examples
- **Contextual help**: Every section includes explanations of what the numbers mean

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ProjectionSimulator.git
   cd ProjectionSimulator
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 📖 User Guide

### Setting Up Your Profile

1. **Personal Info**: Enter your birth year and tax filing status in the sidebar
2. **Income**: Set your current salary and expected growth rate
3. **Contributions**: Configure your annual contributions to each account type
4. **Current Assets**: Enter your current account balances
5. **Timeline**: Set your projection start/end years and planned retirement year

> 💡 **New to this?** Click the "📚 Understanding Your Inputs" expander at the top of the sidebar for explanations of what each section means and why it matters.

### Adding Properties

#### Primary Residence
1. Click "➕ Add New Property"
2. Check "This is my primary residence"
3. Enter purchase details (price, down payment, mortgage rate)
4. Your rent expense will automatically stop when you buy

#### Rental Properties
1. Uncheck "This is my primary residence"
2. Fill in all four tabs:
   - **Purchase Details**: Price, ARV, repair costs
   - **Financing**: Down payment, rate, terms
   - **Revenue**: Rent, units, vacancy
   - **Expenses**: Taxes, insurance, CapEx, management

> 💡 **Not sure about real estate?** Each section has a "📚 Learn" expander with guides on real estate investing concepts, key metrics, and common mistakes to avoid.

### Planning Withdrawals & Conversions

The **Financial Events** section lets you plan:
- **Roth Conversions**: Move money from 401(k) to Roth (taxed as income, no penalty)
- **Roth Withdrawals**: Access your Roth contributions tax-free at any age
- **Brokerage Withdrawals**: Sell investments (capital gains tax applies)
- **401(k) Withdrawals**: Early withdrawals include 10% penalty before 59½

> 💡 **Most important section for early retirees!** Open the "📚 Early Retirement Withdrawal Strategies" expander to learn about the Roth Conversion Ladder — the most popular strategy for accessing retirement funds before age 59½.

### Understanding the Results

#### Key Metrics
- **FI Ratio**: Passive income ÷ expenses (100% = financially independent)
- **Net Worth**: Total assets minus debts
- **Accessible Liquid**: Funds you can access without major penalties

#### Charts (9 tabs)
- **Net Worth**: Stacked view of all your assets over time
- **Cash Flow**: Income vs. expenses with annual savings breakdown
- **Retirement**: 401(k), Roth, and HSA growth with availability rules
- **Real Estate**: Property equity building as mortgages are paid down
- **Taxes**: Federal, state, FICA breakdown and how pre-tax contributions save you money
- **FI Progress**: Track when passive income will exceed your expenses
- **Debt Payoff**: Visualize how debts shrink over time
- **Withdrawals**: Roth conversion ladder and withdrawal strategy visualization
- **Full Data**: Complete projection data with CSV download

## 🧪 Running Tests

The project includes tests for the financial calculation engine:

```bash
python scripts/run_fire_tests.py
```

## 📁 Project Structure

```
ProjectionSimulator/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── scripts/
│   └── run_fire_tests.py    # Test suite for calculations
├── saved_scenarios/         # Your saved scenario files (git-ignored)
└── data/                    # Data files (git-ignored)
```

## ⚙️ Configuration

### Tax Brackets

The simulator uses 2026 IRS-projected tax brackets. To update:
1. Find `calculate_federal_tax()` in `app.py`
2. Update the `brackets` dictionary with new thresholds and rates

### State Taxes

Currently supports:
- **South Carolina**: Full bracket calculations with 2026 rates
- **No Income Tax states**: TX, FL, WA, NV, WY, SD, AK, NH, TN (0% state tax)
- **Other states**: Flat rate configuration

To add a new state, modify the `calculate_sc_state_tax()` function or add a new state-specific function.

## 🔒 Privacy & Security

**Your data stays local.** This application:
- Runs entirely on your local machine
- Stores scenarios as JSON files in your `saved_scenarios/` folder
- Never sends data to external servers
- Has no analytics or tracking

**Important**: The `.gitignore` file is configured to exclude personal data files. If you fork this repo, ensure you don't commit files containing your financial information.

## 🤝 Contributing

Contributions are welcome! Here's how to help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/AmazingFeature`
3. **Commit your changes**: `git commit -m 'Add AmazingFeature'`
4. **Push to the branch**: `git push origin feature/AmazingFeature`
5. **Open a Pull Request**

### Ideas for Contributions
- Monte Carlo simulations for market volatility modeling
- Additional state tax calculations (full bracket support)
- Social Security benefit projections
- Required Minimum Distribution (RMD) calculations
- Roth conversion optimization algorithms
- Historical backtesting with real market data
- Additional investment account types (529, taxable bonds)
- Improved mobile responsiveness

## 🗺️ Roadmap

We want this tool to be the most comprehensive **free, open-source** financial projection simulator available. Here's where we're headed:

### Phase 1: Core Enhancements *(Current Focus)*
- [x] Multi-account tracking (401k, Roth, HSA, brokerage, crypto)
- [x] Federal and state tax calculations with real brackets
- [x] Real estate modeling (primary + rental properties)
- [x] Roth conversion ladder planning with 5-year rule
- [x] Financial events system (withdrawals + conversions)
- [x] Built-in educational guides for each section
- [ ] Roth conversion optimizer (auto-suggest optimal annual conversion amounts to fill low tax brackets)
- [ ] Social Security benefit estimation based on work history

### Phase 2: Advanced Projections
- [ ] **Monte Carlo simulations** — Run thousands of projections with randomized market returns to see the probability of success, not just one "average" line
- [ ] **Historical backtesting** — Test your plan against every historical period (e.g., "What if I retired in 2000? 2007? 1929?")
- [ ] **Variable return modeling** — Different returns for different time periods (e.g., lower returns near retirement for sequence-of-returns risk)
- [ ] **Required Minimum Distributions (RMDs)** — Auto-calculate mandatory 401k/IRA withdrawals starting at age 73+

### Phase 3: Expanded Features
- [ ] Additional state tax calculators with full bracket support
- [ ] More account types (529 college savings, taxable bonds, I-Bonds)
- [ ] Health insurance cost modeling (ACA marketplace subsidies in early retirement)
- [ ] Pension and annuity income modeling
- [ ] Side income / gig work modeling for semi-retirement (Barista FIRE)
- [ ] Estate planning basics (inheritance modeling)

### Phase 4: Experience & Sharing
- [ ] Improved mobile responsiveness
- [ ] Pre-built scenario templates (Lean FIRE, Fat FIRE, Coast FIRE, Real Estate FIRE)
- [ ] Scenario comparison dashboard (side-by-side results)
- [ ] Progress tracker (log real data over time and compare actual vs. projected)
- [ ] Community-shared scenarios (anonymized, opt-in)

**Want to help?** Pick any unchecked item and submit a PR! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for **educational and planning purposes only**. It is not financial advice. The projections are based on assumptions that may not reflect actual market conditions, tax law changes, or your specific situation.

**Always consult with a qualified financial advisor and tax professional** before making financial decisions.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Charts powered by [Plotly](https://plotly.com/)
- Financial calculations using [NumPy Financial](https://numpy.org/numpy-financial/)

---

Made with ❤️ for the FIRE community
