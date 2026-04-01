# Contributing to Financial Projection Simulator

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## Getting Started

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ProjectionSimulator.git
   cd ProjectionSimulator
   ```

3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the app locally:
   ```bash
   streamlit run app.py
   ```

## How to Contribute

### Reporting Bugs

- Use GitHub Issues to report bugs
- Include steps to reproduce the issue
- Include expected vs actual behavior
- Include screenshots if applicable
- Include your Python version and OS

### Suggesting Features

- Use GitHub Issues with the "enhancement" label
- Describe the feature and its use case
- Explain why it would benefit users

### Submitting Code

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines below

3. Test your changes:
   ```bash
   python scripts/run_fire_tests.py
   ```

4. Commit with a clear message:
   ```bash
   git commit -m "Add feature: description of what it does"
   ```

5. Push and create a Pull Request

## Code Style Guidelines

### Python

- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and modular

### Streamlit Components

- Group related UI elements in expanders or columns
- Use consistent emoji icons for headers
- Add help text for complex inputs
- Test on both desktop and mobile viewports

### Financial Calculations

- Document assumptions and formulas in comments
- Include unit tests for new calculations
- Use numpy-financial for standard financial functions
- Handle edge cases (zero values, negative numbers)

## Areas for Contribution

### High Priority
- Additional state tax calculations
- Social Security benefit projections
- Required Minimum Distribution (RMD) calculations
- Improved mobile responsiveness

### Nice to Have
- Dark mode support
- Export to Excel/PDF
- Multi-currency support
- Integration with financial APIs

## Testing

### Running Tests
```bash
python scripts/run_fire_tests.py
```

### Writing Tests

Add new tests to `scripts/run_fire_tests.py`:

```python
def test_your_new_feature():
    assumptions = {
        # minimal assumptions needed
    }
    events = []
    df = run_projection(assumptions, [], [], financial_events=events)
    
    # Assert expected behavior
    assert condition, "Error message"
    print('test_your_new_feature: PASS')
```

## Privacy Considerations

**Important**: This tool handles sensitive financial data.

- Never commit personal financial data
- Use generic example values in tests and samples
- Ensure `.gitignore` covers sensitive files
- Don't add analytics or external API calls without discussion

## Questions?

Open an issue with the "question" label or start a discussion.

Thank you for contributing! 🎉
