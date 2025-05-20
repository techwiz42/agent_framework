# AccountingAgent Usage Examples

This document provides examples of how to use the AccountingAgent in various accounting and financial analysis scenarios.

## Basic Agent Setup

```python
from accounting_agent import AccountingAgent

# Create a default accounting agent
agent = AccountingAgent()

# Create an accounting agent with custom settings
custom_agent = AccountingAgent(
    name="Financial Analysis Agent",
    model="gpt-4-turbo",
    tool_choice="auto",
    parallel_tool_calls=True
)

# Get agent capabilities description
print(agent.description)
```

## Example 1: Financial Statement Analysis

Analyze financial statements to derive insights about a company's financial health.

```python
# Sample financial data
balance_sheet = {
    "cash_and_equivalents": 250000,
    "accounts_receivable": 180000,
    "inventory": 320000,
    "total_current_assets": 750000,
    "property_plant_equipment": 1200000,
    "accumulated_depreciation": -450000,
    "total_non_current_assets": 750000,
    "total_assets": 1500000,
    
    "accounts_payable": 120000,
    "short_term_debt": 80000,
    "accrued_expenses": 50000,
    "total_current_liabilities": 250000,
    "long_term_debt": 450000,
    "total_non_current_liabilities": 450000,
    "total_liabilities": 700000,
    
    "common_stock": 500000,
    "retained_earnings": 300000,
    "total_equity": 800000
}

income_statement = {
    "revenue": 2500000,
    "cost_of_goods_sold": 1500000,
    "gross_profit": 1000000,
    "operating_expenses": 750000,
    "operating_income": 250000,
    "interest_expense": 40000,
    "income_before_tax": 210000,
    "income_tax": 63000,
    "net_income": 147000
}

cash_flow_statement = {
    "net_income": 147000,
    "depreciation": 120000,
    "changes_in_working_capital": -50000,
    "cash_from_operations": 217000,
    "capital_expenditures": -180000,
    "cash_from_investing": -180000,
    "debt_repayments": -50000,
    "dividends_paid": -40000,
    "cash_from_financing": -90000,
    "net_change_in_cash": -53000
}

# Run the financial statement analysis
analysis_result = agent.analyze_financial_statements(
    analysis_type="comprehensive",
    balance_sheet=balance_sheet,
    income_statement=income_statement,
    cash_flow_statement=cash_flow_statement,
    specific_concerns=["liquidity", "debt sustainability"]
)

# Access the analysis results
print("Analysis Summary:", analysis_result["analysis_summary"])
print("Key Observations:", analysis_result["key_observations"])
print("Specific Concerns Addressed:", analysis_result["addressing_concerns"])
```

## Example 2: Calculate and Interpret Financial Ratios

Calculate key financial ratios and get professional interpretations.

```python
# Calculate financial ratios
ratio_results = agent.calculate_financial_ratios(
    balance_sheet=balance_sheet,
    income_statement=income_statement,
    ratio_categories=["liquidity", "profitability", "solvency"]
)

# Access ratio results
liquidity_ratios = ratio_results["ratios_by_category"]["liquidity"]
profitability_ratios = ratio_results["ratios_by_category"]["profitability"]

# Print some key ratios
print(f"Current Ratio: {liquidity_ratios['current_ratio']['value']}")
print(f"Interpretation: {liquidity_ratios['current_ratio']['interpretation']}")

print(f"Return on Equity: {profitability_ratios['return_on_equity']['value']}%")
print(f"Interpretation: {profitability_ratios['return_on_equity']['interpretation']}")
```

## Example 3: Accounting Treatment Advice

Get expert guidance on how to account for complex transactions.

```python
# Get accounting treatment advice
treatment_advice = agent.advise_on_accounting_treatment(
    transaction_description="Acquisition of delivery vehicles through 5-year finance lease",
    amount=250000.00,
    accounting_framework="IFRS",
    industry="Retail",
    entity_type="for-profit"
)

# Access the advice
print("Recommended Treatment:", treatment_advice["recommended_treatment"])
print("Journal Entries:")
for entry in treatment_advice["journal_entries"]:
    account = entry["account"]
    debit = entry.get("debit") or 0
    credit = entry.get("credit") or 0
    print(f"{account}: Debit ${debit:,.2f}, Credit ${credit:,.2f}")

print("Accounting Standards:", treatment_advice["accounting_standards"])
print("Disclosure Requirements:", treatment_advice["disclosure_requirements"])
```

## Example 4: Prepare Journal Entries

Generate proper journal entries for various types of transactions.

```python
# Prepare a journal entry for a sale transaction
sales_entry = agent.prepare_journal_entries(
    transaction_type="sale",
    transaction_details={
        "amount": 5000.00,
        "description": "Sale of merchandise to ABC Company",
        "accounts": {
            "debit_accounts": [{"account": "Accounts Receivable", "amount": 5000.00}],
            "credit_accounts": [
                {"account": "Sales Revenue", "amount": 4545.45},
                {"account": "Sales Tax Payable", "amount": 454.55}
            ]
        }
    },
    accounting_method="accrual",
    date="2024-03-15",
    currency="USD"
)

# Verify the entry is balanced
if sales_entry["balanced"]:
    print("Journal entry is correctly balanced.")
else:
    print("Warning:", sales_entry["warning"])

# Print the journal entry
print("\nJournal Entry:")
print(f"Date: {sales_entry['transaction_info']['date']}")
print(f"Description: {sales_entry['transaction_info']['description']}")
print("\nDebits:")
for entry in sales_entry["journal_entries"]["debits"]:
    print(f"  {entry['account']}: ${entry['amount']:,.2f}")
print("\nCredits:")
for entry in sales_entry["journal_entries"]["credits"]:
    print(f"  {entry['account']}: ${entry['amount']:,.2f}")
```

## Example 5: Tax Implications Analysis

Analyze the tax implications of business transactions.

```python
# Analyze tax implications of a property sale
tax_analysis = agent.calculate_tax_implications(
    transaction_details={
        "type": "property_sale",
        "asset_description": "Commercial property",
        "acquisition_cost": 800000,
        "selling_price": 1200000,
        "holding_period": "6 years",
        "depreciation_claimed": 240000
    },
    tax_jurisdiction="United States",
    entity_type="corporation",
    tax_year="2024",
    specific_tax_concerns=["capital gains", "depreciation recapture"]
)

# Access the tax analysis
print("Tax Classification:", tax_analysis["tax_classification"])
print("Tax Calculations:", tax_analysis["tax_calculations"])
print("Specific Tax Concerns Addressed:")
for concern, analysis in tax_analysis["specific_tax_concerns_addressed"].items():
    print(f"  {concern}: {analysis}")
```

## Example 6: Using the Calculator Tool Directly

The accounting agent has access to a powerful calculator tool that can be used for complex financial calculations.

```python
# Access the agent's calculator tool
calculator_tool = next(tool for tool in agent.tools if tool.name == "calculate")

# Use the calculator tool for a financial calculation
compound_interest_result = calculator_tool.function(
    context=None,
    operation_type="financial",
    operation="compound_interest",
    values=[],
    expression="",
    principal=10000,
    rate=0.05,
    time=5,
    compounding_periods=12
)

# Access and print the result
print(f"Future Value: ${compound_interest_result['final_amount']:,.2f}")
print(f"Interest Earned: ${compound_interest_result['interest_earned']:,.2f}")

# Use the interpreter tool to get a human-friendly explanation
interpreter_tool = next(tool for tool in agent.tools if tool.name == "interpret_calculation_results")
interpretation = interpreter_tool.function(
    context=None,
    calculation_results=compound_interest_result,
    interpretation_level="detailed"
)

print("\nInterpretation:")
print(interpretation["interpretation"]["summary"])
for finding in interpretation["interpretation"]["key_findings"]:
    print(f"- {finding}")
```

## Example 7: Develop Financial Controls

Create a customized financial controls framework for an organization.

```python
# Develop financial controls
controls_framework = agent.develop_financial_controls(
    process_areas=["accounts_payable", "accounts_receivable", "payroll", "inventory"],
    entity_size="medium",
    risk_level="high",
    compliance_requirements=["SOX", "GDPR"]
)

# Access the controls framework
print("Financial Controls Overview:", controls_framework["overview"])

# Print controls for one process area
process = "accounts_payable"
print(f"\nControls for {process}:")
print("Key Risks:")
for risk in controls_framework["process_controls"][process]["key_risks"]:
    print(f"- {risk}")
print("\nControl Activities:")
for activity in controls_framework["process_controls"][process]["control_activities"]:
    print(f"- {activity}")

# Print compliance mapping for SOX
print("\nSOX Compliance Mapping:")
for process, mapping in controls_framework["compliance_mapping"]["SOX"].items():
    print(f"- {process}: {mapping}")
```

## Important Notes

1. **Parameter Flexibility**: All functions accept optional parameters, allowing for flexibility in usage.

2. **Default Values**: All functions have sensible defaults, but provide more detailed analysis when more information is provided.

3. **Calculation Integration**: For accurate financial calculations, the agent uses the calculator tool internally.

4. **Schema Validation**: The agent has been designed to pass OpenAI's schema validation requirements, ensuring all parameters are optional with proper type hints.

5. **Error Handling**: The agent includes robust error handling to address missing or invalid inputs.
