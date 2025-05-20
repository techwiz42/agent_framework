import unittest
from unittest.mock import patch, MagicMock, Mock
import json
import logging

# Import the agent class
from app.services.agents.accounting_agent import AccountingAgent

class TestAccountingAgent(unittest.TestCase):
    """Test suite for the AccountingAgent class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Disable logging during tests
        logging.disable(logging.CRITICAL)
        
        # Create a mock run context wrapper
        self.mock_context = MagicMock()
        
        # Create a test instance of the agent
        self.agent = AccountingAgent(
            name="Test Accounting Agent",
            model="test-model",
            tool_choice="auto"
        )
    
    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Re-enable logging
        logging.disable(logging.NOTSET)
    
    def test_agent_initialization(self):
        """Test that the agent initializes with the correct attributes."""
        self.assertEqual(self.agent.name, "Test Accounting Agent")
        self.assertEqual(self.agent.description, "Expert in financial architectures, economic forensics, GAAP principles, and accounting standards, providing insights on financial reporting and compliance")
        
        # Check that the agent has the expected tools
        tool_names = [tool.name for tool in self.agent.tools]
        expected_tools = [
            "calculate",
            "interpret_calculation_results",
            "analyze_financial_statements",
            "advise_on_accounting_treatment",
            "develop_financial_controls",
            "calculate_tax_implications",
            "calculate_financial_ratios",
            "prepare_journal_entries"
        ]
        
        for tool in expected_tools:
            self.assertIn(tool, tool_names, f"Tool {tool} not found in agent tools")
        
        # Check that instructions include accounting-specific guidance
        self.assertIn("GAAP and IFRS Principles", self.agent.instructions)
        self.assertIn("CALCULATION CAPABILITIES", self.agent.instructions)
    
    def test_analyze_financial_statements(self):
        """Test the analyze_financial_statements method."""
        # Create test data
        balance_sheet = {
            "total_assets": 100000,
            "current_assets": 40000,
            "non_current_assets": 60000,
            "total_liabilities": 60000,
            "current_liabilities": 30000,
            "non_current_liabilities": 30000,
            "equity": 40000
        }
        
        income_statement = {
            "revenue": 200000,
            "cost_of_goods_sold": 120000,
            "gross_profit": 80000,
            "operating_expenses": 50000,
            "operating_income": 30000,
            "net_income": 24000
        }
        
        # Test with minimal parameters
        result = self.agent.analyze_financial_statements()
        self.assertIn("analysis_summary", result)
        self.assertIn("financial_ratios", result)
        
        # Test with full parameters
        result = self.agent.analyze_financial_statements(
            context=self.mock_context,
            analysis_type="profitability",
            balance_sheet=balance_sheet,
            income_statement=income_statement,
            cash_flow_statement={},
            benchmarks={"industry_avg_roe": 15.0},
            specific_concerns=["cash flow", "debt levels"]
        )
        
        self.assertIn("analysis_summary", result)
        self.assertIn("profitability", result["analysis_summary"].lower())
        self.assertIn("addressing_concerns", result)
        self.assertIn("cash flow", result["addressing_concerns"])
        self.assertIn("debt levels", result["addressing_concerns"])
    
    def test_advise_on_accounting_treatment(self):
        """Test the advise_on_accounting_treatment method."""
        # Test with minimal parameters
        result = self.agent.advise_on_accounting_treatment()
        self.assertIn("transaction_summary", result)
        self.assertIn("journal_entries", result)
        
        # Test with full parameters
        result = self.agent.advise_on_accounting_treatment(
            context=self.mock_context,
            transaction_description="Purchase of manufacturing equipment",
            amount=50000.00,
            accounting_framework="IFRS",
            industry="Manufacturing",
            entity_type="corporation"
        )
        
        self.assertIn("transaction_summary", result)
        self.assertIn("Purchase of manufacturing equipment", result["transaction_summary"])
        self.assertIn("$50,000.00", result["transaction_summary"])
        self.assertIn("IFRS", result["recommended_treatment"])
        self.assertIn("industry_specific_considerations", result)
        self.assertIn("Manufacturing", result["industry_specific_considerations"])
        self.assertIn("entity_specific_considerations", result)
        self.assertIn("corporation", result["entity_specific_considerations"])
    
    def test_develop_financial_controls(self):
        """Test the develop_financial_controls method."""
        # Test with minimal parameters
        result = self.agent.develop_financial_controls()
        self.assertIn("overview", result)
        self.assertIn("process_controls", result)
        
        # Check that default process areas are included
        for area in ["accounts payable", "receivables", "payroll"]:
            self.assertIn(area, result["process_controls"])
        
        # Test with full parameters
        result = self.agent.develop_financial_controls(
            context=self.mock_context,
            process_areas=["cash management", "inventory", "fixed assets"],
            entity_size="large",
            risk_level="high",
            compliance_requirements=["SOX", "GDPR"]
        )
        
        self.assertIn("overview", result)
        self.assertIn("large", result["overview"])
        self.assertIn("high", result["overview"])
        
        # Check that specified process areas are included
        for area in ["cash management", "inventory", "fixed assets"]:
            self.assertIn(area, result["process_controls"])
        
        # Check that compliance requirements are included
        self.assertIn("compliance_mapping", result)
        self.assertIn("SOX", result["compliance_mapping"])
        self.assertIn("GDPR", result["compliance_mapping"])
    
    def test_calculate_tax_implications(self):
        """Test the calculate_tax_implications method."""
        # Test with minimal parameters
        result = self.agent.calculate_tax_implications()
        self.assertIn("transaction_summary", result)
        self.assertIn("tax_calculations", result)
        
        # Test with full parameters
        result = self.agent.calculate_tax_implications(
            context=self.mock_context,
            transaction_details={"type": "asset_sale", "amount": 100000},
            tax_jurisdiction="California",
            entity_type="partnership",
            tax_year="2025",
            specific_tax_concerns=["capital gains", "depreciation recapture"]
        )
        
        self.assertIn("transaction_summary", result)
        self.assertIn("tax_classification", result)
        self.assertIn("partnership", result["tax_classification"])
        self.assertIn("California", result["tax_classification"])
        
        # Check that specific tax concerns are addressed
        self.assertIn("specific_tax_concerns_addressed", result)
        self.assertIn("capital gains", result["specific_tax_concerns_addressed"])
        self.assertIn("depreciation recapture", result["specific_tax_concerns_addressed"])
    
    def test_calculate_financial_ratios(self):
        """Test the calculate_financial_ratios method."""
        # Create test financial data
        balance_sheet = {
            "current_assets": 100000,
            "total_assets": 500000,
            "current_liabilities": 70000,
            "total_liabilities": 300000,
            "equity": 200000
        }
        
        income_statement = {
            "revenue": 800000,
            "cost_of_goods_sold": 500000,
            "gross_profit": 300000,
            "operating_income": 100000,
            "net_income": 80000
        }
        
        # Test with minimal parameters
        result = self.agent.calculate_financial_ratios()
        self.assertIn("summary", result)
        self.assertIn("ratios_by_category", result)
        
        # Test with full parameters
        result = self.agent.calculate_financial_ratios(
            context=self.mock_context,
            balance_sheet=balance_sheet,
            income_statement=income_statement,
            cash_flow_statement={"operating_cash_flow": 90000},
            ratio_categories=["liquidity", "profitability"],
            prior_period_data={"ratios_by_category": {"liquidity": {"current_ratio": {"value": 1.4}}}}
        )
        
        self.assertIn("summary", result)
        self.assertIn("ratios_by_category", result)
        
        # Check that only the requested ratio categories are included
        self.assertIn("liquidity", result["ratios_by_category"])
        self.assertIn("profitability", result["ratios_by_category"])
        self.assertNotIn("solvency", result["ratios_by_category"])
        
        # Check that trend analysis is included (since prior period data was provided)
        self.assertIn("trend_analysis", result)
    
    def test_prepare_journal_entries(self):
        """Test the prepare_journal_entries method."""
        # Test with minimal parameters
        result = self.agent.prepare_journal_entries()
        self.assertIn("transaction_info", result)
        self.assertIn("journal_entries", result)
        self.assertIn("balanced", result)
        
        # Verify that default journal entry is balanced
        self.assertTrue(result["balanced"])
        
        # Test with full parameters - sales transaction
        result = self.agent.prepare_journal_entries(
            context=self.mock_context,
            transaction_type="sale",
            transaction_details={
                "amount": 1100.00,
                "description": "Sale of merchandise",
                "accounts": {
                    "debit_accounts": [{"account": "Accounts Receivable", "amount": 1100.00}],
                    "credit_accounts": [
                        {"account": "Sales Revenue", "amount": 1000.00},
                        {"account": "Sales Tax Payable", "amount": 100.00}
                    ]
                }
            },
            accounting_method="accrual",
            date="2024-03-20",
            currency="USD"
        )
        
        self.assertIn("transaction_info", result)
        self.assertEqual(result["transaction_info"]["type"], "sale")
        self.assertEqual(result["transaction_info"]["description"], "Sale of merchandise")
        
        # Check debits and credits
        debits = result["journal_entries"]["debits"]
        credits = result["journal_entries"]["credits"]
        
        self.assertEqual(len(debits), 1)
        self.assertEqual(debits[0]["account"], "Accounts Receivable")
        self.assertEqual(debits[0]["amount"], 1100.00)
        
        self.assertEqual(len(credits), 2)
        self.assertEqual(credits[0]["account"], "Sales Revenue")
        self.assertEqual(credits[0]["amount"], 1000.00)
        self.assertEqual(credits[1]["account"], "Sales Tax Payable")
        self.assertEqual(credits[1]["amount"], 100.00)
        
        # Verify that custom journal entry is balanced
        self.assertTrue(result["balanced"])
        
        # Test with unbalanced journal entry
        result = self.agent.prepare_journal_entries(
            transaction_type="adjustment",
            transaction_details={
                "amount": 1000.00,
                "description": "Adjustment entry",
                "accounts": {
                    "debit_accounts": [{"account": "Expense", "amount": 1000.00}],
                    "credit_accounts": [{"account": "Liability", "amount": 950.00}]
                }
            }
        )
        
        # Verify that unbalanced entry is detected
        self.assertFalse(result["balanced"])
        self.assertIn("warning", result)
        self.assertIn("not balanced", result["warning"])


class TestAccountingAgentIntegration(unittest.TestCase):
    """Integration tests for the AccountingAgent with the calculator tool."""
    
    @patch('app.core.common_calculator.CalculatorUtility')
    def test_integration_with_calculator(self, mock_calculator):
        """Test integration with the calculator utility via tools."""
        # Mock the calculator utility methods
        mock_calculator.basic_arithmetic.return_value = {"result": 1500}
        mock_calculator.financial_calculations.return_value = {
            "final_amount": 10750,
            "interest_earned": 750
        }
        
        # Create a new agent instance with mocked tools
        with patch('app.services.agents.agent_calculator_tool.get_calculator_tool') as mock_calc_tool, \
             patch('app.services.agents.agent_calculator_tool.get_interpreter_tool') as mock_interp_tool:
            
            # Create mock function tools
            mock_calc_tool.return_value = MagicMock()
            mock_interp_tool.return_value = MagicMock()
            
            # Initialize agent
            agent = AccountingAgent()
            
            # Verify the calculator tool is included in the agent's tools
            self.assertTrue(any(tool.name == "calculate" for tool in agent.tools))
            self.assertTrue(any(tool.name == "interpret_calculation_results" for tool in agent.tools))


if __name__ == '__main__':
    unittest.main()
