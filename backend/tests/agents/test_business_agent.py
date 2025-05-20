import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import inspect

from app.services.agents.business_agent import (
    BusinessAgent
)


class TestBusinessAgent:
    """Tests for the BusinessAgent class and related functions."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Patch Agent SDK
        self.agent_patch = patch('app.services.agents.business_agent.Agent')
        self.mock_agent = self.agent_patch.start()
        
        # Patch function_tool
        self.function_tool_patch = patch('app.services.agents.business_agent.function_tool')
        self.mock_function_tool = self.function_tool_patch.start()
        self.mock_function_tool.side_effect = lambda x: x  # Pass through the function
        
        # Patch ModelSettings
        self.model_settings_patch = patch('app.services.agents.business_agent.ModelSettings')
        self.mock_model_settings = self.model_settings_patch.start()
        
        # Patch calculator tools
        self.calculator_tool_patch = patch('app.services.agents.business_agent.get_calculator_tool')
        self.mock_calculator_tool = self.calculator_tool_patch.start()
        self.mock_calculator_tool.return_value = "calculator_tool"
        
        self.interpreter_tool_patch = patch('app.services.agents.business_agent.get_interpreter_tool')
        self.mock_interpreter_tool = self.interpreter_tool_patch.start()
        self.mock_interpreter_tool.return_value = "interpreter_tool"
        
        # Mock context for tool tests
        self.mock_context = MagicMock()
        
    def teardown_method(self):
        """Clean up after each test."""
        self.agent_patch.stop()
        self.function_tool_patch.stop()
        self.model_settings_patch.stop()
        self.calculator_tool_patch.stop()
        self.interpreter_tool_patch.stop()

    def test_initialization(self):
        """Test BusinessAgent initialization."""
        # Create a new agent
        agent = BusinessAgent()
        
        # In the mocked version, we can't directly verify the Agent constructor was called
        # Instead, verify function_tool was called for each tool
        assert self.mock_function_tool.call_count == 8  # 8 tools (6 business tools + 2 calculator tools)
        
        # Verify calculator tools were added
        self.mock_calculator_tool.assert_called_once()
        self.mock_interpreter_tool.assert_called_once()
        
        # Verify the tools list exists
        assert hasattr(agent, 'tools')
        
        # Verify the agent has the correct properties
        assert agent.description == "Expert in business strategy, operations, and organizational management, providing insights on business development and optimization"

    def test_analyze_business_model(self):
        """Test analyze_business_model method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        industry = "Software"
        revenue_streams = ["Subscription", "Professional Services"]
        cost_structure = ["Engineering", "Marketing", "Operations"]
        key_resources = ["Development Team", "Cloud Infrastructure"]
        customer_segments = ["Enterprise", "SMB"]
        competitive_advantage = "Proprietary Technology"
        
        # Call the method
        result = agent.analyze_business_model(
            self.mock_context,
            industry, 
            revenue_streams, 
            cost_structure, 
            key_resources, 
            customer_segments, 
            competitive_advantage
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "business_model_overview" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "opportunities" in result
        assert "recommendations" in result
        assert "detailed_analysis" in result
        
        # Verify the input data was properly included
        assert result["business_model_overview"]["industry"] == industry
        assert result["business_model_overview"]["primary_revenue_streams"] == revenue_streams
        assert result["business_model_overview"]["major_cost_drivers"] == cost_structure
        assert result["business_model_overview"]["key_resources"] == key_resources
        assert result["business_model_overview"]["customer_segments"] == customer_segments
        assert result["business_model_overview"]["competitive_advantage"] == competitive_advantage

    def test_develop_strategy(self):
        """Test develop_strategy method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        business_goal = "Increase market share by 10%"
        timeframe = "12 months"
        current_position = "Currently at 15% market share"
        available_resources = ["Marketing Budget", "Sales Team"]
        market_constraints = ["Competitors lowering prices", "Economic downturn"]
        
        # Call the method
        result = agent.develop_strategy(
            self.mock_context,
            business_goal, 
            timeframe, 
            current_position, 
            available_resources, 
            market_constraints
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "strategy_overview" in result
        assert "strategic_objectives" in result
        assert "key_strategies" in result
        assert "implementation_phases" in result
        assert "resource_allocation" in result
        assert "risk_mitigation" in result
        assert "detailed_plan" in result
        
        # Verify the input data was properly included
        assert result["strategy_overview"]["primary_goal"] == business_goal
        assert result["strategy_overview"]["timeframe"] == timeframe
        assert result["strategy_overview"]["current_position"] == current_position
        assert result["strategy_overview"]["available_resources"] == available_resources
        assert result["strategy_overview"]["market_constraints"] == market_constraints

    def test_perform_competitive_analysis(self):
        """Test perform_competitive_analysis method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        industry = "Cloud Computing"
        company_name = "TechCorp"
        competitors = ["CompetitorA", "CompetitorB", "CompetitorC"]
        market_segments = ["Enterprise", "Government", "Education"]
        evaluation_criteria = ["Product Features", "Pricing", "Support"]
        
        # Call the method
        result = agent.perform_competitive_analysis(
            self.mock_context,
            industry, 
            company_name, 
            competitors, 
            market_segments, 
            evaluation_criteria
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "analysis_overview" in result
        assert "industry_overview" in result
        assert "competitor_profiles" in result
        assert "competitive_position" in result
        assert "segment_analysis" in result
        assert "strategic_recommendations" in result
        assert "detailed_analysis" in result
        
        # Verify the input data was properly included
        assert result["analysis_overview"]["industry"] == industry
        assert result["analysis_overview"]["company"] == company_name
        assert result["analysis_overview"]["competitors"] == competitors
        assert result["analysis_overview"]["market_segments"] == market_segments
        assert result["analysis_overview"]["evaluation_criteria"] == evaluation_criteria
        
        # Verify competitor profiles were created for each competitor
        assert len(result["competitor_profiles"]) == len(competitors)
        
        # Verify segment analysis was created for each segment
        assert len(result["segment_analysis"]) == len(market_segments)

    def test_create_implementation_plan(self):
        """Test create_implementation_plan method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        strategic_initiative = "Digital Transformation"
        timeline = "18 months"
        objectives = ["Modernize Legacy Systems", "Train Staff", "Implement New Workflows"]
        key_stakeholders = ["IT Department", "Executive Team", "End Users"]
        resources_required = {
            "budget": "$1.5M",
            "personnel": ["IT Staff", "Project Managers"],
            "technology": ["Cloud Services", "Development Tools"]
        }
        risk_factors = ["Technical Debt", "Change Resistance", "Budget Overruns"]
        
        # Call the method
        result = agent.create_implementation_plan(
            self.mock_context,
            strategic_initiative, 
            timeline, 
            objectives, 
            key_stakeholders, 
            resources_required, 
            risk_factors
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "plan_overview" in result
        assert "implementation_phases" in result
        assert "stakeholder_management" in result
        assert "risk_management" in result
        assert "success_criteria" in result
        assert "detailed_plan" in result
        
        # Verify the input data was properly included
        assert result["plan_overview"]["initiative"] == strategic_initiative
        assert result["plan_overview"]["timeline"] == timeline
        assert result["plan_overview"]["key_objectives"] == objectives
        assert result["plan_overview"]["stakeholders"] == key_stakeholders
        assert result["plan_overview"]["resources_required"] == resources_required
        assert result["plan_overview"]["risk_factors"] == risk_factors
        
        # Verify stakeholder management was created for each stakeholder
        assert len(result["stakeholder_management"]) == len(key_stakeholders)
        
        # Verify risk management was created for each risk factor
        assert len(result["risk_management"]) == len(risk_factors)
        
    def test_create_implementation_plan_with_defaults(self):
        """Test create_implementation_plan method with default values for resources and risks."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        strategic_initiative = "Digital Transformation"
        timeline = "18 months"
        objectives = ["Modernize Legacy Systems", "Train Staff"]
        key_stakeholders = ["IT Department", "End Users"]
        
        # Call the method with None for optional parameters to trigger defaults
        result = agent.create_implementation_plan(
            self.mock_context,
            strategic_initiative, 
            timeline, 
            objectives, 
            key_stakeholders, 
            None,  # resources_required - should use default
            None   # risk_factors - should use default
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "plan_overview" in result
        assert "resources_required" in result["plan_overview"]
        assert "risk_factors" in result["plan_overview"]
        
        # Verify default resources and risks were created
        assert "personnel" in result["plan_overview"]["resources_required"]
        assert "budget" in result["plan_overview"]["resources_required"]
        assert len(result["plan_overview"]["risk_factors"]) > 0
        
        # Verify risk management was created for default risks
        assert len(result["risk_management"]) == len(result["plan_overview"]["risk_factors"])

    def test_analyze_financial_metrics(self):
        """Test analyze_financial_metrics method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        revenue = 1000000.0
        costs = 750000.0
        time_period = "Q2 2023"
        growth_rate = 0.15
        industry_benchmark = {"profit_margin": 20.0, "revenue": 900000.0}
        additional_metrics = {"customer_acquisition_cost": 500.0, "lifetime_value": 5000.0}
        
        # Call the method
        result = agent.analyze_financial_metrics(
            self.mock_context,
            revenue, 
            costs, 
            time_period, 
            growth_rate, 
            industry_benchmark, 
            additional_metrics
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "financial_overview" in result
        assert "key_metrics" in result
        assert "industry_comparison" in result
        assert "financial_insights" in result
        assert "recommendations" in result
        assert "detailed_analysis" in result
        
        # Verify the input data was properly included
        assert result["financial_overview"]["time_period"] == time_period
        assert result["financial_overview"]["total_revenue"] == revenue
        assert result["financial_overview"]["total_costs"] == costs
        assert result["financial_overview"]["profit"] == revenue - costs
        assert result["financial_overview"]["growth_rate"] == growth_rate
        
        # Verify calculations
        expected_profit_margin = ((revenue - costs) / revenue) * 100
        assert abs(result["financial_overview"]["profit_margin"] - expected_profit_margin) < 0.01
        
        # Verify industry comparison was created
        assert isinstance(result["industry_comparison"], list)
        assert len(result["industry_comparison"]) > 0
        
        # Verify additional metrics were included
        for metric, value in additional_metrics.items():
            for comparison in result["industry_comparison"]:
                if comparison.get("metric") == metric:
                    assert comparison.get("actual") == value
    
    def test_analyze_financial_metrics_with_nonexistent_metrics(self):
        """Test analyze_financial_metrics method with benchmark metrics that don't exist in data."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        revenue = 1000000.0
        costs = 750000.0
        time_period = "Q2 2023"
        growth_rate = None  # Testing default handling
        industry_benchmark = {
            "profit_margin": 20.0,  # Exists in default calculations
            "nonexistent_metric": 50.0  # Doesn't exist in provided data
        }
        additional_metrics = None  # Testing default handling
        
        # Call the method
        result = agent.analyze_financial_metrics(
            self.mock_context,
            revenue, 
            costs, 
            time_period, 
            growth_rate, 
            industry_benchmark, 
            additional_metrics
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "financial_overview" in result
        
        # Verify default growth rate handling
        assert result["financial_overview"]["growth_rate"] == "Not provided"
        
        # Verify industry comparison was created
        assert isinstance(result["industry_comparison"], list)
        
        # Only profit_margin should be compared since others don't exist in the data
        # and there are no additional_metrics
        comparison_metrics = [comp.get("metric") for comp in result["industry_comparison"]]
        assert "profit_margin" in comparison_metrics
        assert "nonexistent_metric" not in comparison_metrics

    def test_analyze_financial_metrics_edge_cases(self):
        """Test analyze_financial_metrics method with edge cases to improve coverage."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        revenue = 1000000.0
        costs = 750000.0
        time_period = "Q2 2023"
        
        # Special test case to hit remaining branches:
        # - Additional metrics with one metric that exists in benchmark
        # - Zero value in benchmark to test division by zero handling
        industry_benchmark = {
            "special_metric": 0.0  # Zero value to test division by zero handling
        }
        additional_metrics = {
            "special_metric": 100.0  # This matches a key in industry_benchmark
        }
        
        # Call the method
        result = agent.analyze_financial_metrics(
            self.mock_context,
            revenue, 
            costs, 
            time_period, 
            None,  # growth_rate
            industry_benchmark, 
            additional_metrics
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        
        # Verify industry comparison handling for zero denominator case
        found_special_metric = False
        for comparison in result["industry_comparison"]:
            if comparison.get("metric") == "special_metric":
                found_special_metric = True
                # When benchmark value is 0, percent_diff should be handled correctly
                # (either a special value or calculated without error)
                assert "percent_difference" in comparison
                
        assert found_special_metric, "The special_metric should be included in the comparison"

    def test_calculate_business_performance_metrics(self):
        """Test calculate_business_performance_metrics method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        revenue = 1000000.0
        costs = 750000.0
        time_period = "Q2 2023"
        previous_revenue = 900000.0
        previous_costs = 700000.0
        units_sold = 5000
        marketing_spend = 100000.0
        
        # Call the method
        result = agent.calculate_business_performance_metrics(
            self.mock_context,
            revenue,
            costs,
            time_period,
            previous_revenue,
            previous_costs,
            units_sold,
            marketing_spend
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "time_period" in result
        assert "core_metrics" in result
        assert "growth_metrics" in result
        assert "unit_economics" in result
        assert "marketing_metrics" in result
        assert "interpretations" in result
        assert "recommendations" in result
        
        # Verify core metrics calculations
        assert result["core_metrics"]["revenue"] == revenue
        assert result["core_metrics"]["costs"] == costs
        assert result["core_metrics"]["gross_profit"] == revenue - costs
        assert abs(result["core_metrics"]["profit_margin_percentage"] - 25.0) < 0.01 # (1000000-750000)/1000000 * 100
        
        # Verify growth metrics calculations
        assert abs(result["growth_metrics"]["revenue_growth_percentage"] - 11.11) < 0.1  # (1000000-900000)/900000 * 100
        assert abs(result["growth_metrics"]["cost_growth_percentage"] - 7.14) < 0.1  # (750000-700000)/700000 * 100
        assert "profit_growth_percentage" in result["growth_metrics"]
        
        # Verify unit economics calculations
        assert result["unit_economics"]["units_sold"] == units_sold
        assert result["unit_economics"]["revenue_per_unit"] == revenue / units_sold
        assert result["unit_economics"]["cost_per_unit"] == costs / units_sold
        assert result["unit_economics"]["profit_per_unit"] == (revenue - costs) / units_sold
        
        # Verify marketing metrics calculations
        assert result["marketing_metrics"]["marketing_spend"] == marketing_spend
        assert "marketing_roi_percentage" in result["marketing_metrics"]
        assert abs(result["marketing_metrics"]["marketing_percentage_of_revenue"] - 10.0) < 0.01  # 100000/1000000 * 100
        assert result["marketing_metrics"]["customer_acquisition_cost"] == marketing_spend / units_sold

    def test_calculate_market_sizing(self):
        """Test calculate_market_sizing method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data for TAM-SAM-SOM approach
        target_market = "Enterprise Software"
        market_approach = "TAM-SAM-SOM"
        total_market_size = 1000000000.0  # $1B
        market_growth_rate = 8.0
        addressable_percentage = 30.0
        serviceable_percentage = 40.0
        obtainable_percentage = 10.0
        
        # Call the method
        result = agent.calculate_market_sizing(
            self.mock_context,
            target_market,
            market_approach,
            total_market_size,
            market_growth_rate,
            addressable_percentage,
            serviceable_percentage,
            obtainable_percentage
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "target_market" in result
        assert "sizing_approach" in result
        assert "total_addressable_market" in result
        assert "serviceable_addressable_market" in result
        assert "serviceable_obtainable_market" in result
        assert "methodology" in result
        assert "five_year_projections" in result
        assert "interpretation" in result
        assert "strategic_implications" in result
        
        # Verify calculations
        tam = total_market_size
        sam = tam * (addressable_percentage / 100)
        som = sam * (serviceable_percentage / 100) * (obtainable_percentage / 100)
        
        assert result["total_addressable_market"]["value"] == tam
        assert result["serviceable_addressable_market"]["value"] == sam
        assert result["serviceable_obtainable_market"]["value"] == som
        
        # Test Bottom-Up approach
        market_approach = "Bottom-Up"
        unit_price = 100.0
        population_size = 1000000
        penetration_rate = 5.0
        
        # Call the method
        result = agent.calculate_market_sizing(
            self.mock_context,
            target_market,
            market_approach,
            None,  # total_market_size not needed for Bottom-Up
            market_growth_rate,
            None,  # addressable_percentage not needed for Bottom-Up
            None,  # serviceable_percentage not needed for Bottom-Up
            None,  # obtainable_percentage not needed for Bottom-Up
            unit_price,
            population_size,
            penetration_rate
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "target_market" in result
        assert "sizing_approach" in result
        assert "market_parameters" in result
        assert "total_potential_market" in result
        assert "obtainable_market" in result
        assert "methodology" in result
        assert "five_year_projections" in result
        
        # Verify calculations
        total_potential = population_size * unit_price
        obtainable = total_potential * (penetration_rate / 100)
        
        assert result["total_potential_market"]["value"] == total_potential
        assert result["obtainable_market"]["value"] == obtainable

    def test_calculate_pricing_optimization(self):
        """Test calculate_pricing_optimization method."""
        # Create a new agent
        agent = BusinessAgent()
        
        # Test data
        product_name = "Enterprise Software License"
        current_price = 1000.0
        current_volume = 500
        variable_cost = 200.0
        fixed_costs = 100000.0
        price_elasticity = -1.5  # 1% price increase reduces demand by 1.5%
        competitor_prices = [800.0, 1200.0, 1500.0]
        pricing_strategy = "profit"
        
        # Call the method
        result = agent.calculate_pricing_optimization(
            self.mock_context,
            product_name,
            current_price,
            current_volume,
            variable_cost,
            fixed_costs,
            price_elasticity,
            competitor_prices,
            pricing_strategy
        )
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "product_name" in result
        assert "current_pricing" in result
        assert "competitive_analysis" in result
        assert "price_elasticity" in result
        assert "price_scenarios" in result
        assert "pricing_recommendations" in result
        assert "analysis_and_recommendations" in result
        
        # Verify current pricing data
        assert result["current_pricing"]["price"] == current_price
        assert result["current_pricing"]["volume"] == current_volume
        assert result["current_pricing"]["revenue"] == current_price * current_volume
        
        # Verify cost structure data
        assert result["current_pricing"]["cost_structure"]["variable_cost_per_unit"] == variable_cost
        assert result["current_pricing"]["cost_structure"]["contribution_margin_per_unit"] == current_price - variable_cost
        assert result["current_pricing"]["cost_structure"]["fixed_costs"] == fixed_costs
        
        # Verify competitive analysis
        assert result["competitive_analysis"]["average_competitor_price"] == sum(competitor_prices) / len(competitor_prices)
        assert result["competitive_analysis"]["minimum_competitor_price"] == min(competitor_prices)
        assert result["competitive_analysis"]["maximum_competitor_price"] == max(competitor_prices)
        
        # Verify price scenarios
        assert len(result["price_scenarios"]) > 0
        for scenario in result["price_scenarios"]:
            assert "price_change_percentage" in scenario
            assert "new_price" in scenario
            assert "new_volume" in scenario
            assert "new_revenue" in scenario
            
        # Verify pricing recommendations
        assert "optimized_price" in result["pricing_recommendations"]
        assert "optimization_basis" in result["pricing_recommendations"]
        assert result["pricing_recommendations"]["pricing_strategy"] == pricing_strategy

    # Helper method tests
    def test_interpret_profit_margin(self):
        """Test _interpret_profit_margin helper method."""
        agent = BusinessAgent()
        
        # Test different profit margin ranges
        negative_interpretation = agent._interpret_profit_margin(-5.0)
        assert "loss" in negative_interpretation.lower()
        
        low_interpretation = agent._interpret_profit_margin(5.0)
        assert "low" in low_interpretation.lower()
        
        moderate_interpretation = agent._interpret_profit_margin(15.0)
        assert "moderate" in moderate_interpretation.lower()
        
        high_interpretation = agent._interpret_profit_margin(25.0)
        assert "healthy" in high_interpretation.lower()

    def test_generate_business_assessment(self):
        """Test _generate_business_assessment helper method."""
        agent = BusinessAgent()
        
        # Test with different combinations of metrics
        assessment1 = agent._generate_business_assessment(profit_margin=25.0, revenue_growth=15.0, profit_growth=20.0)
        assert "strong" in assessment1.lower()
        
        assessment2 = agent._generate_business_assessment(profit_margin=-5.0, revenue_growth=-3.0)
        assert "unprofitable" in assessment2.lower()
        assert "declining" in assessment2.lower()
        
        assessment3 = agent._generate_business_assessment(profit_margin=15.0, revenue_growth=3.0, profit_growth=2.0)
        assert "moderate" in assessment3.lower()
        assert "stagnant" in assessment3.lower()
        assert "lagging behind" in assessment3.lower()
        
        assessment4 = agent._generate_business_assessment()
        assert "insufficient data" in assessment4.lower()

    def test_generate_business_recommendations(self):
        """Test _generate_business_recommendations helper method."""
        agent = BusinessAgent()
        
        # Test with negative profit margin
        metrics_data = {
            "core_metrics": {"profit_margin_percentage": -5.0}
        }
        recommendations1 = agent._generate_business_recommendations(metrics_data)
        assert len(recommendations1) > 0
        assert any("cost structure" in rec.lower() for rec in recommendations1)
        
        # Test with cost growth exceeding revenue growth
        metrics_data = {
            "core_metrics": {"profit_margin_percentage": 8.0},
            "growth_metrics": {
                "revenue_growth_percentage": 5.0,
                "cost_growth_percentage": 10.0
            }
        }
        recommendations2 = agent._generate_business_recommendations(metrics_data)
        assert len(recommendations2) > 0
        assert any("cost controls" in rec.lower() for rec in recommendations2)
        
        # Test with no specific issues
        metrics_data = {
            "core_metrics": {"profit_margin_percentage": 20.0},
            "growth_metrics": {
                "revenue_growth_percentage": 15.0,
                "cost_growth_percentage": 10.0
            }
        }
        recommendations3 = agent._generate_business_recommendations(metrics_data)
        assert len(recommendations3) > 0