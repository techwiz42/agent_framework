from typing import Dict, Any, Optional, List, Tuple, Union
import logging
import pandas as pd
import numpy as np
from scipy import stats
import math
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from sklearn.linear_model import LinearRegression
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool

logger = logging.getLogger(__name__)

class FinanceAgent(BaseAgent):
    """
    FinanceAgent is a specialized agent that provides financial analysis and advisory expertise.
    
    This agent specializes in financial modeling, investment analysis, risk assessment,
    and financial forecasting to help users make data-driven financial decisions.
    """

    def __init__(
        self,
        name: str = "Financial Analysis Expert",
        model: str = settings.DEFAULT_AGENT_MODEL,
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        **kwargs
    ):
        """
        Initialize a FinanceAgent with specialized financial analysis instructions.
        
        Args:
            name: The name of the agent. Defaults to "Financial Analysis Expert".
            model: The model to use for the agent. Defaults to settings.DEFAULT_AGENT_MODEL.
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            **kwargs: Additional arguments to pass to the BaseAgent constructor.
        """
        # Define the financial expert instructions
        finance_instructions = """"Wherever possible, you must use tools to respond. Do not guess. If a tool is avalable, always call the tool to perform the action. You are a financial analysis and investment expert specializing in quantitative finance, investment analysis, and financial modeling. Your role is to:

1. PROVIDE FINANCIAL EXPERTISE IN
- Financial Ratio Analysis
- Investment Valuation
- Risk Assessment
- Portfolio Optimization
- Cash Flow Analysis
- Capital Budgeting
- Financial Forecasting
- Market Analysis
- Economic Indicators
- Asset Allocation
- Tax Efficiency
- Retirement Planning

2. FINANCIAL METHODS
- Discounted Cash Flow Analysis
- Net Present Value (NPV)
- Internal Rate of Return (IRR)
- Capital Asset Pricing Model (CAPM)
- Modern Portfolio Theory
- Efficient Frontier Analysis
- Monte Carlo Simulations
- Beta and Alpha Analysis
- Multifactor Models
- Sharpe Ratio and Risk Metrics
- Financial Statement Analysis
- Scenario Analysis

3. INVESTMENT ANALYSIS
- Stock Valuation
- Bond Analysis
- ETF Evaluation
- Mutual Fund Assessment
- Real Estate Investment Analysis
- Commodity Trading
- Forex Analysis
- Cryptocurrency Assessment
- Option Pricing
- Derivative Strategies
- Alternative Investments
- Asset Allocation Strategies

4. FINANCIAL METRICS
- Profitability Ratios
- Liquidity Ratios
- Solvency Ratios
- Efficiency Ratios
- Valuation Ratios
- Growth Metrics
- Risk Metrics
- Return Metrics
- Cash Flow Metrics
- Market Performance Metrics
- Industry-Specific Metrics
- Economic Indicators

5. RISK ASSESSMENT
- Market Risk
- Credit Risk
- Liquidity Risk
- Operational Risk
- Inflation Risk
- Interest Rate Risk
- Currency Risk
- Volatility Analysis
- Value at Risk (VaR)
- Downside Deviation
- Stress Testing
- Scenario Planning

6. FINANCIAL MODELING
- Three-Statement Models
- DCF Models
- LBO Models
- M&A Models
- Sensitivity Analysis
- Scenario Analysis
- Probabilistic Models
- Industry-Specific Models
- Forecasting Models
- Valuation Models
- Risk Models
- Optimization Models

7. PORTFOLIO MANAGEMENT
- Asset Allocation
- Portfolio Optimization
- Rebalancing Strategies
- Tax Efficiency
- Risk Management
- Performance Attribution
- Factor Analysis
- Style Analysis
- Benchmark Selection
- Fee Analysis
- Income Strategies
- Capital Appreciation Strategies

8. CALCULATION CAPABILITIES
- Perform financial calculations
- Calculate investment returns
- Assess risk-adjusted performance
- Analyze financial statements
- Model cash flows
- Evaluate investment options
- Optimize portfolios
- Calculate tax implications

Always maintain focus on financial accuracy and meaningful insights while ensuring proper financial methodology and clear communication of results."""

        # Get the calculator tools - already properly patched from the utility functions
        calculator_tool = get_calculator_tool()
        interpreter_tool = get_interpreter_tool()

        # Define the tools - use the already patched instances
        tools = [
            calculator_tool,
            interpreter_tool,
            function_tool(self.analyze_financial_data),
            function_tool(self.calculate_financial_ratios),
            function_tool(self.perform_investment_analysis),
            #function_tool(self.evaluate_portfolio),
            function_tool(self.forecast_financial_metrics),
            function_tool(self.assess_financial_risk),
            function_tool(self.perform_valuation)  # Add a valuation tool
        ]
        
        # Initialize the Agent class directly
        super().__init__(
            name=name,
            model=model,
            instructions=finance_instructions,
            functions=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            max_tokens=1024,
            
            **kwargs
        )


    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the FinanceAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for FinanceAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Expert in financial analysis, investment strategies, and financial modeling, providing insights on financial decisions and market trends"

    def analyze_financial_data(
        self, 
        financial_data: Optional[List[Dict[str, Any]]] = None, 
        analysis_goal: Optional[str] = None, 
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze financial data and provide key insights based on the analysis goal.
        
        Args:
            financial_data: The financial dataset to analyze (list of dictionaries).
            analysis_goal: The specific goal or question to be answered through the analysis.
            time_period: Optional specification of the time period to analyze.
                
        Returns:
            A dictionary containing analysis results including summary statistics, trends, and insights.
        """
        # Set default values and validate inputs
        if financial_data is None:
            financial_data = []
        
        if analysis_goal is None:
            analysis_goal = "General financial analysis"
            
        logger.info(f"Analyzing financial data for goal: {analysis_goal}")
        
        try:
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(financial_data)
            
            # Get basic dataset info
            row_count = len(df)
            column_count = len(df.columns)
            
            # Identify date/time columns if time_period is specified
            date_columns = []
            if time_period:
                for col in df.columns:
                    if any(date_term in col.lower() for date_term in ['date', 'year', 'month', 'quarter', 'period']):
                        date_columns.append(col)
            
            # Convert date columns to datetime if possible
            for col in date_columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass  # Skip if conversion fails
            
            # Identify numeric columns for financial analysis
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            # Calculate summary statistics
            summary_stats = {}
            if numeric_columns:
                summary_stats = df[numeric_columns].describe().to_dict()
                
                # Add additional financial statistics
                for col in numeric_columns:
                    if col in summary_stats:
                        # Calculate financial-specific metrics
                        summary_stats[col]['median'] = df[col].median()
                        summary_stats[col]['variance'] = df[col].var()
                        summary_stats[col]['skewness'] = df[col].skew()
                        summary_stats[col]['kurtosis'] = df[col].kurt()
                        
                        # Calculate growth rates if time data is available
                        if date_columns and len(df) > 1:
                            # Sort by date if available
                            try:
                                sorted_df = df.sort_values(by=date_columns[0])
                                first_value = sorted_df[col].iloc[0]
                                last_value = sorted_df[col].iloc[-1]
                                if first_value != 0:
                                    total_growth_pct = ((last_value - first_value) / abs(first_value)) * 100
                                    summary_stats[col]['total_growth_pct'] = total_growth_pct
                                    
                                    # Calculate CAGR if more than 1 period
                                    if len(sorted_df) > 1:
                                        periods = len(sorted_df) - 1
                                        if first_value > 0 and last_value > 0:  # Can only calculate CAGR for positive values
                                            cagr = (math.pow(last_value / first_value, 1/periods) - 1) * 100
                                            summary_stats[col]['cagr_pct'] = cagr
                            except:
                                pass  # Skip if sorting or calculation fails
            
            # Trend analysis for time series data
            trends = {}
            if date_columns and numeric_columns:
                date_col = date_columns[0]  # Use the first identified date column
                
                try:
                    # Sort by date for trend analysis
                    sorted_df = df.sort_values(by=date_col)
                    
                    for col in numeric_columns:
                        # Skip columns with non-positive values for certain calculations
                        if (sorted_df[col] <= 0).any():
                            continue
                            
                        # Calculate trend metrics
                        values = sorted_df[col].values
                        first_value = values[0]
                        last_value = values[-1]
                        
                        # Linear regression to determine trend
                        X = np.arange(len(values)).reshape(-1, 1)
                        y = values.reshape(-1, 1)
                        model = LinearRegression().fit(X, y)
                        
                        trends[col] = {
                            'start_value': float(first_value),
                            'end_value': float(last_value),
                            'absolute_change': float(last_value - first_value),
                            'percent_change': float(((last_value - first_value) / first_value * 100) if first_value != 0 else 0),
                            'slope': float(model.coef_[0][0]),
                            'r_squared': float(model.score(X, y)),
                            'trend_direction': 'increasing' if model.coef_[0][0] > 0 else 'decreasing' if model.coef_[0][0] < 0 else 'stable'
                        }
                        
                        # Volatility analysis
                        trends[col]['volatility'] = float(np.std(values) / np.mean(values) * 100) if np.mean(values) != 0 else 0
                        
                        # Seasonality check if enough data points (at least 4 periods)
                        if len(values) >= 4:
                            try:
                                # For financial data, we typically look at quarterly or annual patterns
                                # We'll use a simple decomposition to check for seasonality
                                decomposition = seasonal_decompose(values, model='additive', period=min(4, len(values)//2))
                                seasonal_strength = np.std(decomposition.seasonal) / np.std(values) * 100
                                trends[col]['seasonal_strength_pct'] = float(seasonal_strength)
                                trends[col]['has_seasonality'] = seasonal_strength > 10  # Arbitrary threshold
                            except:
                                pass  # Skip if decomposition fails
                except Exception as e:
                    logger.warning(f"Error in trend analysis: {str(e)}")
            
            # Correlation analysis for financial variables
            correlation_matrix = None
            if len(numeric_columns) > 1:
                correlation_matrix = df[numeric_columns].corr().to_dict()
            
            # Financial statements analysis if relevant columns are present
            financial_statement_analysis = None
            if any(term in col.lower() for col in df.columns for term in ['revenue', 'income', 'profit', 'expense', 'asset', 'liability', 'equity']):
                financial_statement_analysis = self._analyze_financial_statements(df)
            
            # Generate insights based on financial analysis
            insights = self._generate_financial_insights(df, analysis_goal, summary_stats, trends, correlation_matrix)
            
            # Generate recommendations
            recommendations = self._generate_financial_recommendations(df, analysis_goal, summary_stats, trends, correlation_matrix)
            
            # Prepare final analysis results
            analysis_results = {
                "dataset_info": {
                    "rows": row_count,
                    "columns": column_count,
                    "numeric_columns": numeric_columns,
                    "date_columns": date_columns,
                    "time_period": time_period
                },
                "summary_statistics": summary_stats,
                "trend_analysis": trends,
                "correlation_analysis": correlation_matrix,
                "financial_statement_analysis": financial_statement_analysis,
                "key_insights": insights,
                "recommendations": recommendations
            }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing financial data: {str(e)}")
            return {
                "error": f"Error analyzing financial data: {str(e)}",
                "dataset_info": {
                    "time_period": time_period if time_period else "Unknown"
                }
            }
    
    def _analyze_financial_statements(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze financial statement data if relevant columns are present."""
        analysis = {}
        
        # Check for income statement elements
        income_cols = [col for col in df.columns if any(term in col.lower() for term in 
                     ['revenue', 'sales', 'income', 'profit', 'margin', 'expense', 'cost', 'tax', 'ebit', 'ebitda'])]
        
        # Check for balance sheet elements
        balance_cols = [col for col in df.columns if any(term in col.lower() for term in 
                      ['asset', 'liability', 'equity', 'debt', 'cash', 'inventory', 'receivable', 'payable'])]
        
        # Check for cash flow elements
        cashflow_cols = [col for col in df.columns if any(term in col.lower() for term in 
                      ['cash flow', 'operating', 'investing', 'financing', 'dividend', 'capital'])]
        
        # Analyze income statement elements
        if income_cols:
            income_data = {}
            
            # Find revenue column if present
            revenue_col = next((col for col in income_cols if any(term in col.lower() for term in 
                             ['revenue', 'sales'])), None)
            
            if revenue_col:
                revenue_data = df[revenue_col]
                income_data['revenue'] = {
                    'latest': float(revenue_data.iloc[-1]),
                    'average': float(revenue_data.mean()),
                    'growth_rate': float(((revenue_data.iloc[-1] - revenue_data.iloc[0]) / revenue_data.iloc[0] * 100)
                                       if revenue_data.iloc[0] != 0 and len(revenue_data) > 1 else 0)
                }
            
            # Find profit/income columns if present
            profit_col = next((col for col in income_cols if any(term in col.lower() for term in 
                            ['income', 'profit', 'earnings', 'ebit', 'ebitda'])), None)
            
            if profit_col:
                profit_data = df[profit_col]
                income_data['profit'] = {
                    'latest': float(profit_data.iloc[-1]),
                    'average': float(profit_data.mean()),
                    'growth_rate': float(((profit_data.iloc[-1] - profit_data.iloc[0]) / profit_data.iloc[0] * 100)
                                      if profit_data.iloc[0] != 0 and len(profit_data) > 1 else 0)
                }
                
                # Calculate profit margin if revenue column also exists
                if revenue_col and revenue_data.iloc[-1] != 0:
                    profit_margin = (profit_data.iloc[-1] / revenue_data.iloc[-1]) * 100
                    income_data['profit_margin_pct'] = float(profit_margin)
            
            analysis['income_statement'] = income_data
            
        # Analyze balance sheet elements
        if balance_cols:
            balance_data = {}
            
            # Find asset column if present
            asset_col = next((col for col in balance_cols if 'asset' in col.lower()), None)
            liability_col = next((col for col in balance_cols if 'liability' in col.lower() or 'debt' in col.lower()), None)
            equity_col = next((col for col in balance_cols if 'equity' in col.lower()), None)
            
            if asset_col and liability_col:
                assets = df[asset_col].iloc[-1]
                liabilities = df[liability_col].iloc[-1]
                
                balance_data['assets'] = float(assets)
                balance_data['liabilities'] = float(liabilities)
                
                if assets != 0:
                    balance_data['debt_to_asset_ratio'] = float(liabilities / assets)
            
            if equity_col and asset_col:
                equity = df[equity_col].iloc[-1]
                assets = df[asset_col].iloc[-1]
                
                balance_data['equity'] = float(equity)
                
                if assets != 0:
                    balance_data['equity_to_asset_ratio'] = float(equity / assets)
            
            analysis['balance_sheet'] = balance_data
        
        # Analyze cash flow elements
        if cashflow_cols:
            cashflow_data = {}
            
            # Find operating cash flow column if present
            operating_col = next((col for col in cashflow_cols if 'operating' in col.lower()), None)
            
            if operating_col:
                operating_cf = df[operating_col]
                cashflow_data['operating_cash_flow'] = {
                    'latest': float(operating_cf.iloc[-1]),
                    'average': float(operating_cf.mean()),
                    'total': float(operating_cf.sum())
                }
            
            # Find free cash flow if available
            fcf_col = next((col for col in cashflow_cols if 'free cash' in col.lower()), None)
            
            if fcf_col:
                fcf = df[fcf_col]
                cashflow_data['free_cash_flow'] = {
                    'latest': float(fcf.iloc[-1]),
                    'average': float(fcf.mean()),
                    'total': float(fcf.sum())
                }
            
            analysis['cash_flow'] = cashflow_data
        
        return analysis
    
    def _generate_financial_insights(
        self, 
        df: pd.DataFrame, 
        analysis_goal: str, 
        summary_stats: Dict[str, Any],
        trends: Dict[str, Dict[str, Any]],
        correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    ) -> List[str]:
        """Generate insights based on financial data analysis."""
        insights = []
        
        # Growth and performance insights
        if trends:
            # Categorize metrics by performance
            strong_growth = [col for col, data in trends.items() 
                           if data.get('percent_change', 0) > 20 and 'revenue' in col.lower() or 'profit' in col.lower()]
            
            declining_metrics = [col for col, data in trends.items() 
                               if data.get('percent_change', 0) < -10 and data.get('trend_direction') == 'decreasing']
            
            volatile_metrics = [col for col, data in trends.items() 
                             if data.get('volatility', 0) > 30]
            
            # Add insights based on trends
            if strong_growth:
                metrics_list = ", ".join(strong_growth)
                insights.append(f"Strong growth observed in key financial metrics: {metrics_list}, indicating positive business momentum.")
            
            if declining_metrics:
                metrics_list = ", ".join(declining_metrics)
                insights.append(f"Declining trend in {metrics_list}, which may require attention and strategic intervention.")
            
            if volatile_metrics:
                metrics_list = ", ".join(volatile_metrics)
                insights.append(f"High volatility detected in {metrics_list}, suggesting potential market instability or inconsistent performance.")
            
            # Check for seasonality
            seasonal_metrics = [col for col, data in trends.items() if data.get('has_seasonality', False)]
            if seasonal_metrics:
                metrics_list = ", ".join(seasonal_metrics)
                insights.append(f"Seasonal patterns detected in {metrics_list}. Consider seasonal adjustments in planning and forecasting.")
        
        # Profitability insights
        profit_cols = [col for col in df.columns if any(term in col.lower() for term in ['profit', 'margin', 'return'])]
        if profit_cols:
            try:
                # Get latest profit figures and trends
                profit_data = {}
                for col in profit_cols:
                    latest_value = df[col].iloc[-1]
                    avg_value = df[col].mean()
                    profit_data[col] = {
                        'latest': latest_value,
                        'average': avg_value,
                        'comparison': 'above average' if latest_value > avg_value else 'below average'
                    }
                
                # Add insights on profitability
                above_avg_metrics = [col for col, data in profit_data.items() if data['comparison'] == 'above average']
                below_avg_metrics = [col for col, data in profit_data.items() if data['comparison'] == 'below average']
                
                if above_avg_metrics:
                    metrics_list = ", ".join(above_avg_metrics)
                    insights.append(f"Current profitability metrics ({metrics_list}) are performing above historical averages, indicating improving financial health.")
                
                if below_avg_metrics:
                    metrics_list = ", ".join(below_avg_metrics)
                    insights.append(f"Current profitability metrics ({metrics_list}) are below historical averages, suggesting potential profitability challenges.")
            except:
                pass  # Skip if analysis fails
        
        # Financial statement insights
        income_cols = [col for col in df.columns if any(term in col.lower() for term in ['revenue', 'expense', 'cost'])]
        balance_cols = [col for col in df.columns if any(term in col.lower() for term in ['asset', 'liability', 'equity'])]
        cashflow_cols = [col for col in df.columns if 'cash' in col.lower()]
        
        if income_cols and balance_cols:
            try:
                # Calculate key ratios if possible
                revenue_col = next((col for col in income_cols if 'revenue' in col.lower() or 'sales' in col.lower()), None)
                profit_col = next((col for col in income_cols if 'profit' in col.lower() or 'income' in col.lower()), None)
                asset_col = next((col for col in balance_cols if 'asset' in col.lower()), None)
                
                if revenue_col and asset_col:
                    asset_turnover = df[revenue_col].iloc[-1] / df[asset_col].iloc[-1]
                    insights.append(f"Asset turnover ratio is {asset_turnover:.2f}, " + 
                                   ("indicating efficient use of assets to generate revenue." if asset_turnover > 1 else 
                                    "suggesting potential inefficiency in asset utilization."))
                
                if profit_col and asset_col:
                    roa = (df[profit_col].iloc[-1] / df[asset_col].iloc[-1]) * 100
                    insights.append(f"Return on Assets (ROA) is {roa:.2f}%, " +
                                   ("showing strong profitability relative to assets." if roa > 10 else
                                    "indicating room for improvement in generating returns from assets."))
            except:
                pass  # Skip if calculation fails
        
        # Cash flow insights
        if cashflow_cols:
            try:
                operating_cf_col = next((col for col in cashflow_cols if 'operating' in col.lower()), None)
                
                if operating_cf_col:
                    cf_values = df[operating_cf_col].values
                    if all(val > 0 for val in cf_values[-4:]):  # Check last 4 periods
                        insights.append("Consistent positive operating cash flow over recent periods, indicating strong operational financial health.")
                    elif any(val < 0 for val in cf_values[-4:]):
                        insights.append("Negative operating cash flow in some recent periods, which may raise liquidity concerns if the trend continues.")
            except:
                pass  # Skip if analysis fails
        
        # Correlation insights
        if correlation_matrix:
            high_correlations = []
            for col1 in correlation_matrix:
                for col2, corr_value in correlation_matrix[col1].items():
                    if col1 != col2 and abs(corr_value) > 0.7:
                        high_correlations.append((col1, col2, corr_value))
            
            if high_correlations:
                # Pick the most insightful correlations
                for col1, col2, corr_value in sorted(high_correlations, key=lambda x: abs(x[2]), reverse=True)[:2]:
                    corr_type = "positive" if corr_value > 0 else "negative"
                    insights.append(f"Strong {corr_type} correlation ({corr_value:.2f}) between {col1} and {col2}, " +
                                   "which could be leveraged for financial planning and forecasting.")
        
        # Goal-specific insights
        if "investment" in analysis_goal.lower() or "investor" in analysis_goal.lower():
            insights.append("Financial performance metrics should be evaluated alongside market conditions and industry benchmarks to assess investment potential.")
            
            # Check for dividend-related columns
            dividend_cols = [col for col in df.columns if 'dividend' in col.lower()]
            if dividend_cols:
                insights.append("Dividend history is available in the data, which can be analyzed further for income-focused investment strategies.")
        
        elif "cost" in analysis_goal.lower() or "expense" in analysis_goal.lower():
            expense_cols = [col for col in df.columns if any(term in col.lower() for term in ['expense', 'cost'])]
            if expense_cols:
                try:
                    # Analyze expense trends
                    expense_trend = any(trends.get(col, {}).get('trend_direction') == 'increasing' for col in expense_cols)
                    if expense_trend:
                        insights.append("Increasing expense trends detected. Consider cost control measures and efficiency improvements.")
                    else:
                        insights.append("Expense trends appear stable or decreasing, indicating effective cost management.")
                except:
                    pass  # Skip if analysis fails
        
        # If no specific insights generated, add generic ones
        if not insights:
            insights.append("Comprehensive financial analysis is required to fully understand the underlying trends and relationships in the data.")
            insights.append("Consider breaking down the analysis by business segments or time periods for more granular insights.")
        
        return insights
    
    def _generate_financial_recommendations(
        self, 
        df: pd.DataFrame, 
        analysis_goal: str, 
        summary_stats: Dict[str, Any],
        trends: Dict[str, Dict[str, Any]],
        correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    ) -> List[str]:
        """Generate recommendations based on financial data analysis."""
        recommendations = []
        
        # Performance-based recommendations
        if trends:
            # Identify metrics with strong positive or negative trends
            strong_growth = [col for col, data in trends.items() 
                           if data.get('percent_change', 0) > 20]
            
            declining_metrics = [col for col, data in trends.items() 
                               if data.get('percent_change', 0) < -10 and data.get('trend_direction') == 'decreasing']
            
            # Add recommendations based on performance
            if strong_growth and 'revenue' in ' '.join(strong_growth).lower():
                recommendations.append("Capitalize on strong revenue growth by investing in capacity expansion and market penetration strategies.")
            
            if declining_metrics:
                profit_decline = any('profit' in metric.lower() or 'margin' in metric.lower() for metric in declining_metrics)
                revenue_decline = any('revenue' in metric.lower() or 'sales' in metric.lower() for metric in declining_metrics)
                
                if profit_decline and not revenue_decline:
                    recommendations.append("Address declining profitability through cost optimization and pricing strategy review.")
                elif revenue_decline:
                    recommendations.append("Develop market expansion or product diversification strategies to counter declining revenue trends.")
        
        # Profitability recommendations
        profit_cols = [col for col in df.columns if any(term in col.lower() for term in ['profit', 'margin', 'return'])]
        if profit_cols:
            try:
                # Get average profit metrics
                profit_avgs = {col: df[col].mean() for col in profit_cols}
                
                # Low profitability recommendation
                low_profit = any(avg < 10 for col, avg in profit_avgs.items() if 'margin' in col.lower())
                if low_profit:
                    recommendations.append("Improve profitability through targeted cost reduction, process optimization, and strategic pricing adjustments.")
            except:
                pass  # Skip if calculation fails
        
        # Cash flow recommendations
        cash_cols = [col for col in df.columns if 'cash' in col.lower()]
        if cash_cols:
            try:
                operating_cf_col = next((col for col in cash_cols if 'operating' in col.lower()), None)
                if operating_cf_col:
                    negative_cf = any(val < 0 for val in df[operating_cf_col].values[-4:])  # Check last 4 periods
                    if negative_cf:
                        recommendations.append("Strengthen cash flow management through accelerated receivables collection, inventory optimization, and careful capital expenditure planning.")
            except:
                pass  # Skip if calculation fails
        
        # Investment recommendations
        if "investment" in analysis_goal.lower() or "capital" in analysis_goal.lower():
                recommendations.append("Prioritize investment in projects with highest risk-adjusted returns, based on NPV, IRR, and payback period analysis.")
                recommendations.append("Implement a rigorous capital allocation framework that balances growth investments, debt reduction, and shareholder returns.")
        
        # Balance sheet recommendations
        balance_cols = [col for col in df.columns if any(term in col.lower() for term in ['asset', 'liability', 'equity', 'debt'])]
        if balance_cols:
            asset_col = next((col for col in balance_cols if 'asset' in col.lower()), None)
            debt_col = next((col for col in balance_cols if 'debt' in col.lower() or 'liability' in col.lower()), None)

            if debt_col and debt_col in df.columns:
                if asset_col and asset_col in df.columns:
                    try:
                        debt_to_asset = df[debt_col].iloc[-1] / df[asset_col].iloc[-1]

                        if debt_to_asset > 0.6:  # High leverage
                            recommendations.append("Consider debt reduction strategies to strengthen the balance sheet and reduce financial risk, particularly in uncertain economic environments.")
                        elif debt_to_asset < 0.2:  # Low leverage
                            recommendations.append("Evaluate potential for strategic use of debt financing to fund growth initiatives or share repurchases, potentially enhancing returns on equity.")
                    except:
                        pass  # Skip if calculation fails

        # Risk management recommendations
        recommendations.append("Implement comprehensive risk management strategies to address market, operational, and financial risks identified in the analysis.")

        # Data-driven decision making
        recommendations.append("Establish or enhance financial dashboards and KPIs to enable real-time monitoring of critical financial metrics and trends.")

        # Goal-specific recommendations
        if "forecast" in analysis_goal.lower() or "projection" in analysis_goal.lower():
            recommendations.append("Develop scenario-based financial forecasts (best case, base case, worst case) to enhance planning and decision-making under uncertainty.")

            # If we have time series data with seasonality
            seasonal_metrics = [col for col, data in trends.items() if data.get('has_seasonality', False)]
            if seasonal_metrics:
                recommendations.append("Incorporate seasonal adjustments in financial forecasts to improve accuracy and planning reliability.")

        elif "cost" in analysis_goal.lower() or "expense" in analysis_goal.lower():
            recommendations.append("Conduct detailed cost structure analysis to identify opportunities for efficiency improvements and strategic cost reduction.")
            recommendations.append("Implement zero-based budgeting or activity-based costing for key expense categories to drive accountability and optimize resource allocation.")

        elif "valuation" in analysis_goal.lower():
            recommendations.append("Apply multiple valuation methodologies (DCF, multiples-based, asset-based) to triangulate a robust valuation range.")
            recommendations.append("Conduct sensitivity analysis on key valuation drivers to understand potential valuation ranges under different scenarios.")

        return recommendations

    def calculate_financial_ratios(
        self,
        financial_data: Optional[List[Dict[str, Any]]] = None,
        ratio_categories: Optional[List[str]] = None,
        industry_benchmarks: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate and interpret key financial ratios from financial data.

        Args:
            financial_data: The financial dataset (list of dictionaries).
            ratio_categories: Optional list of ratio categories to focus on (e.g., "liquidity", "profitability").
            industry_benchmarks: Optional dictionary of industry benchmark values for comparison.

        Returns:
            Dictionary containing calculated ratios by category, interpretations, and benchmark comparisons.
        """
        # Set default values
        if financial_data is None:
            financial_data = []

        # Default ratio categories if not specified
        if ratio_categories is None:
            ratio_categories = ["liquidity", "profitability", "solvency", "efficiency", "valuation"]

        # Initialize industry_benchmarks if None
        if industry_benchmarks is None:
            industry_benchmarks = {}

        logger.info(f"Calculating financial ratios for {len(financial_data)} data points")

        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame(financial_data)

            # Init results dictionary
            ratio_results = {
                "ratio_summary": {},
                "interpretations": {},
                "trend_analysis": {},
                "benchmark_comparison": {}
            }

            # Identify financial statement elements from column names
            # This is a simplified approach - in practice, you'd have a more robust mapping
            financial_elements = {
                # Income statement
                "revenue": next((col for col in df.columns if "revenue" in col.lower() or "sales" in col.lower()), None),
                "gross_profit": next((col for col in df.columns if "gross profit" in col.lower() or "gross margin" in col.lower()), None),
                "operating_income": next((col for col in df.columns if "operating income" in col.lower() or "operating profit" in col.lower() or "ebit" in col.lower()), None),
                "net_income": next((col for col in df.columns if "net income" in col.lower() or "net profit" in col.lower() or "earnings" in col.lower()), None),
                "cogs": next((col for col in df.columns if "cogs" in col.lower() or "cost of goods" in col.lower() or "cost of sales" in col.lower()), None),

                # Balance sheet
                "current_assets": next((col for col in df.columns if "current assets" in col.lower()), None),
                "total_assets": next((col for col in df.columns if "total assets" in col.lower() or "assets" in col.lower()), None),
                "current_liabilities": next((col for col in df.columns if "current liabilities" in col.lower()), None),
                "total_liabilities": next((col for col in df.columns if "total liabilities" in col.lower() or "liabilities" in col.lower()), None),
                "equity": next((col for col in df.columns if "equity" in col.lower() or "stockholders equity" in col.lower() or "shareholders equity" in col.lower()), None),
                "inventory": next((col for col in df.columns if "inventory" in col.lower()), None),
                "accounts_receivable": next((col for col in df.columns if "accounts receivable" in col.lower() or "ar" in col.lower()), None),

                # Cash flow
                "operating_cash_flow": next((col for col in df.columns if "operating cash flow" in col.lower() or "cash from operations" in col.lower()), None),
                "capital_expenditure": next((col for col in df.columns if "capital expenditure" in col.lower() or "capex" in col.lower()), None),

                # Market data
                "market_cap": next((col for col in df.columns if "market cap" in col.lower() or "market capitalization" in col.lower()), None),
                "share_price": next((col for col in df.columns if "share price" in col.lower() or "stock price" in col.lower()), None),
                "shares_outstanding": next((col for col in df.columns if "shares outstanding" in col.lower()), None)
            }

            # Filter out None values
            financial_elements = {k: v for k, v in financial_elements.items() if v is not None}

            # Calculate ratios by category
            if "liquidity" in ratio_categories:
                liquidity_ratios = self._calculate_liquidity_ratios(df, financial_elements)
                if liquidity_ratios:
                    ratio_results["ratio_summary"]["liquidity"] = liquidity_ratios

            if "profitability" in ratio_categories:
                profitability_ratios = self._calculate_profitability_ratios(df, financial_elements)
                if profitability_ratios:
                    ratio_results["ratio_summary"]["profitability"] = profitability_ratios

            if "solvency" in ratio_categories:
                solvency_ratios = self._calculate_solvency_ratios(df, financial_elements)
                if solvency_ratios:
                    ratio_results["ratio_summary"]["solvency"] = solvency_ratios

            if "efficiency" in ratio_categories:
                efficiency_ratios = self._calculate_efficiency_ratios(df, financial_elements)
                if efficiency_ratios:
                    ratio_results["ratio_summary"]["efficiency"] = efficiency_ratios

            if "valuation" in ratio_categories:
                valuation_ratios = self._calculate_valuation_ratios(df, financial_elements)
                if valuation_ratios:
                    ratio_results["ratio_summary"]["valuation"] = valuation_ratios

            # Generate interpretations for calculated ratios
            ratio_results["interpretations"] = self._interpret_financial_ratios(ratio_results["ratio_summary"])

            # Compare with industry benchmarks if provided
            if industry_benchmarks:
                benchmark_comparison = {}

                for category, ratios in ratio_results["ratio_summary"].items():
                    category_comparison = {}

                    for ratio_name, ratio_value in ratios.items():
                        # Check if this ratio exists in benchmarks
                        benchmark_key = next((k for k in industry_benchmarks.keys() if ratio_name.lower() in k.lower()), None)

                        if benchmark_key:
                            benchmark_value = industry_benchmarks[benchmark_key]

                            # Calculate difference
                            if isinstance(ratio_value, dict) and 'latest' in ratio_value:
                                ratio_val = ratio_value['latest']
                            else:
                                ratio_val = ratio_value

                            if isinstance(ratio_val, (int, float)) and isinstance(benchmark_value, (int, float)):
                                difference = ratio_val - benchmark_value
                                pct_difference = (difference / benchmark_value) * 100 if benchmark_value != 0 else float('inf')

                                category_comparison[ratio_name] = {
                                    'company_value': ratio_val,
                                    'industry_benchmark': benchmark_value,
                                    'difference': difference,
                                    'percent_difference': pct_difference,
                                    'assessment': 'above industry' if difference > 0 else 'below industry'
                                }

                    if category_comparison:
                        benchmark_comparison[category] = category_comparison

                ratio_results["benchmark_comparison"] = benchmark_comparison

            # Calculate trends if we have time-series data
            date_col = next((col for col in df.columns if any(term in col.lower() for term in ['date', 'year', 'period'])), None)
            if date_col and len(df) > 1:
                try:
                    # Sort by date for trend analysis
                    df_sorted = df.sort_values(by=date_col)

                    # Analyze trends for each ratio category
                    trend_analysis = {}

                    for category, ratios in ratio_results["ratio_summary"].items():
                        category_trends = {}

                        for ratio_name, ratio_value in ratios.items():
                            # Skip if not a time series value
                            if not isinstance(ratio_value, dict) or 'time_series' not in ratio_value:
                                continue

                            # Calculate trend metrics
                            values = ratio_value['time_series']
                            if len(values) >= 3:  # Need at least 3 points for trend
                                first_value = values[0]
                                last_value = values[-1]

                                # Linear regression to determine trend
                                X = np.arange(len(values)).reshape(-1, 1)
                                y = np.array(values).reshape(-1, 1)
                                model = LinearRegression().fit(X, y)

                                category_trends[ratio_name] = {
                                    'start_value': first_value,
                                    'end_value': last_value,
                                    'absolute_change': last_value - first_value,
                                    'percent_change': ((last_value - first_value) / first_value * 100) if first_value != 0 else 0,
                                    'slope': float(model.coef_[0][0]),
                                    'r_squared': float(model.score(X, y)),
                                    'trend_direction': 'improving' if model.coef_[0][0] > 0 else 'deteriorating' if model.coef_[0][0] < 0 else 'stable'
                                }

                        if category_trends:
                            trend_analysis[category] = category_trends

                    ratio_results["trend_analysis"] = trend_analysis
                except Exception as e:
                    logger.warning(f"Error in trend analysis: {str(e)}")

            return ratio_results

        except Exception as e:
            logger.error(f"Error calculating financial ratios: {str(e)}")
            return {
                "error": f"Error calculating financial ratios: {str(e)}",
                "ratio_categories": ratio_categories
            }

    def _calculate_liquidity_ratios(self, df: pd.DataFrame, financial_elements: Dict[str, str]) -> Dict[str, Any]:
        """Calculate liquidity ratios from financial data."""
        liquidity_ratios = {}

        # Current ratio
        if all(elem in financial_elements for elem in ['current_assets', 'current_liabilities']):
            try:
                # For time series data
                if len(df) > 1:
                    current_ratios = []
                    for i in range(len(df)):
                        ca = df[financial_elements['current_assets']].iloc[i]
                        cl = df[financial_elements['current_liabilities']].iloc[i]
                        if cl != 0:
                            current_ratios.append(ca / cl)
                        else:
                            current_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(current_ratios) and current_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(current_ratios):
                        liquidity_ratios['current_ratio'] = {
                            'latest': current_ratios[latest_idx],
                            'average': np.mean([x for x in current_ratios if x is not None]),
                            'time_series': current_ratios
                        }
                else:
                    # For single period data
                    ca = df[financial_elements['current_assets']].iloc[0]
                    cl = df[financial_elements['current_liabilities']].iloc[0]
                    if cl != 0:
                        liquidity_ratios['current_ratio'] = ca / cl
            except Exception as e:
                logger.warning(f"Error calculating current ratio: {str(e)}")

        # Quick ratio (Acid-test ratio)
        if all(elem in financial_elements for elem in ['current_assets', 'inventory', 'current_liabilities']):
            try:
                # For time series data
                if len(df) > 1:
                    quick_ratios = []
                    for i in range(len(df)):
                        ca = df[financial_elements['current_assets']].iloc[i]
                        inv = df[financial_elements['inventory']].iloc[i]
                        cl = df[financial_elements['current_liabilities']].iloc[i]
                        if cl != 0:
                            quick_ratios.append((ca - inv) / cl)
                        else:
                            quick_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(quick_ratios) and quick_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(quick_ratios):
                        liquidity_ratios['quick_ratio'] = {
                            'latest': quick_ratios[latest_idx],
                            'average': np.mean([x for x in quick_ratios if x is not None]),
                            'time_series': quick_ratios
                        }
                else:
                    # For single period data
                    ca = df[financial_elements['current_assets']].iloc[0]
                    inv = df[financial_elements['inventory']].iloc[0]
                    cl = df[financial_elements['current_liabilities']].iloc[0]
                    if cl != 0:
                        liquidity_ratios['quick_ratio'] = (ca - inv) / cl
            except Exception as e:
                logger.warning(f"Error calculating quick ratio: {str(e)}")

        # Cash ratio
        if 'cash' in financial_elements and 'current_liabilities' in financial_elements:
            try:
                # For time series data
                if len(df) > 1:
                    cash_ratios = []
                    for i in range(len(df)):
                        cash = df[financial_elements['cash']].iloc[i]
                        cl = df[financial_elements['current_liabilities']].iloc[i]
                        if cl != 0:
                            cash_ratios.append(cash / cl)
                        else:
                            cash_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(cash_ratios) and cash_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(cash_ratios):
                        liquidity_ratios['cash_ratio'] = {
                            'latest': cash_ratios[latest_idx],
                            'average': np.mean([x for x in cash_ratios if x is not None]),
                            'time_series': cash_ratios
                        }
                else:
                    # For single period data
                    cash = df[financial_elements['cash']].iloc[0]
                    cl = df[financial_elements['current_liabilities']].iloc[0]
                    if cl != 0:
                        liquidity_ratios['cash_ratio'] = cash / cl
            except Exception as e:
                logger.warning(f"Error calculating cash ratio: {str(e)}")

        return liquidity_ratios

    def _calculate_profitability_ratios(self, df: pd.DataFrame, financial_elements: Dict[str, str]) -> Dict[str, Any]:
        """Calculate profitability ratios from financial data."""
        profitability_ratios = {}

        # Gross margin
        if all(elem in financial_elements for elem in ['gross_profit', 'revenue']):
            try:
                # For time series data
                if len(df) > 1:
                    gross_margins = []
                    for i in range(len(df)):
                        gp = df[financial_elements['gross_profit']].iloc[i]
                        rev = df[financial_elements['revenue']].iloc[i]
                        if rev != 0:
                            gross_margins.append((gp / rev) * 100)  # As percentage
                        else:
                            gross_margins.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(gross_margins) and gross_margins[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(gross_margins):
                        profitability_ratios['gross_margin'] = {
                            'latest': gross_margins[latest_idx],
                            'average': np.mean([x for x in gross_margins if x is not None]),
                            'time_series': gross_margins
                        }
                else:
                    # For single period data
                    gp = df[financial_elements['gross_profit']].iloc[0]
                    rev = df[financial_elements['revenue']].iloc[0]
                    if rev != 0:
                        profitability_ratios['gross_margin'] = (gp / rev) * 100  # As percentage
            except Exception as e:
                logger.warning(f"Error calculating gross margin: {str(e)}")

        # Operating margin
        if all(elem in financial_elements for elem in ['operating_income', 'revenue']):
            try:
                # For time series data
                if len(df) > 1:
                    op_margins = []
                    for i in range(len(df)):
                        op_inc = df[financial_elements['operating_income']].iloc[i]
                        rev = df[financial_elements['revenue']].iloc[i]
                        if rev != 0:
                            op_margins.append((op_inc / rev) * 100)  # As percentage
                        else:
                            op_margins.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(op_margins) and op_margins[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(op_margins):
                        profitability_ratios['operating_margin'] = {
                            'latest': op_margins[latest_idx],
                            'average': np.mean([x for x in op_margins if x is not None]),
                            'time_series': op_margins
                        }
                else:
                    # For single period data
                    op_inc = df[financial_elements['operating_income']].iloc[0]
                    rev = df[financial_elements['revenue']].iloc[0]
                    if rev != 0:
                        profitability_ratios['operating_margin'] = (op_inc / rev) * 100  # As percentage
            except Exception as e:
                logger.warning(f"Error calculating operating margin: {str(e)}")

        # Net profit margin
        if all(elem in financial_elements for elem in ['net_income', 'revenue']):
            try:
                # For time series data
                if len(df) > 1:
                    net_margins = []
                    for i in range(len(df)):
                        net_inc = df[financial_elements['net_income']].iloc[i]
                        rev = df[financial_elements['revenue']].iloc[i]
                        if rev != 0:
                            net_margins.append((net_inc / rev) * 100)  # As percentage
                        else:
                            net_margins.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(net_margins) and net_margins[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(net_margins):
                        profitability_ratios['net_profit_margin'] = {
                            'latest': net_margins[latest_idx],
                            'average': np.mean([x for x in net_margins if x is not None]),
                            'time_series': net_margins
                        }
                else:
                    # For single period data
                    net_inc = df[financial_elements['net_income']].iloc[0]
                    rev = df[financial_elements['revenue']].iloc[0]
                    if rev != 0:
                        profitability_ratios['net_profit_margin'] = (net_inc / rev) * 100  # As percentage
            except Exception as e:
                logger.warning(f"Error calculating net profit margin: {str(e)}")

        # Return on assets (ROA)
        if all(elem in financial_elements for elem in ['net_income', 'total_assets']):
            try:
                # For time series data
                if len(df) > 1:
                    roas = []
                    for i in range(len(df)):
                        net_inc = df[financial_elements['net_income']].iloc[i]
                        ta = df[financial_elements['total_assets']].iloc[i]
                        if ta != 0:
                            roas.append((net_inc / ta) * 100)  # As percentage
                        else:
                            roas.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(roas) and roas[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(roas):
                        profitability_ratios['return_on_assets'] = {
                            'latest': roas[latest_idx],
                            'average': np.mean([x for x in roas if x is not None]),
                            'time_series': roas
                        }
                else:
                    # For single period data
                    net_inc = df[financial_elements['net_income']].iloc[0]
                    ta = df[financial_elements['total_assets']].iloc[0]
                    if ta != 0:
                        profitability_ratios['return_on_assets'] = (net_inc / ta) * 100  # As percentage
            except Exception as e:
                logger.warning(f"Error calculating return on assets: {str(e)}")

        # Return on equity (ROE)
        if all(elem in financial_elements for elem in ['net_income', 'equity']):
            try:
                # For time series data
                if len(df) > 1:
                    roes = []
                    for i in range(len(df)):
                        net_inc = df[financial_elements['net_income']].iloc[i]
                        eq = df[financial_elements['equity']].iloc[i]
                        if eq != 0:
                            roes.append((net_inc / eq) * 100)  # As percentage
                        else:
                            roes.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(roes) and roes[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(roes):
                        profitability_ratios['return_on_equity'] = {
                            'latest': roes[latest_idx],
                            'average': np.mean([x for x in roes if x is not None]),
                            'time_series': roes
                        }
                else:
                    # For single period data
                    net_inc = df[financial_elements['net_income']].iloc[0]
                    eq = df[financial_elements['equity']].iloc[0]
                    if eq != 0:
                        profitability_ratios['return_on_equity'] = (net_inc / eq) * 100  # As percentage
            except Exception as e:
                logger.warning(f"Error calculating return on equity: {str(e)}")

        return profitability_ratios
    
    def _calculate_solvency_ratios(self, df: pd.DataFrame, financial_elements: Dict[str, str]) -> Dict[str, Any]:
        """Calculate solvency ratios from financial data."""
        solvency_ratios = {}

        # Debt-to-equity ratio
        if all(elem in financial_elements for elem in ['total_liabilities', 'equity']):
            try:
                # For time series data
                if len(df) > 1:
                    de_ratios = []
                    for i in range(len(df)):
                        tl = df[financial_elements['total_liabilities']].iloc[i]
                        eq = df[financial_elements['equity']].iloc[i]
                        if eq != 0:
                            de_ratios.append(tl / eq)
                        else:
                            de_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(de_ratios) and de_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(de_ratios):
                        solvency_ratios['debt_to_equity'] = {
                            'latest': de_ratios[latest_idx],
                            'average': np.mean([x for x in de_ratios if x is not None]),
                            'time_series': de_ratios
                        }
                else:
                    # For single period data
                    tl = df[financial_elements['total_liabilities']].iloc[0]
                    eq = df[financial_elements['equity']].iloc[0]
                    if eq != 0:
                        solvency_ratios['debt_to_equity'] = tl / eq
            except Exception as e:
                logger.warning(f"Error calculating debt-to-equity ratio: {str(e)}")

        # Debt ratio (Total debt / Total assets)
        if all(elem in financial_elements for elem in ['total_liabilities', 'total_assets']):
            try:
                # For time series data
                if len(df) > 1:
                    debt_ratios = []
                    for i in range(len(df)):
                        tl = df[financial_elements['total_liabilities']].iloc[i]
                        ta = df[financial_elements['total_assets']].iloc[i]
                        if ta != 0:
                            debt_ratios.append(tl / ta)
                        else:
                            debt_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(debt_ratios) and debt_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(debt_ratios):
                        solvency_ratios['debt_ratio'] = {
                            'latest': debt_ratios[latest_idx],
                            'average': np.mean([x for x in debt_ratios if x is not None]),
                            'time_series': debt_ratios
                        }
                else:
                    # For single period data
                    tl = df[financial_elements['total_liabilities']].iloc[0]
                    ta = df[financial_elements['total_assets']].iloc[0]
                    if ta != 0:
                        solvency_ratios['debt_ratio'] = tl / ta
            except Exception as e:
                logger.warning(f"Error calculating debt ratio: {str(e)}")

        # Interest coverage ratio
        if all(elem in financial_elements for elem in ['operating_income', 'interest_expense']):
            try:
                # For time series data
                if len(df) > 1:
                    ic_ratios = []
                    for i in range(len(df)):
                        op_inc = df[financial_elements['operating_income']].iloc[i]
                        int_exp = df[financial_elements['interest_expense']].iloc[i]
                        if int_exp != 0:
                            ic_ratios.append(op_inc / int_exp)
                        else:
                            ic_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(ic_ratios) and ic_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(ic_ratios):
                        solvency_ratios['interest_coverage'] = {
                            'latest': ic_ratios[latest_idx],
                            'average': np.mean([x for x in ic_ratios if x is not None]),
                            'time_series': ic_ratios
                        }
                else:
                    # For single period data
                    op_inc = df[financial_elements['operating_income']].iloc[0]
                    int_exp = df[financial_elements['interest_expense']].iloc[0]
                    if int_exp != 0:
                        solvency_ratios['interest_coverage'] = op_inc / int_exp
            except Exception as e:
                logger.warning(f"Error calculating interest coverage ratio: {str(e)}")

        return solvency_ratios

    def _calculate_efficiency_ratios(self, df: pd.DataFrame, financial_elements: Dict[str, str]) -> Dict[str, Any]:
        """Calculate efficiency ratios from financial data."""
        efficiency_ratios = {}

        # Asset turnover ratio
        if all(elem in financial_elements for elem in ['revenue', 'total_assets']):
            try:
                # For time series data
                if len(df) > 1:
                    asset_turnovers = []
                    for i in range(len(df)):
                        rev = df[financial_elements['revenue']].iloc[i]
                        ta = df[financial_elements['total_assets']].iloc[i]
                        if ta != 0:
                            asset_turnovers.append(rev / ta)
                        else:
                            asset_turnovers.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(asset_turnovers) and asset_turnovers[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(asset_turnovers):
                        efficiency_ratios['asset_turnover'] = {
                            'latest': asset_turnovers[latest_idx],
                            'average': np.mean([x for x in asset_turnovers if x is not None]),
                            'time_series': asset_turnovers
                        }
                else:
                    # For single period data
                    rev = df[financial_elements['revenue']].iloc[0]
                    ta = df[financial_elements['total_assets']].iloc[0]
                    if ta != 0:
                        efficiency_ratios['asset_turnover'] = rev / ta
            except Exception as e:
                logger.warning(f"Error calculating asset turnover ratio: {str(e)}")

        # Inventory turnover ratio
        if all(elem in financial_elements for elem in ['cogs', 'inventory']):
            try:
                # For time series data
                if len(df) > 1:
                    inventory_turnovers = []
                    for i in range(len(df)):
                        cogs = df[financial_elements['cogs']].iloc[i]
                        inv = df[financial_elements['inventory']].iloc[i]
                        if inv != 0:
                            inventory_turnovers.append(cogs / inv)
                        else:
                            inventory_turnovers.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(inventory_turnovers) and inventory_turnovers[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(inventory_turnovers):
                        efficiency_ratios['inventory_turnover'] = {
                            'latest': inventory_turnovers[latest_idx],
                            'average': np.mean([x for x in inventory_turnovers if x is not None]),
                            'time_series': inventory_turnovers
                        }
                else:
                    # For single period data
                    cogs = df[financial_elements['cogs']].iloc[0]
                    inv = df[financial_elements['inventory']].iloc[0]
                    if inv != 0:
                        efficiency_ratios['inventory_turnover'] = cogs / inv
            except Exception as e:
                logger.warning(f"Error calculating inventory turnover ratio: {str(e)}")

        # Receivables turnover ratio
        if all(elem in financial_elements for elem in ['revenue', 'accounts_receivable']):
            try:
                # For time series data
                if len(df) > 1:
                    receivables_turnovers = []
                    for i in range(len(df)):
                        rev = df[financial_elements['revenue']].iloc[i]
                        ar = df[financial_elements['accounts_receivable']].iloc[i]
                        if ar != 0:
                            receivables_turnovers.append(rev / ar)
                        else:
                            receivables_turnovers.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(receivables_turnovers) and receivables_turnovers[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(receivables_turnovers):
                        efficiency_ratios['receivables_turnover'] = {
                            'latest': receivables_turnovers[latest_idx],
                            'average': np.mean([x for x in receivables_turnovers if x is not None]),
                            'time_series': receivables_turnovers
                        }
                else:
                    # For single period data
                    rev = df[financial_elements['revenue']].iloc[0]
                    ar = df[financial_elements['accounts_receivable']].iloc[0]
                    if ar != 0:
                        efficiency_ratios['receivables_turnover'] = rev / ar
            except Exception as e:
                logger.warning(f"Error calculating receivables turnover ratio: {str(e)}")

        return efficiency_ratios
    def _calculate_valuation_ratios(self, df: pd.DataFrame, financial_elements: Dict[str, str]) -> Dict[str, Any]:
        """Calculate valuation ratios from financial data."""
        valuation_ratios = {}

        # Price-to-earnings (P/E) ratio
        if all(elem in financial_elements for elem in ['share_price', 'net_income', 'shares_outstanding']):
            try:
                # For time series data
                if len(df) > 1:
                    pe_ratios = []
                    for i in range(len(df)):
                        price = df[financial_elements['share_price']].iloc[i]
                        net_inc = df[financial_elements['net_income']].iloc[i]
                        shares = df[financial_elements['shares_outstanding']].iloc[i]

                        if net_inc != 0 and shares != 0:
                            eps = net_inc / shares
                            pe_ratios.append(price / eps)
                        else:
                            pe_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(pe_ratios) and pe_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(pe_ratios):
                        valuation_ratios['price_to_earnings'] = {
                            'latest': pe_ratios[latest_idx],
                            'average': np.mean([x for x in pe_ratios if x is not None]),
                            'time_series': pe_ratios
                        }
                else:
                    # For single period data
                    price = df[financial_elements['share_price']].iloc[0]
                    net_inc = df[financial_elements['net_income']].iloc[0]
                    shares = df[financial_elements['shares_outstanding']].iloc[0]

                    if net_inc != 0 and shares != 0:
                        eps = net_inc / shares
                        valuation_ratios['price_to_earnings'] = price / eps
            except Exception as e:
                logger.warning(f"Error calculating P/E ratio: {str(e)}")

        # Price-to-book (P/B) ratio
        if all(elem in financial_elements for elem in ['share_price', 'equity', 'shares_outstanding']):
            try:
                # For time series data
                if len(df) > 1:
                    pb_ratios = []
                    for i in range(len(df)):
                        price = df[financial_elements['share_price']].iloc[i]
                        equity = df[financial_elements['equity']].iloc[i]
                        shares = df[financial_elements['shares_outstanding']].iloc[i]

                        if equity != 0 and shares != 0:
                            book_value_per_share = equity / shares
                            pb_ratios.append(price / book_value_per_share)
                        else:
                            pb_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(pb_ratios) and pb_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(pb_ratios):
                        valuation_ratios['price_to_book'] = {
                            'latest': pb_ratios[latest_idx],
                            'average': np.mean([x for x in pb_ratios if x is not None]),
                            'time_series': pb_ratios
                        }
                else:
                    # For single period data
                    price = df[financial_elements['share_price']].iloc[0]
                    equity = df[financial_elements['equity']].iloc[0]
                    shares = df[financial_elements['shares_outstanding']].iloc[0]

                    if equity != 0 and shares != 0:
                        book_value_per_share = equity / shares
                        valuation_ratios['price_to_book'] = price / book_value_per_share
            except Exception as e:
                logger.warning(f"Error calculating P/B ratio: {str(e)}")

        # Enterprise value-to-EBITDA
        if all(elem in financial_elements for elem in ['market_cap', 'total_debt', 'cash', 'operating_income', 'depreciation', 'amortization']):
            try:
                # For time series data
                if len(df) > 1:
                    ev_ebitda_ratios = []
                    for i in range(len(df)):
                        market_cap = df[financial_elements['market_cap']].iloc[i]
                        debt = df[financial_elements['total_debt']].iloc[i]
                        cash = df[financial_elements['cash']].iloc[i]
                        op_inc = df[financial_elements['operating_income']].iloc[i]
                        depr = df[financial_elements['depreciation']].iloc[i]
                        amort = df[financial_elements['amortization']].iloc[i]

                        # Enterprise Value = Market Cap + Debt - Cash
                        ev = market_cap + debt - cash

                        # EBITDA = Operating Income + Depreciation + Amortization
                        ebitda = op_inc + depr + amort

                        if ebitda != 0:
                            ev_ebitda_ratios.append(ev / ebitda)
                        else:
                            ev_ebitda_ratios.append(None)

                    # Get latest value
                    latest_idx = -1
                    while latest_idx >= -len(ev_ebitda_ratios) and ev_ebitda_ratios[latest_idx] is None:
                        latest_idx -= 1

                    if latest_idx >= -len(ev_ebitda_ratios):
                        valuation_ratios['ev_to_ebitda'] = {
                            'latest': ev_ebitda_ratios[latest_idx],
                            'average': np.mean([x for x in ev_ebitda_ratios if x is not None]),
                            'time_series': ev_ebitda_ratios
                        }
                else:
                    # For single period data
                    market_cap = df[financial_elements['market_cap']].iloc[0]
                    debt = df[financial_elements['total_debt']].iloc[0]
                    cash = df[financial_elements['cash']].iloc[0]
                    op_inc = df[financial_elements['operating_income']].iloc[0]
                    depr = df[financial_elements['depreciation']].iloc[0]
                    amort = df[financial_elements['amortization']].iloc[0]

                    # Enterprise Value = Market Cap + Debt - Cash
                    ev = market_cap + debt - cash

                    # EBITDA = Operating Income + Depreciation + Amortization
                    ebitda = op_inc + depr + amort

                    if ebitda != 0:
                        valuation_ratios['ev_to_ebitda'] = ev / ebitda
            except Exception as e:
                logger.warning(f"Error calculating EV/EBITDA ratio: {str(e)}")

        return valuation_ratios

    def _interpret_financial_ratios(self, ratio_categories: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate interpretations of financial ratios."""
        interpretations = {}

        # Interpret liquidity ratios
        if 'liquidity' in ratio_categories:
            liquidity_insights = []

            # Current ratio interpretation
            if 'current_ratio' in ratio_categories['liquidity']:
                current_ratio = ratio_categories['liquidity']['current_ratio']

                # Extract the value whether it's a single value or time series
                if isinstance(current_ratio, dict) and 'latest' in current_ratio:
                    cr_value = current_ratio['latest']
                else:
                    cr_value = current_ratio

                if cr_value < 1:
                    liquidity_insights.append(f"The current ratio of {cr_value:.2f} indicates potential short-term liquidity issues, as current assets don't cover current liabilities.")
                elif cr_value >= 1 and cr_value < 1.5:
                    liquidity_insights.append(f"The current ratio of {cr_value:.2f} shows adequate but tight liquidity, with current assets just covering current liabilities.")
                else:
                    liquidity_insights.append(f"The current ratio of {cr_value:.2f} indicates strong short-term liquidity position, with ample coverage of current liabilities.")

            # Quick ratio interpretation
            if 'quick_ratio' in ratio_categories['liquidity']:
                quick_ratio = ratio_categories['liquidity']['quick_ratio']

                # Extract the value
                if isinstance(quick_ratio, dict) and 'latest' in quick_ratio:
                    qr_value = quick_ratio['latest']
                else:
                    qr_value = quick_ratio

                if qr_value < 0.7:
                    liquidity_insights.append(f"The quick ratio of {qr_value:.2f} suggests potential issues meeting short-term obligations without selling inventory.")
                elif qr_value >= 0.7 and qr_value < 1:
                    liquidity_insights.append(f"The quick ratio of {qr_value:.2f} indicates moderate ability to cover short-term obligations with liquid assets.")
                else:
                    liquidity_insights.append(f"The quick ratio of {qr_value:.2f} shows strong ability to cover short-term obligations without relying on inventory sales.")

            # Cash ratio interpretation
            if 'cash_ratio' in ratio_categories['liquidity']:
                cash_ratio = ratio_categories['liquidity']['cash_ratio']

                # Extract the value
                if isinstance(cash_ratio, dict) and 'latest' in cash_ratio:
                    cash_value = cash_ratio['latest']
                else:
                    cash_value = cash_ratio

                if cash_value < 0.2:
                    liquidity_insights.append(f"The cash ratio of {cash_value:.2f} suggests limited immediate cash available to cover short-term liabilities.")
                elif cash_value >= 0.2 and cash_value < 0.5:
                    liquidity_insights.append(f"The cash ratio of {cash_value:.2f} indicates moderate cash reserves relative to short-term obligations.")
                else:
                    liquidity_insights.append(f"The cash ratio of {cash_value:.2f} shows strong cash position relative to short-term liabilities.")

            if liquidity_insights:
                interpretations['liquidity'] = liquidity_insights
        # Interpret profitability ratios
        if 'profitability' in ratio_categories:
            profitability_insights = []
            
            # Gross margin interpretation
            if 'gross_margin' in ratio_categories['profitability']:
                gross_margin = ratio_categories['profitability']['gross_margin']
                
                # Extract the value
                if isinstance(gross_margin, dict) and 'latest' in gross_margin:
                    gm_value = gross_margin['latest']
                else:
                    gm_value = gross_margin
                
                if gm_value < 20:
                    profitability_insights.append(f"The gross margin of {gm_value:.2f}% indicates thin margins on core products/services, potentially limiting flexibility in pricing and costs.")
                elif gm_value >= 20 and gm_value < 40:
                    profitability_insights.append(f"The gross margin of {gm_value:.2f}% shows moderate profitability from core operations.")
                else:
                    profitability_insights.append(f"The gross margin of {gm_value:.2f}% demonstrates strong profitability from core products/services.")
            
            # Operating margin interpretation
            if 'operating_margin' in ratio_categories['profitability']:
                operating_margin = ratio_categories['profitability']['operating_margin']
                
                # Extract the value
                if isinstance(operating_margin, dict) and 'latest' in operating_margin:
                    om_value = operating_margin['latest']
                else:
                    om_value = operating_margin
                
                if om_value < 5:
                    profitability_insights.append(f"The operating margin of {om_value:.2f}% indicates challenges in operational profitability, with limited buffer for market downturns.")
                elif om_value >= 5 and om_value < 15:
                    profitability_insights.append(f"The operating margin of {om_value:.2f}% shows healthy operational efficiency and cost management.")
                else:
                    profitability_insights.append(f"The operating margin of {om_value:.2f}% demonstrates exceptional operational profitability and competitive advantage.")
            
            # Net profit margin interpretation
            if 'net_profit_margin' in ratio_categories['profitability']:
                net_margin = ratio_categories['profitability']['net_profit_margin']
                
                # Extract the value
                if isinstance(net_margin, dict) and 'latest' in net_margin:
                    npm_value = net_margin['latest']
                else:
                    npm_value = net_margin
                
                if npm_value < 3:
                    profitability_insights.append(f"The net profit margin of {npm_value:.2f}% indicates slim overall profitability, suggesting limited capacity for reinvestment or shareholder returns.")
                elif npm_value >= 3 and npm_value < 10:
                    profitability_insights.append(f"The net profit margin of {npm_value:.2f}% shows solid overall profitability after all expenses.")
                else:
                    profitability_insights.append(f"The net profit margin of {npm_value:.2f}% demonstrates exceptional profitability and potentially strong competitive positioning.")
            
            # ROA interpretation
            if 'return_on_assets' in ratio_categories['profitability']:
                roa = ratio_categories['profitability']['return_on_assets']
                
                # Extract the value
                if isinstance(roa, dict) and 'latest' in roa:
                    roa_value = roa['latest']
                else:
                    roa_value = roa
                
                if roa_value < 2:
                    profitability_insights.append(f"The return on assets of {roa_value:.2f}% suggests inefficient use of assets to generate profits.")
                elif roa_value >= 2 and roa_value < 5:
                    profitability_insights.append(f"The return on assets of {roa_value:.2f}% indicates moderate efficiency in using assets to generate returns.")
                else:
                    profitability_insights.append(f"The return on assets of {roa_value:.2f}% demonstrates effective asset utilization to generate strong returns.")
            
            # ROE interpretation
            if 'return_on_equity' in ratio_categories['profitability']:
                roe = ratio_categories['profitability']['return_on_equity']
                
                # Extract the value
                if isinstance(roe, dict) and 'latest' in roe:
                    roe_value = roe['latest']
                else:
                    roe_value = roe
                
                if roe_value < 10:
                    profitability_insights.append(f"The return on equity of {roe_value:.2f}% indicates limited returns generated for shareholders relative to their investment.")
                elif roe_value >= 10 and roe_value < 20:
                    profitability_insights.append(f"The return on equity of {roe_value:.2f}% shows solid returns generated on shareholder investments.")
                else:
                    profitability_insights.append(f"The return on equity of {roe_value:.2f}% demonstrates exceptional shareholder value creation.")
            
            if profitability_insights:
                interpretations['profitability'] = profitability_insights
        
        # Interpret solvency ratios
        if 'solvency' in ratio_categories:
            solvency_insights = []
            
            # Debt-to-equity interpretation
            if 'debt_to_equity' in ratio_categories['solvency']:
                de_ratio = ratio_categories['solvency']['debt_to_equity']
                
                # Extract the value
                if isinstance(de_ratio, dict) and 'latest' in de_ratio:
                    de_value = de_ratio['latest']
                else:
                    de_value = de_ratio
                
                if de_value < 0.5:
                    solvency_insights.append(f"The debt-to-equity ratio of {de_value:.2f} indicates conservative financial leverage with relatively low reliance on debt financing.")
                elif de_value >= 0.5 and de_value < 1.5:
                    solvency_insights.append(f"The debt-to-equity ratio of {de_value:.2f} shows balanced use of debt and equity financing.")
                else:
                    solvency_insights.append(f"The debt-to-equity ratio of {de_value:.2f} suggests high financial leverage, which may increase financial risk but potentially enhance returns.")
            
            # Debt ratio interpretation
            if 'debt_ratio' in ratio_categories['solvency']:
                debt_ratio = ratio_categories['solvency']['debt_ratio']
                
                # Extract the value
                if isinstance(debt_ratio, dict) and 'latest' in debt_ratio:
                    dr_value = debt_ratio['latest']
                else:
                    dr_value = debt_ratio
                
                if dr_value < 0.3:
                    solvency_insights.append(f"The debt ratio of {dr_value:.2f} indicates strong financial independence with limited reliance on debt financing.")
                elif dr_value >= 0.3 and dr_value < 0.6:
                    solvency_insights.append(f"The debt ratio of {dr_value:.2f} shows moderate use of debt financing relative to total assets.")
                else:
                    solvency_insights.append(f"The debt ratio of {dr_value:.2f} suggests high dependency on debt financing, which may limit future borrowing capacity.")
            
            # Interest coverage interpretation
            if 'interest_coverage' in ratio_categories['solvency']:
                ic_ratio = ratio_categories['solvency']['interest_coverage']
                
                # Extract the value
                if isinstance(ic_ratio, dict) and 'latest' in ic_ratio:
                    ic_value = ic_ratio['latest']
                else:
                    ic_value = ic_ratio
                
                if ic_value < 2:
                    solvency_insights.append(f"The interest coverage ratio of {ic_value:.2f} indicates potential difficulty meeting interest obligations from operating income.")
                elif ic_value >= 2 and ic_value < 5:
                    solvency_insights.append(f"The interest coverage ratio of {ic_value:.2f} shows adequate ability to service debt interest from operating profits.")
                else:
                    solvency_insights.append(f"The interest coverage ratio of {ic_value:.2f} demonstrates strong capacity to cover interest expenses, suggesting low default risk.")
            
            if solvency_insights:
                interpretations['solvency'] = solvency_insights
        
        # Interpret efficiency ratios
        if 'efficiency' in ratio_categories:
            efficiency_insights = []
            
            # Asset turnover interpretation
            if 'asset_turnover' in ratio_categories['efficiency']:
                asset_turnover = ratio_categories['efficiency']['asset_turnover']
                
                # Extract the value
                if isinstance(asset_turnover, dict) and 'latest' in asset_turnover:
                    at_value = asset_turnover['latest']
                else:
                    at_value = asset_turnover
                
                if at_value < 0.5:
                    efficiency_insights.append(f"The asset turnover ratio of {at_value:.2f} suggests inefficient use of assets to generate revenue.")
                elif at_value >= 0.5 and at_value < 1:
                    efficiency_insights.append(f"The asset turnover ratio of {at_value:.2f} indicates moderate efficiency in using assets to generate sales.")
                else:
                    efficiency_insights.append(f"The asset turnover ratio of {at_value:.2f} demonstrates efficient utilization of assets to drive revenue.")
            
            # Inventory turnover interpretation
            if 'inventory_turnover' in ratio_categories['efficiency']:
                inventory_turnover = ratio_categories['efficiency']['inventory_turnover']
                
                # Extract the value
                if isinstance(inventory_turnover, dict) and 'latest' in inventory_turnover:
                    it_value = inventory_turnover['latest']
                else:
                    it_value = inventory_turnover
                
                if it_value < 4:
                    efficiency_insights.append(f"The inventory turnover ratio of {it_value:.2f} suggests potential excess inventory or slow-moving products.")
                elif it_value >= 4 and it_value < 8:
                    efficiency_insights.append(f"The inventory turnover ratio of {it_value:.2f} indicates healthy inventory management.")
                else:
                    efficiency_insights.append(f"The inventory turnover ratio of {it_value:.2f} demonstrates excellent inventory efficiency, with products moving quickly through the system.")
            
            # Receivables turnover interpretation
            if 'receivables_turnover' in ratio_categories['efficiency']:
                receivables_turnover = ratio_categories['efficiency']['receivables_turnover']
                
                # Extract the value
                if isinstance(receivables_turnover, dict) and 'latest' in receivables_turnover:
                    rt_value = receivables_turnover['latest']
                else:
                    rt_value = receivables_turnover
                
                if rt_value < 4:
                    efficiency_insights.append(f"The receivables turnover ratio of {rt_value:.2f} suggests potential issues with collection efficiency or customer credit quality.")
                elif rt_value >= 4 and rt_value < 8:
                    efficiency_insights.append(f"The receivables turnover ratio of {rt_value:.2f} indicates effective accounts receivable management.")
                else:
                    efficiency_insights.append(f"The receivables turnover ratio of {rt_value:.2f} demonstrates excellent collection practices and customer credit management.")
            
            if efficiency_insights:
                interpretations['efficiency'] = efficiency_insights
        
        # Interpret valuation ratios
        if 'valuation' in ratio_categories:
            valuation_insights = []
            
            # P/E ratio interpretation
            if 'price_to_earnings' in ratio_categories['valuation']:
                pe_ratio = ratio_categories['valuation']['price_to_earnings']
                
                # Extract the value
                if isinstance(pe_ratio, dict) and 'latest' in pe_ratio:
                    pe_value = pe_ratio['latest']
                else:
                    pe_value = pe_ratio
                
                if pe_value < 10:
                    valuation_insights.append(f"The P/E ratio of {pe_value:.2f} suggests the stock may be undervalued or that investors expect declining future earnings.")
                elif pe_value >= 10 and pe_value < 20:
                    valuation_insights.append(f"The P/E ratio of {pe_value:.2f} indicates fairly valued stock based on typical market valuations.")
                else:
                    valuation_insights.append(f"The P/E ratio of {pe_value:.2f} suggests premium valuation, potentially reflecting high growth expectations or market optimism.")
            
            # P/B ratio interpretation
            if 'price_to_book' in ratio_categories['valuation']:
                pb_ratio = ratio_categories['valuation']['price_to_book']
                
                # Extract the value
                if isinstance(pb_ratio, dict) and 'latest' in pb_ratio:
                    pb_value = pb_ratio['latest']
                else:
                    pb_value = pb_ratio
                
                if pb_value < 1:
                    valuation_insights.append(f"The P/B ratio of {pb_value:.2f} suggests the stock may be trading below its book value, potentially indicating undervaluation or concerns about asset quality.")
                elif pb_value >= 1 and pb_value < 3:
                    valuation_insights.append(f"The P/B ratio of {pb_value:.2f} indicates reasonable valuation relative to company's book value.")
                else:
                    valuation_insights.append(f"The P/B ratio of {pb_value:.2f} suggests the market places significant premium on the company's assets, potentially reflecting strong ROE or growth prospects.")
            
            # EV/EBITDA interpretation
            if 'ev_to_ebitda' in ratio_categories['valuation']:
                ev_ebitda = ratio_categories['valuation']['ev_to_ebitda']
                
                # Extract the value
                if isinstance(ev_ebitda, dict) and 'latest' in ev_ebitda:
                    ev_value = ev_ebitda['latest']
                else:
                    ev_value = ev_ebitda
                
                if ev_value < 6:
                    valuation_insights.append(f"The EV/EBITDA ratio of {ev_value:.2f} suggests potential undervaluation relative to the company's cash flow generation.")
                elif ev_value >= 6 and ev_value < 12:
                    valuation_insights.append(f"The EV/EBITDA ratio of {ev_value:.2f} indicates fair valuation in line with typical market multiples.")
                else:
                    valuation_insights.append(f"The EV/EBITDA ratio of {ev_value:.2f} reflects premium valuation, potentially due to strong growth expectations or industry-specific factors.")
            
            if valuation_insights:
                interpretations['valuation'] = valuation_insights
        
        return interpretations

    def perform_investment_analysis(
        self,
        investment_data: Optional[List[Dict[str, Any]]] = None,
        analysis_type: Optional[str] = None, 
        risk_profile: Optional[str] = None,
        time_horizon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze investment opportunities based on financial data and parameters.
        
        Args:
            investment_data: List of dictionaries containing investment data.
            analysis_type: Type of investment analysis ("stock", "bond", "portfolio", "real_estate").
            risk_profile: Risk tolerance profile ("conservative", "moderate", "aggressive").
            time_horizon: Investment time horizon ("short_term", "medium_term", "long_term").
            
        Returns:
            Dictionary with detailed investment analysis results.
        """
        # Set default values inside the function
        if investment_data is None:
            investment_data = []
        
        if analysis_type is None:
            analysis_type = "stock"
        
        if risk_profile is None:
            risk_profile = "moderate"
            
        if time_horizon is None:
            time_horizon = "medium_term"
        
        logger.info(f"Performing {analysis_type} investment analysis with {risk_profile} risk profile")
        
        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame(investment_data)
            
            # Initialize results dictionary
            analysis_results = {
                "analysis_parameters": {
                    "analysis_type": analysis_type,
                    "risk_profile": risk_profile,
                    "time_horizon": time_horizon
                },
                "investment_metrics": {},
                "risk_analysis": {},
                "return_analysis": {},
                "recommendations": []
            }
            
            # Perform specific analysis based on type
            if analysis_type.lower() == "stock":
                analysis_results = self._analyze_stock_investment(df, risk_profile, time_horizon)
            elif analysis_type.lower() == "bond":
                analysis_results = self._analyze_bond_investment(df, risk_profile, time_horizon)
            elif analysis_type.lower() == "portfolio":
                analysis_results = self._analyze_portfolio_investment(df, risk_profile, time_horizon)
            elif analysis_type.lower() == "real_estate":
                analysis_results = self._analyze_real_estate_investment(df, risk_profile, time_horizon)
            else:
                return {
                    "error": f"Unsupported analysis type: {analysis_type}",
                    "supported_types": ["stock", "bond", "portfolio", "real_estate"]
                }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error performing investment analysis: {str(e)}")
            return {
                "error": f"Error performing investment analysis: {str(e)}",
                "analysis_type": analysis_type
            }
            
    def _analyze_stock_investment(
        self, 
        df: pd.DataFrame, 
        risk_profile: str,
        time_horizon: str
    ) -> Dict[str, Any]:
        """Analyze stock investment opportunities."""
        stock_analysis = {
            "analysis_parameters": {
                "analysis_type": "stock",
                "risk_profile": risk_profile,
                "time_horizon": time_horizon
            },
            "investment_metrics": {},
            "risk_analysis": {},
            "return_analysis": {},
            "valuation_analysis": {},
            "recommendations": []
        }
        
        # Check for required columns
        required_cols = ['ticker', 'price']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            stock_analysis["error"] = f"Missing required columns: {', '.join(missing_cols)}"
            return stock_analysis
        
        # Extract stock data
        tickers = df['ticker'].unique()
        
        # Process each stock
        for ticker in tickers:
            stock_df = df[df['ticker'] == ticker]
            
            # Skip if insufficient data
            if len(stock_df) < 2:
                continue
            
            # Get latest price and calculate metrics
            latest_price = stock_df['price'].iloc[-1]
            
            # Calculate price metrics
            stock_metrics = {
                "latest_price": latest_price
            }
            
            # If historical price data available, calculate returns and volatility
            if len(stock_df) > 30:  # Assuming we have reasonable history
                prices = stock_df['price'].values
                
                # Calculate returns
                returns = np.diff(prices) / prices[:-1]
                
                # Calculate return metrics
                avg_return = np.mean(returns)
                annualized_return = ((1 + avg_return) ** 252 - 1) * 100  # Assume 252 trading days
                volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized volatility
                max_drawdown = (np.min(prices) - np.max(prices)) / np.max(prices) * 100
                
                # Calculate Sharpe ratio (assuming risk-free rate of 2%)
                risk_free_rate = 0.02
                sharpe_ratio = (annualized_return / 100 - risk_free_rate) / (volatility / 100)
                
                # Add to metrics
                stock_metrics.update({
                    "avg_daily_return_pct": avg_return * 100,
                    "annualized_return_pct": annualized_return,
                    "annualized_volatility_pct": volatility,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown_pct": max_drawdown
                })
            
            # Check if EPS data available for P/E calculation
            if 'eps' in stock_df.columns:
                latest_eps = stock_df['eps'].iloc[-1]
                if latest_eps > 0:
                    pe_ratio = latest_price / latest_eps
                    stock_metrics["pe_ratio"] = pe_ratio
            
            # Check if book value data available for P/B calculation
            if 'book_value_per_share' in stock_df.columns:
                latest_bvps = stock_df['book_value_per_share'].iloc[-1]
                if latest_bvps > 0:
                    pb_ratio = latest_price / latest_bvps
                    stock_metrics["pb_ratio"] = pb_ratio
            
            # Add dividend metrics if available
            if 'dividend_yield' in stock_df.columns:
                latest_div_yield = stock_df['dividend_yield'].iloc[-1]
                stock_metrics["dividend_yield_pct"] = latest_div_yield * 100
            
            # Add to investment metrics
            stock_analysis["investment_metrics"][ticker] = stock_metrics
            
            # Risk assessment based on volatility and profile
            risk_assessment = {}
            if "annualized_volatility_pct" in stock_metrics:
                volatility = stock_metrics["annualized_volatility_pct"]
                
                if volatility < 15:
                    risk_level = "low"
                elif volatility < 25:
                    risk_level = "moderate"
                else:
                    risk_level = "high"
                
                risk_assessment["risk_level"] = risk_level
                risk_assessment["volatility_assessment"] = f"{volatility:.2f}% annualized volatility indicates {risk_level} risk level"
                
                # Risk match based on profile
                if risk_profile == "conservative" and risk_level == "low":
                    risk_assessment["profile_match"] = "good"
                elif risk_profile == "moderate" and risk_level == "moderate":
                    risk_assessment["profile_match"] = "good"
                elif risk_profile == "aggressive" and risk_level == "high":
                    risk_assessment["profile_match"] = "good"
                elif risk_profile == "conservative" and risk_level == "moderate":
                    risk_assessment["profile_match"] = "marginal"
                elif risk_profile == "moderate" and risk_level in ["low", "high"]:
                    risk_assessment["profile_match"] = "marginal"
                elif risk_profile == "aggressive" and risk_level == "moderate":
                    risk_assessment["profile_match"] = "marginal"
                else:
                    risk_assessment["profile_match"] = "poor"
            
            stock_analysis["risk_analysis"][ticker] = risk_assessment
            
            # Return assessment based on historical performance and time horizon
            return_assessment = {}
            if "annualized_return_pct" in stock_metrics:
                annualized_return = stock_metrics["annualized_return_pct"]
                
                if annualized_return < 0:
                    return_level = "negative"
                elif annualized_return < 5:
                    return_level = "low"
                elif annualized_return < 15:
                    return_level = "moderate"
                else:
                    return_level = "high"
                
                return_assessment["return_level"] = return_level
                return_assessment["return_assessment"] = f"{annualized_return:.2f}% annualized return indicates {return_level} return potential"
                
                # Return-to-risk assessment (Sharpe ratio)
                if "sharpe_ratio" in stock_metrics:
                    sharpe = stock_metrics["sharpe_ratio"]
                    
                    if sharpe < 0:
                        return_risk_assessment = "poor"
                    elif sharpe < 0.5:
                        return_risk_assessment = "suboptimal"
                    elif sharpe < 1:
                        return_risk_assessment = "adequate"
                    else:
                        return_risk_assessment = "excellent"
                    
                    return_assessment["return_to_risk"] = return_risk_assessment
                    return_assessment["sharpe_assessment"] = f"Sharpe ratio of {sharpe:.2f} indicates {return_risk_assessment} risk-adjusted return"
            
            stock_analysis["return_analysis"][ticker] = return_assessment
            
            # Valuation assessment
            valuation_assessment = {}
            if "pe_ratio" in stock_metrics:
                pe = stock_metrics["pe_ratio"]
                
                if pe < 10:
                    pe_assessment = "potentially undervalued"
                elif pe < 20:
                    pe_assessment = "fairly valued"
                else:
                    pe_assessment = "potentially overvalued"
                
                valuation_assessment["pe_assessment"] = f"P/E ratio of {pe:.2f} suggests stock is {pe_assessment} based on earnings"
            
            if "pb_ratio" in stock_metrics:
                pb = stock_metrics["pb_ratio"]
                
                if pb < 1:
                    pb_assessment = "potentially undervalued"
                elif pb < 3:
                    pb_assessment = "fairly valued"
                else:
                    pb_assessment = "potentially overvalued"
                
                valuation_assessment["pb_assessment"] = f"P/B ratio of {pb:.2f} suggests stock is {pb_assessment} based on book value"
            
            if valuation_assessment:
                stock_analysis["valuation_analysis"][ticker] = valuation_assessment
            
            # Generate recommendations based on analysis
            ticker_recommendations = []
            
            # Risk-based recommendation
            if "profile_match" in risk_assessment:
                match = risk_assessment["profile_match"]
                
                if match == "good":
                    ticker_recommendations.append(f"Risk profile aligns well with {ticker}'s volatility characteristics.")
                elif match == "marginal":
                    ticker_recommendations.append(f"Risk profile partially aligns with {ticker}'s volatility. Consider as a smaller allocation.")
                else:
                    ticker_recommendations.append(f"Risk profile doesn't align well with {ticker}'s volatility. Consider alternative investments.")
            
            # Return-based recommendation
            if "return_level" in return_assessment and "return_to_risk" in return_assessment:
                return_level = return_assessment["return_level"]
                risk_adj = return_assessment["return_to_risk"]
                
                if return_level in ["moderate", "high"] and risk_adj in ["adequate", "excellent"]:
                    ticker_recommendations.append(f"{ticker} shows strong return potential with favorable risk-adjusted performance.")
                elif return_level == "negative":
                    ticker_recommendations.append(f"{ticker} has shown negative returns historically. Thoroughly research before investing.")
            
            # Time horizon recommendation
            if time_horizon == "short_term" and "risk_level" in risk_assessment:
                risk_level = risk_assessment["risk_level"]
                
                if risk_level == "high":
                    ticker_recommendations.append(f"{ticker} may be too volatile for short-term investment horizon. Consider extending time horizon or reducing allocation.")
            
            # Valuation recommendation
            if "pe_assessment" in valuation_assessment or "pb_assessment" in valuation_assessment:
                pe_under = "potentially undervalued" in valuation_assessment.get("pe_assessment", "")
                pb_under = "potentially undervalued" in valuation_assessment.get("pb_assessment", "")
                
                if pe_under and pb_under:
                    ticker_recommendations.append(f"{ticker} appears undervalued based on both P/E and P/B metrics, representing a potential value opportunity.")
                elif "potentially overvalued" in valuation_assessment.get("pe_assessment", "") and "potentially overvalued" in valuation_assessment.get("pb_assessment", ""):
                    ticker_recommendations.append(f"{ticker} appears overvalued based on both P/E and P/B metrics. Consider waiting for a better entry point.")
            
            if ticker_recommendations:
                stock_analysis["recommendations"].extend(ticker_recommendations)
        
        # Add general recommendations
        general_recommendations = []
        
        # Portfolio construction recommendation
        if len(tickers) > 1:
            general_recommendations.append("Consider portfolio diversification across multiple stocks to reduce unsystematic risk.")
        
        # Risk profile recommendation
        if risk_profile == "conservative":
            general_recommendations.append("For a conservative risk profile, consider allocating more to blue-chip stocks with stable earnings and dividends.")
        elif risk_profile == "aggressive":
            general_recommendations.append("For an aggressive risk profile, you might accept higher volatility in exchange for growth potential.")
        
        # Time horizon recommendation
        if time_horizon == "long_term":
            general_recommendations.append("With a long-term horizon, you can potentially withstand short-term volatility for higher long-term returns.")
        
        stock_analysis["recommendations"].extend(general_recommendations)
        
        return stock_analysis

    def forecast_financial_metrics(
        self,
        historical_data: Optional[List[Dict[str, Any]]] = None,
        forecast_periods: Optional[int] = None,
        confidence_level: Optional[float] = None,
        seasonality: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Forecast financial metrics based on historical data using time series analysis.

        Args:
            historical_data: List of dictionaries with historical financial data.
            forecast_periods: Number of periods to forecast.
            confidence_level: Confidence level for prediction intervals (0-1).
            seasonality: Whether data has seasonality. Auto-detected if None.

        Returns:
            Dictionary with forecast results, including predicted values and confidence intervals.
        """
        # Set default values inside the function
        if historical_data is None:
            historical_data = []

        if forecast_periods is None:
            forecast_periods = 4

        if confidence_level is None:
            confidence_level = 0.95

        logger.info(f"Forecasting financial metrics for {forecast_periods} periods ahead")

        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame(historical_data)

            # Initialize results
            forecast_results = {
                "forecast_parameters": {
                    "periods": forecast_periods,
                    "confidence_level": confidence_level
                },
                "forecasts": {},
                "model_diagnostics": {},
                "recommendations": []
            }

            # Identify date column
            date_col = next((col for col in df.columns if any(date_term in col.lower()
                                                           for date_term in ['date', 'period', 'time', 'year', 'month'])), None)

            if not date_col:
                forecast_results["error"] = "No date column identified. Please specify a date column."
                return forecast_results

            # Ensure date column is datetime
            try:
                df[date_col] = pd.to_datetime(df[date_col])
            except:
                forecast_results["error"] = f"Could not convert {date_col} to datetime format."
                return forecast_results

            # Sort by date
            df = df.sort_values(by=date_col)

            # Identify numeric columns for forecasting
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col != date_col]

            if not numeric_cols:
                forecast_results["error"] = "No numeric columns identified for forecasting."
                return forecast_results

            # Check sufficient data points
            min_periods = 2 * forecast_periods
            if len(df) < min_periods:
                forecast_results["warning"] = f"Limited historical data ({len(df)} points) may lead to unreliable forecasts. Recommend at least {min_periods} periods."

            # For each metric, generate forecast
            for metric in numeric_cols:
                # Skip if more than 20% of values are missing
                missing_pct = df[metric].isna().sum() / len(df) * 100
                if missing_pct > 20:
                    forecast_results["forecasts"][metric] = {
                        "error": f"Too many missing values ({missing_pct:.1f}%) for reliable forecasting."
                    }
                    continue

                # Fill missing values with interpolation
                values = df[metric].interpolate(method='linear').values

                # Skip if all values are the same (no variance)
                if np.std(values) < 1e-10:
                    forecast_results["forecasts"][metric] = {
                        "error": "No variance in historical data, cannot forecast."
                    }
                    continue

                # Determine if the series is stationary
                try:
                    adf_result = adfuller(values)
                    is_stationary = adf_result[1] < 0.05  # p-value < 0.05 indicates stationarity

                    # Add stationarity info to diagnostics
                    forecast_results["model_diagnostics"][metric] = {
                        "stationary": is_stationary,
                        "adf_p_value": adf_result[1]
                    }
                except:
                    # If ADF test fails, assume non-stationarity
                    is_stationary = False

                # Auto-detect seasonality if not specified
                if seasonality is None:
                    # Need at least 2 full cycles to detect seasonality
                    if len(values) >= 8:
                        try:
                            # Check quarterly seasonality
                            decomposition = seasonal_decompose(values, model='additive', period=4)
                            seasonal_comp = decomposition.seasonal

                            # If seasonal component has significant magnitude relative to trend, assume seasonality
                            seasonal_strength = np.std(seasonal_comp) / np.std(values)
                            has_seasonality = seasonal_strength > 0.1
                        except:
                            has_seasonality = False
                    else:
                        has_seasonality = False
                else:
                    has_seasonality = seasonality

                # Update diagnostics with seasonality info
                if "model_diagnostics" in forecast_results and metric in forecast_results["model_diagnostics"]:
                    forecast_results["model_diagnostics"][metric]["seasonal"] = has_seasonality

                # Choose appropriate forecasting model
                forecast_values = []
                forecast_lower = []
                forecast_upper = []

                try:
                    # Use ARIMA model with differencing for non-stationary series
                    if not is_stationary:
                        # Simple differencing to make stationary
                        d = 1
                    else:
                        d = 0

                    # Set seasonal component if detected
                    if has_seasonality:
                        # Seasonal ARIMA with quarterly seasonality (4)
                        model = ARIMA(values, order=(1, d, 1), seasonal_order=(1, 1, 1, 4))
                    else:
                        model = ARIMA(values, order=(1, d, 1))

                    # Fit model
                    model_fit = model.fit()

                    # Generate forecast
                    forecast = model_fit.get_forecast(steps=forecast_periods)
                    forecast_values = forecast.predicted_mean

                    # Generate prediction intervals
                    alpha = 1 - confidence_level
                    intervals = forecast.conf_int(alpha=alpha)
                    forecast_lower = intervals.iloc[:, 0].values
                    forecast_upper = intervals.iloc[:, 1].values

                    # Calculate model fit statistics
                    aic = model_fit.aic
                    bic = model_fit.bic

                    # Add to diagnostics
                    if metric in forecast_results["model_diagnostics"]:
                        forecast_results["model_diagnostics"][metric].update({
                            "model_type": "Seasonal ARIMA" if has_seasonality else "ARIMA",
                            "order": str((1, d, 1)),
                            "seasonal_order": str((1, 1, 1, 4)) if has_seasonality else "None",
                            "aic": aic,
                            "bic": bic
                        })

                except Exception as e:
                    # If ARIMA fails, use simple moving average or exponential smoothing
                    try:
                        # Calculate growth rate for exponential approach
                        if all(v > 0 for v in values):
                            # Average period-over-period growth rate
                            growth_rates = [values[i] / values[i-1] - 1 for i in range(1, len(values))]
                            avg_growth = np.mean(growth_rates)

                            # Project forward with growth rate
                            last_value = values[-1]
                            forecast_values = [last_value * (1 + avg_growth) ** (i+1) for i in range(forecast_periods)]

                            # Simple confidence intervals based on historical volatility
                            std_dev = np.std(growth_rates)
                            z_score = stats.norm.ppf(confidence_level)

                            forecast_lower = [forecast_values[i] * (1 - z_score * std_dev) for i in range(forecast_periods)]
                            forecast_upper = [forecast_values[i] * (1 + z_score * std_dev) for i in range(forecast_periods)]

                            forecast_results["model_diagnostics"][metric] = {
                                "model_type": "Growth Rate Projection",
                                "average_growth_rate": avg_growth,
                                "growth_volatility": std_dev
                            }
                        else:
                            # Simple moving average for data with zeros or negatives
                            window = min(4, len(values) // 2)
                            ma = np.mean(values[-window:])
                            forecast_values = [ma] * forecast_periods

                            # Simple prediction intervals
                            std_dev = np.std(values[-window:])
                            z_score = stats.norm.ppf(confidence_level)
                            margin = z_score * std_dev

                            forecast_lower = [ma - margin] * forecast_periods
                            forecast_upper = [ma + margin] * forecast_periods

                            forecast_results["model_diagnostics"][metric] = {
                                "model_type": "Moving Average",
                                "window": window
                            }
                    except Exception as inner_e:
                        forecast_results["forecasts"][metric] = {
                            "error": f"Failed to generate forecast: {str(inner_e)}"
                        }
                        continue

                # Generate dates for forecast periods
                last_date = df[date_col].iloc[-1]

                # Determine date frequency from data
                try:
                    date_diff = df[date_col].diff().median()

                    if pd.isna(date_diff):
                        # Default to quarters if can't determine frequency
                        date_freq = pd.DateOffset(months=3)
                    else:
                        days = date_diff.days
                        if days <= 1:
                            date_freq = pd.DateOffset(days=1)
                        elif days <= 7:
                            date_freq = pd.DateOffset(weeks=1)
                        elif days <= 31:
                            date_freq = pd.DateOffset(months=1)
                        elif days <= 100:
                            date_freq = pd.DateOffset(months=3)
                        elif days <= 200:
                            date_freq = pd.DateOffset(months=6)
                        else:
                            date_freq = pd.DateOffset(years=1)
                except:
                    # Default to quarterly if error
                    date_freq = pd.DateOffset(months=3)

                forecast_dates = [(last_date + (i+1) * date_freq).strftime('%Y-%m-%d') for i in range(forecast_periods)]

                # Store forecast results
                forecast_results["forecasts"][metric] = {
                    "dates": forecast_dates,
                    "values": forecast_values.tolist() if isinstance(forecast_values, np.ndarray) else list(forecast_values),
                    "lower_bound": forecast_lower.tolist() if isinstance(forecast_lower, np.ndarray) else list(forecast_lower),
                    "upper_bound": forecast_upper.tolist() if isinstance(forecast_upper, np.ndarray) else list(forecast_upper),
                    "confidence_level": confidence_level
                }

            # Generate forecast recommendations
            recommendations = []

            # Check for significant trends in forecasts
            significant_uptrends = []
            significant_downtrends = []

            for metric, forecast in forecast_results["forecasts"].items():
                if "values" not in forecast:
                    continue

                values = forecast["values"]
                if len(values) < 2:
                    continue

                first_value = values[0]
                last_value = values[-1]

                if first_value == 0:
                    continue

                percent_change = (last_value - first_value) / abs(first_value) * 100

                if percent_change > 20:
                    significant_uptrends.append((metric, percent_change))
                elif percent_change < -15:
                    significant_downtrends.append((metric, percent_change))

            # Add trend-based recommendations
            if significant_uptrends:
                top_uptrends = sorted(significant_uptrends, key=lambda x: x[1], reverse=True)[:3]
                metrics_list = ", ".join([f"{metric} (+{pct:.1f}%)" for metric, pct in top_uptrends])
                recommendations.append(f"Strong positive trends forecasted in {metrics_list}. Consider strategies to capitalize on these expected improvements.")

            if significant_downtrends:
                top_downtrends = sorted(significant_downtrends, key=lambda x: x[1])[:3]
                metrics_list = ", ".join([f"{metric} ({pct:.1f}%)" for metric, pct in top_downtrends])
                recommendations.append(f"Concerning negative trends forecasted in {metrics_list}. Develop mitigation strategies or contingency plans for these potential declines.")

            # Check forecast volatility
            high_uncertainty_metrics = []

            for metric, forecast in forecast_results["forecasts"].items():
                if "values" not in forecast or "upper_bound" not in forecast or "lower_bound" not in forecast:
                    continue

                values = forecast["values"]
                upper = forecast["upper_bound"]
                lower = forecast["lower_bound"]

                # Calculate average forecast range as percentage of forecast value
                ranges = [(upper[i] - lower[i]) / abs(values[i]) * 100 if values[i] != 0 else float('inf')
                        for i in range(len(values))]

                avg_range = sum(r for r in ranges if not math.isinf(r)) / len([r for r in ranges if not math.isinf(r)]) if ranges else 0

                if avg_range > 50:
                    high_uncertainty_metrics.append((metric, avg_range))

            if high_uncertainty_metrics:
                metrics_list = ", ".join([metric for metric, _ in high_uncertainty_metrics[:3]])
                recommendations.append(f"High forecast uncertainty detected in {metrics_list}. Consider scenario planning with multiple potential outcomes for these metrics.")

            # Add data quality recommendations
            if len(df) < 8:
                recommendations.append("Limited historical data may impact forecast reliability. Consider collecting additional historical data points to improve forecast accuracy.")

            # Check for seasonality
            seasonal_metrics = []
            for metric, diagnostics in forecast_results["model_diagnostics"].items():
                if diagnostics.get("seasonal", False):
                    seasonal_metrics.append(metric)

            if seasonal_metrics:
                metrics_list = ", ".join(seasonal_metrics[:3])
                recommendations.append(f"Seasonal patterns detected in {metrics_list}. Ensure planning accounts for this cyclicality and consider seasonally-adjusted analysis.")

            # Add recommendations to results
            forecast_results["recommendations"] = recommendations

            return forecast_results

        except Exception as e:
            logger.error(f"Error forecasting financial metrics: {str(e)}")
            return {
                "error": f"Error forecasting financial metrics: {str(e)}",
                "forecast_periods": forecast_periods
            }

    def assess_financial_risk(
        self,
        financial_data: Optional[List[Dict[str, Any]]] = None,
        risk_types: Optional[List[str]] = None,
        stress_scenarios: Optional[List[Dict[str, Any]]] = None,
        confidence_level: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Assess various financial risks based on financial data and parameters.

        Args:
            financial_data: List of dictionaries with financial data.
            risk_types: Optional list of risk types to assess (e.g., "market", "credit", "liquidity").
            stress_scenarios: Optional list of stress scenarios to model.
            confidence_level: Confidence level for risk metrics (0-1).

        Returns:
            Dictionary with detailed risk assessment results.
        """
        # Set default values inside the function
        if financial_data is None:
            financial_data = []
        
        if risk_types is None:
            risk_types = ["market", "liquidity", "credit", "operational"]
            
        if stress_scenarios is None:
            stress_scenarios = []
            
        if confidence_level is None:
            confidence_level = 0.95
        
        logger.info(f"Assessing financial risks with {len(financial_data)} data points")

        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame(financial_data)

            # Initialize results
            risk_assessment = {
                "risk_parameters": {
                    "risk_types": risk_types,
                    "confidence_level": confidence_level
                },
                "risk_metrics": {},
                "risk_exposure": {},
                "scenario_analysis": {},
                "recommendations": []
            }

            # Process each risk type
            for risk_type in risk_types:
                if risk_type.lower() == "market":
                    market_risk = self._assess_market_risk(df, confidence_level)
                    risk_assessment["risk_metrics"]["market_risk"] = market_risk

                elif risk_type.lower() == "credit":
                    credit_risk = self._assess_credit_risk(df, confidence_level)
                    risk_assessment["risk_metrics"]["credit_risk"] = credit_risk

                elif risk_type.lower() == "liquidity":
                    liquidity_risk = self._assess_liquidity_risk(df, confidence_level)
                    risk_assessment["risk_metrics"]["liquidity_risk"] = liquidity_risk

                elif risk_type.lower() == "operational":
                    operational_risk = self._assess_operational_risk(df, confidence_level)
                    risk_assessment["risk_metrics"]["operational_risk"] = operational_risk

            # Run stress scenario analysis if provided
            if stress_scenarios:
                for i, scenario in enumerate(stress_scenarios):
                    scenario_name = scenario.get("name", f"Scenario {i+1}")
                    scenario_results = self._run_stress_scenario(df, scenario)
                    risk_assessment["scenario_analysis"][scenario_name] = scenario_results

            # Generate risk exposure assessment
            risk_exposure = {}

            # Check for overall risk exposure
            high_risk_areas = []

            for risk_type, metrics in risk_assessment["risk_metrics"].items():
                if "risk_level" in metrics and metrics["risk_level"] in ["high", "very high"]:
                    high_risk_areas.append(risk_type)

                    # Extract key metrics for exposure summary
                    key_metrics = {k: v for k, v in metrics.items()
                                if k in ["risk_level", "var_value", "expected_loss", "key_ratios"]}
                    risk_exposure[risk_type] = key_metrics

            risk_assessment["risk_exposure"] = risk_exposure

            # Generate recommendations based on risk assessment
            recommendations = []

            # High risk area recommendations
            if high_risk_areas:
                risk_areas = ", ".join(high_risk_areas)
                recommendations.append(f"Elevated risk identified in {risk_areas}. Prioritize risk mitigation strategies in these areas.")

            # Market risk recommendations
            if "market_risk" in risk_assessment["risk_metrics"]:
                market_metrics = risk_assessment["risk_metrics"]["market_risk"]

                if "var_value" in market_metrics:
                    var_value = market_metrics["var_value"]
                    var_pct = market_metrics.get("var_percentage", 0)

                    if var_pct > 10:
                        recommendations.append(f"High Value-at-Risk ({var_pct:.2f}%) indicates significant market exposure. Consider hedging strategies or reducing position sizes in volatile assets.")

                if "volatility" in market_metrics and market_metrics["volatility"] > 20:
                    recommendations.append("High market volatility detected. Review portfolio diversification and implement volatility-reducing strategies.")

            # Credit risk recommendations
            if "credit_risk" in risk_assessment["risk_metrics"]:
                credit_metrics = risk_assessment["risk_metrics"]["credit_risk"]

                if "expected_loss" in credit_metrics:
                    el_pct = credit_metrics.get("expected_loss_percentage", 0)

                    if el_pct > 5:
                        recommendations.append(f"High expected credit losses ({el_pct:.2f}%). Review credit policies, consider tightening lending standards, or implement additional collateral requirements.")

                if "concentration_risk" in credit_metrics and credit_metrics["concentration_risk"] == "high":
                    recommendations.append("High credit concentration risk. Diversify credit exposure across counterparties, industries, and geographic regions.")
                # Liquidity risk recommendations
            if "liquidity_risk" in risk_assessment["risk_metrics"]:
                liquidity_metrics = risk_assessment["risk_metrics"]["liquidity_risk"]

                if "current_ratio" in liquidity_metrics:
                    current_ratio = liquidity_metrics["current_ratio"]

                    if current_ratio < 1:
                        recommendations.append(f"Current ratio ({current_ratio:.2f}) below 1.0 indicates potential short-term liquidity issues. Develop strategies to improve working capital management.")

                if "cash_burn_rate" in liquidity_metrics:
                    months_of_runway = liquidity_metrics.get("months_of_runway", 0)

                    if months_of_runway < 6:
                        recommendations.append(f"Limited liquidity runway ({months_of_runway:.1f} months). Consider capital raising, expense reduction, or accelerating accounts receivable collection.")

            # Scenario-based recommendations
            if risk_assessment["scenario_analysis"]:
                severe_impact_scenarios = []

                for scenario_name, results in risk_assessment["scenario_analysis"].items():
                    if "impact_level" in results and results["impact_level"] in ["severe", "critical"]:
                        severe_impact_scenarios.append(scenario_name)

                if severe_impact_scenarios:
                    scenarios_list = ", ".join(severe_impact_scenarios)
                    recommendations.append(f"Severe potential impact identified in scenarios: {scenarios_list}. Develop specific contingency plans for these scenarios.")

            # General risk management recommendations
            if len(risk_types) > 2:
                recommendations.append("Implement integrated risk management framework to holistically address multiple risk factors and their interdependencies.")

            recommendations.append("Regularly review and update risk assessments as market conditions and business operations evolve.")

            # Add recommendations to results
            risk_assessment["recommendations"] = recommendations

            return risk_assessment

        except Exception as e:
            logger.error(f"Error assessing financial risks: {str(e)}")
            return {
                "error": f"Error assessing financial risks: {str(e)}",
                "risk_types": risk_types
            }

    def _assess_market_risk(self, df: pd.DataFrame, confidence_level: float) -> Dict[str, Any]:
        """Assess market risk based on financial data."""
        market_risk = {}

        # Check for required price/return data
        price_col = next((col for col in df.columns if 'price' in col.lower()), None)
        return_col = next((col for col in df.columns if 'return' in col.lower()), None)

        # If we have a date column, sort by it
        date_col = next((col for col in df.columns if any(term in col.lower() for term in
                                                     ['date', 'time', 'period', 'year', 'month'])), None)
        if date_col:
            try:
                df = df.sort_values(by=date_col)
            except:
                pass

        # Calculate returns if we have price but not returns
        if price_col and not return_col:
            try:
                # Calculate percentage returns
                df['return'] = df[price_col].pct_change()
                return_col = 'return'
            except:
                pass

        # Assess market risk if we have returns
        if return_col:
            try:
                returns = df[return_col].dropna().values

                # Calculate volatility
                volatility = np.std(returns) * 100  # as percentage
                annualized_vol = volatility * np.sqrt(252)  # annualized assuming daily data

                market_risk["volatility"] = volatility
                market_risk["annualized_volatility"] = annualized_vol

                # Determine risk level based on volatility
                if annualized_vol < 10:
                    risk_level = "low"
                elif annualized_vol < 20:
                    risk_level = "moderate"
                elif annualized_vol < 30:
                    risk_level = "high"
                else:
                    risk_level = "very high"

                market_risk["risk_level"] = risk_level

                # Calculate Value-at-Risk (VaR)
                # Using historical method for simplicity
                alpha = 1 - confidence_level
                var_value = np.percentile(returns, alpha * 100)

                market_risk["var_value"] = var_value
                market_risk["var_percentage"] = abs(var_value) * 100
                market_risk["var_confidence"] = confidence_level

                # Calculate Conditional VaR (Expected Shortfall)
                cvar_values = returns[returns <= var_value]
                if len(cvar_values) > 0:
                    cvar = np.mean(cvar_values)
                    market_risk["cvar_value"] = cvar
                    market_risk["cvar_percentage"] = abs(cvar) * 100

                # Calculate max drawdown if sufficient data
                if len(returns) > 10:
                    # Convert returns to price series (starting at 100)
                    prices = 100 * (1 + returns).cumprod()

                    # Calculate drawdown
                    peak = np.maximum.accumulate(prices)
                    drawdown = (peak - prices) / peak
                    max_drawdown = np.max(drawdown)

                    market_risk["max_drawdown"] = max_drawdown
                    market_risk["max_drawdown_percentage"] = max_drawdown * 100
            except Exception as e:
                market_risk["error"] = f"Error calculating market risk metrics: {str(e)}"
        else:
            market_risk["error"] = "Insufficient data for market risk assessment. Requires price or return data."

        return market_risk

    def _assess_credit_risk(self, df: pd.DataFrame, confidence_level: float) -> Dict[str, Any]:
        """Assess credit risk based on financial data."""
        credit_risk = {}

        # Look for credit-related columns
        loan_col = next((col for col in df.columns if 'loan' in col.lower() or 'debt' in col.lower()), None)
        default_rate_col = next((col for col in df.columns if 'default' in col.lower() or 'delinquency' in col.lower()), None)
        rating_col = next((col for col in df.columns if 'rating' in col.lower() or 'score' in col.lower()), None)

        has_credit_data = loan_col is not None or default_rate_col is not None or rating_col is not None

        if not has_credit_data:
            credit_risk["error"] = "Insufficient data for credit risk assessment."
            credit_risk["risk_level"] = "unknown"
            return credit_risk

        # Calculate basic credit metrics
        if loan_col:
            try:
                total_loans = df[loan_col].sum()
                credit_risk["total_exposure"] = total_loans

                # Check for concentration
                if 'counterparty' in df.columns or 'borrower' in df.columns:
                    counterparty_col = 'counterparty' if 'counterparty' in df.columns else 'borrower'

                    # Calculate concentration by counterparty
                    concentration = df.groupby(counterparty_col)[loan_col].sum() / total_loans * 100
                    max_concentration = concentration.max()
                    top5_concentration = concentration.nlargest(5).sum()

                    credit_risk["max_counterparty_exposure_pct"] = max_concentration
                    credit_risk["top5_concentration_pct"] = top5_concentration

                    # Assess concentration risk
                    if max_concentration > 25 or top5_concentration > 60:
                        credit_risk["concentration_risk"] = "high"
                    elif max_concentration > 15 or top5_concentration > 40:
                        credit_risk["concentration_risk"] = "moderate"
                    else:
                        credit_risk["concentration_risk"] = "low"
            except Exception as e:
                credit_risk["error_exposure"] = f"Error calculating exposure metrics: {str(e)}"

        # Calculate expected loss if we have default rates
        if default_rate_col:
            try:
                avg_default_rate = df[default_rate_col].mean()
                credit_risk["average_default_rate"] = avg_default_rate

                # Calculate expected loss if we have both loans and default rates
                if loan_col:
                    # Simple expected loss calculation
                    # Ideally would include LGD (Loss Given Default) but using 50% as proxy
                    lgd = 0.5  # Loss Given Default assumption
                    expected_loss = total_loans * avg_default_rate * lgd

                    credit_risk["expected_loss"] = expected_loss
                    credit_risk["expected_loss_percentage"] = expected_loss / total_loans * 100

                    # Determine risk level based on expected loss percentage
                    el_pct = credit_risk["expected_loss_percentage"]

                    if el_pct < 1:
                        risk_level = "low"
                    elif el_pct < 3:
                        risk_level = "moderate"
                    elif el_pct < 7:
                        risk_level = "high"
                    else:
                        risk_level = "very high"

                    credit_risk["risk_level"] = risk_level
            except Exception as e:
                credit_risk["error_loss"] = f"Error calculating expected loss: {str(e)}"
        
        # Credit quality assessment if we have ratings
        if rating_col:
            try:
                # Count ratings distribution
                ratings_dist = df[rating_col].value_counts().to_dict()

                # Check if ratings are already numerical
                try:
                    # Try to convert to numeric if not already
                    if not pd.api.types.is_numeric_dtype(df[rating_col]):
                        # Common ratings mapping (approximate)
                        ratings_map = {
                            'AAA': 1, 'AA+': 2, 'AA': 3, 'AA-': 4,
                            'A+': 5, 'A': 6, 'A-': 7,
                            'BBB+': 8, 'BBB': 9, 'BBB-': 10,
                            'BB+': 11, 'BB': 12, 'BB-': 13,
                            'B+': 14, 'B': 15, 'B-': 16,
                            'CCC+': 17, 'CCC': 18, 'CCC-': 19,
                            'CC': 20, 'C': 21, 'D': 22
                        }

                        # For numeric scores (e.g., 1-10 scale or credit scores)
                        if not any(r in str(df[rating_col].iloc[0]) for r in ratings_map.keys()):
                            # Assume higher is riskier for numeric scores
                            avg_rating = df[rating_col].mean()
                        else:
                            # Convert letter ratings to numbers and calculate average
                            mapped_ratings = df[rating_col].map(ratings_map).dropna()
                            if len(mapped_ratings) > 0:
                                avg_rating = mapped_ratings.mean()
                            else:
                                avg_rating = None
                    else:
                        avg_rating = df[rating_col].mean()

                    if avg_rating is not None:
                        credit_risk["average_rating"] = avg_rating

                        # Determine risk level based on average rating
                        # This is a simplification and would depend on the specific rating scale
                        if avg_rating < 7:  # Investment grade equivalent
                            risk_level = "low"
                        elif avg_rating < 13:  # BB range equivalent
                            risk_level = "moderate"
                        elif avg_rating < 17:  # B range equivalent
                            risk_level = "high"
                        else:  # CCC or lower equivalent
                            risk_level = "very high"

                        credit_risk["risk_level"] = risk_level
                except:
                    # If conversion fails, use distribution instead
                    credit_risk["ratings_distribution"] = ratings_dist
            except Exception as e:
                credit_risk["error_ratings"] = f"Error analyzing credit ratings: {str(e)}"

        # If no risk level determined yet, set default
        if "risk_level" not in credit_risk:
            credit_risk["risk_level"] = "moderate"  # Default if we can't determine

        return credit_risk

    def _assess_liquidity_risk(self, df: pd.DataFrame, confidence_level: float) -> Dict[str, Any]:
        """Assess liquidity risk based on financial data."""
        liquidity_risk = {}

        # Look for liquidity-related columns
        cash_col = next((col for col in df.columns if 'cash' in col.lower() or 'liquidity' in col.lower()), None)
        current_assets_col = next((col for col in df.columns if 'current assets' in col.lower()), None)
        current_liab_col = next((col for col in df.columns if 'current liabilities' in col.lower()), None)

        # Check for cash flow related columns
        cf_col = next((col for col in df.columns if 'cash flow' in col.lower() or 'cf' in col.lower()), None)
        burn_rate_col = next((col for col in df.columns if 'burn' in col.lower() or 'spend' in col.lower()), None)

        has_liquidity_data = cash_col is not None or current_assets_col is not None or cf_col is not None

        if not has_liquidity_data:
            liquidity_risk["error"] = "Insufficient data for liquidity risk assessment."
            liquidity_risk["risk_level"] = "unknown"
            return liquidity_risk

        # Calculate liquidity ratios if we have current assets and liabilities
        if current_assets_col and current_liab_col:
            try:
                # Get latest values if we have multiple periods
                if len(df) > 1:
                    current_assets = df[current_assets_col].iloc[-1]
                    current_liab = df[current_liab_col].iloc[-1]
                else:
                    current_assets = df[current_assets_col].iloc[0]
                    current_liab = df[current_liab_col].iloc[0]

                # Current ratio
                if current_liab != 0:
                    current_ratio = current_assets / current_liab
                    liquidity_risk["current_ratio"] = current_ratio

                    # Quick ratio if we have inventory
                    inventory_col = next((col for col in df.columns if 'inventory' in col.lower()), None)
                    if inventory_col:
                        inventory = df[inventory_col].iloc[-1] if len(df) > 1 else df[inventory_col].iloc[0]
                        quick_ratio = (current_assets - inventory) / current_liab
                        liquidity_risk["quick_ratio"] = quick_ratio

                    # Determine risk level based on current ratio
                    if current_ratio < 1:
                        risk_level = "high"
                    elif current_ratio < 1.5:
                        risk_level = "moderate"
                    else:
                        risk_level = "low"

                    liquidity_risk["risk_level"] = risk_level
            except Exception as e:
                liquidity_risk["error_ratios"] = f"Error calculating liquidity ratios: {str(e)}"

        # Cash burn rate analysis if we have cash and burn rate or cash flow
        if cash_col and (burn_rate_col or cf_col):
            try:
                # Get latest cash position
                latest_cash = df[cash_col].iloc[-1] if len(df) > 1 else df[cash_col].iloc[0]
                liquidity_risk["cash_position"] = latest_cash

                # Calculate burn rate or use provided burn rate
                if burn_rate_col:
                    burn_rate = df[burn_rate_col].iloc[-1] if len(df) > 1 else df[burn_rate_col].iloc[0]
                elif cf_col and len(df) > 1:
                    # Estimate burn rate from average negative cash flow
                    cf_values = df[cf_col].values
                    neg_cf = [v for v in cf_values if v < 0]

                    if neg_cf:
                        burn_rate = abs(np.mean(neg_cf))
                    else:
                        burn_rate = 0
                else:
                    burn_rate = 0

                liquidity_risk["cash_burn_rate"] = burn_rate

                # Calculate runway if burn rate is positive
                if burn_rate > 0:
                    runway_months = latest_cash / burn_rate
                    liquidity_risk["months_of_runway"] = runway_months

                    # Assess risk based on runway
                    if runway_months < 6:
                        runway_risk = "high"
                    elif runway_months < 12:
                        runway_risk = "moderate"
                    else:
                        runway_risk = "low"

                    liquidity_risk["runway_risk"] = runway_risk

                    # Update overall risk level if not already set
                    if "risk_level" not in liquidity_risk:
                        liquidity_risk["risk_level"] = runway_risk
            except Exception as e:
                liquidity_risk["error_runway"] = f"Error calculating cash runway: {str(e)}"

        # If no risk level determined yet, set default
        if "risk_level" not in liquidity_risk:
            liquidity_risk["risk_level"] = "moderate"  # Default if we can't determine

        return liquidity_risk

    def _assess_operational_risk(self, df: pd.DataFrame, confidence_level: float) -> Dict[str, Any]:
        """Assess operational risk based on financial data."""
        operational_risk = {
            "risk_level": "moderate"  # Default risk level
        }

        # Look for operational risk indicators
        operational_indicators = {
            'expense_volatility': None,
            'margin_volatility': None,
            'operational_losses': None,
            'efficiency_ratio': None
        }

        # Check for expense volatility
        expense_col = next((col for col in df.columns if 'expense' in col.lower() or 'cost' in col.lower()), None)
        if expense_col and len(df) > 3:
            try:
                expenses = df[expense_col].values
                expense_volatility = np.std(expenses) / np.mean(expenses) * 100 if np.mean(expenses) != 0 else 0
                operational_indicators['expense_volatility'] = expense_volatility

                # Assess expense volatility risk
                if expense_volatility > 20:
                    operational_risk["expense_volatility_risk"] = "high"
                elif expense_volatility > 10:
                    operational_risk["expense_volatility_risk"] = "moderate"
                else:
                    operational_risk["expense_volatility_risk"] = "low"
            except:
                pass

        # Check for margin volatility
        margin_col = next((col for col in df.columns if 'margin' in col.lower() or 'profit' in col.lower()), None)
        if margin_col and len(df) > 3:
            try:
                margins = df[margin_col].values
                margin_volatility = np.std(margins) / abs(np.mean(margins)) * 100 if np.mean(margins) != 0 else 0
                operational_indicators['margin_volatility'] = margin_volatility

                # Assess margin volatility risk
                if margin_volatility > 30:
                    operational_risk["margin_volatility_risk"] = "high"
                elif margin_volatility > 15:
                    operational_risk["margin_volatility_risk"] = "moderate"
                else:
                    operational_risk["margin_volatility_risk"] = "low"
            except:
                pass

        # Check for operational losses
        loss_col = next((col for col in df.columns if 'loss' in col.lower() or 'incident' in col.lower()), None)
        if loss_col:
            try:
                losses = df[loss_col].values
                total_losses = np.sum(losses)
                operational_indicators['operational_losses'] = total_losses

                # If we have revenue data, assess losses as percentage of revenue
                revenue_col = next((col for col in df.columns if 'revenue' in col.lower() or 'sales' in col.lower()), None)
                if revenue_col:
                    total_revenue = np.sum(df[revenue_col].values)
                    if total_revenue > 0:
                        loss_pct = total_losses / total_revenue * 100
                        operational_risk["operational_loss_pct"] = loss_pct

                        # Assess loss risk
                        if loss_pct > 5:
                            operational_risk["operational_loss_risk"] = "high"
                        elif loss_pct > 2:
                            operational_risk["operational_loss_risk"] = "moderate"
                        else:
                            operational_risk["operational_loss_risk"] = "low"
            except:
                pass

        # Check for efficiency ratio
        if expense_col and 'revenue' in df.columns:
            try:
                expenses = df[expense_col].values
                revenues = df['revenue'].values

                if np.sum(revenues) > 0:
                    efficiency_ratio = np.sum(expenses) / np.sum(revenues) * 100
                    operational_indicators['efficiency_ratio'] = efficiency_ratio
                    operational_risk["efficiency_ratio"] = efficiency_ratio

                    # Assess efficiency risk
                    if efficiency_ratio > 80:
                        operational_risk["efficiency_risk"] = "high"
                    elif efficiency_ratio > 60:
                        operational_risk["efficiency_risk"] = "moderate"
                    else:
                        operational_risk["efficiency_risk"] = "low"
            except:
                pass

        # Store all operational indicators
        operational_risk["operational_indicators"] = {k: v for k, v in operational_indicators.items() if v is not None}

        # Determine overall operational risk level
        risk_levels = [v for k, v in operational_risk.items() if k.endswith('_risk') and k != 'risk_level']

        if risk_levels:
            high_count = risk_levels.count("high")
            moderate_count = risk_levels.count("moderate")

            if high_count > len(risk_levels) / 3:
                operational_risk["risk_level"] = "high"
            elif high_count + moderate_count > len(risk_levels) / 2:
                operational_risk["risk_level"] = "moderate"
            else:
                operational_risk["risk_level"] = "low"

        return operational_risk

    def _run_stress_scenario(self, df: pd.DataFrame, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run stress scenario analysis on financial data."""
        scenario_results = {
            "scenario_parameters": scenario.get("parameters", {}),
            "impact_metrics": {}
        }

        # Get scenario parameters
        scenario_shocks = scenario.get("shocks", {})

        # Check if we have necessary columns
        for shock_variable in scenario_shocks.keys():
            if shock_variable not in df.columns:
                scenario_results["error"] = f"Shock variable {shock_variable} not found in data."
                return scenario_results

        try:
            # Create copy of dataframe for scenario
            scenario_df = df.copy()

            # Apply shocks to variables
            for variable, shock_value in scenario_shocks.items():
                if isinstance(shock_value, dict):
                    # Handle percentage shocks
                    if "percentage" in shock_value:
                        pct_change = shock_value["percentage"] / 100
                        scenario_df[variable] = df[variable] * (1 + pct_change)
                    # Handle absolute shocks
                    elif "absolute" in shock_value:
                        abs_change = shock_value["absolute"]
                        scenario_df[variable] = df[variable] + abs_change
                else:
                    # Direct value replacement
                    scenario_df[variable] = shock_value

            # Calculate impact on key metrics
            impact_metrics = {}

            # Check for P&L impact if we have revenue and expense columns
            revenue_col = next((col for col in df.columns if 'revenue' in col.lower() or 'sales' in col.lower()), None)
            expense_col = next((col for col in df.columns if 'expense' in col.lower() or 'cost' in col.lower()), None)

            if revenue_col and expense_col:
                # Base case P&L
                base_revenue = df[revenue_col].sum()
                base_expense = df[expense_col].sum()
                base_profit = base_revenue - base_expense

                # Scenario P&L
                scenario_revenue = scenario_df[revenue_col].sum()
                scenario_expense = scenario_df[expense_col].sum()
                scenario_profit = scenario_revenue - scenario_expense

                # Calculate impact
                profit_impact = scenario_profit - base_profit
                profit_impact_pct = profit_impact / abs(base_profit) * 100 if base_profit != 0 else float('inf')

                impact_metrics["profit_impact"] = profit_impact
                impact_metrics["profit_impact_pct"] = profit_impact_pct

                # Assess impact level
                if profit_impact_pct < -50:
                    impact_level = "critical"
                elif profit_impact_pct < -25:
                    impact_level = "severe"
                elif profit_impact_pct < -10:
                    impact_level = "moderate"
                else:
                    impact_level = "minor"

                impact_metrics["impact_level"] = impact_level

            # Check for cashflow impact if available
            cash_col = next((col for col in df.columns if 'cash' in col.lower() or 'cf' in col.lower()), None)

            if cash_col:
                # Base case cash
                base_cash = df[cash_col].sum()

                # Scenario cash
                scenario_cash = scenario_df[cash_col].sum()

                # Calculate impact
                cash_impact = scenario_cash - base_cash
                cash_impact_pct = cash_impact / abs(base_cash) * 100 if base_cash != 0 else float('inf')

                impact_metrics["cash_impact"] = cash_impact
                impact_metrics["cash_impact_pct"] = cash_impact_pct

                # If impact level not already set, assess based on cash
                if "impact_level" not in impact_metrics:
                    if cash_impact_pct < -50:
                        impact_level = "critical"
                    elif cash_impact_pct < -25:
                        impact_level = "severe"
                    elif cash_impact_pct < -10:
                        impact_level = "moderate"
                    else:
                        impact_level = "minor"

                    impact_metrics["impact_level"] = impact_level

            # Add impact metrics to results
            scenario_results["impact_metrics"] = impact_metrics

            # Add mitigation suggestions if impact is significant
            if impact_metrics.get("impact_level") in ["moderate", "severe", "critical"]:
                mitigations = []

                # General mitigations based on scenario
                for variable in scenario_shocks.keys():
                    if "revenue" in variable.lower() or "sales" in variable.lower():
                        mitigations.append("Diversify revenue streams to reduce dependency on affected channels.")
                    elif "cost" in variable.lower() or "expense" in variable.lower():
                        mitigations.append("Implement cost control measures and identify variable costs that can be reduced.")
                    elif "rate" in variable.lower() or "interest" in variable.lower():
                        mitigations.append("Consider hedging strategies to mitigate interest rate risk.")
                    elif "exchange" in variable.lower() or "fx" in variable.lower():
                        mitigations.append("Implement currency hedging strategies or natural hedges through matching revenue and expense currencies.")
                    elif "default" in variable.lower() or "credit" in variable.lower():
                        mitigations.append("Strengthen credit policies and collateral requirements for high-risk exposures.")

                # Additional general mitigations
                mitigations.append("Maintain adequate liquidity buffers to withstand stress scenarios.")
                mitigations.append("Develop contingency funding plans for severe stress events.")

                scenario_results["potential_mitigations"] = mitigations

            return scenario_results

        except Exception as e:
            scenario_results["error"] = f"Error running stress scenario: {str(e)}"
            return scenario_results

    def perform_valuation(
        self,
        financial_data: Optional[List[Dict[str, Any]]] = None,
        valuation_method: Optional[str] = None,
        assumptions: Optional[Dict[str, Any]] = None,
        discount_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform valuation analysis using specified method and financial data.

        Args:
            financial_data: List of dictionaries with financial data for valuation.
            valuation_method: Valuation methodology ("dcf", "multiples", "asset", "option").
            assumptions: Optional dictionary with valuation assumptions.
            discount_rate: Optional discount rate for DCF valuation.

        Returns:
            Dictionary with valuation results, sensitivity analysis, and recommendations.
        """
        # Set default values inside the function
        if financial_data is None:
            financial_data = []

        if valuation_method is None:
            valuation_method = "dcf"

        if assumptions is None:
            assumptions = {}

        if discount_rate is None:
            discount_rate = 0.10  # Default 10%

        logger.info(f"Performing {valuation_method} valuation")

        try:
            # Convert to pandas DataFrame
            df = pd.DataFrame(financial_data)

            # Set default assumptions if not provided
            if not assumptions:
                assumptions = {}

            # Initialize results
            valuation_results = {
                "valuation_parameters": {
                    "method": valuation_method,
                    "discount_rate": discount_rate,
                    "assumptions": assumptions
                },
                "valuation_summary": {},
                "detailed_valuation": {},
                "sensitivity_analysis": {},
                "recommendations": []
            }

            # Perform valuation based on method
            if valuation_method.lower() == "dcf":
                valuation_data = self._perform_dcf_valuation(df, discount_rate, assumptions)
            elif valuation_method.lower() == "multiples":
                valuation_data = self._perform_multiples_valuation(df, assumptions)
            elif valuation_method.lower() == "asset":
                valuation_data = self._perform_asset_valuation(df, assumptions)
            elif valuation_method.lower() == "option":
                valuation_data = self._perform_option_valuation(df, assumptions)
            else:
                return {
                    "error": f"Unsupported valuation method: {valuation_method}",
                    "supported_methods": ["dcf", "multiples", "asset", "option"]
                }

            # Add valuation data to results
            valuation_results.update(valuation_data)

            # Generate recommendations based on valuation
            recommendations = []

            # Valuation-specific recommendations
            if valuation_method.lower() == "dcf":
                # DCF recommendations
                if "enterprise_value" in valuation_results["valuation_summary"]:
                    ev = valuation_results["valuation_summary"]["enterprise_value"]

                    if "equity_value" in valuation_results["valuation_summary"]:
                        equity = valuation_results["valuation_summary"]["equity_value"]

                        # Debt to EV ratio if we calculated equity value
                        debt_to_ev = (ev - equity) / ev if ev != 0 else 0

                        if debt_to_ev > 0.5:
                            recommendations.append("High debt levels relative to enterprise value. Consider debt reduction strategies to increase equity value.")

                    # Growth recommendations
                    if "terminal_value_pct" in valuation_results["detailed_valuation"]:
                        tv_pct = valuation_results["detailed_valuation"]["terminal_value_pct"]

                        if tv_pct > 70:
                            recommendations.append(f"Terminal value constitutes {tv_pct:.1f}% of total enterprise value, indicating high dependency on long-term growth assumptions. Consider strategies to drive near-term cash flow growth.")

                # Sensitivity recommendations
                if "sensitivity_analysis" in valuation_results and "discount_rate" in valuation_results["sensitivity_analysis"]:
                    discount_sensitivity = valuation_results["sensitivity_analysis"]["discount_rate"]

                    if max(discount_sensitivity.values()) - min(discount_sensitivity.values()) > ev * 0.3:
                        recommendations.append("Valuation shows high sensitivity to discount rate changes. Consider risk mitigation strategies to reduce cost of capital.")

            elif valuation_method.lower() == "multiples":
                # Multiples recommendations
                if "valuation_range" in valuation_results["valuation_summary"]:
                    val_range = valuation_results["valuation_summary"]["valuation_range"]

                    range_width = (val_range["high"] - val_range["low"]) / val_range["median"] * 100 if val_range["median"] != 0 else 0

                    if range_width > 50:
                        recommendations.append(f"Wide valuation range ({range_width:.1f}% spread) suggests high uncertainty. Consider focusing on operational improvements to key value drivers.")

                if "multiple_comparison" in valuation_results["detailed_valuation"]:
                    multiple_comp = valuation_results["detailed_valuation"]["multiple_comparison"]

                    below_peers = [m for m, v in multiple_comp.items() if v.get("vs_peer_group", 0) < -15]

                    if below_peers:
                        multiples_list = ", ".join(below_peers)
                        recommendations.append(f"Trading at discount to peers on {multiples_list}. Focus on initiatives to improve these metrics.")

            # General valuation recommendations
            recommendations.append("Regularly update valuation model as new financial data becomes available and market conditions change.")

            if "key_value_drivers" in valuation_results["detailed_valuation"]:
                value_drivers = valuation_results["detailed_valuation"]["key_value_drivers"]

                if value_drivers:
                    drivers_list = ", ".join(value_drivers[:3])
                    recommendations.append(f"Focus strategic initiatives on improving key value drivers: {drivers_list}.")

            # Add recommendations to results
            valuation_results["recommendations"] = recommendations

            return valuation_results

        except Exception as e:
            logger.error(f"Error performing valuation: {str(e)}")
            return {
                "error": f"Error performing valuation: {str(e)}",
                "valuation_method": valuation_method
            }

    def _perform_dcf_valuation(self, df: pd.DataFrame, discount_rate: float, assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for DCF valuation implementation."""
        # This would be implemented in a real application
        return {
            "valuation_summary": {
                "enterprise_value": 1000000,
                "equity_value": 800000
            },
            "detailed_valuation": {
                "terminal_value_pct": 75,
                "key_value_drivers": ["Revenue Growth", "EBITDA Margin", "Working Capital"]
            },
            "sensitivity_analysis": {
                "discount_rate": {
                    "8%": 1200000,
                    "10%": 1000000,
                    "12%": 850000
                }
            }
        }

    def _perform_multiples_valuation(self, df: pd.DataFrame, assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for multiples-based valuation implementation."""
        # This would be implemented in a real application
        return {
            "valuation_summary": {
                "valuation_range": {
                    "low": 900000,
                    "median": 1100000,
                    "high": 1300000
                }
            },
            "detailed_valuation": {
                "multiple_comparison": {
                    "EV/EBITDA": {"company": 6.5, "peer_group": 7.2, "vs_peer_group": -9.7},
                    "P/E": {"company": 12.3, "peer_group": 15.1, "vs_peer_group": -18.5}
                },
                "key_value_drivers": ["EBITDA", "Net Income", "Growth Rate"]
            }
        }

    def _perform_asset_valuation(self, df: pd.DataFrame, assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for asset-based valuation implementation."""
        # This would be implemented in a real application
        return {
            "valuation_summary": {
                "adjusted_book_value": 950000
            },
            "detailed_valuation": {
                "asset_adjustments": {
                    "real_estate": 200000,
                    "inventory": -50000,
                    "intangibles": 100000
                },
                "key_value_drivers": ["Asset Quality", "Hidden Value", "Liquidation Value"]
            }
        }

    def _perform_option_valuation(self, df: pd.DataFrame, assumptions: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for real options valuation implementation."""
        # This would be implemented in a real application
        return {
            "valuation_summary": {
                "option_value": 250000
            },
            "detailed_valuation": {
                "option_parameters": {
                    "volatility": 0.35,
                    "time_to_expiry": 3,
                    "strike_price": 800000
                },
                "key_value_drivers": ["Volatility", "Time Horizon", "Growth Potential"]
            }
        }
