import pytest
import asyncio
from unittest.mock import MagicMock
from typing import Dict, Any, List
from app.services.agents.agent_calculator_tool import (
    AgentCalculatorTool,
    get_calculator_tool,
    get_interpreter_tool
)

# We won't mock CalculatorUtility - we want to test real functionality
# (We'll inject mocks only where they don't interfere with the actual calculations)

# Helper function to run async functions in tests
def async_run(coro):
    """Run an async coroutine in a test function."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


class TestAgentCalculatorTool:
    """Test suite for the AgentCalculatorTool class."""

    def test_calculate_without_operation_type(self):
        """Test calculate method without providing operation_type."""
        result = async_run(AgentCalculatorTool.calculate())
        assert "error" in result
        assert result["error"] == "Operation type is required"

    def test_calculate_without_operation(self):
        """Test calculate method without providing operation."""
        result = async_run(AgentCalculatorTool.calculate(operation_type="arithmetic"))
        assert "error" in result
        assert result["error"] == "Operation is required"

    def test_calculate_arithmetic_add(self):
        """Test calculate method with arithmetic add operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="add",
            values=[2, 3, 5]
        ))
        
        assert "result" in result
        assert result["result"] == 10
        assert "calculation_steps" in result
        assert result["calculation_steps"][0] == "2 + 3 + 5 = 10"

    def test_calculate_arithmetic_add_without_values(self):
        """Test calculate method with arithmetic add operation without providing values."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="add"
        ))
        
        assert "error" in result
        assert result["error"] == "add requires numeric values"

    def test_calculate_arithmetic_subtract(self):
        """Test calculate method with arithmetic subtract operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="subtract",
            values=[10, 3, 2]
        ))
        
        assert "result" in result
        assert result["result"] == 5
        assert "calculation_steps" in result

    def test_calculate_arithmetic_multiply(self):
        """Test calculate method with arithmetic multiply operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="multiply",
            values=[2, 3, 4]
        ))
        
        assert "result" in result
        assert result["result"] == 24
        assert "calculation_steps" in result

    def test_calculate_arithmetic_divide(self):
        """Test calculate method with arithmetic divide operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="divide",
            values=[20, 5, 2]
        ))
        
        assert "result" in result
        assert result["result"] == 2
        assert "calculation_steps" in result

    def test_calculate_arithmetic_divide_by_zero(self):
        """Test calculate method with arithmetic divide by zero."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="divide",
            values=[10, 0]
        ))
        
        assert "error" in result
        assert "Cannot divide by zero" in result["error"]

    def test_calculate_arithmetic_power(self):
        """Test calculate method with arithmetic power operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="power",
            base=2,
            exponent=3
        ))
        
        assert "result" in result
        assert result["result"] == 8
        assert "calculation_steps" in result

    def test_calculate_arithmetic_root(self):
        """Test calculate method with arithmetic root operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="root",
            value=9,
            n=2
        ))
        
        assert "result" in result
        assert result["result"] == 3
        assert "calculation_steps" in result

    def test_calculate_statistical_mean(self):
        """Test calculate method with statistical mean operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="statistical",
            operation="mean",
            values=[1, 2, 3, 4, 5]
        ))
        
        assert "mean" in result
        assert result["mean"] == 3.0

    def test_calculate_statistical_median(self):
        """Test calculate method with statistical median operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="statistical",
            operation="median",
            values=[1, 3, 5, 7, 9]
        ))
        
        assert "median" in result
        assert result["median"] == 5.0

    def test_calculate_statistical_mode(self):
        """Test calculate method with statistical mode operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="statistical",
            operation="mode",
            values=[1, 2, 2, 3, 4, 2, 5]
        ))
        
        assert "mode" in result
        assert result["mode"] == 2

    def test_calculate_statistical_summary(self):
        """Test calculate method with statistical summary operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="statistical",
            operation="summary",
            values=[1, 2, 3, 4, 5]
        ))
        
        assert "mean" in result
        assert "median" in result
        assert "standard_deviation" in result
        assert "variance" in result
        assert "range" in result
        assert "count" in result
        assert "sum" in result
        assert result["mean"] == 3.0
        assert result["median"] == 3.0
        assert result["count"] == 5
        assert result["sum"] == 15

    def test_calculate_statistical_no_values(self):
        """Test calculate method with statistical operation without values."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="statistical",
            operation="mean"
        ))
        
        assert "error" in result
        assert "Statistical operations require numeric values" in result["error"]

    def test_calculate_financial_compound_interest(self):
        """Test calculate method with financial compound interest operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="financial",
            operation="compound_interest",
            principal=1000,
            rate=5,
            time=1,
            periods=1
        ))
        
        assert "final_amount" in result
        assert "interest_earned" in result
        assert result["final_amount"] == 1050.0
        assert result["interest_earned"] == 50.0

    def test_calculate_financial_loan_payment(self):
        """Test calculate method with financial loan payment operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="financial",
            operation="loan_payment",
            principal=10000,
            rate=5,
            time=1
        ))
        
        assert "monthly_payment" in result
        assert "total_paid" in result
        assert "total_interest" in result
        assert "amortization_schedule" in result
        assert result["total_interest"] > 0

    def test_calculate_health_bmi(self):
        """Test calculate method with health bmi operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="health",
            operation="bmi",
            weight_kg=70,
            height_cm=175
        ))
        
        assert "bmi" in result
        assert "category" in result
        assert abs(result["bmi"] - 22.9) < 0.1  # Allow for small rounding differences

    def test_calculate_business_profit_margin(self):
        """Test calculate method with business profit margin operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="business",
            operation="profit_margin",
            revenue=100000,
            costs=60000,
            margin_type="net"
        ))
        
        assert "net_profit" in result
        assert "net_profit_margin" in result
        assert result["net_profit"] == 40000
        assert result["net_profit_margin"] == 40.0

    def test_calculate_business_break_even(self):
        """Test calculate method with business break even operation."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="business",
            operation="break_even",
            fixed_costs=50000,
            unit_price=100,
            unit_variable_cost=60
        ))
        
        assert "break_even_units" in result
        assert "break_even_revenue" in result
        assert result["break_even_units"] == 1250
        assert result["break_even_revenue"] == 125000

    def test_calculate_unsupported_operation_type(self):
        """Test calculate method with unsupported operation type."""
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="unsupported_type",
            operation="some_operation"
        ))
        
        assert "error" in result
        assert "Unsupported operation type" in result["error"]

    def test_calculate_with_exception(self):
        """Test calculate method with an exception being raised."""
        # Use an operation that will always raise an exception
        result = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic",
            operation="divide",
            values=[1, 0]  # This will cause a division by zero error
        ))
        
        assert "error" in result
        # The error should contain the specific error message
        assert "Cannot divide by zero" in result["error"]

    def test_interpret_calculation_results_with_no_results(self):
        """Test interpret_calculation_results with empty results."""
        result = async_run(AgentCalculatorTool.interpret_calculation_results())
        
        assert "interpretation" in result
        assert isinstance(result["interpretation"], dict)
        assert "summary" in result["interpretation"]
        assert "key_findings" in result["interpretation"]
        assert "recommendations" in result["interpretation"]

    def test_interpret_calculation_results_with_error(self):
        """Test interpret_calculation_results with an error in the calculation results."""
        calculation_results = {"error": "Some calculation error"}
        result = async_run(AgentCalculatorTool.interpret_calculation_results(calculation_results=calculation_results))
        
        assert "interpretation" in result
        assert "Error in calculation" in result["interpretation"]

    def test_interpret_calculation_results_with_result(self):
        """Test interpret_calculation_results with a simple result value."""
        calculation_results = {"result": 10}
        result = async_run(AgentCalculatorTool.interpret_calculation_results(calculation_results=calculation_results))
        
        assert "interpretation" in result
        assert "summary" in result["interpretation"]
        assert "The calculation resulted in 10" in result["interpretation"]["summary"]

    def test_interpret_calculation_results_with_financial_data(self):
        """Test interpret_calculation_results with financial calculation data."""
        # Generate actual financial calculation data
        calc_results = async_run(AgentCalculatorTool.calculate(
            operation_type="financial",
            operation="compound_interest",
            principal=1000,
            rate=5,
            time=1
        ))
        
        result = async_run(AgentCalculatorTool.interpret_calculation_results(calculation_results=calc_results))
        
        assert "interpretation" in result
        assert "summary" in result["interpretation"]
        assert "The investment grows to" in result["interpretation"]["summary"]
        assert "key_findings" in result["interpretation"]
        assert any("Total interest/growth:" in finding for finding in result["interpretation"]["key_findings"])

    def test_interpret_calculation_results_with_statistical_data(self):
        """Test interpret_calculation_results with statistical calculation data."""
        # Generate actual statistical calculation data
        calc_results = async_run(AgentCalculatorTool.calculate(
            operation_type="statistical",
            operation="mean",
            values=[1, 2, 3, 4, 5]
        ))
        
        result = async_run(AgentCalculatorTool.interpret_calculation_results(calculation_results=calc_results))
        
        assert "interpretation" in result
        assert "key_findings" in result["interpretation"]
        assert any("Average (mean) value:" in finding for finding in result["interpretation"]["key_findings"])

    def test_interpret_calculation_results_with_bmi_data(self):
        """Test interpret_calculation_results with BMI data."""
        # Generate actual BMI calculation data
        calc_results = async_run(AgentCalculatorTool.calculate(
            operation_type="health",
            operation="bmi",
            weight_kg=70,
            height_cm=175
        ))
        
        result = async_run(AgentCalculatorTool.interpret_calculation_results(calculation_results=calc_results))
        
        assert "interpretation" in result
        assert "summary" in result["interpretation"]
        assert "BMI is" in result["interpretation"]["summary"]

    def test_interpret_calculation_results_with_profit_margin_data(self):
        """Test interpret_calculation_results with profit margin data."""
        # Generate actual profit margin calculation data
        calc_results = async_run(AgentCalculatorTool.calculate(
            operation_type="business",
            operation="profit_margin",
            revenue=100000,
            costs=60000,
            margin_type="net"
        ))
        
        result = async_run(AgentCalculatorTool.interpret_calculation_results(calculation_results=calc_results))
        
        assert "interpretation" in result
        assert "summary" in result["interpretation"]
        assert "Profit margin is" in result["interpretation"]["summary"]
        assert "key_findings" in result["interpretation"]
        assert "recommendations" in result["interpretation"]

    def test_interpret_calculation_results_with_break_even_data(self):
        """Test interpret_calculation_results with break-even data."""
        # Generate actual break-even calculation data
        calc_results = async_run(AgentCalculatorTool.calculate(
            operation_type="business",
            operation="break_even",
            fixed_costs=50000,
            unit_price=100,
            unit_variable_cost=60
        ))
        
        result = async_run(AgentCalculatorTool.interpret_calculation_results(calculation_results=calc_results))
        
        assert "interpretation" in result
        assert "summary" in result["interpretation"]
        assert "Break-even point is" in result["interpretation"]["summary"]
        assert "key_findings" in result["interpretation"]
        assert any("sell at least" in finding for finding in result["interpretation"]["key_findings"])

    def test_interpret_calculation_results_with_basic_level(self):
        """Test interpret_calculation_results with basic interpretation level."""
        calculation_results = {"result": 10}
        result = async_run(AgentCalculatorTool.interpret_calculation_results(
            calculation_results=calculation_results,
            interpretation_level="basic"
        ))
        
        assert "interpretation" in result
        assert isinstance(result["interpretation"], str)
        assert "The calculation resulted in 10" in result["interpretation"]

    def test_interpret_calculation_results_with_detailed_level(self):
        """Test interpret_calculation_results with detailed interpretation level."""
        # Generate data with calculation steps
        calc_results = async_run(AgentCalculatorTool.calculate(
            operation_type="arithmetic", 
            operation="add",
            values=[5, 5]
        ))
        
        result = async_run(AgentCalculatorTool.interpret_calculation_results(
            calculation_results=calc_results,
            interpretation_level="detailed"
        ))
        
        assert "interpretation" in result
        assert isinstance(result["interpretation"], dict)
        assert "calculation_steps" in result["interpretation"]


class TestCalculatorToolFunctions:
    """Test suite for the calculator tool functions."""

    def test_get_calculator_tool(self):
        """Test get_calculator_tool function returns a properly configured tool."""
        tool = get_calculator_tool()
        
        # Check if the tool is not None
        assert tool is not None
        
        # Ensure the tool has needed attributes
        assert hasattr(tool, 'function') or hasattr(tool, 'name'), "Tool should have a function or name attribute"

    def test_get_interpreter_tool(self):
        """Test get_interpreter_tool function returns a properly configured tool."""
        tool = get_interpreter_tool()
        
        # Check if the tool is not None
        assert tool is not None
        
        # Ensure the tool has needed attributes  
        assert hasattr(tool, 'function') or hasattr(tool, 'name'), "Tool should have a function or name attribute"


if __name__ == "__main__":
    pytest.main(["-xvs", "test_agent_calculator_tool.py"])
