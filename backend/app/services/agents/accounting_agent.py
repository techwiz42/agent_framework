from typing import Dict, Any, Optional, List, Union, Tuple
import logging
import pandas as pd
import datetime
from decimal import Decimal, ROUND_HALF_UP
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from app.core.common_calculator import CalculatorUtility

# Import calculator tools
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool

logger = logging.getLogger(__name__)

class AccountingAgent(BaseAgent):
    """
    AccountingAgent is a specialized agent that provides expertise in accounting, 
    financial reporting, and economic analysis.
    
    This agent specializes in financial architectures, economic forensics, and GAAP principles.
    """

    def __init__(
        self,
        name: str = "Accounting Expert",
        model: str = settings.DEFAULT_AGENT_MODEL,
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        **kwargs
    ):
        """
        Initialize an AccountingAgent with specialized accounting instructions.
        
        Args:
            name: The name of the agent. Defaults to "Accounting Expert".
            model: The model to use for this agent.
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            **kwargs: Additional arguments to pass to the BaseAgent constructor.
        """
        # Define the accounting expert instructions
        accounting_instructions = """Wherever possible, you must use tools to respond. Do not guess. If a tool is available, always call the tool to perform the action.
You are an accounting expert agent specializing in financial reporting, accounting principles, auditing, and financial analysis. Your role is to:

1. PROVIDE ACCOUNTING EXPERTISE IN
- Financial Reporting
- GAAP and IFRS Principles
- Financial Statement Analysis
- Audit Procedures and Compliance
- Cost Accounting and Analysis
- Management Accounting
- Bookkeeping Best Practices
- Financial Controls
- Regulatory Compliance
- Fraud Detection and Prevention
- Accounting Technology and Systems

2. ANALYTICAL APPROACH
- Use systematic analysis methods
- Apply accounting principles and standards
- Consider internal control implications
- Evaluate financial accuracy and transparency
- Assess regulatory compliance
- Consider multiple accounting treatments
- Apply professional skepticism
- Ensure mathematical accuracy in all calculations

3. PRACTICAL FOCUS
- Provide actionable guidance
- Consider implementation complexity
- Address practical record-keeping issues
- Include audit trail considerations
- Focus on documentation requirements
- Include verification methods
- Address timing and cut-off issues
- Consider automation possibilities

4. CONTEXT AWARENESS
- Consider business entity structure
- Account for industry-specific regulations
- Build on previous financial periods
- Maintain accounting consistency
- Reference relevant disclosures
- Consider stakeholder implications

5. RESPONSE STRUCTURE
- Begin with key accounting principles
- Provide detailed technical analysis
- Include documentation requirements
- Note important considerations
- Highlight risk areas
- Suggest verification methods
- Include regulatory citations
- Reference relevant standards

6. CALCULATION CAPABILITIES
- Use the calculator tool for all financial calculations
- Interpret calculation results in context
- Verify mathematical accuracy
- Apply formulas correctly
- Provide step-by-step calculation breakdowns
- Show working for complex calculations

Always maintain professional objectivity and emphasize accuracy, compliance, and transparency in financial reporting."""

        # Get the calculator tools - already properly patched from the utility functions
        calculator_tool = get_calculator_tool()
        interpreter_tool = get_interpreter_tool()

        # Define the tools - use the already patched instances
        tools = [
            calculator_tool,
            interpreter_tool,
            function_tool(self.analyze_financial_statements),
            function_tool(self.advise_on_accounting_treatment),
            function_tool(self.develop_financial_controls),
            function_tool(self.calculate_financial_ratios),
            function_tool(self.prepare_journal_entries)
        ]
        
        # Initialize the Agent class directly
        super().__init__(
            name=name,
            model=model,
            instructions=accounting_instructions,
            functions=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            max_tokens=2048,
            **kwargs
        )


    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the AccountingAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for AccountingAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Expert in financial architectures, economic forensics, GAAP principles, and accounting standards, providing insights on financial reporting and compliance"

    def _calculate_liquidity_ratios(self, balance_sheet: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate liquidity ratios based on balance sheet data.
        
        Args:
            balance_sheet: Dictionary containing balance sheet accounts and values.
            
        Returns:
            Dictionary of liquidity ratios with values, formulas, and interpretations.
        """
        ratios = {}
        
        # Extract required values with safe defaults
        current_assets = balance_sheet.get("current_assets", 0)
        current_liabilities = balance_sheet.get("current_liabilities", 0)
        inventory = balance_sheet.get("inventory", 0)
        cash_equivalents = balance_sheet.get("cash_and_cash_equivalents", 0)
        
        # Avoid division by zero
        if current_liabilities <= 0:
            return {
                "current_ratio": {
                    "value": None,
                    "formula": "Current Assets / Current Liabilities",
                    "interpretation": "Cannot calculate due to zero or negative current liabilities."
                },
                "quick_ratio": {
                    "value": None,
                    "formula": "(Current Assets - Inventory) / Current Liabilities",
                    "interpretation": "Cannot calculate due to zero or negative current liabilities."
                },
                "cash_ratio": {
                    "value": None,
                    "formula": "Cash and Cash Equivalents / Current Liabilities",
                    "interpretation": "Cannot calculate due to zero or negative current liabilities."
                }
            }
        
        # Calculate current ratio
        current_ratio = round(current_assets / current_liabilities, 2)
        ratios["current_ratio"] = {
            "value": current_ratio,
            "formula": "Current Assets / Current Liabilities",
            "interpretation": f"The company has ${current_ratio:.2f} in current assets for every $1 in current liabilities."
        }
        
        # Calculate quick ratio
        quick_assets = current_assets - inventory
        quick_ratio = round(quick_assets / current_liabilities, 2)
        ratios["quick_ratio"] = {
            "value": quick_ratio,
            "formula": "(Current Assets - Inventory) / Current Liabilities",
            "interpretation": f"The company has ${quick_ratio:.2f} in quick assets for every $1 in current liabilities."
        }
        
        # Calculate cash ratio
        cash_ratio = round(cash_equivalents / current_liabilities, 2)
        ratios["cash_ratio"] = {
            "value": cash_ratio,
            "formula": "Cash and Cash Equivalents / Current Liabilities",
            "interpretation": f"The company has ${cash_ratio:.2f} in cash and equivalents for every $1 in current liabilities."
        }
        
        return ratios
        
    def _calculate_profitability_ratios(
        self, 
        income_statement: Dict[str, Any],
        balance_sheet: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate profitability ratios based on income statement and balance sheet data.
        
        Args:
            income_statement: Dictionary containing income statement accounts and values.
            balance_sheet: Dictionary containing balance sheet accounts and values.
            
        Returns:
            Dictionary of profitability ratios with values, formulas, and interpretations.
        """
        ratios = {}
        
        # Extract required values with safe defaults
        revenue = income_statement.get("revenue", 0)
        gross_profit = income_statement.get("gross_profit", 0)
        operating_income = income_statement.get("operating_income", 0)
        net_income = income_statement.get("net_income", 0)
        total_assets = balance_sheet.get("total_assets", 0)
        shareholders_equity = balance_sheet.get("shareholders_equity", 0)
        
        # Gross margin
        if revenue > 0:
            gross_margin_pct = round((gross_profit / revenue) * 100, 2)
            ratios["gross_margin"] = {
                "value": gross_margin_pct,
                "formula": "Gross Profit / Revenue * 100",
                "interpretation": f"The company generates a {gross_margin_pct:.2f}% gross margin on sales."
            }
        else:
            ratios["gross_margin"] = {
                "value": None,
                "formula": "Gross Profit / Revenue * 100",
                "interpretation": "Cannot calculate due to zero or negative revenue."
            }
        
        # Operating margin
        if revenue > 0:
            operating_margin_pct = round((operating_income / revenue) * 100, 2)
            ratios["operating_margin"] = {
                "value": operating_margin_pct,
                "formula": "Operating Income / Revenue * 100",
                "interpretation": f"The company generates a {operating_margin_pct:.2f}% operating margin on sales."
            }
        else:
            ratios["operating_margin"] = {
                "value": None,
                "formula": "Operating Income / Revenue * 100",
                "interpretation": "Cannot calculate due to zero or negative revenue."
            }
        
        # Net profit margin
        if revenue > 0:
            net_profit_margin_pct = round((net_income / revenue) * 100, 2)
            ratios["net_profit_margin"] = {
                "value": net_profit_margin_pct,
                "formula": "Net Income / Revenue * 100",
                "interpretation": f"The company generates a {net_profit_margin_pct:.2f}% net profit margin on sales."
            }
        else:
            ratios["net_profit_margin"] = {
                "value": None,
                "formula": "Net Income / Revenue * 100",
                "interpretation": "Cannot calculate due to zero or negative revenue."
            }
        
        # Return on assets (ROA)
        if total_assets > 0:
            roa_pct = round((net_income / total_assets) * 100, 2)
            ratios["return_on_assets"] = {
                "value": roa_pct,
                "formula": "Net Income / Total Assets * 100",
                "interpretation": f"The company generates a {roa_pct:.2f}% return on its assets."
            }
        else:
            ratios["return_on_assets"] = {
                "value": None,
                "formula": "Net Income / Total Assets * 100",
                "interpretation": "Cannot calculate due to zero or negative total assets."
            }
        
        # Return on equity (ROE)
        if shareholders_equity > 0:
            roe_pct = round((net_income / shareholders_equity) * 100, 2)
            ratios["return_on_equity"] = {
                "value": roe_pct,
                "formula": "Net Income / Shareholders' Equity * 100",
                "interpretation": f"The company generates a {roe_pct:.2f}% return on equity."
            }
        else:
            ratios["return_on_equity"] = {
                "value": None,
                "formula": "Net Income / Shareholders' Equity * 100",
                "interpretation": "Cannot calculate due to zero or negative shareholders' equity."
            }
        
        return ratios
        
    def _calculate_solvency_ratios(
        self, 
        balance_sheet: Dict[str, Any],
        income_statement: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate solvency ratios based on balance sheet and income statement data.
        
        Args:
            balance_sheet: Dictionary containing balance sheet accounts and values.
            income_statement: Dictionary containing income statement accounts and values.
            
        Returns:
            Dictionary of solvency ratios with values, formulas, and interpretations.
        """
        ratios = {}
        
        # Extract required values with safe defaults
        total_debt = balance_sheet.get("total_debt", 0)
        shareholders_equity = balance_sheet.get("shareholders_equity", 0)
        total_assets = balance_sheet.get("total_assets", 0)
        ebit = income_statement.get("ebit", 0)
        interest_expense = income_statement.get("interest_expense", 0)
        
        # Debt to equity ratio
        if shareholders_equity > 0:
            debt_to_equity = round(total_debt / shareholders_equity, 2)
            ratios["debt_to_equity"] = {
                "value": debt_to_equity,
                "formula": "Total Debt / Shareholders' Equity",
                "interpretation": f"The company has ${debt_to_equity:.2f} in debt for every $1 in equity."
            }
        else:
            ratios["debt_to_equity"] = {
                "value": None,
                "formula": "Total Debt / Shareholders' Equity",
                "interpretation": "Cannot calculate due to zero or negative shareholders' equity."
            }
        
        # Debt ratio
        if total_assets > 0:
            debt_ratio = round(total_debt / total_assets, 2)
            debt_pct = round(debt_ratio * 100, 2)
            ratios["debt_ratio"] = {
                "value": debt_ratio,
                "formula": "Total Debt / Total Assets",
                "interpretation": f"{debt_pct:.2f}% of the company's assets are financed by debt."
            }
        else:
            ratios["debt_ratio"] = {
                "value": None,
                "formula": "Total Debt / Total Assets",
                "interpretation": "Cannot calculate due to zero or negative total assets."
            }
        
        # Interest coverage ratio
        if interest_expense > 0:
            interest_coverage = round(ebit / interest_expense, 2)
            ratios["interest_coverage"] = {
                "value": interest_coverage,
                "formula": "EBIT / Interest Expense",
                "interpretation": f"The company can cover its interest expense {interest_coverage:.2f} times with its earnings."
            }
        else:
            ratios["interest_coverage"] = {
                "value": None,
                "formula": "EBIT / Interest Expense",
                "interpretation": "Cannot calculate due to zero or negative interest expense."
            }
        
        return ratios
    
    def _calculate_efficiency_ratios(
        self, 
        balance_sheet: Dict[str, Any],
        income_statement: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate efficiency ratios based on balance sheet and income statement data.
        
        Args:
            balance_sheet: Dictionary containing balance sheet accounts and values.
            income_statement: Dictionary containing income statement accounts and values.
            
        Returns:
            Dictionary of efficiency ratios with values, formulas, and interpretations.
        """
        ratios = {}
        
        # Extract required values with safe defaults
        revenue = income_statement.get("revenue", 0)
        total_assets = balance_sheet.get("total_assets", 0)
        cogs = income_statement.get("cost_of_goods_sold", 0)
        inventory = balance_sheet.get("inventory", 0)
        accounts_receivable = balance_sheet.get("accounts_receivable", 0)
        accounts_payable = balance_sheet.get("accounts_payable", 0)
        
        # Asset turnover ratio
        if total_assets > 0:
            asset_turnover = round(revenue / total_assets, 2)
            ratios["asset_turnover"] = {
                "value": asset_turnover,
                "formula": "Revenue / Total Assets",
                "interpretation": f"The company generates ${asset_turnover:.2f} in revenue for every $1 in assets."
            }
        else:
            ratios["asset_turnover"] = {
                "value": None,
                "formula": "Revenue / Total Assets",
                "interpretation": "Cannot calculate due to zero or negative total assets."
            }
        
        # Inventory turnover ratio
        if inventory > 0:
            inventory_turnover = round(cogs / inventory, 2)
            ratios["inventory_turnover"] = {
                "value": inventory_turnover,
                "formula": "Cost of Goods Sold / Average Inventory",
                "interpretation": f"The company turns over its inventory {inventory_turnover:.2f} times per year."
            }
        else:
            ratios["inventory_turnover"] = {
                "value": None,
                "formula": "Cost of Goods Sold / Average Inventory",
                "interpretation": "Cannot calculate due to zero or negative inventory."
            }
        
        # Days sales outstanding (DSO)
        if revenue > 0:
            daily_revenue = revenue / 365
            if daily_revenue > 0:
                dso = round(accounts_receivable / daily_revenue, 0)
                ratios["days_sales_outstanding"] = {
                    "value": dso,
                    "formula": "(Accounts Receivable / Revenue) * 365",
                    "interpretation": f"The company takes an average of {dso:.0f} days to collect its receivables."
                }
            else:
                ratios["days_sales_outstanding"] = {
                    "value": None,
                    "formula": "(Accounts Receivable / Revenue) * 365",
                    "interpretation": "Cannot calculate due to zero daily revenue."
                }
        else:
            ratios["days_sales_outstanding"] = {
                "value": None,
                "formula": "(Accounts Receivable / Revenue) * 365",
                "interpretation": "Cannot calculate due to zero or negative revenue."
            }
        
        # Days payable outstanding (DPO)
        if cogs > 0:
            daily_cogs = cogs / 365
            if daily_cogs > 0:
                dpo = round(accounts_payable / daily_cogs, 0)
                ratios["days_payable_outstanding"] = {
                    "value": dpo,
                    "formula": "(Accounts Payable / Cost of Goods Sold) * 365",
                    "interpretation": f"The company takes an average of {dpo:.0f} days to pay its suppliers."
                }
            else:
                ratios["days_payable_outstanding"] = {
                    "value": None,
                    "formula": "(Accounts Payable / Cost of Goods Sold) * 365",
                    "interpretation": "Cannot calculate due to zero daily cost of goods sold."
                }
        else:
            ratios["days_payable_outstanding"] = {
                "value": None,
                "formula": "(Accounts Payable / Cost of Goods Sold) * 365",
                "interpretation": "Cannot calculate due to zero or negative cost of goods sold."
            }
        
        return ratios
        
    def _compare_with_benchmarks(
        self, 
        calculated_ratios: Dict[str, Dict[str, Dict[str, Any]]],
        benchmarks: Dict[str, Any]
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Compare calculated ratios with industry benchmarks.
        
        Args:
            calculated_ratios: Dictionary of calculated financial ratios by category.
            benchmarks: Dictionary of industry benchmarks for comparison.
            
        Returns:
            Dictionary containing benchmark comparisons by category and ratio.
        """
        comparisons = {}
        
        for category, ratios in calculated_ratios.items():
            comparisons[category] = {}
            
            for ratio_name, ratio_data in ratios.items():
                # Skip ratios that couldn't be calculated
                if ratio_data["value"] is None:
                    comparisons[category][ratio_name] = "Cannot compare due to inability to calculate ratio."
                    continue
                
                # Get benchmark value for this ratio if it exists
                benchmark_value = benchmarks.get(category, {}).get(ratio_name)
                
                if benchmark_value is None:
                    comparisons[category][ratio_name] = "No benchmark data available for comparison."
                    continue
                
                # Calculate percentage difference
                pct_diff = ((ratio_data["value"] - benchmark_value) / benchmark_value) * 100
                
                # Determine if the difference is favorable or unfavorable
                # This is simplistic and would need to be refined based on the specific ratio
                if ratio_name in ["current_ratio", "quick_ratio", "cash_ratio", "gross_margin", 
                                 "operating_margin", "net_profit_margin", "return_on_assets", 
                                 "return_on_equity", "interest_coverage", "asset_turnover", 
                                 "inventory_turnover"]:
                    favorable = pct_diff > 0
                else:  # For ratios where lower is better
                    favorable = pct_diff < 0
                
                status = "favorable" if favorable else "unfavorable"
                
                comparisons[category][ratio_name] = (
                    f"The company's {ratio_name} of {ratio_data['value']} is "
                    f"{abs(pct_diff):.2f}% {status} compared to the industry benchmark "
                    f"of {benchmark_value}."
                )
                
        return comparisons

    def calculate_financial_ratios(
        self,
        balance_sheet: Optional[Dict[str, Any]] = None,
        income_statement: Optional[Dict[str, Any]] = None,
        cash_flow_statement: Optional[Dict[str, Any]] = None,
        ratio_categories: Optional[List[str]] = None,
        prior_period_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive financial ratios from financial statement data.

        Args:
            balance_sheet: Dictionary containing balance sheet accounts and values.
            income_statement: Dictionary containing income statement accounts and values.
            cash_flow_statement: Dictionary containing cash flow statement data.
            ratio_categories: Categories of ratios to calculate (e.g., "liquidity", "profitability", "solvency", "efficiency").
            prior_period_data: Optional dictionary of prior period data for trend analysis.

        Returns:
            Dictionary containing calculated ratios, interpretations, and trends.
        """
        # Set default values if not provided
        balance_sheet = balance_sheet or {}
        income_statement = income_statement or {}
        cash_flow_statement = cash_flow_statement or {}
        ratio_categories = ratio_categories or ["liquidity", "profitability", "solvency", "efficiency"]
        prior_period_data = prior_period_data or {}

        logger.info(f"Calculating financial ratios for {', '.join(ratio_categories)}")

        # Initialize result structure
        ratio_analysis = {
            "summary": "Financial ratio analysis based on provided financial statement data",
            "ratios_by_category": {}
        }

        # Calculate requested ratio categories
        if "liquidity" in ratio_categories:
            ratio_analysis["ratios_by_category"]["liquidity"] = self._calculate_liquidity_ratios(balance_sheet)

        if "profitability" in ratio_categories:
            ratio_analysis["ratios_by_category"]["profitability"] = self._calculate_profitability_ratios(
                income_statement, balance_sheet
            )

        if "solvency" in ratio_categories:
            ratio_analysis["ratios_by_category"]["solvency"] = self._calculate_solvency_ratios(
                balance_sheet, income_statement
            )

        if "efficiency" in ratio_categories:
            ratio_analysis["ratios_by_category"]["efficiency"] = self._calculate_efficiency_ratios(
                balance_sheet, income_statement
            )

        if "cash_flow" in ratio_categories:
            ratio_analysis["ratios_by_category"]["cash_flow"] = self._calculate_cash_flow_ratios(
                cash_flow_statement, income_statement, balance_sheet
            )

        if "valuation" in ratio_categories and "market_data" in balance_sheet:
            ratio_analysis["ratios_by_category"]["valuation"] = self._calculate_valuation_ratios(
                balance_sheet, income_statement
            )

        # Calculate trend analysis if prior period data is provided
        if prior_period_data:
            ratio_analysis["trend_analysis"] = self._calculate_ratio_trends(
                ratio_analysis["ratios_by_category"], prior_period_data
            )

        # Generate overall assessment
        ratio_analysis["overall_assessment"] = self._generate_financial_health_assessment(
            ratio_analysis["ratios_by_category"]
        )

        return ratio_analysis


    def analyze_financial_statements(
        self, 
        analysis_type: Optional[str] = None,
        balance_sheet: Optional[Dict[str, Any]] = None,
        income_statement: Optional[Dict[str, Any]] = None,
        cash_flow_statement: Optional[Dict[str, Any]] = None,
        benchmarks: Optional[Dict[str, Any]] = None,
        specific_concerns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze financial statements and provide insights on financial health.
        
        Args:
            analysis_type: Type of analysis to perform (e.g., "comprehensive", "liquidity", "profitability", "solvency").
            balance_sheet: Dictionary containing balance sheet data.
            income_statement: Dictionary containing income statement data.
            cash_flow_statement: Dictionary containing cash flow statement data.
            benchmarks: Optional dictionary of industry benchmarks for comparison.
            specific_concerns: Optional list of specific areas of concern to address in analysis.
                
        Returns:
            A dictionary containing financial analysis, key ratios, trends, and recommendations.
        """
        # Set default values if not provided
        analysis_type = analysis_type or "comprehensive"
        balance_sheet = balance_sheet or {}
        income_statement = income_statement or {}
        cash_flow_statement = cash_flow_statement or {}
        benchmarks = benchmarks or {}
        specific_concerns = specific_concerns or []
            
        logger.info(f"Performing {analysis_type} analysis on financial statements")
        
        # Initialize result structure
        result = {
            "analysis_summary": f"{analysis_type.capitalize()} analysis of financial statements",
            "key_observations": [],
            "financial_ratios": {},
            "recommendations": []
        }
        
        # Calculate relevant ratios based on analysis type
        if analysis_type in ["comprehensive", "liquidity"]:
            result["financial_ratios"]["liquidity"] = self._calculate_liquidity_ratios(balance_sheet)
            
        if analysis_type in ["comprehensive", "profitability"]:
            result["financial_ratios"]["profitability"] = self._calculate_profitability_ratios(
                income_statement, balance_sheet
            )
            
        if analysis_type in ["comprehensive", "solvency"]:
            result["financial_ratios"]["solvency"] = self._calculate_solvency_ratios(
                balance_sheet, income_statement
            )
            
        if analysis_type in ["comprehensive", "efficiency"]:
            result["financial_ratios"]["efficiency"] = self._calculate_efficiency_ratios(
                balance_sheet, income_statement
            )
        
        # Generate key observations based on calculated ratios
        observations = []
        
        # Liquidity observations
        if "liquidity" in result["financial_ratios"]:
            liquidity_ratios = result["financial_ratios"]["liquidity"]
            
            if liquidity_ratios["current_ratio"]["value"] is not None:
                current_ratio = liquidity_ratios["current_ratio"]["value"]
                if current_ratio < 1:
                    observations.append(
                        f"The current ratio of {current_ratio:.2f} indicates the company may have difficulty meeting short-term obligations."
                    )
                elif current_ratio > 2:
                    observations.append(
                        f"The current ratio of {current_ratio:.2f} suggests the company has strong short-term liquidity, but may be underutilizing assets."
                    )
                else:
                    observations.append(
                        f"The current ratio of {current_ratio:.2f} indicates adequate short-term liquidity."
                    )
        
        # Profitability observations
        if "profitability" in result["financial_ratios"]:
            prof_ratios = result["financial_ratios"]["profitability"]
            
            if prof_ratios["net_profit_margin"]["value"] is not None:
                npm = prof_ratios["net_profit_margin"]["value"]
                if npm < 0:
                    observations.append(
                        f"The negative net profit margin of {npm:.2f}% indicates the company is operating at a loss."
                    )
                elif npm < 5:
                    observations.append(
                        f"The net profit margin of {npm:.2f}% is relatively low, suggesting thin profitability."
                    )
                else:
                    observations.append(
                        f"The net profit margin of {npm:.2f}% indicates good profitability."
                    )
        
        # Solvency observations
        if "solvency" in result["financial_ratios"]:
            solv_ratios = result["financial_ratios"]["solvency"]
            
            if solv_ratios["debt_to_equity"]["value"] is not None:
                dte = solv_ratios["debt_to_equity"]["value"]
                if dte > 2:
                    observations.append(
                        f"The debt-to-equity ratio of {dte:.2f} indicates high financial leverage, which may increase financial risk."
                    )
                elif dte < 0.5:
                    observations.append(
                        f"The debt-to-equity ratio of {dte:.2f} suggests conservative financing, potentially underutilizing debt."
                    )
                else:
                    observations.append(
                        f"The debt-to-equity ratio of {dte:.2f} indicates balanced financing between debt and equity."
                    )
        
        # Add observations to result if we have any, otherwise indicate insufficient data
        if observations:
            result["key_observations"] = observations
        else:
            result["key_observations"] = ["Insufficient data provided to generate meaningful observations."]
        
        # Add benchmark comparisons if provided
        if benchmarks:
            result["benchmark_comparison"] = self._compare_with_benchmarks(
                result["financial_ratios"], benchmarks
            )
        
        # Generate recommendations based on analysis
        recommendations = []
        
        # Only generate recommendations if we have data to analyze
        if not balance_sheet and not income_statement and not cash_flow_statement:
            recommendations.append("Insufficient financial data provided. Please provide balance sheet, income statement, or cash flow statement data for analysis.")
        else:
            # Consider liquidity for recommendations
            if "liquidity" in result["financial_ratios"]:
                liquidity_ratios = result["financial_ratios"]["liquidity"]
                
                if (liquidity_ratios["current_ratio"]["value"] is not None and 
                    liquidity_ratios["current_ratio"]["value"] < 1):
                    recommendations.append(
                        "Improve short-term liquidity by extending payment terms with suppliers, accelerating collections, or securing additional working capital financing."
                    )
                elif (liquidity_ratios["cash_ratio"]["value"] is not None and 
                     liquidity_ratios["cash_ratio"]["value"] < 0.2):
                    recommendations.append(
                        "Consider increasing cash reserves to improve emergency liquidity position."
                    )
                elif (liquidity_ratios["current_ratio"]["value"] is not None and 
                     liquidity_ratios["current_ratio"]["value"] > 3):
                    recommendations.append(
                        "Evaluate opportunities to deploy excess current assets to generate higher returns."
                    )
            
            # Consider profitability for recommendations
            if "profitability" in result["financial_ratios"]:
                prof_ratios = result["financial_ratios"]["profitability"]
                
                if (prof_ratios["gross_margin"]["value"] is not None and 
                    prof_ratios["gross_margin"]["value"] < 20):
                    recommendations.append(
                        "Review pricing strategy and cost of goods sold to improve gross margins."
                    )
                
                if (prof_ratios["operating_margin"]["value"] is not None and 
                    prof_ratios["operating_margin"]["value"] < 5):
                    recommendations.append(
                        "Implement cost control measures to reduce operating expenses and improve operating margins."
                    )
            
            # Consider efficiency for recommendations
            if "efficiency" in result["financial_ratios"]:
                eff_ratios = result["financial_ratios"]["efficiency"]
                
                if (eff_ratios["days_sales_outstanding"]["value"] is not None and 
                    eff_ratios["days_sales_outstanding"]["value"] > 60):
                    recommendations.append(
                        "Improve accounts receivable management to reduce days sales outstanding and accelerate cash collection."
                    )
                
                if (eff_ratios["inventory_turnover"]["value"] is not None and 
                    eff_ratios["inventory_turnover"]["value"] < 4):
                    recommendations.append(
                        "Review inventory management practices to improve inventory turnover and reduce carrying costs."
                    )
        
        # Add recommendations to result
        if recommendations:
            result["recommendations"] = recommendations
        else:
            result["recommendations"] = ["Insufficient data to generate specific recommendations. Please provide more detailed financial information."]
            
        # Address specific concerns if provided
        if specific_concerns:
            addressed_concerns = {}
            
            # Check if we have enough data to address specific concerns
            if not balance_sheet and not income_statement and not cash_flow_statement:
                for concern in specific_concerns:
                    addressed_concerns[concern] = "Insufficient financial data provided to address this concern. Please provide balance sheet, income statement, or cash flow statement data for analysis."
            else:
                for concern in specific_concerns:
                    if "liquidity" in concern.lower():
                        if "liquidity" in result["financial_ratios"] and result["financial_ratios"]["liquidity"]:
                            # Find relevant liquidity observation if it exists
                            liquidity_obs = next((obs for obs in observations if "current ratio" in obs.lower()), None)
                            addressed_concerns[concern] = "Liquidity analysis indicates that " + \
                                (liquidity_obs if liquidity_obs else "specific liquidity metrics are available, but more context is needed to fully address this concern.")
                        else:
                            addressed_concerns[concern] = "Insufficient data is available to address liquidity concerns. Please provide balance sheet data including current assets and current liabilities."
                    
                    elif "profitability" in concern.lower():
                        if "profitability" in result["financial_ratios"] and result["financial_ratios"]["profitability"]:
                            # Find relevant profitability observation if it exists
                            prof_obs = next((obs for obs in observations if "profit margin" in obs.lower()), None)
                            addressed_concerns[concern] = "Profitability analysis shows that " + \
                                (prof_obs if prof_obs else "specific profitability metrics are available, but more context is needed to fully address this concern.")
                        else:
                            addressed_concerns[concern] = "Insufficient data is available to address profitability concerns. Please provide income statement data including revenue and various profit measures."
                    
                    elif "solvency" in concern.lower() or "debt" in concern.lower():
                        if "solvency" in result["financial_ratios"] and result["financial_ratios"]["solvency"]:
                            # Find relevant solvency observation if it exists
                            solvency_obs = next((obs for obs in observations if "debt-to-equity" in obs.lower()), None)
                            addressed_concerns[concern] = "Solvency analysis reveals that " + \
                                (solvency_obs if solvency_obs else "specific solvency metrics are available, but more context is needed to fully address this concern.")
                        else:
                            addressed_concerns[concern] = "Insufficient data is available to address solvency concerns. Please provide balance sheet data including debt and equity information."
                    
                    elif "cash flow" in concern.lower():
                        if cash_flow_statement:
                            operating_cf = cash_flow_statement.get("operating_cash_flow")
                            net_income = income_statement.get("net_income") if income_statement else None
                            
                            if operating_cf is not None and net_income is not None and net_income > 0:
                                cf_to_income = operating_cf / net_income
                                addressed_concerns[concern] = f"Cash flow analysis shows an operating cash flow to net income ratio of {cf_to_income:.2f}, indicating " + \
                                    ("strong" if cf_to_income > 1 else "weak") + " cash generation relative to reported earnings."
                            elif operating_cf is not None:
                                addressed_concerns[concern] = f"Cash flow data shows operating cash flow of ${operating_cf:,.2f}, but additional context or income statement data is needed for a complete analysis."
                            else:
                                addressed_concerns[concern] = "Cash flow statement provided, but operating cash flow data is missing or incomplete."
                        else:
                            addressed_concerns[concern] = "Insufficient cash flow data is available to address this concern. Please provide a cash flow statement."
                    
                    else:
                        addressed_concerns[concern] = "This specific concern requires additional context or data to address adequately. Please provide more details about your concern and relevant financial data."
            
            result["addressing_concerns"] = addressed_concerns
            
        return result
    
    def _get_gaap_references(self, transaction_type: str) -> List[str]:
        """
        Get relevant GAAP references for a given transaction type.
        
        Args:
            transaction_type: The type of transaction.
            
        Returns:
            List of relevant GAAP standards and references.
        """
        gaap_references = {
            "revenue_recognition": [
                "ASC 606 - Revenue from Contracts with Customers",
                "ASC 610-20 - Gains and Losses from Derecognition of Nonfinancial Assets"
            ],
            "leases": [
                "ASC 842 - Leases"
            ],
            "inventory": [
                "ASC 330 - Inventory"
            ],
            "fixed_assets": [
                "ASC 360 - Property, Plant, and Equipment"
            ],
            "intangible_assets": [
                "ASC 350 - Intangibles - Goodwill and Other"
            ],
            "depreciation": [
                "ASC 360 - Property, Plant, and Equipment"
            ],
            "impairment": [
                "ASC 360 - Property, Plant, and Equipment",
                "ASC 350 - Intangibles - Goodwill and Other"
            ],
            "debt": [
                "ASC 470 - Debt"
            ],
            "equity": [
                "ASC 505 - Equity"
            ],
            "investments": [
                "ASC 320 - Investments - Debt and Equity Securities",
                "ASC 321 - Investments - Equity Securities",
                "ASC 323 - Investments - Equity Method and Joint Ventures"
            ],
            "business_combinations": [
                "ASC 805 - Business Combinations"
            ],
            "contingencies": [
                "ASC 450 - Contingencies"
            ],
            "fair_value": [
                "ASC 820 - Fair Value Measurement"
            ],
            "income_taxes": [
                "ASC 740 - Income Taxes"
            ],
            "foreign_currency": [
                "ASC 830 - Foreign Currency Matters"
            ],
            "stock_compensation": [
                "ASC 718 - Compensation - Stock Compensation"
            ],
            "pensions": [
                "ASC 715 - Compensation - Retirement Benefits"
            ],
            "accruals": [
                "ASC 450 - Contingencies"
            ],
        }
        
        # Default references for transactions not specifically mapped
        default_references = [
            "ASC 105 - Generally Accepted Accounting Principles",
            "ASC 205 - Presentation of Financial Statements"
        ]
        
        # Return specific references if available, otherwise default
        return gaap_references.get(transaction_type.lower(), default_references)
    
    def _get_ifrs_references(self, transaction_type: str) -> List[str]:
        """
        Get relevant IFRS references for a given transaction type.
        
        Args:
            transaction_type: The type of transaction.
            
        Returns:
            List of relevant IFRS standards and references.
        """
        ifrs_references = {
            "revenue_recognition": [
                "IFRS 15 - Revenue from Contracts with Customers"
            ],
            "leases": [
                "IFRS 16 - Leases"
            ],
            "inventory": [
                "IAS 2 - Inventories"
            ],
            "fixed_assets": [
                "IAS 16 - Property, Plant and Equipment"
            ],
            "intangible_assets": [
                "IAS 38 - Intangible Assets",
                "IFRS 3 - Business Combinations (for goodwill)"
            ],
            "depreciation": [
                "IAS 16 - Property, Plant and Equipment"
            ],
            "impairment": [
                "IAS 36 - Impairment of Assets"
            ],
            "debt": [
                "IFRS 9 - Financial Instruments",
                "IAS 32 - Financial Instruments: Presentation"
            ],
            "equity": [
                "IAS 32 - Financial Instruments: Presentation"
            ],
            "investments": [
                "IFRS 9 - Financial Instruments",
                "IAS 28 - Investments in Associates and Joint Ventures"
            ],
            "business_combinations": [
                "IFRS 3 - Business Combinations"
            ],
            "contingencies": [
                "IAS 37 - Provisions, Contingent Liabilities and Contingent Assets"
            ],
            "fair_value": [
                "IFRS 13 - Fair Value Measurement"
            ],
            "income_taxes": [
                "IAS 12 - Income Taxes"
            ],
            "foreign_currency": [
                "IAS 21 - The Effects of Changes in Foreign Exchange Rates"
            ],
            "stock_compensation": [
                "IFRS 2 - Share-based Payment"
            ],
            "pensions": [
                "IAS 19 - Employee Benefits"
            ],
            "accruals": [
                "IAS 37 - Provisions, Contingent Liabilities and Contingent Assets"
            ],
        }
        
        # Default references for transactions not specifically mapped
        default_references = [
            "IAS 1 - Presentation of Financial Statements",
            "IAS 8 - Accounting Policies, Changes in Accounting Estimates and Errors"
        ]
        
        # Return specific references if available, otherwise default
        return ifrs_references.get(transaction_type.lower(), default_references)
    
    def advise_on_accounting_treatment(
        self, 
        transaction_description: Optional[str] = None,
        amount: Optional[float] = None,
        accounting_framework: Optional[str] = None,
        industry: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Provide guidance on the appropriate accounting treatment for a transaction.
        
        Args:
            transaction_description: Description of the transaction requiring accounting guidance.
            amount: The monetary amount involved in the transaction.
            accounting_framework: The accounting framework to use (e.g., "GAAP", "IFRS").
            industry: Optional industry context, which may affect specialized accounting guidance.
            entity_type: Optional entity type (e.g., "for-profit", "non-profit", "governmental").
            
        Returns:
            A dictionary containing recommended accounting treatment, journal entries, disclosure requirements,
            and relevant accounting standards.
        """
        # Set default values if not provided
        transaction_description = transaction_description or "Unspecified transaction"
        amount = amount or 0.0
        accounting_framework = accounting_framework or "GAAP"
        industry = industry or "General"
        entity_type = entity_type or "for-profit"
            
        logger.info(f"Advising on {accounting_framework} treatment for transaction: {transaction_description[:50]}...")
        
        # Determine transaction type from description
        transaction_type = self._identify_transaction_type(transaction_description)
        
        # Get relevant accounting standards based on the framework and transaction type
        if accounting_framework.upper() == "IFRS":
            accounting_standards = self._get_ifrs_references(transaction_type)
        else:  # Default to GAAP
            accounting_standards = self._get_gaap_references(transaction_type)
        
        # Determine appropriate accounts and journal entries based on transaction type
        journal_entries = self._generate_journal_entries(
            transaction_type, 
            amount, 
            accounting_framework,
            entity_type
        )
        
        # Generate documentation requirements
        documentation_requirements = self._generate_documentation_requirements(
            transaction_type, 
            amount, 
            accounting_framework
        )
        
        # Generate disclosure requirements
        disclosure_requirements = self._generate_disclosure_requirements(
            transaction_type, 
            amount, 
            accounting_framework
        )
        
        # Prepare response
        guidance = {
            "transaction_summary": f"{transaction_description} for ${amount:,.2f}",
            "transaction_type_identified": transaction_type,
            "recommended_treatment": self._generate_accounting_treatment(
                transaction_type, 
                amount, 
                accounting_framework
            ),
            "journal_entries": journal_entries,
            "accounting_standards": accounting_standards,
            "documentation_requirements": documentation_requirements,
            "disclosure_requirements": disclosure_requirements
        }
        
        # Add industry-specific considerations if applicable
        if industry:
            guidance["industry_specific_considerations"] = self._generate_industry_considerations(
                transaction_type, 
                industry, 
                accounting_framework
            )
            
        # Add entity-specific considerations if applicable
        if entity_type:
            guidance["entity_specific_considerations"] = self._generate_entity_considerations(
                transaction_type, 
                entity_type, 
                accounting_framework
            )
            
        return guidance
    
    def _identify_transaction_type(self, transaction_description: str) -> str:
        """
        Identify the transaction type from a description.
        
        Args:
            transaction_description: Description of the transaction.
            
        Returns:
            The identified transaction type.
        """
        # Dictionary mapping keywords to transaction types
        transaction_keywords = {
            "revenue_recognition": ["revenue", "sales", "income", "customer", "contract"],
            "leases": ["lease", "rent", "rental"],
            "inventory": ["inventory", "stock", "goods", "merchandise"],
            "fixed_assets": ["equipment", "property", "plant", "building", "machine"],
            "intangible_assets": ["intangible", "goodwill", "trademark", "patent"],
            "depreciation": ["depreciation", "depreciate"],
            "impairment": ["impairment", "impair", "write-down", "write down"],
            "debt": ["loan", "debt", "borrow", "borrowing", "credit"],
            "equity": ["equity", "stock", "share", "capital"],
            "investments": ["investment", "invest", "security", "securities"],
            "business_combinations": ["acquisition", "merge", "merger", "acquire"],
            "contingencies": ["contingent", "contingency", "lawsuit", "litigation"],
            "fair_value": ["fair value", "market value"],
            "income_taxes": ["tax", "income tax"],
            "foreign_currency": ["foreign", "currency", "exchange rate"],
            "stock_compensation": ["stock option", "equity award", "stock award"],
            "pensions": ["pension", "retirement", "benefit"],
            "accruals": ["accrual", "accrue", "provision"]
        }
        
        # Convert description to lowercase
        desc_lower = transaction_description.lower()
        
        # Find matching transaction types
        matching_types = []
        for tx_type, keywords in transaction_keywords.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    matching_types.append(tx_type)
                    break
        
        # Return the most specific match or a default
        if matching_types:
            # If multiple matches, prioritize certain types
            priority_order = [
                "revenue_recognition", "leases", "inventory", "fixed_assets", 
                "intangible_assets", "depreciation", "impairment"
            ]
            
            for priority_type in priority_order:
                if priority_type in matching_types:
                    return priority_type
            
            # If no priority match, return the first match
            return matching_types[0]
        
        # Default to general if no match found
        return "general"
    
    def _generate_journal_entries(
        self, 
        transaction_type: str, 
        amount: float, 
        accounting_framework: str,
        entity_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate appropriate journal entries for a transaction.
        
        Args:
            transaction_type: The type of transaction.
            amount: The amount involved in the transaction.
            accounting_framework: The accounting framework (GAAP, IFRS).
            entity_type: The entity type (for-profit, non-profit, governmental).
            
        Returns:
            List of journal entries with accounts, debits, and credits.
        """
        entries = []
        
        # Format amount to two decimal places
        amount = round(amount, 2)
        
        # Generate entries based on transaction type
        if transaction_type == "revenue_recognition":
            # For revenue recognition, record revenue and either A/R or cash
            entries = [
                {
                    "account": "Accounts Receivable",
                    "debit": amount,
                    "credit": 0
                },
                {
                    "account": "Revenue",
                    "debit": 0,
                    "credit": amount
                }
            ]
            
            # For non-profits, the account naming may differ
            if entity_type == "non-profit":
                entries[1]["account"] = "Program Revenue"
        
        elif transaction_type == "leases":
            # Handle leases differently based on accounting framework
            if accounting_framework.upper() == "IFRS" or (accounting_framework.upper() == "GAAP" and amount >= 5000):
                # Under IFRS 16 or ASC 842, capitalize lease
                entries = [
                    {
                        "account": "Right-of-Use Asset",
                        "debit": amount,
                        "credit": 0
                    },
                    {
                        "account": "Lease Liability",
                        "debit": 0,
                        "credit": amount
                    }
                ]
            else:
                # Under old GAAP or for small leases, may treat as operating lease
                entries = [
                    {
                        "account": "Rent Expense",
                        "debit": amount,
                        "credit": 0
                    },
                    {
                        "account": "Cash",
                        "debit": 0,
                        "credit": amount
                    }
                ]
        
        elif transaction_type == "fixed_assets":
            # For fixed asset acquisition
            entries = [
                {
                    "account": "Property, Plant & Equipment",
                    "debit": amount,
                    "credit": 0
                },
                {
                    "account": "Cash" if amount <= 10000 else "Accounts Payable",
                    "debit": 0,
                    "credit": amount
                }
            ]
        
        elif transaction_type == "depreciation":
            # For depreciation expense
            entries = [
                {
                    "account": "Depreciation Expense",
                    "debit": amount,
                    "credit": 0
                },
                {
                    "account": "Accumulated Depreciation",
                    "debit": 0,
                    "credit": amount
                }
            ]
        
        elif transaction_type == "debt":
            # For loan/debt acquisition
            entries = [
                {
                    "account": "Cash",
                    "debit": amount,
                    "credit": 0
                },
                {
                    "account": "Notes Payable" if amount <= 50000 else "Long-term Debt",
                    "debit": 0,
                    "credit": amount
                }
            ]
        
        elif transaction_type == "accruals":
            # For accrued expenses
            entries = [
                {
                    "account": "Accrued Expense",
                    "debit": amount,
                    "credit": 0
                },
                {
                    "account": "Accrued Liability",
                    "debit": 0,
                    "credit": amount
                }
            ]
        
        else:
            # Default, generic entry
            entries = [
                {
                    "account": "Debit Account",
                    "debit": amount,
                    "credit": 0,
                    "note": "Specific account should be determined based on detailed transaction analysis"
                },
                {
                    "account": "Credit Account",
                    "debit": 0,
                    "credit": amount,
                    "note": "Specific account should be determined based on detailed transaction analysis"
                }
            ]
        
        return entries
    
    def _generate_accounting_treatment(
        self, 
        transaction_type: str, 
        amount: float, 
        accounting_framework: str
    ) -> str:
        """
        Generate appropriate accounting treatment explanation.
        
        Args:
            transaction_type: The type of transaction.
            amount: The amount involved in the transaction.
            accounting_framework: The accounting framework (GAAP, IFRS).
            
        Returns:
            Explanation of the recommended accounting treatment.
        """
        if transaction_type == "revenue_recognition":
            if accounting_framework.upper() == "IFRS":
                return (
                    f"Under IFRS 15, this transaction should be accounted for using the five-step model: "
                    f"(1) Identify the contract, (2) Identify performance obligations, (3) Determine transaction price, "
                    f"(4) Allocate price to obligations, and (5) Recognize revenue when obligations are satisfied. "
                    f"Based on the transaction description, recognize ${amount:,.2f} as revenue when control of "
                    f"goods/services transfers to the customer."
                )
            else:  # GAAP
                return (
                    f"Under ASC 606, this transaction should be accounted for using the five-step model: "
                    f"(1) Identify the contract, (2) Identify performance obligations, (3) Determine transaction price, "
                    f"(4) Allocate price to obligations, and (5) Recognize revenue when obligations are satisfied. "
                    f"Based on the transaction description, recognize ${amount:,.2f} as revenue when control of "
                    f"goods/services transfers to the customer."
                )
        
        elif transaction_type == "leases":
            if accounting_framework.upper() == "IFRS":
                return (
                    f"Under IFRS 16, this lease should be recognized on the balance sheet as a right-of-use asset "
                    f"of ${amount:,.2f} with a corresponding lease liability. The right-of-use asset will be depreciated "
                    f"over the lease term, and the lease liability will be reduced as payments are made, with a portion "
                    f"of each payment allocated to interest expense."
                )
            else:  # GAAP
                return (
                    f"Under ASC 842, this lease should be recognized on the balance sheet as a right-of-use asset "
                    f"of ${amount:,.2f} with a corresponding lease liability. The right-of-use asset will be depreciated "
                    f"over the lease term, and the lease liability will be reduced as payments are made, with a portion "
                    f"of each payment allocated to interest expense."
                )
        
        elif transaction_type == "fixed_assets":
            if accounting_framework.upper() == "IFRS":
                return (
                    f"Under IAS 16, this fixed asset should be initially recognized at cost of ${amount:,.2f}, "
                    f"which includes purchase price and any directly attributable costs of bringing the asset to working "
                    f"condition. The asset should be depreciated over its useful life using an appropriate method "
                    f"(straight-line, diminishing balance, or units of production)."
                )
            else:  # GAAP
                return (
                    f"Under ASC 360, this fixed asset should be initially recognized at cost of ${amount:,.2f}, "
                    f"which includes purchase price and any directly attributable costs of bringing the asset to working "
                    f"condition. The asset should be depreciated over its useful life using an appropriate method "
                    f"(straight-line, declining balance, or units of production)."
                )
        
        # Default response for other transaction types
        return (
            f"Based on the transaction type identified ({transaction_type}), this transaction should be "
            f"recorded according to applicable {accounting_framework} standards, with appropriate recognition, "
            f"measurement, and disclosure of the ${amount:,.2f} transaction amount."
        )
    
    def _generate_documentation_requirements(
        self, 
        transaction_type: str, 
        amount: float, 
        accounting_framework: str
    ) -> List[str]:
        """
        Generate documentation requirements for a transaction.
        
        Args:
            transaction_type: The type of transaction.
            amount: The amount involved in the transaction.
            accounting_framework: The accounting framework (GAAP, IFRS).
            
        Returns:
            List of documentation requirements.
        """
        # Base documentation requirements that apply to most transactions
        base_requirements = [
            "Transaction authorization with appropriate approval signatures",
            "Original source documents (invoices, contracts, receipts)",
            "Evidence of goods/services delivered or received",
            "Payment confirmation or receipt"
        ]
        
        # Additional requirements based on transaction type
        additional_requirements = {
            "revenue_recognition": [
                "Signed customer contract or purchase order",
                "Delivery confirmation or service completion documentation",
                "Evidence of transfer of control to customer",
                "Analysis of performance obligations and transaction price allocation"
            ],
            "leases": [
                "Signed lease agreement with all terms and conditions",
                "Lease classification analysis documentation",
                "Present value calculation of lease payments",
                "Useful life and residual value assessment for right-of-use asset"
            ],
            "fixed_assets": [
                "Asset acquisition documentation (purchase agreement, bill of sale)",
                "Proof of payment and ownership transfer",
                "Assessment of useful life and residual value",
                "Capitalization policy compliance documentation"
            ],
            "depreciation": [
                "Fixed asset register details",
                "Depreciation method and useful life documentation",
                "Calculation supporting depreciation amount",
                "Evidence of asset's continued use and condition"
            ],
            "debt": [
                "Loan agreement or debt instrument documentation",
                "Amortization schedule",
                "Debt covenant compliance documentation",
                "Board or management approval for debt issuance"
            ],
            "accruals": [
                "Supporting calculation for accrual amount",
                "Basis for estimation methodology",
                "Supporting documentation for underlying obligation",
                "Review and approval of accrual journal entry"
            ]
        }
        
        # Get additional requirements for this transaction type
        transaction_requirements = additional_requirements.get(transaction_type, [])
        
        # For high-value transactions, add more stringent requirements
        if amount > 100000:
            high_value_requirements = [
                "Senior management or board approval documentation",
                "Independent valuation or third-party verification if applicable",
                "Enhanced documentation of accounting rationale and treatment"
            ]
            transaction_requirements.extend(high_value_requirements)
        
        # Combine base and transaction-specific requirements
        all_requirements = base_requirements + transaction_requirements
        
        return all_requirements
    
    def _generate_disclosure_requirements(
        self, 
        transaction_type: str, 
        amount: float, 
        accounting_framework: str
    ) -> str:
        """
        Generate disclosure requirements for a transaction.
        
        Args:
            transaction_type: The type of transaction.
            amount: The amount involved in the transaction.
            accounting_framework: The accounting framework (GAAP, IFRS).
            
        Returns:
            Description of disclosure requirements.
        """
        framework = "IFRS" if accounting_framework.upper() == "IFRS" else "GAAP"
        materiality = "material" if amount > 100000 else "potentially immaterial"
        
        # Base disclosure requirements based on transaction type
        disclosure_by_type = {
            "revenue_recognition": (
                f"Under {framework}, disclose significant revenue streams, timing of satisfaction of performance "
                f"obligations, transaction prices allocated to remaining performance obligations, and "
                f"significant judgments in applying the revenue standard. As this is a {materiality} transaction, "
                f"consider specific disclosure of any unusual terms or conditions."
            ),
            "leases": (
                f"Under {framework}, disclose the nature of leasing activities, restrictions or covenants imposed "
                f"by leases, maturity analysis of lease liabilities, and amounts recognized in the financial statements. "
                f"For this {materiality} lease, include details in the lease commitment disclosures."
            ),
            "fixed_assets": (
                f"Under {framework}, disclose the measurement bases, depreciation methods, useful lives, gross carrying "
                f"amounts, and accumulated depreciation. For this {materiality} asset acquisition, consider "
                f"specific disclosure if it represents a significant addition to the asset base."
            ),
            "depreciation": (
                f"Under {framework}, disclose depreciation methods, useful lives, and depreciation amounts for "
                f"major classes of depreciable assets. This {materiality} depreciation charge should be "
                f"included in the aggregate depreciation disclosures."
            ),
            "debt": (
                f"Under {framework}, disclose terms and conditions of debt agreements, maturity analysis, interest rates, "
                f"collateral pledged, and debt covenants. For this {materiality} debt obligation, "
                f"consider specific disclosure of its purpose and terms."
            ),
            "accruals": (
                f"Under {framework}, disclose the nature of the accrual, expected timing of outflows, and "
                f"uncertainties about amount or timing. This {materiality} accrual should be included in the "
                f"appropriate financial statement line item disclosures."
            )
        }
        
        # Get specific disclosure requirements or use a generic one
        disclosure = disclosure_by_type.get(transaction_type, (
            f"Under {framework}, provide appropriate disclosures related to this {materiality} transaction "
            f"in accordance with applicable accounting standards, including nature, amount, and any "
            f"significant terms or conditions that may influence financial statement users' understanding."
        ))
        
        return disclosure
    
    def _generate_industry_considerations(
        self, 
        transaction_type: str, 
        industry: str, 
        accounting_framework: str
    ) -> str:
        """
        Generate industry-specific considerations for a transaction.
        
        Args:
            transaction_type: The type of transaction.
            industry: The industry context.
            accounting_framework: The accounting framework (GAAP, IFRS).
            
        Returns:
            Description of industry-specific considerations.
        """
        industry_lower = industry.lower()
        
        # Industry-specific considerations for different transaction types
        industry_considerations = {
            "banking": {
                "revenue_recognition": "Banking institutions have specific revenue recognition requirements for interest income, fee income, and commissions under regulatory frameworks like Basel III.",
                "leases": "Banking institutions may have special considerations for leasehold improvements in branch locations and disclosure requirements under banking regulations.",
                "debt": "Banks have specific regulatory capital requirements that may affect debt classification and disclosure requirements."
            },
            "healthcare": {
                "revenue_recognition": "Healthcare providers must consider third-party payor arrangements, contractual adjustments, and patient responsibility when recognizing revenue.",
                "fixed_assets": "Healthcare entities often have specialized medical equipment with specific useful life considerations and regulatory compliance requirements."
            },
            "retail": {
                "inventory": "Retail entities should consider inventory valuation methods, shrinkage, and markdown reserves appropriate for the retail industry.",
                "leases": "Retail companies with numerous store locations should implement systematic approaches to lease accounting with consideration for variable rent provisions."
            },
            "manufacturing": {
                "inventory": "Manufacturing companies must appropriately capitalize labor and overhead costs into inventory according to applicable standards.",
                "fixed_assets": "Manufacturing entities should consider componentization of significant manufacturing equipment for depreciation purposes."
            },
            "technology": {
                "revenue_recognition": "Technology companies often have complex arrangements involving multiple performance obligations, requiring careful analysis under revenue recognition standards.",
                "intangible_assets": "Technology firms should carefully evaluate capitalization criteria for internal development costs under applicable R&D standards."
            },
            "construction": {
                "revenue_recognition": "Construction companies must carefully evaluate whether to recognize revenue over time or at a point in time based on contract terms and control transfer.",
                "fixed_assets": "Construction companies should evaluate whether equipment is held for internal use or as part of their rental fleet, affecting classification."
            }
        }
        
        # Find the best matching industry
        best_match = None
        for ind in industry_considerations.keys():
            if ind in industry_lower:
                best_match = ind
                break
        
        if not best_match:
            return f"For the {industry} industry, consider any industry-specific accounting practices or regulatory requirements that may affect the accounting treatment of this transaction type."
        
        # Get consideration for this industry and transaction type, or default
        industry_consideration = industry_considerations.get(best_match, {}).get(
            transaction_type,
            f"For the {industry} industry, consider any industry-specific accounting practices or regulatory requirements that may affect the accounting treatment of this transaction type."
        )
        
        return industry_consideration
    
    def _generate_entity_considerations(
        self, 
        transaction_type: str, 
        entity_type: str, 
        accounting_framework: str
    ) -> str:
        """
        Generate entity-specific considerations for a transaction.
        
        Args:
            transaction_type: The type of transaction.
            entity_type: The entity type.
            accounting_framework: The accounting framework (GAAP, IFRS).
            
        Returns:
            Description of entity-specific considerations.
        """
        entity_lower = entity_type.lower()
        
        # Entity-specific considerations for different transaction types
        entity_considerations = {
            "non-profit": {
                "revenue_recognition": "Non-profit entities must distinguish between contributions and exchange transactions, and evaluate whether contributions are conditional or restricted.",
                "fixed_assets": "Non-profit entities should consider donor restrictions on fixed asset acquisitions and may use different terminology in financial statements.",
                "depreciation": "Non-profit entities typically follow the same depreciation principles as for-profit entities but may have different reporting requirements."
            },
            "governmental": {
                "revenue_recognition": "Governmental entities follow GASB standards which distinguish between exchange, non-exchange, and exchange-like transactions.",
                "fixed_assets": "Governmental entities use the capital asset classification and may employ different capitalization thresholds for different asset categories.",
                "debt": "Governmental entities have specific requirements for debt issuance and reporting under GASB standards."
            },
            "small business": {
                "revenue_recognition": "Small businesses may qualify for simplified methods of revenue recognition under certain accounting frameworks.",
                "leases": "Small businesses may qualify for practical expedients under lease accounting standards that simplify implementation."
            },
            "public company": {
                "revenue_recognition": "Public companies have enhanced disclosure requirements and SEC considerations for revenue recognition.",
                "leases": "Public companies must adhere to more stringent documentation and control requirements for lease accounting."
            }
        }
        
        # Find the best matching entity type
        best_match = None
        for ent in entity_considerations.keys():
            if ent in entity_lower:
                best_match = ent
                break
        
        if not best_match:
            return f"For {entity_type} entities, consider any specific accounting policies, reporting requirements, or regulatory considerations that may affect the accounting treatment of this transaction."
        
        # Get consideration for this entity type and transaction type, or default
        entity_consideration = entity_considerations.get(best_match, {}).get(
            transaction_type,
            f"For {entity_type} entities, consider any specific accounting policies, reporting requirements, or regulatory considerations that may affect the accounting treatment of this transaction."
        )
        
        return entity_consideration
    
    def develop_financial_controls(
        self,
        process_areas: Optional[List[str]] = None,
        entity_size: Optional[str] = None,
        risk_level: Optional[str] = None,
        compliance_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Develop financial control recommendations for various business processes.
        
        Args:
            process_areas: List of business process areas (e.g., "accounts payable", "payroll", "inventory").
            entity_size: Size of the entity (e.g., "small", "medium", "large").
            risk_level: Overall risk level to address (e.g., "low", "medium", "high").
            compliance_requirements: Optional list of specific compliance frameworks to address.
            
        Returns:
            Dictionary containing financial control recommendations, segregation of duties,
            monitoring procedures, and implementation guidance.
        """
        # Set default values if not provided
        process_areas = process_areas or ["accounts payable", "receivables", "payroll"]
        entity_size = entity_size or "medium"
        risk_level = risk_level or "medium"
        compliance_requirements = compliance_requirements or []
            
        logger.info(f"Developing financial controls for {len(process_areas)} process areas in {entity_size} entity")
        
        # Initialize results structure
        controls = {
            "overview": f"Financial controls framework for {entity_size} entity with {risk_level} risk profile",
            "process_controls": {},
            "documentation_requirements": self._generate_documentation_requirements_for_controls(entity_size, risk_level),
            "implementation_approach": self._generate_implementation_approach(entity_size, risk_level, process_areas),
            "key_control_owners": self._generate_control_owners_guidance(entity_size)
        }
        
        # Generate controls for each process area
        for process in process_areas:
            controls["process_controls"][process] = self._generate_process_controls(
                process, entity_size, risk_level
            )
        
        # Add compliance mapping if requirements specified
        if compliance_requirements:
            controls["compliance_mapping"] = self._generate_compliance_mapping(
                process_areas, compliance_requirements
            )
            
        return controls
    
    def _generate_process_controls(
        self, 
        process: str, 
        entity_size: str, 
        risk_level: str
    ) -> Dict[str, Any]:
        """
        Generate controls for a specific business process.
        
        Args:
            process: The business process area.
            entity_size: Size of the entity.
            risk_level: Risk level to address.
            
        Returns:
            Dictionary containing key risks, controls, segregation of duties, and monitoring.
        """
        process_lower = process.lower()
        
        # Control frameworks for different processes
        control_frameworks = {
            "accounts payable": {
                "key_risks": [
                    "Unauthorized or fraudulent payments",
                    "Duplicate payments to vendors",
                    "Inaccurate recording of liabilities",
                    "Payment to fictitious vendors",
                    "Failure to take advantage of discounts"
                ],
                "control_activities": {
                    "small": [
                        "Require dual signatures for checks above a defined threshold",
                        "Implement a purchase order system with approval workflows",
                        "Perform regular reconciliation of vendor statements to AP ledger",
                        "Maintain an approved vendor list with periodic review"
                    ],
                    "medium": [
                        "Implement three-way matching of PO, receiving report, and invoice",
                        "Configure system to flag potential duplicate invoices",
                        "Establish formal vendor onboarding and maintenance procedures",
                        "Implement approval matrix based on payment amount",
                        "Conduct periodic AP aging analysis and review"
                    ],
                    "large": [
                        "Implement automated three-way matching with exception reporting",
                        "Use electronic payment systems with multiple approval levels",
                        "Implement vendor master data management procedures",
                        "Conduct regular vendor validation and authentication",
                        "Use data analytics to identify unusual payment patterns",
                        "Implement formal vendor management program"
                    ]
                },
                "segregation_of_duties": {
                    "small": "Separate responsibilities for vendor setup, invoice approval, and payment processing between at least two individuals",
                    "medium": "Separate duties among vendor management, invoice processing, payment authorization, and reconciliation functions",
                    "large": "Implement comprehensive segregation of duties across vendor management, purchasing, receiving, invoice processing, payment authorization, and reconciliation, with system-enforced controls"
                },
                "monitoring_procedures": {
                    "small": [
                        "Monthly review of AP aging",
                        "Quarterly review of payment activities",
                        "Annual vendor file clean-up"
                    ],
                    "medium": [
                        "Monthly review of payments exceeding predetermined thresholds",
                        "Quarterly analysis of payment patterns",
                        "Semi-annual vendor file review",
                        "Periodic surprise audits of payment processes"
                    ],
                    "large": [
                        "Continuous monitoring of payment processing metrics",
                        "Monthly analysis of payment exceptions",
                        "Quarterly vendor analysis and performance review",
                        "Semi-annual control effectiveness testing",
                        "Annual comprehensive AP process audit"
                    ]
                }
            },
            "receivables": {
                "key_risks": [
                    "Unauthorized credit terms extended to customers",
                    "Inaccurate recording of sales and receivables",
                    "Failure to collect receivables in a timely manner",
                    "Misappropriation of customer payments",
                    "Improper write-off of receivables"
                ],
                "control_activities": {
                    "small": [
                        "Establish written credit approval policy",
                        "Perform monthly accounts receivable aging review",
                        "Implement basic customer credit limits",
                        "Reconcile customer payments to customer accounts"
                    ],
                    "medium": [
                        "Implement formal credit application and review process",
                        "Establish tiered credit approval authorities",
                        "Develop structured collection procedures",
                        "Reconcile daily deposits to sales records",
                        "Implement formal write-off approval policy"
                    ],
                    "large": [
                        "Implement automated credit scoring and monitoring",
                        "Use dedicated credit and collections department",
                        "Implement customer portal for payment processing",
                        "Use data analytics for collections prioritization",
                        "Implement automated dunning processes",
                        "Conduct regular credit file reviews"
                    ]
                },
                "segregation_of_duties": {
                    "small": "Separate responsibilities for credit approval, sales recording, payment processing, and write-off approval",
                    "medium": "Separate duties among credit management, sales processing, cash receipts, AR recording, and collections functions",
                    "large": "Implement comprehensive segregation of duties across credit management, customer onboarding, sales order processing, invoicing, cash application, collections, and write-off approval, with system-enforced controls"
                },
                "monitoring_procedures": {
                    "small": [
                        "Weekly review of past due accounts",
                        "Monthly AR aging analysis",
                        "Quarterly review of write-offs"
                    ],
                    "medium": [
                        "Weekly collection activity reporting",
                        "Monthly review of credit limit exceptions",
                        "Quarterly DSO (Days Sales Outstanding) analysis",
                        "Semi-annual review of collection effectiveness"
                    ],
                    "large": [
                        "Daily cash application monitoring",
                        "Weekly collection performance metrics",
                        "Monthly credit portfolio analysis",
                        "Quarterly trend analysis of payment patterns",
                        "Semi-annual customer risk assessment"
                    ]
                }
            },
            "payroll": {
                "key_risks": [
                    "Unauthorized or fictitious employees",
                    "Inaccurate time reporting",
                    "Unauthorized changes to pay rates or deductions",
                    "Errors in tax calculations or remittances",
                    "Misappropriation of payroll funds"
                ],
                "control_activities": {
                    "small": [
                        "Require written authorization for new hires and pay changes",
                        "Review and approve payroll register before processing",
                        "Secure payroll records with restricted access",
                        "Reconcile payroll bank account monthly"
                    ],
                    "medium": [
                        "Implement formal hiring and termination procedures",
                        "Use electronic time tracking with approval workflows",
                        "Develop change management controls for pay rates",
                        "Separate payroll processing from HR functions",
                        "Conduct periodic comparison of payroll to HR records"
                    ],
                    "large": [
                        "Implement integrated HR and payroll systems",
                        "Use biometric or multi-factor time tracking systems",
                        "Implement automated validation of payroll changes",
                        "Use payroll analytics to identify unusual patterns",
                        "Implement system controls over master data changes",
                        "Conduct regular payroll audits"
                    ]
                },
                "segregation_of_duties": {
                    "small": "Separate responsibilities for employee onboarding, time approval, payroll preparation, and payment distribution",
                    "medium": "Separate duties among HR functions, time entry approval, payroll processing, payroll approval, and payment distribution",
                    "large": "Implement comprehensive segregation of duties across HR functions, time and attendance, payroll master data, payroll processing, payment approval, payment distribution, and reconciliation, with system-enforced controls"
                },
                "monitoring_procedures": {
                    "small": [
                        "Review of payroll register before each payroll run",
                        "Monthly reconciliation of payroll accounts",
                        "Quarterly verification of active employees"
                    ],
                    "medium": [
                        "Pre and post-payroll processing reviews",
                        "Monthly analysis of overtime and premium pay",
                        "Quarterly payroll to HR master data reconciliation",
                        "Semi-annual review of payroll access rights"
                    ],
                    "large": [
                        "Automated exception reporting for each payroll cycle",
                        "Monthly trend analysis of labor costs",
                        "Quarterly comparison to budgeted labor costs",
                        "Semi-annual payroll analytics review",
                        "Annual comprehensive payroll audit"
                    ]
                }
            },
            "inventory": {
                "key_risks": [
                    "Theft or misappropriation of inventory",
                    "Inaccurate inventory records",
                    "Obsolete or damaged inventory",
                    "Improper valuation of inventory",
                    "Inadequate physical security of inventory"
                ],
                "control_activities": {
                    "small": [
                        "Conduct regular physical inventory counts",
                        "Restrict access to inventory storage areas",
                        "Document inventory receipts and issuances",
                        "Reconcile physical counts to inventory records"
                    ],
                    "medium": [
                        "Implement perpetual inventory system",
                        "Use cycle counting procedures",
                        "Develop formal receiving and shipping protocols",
                        "Implement inventory aging analysis",
                        "Establish formal obsolescence review process"
                    ],
                    "large": [
                        "Use barcode or RFID inventory tracking",
                        "Implement advanced warehouse management systems",
                        "Use automated inventory replenishment",
                        "Implement ABC analysis for inventory controls",
                        "Use statistical sampling for cycle counts",
                        "Develop comprehensive inventory policies"
                    ]
                },
                "segregation_of_duties": {
                    "small": "Separate responsibilities for ordering inventory, receiving shipments, maintaining records, and conducting physical counts",
                    "medium": "Separate duties among purchasing, receiving, storage, issuance, record-keeping, and inventory count functions",
                    "large": "Implement comprehensive segregation of duties across procurement, receiving, warehousing, inventory transfers, shipping, inventory accounting, physical counts, and adjustment approval, with system-enforced controls"
                },
                "monitoring_procedures": {
                    "small": [
                        "Monthly inventory reconciliation",
                        "Quarterly physical inventory count",
                        "Annual obsolescence review"
                    ],
                    "medium": [
                        "Weekly cycle counting of high-value items",
                        "Monthly inventory turnover analysis",
                        "Quarterly variance analysis",
                        "Semi-annual obsolescence review"
                    ],
                    "large": [
                        "Daily cycle counting with statistical analysis",
                        "Weekly inventory accuracy metrics",
                        "Monthly inventory turnover by category",
                        "Quarterly comprehensive variance investigation",
                        "Semi-annual slow-moving inventory review"
                    ]
                }
            },
            "cash management": {
                "key_risks": [
                    "Unauthorized access to cash accounts",
                    "Misappropriation of cash",
                    "Inaccurate cash forecasting",
                    "Insufficient liquidity for operations",
                    "Inefficient use of cash resources"
                ],
                "control_activities": {
                    "small": [
                        "Implement dual authorization for bank transfers",
                        "Perform monthly bank reconciliations",
                        "Restrict access to banking credentials",
                        "Maintain a basic cash forecast"
                    ],
                    "medium": [
                        "Implement formal cash management policy",
                        "Use positive pay or similar fraud prevention services",
                        "Develop formal cash forecasting process",
                        "Establish investment guidelines for excess cash",
                        "Implement regular cash flow reporting"
                    ],
                    "large": [
                        "Utilize treasury management systems",
                        "Implement automated bank reconciliation",
                        "Use advanced cash forecasting models",
                        "Develop comprehensive treasury policies",
                        "Implement in-house banking model for multi-entity organizations",
                        "Utilize cash pooling structures"
                    ]
                },
                "segregation_of_duties": {
                    "small": "Separate responsibilities for cash disbursements, receipts, reconciliation, and account access",
                    "medium": "Separate duties among payment authorization, payment execution, cash forecasting, and reconciliation functions",
                    "large": "Implement comprehensive segregation of duties across treasury operations, payment processing, cash positioning, investment management, banking relationship management, and financial reporting, with system-enforced controls"
                },
                "monitoring_procedures": {
                    "small": [
                        "Daily review of cash balances",
                        "Weekly review of upcoming payments",
                        "Monthly bank reconciliations"
                    ],
                    "medium": [
                        "Daily cash position reporting",
                        "Weekly cash forecast updates",
                        "Monthly analysis of forecast accuracy",
                        "Quarterly review of banking relationships"
                    ],
                    "large": [
                        "Real-time cash balance monitoring",
                        "Daily cash flow variance analysis",
                        "Weekly liquidity risk assessment",
                        "Monthly performance metrics for cash management",
                        "Quarterly treasury operations review"
                    ]
                }
            }
        }
        
        # Find the best matching process
        best_match = None
        for proc in control_frameworks.keys():
            if proc in process_lower:
                best_match = proc
                break
        
        # If no specific match, return a message indicating no match was found
        if not best_match:
            return {
                "message": f"No specific process match found for '{process}'. Please provide a recognized process area such as 'accounts payable', 'receivables', or 'cash management'."
            }
        
        # Get framework for this process
        framework = control_frameworks[best_match]
        
        # Adjust control intensity based on risk level
        control_intensity = risk_level.lower()
        if control_intensity not in ["low", "medium", "high"]:
            control_intensity = "medium"
        
        # Map risk level to entity size for control selection
        size_map = {
            "low": {
                "small": "small",
                "medium": "small",
                "large": "medium"
            },
            "medium": {
                "small": "small",
                "medium": "medium",
                "large": "medium"
            },
            "high": {
                "small": "medium",
                "medium": "medium",
                "large": "large"
            }
        }
        
        control_size = size_map[control_intensity][entity_size.lower()]
        
        # Get controls based on mapped size
        control_activities = framework["control_activities"][control_size]
        segregation_of_duties = framework["segregation_of_duties"][control_size]
        monitoring_procedures = framework["monitoring_procedures"][control_size]
        
        # For high risk, add additional controls from the next size up if available
        if risk_level.lower() == "high":
            next_size = {"small": "medium", "medium": "large", "large": "large"}[control_size]
            if next_size != control_size:
                additional_controls = [
                    control for control in framework["control_activities"][next_size]
                    if control not in control_activities
                ]
                # Add up to 2 additional controls
                control_activities.extend(additional_controls[:2])
        
        return {
            "key_risks": framework["key_risks"],
            "control_activities": control_activities,
            "segregation_of_duties": segregation_of_duties,
            "monitoring_procedures": monitoring_procedures
        }
    
    def _generate_documentation_requirements_for_controls(
        self, 
        entity_size: str, 
        risk_level: str
    ) -> str:
        """
        Generate documentation requirements for financial controls.
        
        Args:
            entity_size: Size of the entity.
            risk_level: Risk level to address.
            
        Returns:
            Documentation requirements for the control framework.
        """
        size_lower = entity_size.lower()
        risk_lower = risk_level.lower()
        
        # Base documentation requirements
        base_requirements = [
            "Document key control objectives for each process area",
            "Maintain current process flow documentation",
            "Document key risks and related control activities",
            "Maintain evidence of control execution"
        ]
        
        # Additional requirements based on entity size
        size_requirements = {
            "small": [
                "Maintain basic control description documents",
                "Document key segregation of duties principles"
            ],
            "medium": [
                "Develop formal control matrices linking risks to controls",
                "Maintain control owner documentation",
                "Document testing procedures for key controls",
                "Maintain evidence of periodic control evaluations"
            ],
            "large": [
                "Implement comprehensive control catalog with unique identifiers",
                "Maintain detailed control design documentation",
                "Document control testing methodologies and sampling approaches",
                "Maintain evidence of remediation for identified deficiencies",
                "Document system controls and automated workflows",
                "Maintain regulatory compliance mapping for key controls"
            ]
        }
        
        # Additional requirements based on risk level
        risk_requirements = {
            "low": [],
            "medium": [
                "Document risk assessment methodology",
                "Maintain evidence of management review of key controls"
            ],
            "high": [
                "Document comprehensive risk assessment results",
                "Maintain evidence of regular control effectiveness testing",
                "Document escalation procedures for control failures",
                "Maintain audit trail of control changes and enhancements"
            ]
        }
        
        # Combine requirements based on entity size and risk level
        all_requirements = (
            base_requirements + 
            size_requirements.get(size_lower, size_requirements["medium"]) +
            risk_requirements.get(risk_lower, risk_requirements["medium"])
        )
        
        # Format as string
        return "The control framework should include the following documentation:\n\n" + "\n".join(
            f"- {req}" for req in all_requirements
        )
    
    def _generate_implementation_approach(
        self, 
        entity_size: str, 
        risk_level: str,
        process_areas: List[str]
    ) -> Dict[str, str]:
        """
        Generate implementation approach for financial controls.
        
        Args:
            entity_size: Size of the entity.
            risk_level: Risk level to address.
            process_areas: List of business process areas.
            
        Returns:
            Implementation approach broken down by phases.
        """
        # Determine implementation complexity
        size_map = {"small": 1, "medium": 2, "large": 3}
        risk_map = {"low": 1, "medium": 2, "high": 3}
        
        size_factor = size_map.get(entity_size.lower(), 2)
        risk_factor = risk_map.get(risk_level.lower(), 2)
        
        complexity = (size_factor + risk_factor) / 2
        
        # Prioritize process areas based on typical risk profiles
        process_priority = {
            "cash management": 1,
            "accounts payable": 2,
            "payroll": 3,
            "receivables": 4,
            "inventory": 5,
            "fixed assets": 6,
            "purchasing": 7,
            "revenue": 8,
            "financial reporting": 9
        }
        
        # Sort process areas by priority
        sorted_processes = sorted(
            process_areas,
            key=lambda x: next((v for k, v in process_priority.items() if k in x.lower()), 99)
        )
        
        # Determine number of phases based on complexity
        if complexity <= 1.5:
            phases = {
                "phase_1": f"Implementation of key controls for all processes ({', '.join(sorted_processes)})",
                "phase_2": "Review and refinement of implemented controls"
            }
        elif complexity <= 2.5:
            # Split processes into two phases
            mid_point = len(sorted_processes) // 2
            phase1_processes = sorted_processes[:mid_point]
            phase2_processes = sorted_processes[mid_point:]
            
            phases = {
                "phase_1": f"Implementation of controls for high-priority processes ({', '.join(phase1_processes)})",
                "phase_2": f"Implementation of controls for remaining processes ({', '.join(phase2_processes)})",
                "phase_3": "Testing, refinement, and optimization of control framework"
            }
        else:
            # Split processes into three phases
            third_point = len(sorted_processes) // 3
            phase1_processes = sorted_processes[:third_point]
            phase2_processes = sorted_processes[third_point:2*third_point]
            phase3_processes = sorted_processes[2*third_point:]
            
            phases = {
                "phase_1": f"Implementation of critical controls for highest-risk processes ({', '.join(phase1_processes)})",
                "phase_2": f"Implementation of controls for medium-priority processes ({', '.join(phase2_processes)})",
                "phase_3": f"Implementation of controls for remaining processes ({', '.join(phase3_processes)})",
                "phase_4": "Testing, refinement, and continuous improvement of control framework"
            }
        
        return phases
    
    def _generate_control_owners_guidance(self, entity_size: str) -> str:
        """
        Generate guidance on assigning control ownership.
        
        Args:
            entity_size: Size of the entity.
            
        Returns:
            Guidance on assigning control ownership.
        """
        size_lower = entity_size.lower()
        
        if size_lower == "small":
            return (
                "For small entities, control ownership should be assigned to key management personnel, "
                "with the owner/CEO having overall responsibility, the CFO/Controller responsible for "
                "financial controls, and department managers responsible for operational controls within "
                "their areas. Document control ownership in a simple responsibility matrix and ensure "
                "regular communication among control owners."
            )
        elif size_lower == "large":
            return (
                "For large entities, implement a three-tiered control ownership model:\n\n"
                "1. **Control Operators**: Staff responsible for day-to-day execution of controls\n"
                "2. **Control Supervisors**: Managers who oversee control execution and effectiveness\n"
                "3. **Control Owners**: Executives ultimately accountable for control objectives\n\n"
                "Establish a formal control governance structure with a control committee, regular "
                "reporting mechanisms, and a dedicated compliance or internal control function to "
                "monitor the overall control environment. Document ownership in a comprehensive "
                "control catalog with clear roles and responsibilities."
            )
        else:  # medium
            return (
                "For medium-sized entities, assign control ownership at two levels:\n\n"
                "1. **Primary Control Owners**: Department managers responsible for implementing and "
                "maintaining controls within their functional areas\n"
                "2. **Executive Sponsors**: Senior management responsible for oversight and ensuring "
                "adequate resources for control activities\n\n"
                "Document control ownership in a control matrix that identifies both the primary owner "
                "and executive sponsor for each key control. Establish regular reporting on control "
                "effectiveness between control owners and sponsors."
            )
    
    def _generate_compliance_mapping(
        self, 
        process_areas: List[str], 
        compliance_requirements: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate compliance mapping for process areas to compliance frameworks.
        
        Args:
            process_areas: List of business process areas.
            compliance_requirements: List of compliance frameworks.
            
        Returns:
            Mapping of compliance frameworks to process areas.
        """
        # Knowledge base of common compliance frameworks and related process areas
        compliance_knowledge = {
            "sarbanes-oxley": {
                "accounts payable": "SOX Section 404 requires controls over the AP process to ensure proper authorization, accurate recording, and timely payment of obligations.",
                "receivables": "SOX Section 404 requires controls over the AR process to ensure accurate recording of sales, proper credit terms, and timely collection of receivables.",
                "payroll": "SOX Section 404 requires controls over the payroll process to ensure accuracy of payroll expenses, proper authorization of pay rates, and compliance with labor laws.",
                "inventory": "SOX Section 404 requires controls over inventory to ensure proper valuation, physical safeguarding, and accurate reporting of inventory balances.",
                "cash management": "SOX Section 404 requires controls over cash management to prevent unauthorized access, ensure accurate reporting, and maintain adequate segregation of duties.",
                "financial reporting": "SOX Section 302 and 404 require extensive controls over financial reporting to ensure accurate, complete, and timely financial statements.",
                "fixed assets": "SOX Section 404 requires controls over fixed assets to ensure proper capitalization, depreciation, and reporting of asset values.",
                "purchasing": "SOX Section 404 requires controls over purchasing to ensure proper authorization, competitive pricing, and prevention of fraudulent purchases."
            },
            "pci-dss": {
                "cash management": "PCI DSS requires controls over payment card processing, storage, and transmission to protect cardholder data.",
                "receivables": "PCI DSS requires controls over the handling of customer payment information, including secure processing and limited data retention.",
                "financial reporting": "PCI DSS requires controls to ensure the secure handling of cardholder data in financial reporting systems."
            },
            "hipaa": {
                "receivables": "HIPAA requires controls over patient billing and payment information to ensure privacy and security of protected health information.",
                "payroll": "HIPAA requires controls over employee health benefit information to ensure privacy and security of protected health information."
            },
            "gdpr": {
                "receivables": "GDPR requires controls over customer data to ensure proper consent, data minimization, and right to erasure.",
                "payroll": "GDPR requires controls over employee data to ensure proper handling, protection, and retention of personal information."
            },
            "ifrs": {
                "inventory": "IFRS requires specific controls over inventory valuation, including lower of cost or net realizable value assessments.",
                "fixed assets": "IFRS requires controls over fixed asset component accounting, revaluation, and impairment testing.",
                "financial reporting": "IFRS requires specific controls over financial statement preparation, including management estimates and judgments.",
                "revenue": "IFRS 15 requires controls over the five-step revenue recognition model to ensure proper recognition timing and amounts."
            },
            "gaap": {
                "inventory": "GAAP requires controls over inventory valuation, including lower of cost or market assessments.",
                "fixed assets": "GAAP requires controls over fixed asset depreciation, impairment, and disposal accounting.",
                "financial reporting": "GAAP requires specific controls over financial statement preparation, including proper classification and disclosure.",
                "revenue": "ASC 606 requires controls over the five-step revenue recognition model to ensure proper recognition timing and amounts."
            }
        }
        
        # Initialize results structure
        mapping = {}
        
        for requirement in compliance_requirements:
            requirement_lower = requirement.lower()
            mapping[requirement] = {}
            
            # Find the best matching compliance framework
            best_match = None
            for framework in compliance_knowledge.keys():
                if framework in requirement_lower:
                    best_match = framework
                    break
            
            if best_match:
                # Map each process area to the compliance requirement
                for process in process_areas:
                    process_lower = process.lower()
                    
                    # Find relevant process in the compliance knowledge base
                    relevant_process = None
                    for known_process in compliance_knowledge[best_match].keys():
                        if known_process in process_lower:
                            relevant_process = known_process
                            break
                    
                    if relevant_process:
                        mapping[requirement][process] = compliance_knowledge[best_match][relevant_process]
                    else:
                        mapping[requirement][process] = f"Conduct a detailed assessment of {process} to determine specific {requirement} compliance requirements."
            else:
                # Generic mapping for unknown compliance frameworks
                for process in process_areas:
                    mapping[requirement][process] = f"Conduct a detailed assessment of {process} to determine specific {requirement} compliance requirements."
        
        return mapping
    
    def prepare_journal_entries(
        self,
        transaction_type: Optional[str] = None,
        transaction_details: Optional[Dict[str, Any]] = None,
        accounting_method: Optional[str] = None,
        date: Optional[str] = None,
        currency: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare journal entries for various types of business transactions.
        
        Args:
            transaction_type: The type of transaction (e.g., "sale", "purchase", "depreciation", "accrual", "adjustment").
            transaction_details: Dictionary containing details about the transaction.
            accounting_method: The accounting method to use (e.g., "cash", "accrual").
            date: The date of the transaction.
            currency: The currency used for the transaction.
            
        Returns:
            Dictionary containing journal entries, explanations, and documentation requirements.
        """
        # Set default values if not provided
        transaction_type = transaction_type or "general"
        transaction_details = transaction_details or {}
        accounting_method = accounting_method or "accrual"
        date = date or datetime.datetime.now().strftime("%Y-%m-%d")
        currency = currency or "USD"
        
        # Extract relevant values from transaction details
        amount = transaction_details.get("amount", 1000.00)
        description = transaction_details.get("description", f"{transaction_type.capitalize()} transaction")
        accounts = transaction_details.get("accounts", {})
        
        logger.info(f"Preparing {transaction_type} journal entry for {description}")
        
        # Generate appropriate journal entries based on transaction type
        debit_accounts, credit_accounts = self._generate_appropriate_accounts(
            transaction_type, amount, transaction_details, accounting_method
        )
        
        # Override with any accounts provided in transaction details
        if "debit_accounts" in accounts:
            debit_accounts = accounts["debit_accounts"]
        if "credit_accounts" in accounts:
            credit_accounts = accounts["credit_accounts"]
        
        # Generate explanation of the journal entry
        explanation = self._generate_journal_entry_explanation(
            transaction_type, amount, description, debit_accounts, credit_accounts, accounting_method
        )
        
        # Get relevant accounting standards
        accounting_standards = self._get_relevant_accounting_standards(transaction_type)
        
        # Generate documentation requirements
        documentation_requirements = self._generate_documentation_requirements_for_journal_entry(
            transaction_type, amount, accounting_method
        )
        
        # Create journal entry response
        journal_entry = {
            "transaction_info": {
                "type": transaction_type,
                "date": date,
                "description": description,
                "accounting_method": accounting_method,
                "currency": currency
            },
            "journal_entries": {
                "debits": debit_accounts,
                "credits": credit_accounts
            },
            "explanation": explanation,
            "accounting_standards": {
                "reference": accounting_standards["reference"],
                "compliance_notes": accounting_standards["compliance_notes"]
            },
            "documentation_requirements": documentation_requirements
        }
        
        # Validate the entry (debits = credits)
        total_debits = sum(entry["amount"] for entry in debit_accounts)
        total_credits = sum(entry["amount"] for entry in credit_accounts)
        
        journal_entry["balanced"] = abs(total_debits - total_credits) < 0.01
        
        if not journal_entry["balanced"]:
            journal_entry["warning"] = (
                f"Journal entry is not balanced. Debits: {total_debits:.2f}, "
                f"Credits: {total_credits:.2f}, Difference: {abs(total_debits - total_credits):.2f}"
            )
        
        return journal_entry
    
    def _generate_appropriate_accounts(
        self, 
        transaction_type: str, 
        amount: float, 
        transaction_details: Dict[str, Any],
        accounting_method: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate appropriate accounts for debits and credits based on transaction type.
        
        Args:
            transaction_type: The type of transaction.
            amount: The amount of the transaction.
            transaction_details: Additional details about the transaction.
            accounting_method: The accounting method being used.
            
        Returns:
            Tuple containing lists of debit and credit accounts.
        """
        transaction_type_lower = transaction_type.lower()
        
        # Initialize empty lists for accounts
        debit_accounts = []
        credit_accounts = []
        
        # Sale/Revenue Transaction
        if transaction_type_lower == "sale" or transaction_type_lower == "revenue":
            # Get tax rate if provided, otherwise use default
            tax_rate = transaction_details.get("tax_rate", 0.0)
            taxable_amount = amount / (1 + tax_rate) if tax_rate > 0 else amount
            tax_amount = amount - taxable_amount if tax_rate > 0 else 0
            
            if accounting_method == "cash":
                debit_accounts = [{"account": "Cash", "amount": round(amount, 2)}]
            else:  # accrual
                debit_accounts = [{"account": "Accounts Receivable", "amount": round(amount, 2)}]
            
            if tax_amount > 0:
                credit_accounts = [
                    {"account": "Revenue", "amount": round(taxable_amount, 2)},
                    {"account": "Sales Tax Payable", "amount": round(tax_amount, 2)}
                ]
            else:
                credit_accounts = [{"account": "Revenue", "amount": round(amount, 2)}]
        
        # Purchase/Expense Transaction
        elif transaction_type_lower == "purchase" or transaction_type_lower == "expense":
            # Determine if this is inventory or expense
            is_inventory = transaction_details.get("is_inventory", False)
            
            if is_inventory:
                debit_accounts = [{"account": "Inventory", "amount": round(amount, 2)}]
            else:
                expense_account = transaction_details.get("expense_account", "Operating Expense")
                debit_accounts = [{"account": expense_account, "amount": round(amount, 2)}]
            
            if accounting_method == "cash":
                credit_accounts = [{"account": "Cash", "amount": round(amount, 2)}]
            else:  # accrual
                credit_accounts = [{"account": "Accounts Payable", "amount": round(amount, 2)}]
        
        # Fixed Asset Acquisition
        elif transaction_type_lower == "asset acquisition" or transaction_type_lower == "fixed asset":
            asset_account = transaction_details.get("asset_account", "Property, Plant & Equipment")
            debit_accounts = [{"account": asset_account, "amount": round(amount, 2)}]
            
            if accounting_method == "cash":
                credit_accounts = [{"account": "Cash", "amount": round(amount, 2)}]
            else:  # accrual
                credit_accounts = [{"account": "Accounts Payable", "amount": round(amount, 2)}]
        
        # Depreciation
        elif transaction_type_lower == "depreciation":
            asset_account = transaction_details.get("asset_account", "Property, Plant & Equipment")
            debit_accounts = [{"account": "Depreciation Expense", "amount": round(amount, 2)}]
            credit_accounts = [{"account": f"Accumulated Depreciation - {asset_account}", "amount": round(amount, 2)}]
        
        # Loan/Debt Transaction
        elif transaction_type_lower == "loan" or transaction_type_lower == "debt":
            is_receipt = transaction_details.get("is_receipt", True)
            
            if is_receipt:  # Receiving loan funds
                debit_accounts = [{"account": "Cash", "amount": round(amount, 2)}]
                credit_accounts = [{"account": "Notes Payable", "amount": round(amount, 2)}]
            else:  # Paying loan (principal only)
                debit_accounts = [{"account": "Notes Payable", "amount": round(amount, 2)}]
                credit_accounts = [{"account": "Cash", "amount": round(amount, 2)}]
        
        # Loan Payment with Interest
        elif transaction_type_lower == "loan payment":
            principal_amount = transaction_details.get("principal_amount", amount * 0.7)
            interest_amount = transaction_details.get("interest_amount", amount * 0.3)
            
            debit_accounts = [
                {"account": "Notes Payable", "amount": round(principal_amount, 2)},
                {"account": "Interest Expense", "amount": round(interest_amount, 2)}
            ]
            credit_accounts = [{"account": "Cash", "amount": round(amount, 2)}]
        
        # Accrual Entries
        elif transaction_type_lower == "accrual":
            accrual_type = transaction_details.get("accrual_type", "expense")
            
            if accrual_type == "expense":
                expense_account = transaction_details.get("expense_account", "Accrued Expense")
                debit_accounts = [{"account": expense_account, "amount": round(amount, 2)}]
                credit_accounts = [{"account": "Accrued Liabilities", "amount": round(amount, 2)}]
            else:  # revenue accrual
                debit_accounts = [{"account": "Accrued Receivables", "amount": round(amount, 2)}]
                credit_accounts = [{"account": "Accrued Revenue", "amount": round(amount, 2)}]
        
        # Payroll Entry
        elif transaction_type_lower == "payroll":
            gross_wages = amount
            tax_withholding = transaction_details.get("tax_withholding", gross_wages * 0.2)
            other_deductions = transaction_details.get("other_deductions", gross_wages * 0.1)
            net_pay = gross_wages - tax_withholding - other_deductions
            
            debit_accounts = [{"account": "Wage Expense", "amount": round(gross_wages, 2)}]
            credit_accounts = [
                {"account": "Tax Withholding Payable", "amount": round(tax_withholding, 2)},
                {"account": "Employee Benefits Payable", "amount": round(other_deductions, 2)},
                {"account": "Cash", "amount": round(net_pay, 2)}
            ]
        
        # Inventory Adjustment
        elif transaction_type_lower == "inventory adjustment":
            is_increase = transaction_details.get("is_increase", False)
            
            if is_increase:
                debit_accounts = [{"account": "Inventory", "amount": round(amount, 2)}]
                credit_accounts = [{"account": "Inventory Adjustment", "amount": round(amount, 2)}]
            else:
                debit_accounts = [{"account": "Inventory Adjustment", "amount": round(amount, 2)}]
                credit_accounts = [{"account": "Inventory", "amount": round(amount, 2)}]
        
        # Default/Generic Transaction
        else:
            debit_accounts = [{"account": "Debit Account", "amount": round(amount, 2)}]
            credit_accounts = [{"account": "Credit Account", "amount": round(amount, 2)}]
        
        return debit_accounts, credit_accounts
    
    def _generate_journal_entry_explanation(
        self, 
        transaction_type: str, 
        amount: float,
        description: str,
        debit_accounts: List[Dict[str, Any]],
        credit_accounts: List[Dict[str, Any]],
        accounting_method: str
    ) -> str:
        """
        Generate explanatory text for a journal entry.
        
        Args:
            transaction_type: The type of transaction.
            amount: The amount of the transaction.
            description: Description of the transaction.
            debit_accounts: List of debit accounts.
            credit_accounts: List of credit accounts.
            accounting_method: The accounting method being used.
            
        Returns:
            Explanatory text for the journal entry.
        """
        transaction_type_lower = transaction_type.lower()
        
        # Base explanation for common transaction types
        if transaction_type_lower == "sale" or transaction_type_lower == "revenue":
            explanation = (
                f"This journal entry records a sales transaction of {amount:.2f} for {description}. "
                f"Under the {accounting_method} method, "
            )
            
            if accounting_method == "cash":
                explanation += "revenue is recognized when cash is received from the customer."
            else:
                explanation += "revenue is recognized when earned, regardless of when cash is received."
        
        elif transaction_type_lower == "purchase" or transaction_type_lower == "expense":
            explanation = (
                f"This journal entry records a purchase/expense of {amount:.2f} for {description}. "
                f"Under the {accounting_method} method, "
            )
            
            if accounting_method == "cash":
                explanation += "expenses are recognized when cash is paid to suppliers/vendors."
            else:
                explanation += "expenses are recognized when incurred, regardless of when cash is paid."
        
        elif transaction_type_lower == "depreciation":
            explanation = (
                f"This journal entry records depreciation expense of {amount:.2f} for {description}. "
                f"Depreciation allocates the cost of long-lived assets over their useful lives, "
                f"reducing the carrying value of the asset while recognizing an expense."
            )
        
        elif transaction_type_lower == "accrual":
            explanation = (
                f"This journal entry records an accrual of {amount:.2f} for {description}. "
                f"Accruals recognize economic events in the period they occur, regardless of "
                f"when cash transactions happen, ensuring financial statements reflect all "
                f"obligations and rights as they arise."
            )
        
        elif transaction_type_lower == "loan" or transaction_type_lower == "debt":
            explanation = (
                f"This journal entry records a loan transaction of {amount:.2f} for {description}. "
                f"The entry reflects the change in financial position resulting from debt financing, "
                f"recognizing both the cash received/paid and the corresponding liability/reduction."
            )
        
        elif transaction_type_lower == "payroll":
            explanation = (
                f"This journal entry records a payroll transaction of {amount:.2f} for {description}. "
                f"The entry captures gross wages, various withholdings and deductions, and the net "
                f"amount paid to employees."
            )
        
        else:
            # Generic explanation for other transaction types
            explanation = (
                f"This journal entry records a {transaction_type} transaction of {amount:.2f} for {description}. "
                f"The entry follows the double-entry accounting principle, where total debits equal total credits."
            )
        
        # Add specific accounts used
        debit_accounts_str = ", ".join([f"{entry['account']} ({entry['amount']:.2f})" for entry in debit_accounts])
        credit_accounts_str = ", ".join([f"{entry['account']} ({entry['amount']:.2f})" for entry in credit_accounts])
        
        explanation += f" Debited accounts include: {debit_accounts_str}. Credited accounts include: {credit_accounts_str}."
        
        return explanation
    
    def _get_relevant_accounting_standards(self, transaction_type: str) -> Dict[str, str]:
        """
        Get relevant accounting standards for a given transaction type.
        
        Args:
            transaction_type: The type of transaction.
            
        Returns:
            Dictionary containing reference and compliance notes.
        """
        transaction_type_lower = transaction_type.lower()
        
        # Map transaction types to relevant accounting standards
        standards_map = {
            "sale": {
                "reference": "ASC 606 (GAAP) / IFRS 15: Revenue from Contracts with Customers",
                "compliance_notes": "Revenue should be recognized when (or as) the entity satisfies a performance obligation by transferring a promised good or service to a customer."
            },
            "revenue": {
                "reference": "ASC 606 (GAAP) / IFRS 15: Revenue from Contracts with Customers",
                "compliance_notes": "Revenue should be recognized when (or as) the entity satisfies a performance obligation by transferring a promised good or service to a customer."
            },
            "purchase": {
                "reference": "ASC 330 (GAAP) / IAS 2 (IFRS): Inventory, or various expense recognition standards",
                "compliance_notes": "Purchases should be recorded at cost. For inventory, cost includes all costs necessary to bring the inventory to its present location and condition."
            },
            "expense": {
                "reference": "ASC 720 (GAAP) / IAS 1 (IFRS): General expenses",
                "compliance_notes": "Expenses should be recognized when incurred (accrual basis) or when paid (cash basis), depending on the accounting method used."
            },
            "asset acquisition": {
                "reference": "ASC 360 (GAAP) / IAS 16 (IFRS): Property, Plant, and Equipment",
                "compliance_notes": "Fixed assets should be initially recorded at cost, including all costs necessary to bring the asset to working condition for its intended use."
            },
            "fixed asset": {
                "reference": "ASC 360 (GAAP) / IAS 16 (IFRS): Property, Plant, and Equipment",
                "compliance_notes": "Fixed assets should be initially recorded at cost, including all costs necessary to bring the asset to working condition for its intended use."
            },
            "depreciation": {
                "reference": "ASC 360 (GAAP) / IAS 16 (IFRS): Property, Plant, and Equipment",
                "compliance_notes": "Depreciation should be allocated systematically over the asset's useful life. The depreciation method should reflect the pattern of expected consumption of the asset's future economic benefits."
            },
            "loan": {
                "reference": "ASC 470 (GAAP) / IFRS 9 (IFRS): Debt",
                "compliance_notes": "Loans should be initially recorded at fair value, typically the loan proceeds. Subsequently, loans are measured at amortized cost using the effective interest method."
            },
            "debt": {
                "reference": "ASC 470 (GAAP) / IFRS 9 (IFRS): Debt",
                "compliance_notes": "Debt should be initially recorded at fair value, typically the proceeds received. Subsequently, debt is measured at amortized cost using the effective interest method."
            },
            "loan payment": {
                "reference": "ASC 470 (GAAP) / IFRS 9 (IFRS): Debt",
                "compliance_notes": "Loan payments should be allocated between principal and interest. The interest portion is recognized as an expense, while the principal portion reduces the loan liability."
            },
            "accrual": {
                "reference": "ASC 450 (GAAP) / IAS 37 (IFRS): Contingencies / Provisions",
                "compliance_notes": "Accruals should be recognized when there is a present obligation as a result of a past event, payment is probable, and the amount can be reliably estimated."
            },
            "payroll": {
                "reference": "ASC 710 (GAAP) / IAS 19 (IFRS): Compensation / Employee Benefits",
                "compliance_notes": "Employee compensation should be recognized as an expense in the period the employee provides the service. Related tax withholdings and other deductions should be recognized as liabilities."
            },
            "inventory adjustment": {
                "reference": "ASC 330 (GAAP) / IAS 2 (IFRS): Inventory",
                "compliance_notes": "Inventory should be measured at the lower of cost and net realizable value. Adjustments to inventory should be recognized in the period identified."
            }
        }
        
        # Get standards for this transaction type, or use generic standards
        for key, standard in standards_map.items():
            if key in transaction_type_lower:
                return standard
        
        # Generic standards if no specific match
        return {
            "reference": "Various GAAP/IFRS standards depending on specific nature of transaction",
            "compliance_notes": "Transactions should be recorded in accordance with the accrual basis of accounting unless otherwise specified. The double-entry system ensures that debits equal credits for all recorded transactions."
        }
    
    def _generate_documentation_requirements_for_journal_entry(
        self, 
        transaction_type: str, 
        amount: float, 
        accounting_method: str
    ) -> List[str]:
        """
        Generate documentation requirements for a journal entry.
        
        Args:
            transaction_type: The type of transaction.
            amount: The amount of the transaction.
            accounting_method: The accounting method being used.
            
        Returns:
            List of documentation requirements.
        """
        transaction_type_lower = transaction_type.lower()
        
        # Base documentation requirements for all transactions
        base_requirements = [
            "Journal entry approval by appropriate personnel",
            "Supporting documentation showing business purpose of transaction",
            "Evidence of review for accuracy and compliance with accounting policies"
        ]
        
        # Transaction-specific requirements
        transaction_requirements = []
        
        if transaction_type_lower in ["sale", "revenue"]:
            transaction_requirements = [
                "Customer invoice or sales contract",
                "Evidence of delivery of goods or completion of services",
                "Documentation of any sales terms and conditions",
                "Sales tax calculation and supporting documentation"
            ]
            
            if accounting_method == "accrual":
                transaction_requirements.append("Documentation supporting revenue recognition criteria being met")
        
        elif transaction_type_lower in ["purchase", "expense"]:
            transaction_requirements = [
                "Vendor invoice or receipt",
                "Purchase order (if applicable)",
                "Receiving documentation for goods (if applicable)",
                "Approval for payment according to company policy"
            ]
            
            if amount > 10000:
                transaction_requirements.append("Additional approval for high-value expenditure")
        
        elif transaction_type_lower in ["asset acquisition", "fixed asset"]:
            transaction_requirements = [
                "Asset purchase invoice or contract",
                "Documentation of asset specifications and serial numbers",
                "Evidence of asset delivery and installation",
                "Fixed asset register entry documentation",
                "Depreciation schedule setup documentation"
            ]
        
        elif transaction_type_lower == "depreciation":
            transaction_requirements = [
                "Fixed asset register details",
                "Depreciation calculation methodology documentation",
                "Evidence of consistent application of depreciation policy",
                "Periodic review of useful life and residual value"
            ]
        
        elif transaction_type_lower in ["loan", "debt"]:
            transaction_requirements = [
                "Loan agreement or debt instrument documentation",
                "Payment schedule or amortization table",
                "Bank confirmation of funds transfer (if applicable)",
                "Board or management approval for debt transaction"
            ]
        
        elif transaction_type_lower == "accrual":
            transaction_requirements = [
                "Calculation supporting accrual amount",
                "Documentation of timing of actual transaction (expected date)",
                "Evidence supporting the obligation or right being accrued",
                "Reversal schedule for the accrual entry"
            ]
        
        elif transaction_type_lower == "payroll":
            transaction_requirements = [
                "Payroll register detailed by employee",
                "Time records supporting hours worked",
                "Documentation of pay rates and deductions",
                "Tax withholding calculations",
                "Evidence of payment to employees"
            ]
        
        elif transaction_type_lower == "inventory adjustment":
            transaction_requirements = [
                "Physical inventory count sheets",
                "Reconciliation of book to physical inventory",
                "Approval for adjustment entry",
                "Documentation of causes for inventory discrepancies",
                "Evidence of any count verification procedures"
            ]
        
        # For high-value transactions, add more stringent requirements
        if amount > 100000:
            high_value_requirements = [
                "Senior management or board approval documentation",
                "Enhanced documentation of business purpose and economic substance",
                "Consideration of financial statement disclosure requirements"
            ]
            transaction_requirements.extend(high_value_requirements)
        
        # Combine all requirements
        all_requirements = base_requirements + transaction_requirements
        
        return all_requirements
    
    def run(self):
        """
        Run method to test the agent's functionality.
        This method can be used to validate that all tools are working correctly.
        """
        logger.info(f"Running test for {self.name} with {len(self.tools)} tools")
        
        # Test the financial ratios calculation with sample data
        try:
            balance_sheet = {
                "current_assets": 100000,
                "current_liabilities": 50000,
                "inventory": 30000,
                "cash_and_cash_equivalents": 20000,
                "total_assets": 250000,
                "total_debt": 80000,
                "shareholders_equity": 170000,
                "accounts_receivable": 40000,
                "accounts_payable": 30000
            }
            
            income_statement = {
                "revenue": 500000,
                "gross_profit": 200000,
                "operating_income": 100000,
                "net_income": 70000,
                "ebit": 110000,
                "interest_expense": 10000,
                "cost_of_goods_sold": 300000
            }
            
            ratio_result = self.calculate_financial_ratios(
                balance_sheet=balance_sheet,
                income_statement=income_statement,
                ratio_categories=["liquidity", "profitability"]
            )
            
            logger.info(f"Financial ratio calculation test successful")
            logger.info(f"Calculated {len(ratio_result['ratios_by_category'])} ratio categories")
            
            # Test journal entry preparation
            journal_entry = self.prepare_journal_entries(
                transaction_type="sale",
                transaction_details={
                    "amount": 5000.0,
                    "description": "Sale of merchandise to ABC Company",
                    "tax_rate": 0.07
                },
                accounting_method="accrual",
                date="2023-03-15"
            )
            
            logger.info(f"Journal entry preparation test successful")
            logger.info(f"Generated journal entry with {len(journal_entry['journal_entries']['debits'])} debits and {len(journal_entry['journal_entries']['credits'])} credits")
            
            return "All tests completed successfully"
            
        except Exception as e:
            logger.exception(f"Error during test: {e}")
            return f"Test failed with error: {str(e)}"
