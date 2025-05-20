from typing import Dict, Any, Optional, List, Union
import logging
from decimal import Decimal
import numpy as np
import pandas as pd
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper
from app.core.config import settings
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool
from app.services.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class BusinessAgent(BaseAgent):
    """
    BusinessAgent is a specialized agent that provides business expertise and analysis.
    
    This agent specializes in business strategy, operations, management, organizational 
    development, and other business-related areas.
    """

    # Industry benchmarks by sector for common financial metrics
    INDUSTRY_BENCHMARKS = {
        "technology": {
            "profit_margin": 15.0,
            "revenue_growth": 12.0,
            "marketing_percentage": 12.0,
            "r_and_d_percentage": 15.0
        },
        "retail": {
            "profit_margin": 3.5,
            "revenue_growth": 4.0,
            "marketing_percentage": 4.0,
            "r_and_d_percentage": 1.0
        },
        "manufacturing": {
            "profit_margin": 7.0,
            "revenue_growth": 3.5,
            "marketing_percentage": 2.0,
            "r_and_d_percentage": 5.0
        },
        "healthcare": {
            "profit_margin": 9.0,
            "revenue_growth": 6.0,
            "marketing_percentage": 2.5,
            "r_and_d_percentage": 7.5
        },
        "financial_services": {
            "profit_margin": 18.0,
            "revenue_growth": 5.0,
            "marketing_percentage": 6.0,
            "r_and_d_percentage": 8.0
        },
        "default": {
            "profit_margin": 10.0,
            "revenue_growth": 5.0,
            "marketing_percentage": 5.0,
            "r_and_d_percentage": 5.0
        }
    }

    # Standard business model canvas components
    BUSINESS_MODEL_COMPONENTS = [
        "value_propositions", 
        "customer_segments",
        "channels", 
        "customer_relationships", 
        "revenue_streams",
        "key_resources", 
        "key_activities", 
        "key_partnerships", 
        "cost_structure"
    ]

    def __init__(
        self,
        name: str = "Business Expert",
        model: str = settings.DEFAULT_AGENT_MODEL,
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        **kwargs
    ):
        """
        Initialize a BusinessAgent with specialized business instructions.
        
        Args:
            name: The name of the agent. Defaults to "Business Expert".
            model: The model to use. Defaults to settings.DEFAULT_AGENT_MODEL.
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            **kwargs: Additional arguments to pass to the Agent constructor.
        """
        # Define the business expert instructions
        business_instructions = """"Wherever possible, you must use tools to respond. Do not guess. If a tool is avalable, always call the tool to perform the action. You are a business expert agent specializing in business strategy, operations, management, and organizational development. Your role is to:

1. PROVIDE BUSINESS EXPERTISE IN
- Strategic Planning and Analysis
- Operations Management
- Marketing and Sales
- Organizational Development
- Business Model Innovation
- Market Analysis and Research
- Performance Optimization
- Change Management
- Project Management
- Business Process Improvement

2. ANALYTICAL APPROACH
- Use data-driven reasoning
- Consider multiple stakeholder perspectives
- Evaluate risks and opportunities
- Assess market conditions and trends
- Consider resource implications
- Analyze competitive dynamics
- Evaluate implementation feasibility

3. PRACTICAL FOCUS
- Provide actionable insights
- Suggest concrete steps and solutions
- Consider resource constraints
- Focus on practical implementation
- Address potential challenges
- Recommend measurement metrics
- Consider timing and sequencing

4. CONTEXT AWARENESS
- Build on previous discussion points
- Consider organizational context
- Account for market conditions
- Acknowledge industry specifics
- Reference relevant past decisions
- Maintain strategic consistency

5. RESPONSE STRUCTURE
- Begin with key insights
- Provide structured analysis
- Include actionable recommendations
- Note important considerations
- Highlight potential risks
- Suggest next steps
- Include implementation guidance

6. CALCULATION CAPABILITIES
- Perform business metric calculations
- Calculate financial indicators
- Perform statistical analysis
- Generate quantifiable insights
- Provide data-driven recommendations

Always maintain professionalism and base recommendations on sound business principles and accurate calculations."""

        # Get the calculator tools - already properly patched from the utility functions
        calculator_tool = get_calculator_tool()
        interpreter_tool = get_interpreter_tool()
        
        # Define the tools - use the already patched instances
        tools = [
            calculator_tool,
            interpreter_tool,
            function_tool(self.analyze_business_model),
            function_tool(self.develop_strategy),
            function_tool(self.perform_competitive_analysis),
            function_tool(self.create_implementation_plan),
            function_tool(self.analyze_financial_metrics),
            function_tool(self.calculate_business_performance_metrics),
            function_tool(self.calculate_market_sizing),
            function_tool(self.calculate_pricing_optimization)
        ]
        
        # Initialize using BaseAgent
        super().__init__(
            name=name,
            model=model,
            instructions=business_instructions,
            functions=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            max_tokens=4096,
            **kwargs
        )

    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the BusinessAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any business agent specific context initialization here
        logger.info(f"Initialized context for BusinessAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Expert in business strategy, operations, and organizational management, providing insights on business development and optimization"

    def analyze_business_model(
        self, 
        industry: Optional[str] = None, 
        revenue_streams: Optional[List[str]] = None,
        cost_structure: Optional[List[str]] = None,
        key_resources: Optional[List[str]] = None,
        customer_segments: Optional[List[str]] = None,
        competitive_advantage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a business model to identify strengths, weaknesses, and opportunities for improvement.
        
        Args:
            industry: The industry or sector the business operates in.
            revenue_streams: List of ways the business generates revenue.
            cost_structure: List of major cost categories for the business.
            key_resources: Optional list of critical resources the business relies on.
            customer_segments: Optional list of primary customer segments.
            competitive_advantage: Optional description of the business's competitive advantage.
            
        Returns:
            A structured analysis of the business model with recommendations.
        """
        # Set default values for required parameters
        industry = industry or "Unspecified industry"
        revenue_streams = revenue_streams or []
        cost_structure = cost_structure or []
        
        logger.info(f"Analyzing business model for industry: {industry}")
        
        # Format inputs for display
        revenue_str = "\n".join([f"- {stream}" for stream in revenue_streams])
        cost_str = "\n".join([f"- {cost}" for cost in cost_structure])
        resources_str = "\n".join([f"- {resource}" for resource in (key_resources or [])]) if key_resources else "Not specified"
        segments_str = "\n".join([f"- {segment}" for segment in (customer_segments or [])]) if customer_segments else "Not specified"
        
        # Normalize industry for benchmark lookup
        normalized_industry = self._normalize_industry(industry)
        benchmarks = self.INDUSTRY_BENCHMARKS.get(normalized_industry, self.INDUSTRY_BENCHMARKS["default"])
        
        # Analyze business model components for completeness
        provided_components = []
        if revenue_streams:
            provided_components.append("revenue_streams")
        if cost_structure:
            provided_components.append("cost_structure")
        if key_resources:
            provided_components.append("key_resources")
        if customer_segments:
            provided_components.append("customer_segments")
        
        # Calculate completeness score
        completeness_score = len(provided_components) / len(self.BUSINESS_MODEL_COMPONENTS) * 100
        missing_components = [c for c in self.BUSINESS_MODEL_COMPONENTS if c not in provided_components]
        
        # Generate SWOT analysis
        strengths = self._analyze_business_model_strengths(
            industry, revenue_streams, cost_structure, key_resources, customer_segments, competitive_advantage
        )
        
        weaknesses = self._analyze_business_model_weaknesses(
            industry, revenue_streams, cost_structure, key_resources, customer_segments, competitive_advantage, 
            missing_components
        )
        
        opportunities = self._analyze_business_model_opportunities(
            industry, revenue_streams, cost_structure, key_resources, customer_segments, competitive_advantage
        )
        
        threats = self._analyze_business_model_threats(
            industry, revenue_streams, cost_structure, key_resources, customer_segments
        )
        
        # Generate recommendations based on SWOT
        recommendations = self._generate_business_model_recommendations(
            strengths, weaknesses, opportunities, threats, benchmarks, industry
        )
        
        # Create a structured analysis of the business model
        analysis = {
            "business_model_overview": {
                "industry": industry,
                "primary_revenue_streams": revenue_streams,
                "major_cost_drivers": cost_structure,
                "key_resources": key_resources or [],
                "customer_segments": customer_segments or [],
                "competitive_advantage": competitive_advantage or "Not specified"
            },
            "model_assessment": {
                "completeness_score": completeness_score,
                "missing_components": missing_components,
                "diversification_level": "High" if len(revenue_streams) > 2 else "Medium" if len(revenue_streams) == 2 else "Low"
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats,
            "recommendations": recommendations,
            "detailed_analysis": self._generate_detailed_business_model_analysis(
                industry, revenue_streams, cost_structure, key_resources, customer_segments, 
                competitive_advantage, benchmarks, strengths, weaknesses, opportunities, threats
            )
        }
        
        return analysis
    
    def develop_strategy(
        self, 
        business_goal: Optional[str] = None,
        timeframe: Optional[str] = None, 
        current_position: Optional[str] = None,
        available_resources: Optional[List[str]] = None,
        market_constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Develop a business strategy to achieve a specific goal within a given timeframe.
        
        Args:
            business_goal: The primary goal the strategy should achieve.
            timeframe: The time period for achieving the goal (e.g., "6 months", "2 years").
            current_position: Description of the current business position or situation.
            available_resources: Optional list of resources available for strategy implementation.
            market_constraints: Optional list of market constraints or challenges.
            
        Returns:
            A structured business strategy with implementation steps.
        """
        # Set default values for required parameters
        business_goal = business_goal or "Grow business"
        timeframe = timeframe or "12 months"
        current_position = current_position or "Current business position"
        available_resources = available_resources or []
        market_constraints = market_constraints or []
        
        logger.info(f"Developing strategy for goal: {business_goal} within {timeframe}")
        
        # Format inputs for display
        resources_str = "\n".join([f"- {resource}" for resource in available_resources]) if available_resources else "None specified"
        constraints_str = "\n".join([f"- {constraint}" for constraint in market_constraints]) if market_constraints else "None specified"
        
        # Parse timeframe to estimate number of months
        months = self._parse_timeframe_to_months(timeframe)
        
        # Categorize goal and determine strategic approach
        goal_type, goal_focus = self._categorize_business_goal(business_goal)
        
        # Identify appropriate strategic objectives based on goal type
        strategic_objectives = self._generate_strategic_objectives(goal_type, goal_focus, months)
        
        # Determine key strategies based on objectives, resources, and constraints
        key_strategies = self._generate_key_strategies(
            strategic_objectives, goal_type, available_resources, market_constraints
        )
        
        # Generate implementation phases based on timeframe
        implementation_phases = self._generate_implementation_phases(
            key_strategies, months, goal_type
        )
        
        # Identify resource allocation recommendations
        resource_allocation = self._generate_resource_allocation(
            available_resources, key_strategies, implementation_phases
        )
        
        # Identify risks and mitigation strategies
        risks_and_mitigation = self._identify_risks_and_mitigation(
            goal_type, market_constraints, key_strategies, months
        )
        
        # Create a structured strategy plan
        strategy = {
            "strategy_overview": {
                "primary_goal": business_goal,
                "goal_type": goal_type,
                "goal_focus": goal_focus,
                "timeframe": timeframe,
                "estimated_duration_months": months,
                "current_position": current_position,
                "available_resources": available_resources,
                "market_constraints": market_constraints
            },
            "strategic_objectives": strategic_objectives,
            "key_strategies": key_strategies,
            "implementation_phases": implementation_phases,
            "resource_allocation": resource_allocation,
            "risk_mitigation": risks_and_mitigation,
            "detailed_plan": self._generate_detailed_strategy_plan(
                business_goal, timeframe, current_position, resources_str, constraints_str,
                strategic_objectives, key_strategies, implementation_phases, resource_allocation,
                risks_and_mitigation
            )
        }
        
        return strategy
    
    def perform_competitive_analysis(
        self, 
        industry: Optional[str] = None,
        company_name: Optional[str] = None,
        competitors: Optional[List[str]] = None,
        market_segments: Optional[List[str]] = None,
        evaluation_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze the competitive landscape for a company within its industry.
        
        Args:
            industry: The industry or sector being analyzed.
            company_name: The name of the company being analyzed.
            competitors: List of key competitors to analyze.
            market_segments: List of market segments to consider in the analysis.
            evaluation_criteria: Optional list of criteria for evaluating competitive position.
            
        Returns:
            A structured competitive analysis with market position assessment.
        """
        # Set default values for required parameters
        industry = industry or "Unspecified industry"
        company_name = company_name or "Your Company"
        competitors = competitors or []
        market_segments = market_segments or []
        
        logger.info(f"Performing competitive analysis for {company_name} in {industry}")
        
        # Normalize industry for benchmark lookup
        normalized_industry = self._normalize_industry(industry)
        industry_benchmarks = self.INDUSTRY_BENCHMARKS.get(normalized_industry, self.INDUSTRY_BENCHMARKS["default"])
        
        # Define default evaluation criteria if none provided
        criteria = evaluation_criteria or [
            "Product/Service Quality", 
            "Pricing", 
            "Market Share", 
            "Customer Experience", 
            "Innovation"
        ]
        
        # Format inputs for display
        competitors_str = ", ".join(competitors)
        segments_str = ", ".join(market_segments)
        criteria_str = ", ".join(criteria)
        
        # Analysis of industry structure and dynamics
        industry_analysis = self._analyze_industry_structure(industry)
        
        # Generate competitor profiles
        competitor_profiles = self._generate_competitor_profiles(competitors, industry, criteria)
        
        # Assess company's competitive position
        competitive_position = self._assess_competitive_position(
            company_name, competitors, industry, criteria
        )
        
        # Analyze market segments
        segment_analysis = self._analyze_market_segments(
            market_segments, company_name, competitors, industry
        )
        
        # Generate strategic recommendations
        strategic_recommendations = self._generate_competitive_strategy_recommendations(
            company_name, competitors, industry, competitive_position, segment_analysis
        )
        
        # Create a structured competitive analysis
        analysis = {
            "analysis_overview": {
                "industry": industry,
                "company": company_name,
                "competitors": competitors,
                "market_segments": market_segments,
                "evaluation_criteria": criteria
            },
            "industry_overview": industry_analysis,
            "competitor_profiles": competitor_profiles,
            "competitive_position": competitive_position,
            "segment_analysis": segment_analysis,
            "strategic_recommendations": strategic_recommendations,
            "detailed_analysis": self._generate_detailed_competitive_analysis(
                company_name, industry, competitors_str, segments_str, criteria_str,
                industry_analysis, competitor_profiles, competitive_position,
                segment_analysis, strategic_recommendations
            )
        }
        
        return analysis
    
    def create_implementation_plan(
        self, 
        strategic_initiative: Optional[str] = None,
        timeline: Optional[str] = None,
        objectives: Optional[List[str]] = None,
        key_stakeholders: Optional[List[str]] = None,
        resources_required: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create an implementation plan for a strategic business initiative.
        
        Args:
            strategic_initiative: The name or description of the strategic initiative.
            timeline: The overall timeline for implementation.
            objectives: List of key objectives for the initiative.
            key_stakeholders: List of stakeholders involved in or affected by the initiative.
            resources_required: Optional dictionary of resources required (people, budget, etc).
            risk_factors: Optional list of risk factors to consider.
            
        Returns:
            A structured implementation plan with phases, tasks, and success criteria.
        """
        # Set default values for required parameters
        strategic_initiative = strategic_initiative or "Strategic Initiative"
        timeline = timeline or "12 months"
        objectives = objectives or []
        key_stakeholders = key_stakeholders or []
        
        logger.info(f"Creating implementation plan for: {strategic_initiative}")
        
        # Parse timeline to estimate number of months
        months = self._parse_timeframe_to_months(timeline)
        
        # Default resources if none provided
        if not resources_required:
            resources_required = {
                "personnel": ["Implementation team members"],
                "budget": "Estimated budget required",
                "time": f"{months} months",
                "technology": ["Required technology resources"]
            }
            
        # Default risks if none provided
        if not risk_factors:
            risk_factors = self._generate_default_risk_factors(strategic_initiative)
        
        # Format inputs for display
        objectives_str = "\n".join([f"- {objective}" for objective in objectives])
        stakeholders_str = "\n".join([f"- {stakeholder}" for stakeholder in key_stakeholders])
        risks_str = "\n".join([f"- {risk}" for risk in risk_factors])
        
        # Categorize initiative type
        initiative_type = self._categorize_initiative(strategic_initiative)
        
        # Generate implementation phases based on initiative type and timeline
        implementation_phases = self._generate_implementation_phases_for_initiative(
            initiative_type, months, objectives
        )
        
        # Generate stakeholder management strategies
        stakeholder_management = self._generate_stakeholder_management_strategies(
            key_stakeholders, initiative_type
        )
        
        # Generate risk management strategies
        risk_management = self._generate_risk_management_strategies(
            risk_factors, initiative_type, months
        )
        
        # Generate success criteria
        success_criteria = self._generate_success_criteria(
            objectives, initiative_type, months
        )
        
        # Create a structured implementation plan
        implementation_plan = {
            "plan_overview": {
                "initiative": strategic_initiative,
                "initiative_type": initiative_type,
                "timeline": timeline,
                "key_objectives": objectives,
                "stakeholders": key_stakeholders,
                "resources_required": resources_required,
                "risk_factors": risk_factors
            },
            "implementation_phases": implementation_phases,
            "stakeholder_management": stakeholder_management,
            "risk_management": risk_management,
            "success_criteria": success_criteria,
            "detailed_plan": self._generate_detailed_implementation_plan(
                strategic_initiative, timeline, objectives_str, stakeholders_str, 
                risks_str, implementation_phases, stakeholder_management, risk_management,
                success_criteria
            )
        }
        
        return implementation_plan
    
    def analyze_financial_metrics(
        self, 
        revenue: Optional[float] = None,
        costs: Optional[float] = None,
        time_period: Optional[str] = None,
        growth_rate: Optional[float] = None,
        industry_benchmark: Optional[Dict[str, float]] = None,
        additional_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Analyze key financial metrics and provide business insights.
        
        Args:
            revenue: Total revenue for the specified time period.
            costs: Total costs for the specified time period.
            time_period: The time period for the financial data (e.g., "Q2 2023", "FY 2022").
            growth_rate: Optional revenue growth rate compared to previous period.
            industry_benchmark: Optional dictionary of industry benchmark metrics for comparison.
            additional_metrics: Optional dictionary of additional financial metrics to analyze.
            
        Returns:
            A structured financial analysis with insights and recommendations.
        """
        # Validate input parameters
        if revenue is not None and revenue < 0:
            logger.warning("Received negative revenue value, adjusting to 0")
            revenue = 0
            
        if costs is not None and costs < 0:
            logger.warning("Received negative costs value, adjusting to 0")
            costs = 0
        
        # Set default values for required parameters
        revenue = revenue or 0.0
        costs = costs or 0.0
        time_period = time_period or "Current period"
        additional_metrics = additional_metrics or {}
        
        logger.info(f"Analyzing financial metrics for period: {time_period}")
        
        # Calculate basic financial metrics
        profit = revenue - costs
        profit_margin = (profit / revenue) * 100 if revenue > 0 else 0
        
        # Prepare benchmark data
        if not industry_benchmark:
            # Try to extract industry from time_period if it contains industry information
            industry_keywords = ["tech", "retail", "healthcare", "finance", "manufacturing"]
            detected_industry = None
            for keyword in industry_keywords:
                if keyword.lower() in time_period.lower():
                    detected_industry = keyword
                    break
            
            normalized_industry = self._normalize_industry(detected_industry or "default")
            industry_benchmark = {
                "profit_margin": self.INDUSTRY_BENCHMARKS[normalized_industry]["profit_margin"],
                "revenue_growth": self.INDUSTRY_BENCHMARKS[normalized_industry]["revenue_growth"]
            }
        
        # Format benchmark comparison
        benchmark_comparison = []
        for metric, value in industry_benchmark.items():
            actual_value = None
            if metric == "profit_margin":
                actual_value = profit_margin
            elif metric == "revenue_growth":
                actual_value = growth_rate
            elif metric in additional_metrics:
                actual_value = additional_metrics[metric]
            
            if actual_value is not None:
                difference = actual_value - value
                percent_diff = (difference / value) * 100 if value > 0 else 0
                status = "Above benchmark" if difference > 0 else "Below benchmark"
                assessment = self._assess_metric_performance(metric, actual_value, value, difference)
                
                comparison = {
                    "metric": metric,
                    "actual": actual_value,
                    "benchmark": value,
                    "difference": difference,
                    "percent_difference": percent_diff,
                    "status": status,
                    "assessment": assessment
                }
                benchmark_comparison.append(comparison)
        
        # Generate financial insights
        financial_insights = self._generate_financial_insights(
            profit_margin, growth_rate, benchmark_comparison, additional_metrics
        )
        
        # Generate recommendations
        recommendations = self._generate_financial_recommendations(
            profit_margin, growth_rate, benchmark_comparison, additional_metrics
        )
        
        # Create a structured financial analysis
        analysis = {
            "financial_overview": {
                "time_period": time_period,
                "total_revenue": revenue,
                "total_costs": costs,
                "profit": profit,
                "profit_margin": profit_margin,
                "growth_rate": growth_rate if growth_rate is not None else "Not provided"
            },
            "key_metrics": {
                "profitability": {
                    "profit": profit,
                    "profit_margin": f"{profit_margin:.2f}%",
                    "assessment": self._assess_profit_margin(profit_margin)
                },
                "growth": {
                    "rate": f"{growth_rate:.2f}%" if growth_rate is not None else "Not provided",
                    "assessment": self._assess_growth_rate(growth_rate) if growth_rate is not None else "No growth data provided"
                },
                "additional_metrics": additional_metrics
            },
            "industry_comparison": benchmark_comparison if benchmark_comparison else "No benchmark data provided",
            "financial_insights": financial_insights,
            "recommendations": recommendations,
            "detailed_analysis": self._generate_detailed_financial_analysis(
                time_period, revenue, costs, profit, profit_margin, growth_rate,
                benchmark_comparison, financial_insights, recommendations, additional_metrics
            )
        }
        
        return analysis
    
    def calculate_business_performance_metrics(
        self,
        revenue: Optional[float] = None,
        costs: Optional[float] = None,
        time_period: Optional[str] = None,
        previous_revenue: Optional[float] = None,
        previous_costs: Optional[float] = None,
        units_sold: Optional[int] = None,
        marketing_spend: Optional[float] = None,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive business performance metrics based on provided financial data.
        
        Args:
            revenue: Total revenue for the specified time period.
            costs: Total costs for the specified time period.
            time_period: The time period for the data (e.g., "Q2 2023", "FY 2022").
            previous_revenue: Optional revenue from previous comparable period for growth calculations.
            previous_costs: Optional costs from previous comparable period for growth calculations.
            units_sold: Optional number of units sold for unit economics calculations.
            marketing_spend: Optional marketing spend for marketing efficiency calculations.
            industry: Optional industry or sector for benchmark comparisons.
            
        Returns:
            Dictionary containing calculated business metrics with interpretations.
        """
        # Validate input parameters
        if revenue is not None and revenue < 0:
            logger.warning("Received negative revenue value, adjusting to 0")
            revenue = 0
            
        if costs is not None and costs < 0:
            logger.warning("Received negative costs value, adjusting to 0")
            costs = 0
            
        if previous_revenue is not None and previous_revenue < 0:
            logger.warning("Received negative previous revenue value, adjusting to 0")
            previous_revenue = 0
            
        if previous_costs is not None and previous_costs < 0:
            logger.warning("Received negative previous costs value, adjusting to 0")
            previous_costs = 0
            
        if units_sold is not None and units_sold < 0:
            logger.warning("Received negative units sold value, adjusting to 0")
            units_sold = 0
            
        if marketing_spend is not None and marketing_spend < 0:
            logger.warning("Received negative marketing spend value, adjusting to 0")
            marketing_spend = 0
        
        # Set default values for required parameters
        revenue = revenue or 0.0
        costs = costs or 0.0
        time_period = time_period or "Current period"
        
        logger.info(f"Calculating business performance metrics for {time_period}")
        
        # Normalize industry for benchmark lookup
        normalized_industry = self._normalize_industry(industry or "default")
        industry_benchmarks = self.INDUSTRY_BENCHMARKS.get(normalized_industry, self.INDUSTRY_BENCHMARKS["default"])
        
        # Calculate core metrics
        gross_profit = revenue - costs
        profit_margin = (gross_profit / revenue) * 100 if revenue > 0 else 0
        
        # Initialize results dictionary
        results = {
            "time_period": time_period,
            "industry": industry or "Not specified",
            "core_metrics": {
                "revenue": revenue,
                "costs": costs,
                "gross_profit": gross_profit,
                "profit_margin_percentage": profit_margin,
                "benchmark_comparison": {
                    "profit_margin_benchmark": industry_benchmarks["profit_margin"],
                    "difference": profit_margin - industry_benchmarks["profit_margin"],
                    "assessment": self._assess_profit_margin_compared_to_benchmark(
                        profit_margin, industry_benchmarks["profit_margin"]
                    )
                }
            }
        }
        
        # Calculate growth metrics if previous period data is provided
        if previous_revenue is not None:
            revenue_growth = ((revenue - previous_revenue) / previous_revenue) * 100 if previous_revenue > 0 else 0
            results["growth_metrics"] = {
                "revenue_growth_percentage": revenue_growth,
                "benchmark_comparison": {
                    "growth_benchmark": industry_benchmarks["revenue_growth"],
                    "difference": revenue_growth - industry_benchmarks["revenue_growth"],
                    "assessment": self._assess_growth_rate_compared_to_benchmark(
                        revenue_growth, industry_benchmarks["revenue_growth"]
                    )
                }
            }
            
            if previous_costs is not None:
                previous_profit = previous_revenue - previous_costs
                profit_growth = ((gross_profit - previous_profit) / previous_profit) * 100 if previous_profit > 0 else 0
                cost_growth = ((costs - previous_costs) / previous_costs) * 100 if previous_costs > 0 else 0
                
                results["growth_metrics"].update({
                    "cost_growth_percentage": cost_growth,
                    "profit_growth_percentage": profit_growth,
                    "efficiency_trend": self._assess_efficiency_trend(revenue_growth, cost_growth)
                })
        
        # Calculate unit economics if units sold is provided
        if units_sold is not None and units_sold > 0:
            revenue_per_unit = revenue / units_sold
            cost_per_unit = costs / units_sold
            profit_per_unit = gross_profit / units_sold
            
            results["unit_economics"] = {
                "units_sold": units_sold,
                "revenue_per_unit": revenue_per_unit,
                "cost_per_unit": cost_per_unit,
                "profit_per_unit": profit_per_unit,
                "unit_economics_assessment": self._assess_unit_economics(
                    revenue_per_unit, cost_per_unit, profit_per_unit, industry
                )
            }
        
        # Calculate marketing efficiency if marketing spend is provided
        if marketing_spend is not None and marketing_spend > 0:
            marketing_roi = ((gross_profit - marketing_spend) / marketing_spend) * 100 if marketing_spend > 0 else 0
            marketing_percent_of_revenue = (marketing_spend / revenue) * 100 if revenue > 0 else 0
            
            results["marketing_metrics"] = {
                "marketing_spend": marketing_spend,
                "marketing_roi_percentage": marketing_roi,
                "marketing_percentage_of_revenue": marketing_percent_of_revenue,
                "benchmark_comparison": {
                    "marketing_spend_benchmark": industry_benchmarks["marketing_percentage"],
                    "difference": marketing_percent_of_revenue - industry_benchmarks["marketing_percentage"],
                    "assessment": self._assess_marketing_spend(
                        marketing_percent_of_revenue, industry_benchmarks["marketing_percentage"]
                    )
                }
            }
            
            if units_sold and units_sold > 0:
                customer_acquisition_cost = marketing_spend / units_sold
                customer_lifetime_value = profit_per_unit * 3  # Simplified LTV estimation
                ltv_to_cac_ratio = customer_lifetime_value / customer_acquisition_cost if customer_acquisition_cost > 0 else 0
                
                results["marketing_metrics"].update({
                    "customer_acquisition_cost": customer_acquisition_cost,
                    "estimated_customer_lifetime_value": customer_lifetime_value,
                    "ltv_to_cac_ratio": ltv_to_cac_ratio,
                    "ltv_cac_assessment": self._assess_ltv_cac_ratio(ltv_to_cac_ratio)
                })
        
        # Add interpretations and insights
        results["interpretations"] = {
            "profit_margin": self._interpret_profit_margin(profit_margin),
            "overall_assessment": self._generate_business_assessment(
                profit_margin,
                results.get("growth_metrics", {}).get("revenue_growth_percentage"),
                results.get("growth_metrics", {}).get("profit_growth_percentage")
            )
        }
        
        # Add recommendations based on the metrics
        results["recommendations"] = self._generate_business_recommendations(results)
        
        return results
    
    def calculate_market_sizing(
        self,
        target_market: Optional[str] = None,
        market_approach: Optional[str] = None,
        total_market_size: Optional[float] = None,
        market_growth_rate: Optional[float] = None,
        addressable_percentage: Optional[float] = None,
        serviceable_percentage: Optional[float] = None,
        obtainable_percentage: Optional[float] = None,
        unit_price: Optional[float] = None,
        population_size: Optional[int] = None,
        penetration_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate market size estimates using various market sizing methodologies.
        
        Args:
            target_market: Description of the target market being analyzed.
            market_approach: Methodology to use ("TAM-SAM-SOM" or "Bottom-Up").
            total_market_size: Optional total market size in monetary value (for TAM-SAM-SOM approach).
            market_growth_rate: Optional annual market growth rate as percentage.
            addressable_percentage: Optional percentage of total market that is addressable (for TAM-SAM-SOM).
            serviceable_percentage: Optional percentage of addressable market that is serviceable (for TAM-SAM-SOM).
            obtainable_percentage: Optional percentage of serviceable market that is obtainable (for TAM-SAM-SOM).
            unit_price: Optional average price per unit or customer (for Bottom-Up approach).
            population_size: Optional total population or customer count (for Bottom-Up approach).
            penetration_rate: Optional market penetration rate as percentage (for Bottom-Up approach).
            
        Returns:
            Dictionary containing market size estimates with methodology explanation.
        """
        # Validate input parameters
        if total_market_size is not None and total_market_size < 0:
            logger.warning("Received negative total market size, adjusting to 0")
            total_market_size = 0
            
        if market_growth_rate is not None and market_growth_rate < -100:
            logger.warning("Received market growth rate below -100%, adjusting to -100%")
            market_growth_rate = -100
            
        if addressable_percentage is not None:
            addressable_percentage = max(0, min(100, addressable_percentage))
            
        if serviceable_percentage is not None:
            serviceable_percentage = max(0, min(100, serviceable_percentage))
            
        if obtainable_percentage is not None:
            obtainable_percentage = max(0, min(100, obtainable_percentage))
            
        if unit_price is not None and unit_price < 0:
            logger.warning("Received negative unit price, adjusting to 0")
            unit_price = 0
            
        if population_size is not None and population_size < 0:
            logger.warning("Received negative population size, adjusting to 0")
            population_size = 0
            
        if penetration_rate is not None:
            penetration_rate = max(0, min(100, penetration_rate))
        
        # Set default values
        target_market = target_market or "Generic market"
        market_approach = market_approach or "TAM-SAM-SOM"
        
        logger.info(f"Calculating market sizing for {target_market} using {market_approach} approach")
        
        result = {
            "target_market": target_market,
            "sizing_approach": market_approach,
            "market_growth_rate": market_growth_rate
        }
        
        if market_approach.upper() == "TAM-SAM-SOM":
            # Check for required parameters
            if total_market_size is None:
                return {"error": "Total market size is required for TAM-SAM-SOM approach"}
            
            # Set default percentages if not provided
            addressable_percentage = addressable_percentage or 30.0
            serviceable_percentage = serviceable_percentage or 40.0
            obtainable_percentage = obtainable_percentage or 10.0
            
            # Calculate TAM, SAM, and SOM
            tam = total_market_size
            sam = tam * (addressable_percentage / 100)
            som = sam * (serviceable_percentage / 100) * (obtainable_percentage / 100)
            
            result.update({
                "total_addressable_market": {
                    "value": tam,
                    "description": "Total size of the market that could theoretically be served"
                },
                "serviceable_addressable_market": {
                    "value": sam,
                    "percentage_of_tam": addressable_percentage,
                    "description": "Portion of the market that can realistically be targeted"
                },
                "serviceable_obtainable_market": {
                    "value": som,
                    "percentage_of_sam": serviceable_percentage,
                    "obtainable_percentage": obtainable_percentage,
                    "description": "Portion of the market that can realistically be captured"
                },
                "methodology": {
                    "tam_calculation": "Used provided total market size value",
                    "sam_calculation": f"TAM × Addressable Percentage = ${tam:,.2f} × {addressable_percentage}%",
                    "som_calculation": f"SAM × Serviceable Percentage × Obtainable Percentage = ${sam:,.2f} × {serviceable_percentage}% × {obtainable_percentage}%"
                }
            })
            
            # Add growth projections if growth rate is provided
            if market_growth_rate is not None:
                growth_multiplier = (1 + market_growth_rate/100)
                five_year_tam = tam * (growth_multiplier ** 5)
                five_year_sam = sam * (growth_multiplier ** 5)
                five_year_som = som * (growth_multiplier ** 5)
                
                result["five_year_projections"] = {
                    "projected_tam": five_year_tam,
                    "projected_sam": five_year_sam,
                    "projected_som": five_year_som,
                    "calculation_methodology": f"Current value × (1 + {market_growth_rate}%)^5"
                }
        
        elif market_approach.upper() == "BOTTOM-UP":
            # Check for required parameters
            if any(param is None for param in [unit_price, population_size, penetration_rate]):
                return {"error": "Unit price, population size, and penetration rate are required for Bottom-Up approach"}
            
            # Calculate total potential market and obtainable market
            total_potential_market = population_size * unit_price
            obtainable_market = total_potential_market * (penetration_rate / 100)
            
            result.update({
                "market_parameters": {
                    "population_size": population_size,
                    "unit_price": unit_price,
                    "penetration_rate": penetration_rate
                },
                "total_potential_market": {
                    "value": total_potential_market,
                    "description": "Maximum theoretical market size if 100% penetration was achieved"
                },
                "obtainable_market": {
                    "value": obtainable_market,
                    "description": "Realistic market size based on achievable penetration rate"
                },
                "methodology": {
                    "total_potential_calculation": f"Population Size × Unit Price = {population_size:,} × ${unit_price:,.2f}",
                    "obtainable_calculation": f"Total Potential Market × Penetration Rate = ${total_potential_market:,.2f} × {penetration_rate}%"
                }
            })
            
            # Add growth projections if growth rate is provided
            if market_growth_rate is not None:
                growth_multiplier = (1 + market_growth_rate/100)
                five_year_population = population_size * (growth_multiplier ** 5)
                five_year_market = five_year_population * unit_price * (penetration_rate / 100)
                
                result["five_year_projections"] = {
                    "projected_population": five_year_population,
                    "projected_obtainable_market": five_year_market,
                    "calculation_methodology": f"Current population × (1 + {market_growth_rate}%)^5, then applying unit price and penetration rate"
                }
        
        else:
            return {"error": f"Unsupported market sizing approach: {market_approach}. Use 'TAM-SAM-SOM' or 'Bottom-Up'."}
        
        # Add interpretation of market sizing results
        result["interpretation"] = self._interpret_market_sizing_results(result)
        
        # Add strategic implications
        result["strategic_implications"] = self._generate_market_sizing_implications(result)
        
        return result
    
    def calculate_pricing_optimization(
        self,
        product_name: Optional[str] = None,
        current_price: Optional[float] = None,
        current_volume: Optional[int] = None,
        variable_cost: Optional[float] = None,
        fixed_costs: Optional[float] = None,
        price_elasticity: Optional[float] = None,
        competitor_prices: Optional[List[float]] = None,
        pricing_strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimized pricing recommendations based on cost structure, volume, and elasticity.
        
        Args:
            product_name: Name of the product or service being priced.
            current_price: Optional current price of the product or service.
            current_volume: Optional current sales volume at the current price.
            variable_cost: Optional variable cost per unit.
            fixed_costs: Optional total fixed costs.
            price_elasticity: Optional price elasticity of demand (-2.0 means 1% price increase reduces demand by 2%).
            competitor_prices: Optional list of competitor prices for similar products/services.
            pricing_strategy: Optional pricing strategy to prioritize ("profit", "revenue", "market_share", "premium").
            
        Returns:
            Dictionary containing pricing analysis, recommendations, and optimizations.
        """
        # Validate input parameters
        if current_price is not None and current_price < 0:
            logger.warning("Received negative current price, adjusting to 0")
            current_price = 0
            
        if current_volume is not None and current_volume < 0:
            logger.warning("Received negative current volume, adjusting to 0")
            current_volume = 0
            
        if variable_cost is not None and variable_cost < 0:
            logger.warning("Received negative variable cost, adjusting to 0")
            variable_cost = 0
            
        if fixed_costs is not None and fixed_costs < 0:
            logger.warning("Received negative fixed costs, adjusting to 0")
            fixed_costs = 0
            
        if competitor_prices:
            competitor_prices = [max(0, price) for price in competitor_prices]
        
        # Set default values for required parameters
        product_name = product_name or "Product"
        pricing_strategy = pricing_strategy or "profit"
        
        logger.info(f"Calculating pricing optimization for {product_name}")
        
        # Initialize result structure
        result = {
            "product_name": product_name,
            "pricing_strategy": pricing_strategy,
            "current_pricing": {}
        }
        
        # Add current pricing information if available
        if current_price is not None:
            result["current_pricing"]["price"] = current_price
            
            if current_volume is not None:
                current_revenue = current_price * current_volume
                result["current_pricing"]["volume"] = current_volume
                result["current_pricing"]["revenue"] = current_revenue
                
                if variable_cost is not None:
                    contribution_margin = current_price - variable_cost
                    contribution_margin_percentage = (contribution_margin / current_price) * 100 if current_price > 0 else 0
                    total_contribution = contribution_margin * current_volume
                    
                    result["current_pricing"]["cost_structure"] = {
                        "variable_cost_per_unit": variable_cost,
                        "contribution_margin_per_unit": contribution_margin,
                        "contribution_margin_percentage": contribution_margin_percentage,
                        "total_contribution": total_contribution
                    }
                    
                    if fixed_costs is not None:
                        profit = total_contribution - fixed_costs
                        break_even_volume = fixed_costs / contribution_margin if contribution_margin > 0 else float('inf')
                        
                        result["current_pricing"]["cost_structure"].update({
                            "fixed_costs": fixed_costs,
                            "profit": profit,
                            "break_even_volume": break_even_volume,
                            "volume_to_break_even_ratio": (current_volume / break_even_volume if break_even_volume > 0 else float('inf')),
                            "break_even_assessment": self._assess_break_even_point(current_volume, break_even_volume)
                        })
        
        # Add competitive analysis if competitor prices are provided
        if competitor_prices:
            avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
            min_competitor_price = min(competitor_prices)
            max_competitor_price = max(competitor_prices)
            
            result["competitive_analysis"] = {
                "average_competitor_price": avg_competitor_price,
                "minimum_competitor_price": min_competitor_price,
                "maximum_competitor_price": max_competitor_price,
                "competitor_prices": competitor_prices,
                "price_spread": max_competitor_price - min_competitor_price,
                "price_variance": np.var(competitor_prices) if len(competitor_prices) > 1 else 0
            }
            
            if current_price is not None:
                price_position = (current_price - min_competitor_price) / (max_competitor_price - min_competitor_price) * 100 if (max_competitor_price > min_competitor_price) else 50
                price_relative_to_avg = ((current_price / avg_competitor_price) - 1) * 100 if avg_competitor_price > 0 else 0
                
                result["competitive_analysis"].update({
                    "price_position_percentile": price_position,
                    "price_relative_to_average": price_relative_to_avg,
                    "competitive_position_assessment": self._assess_competitive_price_position(
                        price_position, price_relative_to_avg
                    )
                })
        
        # Calculate optimized pricing if elasticity and current price/volume are available
        if price_elasticity is not None and current_price is not None and current_volume is not None:
            # Ensure elasticity is negative for normal demand curves
            if price_elasticity > 0:
                logger.warning("Received positive price elasticity, converting to negative value")
                price_elasticity = -price_elasticity
            
            # Calculate price optimization scenarios
            price_scenarios = self._calculate_price_scenarios(
                current_price, current_volume, price_elasticity, variable_cost, fixed_costs
            )
            
            result["price_elasticity"] = price_elasticity
            result["price_scenarios"] = price_scenarios
            
            # Determine optimized price based on strategy
            optimized_price, optimization_basis = self._determine_optimized_price(
                price_scenarios, pricing_strategy
            )
            
            # Calculate expected impact of price change
            price_change_percentage = ((optimized_price / current_price) - 1) * 100 if current_price > 0 else 0
            volume_impact_percentage = price_change_percentage * price_elasticity
            new_expected_volume = current_volume * (1 + volume_impact_percentage/100)
            revenue_impact_percentage = ((optimized_price * new_expected_volume) / (current_price * current_volume) - 1) * 100 if (current_price * current_volume) > 0 else 0
            
            result["pricing_recommendations"] = {
                "optimized_price": optimized_price,
                "optimization_basis": optimization_basis,
                "pricing_strategy": pricing_strategy,
                "expected_impact": {
                    "price_change_percentage": price_change_percentage,
                    "expected_volume_impact": volume_impact_percentage,
                    "expected_revenue_impact": revenue_impact_percentage
                },
                "implementation_considerations": self._generate_pricing_implementation_considerations(
                    price_change_percentage, product_name, competitor_prices
                )
            }
        
        # Add recommendations and interpretation
        result["analysis_and_recommendations"] = self._interpret_pricing_analysis(result)
        
        return result
    
    # Helper methods for business model analysis
    
    def _normalize_industry(self, industry: Optional[str]) -> str:
        """
        Normalize industry name to match benchmark categories.
        
        Args:
            industry: Industry name to normalize.
            
        Returns:
            Normalized industry name for benchmark lookup.
        """
        if not industry:
            return "default"
            
        industry_lower = industry.lower()
        
        if any(tech in industry_lower for tech in ["tech", "software", "it", "information technology", "saas", "digital"]):
            return "technology"
        elif any(retail in industry_lower for retail in ["retail", "ecommerce", "e-commerce", "store", "shop"]):
            return "retail"
        elif any(mfg in industry_lower for mfg in ["manufacturing", "factory", "production", "industrial"]):
            return "manufacturing"
        elif any(health in industry_lower for health in ["health", "medical", "pharma", "hospital", "care"]):
            return "healthcare"
        elif any(fin in industry_lower for fin in ["financial", "banking", "insurance", "finance", "investment"]):
            return "financial_services"
        else:
            return "default"
    
    def _analyze_business_model_strengths(
        self, 
        industry: str, 
        revenue_streams: List[str],
        cost_structure: List[str],
        key_resources: Optional[List[str]],
        customer_segments: Optional[List[str]],
        competitive_advantage: Optional[str]
    ) -> List[str]:
        """
        Analyze strengths of a business model based on provided components.
        """
        strengths = []
        
        # Revenue stream analysis
        if len(revenue_streams) > 2:
            strengths.append("Diversified revenue streams reduce dependency on any single source of income")
        
        if key_resources and any("proprietary" in r.lower() for r in key_resources):
            strengths.append("Proprietary resources provide competitive differentiation and potential barriers to entry")
        
        if customer_segments and len(customer_segments) > 1:
            strengths.append("Multiple customer segments allow for market diversification and cross-selling opportunities")
        
        if competitive_advantage:
            if "cost" in competitive_advantage.lower():
                strengths.append("Cost advantage provides pricing flexibility and margin protection")
            if any(term in competitive_advantage.lower() for term in ["unique", "differentiated", "innovative"]):
                strengths.append("Unique value proposition creates strong market differentiation")
            if "network" in competitive_advantage.lower():
                strengths.append("Network effects create scalable growth potential and increasing returns to scale")
        
        # Industry-specific strengths
        normalized_industry = self._normalize_industry(industry)
        if normalized_industry == "technology":
            strengths.append("Technology sector offers high scalability with marginal incremental costs")
        elif normalized_industry == "financial_services":
            strengths.append("Financial services typically generate recurring revenue and high customer retention")
        
        return strengths if strengths else ["Insufficient data to identify specific strengths"]
    
    def _analyze_business_model_weaknesses(
        self, 
        industry: str, 
        revenue_streams: List[str],
        cost_structure: List[str],
        key_resources: Optional[List[str]],
        customer_segments: Optional[List[str]],
        competitive_advantage: Optional[str],
        missing_components: List[str]
    ) -> List[str]:
        """
        Analyze weaknesses of a business model based on provided components.
        """
        weaknesses = []
        
        # Missing components analysis
        if missing_components:
            if len(missing_components) > 3:
                weaknesses.append(f"Incomplete business model definition with multiple missing components: {', '.join(missing_components)}")
            else:
                for component in missing_components:
                    if component == "customer_segments":
                        weaknesses.append("Undefined customer segments may lead to unfocused marketing and product development")
                    elif component == "revenue_streams":
                        weaknesses.append("Unclear revenue model may impact financial planning and resource allocation")
                    elif component == "value_propositions":
                        weaknesses.append("Undefined value proposition may weaken market positioning and customer acquisition")
        
        # Revenue stream analysis
        if len(revenue_streams) == 1:
            weaknesses.append("Reliance on a single revenue stream creates business vulnerability to market changes")
        
        # Customer segment analysis
        if not customer_segments or len(customer_segments) == 0:
            weaknesses.append("Undefined customer segments may lead to unfocused marketing and product development")
        
        # Industry-specific weaknesses
        normalized_industry = self._normalize_industry(industry)
        if normalized_industry == "retail":
            weaknesses.append("Retail typically faces thin margins and high competitive pressure")
        elif normalized_industry == "manufacturing":
            weaknesses.append("Manufacturing often requires significant capital investment and faces capacity constraints")
        
        return weaknesses if weaknesses else ["No significant weaknesses identified with the available information"]
    
    def _analyze_business_model_opportunities(
        self, 
        industry: str, 
        revenue_streams: List[str],
        cost_structure: List[str],
        key_resources: Optional[List[str]],
        customer_segments: Optional[List[str]],
        competitive_advantage: Optional[str]
    ) -> List[str]:
        """
        Analyze opportunities for a business model based on provided components.
        """
        opportunities = []
        
        # Revenue stream opportunities
        existing_revenue_types = " ".join(revenue_streams).lower()
        if "subscription" not in existing_revenue_types:
            opportunities.append("Explore subscription-based revenue models to create recurring income and improve customer lifetime value")
        
        if "service" not in existing_revenue_types and "product" in existing_revenue_types:
            opportunities.append("Develop complementary services to expand revenue from existing product customers")
        
        # Customer segment opportunities
        if customer_segments and len(customer_segments) <= 2:
            opportunities.append("Explore adjacent customer segments to expand market reach")
        
        # Industry-specific opportunities
        normalized_industry = self._normalize_industry(industry)
        if normalized_industry == "technology":
            opportunities.append("Explore API or platform business models to create ecosystem value and additional revenue streams")
        elif normalized_industry == "retail":
            opportunities.append("Develop omnichannel presence to improve customer experience and expand market reach")
        elif normalized_industry == "healthcare":
            opportunities.append("Explore telehealth and digital health technologies to expand service delivery options")
        
        return opportunities if opportunities else ["Additional market research needed to identify specific opportunities"]
    
    def _analyze_business_model_threats(
        self, 
        industry: str, 
        revenue_streams: List[str],
        cost_structure: List[str],
        key_resources: Optional[List[str]],
        customer_segments: Optional[List[str]]
    ) -> List[str]:
        """
        Analyze threats to a business model based on provided components.
        """
        threats = []
        
        # Industry-specific threats
        normalized_industry = self._normalize_industry(industry)
        if normalized_industry == "technology":
            threats.append("Rapid technological change creating risk of obsolescence and continuous investment requirements")
            threats.append("Low barriers to entry in many technology segments leading to increasing competition")
        elif normalized_industry == "retail":
            threats.append("E-commerce disruption changing consumer behavior and increasing price transparency")
            threats.append("Increasing logistics and fulfillment costs affecting margins")
        elif normalized_industry == "manufacturing":
            threats.append("Supply chain vulnerabilities and raw material price volatility")
            threats.append("Automation and technological advancement requiring continuous capital investment")
        elif normalized_industry == "healthcare":
            threats.append("Regulatory changes affecting reimbursement and compliance costs")
            threats.append("Technological disruption changing service delivery models")
        elif normalized_industry == "financial_services":
            threats.append("Fintech disruption changing consumer expectations and service models")
            threats.append("Regulatory changes increasing compliance requirements and costs")
        else:
            threats.append("Market disruption from new technologies and business models")
            threats.append("Changing customer preferences and expectations")
        
        # Revenue model threats
        if len(revenue_streams) == 1:
            threats.append("Vulnerability to disruption in primary revenue channel")
        
        return threats
    
    def _generate_business_model_recommendations(
        self,
        strengths: List[str],
        weaknesses: List[str],
        opportunities: List[str],
        threats: List[str],
        benchmarks: Dict[str, float],
        industry: str
    ) -> List[str]:
        """
        Generate business model recommendations based on SWOT analysis.
        """
        recommendations = []
        
        # Address major weaknesses
        for weakness in weaknesses:
            if "single revenue stream" in weakness.lower():
                recommendations.append("Develop additional revenue streams to diversify income sources and reduce market vulnerability")
            elif "unfocused marketing" in weakness.lower() or "undefined customer segments" in weakness.lower():
                recommendations.append("Conduct customer segmentation analysis to identify and prioritize key customer groups")
        
        # Leverage opportunities
        for opportunity in opportunities:
            if "subscription" in opportunity.lower():
                recommendations.append("Evaluate subscription-based revenue models for applicable products/services")
            elif "adjacent customer segments" in opportunity.lower():
                recommendations.append("Research and test expansion into adjacent customer segments with similar needs")
        
        # Mitigate threats
        for threat in threats:
            if "technological change" in threat.lower() or "disruption" in threat.lower():
                recommendations.append("Establish ongoing competitive and technology monitoring to identify emerging threats")
            elif "supply chain" in threat.lower():
                recommendations.append("Develop supply chain resilience strategies including diversification of suppliers")
        
        # Industry-specific recommendations
        normalized_industry = self._normalize_industry(industry)
        if normalized_industry == "technology":
            recommendations.append("Implement agile development methodologies to improve responsiveness to market changes")
        elif normalized_industry == "retail":
            recommendations.append("Develop integrated online and offline customer experience to adapt to changing shopping behaviors")
        elif normalized_industry == "healthcare":
            recommendations.append("Explore value-based pricing models aligned with patient outcomes")
        
        return recommendations if recommendations else ["Conduct detailed business model canvas exercise to identify specific optimization opportunities"]
    
    def _generate_detailed_business_model_analysis(
        self,
        industry: str,
        revenue_streams: List[str],
        cost_structure: List[str],
        key_resources: Optional[List[str]],
        customer_segments: Optional[List[str]],
        competitive_advantage: Optional[str],
        benchmarks: Dict[str, float],
        strengths: List[str],
        weaknesses: List[str],
        opportunities: List[str],
        threats: List[str]
    ) -> str:
        """
        Generate detailed business model analysis text.
        """
        # Format inputs for display
        revenue_str = "\n".join([f"- {stream}" for stream in revenue_streams]) if revenue_streams else "Not specified"
        cost_str = "\n".join([f"- {cost}" for cost in cost_structure]) if cost_structure else "Not specified"
        resources_str = "\n".join([f"- {resource}" for resource in (key_resources or [])]) if key_resources else "Not specified"
        segments_str = "\n".join([f"- {segment}" for segment in (customer_segments or [])]) if customer_segments else "Not specified"
        
        # Generate strengths, weaknesses, opportunities, threats sections
        strengths_str = "\n".join([f"- {strength}" for strength in strengths])
        weaknesses_str = "\n".join([f"- {weakness}" for weakness in weaknesses])
        opportunities_str = "\n".join([f"- {opportunity}" for opportunity in opportunities])
        threats_str = "\n".join([f"- {threat}" for threat in threats])
        
        # Industry analysis
        normalized_industry = self._normalize_industry(industry)
        industry_analysis = ""
        if normalized_industry == "technology":
            industry_analysis = """The technology industry is characterized by rapid innovation, scalability, and potential for high margins. 
Key success factors include technological differentiation, strong intellectual property, and ability to scale.
The industry faces challenges of rapid obsolescence and relatively low barriers to entry in many segments."""
        elif normalized_industry == "technology":
            industry_analysis = """The technology industry is characterized by rapid innovation, scalability, and potential for high margins. 
Key success factors include technological differentiation, strong intellectual property, and ability to scale.
The industry faces challenges of rapid obsolescence and relatively low barriers to entry in many segments."""
        elif normalized_industry == "retail":
            industry_analysis = """The retail industry operates on relatively thin margins with high competition. 
Key success factors include efficient operations, strong brand positioning, and effective supply chain management.
The industry is experiencing significant disruption from e-commerce and changing consumer behaviors."""
        elif normalized_industry == "manufacturing":
            industry_analysis = """The manufacturing industry requires significant capital investment and operational efficiency. 
Key success factors include scale, process optimization, and supply chain management.
The industry faces challenges from global competition, raw material costs, and technological advancement."""
        elif normalized_industry == "healthcare":
            industry_analysis = """The healthcare industry combines mission-driven service with complex regulatory requirements. 
Key success factors include quality outcomes, regulatory compliance, and efficient operations.
The industry is experiencing significant change from technology, policy shifts, and demographic trends."""
        elif normalized_industry == "financial_services":
            industry_analysis = """The financial services industry provides essential economic infrastructure with high regulatory oversight. 
Key success factors include risk management, trust, and technological capabilities.
The industry faces disruption from fintech innovation and changing customer expectations."""
        else:
            industry_analysis = f"""The {industry} industry has specific dynamics and success factors that should be analyzed in detail.
A comprehensive industry analysis would help identify key success factors and competitive dynamics."""
        
        # Create detailed analysis markdown
        detailed_analysis = f"""
# Business Model Analysis

## Industry Context
{industry_analysis}

## Revenue Structure
{revenue_str}

## Cost Structure
{cost_str}

## Key Resources
{resources_str}

## Customer Segments
{segments_str}

## Competitive Advantage
{competitive_advantage or "Not specified"}

## SWOT Analysis

### Strengths
{strengths_str}

### Weaknesses
{weaknesses_str}

### Opportunities
{opportunities_str}

### Threats
{threats_str}

## Model Assessment
The business model demonstrates {"strong coherence between components" if len(strengths) > len(weaknesses) else "some misalignment between components that should be addressed"}.
{"Revenue diversification appears adequate" if len(revenue_streams) > 1 else "Revenue concentration in a single stream creates vulnerability"}.
{"Customer segmentation provides focus" if customer_segments and len(customer_segments) > 0 else "Customer segmentation requires further development"}.
"""
        
        return detailed_analysis
    
    # Helper methods for strategy development
    
    def _parse_timeframe_to_months(self, timeframe: str) -> int:
        """
        Parse timeframe string to estimate number of months.
        
        Args:
            timeframe: String description of timeframe (e.g., "6 months", "2 years").
            
        Returns:
            Estimated number of months.
        """
        timeframe_lower = timeframe.lower()
        
        # Extract numbers from the timeframe string
        import re
        numbers = re.findall(r'\d+', timeframe_lower)
        if not numbers:
            return 12  # Default to 12 months if no numbers found
        
        quantity = int(numbers[0])
        
        # Determine the time unit
        if "year" in timeframe_lower:
            return quantity * 12
        elif "month" in timeframe_lower:
            return quantity
        elif "week" in timeframe_lower:
            return max(1, round(quantity / 4.33))  # Approximate weeks to months
        elif "day" in timeframe_lower:
            return max(1, round(quantity / 30.4))  # Approximate days to months
        elif "quarter" in timeframe_lower:
            return quantity * 3
        else:
            return 12  # Default to 12 months if unit not recognized
    
    def _categorize_business_goal(self, goal: str) -> tuple:
        """
        Categorize business goal type and focus.
        
        Args:
            goal: Business goal description.
            
        Returns:
            Tuple of (goal_type, goal_focus).
        """
        goal_lower = goal.lower()
        
        # Determine goal type
        if any(term in goal_lower for term in ["grow", "increase", "expand", "scale"]):
            goal_type = "growth"
        elif any(term in goal_lower for term in ["cost", "efficien", "optimi", "productivity"]):
            goal_type = "optimization"
        elif any(term in goal_lower for term in ["launch", "introduce", "new", "develop"]):
            goal_type = "innovation"
        elif any(term in goal_lower for term in ["restructure", "reorganize", "transform"]):
            goal_type = "transformation"
        else:
            goal_type = "general"
        
        # Determine goal focus
        if any(term in goal_lower for term in ["revenue", "sales", "income"]):
            goal_focus = "revenue"
        elif any(term in goal_lower for term in ["profit", "margin"]):
            goal_focus = "profit"
        elif any(term in goal_lower for term in ["market share", "customer", "acquisition"]):
            goal_focus = "market_share"
        elif any(term in goal_lower for term in ["product", "service", "offering"]):
            goal_focus = "product"
        elif any(term in goal_lower for term in ["international", "global", "region"]):
            goal_focus = "geographic_expansion"
        else:
            goal_focus = "general"
        
        return goal_type, goal_focus
    
    def _generate_strategic_objectives(self, goal_type: str, goal_focus: str, timeframe_months: int) -> List[str]:
        """
        Generate strategic objectives based on goal type and focus.
        
        Args:
            goal_type: Type of business goal (growth, optimization, etc.).
            goal_focus: Focus area of the goal (revenue, profit, etc.).
            timeframe_months: Timeframe in months.
            
        Returns:
            List of strategic objectives.
        """
        objectives = []
        
        # Time horizon classifier
        time_horizon = "short-term" if timeframe_months <= 6 else "medium-term" if timeframe_months <= 24 else "long-term"
        
        # Growth-oriented objectives
        if goal_type == "growth":
            if goal_focus == "revenue":
                objectives.append(f"Increase revenue by targeting higher-value customer segments")
                objectives.append(f"Expand product/service offerings to increase average transaction value")
                if time_horizon != "short-term":
                    objectives.append(f"Develop new revenue streams from adjacent markets or complementary products")
            elif goal_focus == "market_share":
                objectives.append(f"Increase market penetration in primary customer segments")
                objectives.append(f"Enhance competitive positioning through strengthened value proposition")
                if time_horizon != "short-term":
                    objectives.append(f"Develop strategic partnerships to access new customer channels")
            elif goal_focus == "geographic_expansion":
                objectives.append(f"Establish market presence in target geographic regions")
                objectives.append(f"Adapt offerings to meet local market requirements and preferences")
                objectives.append(f"Develop appropriate distribution and fulfillment capabilities for new markets")
        
        # Optimization-oriented objectives
        elif goal_type == "optimization":
            if goal_focus == "profit":
                objectives.append(f"Improve gross margin through pricing optimization and cost control")
                objectives.append(f"Enhance operational efficiency to reduce overhead costs")
                if time_horizon != "short-term":
                    objectives.append(f"Restructure business processes to eliminate redundancies and improve productivity")
            elif goal_focus == "general":
                objectives.append(f"Streamline core business processes to improve efficiency")
                objectives.append(f"Optimize resource allocation to high-value activities")
                objectives.append(f"Implement technology solutions to automate routine tasks")
        
        # Innovation-oriented objectives
        elif goal_type == "innovation":
            if goal_focus == "product":
                objectives.append(f"Develop and launch new products/services that address unmet customer needs")
                objectives.append(f"Establish product development capabilities and processes")
                if time_horizon != "short-term":
                    objectives.append(f"Create an innovation pipeline with staged development milestones")
            else:
                objectives.append(f"Establish innovation capabilities within the organization")
                objectives.append(f"Develop mechanisms to identify and evaluate market opportunities")
                objectives.append(f"Create processes for rapidly testing and iterating on new concepts")
        
        # Transformation-oriented objectives
        elif goal_type == "transformation":
            objectives.append(f"Realign organizational structure to support new strategic direction")
            objectives.append(f"Develop new capabilities required for future success")
            objectives.append(f"Manage transition while maintaining operational continuity")
        
        # General objectives (fallback)
        else:
            objectives.append(f"Establish clear metrics and KPIs to measure business performance")
            objectives.append(f"Develop competitive advantages in key market segments")
            objectives.append(f"Build organizational capabilities aligned with long-term vision")
        
        return objectives
    
    def _generate_key_strategies(
        self, 
        objectives: List[str], 
        goal_type: str, 
        available_resources: List[str],
        market_constraints: List[str]
    ) -> List[str]:
        """
        Generate key strategies to achieve objectives given resources and constraints.
        
        Args:
            objectives: List of strategic objectives.
            goal_type: Type of business goal.
            available_resources: List of available resources.
            market_constraints: List of market constraints.
            
        Returns:
            List of key strategies.
        """
        strategies = []
        
        # Resource assessment
        has_financial_resources = any("capital" in r.lower() or "fund" in r.lower() or "budget" in r.lower() for r in available_resources)
        has_human_resources = any("team" in r.lower() or "staff" in r.lower() or "personnel" in r.lower() for r in available_resources)
        has_technical_resources = any("tech" in r.lower() or "platform" in r.lower() or "system" in r.lower() for r in available_resources)
        has_brand_resources = any("brand" in r.lower() or "reputation" in r.lower() for r in available_resources)
        
        # Constraint assessment
        has_competitive_constraints = any("competition" in c.lower() or "competitor" in c.lower() for c in market_constraints)
        has_regulatory_constraints = any("regulation" in c.lower() or "compliance" in c.lower() or "legal" in c.lower() for c in market_constraints)
        has_resource_constraints = any("resource" in c.lower() or "capacity" in c.lower() or "limit" in c.lower() for c in market_constraints)
        
        # Generate strategies based on goal type and available resources
        if goal_type == "growth":
            if has_financial_resources:
                strategies.append("Invest in marketing and sales capabilities to accelerate customer acquisition")
                if not has_competitive_constraints:
                    strategies.append("Consider strategic acquisitions to rapidly expand market presence")
            
            if has_technical_resources:
                strategies.append("Leverage technology to scale operations efficiently without proportional cost increases")
            
            if has_brand_resources:
                strategies.append("Extend brand into adjacent markets or product categories")
            
            if has_resource_constraints:
                strategies.append("Pursue strategic partnerships to access complementary capabilities and resources")
        
        elif goal_type == "optimization":
            strategies.append("Implement data-driven decision making to identify and address inefficiencies")
            
            if has_technical_resources:
                strategies.append("Deploy automation and process optimization technologies to improve operational efficiency")
            
            if has_human_resources:
                strategies.append("Implement continuous improvement methodologies (e.g., Lean, Six Sigma) to enhance processes")
            
            if has_resource_constraints:
                strategies.append("Prioritize optimization initiatives based on ROI potential and resource requirements")
        
        elif goal_type == "innovation":
            if has_financial_resources:
                strategies.append("Allocate dedicated resources to research and development activities")
            
            if has_technical_resources:
                strategies.append("Create rapid prototyping capabilities to test concepts quickly and cost-effectively")
            
            strategies.append("Establish systematic processes for capturing and evaluating innovative ideas")
            
            if has_resource_constraints:
                strategies.append("Implement open innovation approaches to leverage external ideas and capabilities")
        
        elif goal_type == "transformation":
            strategies.append("Develop clear change management approach to guide transformation process")
            strategies.append("Create governance structure to oversee transformation initiatives")
            
            if has_human_resources:
                strategies.append("Invest in leadership development and organizational capabilities aligned with future state")
            
            if has_resource_constraints:
                strategies.append("Sequence transformation initiatives to manage resource requirements and organizational capacity")
        
        # Add general strategies if needed
        if len(strategies) < 3:
            strategies.append("Establish clear metrics and KPIs to track progress and guide decision making")
            strategies.append("Develop feedback mechanisms to identify issues early and enable rapid course correction")
        
        return strategies
    
    def _generate_implementation_phases(
        self, 
        strategies: List[str], 
        timeframe_months: int, 
        goal_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate implementation phases with activities and metrics.
        
        Args:
            strategies: Key strategies to implement.
            timeframe_months: Timeframe in months.
            goal_type: Type of business goal.
            
        Returns:
            List of implementation phase dictionaries.
        """
        # Determine number and duration of phases based on timeframe
        if timeframe_months <= 3:
            phases = [{"phase": "Implementation", "duration": f"{timeframe_months} months"}]
        elif timeframe_months <= 6:
            phases = [
                {"phase": "Phase 1: Foundation", "duration": f"{timeframe_months // 2} months"},
                {"phase": "Phase 2: Execution", "duration": f"{timeframe_months - (timeframe_months // 2)} months"}
            ]
        elif timeframe_months <= 12:
            phases = [
                {"phase": "Phase 1: Preparation", "duration": f"{timeframe_months // 3} months"},
                {"phase": "Phase 2: Implementation", "duration": f"{timeframe_months // 3} months"},
                {"phase": "Phase 3: Optimization", "duration": f"{timeframe_months - 2 * (timeframe_months // 3)} months"}
            ]
        else:
            phases = [
                {"phase": "Phase 1: Foundation", "duration": f"{timeframe_months // 4} months"},
                {"phase": "Phase 2: Building", "duration": f"{timeframe_months // 3} months"},
                {"phase": "Phase 3: Scaling", "duration": f"{timeframe_months // 3} months"},
                {"phase": "Phase 4: Optimization", "duration": f"{timeframe_months - ((timeframe_months // 4) + 2 * (timeframe_months // 3))} months"}
            ]
        
        # Generate activities and metrics for each phase
        for i, phase in enumerate(phases):
            # Generate appropriate activities based on phase and strategies
            if "Foundation" in phase["phase"] or "Preparation" in phase["phase"] or i == 0:
                activities = [
                    "Define detailed implementation plan with resource requirements and timelines",
                    "Establish baseline metrics and tracking mechanisms",
                    "Secure necessary resources and organizational alignment"
                ]
                
                if goal_type == "growth":
                    activities.append("Conduct market research to identify highest-potential opportunities")
                elif goal_type == "optimization":
                    activities.append("Conduct process audits to identify improvement opportunities")
                elif goal_type == "innovation":
                    activities.append("Establish innovation framework and governance process")
                elif goal_type == "transformation":
                    activities.append("Develop comprehensive change management and communication plan")
                
                metrics = [
                    "Completion of planning milestones",
                    "Resource allocation secured",
                    "Baseline metrics established"
                ]
            
            elif "Building" in phase["phase"] or "Implementation" in phase["phase"]:
                activities = [
                    "Execute core initiative components according to plan",
                    "Monitor progress against key milestones",
                    "Address implementation challenges as they arise"
                ]
                
                if goal_type == "growth":
                    activities.append("Launch marketing and sales initiatives to drive growth")
                elif goal_type == "optimization":
                    activities.append("Implement process improvements in priority areas")
                elif goal_type == "innovation":
                    activities.append("Develop and test prototypes of new concepts")
                elif goal_type == "transformation":
                    activities.append("Implement structural and process changes")
                
                metrics = [
                    "Implementation milestones achieved",
                    "Early performance indicators",
                    "Resource utilization efficiency"
                ]
            
            elif "Scaling" in phase["phase"]:
                activities = [
                    "Expand implementation to additional areas or markets",
                    "Refine approach based on early implementation learnings",
                    "Build capacity to support scaled operations"
                ]
                
                metrics = [
                    "Scaling velocity metrics",
                    "Operational performance indicators",
                    "Return on investment metrics"
                ]
            
            elif "Optimization" in phase["phase"] or i == len(phases) - 1:
                activities = [
                    "Evaluate results against objectives",
                    "Identify and address performance gaps",
                    "Document learnings and best practices",
                    "Establish mechanisms for continuous improvement"
                ]
                
                metrics = [
                    "Performance against target KPIs",
                    "ROI metrics",
                    "Implementation effectiveness assessment"
                ]
            
            # Add activities and metrics to phase
            phase["key_activities"] = activities
            phase["success_metrics"] = metrics
            
            # Determine responsible parties based on general organizational structure
            if i == 0:
                phase["responsible_parties"] = ["Executive Leadership", "Initiative Leads"]
            elif i == len(phases) - 1:
                phase["responsible_parties"] = ["Implementation Teams", "Executive Leadership"]
            else:
                phase["responsible_parties"] = ["Implementation Teams", "Initiative Leads"]
        
        return phases
    
    def _generate_resource_allocation(
        self,
        available_resources: List[str],
        strategies: List[str],
        implementation_phases: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate resource allocation recommendations.
        
        Args:
            available_resources: List of available resources.
            strategies: Key strategies to implement.
            implementation_phases: Implementation phases.
            
        Returns:
            List of resource allocation recommendations.
        """
        resource_allocation = []
        
        # Identify resource categories from available resources
        resource_categories = {
            "financial": any("capital" in r.lower() or "fund" in r.lower() or "budget" in r.lower() for r in available_resources),
            "human": any("team" in r.lower() or "staff" in r.lower() or "personnel" in r.lower() for r in available_resources),
            "technical": any("tech" in r.lower() or "platform" in r.lower() or "system" in r.lower() for r in available_resources),
            "physical": any("facility" in r.lower() or "equipment" in r.lower() or "asset" in r.lower() for r in available_resources)
        }
        
        # Generate allocation recommendations for each resource category
        if resource_categories["financial"]:
            if len(implementation_phases) > 2:
                resource_allocation.append("Allocate 50% of budget to early phases for foundational capabilities, reserving remaining budget for scaling and optimization phases")
            else:
                resource_allocation.append("Allocate budget proportionally to support critical path activities in each phase")
        
        if resource_categories["human"]:
            resource_allocation.append("Identify required skills and capabilities for each phase and assign resources accordingly")
            resource_allocation.append("Consider external resources for specialized capabilities or capacity constraints")
        
        if resource_categories["technical"]:
            resource_allocation.append("Prioritize technology investments that enable multiple strategic objectives")
            resource_allocation.append("Sequence technical implementations to minimize operational disruption")
        
        if resource_categories["physical"]:
            resource_allocation.append("Optimize utilization of physical assets to support implementation requirements")
        
        # Add general allocation recommendations if needed
        if len(resource_allocation) < 2:
            resource_allocation.append("Conduct resource planning for each phase to identify and address potential constraints")
            resource_allocation.append("Establish resource governance process to manage allocation and monitor utilization")
        
        return resource_allocation
    
    def _identify_risks_and_mitigation(
        self,
        goal_type: str,
        market_constraints: List[str],
        strategies: List[str],
        timeframe_months: int
    ) -> List[str]:
        """
        Identify risks and mitigation strategies.
        
        Args:
            goal_type: Type of business goal.
            market_constraints: List of market constraints.
            strategies: Key strategies to implement.
            timeframe_months: Timeframe in months.
            
        Returns:
            List of risk and mitigation strategy pairs.
        """
        risks_and_mitigation = []
        
        # Identify generic risks based on goal type
        if goal_type == "growth":
            risks_and_mitigation.append("Market response below expectations — Develop phased approach with clear success criteria for each phase")
            risks_and_mitigation.append("Resource constraints limiting growth capacity — Prioritize highest-potential growth initiatives with clear ROI expectations")
            
        elif goal_type == "optimization":
            risks_and_mitigation.append("Operational disruption during implementation — Develop change management plan to minimize business impact")
            risks_and_mitigation.append("Resistance to process changes — Engage stakeholders early and demonstrate clear benefits of changes")
            
        elif goal_type == "innovation":
            risks_and_mitigation.append("Innovation outcomes not meeting market needs — Implement rapid validation approach with customer feedback throughout development")
            risks_and_mitigation.append("Longer-than-expected development cycles — Break initiatives into smaller components with incremental value delivery")
            
        elif goal_type == "transformation":
            risks_and_mitigation.append("Employee resistance to change — Implement comprehensive change management with clear communication and stakeholder engagement")
            risks_and_mitigation.append("Loss of operational focus during transformation — Ensure governance structure maintains focus on core business performance")
        
        # Add timeline-related risks
        if timeframe_months > 12:
            risks_and_mitigation.append("Market conditions changing during implementation — Build flexibility into the plan with regular reassessment points")
            risks_and_mitigation.append("Initiative fatigue for longer duration — Create visible wins throughout the timeline to maintain momentum")
        
        # Add market constraint-related risks
        for constraint in market_constraints:
            if "competition" in constraint.lower() or "competitive" in constraint.lower():
                risks_and_mitigation.append("Competitive response during implementation — Monitor competitive activity closely and prepare contingency plans")
            
            elif "regulation" in constraint.lower() or "legal" in constraint.lower():
                risks_and_mitigation.append("Regulatory changes affecting implementation — Engage compliance expertise early and monitor regulatory developments")
            
            elif "talent" in constraint.lower() or "skill" in constraint.lower():
                risks_and_mitigation.append("Skill gaps limiting implementation capacity — Develop training plan and consider strategic use of external resources")
        
        return risks_and_mitigation
    
    def _generate_detailed_strategy_plan(
        self,
        business_goal: str,
        timeframe: str,
        current_position: str,
        resources_str: str,
        constraints_str: str,
        strategic_objectives: List[str],
        key_strategies: List[str],
        implementation_phases: List[Dict[str, Any]],
        resource_allocation: List[str],
        risks_and_mitigation: List[str]
    ) -> str:
        """
        Generate detailed strategy plan text.
        """
        # Format strategic objectives, key strategies
        objectives_str = "\n".join([f"- {objective}" for objective in strategic_objectives])
        strategies_str = "\n".join([f"- {strategy}" for strategy in key_strategies])
        
        # Format implementation phases
        phases_str = ""
        for phase in implementation_phases:
            activities_str = "\n".join([f"  - {activity}" for activity in phase.get("key_activities", [])])
            metrics_str = "\n".join([f"  - {metric}" for metric in phase.get("success_metrics", [])])
            responsible_str = ", ".join(phase.get("responsible_parties", []))
            
            phases_str += f"""
### {phase['phase']}
**Duration:** {phase['duration']}

**Key Activities:**
{activities_str}

**Success Metrics:**
{metrics_str}

**Responsible:** {responsible_str}
"""
        
        # Format resource allocation
        allocation_str = "\n".join([f"- {allocation}" for allocation in resource_allocation])
        
        # Format risks and mitigation
        risks_str = "\n".join([f"- {risk}" for risk in risks_and_mitigation])
        
        # Create detailed plan markdown
        detailed_plan = f"""
# Strategic Plan: {business_goal}

## Timeframe
{timeframe}

## Current Position
{current_position}

## Available Resources
{resources_str}

## Market Constraints
{constraints_str}

## Strategic Objectives
{objectives_str}

## Strategic Approach
{strategies_str}

## Implementation Plan
{phases_str}

## Resource Allocation
{allocation_str}

## Risk Management
{risks_str}

## Success Criteria
The strategy will be considered successful when the strategic objectives are achieved within the specified timeframe with the allocated resources.
"""
        
        return detailed_plan
    
    # Helper methods for competitive analysis
    
    def _analyze_industry_structure(self, industry: str) -> str:
        """
        Analyze industry structure and dynamics.
        
        Args:
            industry: Industry name.
            
        Returns:
            Industry analysis text.
        """
        normalized_industry = self._normalize_industry(industry)
        
        if normalized_industry == "technology":
            return """The technology industry is characterized by rapid innovation cycles, network effects, and platform dynamics. 
Competition is intense with both established players and disruptive entrants. Success factors include innovation capacity, 
intellectual property, scalability, and speed to market. The industry has relatively low barriers to entry but high barriers to scale."""
        
        elif normalized_industry == "retail":
            return """The retail industry operates in a highly competitive environment with thin margins. The sector is experiencing 
significant disruption from e-commerce and changing consumer behaviors. Success factors include supply chain efficiency, 
customer experience, brand loyalty, and omnichannel capabilities. Scale and operational excellence are critical."""
        
        elif normalized_industry == "manufacturing":
            return """The manufacturing industry is capital intensive with significant economies of scale. Competition is increasingly 
global with pressure on costs and quality. Success factors include operational efficiency, supply chain management, quality control, 
and innovation in both products and processes. Automation and technology integration are reshaping the competitive landscape."""
        
        elif normalized_industry == "healthcare":
            return """The healthcare industry combines complex regulatory requirements with mission-driven service delivery. The sector faces 
pressures from rising costs, technological change, and policy shifts. Success factors include quality outcomes, compliance capabilities, 
operational efficiency, and increasingly, technological integration and data utilization."""
        
        elif normalized_industry == "financial_services":
            return """The financial services industry provides essential economic infrastructure with significant regulatory oversight. 
Traditional players face disruption from fintech innovations and changing customer expectations. Success factors include risk management, 
trust, customer relationships, technological capabilities, and regulatory compliance."""
        
        else:
            return f"""The {industry} industry has specific dynamics that should be analyzed using frameworks such as Porter's Five Forces 
to understand competitive intensity, barriers to entry, supplier and buyer power, and other key factors that shape competitive dynamics."""
    
    def _generate_competitor_profiles(
        self, 
        competitors: List[str], 
        industry: str, 
        criteria: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate competitor profiles with strengths and weaknesses.
        
        Args:
            competitors: List of competitor names.
            industry: Industry name.
            criteria: Evaluation criteria.
            
        Returns:
            List of competitor profile dictionaries.
        """
        import hashlib
        competitor_profiles = []
        
        for competitor in competitors:
            # Use hash of competitor name to generate consistent pseudo-random characteristics
            hash_obj = hashlib.md5(competitor.encode())
            hash_value = int(hash_obj.hexdigest(), 16)
            
            # Generate strengths based on competitor name hash
            strengths = []
            if hash_value % 5 == 0:
                strengths.append("Strong brand recognition and market presence")
            if hash_value % 7 == 0:
                strengths.append("Superior customer experience and service quality")
            if hash_value % 3 == 0:
                strengths.append("Cost-efficient operations and competitive pricing")
            if hash_value % 4 == 0:
                strengths.append("Innovative product/service offerings")
            if hash_value % 6 == 0:
                strengths.append("Extensive distribution network and market reach")
            
            # Ensure at least one strength
            if not strengths:
                strengths.append("Established market position with loyal customer base")
            
            # Generate weaknesses based on competitor name hash
            weaknesses = []
            if hash_value % 5 == 1:
                weaknesses.append("Limited innovation capability and slow adaptation")
            if hash_value % 7 == 1:
                weaknesses.append("Higher cost structure affecting price competitiveness")
            if hash_value % 3 == 1:
                weaknesses.append("Inconsistent customer experience across channels")
            if hash_value % 4 == 1:
                weaknesses.append("Narrow product/service portfolio compared to competitors")
            if hash_value % 6 == 1:
                weaknesses.append("Organizational complexity slowing decision-making")
            
            # Ensure at least one weakness
            if not weaknesses:
                weaknesses.append("Challenges in adapting to changing market conditions")
            
            # Generate market position and strategy based on hash
            market_position = self._generate_competitor_market_position(hash_value, competitor, industry)
            strategy = self._generate_competitor_strategy(hash_value, competitor, industry)
            
            competitor_profiles.append({
                "name": competitor,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "market_position": market_position,
                "strategy": strategy
            })
        
        return competitor_profiles
    
    def _generate_competitor_market_position(self, hash_value: int, competitor: str, industry: str) -> str:
        """
        Generate market position description for a competitor.
        
        Args:
            hash_value: Hash value of competitor name.
            competitor: Competitor name.
            industry: Industry name.
            
        Returns:
            Market position description.
        """
        position_type = hash_value % 4
        normalized_industry = self._normalize_industry(industry)
        
        if position_type == 0:  # Market leader
            if normalized_industry == "technology":
                return f"{competitor} holds a leading market position with significant market share and strong platform/ecosystem advantages."
            elif normalized_industry == "retail":
                return f"{competitor} maintains a dominant market position with extensive retail footprint and strong brand recognition."
            else:
                return f"{competitor} is a market leader with substantial market share and strong competitive positioning."
        
        elif position_type == 1:  # Strong challenger
            if normalized_industry == "technology":
                return f"{competitor} is a strong challenger with growing market share and innovative offerings challenging established players."

            elif normalized_industry == "retail":
                return f"{competitor} is a significant player with strong regional presence and loyal customer base."
            else:
                return f"{competitor} is positioned as a strong challenger with distinctive offerings and growing market influence."

        elif position_type == 2:  # Niche specialist
            if normalized_industry == "technology":
                return f"{competitor} occupies a specialized niche with strong expertise in specific technologies or customer segments."
            elif normalized_industry == "healthcare":
                return f"{competitor} focuses on specialized services with strong reputation in specific treatment areas."
            else:
                return f"{competitor} is a niche specialist with strong position in targeted segments but limited broader presence."

        else:  # Emerging player
            if normalized_industry == "technology":
                return f"{competitor} is an emerging player with disruptive offerings gaining market attention and early customer traction."
            elif normalized_industry == "financial_services":
                return f"{competitor} is a fintech disruptor challenging traditional models with innovative approaches."
            else:
                return f"{competitor} is an emerging competitor with innovative approaches but currently limited market presence."

    def _generate_competitor_strategy(self, hash_value: int, competitor: str, industry: str) -> str:
        """
        Generate strategy description for a competitor.

        Args:
            hash_value: Hash value of competitor name.
            competitor: Competitor name.
            industry: Industry name.

        Returns:
            Strategy description.
        """
        strategy_type = hash_value % 5
        normalized_industry = self._normalize_industry(industry)

        if strategy_type == 0:  # Cost leadership
            return f"{competitor} pursues a cost leadership strategy, focusing on operational efficiency and competitive pricing to drive market share growth."

        elif strategy_type == 1:  # Differentiation
            if normalized_industry == "technology":
                return f"{competitor} employs a differentiation strategy with emphasis on technological innovation and superior product features."
            elif normalized_industry == "retail":
                return f"{competitor} focuses on differentiation through superior customer experience and curated product selection."
            else:
                return f"{competitor} utilizes a differentiation strategy, emphasizing unique value propositions and premium positioning."

        elif strategy_type == 2:  # Focus
            return f"{competitor} applies a focused strategy targeting specific market segments with tailored offerings and specialized expertise."

        elif strategy_type == 3:  # Innovation
            if normalized_industry == "technology":
                return f"{competitor} prioritizes disruptive innovation, continuously introducing new technologies and business models."
            else:
                return f"{competitor} emphasizes innovation as a core strategy, regularly introducing new products and services to drive growth."

        else:  # Hybrid
            return f"{competitor} employs a hybrid strategy combining elements of cost efficiency and differentiation depending on market segment."

    def _assess_competitive_position(
        self,
        company_name: str,
        competitors: List[str],
        industry: str,
        criteria: List[str]
    ) -> Dict[str, Any]:
        """
        Assess company's competitive position relative to competitors.

        Args:
            company_name: Company name.
            competitors: List of competitor names.
            industry: Industry name.
            criteria: Evaluation criteria.

        Returns:
            Dictionary with competitive position assessment.
        """
        # This would normally be based on actual data, but for now we'll generate insights
        normalized_industry = self._normalize_industry(industry)

        # Generate market share assessment
        market_share_assessment = f"Analysis of market share position would require specific market data. A comprehensive competitive analysis should include market share data and trends for {company_name} and key competitors."

        # Generate competitive advantages based on industry
        competitive_advantages = []
        if normalized_industry == "technology":
            competitive_advantages = [
                "Proprietary technology platform creating barriers to entry",
                "Strong innovation pipeline generating continuous competitive differentiation",
                "Scalable business model with decreasing marginal costs"
            ]
        elif normalized_industry == "retail":
            competitive_advantages = [
                "Omnichannel presence providing seamless customer experience",
                "Efficient supply chain reducing costs and improving inventory management",
                "Strong brand loyalty reducing price sensitivity"
            ]
        elif normalized_industry == "manufacturing":
            competitive_advantages = [
                "Operational excellence reducing production costs",
                "Quality control processes ensuring consistent product quality",
                "Supply chain integration creating procurement advantages"
            ]
        elif normalized_industry == "healthcare":
            competitive_advantages = [
                "Specialized expertise in high-value treatment areas",
                "Quality outcomes creating reputation advantage",
                "Integrated care approach improving patient experience"
            ]
        elif normalized_industry == "financial_services":
            competitive_advantages = [
                "Advanced risk management capabilities",
                "Customer trust and loyalty reducing switching",
                "Digital platform enabling cost-efficient service delivery"
            ]
        else:
            competitive_advantages = [
                "Differentiated value proposition addressing specific customer needs",
                "Operational capabilities supporting consistent service delivery",
                "Strategic resources creating sustainable competitive advantage"
            ]

        # Generate competitive disadvantages based on industry
        competitive_disadvantages = []
        if normalized_industry == "technology":
            competitive_disadvantages = [
                "Rapidly evolving technology creating obsolescence risk",
                "Increasing R&D costs to maintain competitive position",
                "Platform dependencies limiting flexibility"
            ]
        elif normalized_industry == "retail":
            competitive_disadvantages = [
                "Physical footprint creating cost structure challenges",
                "Price transparency increasing competitive pressure",
                "Changing consumer preferences requiring continuous adaptation"
            ]
        elif normalized_industry == "manufacturing":
            competitive_disadvantages = [
                "Capital intensity limiting flexibility",
                "Labor cost pressures affecting margins",
                "Raw material price volatility impacting cost predictability"
            ]
        else:
            competitive_disadvantages = [
                "Resource constraints limiting growth capacity",
                "Increasing competitive intensity pressuring margins",
                "Evolving customer expectations requiring continuous adaptation"
            ]

        return {
            "market_share_assessment": market_share_assessment,
            "competitive_advantages": competitive_advantages,
            "competitive_disadvantages": competitive_disadvantages
        }

    def _analyze_market_segments(
        self,
        market_segments: List[str],
        company_name: str,
        competitors: List[str],
        industry: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze company position in different market segments.

        Args:
            market_segments: List of market segments.
            company_name: Company name.
            competitors: List of competitor names.
            industry: Industry name.

        Returns:
            List of segment analysis dictionaries.
        """
        import random
        import hashlib

        segment_analyses = []

        for segment in market_segments:
            # Use hash of segment name to generate consistent pseudo-random characteristics
            hash_obj = hashlib.md5(segment.encode())
            hash_value = int(hash_obj.hexdigest(), 16)

            # Set segment attractiveness based on hash
            attractiveness_type = hash_value % 4
            if attractiveness_type == 0:
                attractiveness = f"High attractiveness with significant growth potential and favorable competitive dynamics."
            elif attractiveness_type == 1:
                attractiveness = f"Moderate attractiveness with stable growth and established competitive structure."
            elif attractiveness_type == 2:
                attractiveness = f"Mixed attractiveness with growth potential but increasing competitive intensity."
            else:
                attractiveness = f"Challenging segment with limited growth and intense price competition."

            # Set competitive position based on hash
            position_type = hash_value % 3
            if position_type == 0:
                position = f"Strong competitive position with established presence and clear differentiation."
            elif position_type == 1:
                position = f"Moderate competitive position with specific strengths but also areas for improvement."
            else:
                position = f"Developing competitive position with opportunities to strengthen market presence."

            # Set growth potential based on hash
            growth_type = hash_value % 3
            if growth_type == 0:
                growth = f"Strong growth potential through increased penetration and share gains."
            elif growth_type == 1:
                growth = f"Moderate growth potential primarily through market expansion."
            else:
                growth = f"Limited organic growth potential requiring innovation or new approaches."

            segment_analyses.append({
                "segment": segment,
                "segment_attractiveness": attractiveness,
                "competitive_position": position,
                "growth_potential": growth
            })

        return segment_analyses

    def _generate_competitive_strategy_recommendations(
        self,
        company_name: str,
        competitors: List[str],
        industry: str,
        competitive_position: Dict[str, Any],
        segment_analysis: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate strategic recommendations based on competitive analysis.

        Args:
            company_name: Company name.
            competitors: List of competitor names.
            industry: Industry name.
            competitive_position: Competitive position assessment.
            segment_analysis: Market segment analysis.

        Returns:
            List of strategic recommendations.
        """
        recommendations = []
        normalized_industry = self._normalize_industry(industry)

        # Leverage competitive advantages
        advantages = competitive_position.get("competitive_advantages", [])
        if advantages:
            for advantage in advantages[:1]:  # Take first advantage for recommendation
                recommendations.append(f"Leverage {advantage.lower()} to strengthen market differentiation and customer value")

        # Address competitive disadvantages
        disadvantages = competitive_position.get("competitive_disadvantages", [])
        if disadvantages:
            for disadvantage in disadvantages[:1]:  # Take first disadvantage for recommendation
                recommendations.append(f"Address {disadvantage.lower()} through targeted initiatives and strategic investments")

        # Segment-specific recommendations
        high_potential_segments = []
        for segment in segment_analysis:
            if "strong" in segment.get("growth_potential", "").lower() or "high" in segment.get("segment_attractiveness", "").lower():
                high_potential_segments.append(segment.get("segment"))

        if high_potential_segments:
            segment_list = ", ".join(high_potential_segments)
            recommendations.append(f"Prioritize resources for high-potential segments: {segment_list}")

        # Industry-specific recommendations
        if normalized_industry == "technology":
            recommendations.append("Accelerate innovation pipeline to maintain competitive differentiation in rapidly evolving market")
        elif normalized_industry == "retail":
            recommendations.append("Enhance omnichannel integration to provide seamless customer experience across touchpoints")
        elif normalized_industry == "manufacturing":
            recommendations.append("Optimize operations and supply chain to improve cost position while maintaining quality standards")
        elif normalized_industry == "healthcare":
            recommendations.append("Focus on quality outcomes and patient experience to strengthen reputation and referral networks")
        elif normalized_industry == "financial_services":
            recommendations.append("Invest in digital capabilities to improve customer experience and operational efficiency")

        # General recommendations
        if len(recommendations) < 3:
            recommendations.append("Develop clear value proposition emphasizing unique strengths and customer benefits")
            recommendations.append("Establish systematic competitive intelligence to monitor market dynamics and competitor activities")

        return recommendations

    def _generate_detailed_competitive_analysis(
        self,
        company_name: str,
        industry: str,
        competitors_str: str,
        segments_str: str,
        criteria_str: str,
        industry_analysis: str,
        competitor_profiles: List[Dict[str, Any]],
        competitive_position: Dict[str, Any],
        segment_analysis: List[Dict[str, Any]],
        strategic_recommendations: List[str]
    ) -> str:
        """
        Generate detailed competitive analysis text.
        """
        # Format competitor profiles
        competitor_profiles_str = ""
        for profile in competitor_profiles:
            strengths_str = "\n".join([f"  - {strength}" for strength in profile.get("strengths", [])])
            weaknesses_str = "\n".join([f"  - {weakness}" for weakness in profile.get("weaknesses", [])])

            competitor_profiles_str += f"""
### {profile['name']}
**Market Position:** {profile.get('market_position', 'Not assessed')}

**Strategy:** {profile.get('strategy', 'Not assessed')}

**Strengths:**
{strengths_str}

**Weaknesses:**
{weaknesses_str}
"""

        # Format competitive position
        advantages_str = "\n".join([f"- {advantage}" for advantage in competitive_position.get("competitive_advantages", [])])
        disadvantages_str = "\n".join([f"- {disadvantage}" for disadvantage in competitive_position.get("competitive_disadvantages", [])])

        # Format segment analysis
        segment_analysis_str = ""
        for segment in segment_analysis:
            segment_analysis_str += f"""
### {segment['segment']}
**Attractiveness:** {segment.get('segment_attractiveness', 'Not assessed')}

**Competitive Position:** {segment.get('competitive_position', 'Not assessed')}

**Growth Potential:** {segment.get('growth_potential', 'Not assessed')}
"""

        # Format strategic recommendations
        recommendations_str = "\n".join([f"- {recommendation}" for recommendation in strategic_recommendations])

        # Create detailed analysis markdown
        detailed_analysis = f"""
# Competitive Analysis: {company_name} in {industry}

## Industry Overview
{industry_analysis}

## Competitor Profiles
{competitor_profiles_str}

## Competitive Position
**Market Share Assessment:**
{competitive_position.get('market_share_assessment', 'Not assessed')}

**Competitive Advantages:**
{advantages_str}

**Competitive Disadvantages:**
{disadvantages_str}

## Segment Analysis
{segment_analysis_str}

## Strategic Recommendations
{recommendations_str}

## Methodology Note
This competitive analysis is based on available information and would be enhanced by primary research including customer interviews, detailed market data, and comprehensive competitor intelligence.
"""

        return detailed_analysis

    # Helper methods for implementation planning

    def _categorize_initiative(self, initiative: str) -> str:
        """
        Categorize the type of strategic initiative.

        Args:
            initiative: Initiative description.

        Returns:
            Initiative type.
        """
        initiative_lower = initiative.lower()

        if any(term in initiative_lower for term in ["grow", "expan", "scale", "new market"]):
            return "growth"
        elif any(term in initiative_lower for term in ["cost", "efficien", "optimi", "productiv"]):
            return "optimization"
        elif any(term in initiative_lower for term in ["launch", "new product", "innovat"]):
            return "product_launch"
        elif any(term in initiative_lower for term in ["digital", "technolog", "automat", "platform"]):
            return "digital_transformation"
        elif any(term in initiative_lower for term in ["restructur", "reorganiz"]):
            return "restructuring"
        elif any(term in initiative_lower for term in ["merger", "acqui", "integration"]):
            return "m_and_a"
        else:
            return "strategic_initiative"

    def _generate_default_risk_factors(self, initiative: str) -> List[str]:
        """
        Generate default risk factors based on initiative description.

        Args:
            initiative: Initiative description.

        Returns:
            List of risk factors.
        """
        # Categorize initiative
        initiative_type = self._categorize_initiative(initiative)

        # Generate appropriate risk factors
        if initiative_type == "growth":
            return [
                "Market penetration slower than projected",
                "Operational capacity constraints limiting growth",
                "Competitive response affecting market access"
            ]
        elif initiative_type == "optimization":
            return [
                "Process changes disrupting ongoing operations",
                "Employee resistance to new processes or tools",
                "Cost savings taking longer than expected to realize"
            ]
        elif initiative_type == "product_launch":
            return [
                "Product development delays affecting launch timeline",
                "Market acceptance below expectations",
                "Technical issues affecting product performance"
            ]
        elif initiative_type == "digital_transformation":
            return [
                "Technical complexity extending implementation timeline",
                "Integration challenges with existing systems",
                "User adoption challenges affecting realization of benefits"
            ]
        elif initiative_type == "restructuring":
            return [
                "Employee morale and productivity impacts",
                "Loss of key talent during transition",
                "Disruption to customer relationships during reorganization"
            ]
        elif initiative_type == "m_and_a":
            return [
                "Integration challenges affecting expected synergies",
                "Cultural alignment issues between organizations",
                "Key talent retention during integration"
            ]
        else:
            return [
                "Resource constraints affecting implementation",
                "Timeline delays due to unforeseen challenges",
                "Stakeholder resistance to change"
            ]

    def _generate_implementation_phases_for_initiative(
        self,
        initiative_type: str,
        months: int,
        objectives: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate implementation phases based on initiative type and timeline.

        Args:
            initiative_type: Type of initiative.
            months: Timeline in months.
            objectives: List of initiative objectives.

        Returns:
            List of implementation phase dictionaries.
        """
        # Determine number and duration of phases based on timeframe and initiative type
        if months <= 3:
            # Short timeframe - simplified phases
            if initiative_type in ["product_launch", "growth"]:
                phases = [
                    {"phase": "Phase 1: Preparation", "duration": f"{months // 2} months"},
                    {"phase": "Phase 2: Launch", "duration": f"{months - (months // 2)} months"}
                ]
            else:
                phases = [{"phase": "Implementation", "duration": f"{months} months"}]
        elif months <= 6:
            # Medium timeframe - standard phases
            if initiative_type == "product_launch":
                phases = [
                    {"phase": "Phase 1: Planning & Design", "duration": f"{months // 3} months"},
                    {"phase": "Phase 2: Development & Testing", "duration": f"{months // 3} months"},
                    {"phase": "Phase 3: Launch & Scaling", "duration": f"{months - 2 * (months // 3)} months"}
                ]
            elif initiative_type == "digital_transformation":
                phases = [
                    {"phase": "Phase 1: Assessment & Planning", "duration": f"{months // 3} months"},
                    {"phase": "Phase 2: Implementation", "duration": f"{months // 2} months"},
                    {"phase": "Phase 3: Adoption & Optimization", "duration": f"{months - (months // 3) - (months // 2)} months"}
                ]
            else:
                phases = [
                    {"phase": "Phase 1: Preparation", "duration": f"{months // 3} months"},
                    {"phase": "Phase 2: Implementation", "duration": f"{months // 2} months"},
                    {"phase": "Phase 3: Evaluation & Refinement", "duration": f"{months - (months // 3) - (months // 2)} months"}
                ]
        else:
            # Longer timeframe - comprehensive phases
            if initiative_type == "product_launch":
                phases = [
                    {"phase": "Phase 1: Market Research & Planning", "duration": f"{months // 5} months"},
                    {"phase": "Phase 2: Product Design & Development", "duration": f"{months // 3} months"},
                    {"phase": "Phase 3: Testing & Refinement", "duration": f"{months // 4} months"},
                    {"phase": "Phase 4: Market Launch", "duration": f"{months // 6} months"},
                    {"phase": "Phase 5: Scaling & Optimization", "duration": f"{months - (months // 5) - (months // 3) - (months // 4) - (months // 6)} months"}
                ]
            elif initiative_type == "digital_transformation":
                phases = [
                    {"phase": "Phase 1: Assessment & Strategy", "duration": f"{months // 6} months"},
                    {"phase": "Phase 2: Platform Development", "duration": f"{months // 3} months"},
                    {"phase": "Phase 3: Initial Deployment", "duration": f"{months // 4} months"},
                    {"phase": "Phase 4: Enterprise Rollout", "duration": f"{months // 3} months"},
                    {"phase": "Phase 5: Optimization & Innovation", "duration": f"{months - (months // 6) - (months // 3) - (months // 4) - (months // 3)} months"}
                ]
            elif initiative_type == "m_and_a":
                phases = [
                    {"phase": "Phase 1: Due Diligence & Planning", "duration": f"{months // 5} months"},
                    {"phase": "Phase 2: Day 1 Readiness", "duration": f"{months // 8} months"},
                    {"phase": "Phase 3: Initial Integration", "duration": f"{months // 4} months"},
                    {"phase": "Phase 4: Full Integration", "duration": f"{months // 2} months"},
                    {"phase": "Phase 5: Synergy Realization", "duration": f"{months - (months // 5) - (months // 8) - (months // 4) - (months // 2)} months"}
                ]
            else:
                phases = [
                    {"phase": "Phase 1: Analysis & Planning", "duration": f"{months // 5} months"},
                    {"phase": "Phase 2: Initial Implementation", "duration": f"{months // 3} months"},
                    {"phase": "Phase 3: Full Implementation", "duration": f"{months // 2} months"},
                    {"phase": "Phase 4: Evaluation & Optimization", "duration": f"{months - (months // 5) - (months // 3) - (months // 2)} months"}
                ]

        # Generate tasks for each phase
        for i, phase in enumerate(phases):
            phase["key_tasks"] = self._generate_tasks_for_phase(phase["phase"], initiative_type, i, len(phases))
            phase["deliverables"] = self._generate_deliverables_for_phase(phase["phase"], initiative_type, i, len(phases))
            phase["responsible_parties"] = self._generate_responsible_parties_for_phase(phase["phase"], initiative_type)

        return phases

    def _generate_tasks_for_phase(
        self,
        phase_name: str,
        initiative_type: str,
        phase_index: int,
        total_phases: int
    ) -> List[str]:
        """
        Generate tasks for implementation phase.

        Args:
            phase_name: Name of the phase.
            initiative_type: Type of initiative.
            phase_index: Index of the phase.
            total_phases: Total number of phases.

        Returns:
            List of tasks.
        """
        # Early phase tasks (planning, preparation)
        if "Planning" in phase_name or "Preparation" in phase_name or "Assessment" in phase_name or phase_index == 0:
            if initiative_type == "product_launch":
                return [
                    "Conduct market research to validate customer needs and requirements",
                    "Define product features, specifications, and success criteria",
                    "Develop detailed project plan with timeline and resource requirements",
                    "Establish governance structure and decision-making framework"
                ]
            elif initiative_type == "digital_transformation":
                return [
                    "Conduct current state assessment of systems, processes, and capabilities",
                    "Define future state vision and requirements",
                    "Develop technology roadmap and implementation approach",
                    "Establish governance structure and change management framework"
                ]
            elif initiative_type == "m_and_a":
                return [
                    "Conduct due diligence across functional areas",
                    "Develop integration strategy and approach",
                    "Identify key risks and develop mitigation strategies",
                    "Establish integration governance structure and decision framework"
                ]
            else:
                return [
                    "Define detailed initiative scope and objectives",
                    "Develop implementation plan with timeline and milestones",
                    "Identify resource requirements and secure commitments",
                    "Establish governance structure and decision-making framework"
                ]

        # Middle phase tasks (implementation, development)
        elif "Implementation" in phase_name or "Development" in phase_name or phase_index < total_phases - 1:
            if initiative_type == "product_launch":
                return [
                    "Develop product according to specifications",
                    "Conduct internal testing and quality assurance",
                    "Prepare go-to-market materials and launch plan",
                    "Develop training materials for sales and support teams"
                ]
            elif initiative_type == "digital_transformation":
                return [
                    "Develop/configure technology solutions according to requirements",
                    "Integrate with existing systems and data sources",
                    "Conduct testing and validation of functionality",
                    "Develop training materials and user documentation"
                ]
            elif initiative_type == "optimization":
                return [
                    "Implement process changes according to design",
                    "Deploy supporting tools and technologies",
                    "Train teams on new processes and tools",
                    "Monitor initial implementation and address issues"
                ]
            elif initiative_type == "m_and_a":
                return [
                    "Integrate key systems and processes",
                    "Harmonize policies and procedures",
                    "Implement organizational structure changes",
                    "Execute communication plan for internal and external stakeholders"
                ]
            else:
                return [
                    "Execute implementation activities according to plan",
                    "Monitor progress against milestones and address issues",
                    "Communicate progress to stakeholders",
                    "Document learnings and update approach as needed"
                ]

        # Final phase tasks (evaluation, scaling, optimization)
        else:
            if initiative_type == "product_launch":
                return [
                    "Monitor market response and customer feedback",
                    "Implement product enhancements based on initial feedback",
                    "Scale marketing and sales activities based on response",
                    "Develop roadmap for future product iterations"
                ]
            elif initiative_type == "digital_transformation":
                return [
                    "Monitor system performance and user adoption",
                    "Collect and analyze feedback for enhancements",
                    "Implement refinements to improve functionality and user experience",
                    "Document learnings and best practices for future initiatives"
                ]
            else:
                return [
                    "Evaluate results against initiative objectives",
                    "Identify and address any performance gaps",
                    "Document learnings and best practices",
                    "Develop approach for sustaining changes and continuous improvement"
                ]

    def _generate_deliverables_for_phase(
        self,
        phase_name: str,
        initiative_type: str,
        phase_index: int,
        total_phases: int
    ) -> List[str]:
        """
        Generate deliverables for implementation phase.

        Args:
            phase_name: Name of the phase.
            initiative_type: Type of initiative.
            phase_index: Index of the phase.
            total_phases: Total number of phases.

        Returns:
            List of deliverables.
        """
        # Early phase deliverables
        if "Planning" in phase_name or "Preparation" in phase_name or "Assessment" in phase_name or phase_index == 0:
            if initiative_type == "product_launch":
                return [
                    "Market analysis and customer requirements document",
                    "Product specifications and development plan",
                    "Project plan with timeline and resource allocations"
                ]
            elif initiative_type == "digital_transformation":
                return [
                    "Current state assessment report",
                    "Future state design and requirements document",
                    "Implementation roadmap and approach document"
                ]
            else:
                return [
                    "Detailed implementation plan",
                    "Resource and budget allocation plan",
                    "Governance framework document"
                ]

        # Middle phase deliverables
        elif "Implementation" in phase_name or "Development" in phase_name or phase_index < total_phases - 1:
            if initiative_type == "product_launch":
                return [
                    "Product prototype or beta version",
                    "Testing results and quality assurance report",
                    "Go-to-market plan and marketing materials"
                ]
            elif initiative_type == "digital_transformation":
                return [
                    "Configured system components or platforms",
                    "Integration and testing documentation",
                    "Training materials and user guides"
                ]
            else:
                return [
                    "Implemented solution components",
                    "Progress reports against milestones",
                    "Updated implementation plan based on learnings"
                ]

        # Final phase deliverables
        else:
            if initiative_type == "product_launch":
                return [
                    "Launched product",
                    "Customer feedback analysis",
                    "Roadmap for enhancements and future development"
                ]
            elif initiative_type == "digital_transformation":
                return [
                    "Fully deployed platform or system",
                    "Adoption metrics and analysis",
                    "Enhancement roadmap based on user feedback"
                ]
            else:
                return [
                    "Results analysis and performance report",
                    "Lessons learned documentation",
                    "Sustainability and continuous improvement plan"
                ]

    def _generate_responsible_parties_for_phase(
        self,
        phase_name: str,
        initiative_type: str
    ) -> List[str]:
        """
        Generate responsible parties for implementation phase.

        Args:
            phase_name: Name of the phase.
            initiative_type: Type of initiative.

        Returns:
            List of responsible parties.
        """
        # Generate responsible parties based on initiative type and phase
        if "Planning" in phase_name or "Preparation" in phase_name or "Assessment" in phase_name:
            if initiative_type == "product_launch":
                return ["Product Management", "R&D Leadership", "Marketing Leadership"]
            elif initiative_type == "digital_transformation":
                return ["IT Leadership", "Business Stakeholders", "Transformation Office"]
            elif initiative_type == "m_and_a":
                return ["Executive Leadership", "Integration Management Office", "Functional Leads"]
            else:
                return ["Initiative Sponsor", "Project Management", "Key Stakeholders"]

        elif "Development" in phase_name or "Implementation" in phase_name:
            if initiative_type == "product_launch":
                return ["R&D Team", "Product Management", "Quality Assurance"]
            elif initiative_type == "digital_transformation":
                return ["IT Implementation Team", "Business Process Owners", "Change Management Team"]
            elif initiative_type == "m_and_a":
                return ["Integration Teams", "Functional Leads", "Integration Management Office"]
            else:
                return ["Implementation Team", "Project Management", "Business Stakeholders"]

        elif "Launch" in phase_name:
            if initiative_type == "product_launch":
                return ["Marketing Team", "Sales Team", "Product Management", "Customer Support"]
            else:
                return ["Implementation Team", "Communications Team", "Key Stakeholders"]

        elif "Evaluation" in phase_name or "Optimization" in phase_name:
            return ["Project Management", "Business Stakeholders", "Implementation Team"]

        else:
            return ["Project Team", "Key Stakeholders"]

    def _generate_stakeholder_management_strategies(
        self,
        stakeholders: List[str],
        initiative_type: str
    ) -> List[Dict[str, str]]:
        """
        Generate stakeholder management strategies.

        Args:
            stakeholders: List of stakeholder names/groups.
            initiative_type: Type of initiative.

        Returns:
            List of stakeholder management strategy dictionaries.
        """
        stakeholder_strategies = []

        for stakeholder in stakeholders:
            # Determine stakeholder type/category
            stakeholder_lower = stakeholder.lower()

            if any(term in stakeholder_lower for term in ["executive", "ceo", "cfo", "cio", "cto", "board", "director"]):
                stakeholder_type = "executive"
            elif any(term in stakeholder_lower for term in ["manager", "head", "lead", "supervisor"]):
                stakeholder_type = "manager"
            elif any(term in stakeholder_lower for term in ["employee", "staff", "team", "personnel"]):
                stakeholder_type = "employee"
            elif any(term in stakeholder_lower for term in ["customer", "client", "user", "patient"]):
                stakeholder_type = "customer"
            elif any(term in stakeholder_lower for term in ["vendor", "supplier", "partner"]):
                stakeholder_type = "partner"
            else:
                stakeholder_type = "general"

            # Generate communication strategy based on stakeholder type
            if stakeholder_type == "executive":
                communication = "Regular executive briefings focused on strategic impact, ROI, and key milestones"
            elif stakeholder_type == "manager":
                communication = "Detailed status updates on progress, issues, and resource utilization with emphasis on operational impacts"
            elif stakeholder_type == "employee":
                communication = "Clear communication on changes, impacts to roles and responsibilities, and training opportunities"
            elif stakeholder_type == "customer":
                communication = "Targeted communication on value proposition, timing, and any potential service impacts during implementation"
            elif stakeholder_type == "partner":
                communication = "Proactive updates on changes affecting partnerships, integration requirements, and timeline implications"
            else:
                communication = "Regular updates tailored to stakeholder's specific interests and involvement"

            # Generate engagement approach based on stakeholder type and initiative
            if stakeholder_type == "executive":
                if initiative_type in ["digital_transformation", "restructuring", "m_and_a"]:
                    engagement = "Involve in key strategic decisions and governance oversight with regular steering committee participation"
                else:
                    engagement = "Engage through governance processes with focus on strategic alignment and resource allocation decisions"

            elif stakeholder_type == "manager":
                if initiative_type in ["optimization", "restructuring"]:
                    engagement = "Actively involve in process design and implementation planning to leverage operational expertise and ensure buy-in"
                else:
                    engagement = "Engage as functional representatives to provide domain expertise and manage team implementation activities"

            elif stakeholder_type == "employee":
                engagement = "Involve select representatives in working groups to provide input and serve as change champions within their teams"

            elif stakeholder_type == "customer":
                if initiative_type == "product_launch":
                    engagement = "Engage select customers in beta testing and feedback processes to refine offering"
                else:
                    engagement = "Collect feedback on current pain points and validate proposed solutions through customer research activities"

            elif stakeholder_type == "partner":
                engagement = "Collaborate on integration requirements and timeline coordination to ensure alignment"

            else:
                engagement = "Tailor engagement based on influence and interest levels with appropriate involvement in relevant activities"

            stakeholder_strategies.append({
                "stakeholder_group": stakeholder,
                "stakeholder_type": stakeholder_type,
                "communication_strategy": communication,
                "engagement_approach": engagement
            })

        return stakeholder_strategies

    def _generate_risk_management_strategies(
        self,
        risk_factors: List[str],
        initiative_type: str,
        timeframe_months: int
    ) -> List[Dict[str, str]]:
        """
        Generate risk management strategies.

        Args:
            risk_factors: List of risk factors.
            initiative_type: Type of initiative.
            timeframe_months: Timeframe in months.

        Returns:
            List of risk management strategy dictionaries.
        """
        risk_strategies = []

        for risk in risk_factors:
            # Analyze risk characteristics
            risk_lower = risk.lower()

            # Determine risk likelihood
            if "typically" in risk_lower or "common" in risk_lower or "frequently" in risk_lower:
                likelihood = "High"
            elif "possible" in risk_lower or "potential" in risk_lower or "may" in risk_lower:
                likelihood = "Medium"
            else:
                # Determine based on initiative type and timeframe
                if initiative_type in ["digital_transformation", "m_and_a"] and "integration" in risk_lower:
                    likelihood = "High"
                elif initiative_type == "product_launch" and "delay" in risk_lower:
                    likelihood = "Medium-High"
                elif timeframe_months > 12 and "change" in risk_lower:
                    likelihood = "Medium-High"
                else:
                    likelihood = "Medium"

            # Determine risk impact
            if any(term in risk_lower for term in ["significant", "major", "critical", "substantial"]):
                impact = "High"
            elif any(term in risk_lower for term in ["moderate", "important"]):
                impact = "Medium"
            else:
                # Determine based on risk content
                if "cost" in risk_lower or "budget" in risk_lower:
                    impact = "Medium-High"
                elif "delay" in risk_lower or "timeline" in risk_lower:
                    impact = "Medium"
                elif "quality" in risk_lower or "performance" in risk_lower:
                    impact = "High"
                else:
                    impact = "Medium"

            # Generate appropriate mitigation strategy
            if "resource" in risk_lower or "capacity" in risk_lower:
                mitigation = "Develop detailed resource plan with contingency options and regular capacity reviews"
            elif "delay" in risk_lower or "timeline" in risk_lower:
                mitigation = "Implement robust project management with buffer periods and critical path monitoring"
            elif "resistance" in risk_lower or "adoption" in risk_lower:
                mitigation = "Develop comprehensive change management plan with stakeholder engagement and clear communication of benefits"
            elif "technical" in risk_lower or "integration" in risk_lower:
                mitigation = "Conduct technical proof of concept early and implement phased approach with quality gates"
            elif "market" in risk_lower or "customer" in risk_lower:
                mitigation = "Validate with customer research pre-launch and prepare contingency plans for different market response scenarios"
            elif "cost" in risk_lower or "budget" in risk_lower:
                mitigation = "Implement rigorous cost tracking and establish clear thresholds for escalation and remediation"
            else:
                mitigation = "Develop detailed risk response plan with clear ownership and monitoring mechanisms"

            risk_strategies.append({
                "risk": risk,
                "likelihood": likelihood,
                "impact": impact,
                "mitigation_strategy": mitigation
            })

        return risk_strategies

    def _generate_success_criteria(
        self,
        objectives: List[str],
        initiative_type: str,
        timeframe_months: int
    ) -> List[str]:
        """
        Generate success criteria for the initiative.

        Args:
            objectives: List of initiative objectives.
            initiative_type: Type of initiative.
            timeframe_months: Timeframe in months.

        Returns:
            List of success criteria.
        """
        criteria = []

        # Generate criteria based on objectives
        for objective in objectives:
            objective_lower = objective.lower()

            if "revenue" in objective_lower or "sales" in objective_lower:
                criteria.append("Achievement of revenue targets defined in project business case")
            elif "cost" in objective_lower or "efficien" in objective_lower:
                criteria.append("Realization of cost savings or efficiency improvements as specified in business case")
            elif "customer" in objective_lower or "satisfaction" in objective_lower:
                criteria.append("Improvement in customer satisfaction metrics in target segments")
            elif "quality" in objective_lower or "defect" in objective_lower:
                criteria.append("Achievement of quality targets with defect rates below defined thresholds")
            elif "process" in objective_lower or "cycle time" in objective_lower:
                criteria.append("Process performance improvements meeting or exceeding target metrics")

        # Add initiative-specific criteria
        if initiative_type == "product_launch":
            criteria.append("Product launched within defined timeline and budget constraints")
            criteria.append("Market adoption metrics meeting or exceeding targets for first three months")
            criteria.append("Customer feedback meeting quality and satisfaction thresholds")

        elif initiative_type == "optimization":
            criteria.append("Implementation of process changes with minimal operational disruption")
            criteria.append("Performance metrics demonstrating expected efficiency improvements")
            criteria.append("Positive feedback from process users and stakeholders")

        elif initiative_type == "digital_transformation":
            criteria.append("System implementation meeting functional and technical requirements")
            criteria.append("User adoption meeting or exceeding target levels")
            criteria.append("Business process metrics showing expected improvements")

        elif initiative_type == "m_and_a":
            criteria.append("Integration executed within timeline and budget parameters")
            criteria.append("Synergy targets achieved as defined in integration business case")
            criteria.append("Minimal business disruption during integration process")

        # Add general criteria
        if len(criteria) < 3:
            criteria.append("Implementation completed within timeline and budget constraints")
            criteria.append("Initiative objectives achieved as measured by defined KPIs")
            criteria.append("Stakeholder feedback indicates satisfaction with implementation and outcomes")

        return criteria

    def _generate_detailed_implementation_plan(
        self,
        strategic_initiative: str,
        timeline: str,
        objectives_str: str,
        stakeholders_str: str,
        risks_str: str,
        implementation_phases: List[Dict[str, Any]],
        stakeholder_management: List[Dict[str, str]],
        risk_management: List[Dict[str, str]],
        success_criteria: List[str]
    ) -> str:
        """
        Generate detailed implementation plan text.
        """
        # Format success criteria
        criteria_str = "\n".join([f"- {criterion}" for criterion in success_criteria])

        # Format implementation phases
        phases_str = ""
        for phase in implementation_phases:
            tasks_str = "\n".join([f"  - {task}" for task in phase.get("key_tasks", [])])
            deliverables_str = "\n".join([f"  - {deliverable}" for deliverable in phase.get("deliverables", [])])
            responsible_str = ", ".join(phase.get("responsible_parties", []))

            phases_str += f"""
### {phase['phase']}
**Duration:** {phase['duration']}

**Key Tasks:**
{tasks_str}

**Deliverables:**
{deliverables_str}

**Responsible:** {responsible_str}
"""

        # Format stakeholder management
        stakeholder_str = ""
        for stakeholder in stakeholder_management:
            stakeholder_str += f"""
### {stakeholder['stakeholder_group']}
**Communication Strategy:** {stakeholder['communication_strategy']}

**Engagement Approach:** {stakeholder['engagement_approach']}
"""

        # Format risk management
        risk_mgmt_str = ""
        for risk in risk_management:
            risk_mgmt_str += f"""
### {risk['risk']}
**Likelihood:** {risk['likelihood']}

**Impact:** {risk['impact']}

**Mitigation Strategy:** {risk['mitigation_strategy']}
"""

        # Create detailed plan markdown
        detailed_plan = f"""
# Implementation Plan: {strategic_initiative}

## Timeline Overview
{timeline}

## Key Objectives
{objectives_str}

## Key Stakeholders
{stakeholders_str}

## Risk Factors
{risks_str}

## Implementation Approach
This implementation plan follows a structured approach with clear phases, responsibilities, and success criteria.
The plan addresses potential risks and includes stakeholder management strategies to maximize likelihood of success.

## Implementation Phases
{phases_str}

## Stakeholder Management
{stakeholder_str}

## Risk Management
{risk_mgmt_str}

## Success Criteria
{criteria_str}

## Monitoring and Evaluation
Implementation progress will be monitored against defined milestones and success criteria.
Regular status reviews will assess progress, identify issues, and implement corrective actions as needed.
A formal evaluation will be conducted at implementation completion to assess outcomes and document learnings.
"""

        return detailed_plan

    # Helper methods for financial analysis

    def _interpret_profit_margin(self, margin: float) -> str:
        """
        Provide interpretation of profit margin value.

        Args:
            margin: Profit margin percentage.

        Returns:
            Interpretation text.
        """
        if margin <= 0:
            return "The business is operating at a loss. Immediate action recommended to reduce costs or increase revenue."
        elif margin < 5:
            return "Very low profit margin indicating significant profitability challenges. Comprehensive profit improvement plan needed."
        elif margin < 10:
            return "Below average profit margin. Focused initiatives needed to improve pricing strategy, reduce costs, or optimize product mix."
        elif margin < 15:
            return "Moderate profit margin in line with many industries. Continue monitoring while seeking incremental improvements in efficiency and pricing."
        elif margin < 25:
            return "Healthy profit margin indicating good financial performance. Focus on maintaining competitive advantage and exploring growth opportunities."
        else:
            return "Excellent profit margin significantly above average. Maintain pricing power and cost discipline while potentially investing in growth initiatives."

    def _assess_profit_margin_compared_to_benchmark(self, margin: float, benchmark: float) -> str:
        """
        Assess profit margin compared to industry benchmark.

        Args:
            margin: Actual profit margin percentage.
            benchmark: Benchmark profit margin percentage.

        Returns:
            Assessment text.
        """
        difference = margin - benchmark
        percent_difference = (difference / benchmark) * 100 if benchmark > 0 else 0

        if difference >= 5:
            return f"Exceptional performance with profit margin {difference:.1f} percentage points ({percent_difference:.1f}%) above industry benchmark. Indicates sustainable competitive advantage."
        elif difference >= 2:
            return f"Strong performance with profit margin {difference:.1f} percentage points ({percent_difference:.1f}%) above industry benchmark. Well-positioned versus competitors."
        elif difference >= -2:
            return f"Average performance with profit margin near industry benchmark (difference of {difference:.1f} percentage points). Maintaining competitive parity."
        elif difference >= -5:
            return f"Below average performance with profit margin {-difference:.1f} percentage points below industry benchmark. Improvements needed to remain competitive."
        else:
            return f"Significant underperformance with profit margin {-difference:.1f} percentage points below industry benchmark. Urgent profit improvement initiatives required."

    def _assess_growth_rate(self, growth_rate: float) -> str:
        """
        Assess revenue growth rate.

        Args:
            growth_rate: Revenue growth rate percentage.

        Returns:
            Assessment text.
        """
        if growth_rate <= -10:
            return "Severe revenue decline indicating significant business challenges. Urgent action required to stabilize and reverse trend."
        elif growth_rate < 0:
            return "Revenue contraction indicating potential market challenges or internal issues. Detailed analysis needed to identify and address causes."
        elif growth_rate < 3:
            return "Minimal growth below inflation rate, representing effective contraction in real terms. Revenue growth initiatives should be prioritized."
        elif growth_rate < 8:
            return "Moderate growth indicating stable business performance. Continued focus on growth initiatives recommended to improve trajectory."
        elif growth_rate < 15:
            return "Strong growth significantly outpacing inflation and likely gaining market share. Continue successful growth strategies."
        else:
            return "Exceptional growth rate indicating successful market positioning or expansion. Ensure operational capacity to sustain growth trajectory."

    def _assess_growth_rate_compared_to_benchmark(self, growth_rate: float, benchmark: float) -> str:
        """
        Assess growth rate compared to industry benchmark.

        Args:
            growth_rate: Actual growth rate percentage.
            benchmark: Benchmark growth rate percentage.

        Returns:
            Assessment text.
        """
        difference = growth_rate - benchmark

        if difference >= 5:
            return f"Exceptional growth outperforming industry by {difference:.1f} percentage points. Indicates market share gains and/or successful entry into new markets."
        elif difference >= 2:
            return f"Above average growth exceeding industry benchmark by {difference:.1f} percentage points. Successfully outperforming the market."
        elif difference >= -2:
            return f"Growth in line with industry benchmark (difference of {difference:.1f} percentage points). Maintaining competitive position."
        elif difference >= -5:
            return f"Below average growth lagging industry benchmark by {-difference:.1f} percentage points. Risk of market share erosion if trend continues."
        else:
            return f"Significant growth underperformance of {-difference:.1f} percentage points below industry. Urgent growth initiatives needed to remain competitive."

    def _assess_efficiency_trend(self, revenue_growth: float, cost_growth: float) -> str:
        """
        Assess operational efficiency trend based on revenue vs. cost growth.

        Args:
            revenue_growth: Revenue growth rate percentage.
            cost_growth: Cost growth rate percentage.

        Returns:
            Assessment text.
        """
        difference = revenue_growth - cost_growth

        if difference >= 5:
            return "Excellent efficiency trend with revenue growing significantly faster than costs, driving margin expansion and operational leverage."
        elif difference >= 2:
            return "Positive efficiency trend with revenue growth outpacing cost growth, indicating improving operational efficiency."
        elif difference >= -2:
            return "Stable efficiency with revenue and cost growth roughly aligned. Maintaining operational performance but not generating leverage."
        elif difference >= -5:
            return "Negative efficiency trend with costs growing faster than revenue, creating margin pressure. Efficiency initiatives should be prioritized."
        else:
            return "Severe efficiency deterioration with cost growth substantially exceeding revenue growth. Urgent cost control measures required."

    def _assess_unit_economics(
        self,
        revenue_per_unit: float,
        cost_per_unit: float,
        profit_per_unit: float,
        industry: Optional[str] = None
    ) -> str:
        """
        Assess unit economics performance.

        Args:
            revenue_per_unit: Revenue per unit sold.
            cost_per_unit: Cost per unit sold.
            profit_per_unit: Profit per unit sold.
            industry: Optional industry for context.

        Returns:
            Assessment text.
        """
        margin_percentage = (profit_per_unit / revenue_per_unit) * 100 if revenue_per_unit > 0 else 0

        if margin_percentage <= 0:
            return "Negative unit economics indicating fundamental business model challenges. Each additional sale increases losses."
        elif margin_percentage < 10:
            return "Thin unit margins creating vulnerability to volume fluctuations and pricing pressure. Improving unit economics should be prioritized."
        elif margin_percentage < 25:
            return "Adequate unit economics providing positive contribution to fixed costs and profit. Continue monitoring for optimization opportunities."
        elif margin_percentage < 50:
            return "Strong unit economics indicating efficient value delivery and pricing power. Provides solid foundation for profitability and growth."
        else:
            return "Exceptional unit economics with very high contribution margin. Indicates premium positioning and strong value proposition."

    def _assess_marketing_spend(self, marketing_percentage: float, benchmark: float) -> str:
        """
        Assess marketing spend as percentage of revenue.

        Args:
            marketing_percentage: Marketing spend as percentage of revenue.
            benchmark: Industry benchmark percentage.

        Returns:
            Assessment text.
        """
        difference = marketing_percentage - benchmark

        if difference >= 5:
            return f"Marketing spend significantly above industry benchmark by {difference:.1f} percentage points. Evaluate effectiveness and ROI to ensure efficient spending."
        elif difference >= 2:
            return f"Marketing spend moderately above industry benchmark by {difference:.1f} percentage points. Monitor effectiveness to ensure spending generates adequate returns."
        elif difference >= -2:
            return f"Marketing spend in line with industry benchmark (difference of {difference:.1f} percentage points). Appropriate investment level based on industry standards."
        elif difference >= -5:
            return f"Marketing spend below industry benchmark by {-difference:.1f} percentage points. Consider whether additional investment could drive growth."
        else:
            return f"Marketing spend significantly below industry benchmark by {-difference:.1f} percentage points. May indicate underinvestment limiting growth potential."

    def _assess_ltv_cac_ratio(self, ltv_cac_ratio: float) -> str:
        """
        Assess customer lifetime value to acquisition cost ratio.

        Args:
            ltv_cac_ratio: LTV to CAC ratio.

        Returns:
            Assessment text.
        """
        if ltv_cac_ratio < 1:
            return "Critical customer economics with LTV below acquisition cost. Fundamental business model revision required as each customer acquisition generates negative value."
        elif ltv_cac_ratio < 2:
            return "Concerning LTV:CAC ratio below recommended minimum threshold of 3:1. Immediate improvements needed in either customer value or acquisition efficiency."
        elif ltv_cac_ratio < 3:
            return "Marginal LTV:CAC ratio approaching but still below recommended minimum threshold of 3:1. Focus needed on improving customer economics."
        elif ltv_cac_ratio < 5:
            return "Healthy LTV:CAC ratio above 3:1 threshold indicating sustainable customer acquisition economics. Continue optimizing for improvement."
        else:
            return "Excellent LTV:CAC ratio of 5:1 or higher indicating very efficient customer acquisition and strong customer lifetime value. Potential opportunity to accelerate growth through increased acquisition spending."

    def _assess_metric_performance(
        self,
        metric: str,
        actual_value: float,
        benchmark: float,
        difference: float
    ) -> str:
        """
        Assess performance of a specific metric compared to benchmark.

        Args:
            metric: Metric name.
            actual_value: Actual metric value.
            benchmark: Benchmark value.
            difference: Difference between actual and benchmark.

        Returns:
            Assessment text.
        """
        metric_lower = metric.lower()

        # For metrics where higher is better
        if any(term in metric_lower for term in ["margin", "growth", "roi", "return", "efficiency"]):
            if difference >= benchmark * 0.2:  # 20% or more above benchmark
                return f"Exceptional performance significantly exceeding industry benchmark"
            elif difference >= benchmark * 0.05:  # 5-20% above benchmark
                return f"Strong performance above industry benchmark"
            elif difference >= -benchmark * 0.05:  # Within 5% of benchmark
                return f"Performance in line with industry benchmark"
            elif difference >= -benchmark * 0.2:  # 5-20% below benchmark
                return f"Performance below industry benchmark requiring attention"
            else:  # More than 20% below benchmark
                return f"Significant underperformance requiring immediate action"

        # For metrics where lower is better (e.g., cost ratios)
        elif any(term in metric_lower for term in ["cost", "expense", "ratio"]):
            # Invert the assessment logic
            if difference <= -benchmark * 0.2:  # 20% or more below benchmark
                return f"Exceptional performance with metric significantly better than industry benchmark"
            elif difference <= -benchmark * 0.05:  # 5-20% below benchmark
                return f"Strong performance better than industry benchmark"
            elif difference <= benchmark * 0.05:  # Within 5% of benchmark
                return f"Performance in line with industry benchmark"
            elif difference <= benchmark * 0.2:  # 5-20% above benchmark
                return f"Performance worse than industry benchmark requiring attention"
            else:  # More than 20% above benchmark
                return f"Significant underperformance requiring immediate action"

        # Default case
        else:
            if difference > 0:
                return f"Performance above industry benchmark"
            elif difference == 0:
                return f"Performance exactly at industry benchmark"
            else:
                return f"Performance below industry benchmark"

    def _generate_financial_insights(
        self,
        profit_margin: float,
        growth_rate: Optional[float],
        benchmark_comparison: List[Dict[str, Any]],
        additional_metrics: Dict[str, float]
    ) -> List[str]:
        """
        Generate financial insights based on metrics analysis.

        Args:
            profit_margin: Profit margin percentage.
            growth_rate: Optional growth rate percentage.
            benchmark_comparison: List of benchmark comparison results.
            additional_metrics: Dictionary of additional metrics.

        Returns:
            List of financial insights.
        """
        insights = []

        # Profit margin insights
        if profit_margin <= 0:
            insights.append("The negative profit margin indicates fundamental profitability challenges requiring comprehensive review of pricing strategy, cost structure, and business model")
        elif profit_margin < 5:
            insights.append("The low profit margin creates vulnerability to market fluctuations and limits reinvestment capacity, indicating need for margin improvement initiatives")
        elif profit_margin > 15:
            insights.append("The strong profit margin provides financial resilience and capacity for strategic investments in growth and innovation")

        # Growth insights
        if growth_rate is not None:
            if growth_rate < 0:
                insights.append("The revenue contraction signals market challenges or competitive pressure requiring focused attention on sales and customer retention")
            elif growth_rate > 10:
                insights.append("The strong revenue growth creates opportunity to gain market share while requiring careful management of operational capacity and quality")

            # Growth and margin relationship
            if growth_rate > 10 and profit_margin < 5:
                insights.append("The combination of high growth and low margins suggests aggressive pricing strategy or high customer acquisition costs that may affect long-term sustainability")
            elif growth_rate < 0 and profit_margin > 15:
                insights.append("The high margins despite revenue contraction indicate strong pricing power but potential market saturation or competitive challenges")

        # Benchmark comparison insights
        for comparison in benchmark_comparison:
            metric = comparison.get("metric", "")
            status = comparison.get("status", "")
            percent_diff = comparison.get("percent_difference", 0)

            if "margin" in metric.lower() and "above" in status.lower() and percent_diff > 20:
                insights.append(f"The profit margin significantly exceeds industry benchmarks by {percent_diff:.1f}%, indicating potential competitive advantage or premium market positioning")
            elif "margin" in metric.lower() and "below" in status.lower() and percent_diff < -20:
                insights.append(f"The profit margin is substantially below industry benchmarks by {-percent_diff:.1f}%, suggesting potential pricing challenges or cost structure inefficiencies")

            if "growth" in metric.lower() and "above" in status.lower() and percent_diff > 30:
                insights.append(f"The growth rate substantially outperforms industry benchmarks by {percent_diff:.1f}%, indicating market share gains and effective growth strategy")
            elif "growth" in metric.lower() and "below" in status.lower() and percent_diff < -30:
                insights.append(f"The growth rate significantly underperforms industry benchmarks by {-percent_diff:.1f}%, suggesting competitive challenges or market positioning issues")

        # Additional metrics insights
        for metric, value in additional_metrics.items():
            if "roi" in metric.lower() or "return" in metric.lower():
                if value > 20:
                    insights.append(f"The {metric} of {value:.1f}% indicates strong investment performance and effective capital allocation")
                elif value < 5:
                    insights.append(f"The {metric} of {value:.1f}% is below typical investment hurdle rates, suggesting need for improved capital allocation")

            elif "debt" in metric.lower() or "leverage" in metric.lower():
                if value > 60:
                    insights.append(f"The {metric} of {value:.1f}% represents elevated leverage potentially limiting financial flexibility and increasing risk profile")
                elif value < 20:
                    insights.append(f"The {metric} of {value:.1f}% indicates conservative capital structure providing financial flexibility but potential for increased leverage to enhance returns")

        return insights if insights else ["Comprehensive financial analysis requires additional context and historical data to identify specific insights and trends"]

    def _generate_financial_recommendations(
        self,
        profit_margin: float,
        growth_rate: Optional[float],
        benchmark_comparison: List[Dict[str, Any]],
        additional_metrics: Dict[str, float]
    ) -> List[str]:
        """
        Generate financial recommendations based on metrics analysis.

        Args:
            profit_margin: Profit margin percentage.
            growth_rate: Optional growth rate percentage.
            benchmark_comparison: List of benchmark comparison results.
            additional_metrics: Dictionary of additional metrics.

        Returns:
            List of financial recommendations.
        """
        recommendations = []

        # Profit margin recommendations
        if profit_margin <= 0:
            recommendations.append("Conduct comprehensive profitability analysis to identify negative margin drivers and develop action plan with specific profit improvement initiatives")
            recommendations.append("Evaluate pricing strategy to ensure appropriate value capture reflecting product differentiation and competitive positioning")
        elif profit_margin < 5:
            recommendations.append("Implement targeted cost optimization initiatives focusing on major cost categories with efficiency opportunities")
            recommendations.append("Analyze product/service mix to identify and prioritize higher-margin offerings")
        elif profit_margin < 10:
            recommendations.append("Develop margin improvement roadmap with initiatives balancing short-term tactics and structural improvements")

        # Growth recommendations
        if growth_rate is not None:
            if growth_rate < 0:
                recommendations.append("Conduct customer retention analysis to identify and address churn drivers")
                recommendations.append("Develop targeted growth strategy for highest-potential segments and offerings")
            elif growth_rate < 5:
                recommendations.append("Invest in growth acceleration initiatives in highest-potential segments while maintaining cost discipline")
            elif growth_rate > 15:
                recommendations.append("Ensure operational capacity and quality systems can scale to support continued high growth")
                recommendations.append("Evaluate potential for strategic price increases to capitalize on strong market position")

        # Benchmark-based recommendations
        below_benchmark_metrics = [comp.get("metric") for comp in benchmark_comparison if "below" in comp.get("status", "").lower()]
        if below_benchmark_metrics:
            metrics_str = ", ".join(below_benchmark_metrics)
            recommendations.append(f"Develop action plans targeting metrics below industry benchmarks: {metrics_str}")

        # Additional metrics recommendations
        high_liquidity = any("cash" in metric.lower() and value > 20 for metric, value in additional_metrics.items())
        if high_liquidity:
            recommendations.append("Evaluate capital allocation strategy to optimize returns on excess liquidity through growth investments, share repurchases, or dividends")

        high_debt = any("debt" in metric.lower() and value > 60 for metric, value in additional_metrics.items())
        if high_debt:
            recommendations.append("Develop debt reduction strategy to strengthen balance sheet and improve financial flexibility")

        # Default recommendations if few generated
        if len(recommendations) < 2:
            recommendations.append("Implement regular financial performance reviews with clear KPIs and accountability for improvement initiatives")
            recommendations.append("Develop more granular financial reporting to identify profitability drivers at segment and product levels")

        return recommendations

    def _generate_detailed_financial_analysis(
        self,
        time_period: str,
        revenue: float,
        costs: float,
        profit: float,
        profit_margin: float,
        growth_rate: Optional[float],
        benchmark_comparison: List[Dict[str, Any]],
        financial_insights: List[str],
        recommendations: List[str],
        additional_metrics: Dict[str, float]
    ) -> str:
        """
        Generate detailed financial analysis text.
        """
        # Format benchmark comparison
        benchmark_str = ""
        if benchmark_comparison:
            for comparison in benchmark_comparison:
                metric = comparison.get("metric", "")
                actual = comparison.get("actual", 0)
                benchmark = comparison.get("benchmark", 0)
                difference = comparison.get("difference", 0)
                percent_diff = comparison.get("percent_difference", 0)
                status = comparison.get("status", "")
                assessment = comparison.get("assessment", "")

                benchmark_str += f"""
### {metric.title()}
**Actual:** {actual:.2f}%
**Benchmark:** {benchmark:.2f}%
**Difference:** {difference:.2f} percentage points ({percent_diff:.2f}%)
**Status:** {status}

{assessment}
"""
        else:
            benchmark_str = "No benchmark data available for comparison."

        # Format additional metrics
        additional_metrics_str = ""
        if additional_metrics:
            for metric, value in additional_metrics.items():
                additional_metrics_str += f"- **{metric.title()}:** {value}\n"
        else:
            additional_metrics_str = "No additional metrics provided."

        # Format insights and recommendations
        insights_str = "\n".join([f"- {insight}" for insight in financial_insights])
        recommendations_str = "\n".join([f"- {recommendation}" for recommendation in recommendations])

        # Create detailed financial analysis markdown
        detailed_analysis = f"""
# Financial Metrics Analysis: {time_period}

## Revenue and Cost Analysis
- **Revenue:** ${revenue:,.2f}
- **Costs:** ${costs:,.2f}
- **Profit:** ${profit:,.2f}
- **Profit Margin:** {profit_margin:.2f}%

## Profit Margin Assessment
{self._interpret_profit_margin(profit_margin)}

## Growth Analysis
{f"**Growth Rate:** {growth_rate:.2f}%\n\n{self._assess_growth_rate(growth_rate)}" if growth_rate is not None else "Growth data not provided."}

## Industry Benchmark Comparison
{benchmark_str}

## Additional Financial Metrics
{additional_metrics_str}

## Key Financial Insights
{insights_str}

## Strategic Implications
The financial performance has direct implications for business strategy and decision-making:

1. **Capital Allocation:** The current profitability and growth profile suggest {'prioritizing investments in growth initiatives' if (profit_margin > 10 and (growth_rate or 0) > 5) else 'focusing on operational improvements before major growth investments' if profit_margin < 10 else 'balanced approach to optimization and growth investments'}.

2. **Competitive Position:** Financial performance relative to benchmarks indicates {'a strong competitive position that can be leveraged' if len([c for c in benchmark_comparison if 'above' in c.get('status', '').lower()]) > len([c for c in benchmark_comparison if 'below' in c.get('status', '').lower()]) else 'areas requiring improvement to strengthen competitive position'}.

3. **Risk Profile:** The financial structure and performance suggest {'a relatively low risk profile with capacity to pursue opportunities' if profit_margin > 15 else 'elevated risk requiring careful management of resources and investments' if profit_margin < 5 else 'moderate risk profile requiring balanced approach to opportunities and risk management'}.

## Recommendations for Improvement
{recommendations_str}

## Monitoring Framework
Establish regular monitoring of key financial metrics with clear thresholds for action. Implement quarterly in-depth reviews to assess progress on improvement initiatives and adjust strategy as needed.
"""

        return detailed_analysis

    # Helper methods for market sizing analysis

    def _interpret_market_sizing_results(self, market_sizing_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate interpretation of market sizing results.

        Args:
            market_sizing_data: Market sizing results dictionary.

        Returns:
            Dictionary of interpretations by category.
        """
        interpretation = {}

        # Get approach-specific interpretation
        approach = market_sizing_data.get("sizing_approach", "").upper()

        if approach == "TAM-SAM-SOM":
            tam = market_sizing_data.get("total_addressable_market", {}).get("value")
            sam = market_sizing_data.get("serviceable_addressable_market", {}).get("value")
            som = market_sizing_data.get("serviceable_obtainable_market", {}).get("value")

            if all(val is not None for val in [tam, sam, som]):
                interpretation["market_potential"] = (
                    f"The total addressable market (TAM) of ${tam:,.2f} represents the theoretical "
                    f"maximum opportunity, while the serviceable addressable market (SAM) of "
                    f"${sam:,.2f} represents a more realistic target based on geographic, "
                    f"technological, and regulatory constraints."
                )

                interpretation["obtainable_market"] = (
                    f"The serviceable obtainable market (SOM) of ${som:,.2f} represents "
                    f"the portion of the market that can realistically be captured given "
                    f"competition, go-to-market strategy, and other practical constraints."
                )

                som_percentage = (som / tam) * 100 if tam > 0 else 0
                som_assessment = "conservative" if som_percentage < 5 else "reasonable" if som_percentage < 10 else "ambitious"

                interpretation["market_share"] = (
                    f"The obtainable market represents {som_percentage:.2f}% of the total "
                    f"addressable market, which is a {som_assessment} target based on "
                    f"typical market penetration patterns."
                )

                # Add business viability assessment
                if som < 1000000:  # Less than $1M
                    interpretation["business_viability"] = (
                        f"The SOM of ${som:,.2f} represents a relatively small market opportunity. "
                        f"This may be viable for a focused small business or niche offering, but would "
                        f"likely be challenging for a venture-backed company seeking significant scale."
                    )
                elif som < 10000000:  # $1M - $10M
                    interpretation["business_viability"] = (
                        f"The SOM of ${som:,.2f} represents a moderate market opportunity. "
                        f"This could support a sustainable small to medium business with focused "
                        f"operations and efficient customer acquisition."
                    )
                elif som < 100000000:  # $10M - $100M
                    interpretation["business_viability"] = (
                        f"The SOM of ${som:,.2f} represents a substantial market opportunity. "
                        f"This could support a high-growth company with potential for significant scale, "
                        f"making it attractive for various business models and investment approaches."
                    )
                else:  # More than $100M
                    interpretation["business_viability"] = (
                        f"The SOM of ${som:,.2f} represents a large market opportunity. "
                        f"This sizeable addressable market could support multiple competitors and "
                        f"provides potential for substantial business scale, making it highly attractive "
                        f"for growth-oriented companies and investors."
                    )

        elif approach == "BOTTOM-UP":
            total_potential = market_sizing_data.get("total_potential_market", {}).get("value")
            obtainable = market_sizing_data.get("obtainable_market", {}).get("value")
            penetration = market_sizing_data.get("market_parameters", {}).get("penetration_rate")
            population = market_sizing_data.get("market_parameters", {}).get("population_size")
            unit_price = market_sizing_data.get("market_parameters", {}).get("unit_price")

            if all(val is not None for val in [total_potential, obtainable, penetration]):
                interpretation["market_potential"] = (
                    f"The total potential market of ${total_potential:,.2f} represents the maximum "
                    f"theoretical market size if all {population:,} potential customers purchased "
                    f"the product/service at ${unit_price:,.2f} per unit."
                )

                penetration_assessment = "conservative" if penetration < 5 else "moderate" if penetration < 15 else "aggressive"

                interpretation["obtainable_market"] = (
                    f"With a {penetration_assessment} projected market penetration rate of {penetration}%, "
                    f"the obtainable market is estimated at ${obtainable:,.2f}, which represents a "
                    f"more realistic target given typical adoption patterns and competitive dynamics."
                )

                # Add business viability assessment
                if obtainable < 1000000:  # Less than $1M
                    interpretation["business_viability"] = (
                        f"The obtainable market of ${obtainable:,.2f} represents a relatively small opportunity. "
                        f"With a unit price of ${unit_price:,.2f}, this translates to approximately "
                        f"{int(obtainable/unit_price):,} customers, which may be viable for a focused small "
                        f"business but challenging for a venture seeking significant scale."
                    )
                elif obtainable < 10000000:  # $1M - $10M
                    interpretation["business_viability"] = (
                        f"The obtainable market of ${obtainable:,.2f} represents a moderate opportunity. "
                        f"With a unit price of ${unit_price:,.2f}, this translates to approximately "
                        f"{int(obtainable/unit_price):,} customers, which could support a sustainable "
                        f"small to medium business with effective customer acquisition."
                    )
                elif obtainable < 100000000:  # $10M - $100M
                    interpretation["business_viability"] = (
                        f"The obtainable market of ${obtainable:,.2f} represents a substantial opportunity. "
                        f"With a unit price of ${unit_price:,.2f}, this translates to approximately "
                        f"{int(obtainable/unit_price):,} customers, which could support a high-growth "
                        f"company with significant scale potential."
                    )
                else:  # More than $100M
                    interpretation["business_viability"] = (
                        f"The obtainable market of ${obtainable:,.2f} represents a large opportunity. "
                        f"With a unit price of ${unit_price:,.2f}, this translates to approximately "
                        f"{int(obtainable/unit_price):,} customers, providing potential for substantial "
                        f"business scale and making it highly attractive for growth-oriented companies."
                    )

        # Add growth projection interpretation if available
        if "five_year_projections" in market_sizing_data:
            growth_rate = market_sizing_data.get("market_growth_rate")

            if growth_rate is not None:
                growth_assessment = "modest" if growth_rate < 5 else "healthy" if growth_rate < 10 else "strong"

                interpretation["growth_projection"] = (
                    f"With a {growth_assessment} annual growth rate of {growth_rate}%, "
                    f"the market is projected to expand significantly over the next five years. "
                    f"This growth trajectory {'provides favorable tailwinds for business expansion' if growth_rate > 0 else 'creates challenging headwinds requiring careful strategy'}."
                )

                # Add five-year projection details
                if approach == "TAM-SAM-SOM":
                    future_som = market_sizing_data.get("five_year_projections", {}).get("projected_som")
                    if future_som:
                        interpretation["future_market_potential"] = (
                            f"In five years, the serviceable obtainable market is projected to reach "
                            f"${future_som:,.2f}, representing {'significant expansion opportunity' if growth_rate > 5 else 'moderate growth potential'}."
                        )

                elif approach == "BOTTOM-UP":
                    future_obtainable = market_sizing_data.get("five_year_projections", {}).get("projected_obtainable_market")
                    if future_obtainable:
                        interpretation["future_market_potential"] = (
                            f"In five years, the obtainable market is projected to reach "
                            f"${future_obtainable:,.2f}, representing {'significant expansion opportunity' if growth_rate > 5 else 'moderate growth potential'}."
                        )

        return interpretation

    def _generate_market_sizing_implications(self, market_sizing_data: Dict[str, Any]) -> List[str]:
        """
        Generate strategic implications based on market sizing results.

        Args:
            market_sizing_data: Market sizing results dictionary.

        Returns:
            List of strategic implications.
        """
        implications = []

        # Get approach-specific implications
        approach = market_sizing_data.get("sizing_approach", "").upper()

        if approach == "TAM-SAM-SOM":
            tam = market_sizing_data.get("total_addressable_market", {}).get("value")
            sam = market_sizing_data.get("serviceable_addressable_market", {}).get("value")
            som = market_sizing_data.get("serviceable_obtainable_market", {}).get("value")

            if all(val is not None for val in [tam, sam, som]):
                # Market size implications
                if som < 1000000:  # Less than $1M
                    implications.append("The modest obtainable market size suggests focusing on a capital-efficient business model with low overhead and targeted customer acquisition.")
                elif som < 10000000:  # $1M - $10M
                    implications.append("The moderate market size suggests a focused go-to-market strategy targeting highest-value segments with efficient customer acquisition.")
                else:  # More than $10M
                    implications.append("The substantial market size justifies investment in scalable business infrastructure and potentially more aggressive customer acquisition.")

                # SAM to TAM ratio implications
                sam_to_tam_ratio = (sam / tam) * 100 if tam > 0 else 0
                if sam_to_tam_ratio < 20:
                    implications.append("The relatively small serviceable portion of the total market suggests focusing on specific niches or considering ways to expand addressability through innovation or market development.")
                else:
                    implications.append("The significant serviceable portion of the total market suggests opportunity for broad market approach with potential for segment-specific customization.")

                # SOM to SAM ratio implications
                som_to_sam_ratio = (som / sam) * 100 if sam > 0 else 0
                if som_to_sam_ratio < 10:
                    implications.append("The conservative obtainable market estimate relative to serviceable market suggests phased approach focusing on highest-probability segments first.")
                elif som_to_sam_ratio > 30:
                    implications.append("The ambitious obtainable market target relative to serviceable market suggests need for significant competitive differentiation and go-to-market investment.")

        elif approach == "BOTTOM-UP":
            total_potential = market_sizing_data.get("total_potential_market", {}).get("value")
            obtainable = market_sizing_data.get("obtainable_market", {}).get("value")
            penetration = market_sizing_data.get("market_parameters", {}).get("penetration_rate")

            if all(val is not None for val in [total_potential, obtainable, penetration]):
                # Market size implications
                if obtainable < 1000000:  # Less than $1M
                    implications.append("The modest obtainable market size suggests focusing on efficient operations and targeted customer acquisition to achieve profitability with limited scale.")
                elif obtainable < 10000000:  # $1M - $10M
                    implications.append("The moderate market size represents viable opportunity requiring disciplined growth strategy focused on capital efficiency and customer economics.")
                else:  # More than $10M
                    implications.append("The substantial obtainable market justifies investment in scalable infrastructure and potentially more aggressive customer acquisition strategy.")

                # Penetration rate implications
                if penetration < 5:
                    implications.append("The conservative penetration projection suggests focused go-to-market strategy targeting early adopters or specific market segments with highest value potential.")
                elif penetration < 15:
                    implications.append("The moderate penetration projection suggests balanced approach to market development with phased expansion strategy.")
                else:
                    implications.append("The ambitious penetration target suggests need for significant investment in market education, brand building, and competitive differentiation.")

        # Add growth implications if available
        if "five_year_projections" in market_sizing_data:
            growth_rate = market_sizing_data.get("market_growth_rate")

            if growth_rate is not None:
                if growth_rate < 0:
                    implications.append("The negative growth projection suggests focusing on taking market share from competitors rather than relying on market expansion, with emphasis on clear differentiation and competitive displacement.")
                elif growth_rate < 5:
                    implications.append("The modest growth rate suggests focusing on market share gains and operational efficiency rather than relying primarily on market expansion.")
                elif growth_rate < 10:
                    implications.append("The healthy growth rate suggests balanced approach of market development and share capture to maximize opportunity.")
                else:
                    implications.append("The strong growth trajectory suggests prioritizing market presence and scalability to capitalize on expanding opportunity, with potential for first-mover advantage in emerging segments.")

        # Add pricing implications for bottom-up approach
        if approach == "BOTTOM-UP":
            unit_price = market_sizing_data.get("market_parameters", {}).get("unit_price")
            if unit_price:
                implications.append(f"The unit price of ${unit_price:,.2f} suggests {'a premium positioning requiring clear value differentiation' if unit_price > 100 else 'a mass-market approach requiring efficient customer acquisition and operations' if unit_price < 50 else 'a mid-market positioning balancing value and scale'}.")

        return implications

    # Helper methods for pricing optimization

    def _calculate_price_scenarios(
        self,
        current_price: float,
        current_volume: int,
        price_elasticity: float,
        variable_cost: Optional[float] = None,
        fixed_costs: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate price scenarios to identify optimal price points.

        Args:
            current_price: Current price of the product or service.
            current_volume: Current sales volume at the current price.
            price_elasticity: Price elasticity of demand (negative value).
            variable_cost: Optional variable cost per unit.
            fixed_costs: Optional total fixed costs.

        Returns:
            List of price scenarios with volume, revenue, and profit projections.
        """
        # Ensure elasticity is negative (normal demand curve)
        price_elasticity = min(price_elasticity, 0) if price_elasticity > 0 else price_elasticity

        # Generate price points from -30% to +30% of current price
        price_changes = [-30, -25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25, 30]
        scenarios = []

        for change in price_changes:
            # Calculate new price
            price_pct_change = change
            new_price = current_price * (1 + price_pct_change/100)

            # Calculate new volume based on elasticity
            volume_pct_change = price_pct_change * price_elasticity
            new_volume = max(0, int(current_volume * (1 + volume_pct_change/100)))

            # Calculate revenue
            new_revenue = new_price * new_volume
            revenue_pct_change = ((new_revenue / (current_price * current_volume)) - 1) * 100 if current_price * current_volume > 0 else 0

            # Create scenario
            scenario = {
                "price_change_percentage": price_pct_change,
                "new_price": new_price,
                "new_volume": new_volume,
                "new_revenue": new_revenue,
                "volume_change_percentage": volume_pct_change,
                "revenue_change_percentage": revenue_pct_change
            }

            # Calculate profit if cost information is available
            if variable_cost is not None:
                contribution_margin = new_price - variable_cost
                contribution_margin_percentage = (contribution_margin / new_price) * 100 if new_price > 0 else 0
                total_contribution = contribution_margin * new_volume

                scenario.update({
                    "contribution_margin": contribution_margin,
                    "contribution_margin_percentage": contribution_margin_percentage,
                    "total_contribution": total_contribution
                })

                if fixed_costs is not None:
                    profit = total_contribution - fixed_costs
                    profit_pct_change = 0

                    # Calculate current profit for percentage change calculation
                    current_contribution = (current_price - variable_cost) * current_volume
                    current_profit = current_contribution - fixed_costs

                    if current_profit != 0:
                        profit_pct_change = ((profit / current_profit) - 1) * 100

                    scenario.update({
                        "profit": profit,
                        "profit_change_percentage": profit_pct_change
                    })

            scenarios.append(scenario)

        return scenarios

    def _determine_optimized_price(
        self,
        price_scenarios: List[Dict[str, Any]],
        pricing_strategy: str
    ) -> tuple:
        """
        Determine the optimal price point based on pricing strategy.

        Args:
            price_scenarios: List of price scenarios with projections.
            pricing_strategy: Strategy to prioritize ("profit", "revenue", "market_share", "premium").

        Returns:
            Tuple of (optimized price, basis for optimization)
        """
        # Default to profit optimization if strategy is not recognized
        pricing_strategy = pricing_strategy.lower() if pricing_strategy else "profit"

        if pricing_strategy == "profit":
            # Check if profit data is available
            if "profit" in price_scenarios[0]:
                # Find scenario with maximum profit
                best_scenario = max(price_scenarios, key=lambda x: x["profit"])
                return best_scenario["new_price"], f"Maximum profit of ${best_scenario['profit']:,.2f}"
            else:
                # Use contribution margin as a proxy for profit
                best_scenario = max(price_scenarios, key=lambda x: x.get("total_contribution", 0))
                return best_scenario["new_price"], f"Maximum total contribution of ${best_scenario.get('total_contribution', 0):,.2f}"

        elif pricing_strategy == "revenue":
            # Find scenario with maximum revenue
            best_scenario = max(price_scenarios, key=lambda x: x["new_revenue"])
            return best_scenario["new_price"], f"Maximum revenue of ${best_scenario['new_revenue']:,.2f}"

        elif pricing_strategy == "market_share":
            # Find scenario with maximum volume while maintaining positive contribution margin
            if "contribution_margin" in price_scenarios[0]:
                viable_scenarios = [s for s in price_scenarios if s.get("contribution_margin", 0) > 0]
                if viable_scenarios:
                    best_scenario = max(viable_scenarios, key=lambda x: x["new_volume"])
                    return best_scenario["new_price"], f"Maximum volume of {best_scenario['new_volume']} units with positive contribution margin"

            # If contribution margin not available, simply maximize volume
            best_scenario = max(price_scenarios, key=lambda x: x["new_volume"])
            return best_scenario["new_price"], f"Maximum volume of {best_scenario['new_volume']} units"

        elif pricing_strategy == "premium":
            # Find highest price that doesn't reduce profit/contribution by more than 10%
            baseline = next((s for s in price_scenarios if s["price_change_percentage"] == 0), None)

            if baseline:
                if "profit" in baseline:
                    baseline_metric = baseline["profit"]
                    metric_name = "profit"
                elif "total_contribution" in baseline:
                    baseline_metric = baseline["total_contribution"]
                    metric_name = "total contribution"
                else:
                    baseline_metric = baseline["new_revenue"]
                    metric_name = "revenue"

                # Filter for scenarios with higher prices that maintain at least 90% of baseline metric
                premium_scenarios = [
                    s for s in price_scenarios
                    if s["price_change_percentage"] > 0 and
                    (s.get("profit", s.get("total_contribution", s["new_revenue"])) >= baseline_metric * 0.9)
                ]

                if premium_scenarios:
                    # Find highest price that meets criteria
                    best_scenario = max(premium_scenarios, key=lambda x: x["new_price"])
                    return best_scenario["new_price"], f"Premium price maintaining at least 90% of baseline {metric_name}"

            # Default to 10% price increase if premium strategy can't be optimized
            premium_scenario = next((s for s in price_scenarios if s["price_change_percentage"] == 10), None)
            if premium_scenario:
                return premium_scenario["new_price"], "Standard premium pricing (10% increase)"

        # Default: find scenario with highest price that doesn't reduce volume by more than 15%
        baseline = next((s for s in price_scenarios if s["price_change_percentage"] == 0), None)
        optimal_scenario = next(
            (s for s in sorted(price_scenarios, key=lambda x: -x["new_price"])
             if s["volume_change_percentage"] > -15),
            price_scenarios[0]
        )

        return optimal_scenario["new_price"], f"Balanced price maintaining reasonable volume"

    def _assess_break_even_point(self, current_volume: int, break_even_volume: float) -> str:
        """
        Assess break-even point relative to current volume.

        Args:
            current_volume: Current sales volume.
            break_even_volume: Break-even volume.

        Returns:
            Assessment text.
        """
        if break_even_volume <= 0:
            return "Invalid break-even calculation - please check fixed costs and contribution margin inputs."

        ratio = current_volume / break_even_volume if break_even_volume > 0 else float('inf')

        if ratio < 0.7:
            return f"Current volume is significantly below break-even point ({ratio:.2f}x). Business is operating at a loss, requiring substantial volume growth or cost structure changes."
        elif ratio < 0.9:
            return f"Current volume is below break-even point ({ratio:.2f}x). Focused efforts needed to increase volume or adjust cost structure to achieve profitability."
        elif ratio < 1.1:
            return f"Current volume is near break-even point ({ratio:.2f}x). Business is at or near profitability threshold, but has limited margin of safety."
        elif ratio < 1.5:
            return f"Current volume exceeds break-even point ({ratio:.2f}x), providing moderate margin of safety. Business is profitable with some buffer against volume fluctuations."
        elif ratio < 2.0:
            return f"Current volume significantly exceeds break-even point ({ratio:.2f}x), providing healthy margin of safety. Business is solidly profitable with good resilience to volume fluctuations."
        else:
            return f"Current volume far exceeds break-even point ({ratio:.2f}x), providing excellent margin of safety. Business is highly profitable with strong resilience to volume fluctuations."

    def _assess_competitive_price_position(self, price_position: float, price_relative_to_avg: float) -> str:
        """
        Assess competitive price positioning.

        Args:
            price_position: Percentile position within competitive range.
            price_relative_to_avg: Percentage difference from average competitor price.

        Returns:
            Assessment text.
        """
        if price_position < 25:
            if price_relative_to_avg < -15:
                return "Positioned as value leader with significantly lower pricing than competitors. This may drive volume but risks margin compression and potential perception of lower quality."
            else:
                return "Positioned at lower end of competitive price range. This competitive pricing should support volume while maintaining margin if cost structure is efficient."

        elif price_position < 50:
            return "Positioned in lower-middle of competitive price range. This balanced approach provides moderate price advantage without severe margin compression or value perception challenges."

        elif price_position < 75:
            return "Positioned in upper-middle of competitive price range. This positioning supports margins but requires clear value differentiation to justify premium versus lower-priced alternatives."

        else:
            if price_relative_to_avg > 15:
                return "Positioned as premium leader with significantly higher pricing than competitors. This supports margins but requires exceptional value delivery and brand positioning to justify premium."
            else:
                return "Positioned at upper end of competitive price range. This premium positioning supports margins but requires clear value differentiation and strong brand positioning."

    def _generate_pricing_implementation_considerations(
        self,
        price_change_percentage: float,
        product_name: str,
        competitor_prices: Optional[List[float]] = None
    ) -> List[str]:
        """
        Generate implementation considerations for pricing changes.

        Args:
            price_change_percentage: Percentage price change from current price.
            product_name: Product name.
            competitor_prices: Optional list of competitor prices.

        Returns:
            List of implementation considerations.
        """
        considerations = []

        # Price increase considerations
        if price_change_percentage > 0:
            if price_change_percentage > 10:
                considerations.append("Implement significant price increase gradually to minimize customer resistance and potential volume impact")
                considerations.append("Develop clear communication strategy emphasizing value proposition to support price increase")
            else:
                considerations.append("Communicate price adjustment with emphasis on value delivered to minimize volume impact")

            considerations.append("Monitor customer response and competitive reaction closely following price implementation")

        # Price decrease considerations
        elif price_change_percentage < 0:
            if price_change_percentage < -10:
                considerations.append("Evaluate impact of significant price decrease on brand perception and positioning before implementation")
                considerations.append("Consider targeted promotions or segmented pricing as alternatives to broad price reduction")
            else:
                considerations.append("Promote price adjustment to maximize volume response and potential market share gains")

            considerations.append("Prepare for potential competitive response and develop contingency plans")

        # Competitive positioning considerations
        if competitor_prices:
            avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
            new_price_relative = ((current_price * (1 + price_change_percentage/100)) / avg_competitor_price - 1) * 100

            if new_price_relative > 10:
                considerations.append("Ensure clear communication of differentiated value to justify premium pricing relative to competition")
            elif new_price_relative < -10:
                considerations.append("Ensure cost structure supports lower pricing to maintain profitability while positioned as value option")

        # General considerations
        if len(considerations) < 3:
            considerations.append("Develop clear implementation timeline with appropriate stakeholder communication")
            considerations.append("Establish monitoring framework to track impact on volume, revenue, and profit following implementation")

        return considerations

    def _interpret_pricing_analysis(self, pricing_data: Dict[str, Any]) -> List[str]:
        """
        Generate interpretation and recommendations based on pricing analysis.

        Args:
            pricing_data: Pricing analysis results dictionary.

        Returns:
            List of interpretations and recommendations.
        """
        recommendations = []

        # Check if we have complete pricing analysis
        if has_complete_analysis:
            # Add recommendation about optimal price
            optimal_price = pricing_data.get("pricing_recommendations", {}).get("optimized_price")
            current_price = pricing_data.get("current_pricing", {}).get("price")
            pricing_strategy = pricing_data.get("pricing_strategy")

            if optimal_price and current_price:
                price_change = ((optimal_price / current_price) - 1) * 100

                if abs(price_change) < 2:
                    recommendations.append(f"The current pricing is already near optimal based on {pricing_strategy} optimization objective. Maintain current pricing while monitoring market conditions.")
                elif price_change > 0:
                    if price_change > 10:
                        recommendations.append(f"Consider significant price increase of approximately {price_change:.1f}% to optimize {pricing_strategy}. Implement gradually with clear value communication to minimize volume impact.")
                    else:
                        recommendations.append(f"Implement moderate price increase of approximately {price_change:.1f}% to optimize {pricing_strategy}, with appropriate communication emphasizing value proposition.")
                else:
                    if price_change < -10:
                        recommendations.append(f"Consider significant price decrease of approximately {-price_change:.1f}% to optimize {pricing_strategy}. Evaluate impact on brand perception and competitive positioning before implementation.")
                    else:
                        recommendations.append(f"Implement moderate price decrease of approximately {-price_change:.1f}% to optimize {pricing_strategy}, with appropriate promotion to maximize volume response.")

            # Add recommendation based on price elasticity
            elasticity = pricing_data.get("price_elasticity")
            if elasticity:
                if elasticity > -0.5:
                    recommendations.append("The very low price sensitivity (elasticity near zero) indicates strong pricing power and potential for significant price increases with minimal volume impact.")
                elif elasticity > -1:
                    recommendations.append("The relatively inelastic demand suggests an opportunity for price increases with minimal volume impact, indicating possible premium positioning.")
                elif elasticity > -1.5:
                    recommendations.append("The moderate price sensitivity indicates balanced price-volume dynamics where price adjustments should be evaluated carefully against volume implications.")
                elif elasticity > -2:
                    recommendations.append("The moderately high price sensitivity suggests caution with price increases and potential for volume-based strategies leveraging price decreases.")
                else:
                    recommendations.append("The high price sensitivity indicates price-driven purchasing dynamics where lower pricing may significantly drive volume, favoring market share strategies.")

            # Add recommendation based on competitive positioning
            competitive_analysis = pricing_data.get("competitive_analysis")
            if competitive_analysis:
                price_position = competitive_analysis.get("price_position_percentile")
                price_relative = competitive_analysis.get("price_relative_to_average")

                if price_position is not None and price_relative is not None:
                    if price_position < 25 and price_relative < -10:
                        recommendations.append("The current positioning as a value option with significantly lower pricing than competitors may be leveraged for market share growth, but consider whether it aligns with desired brand positioning and ensures adequate margins.")
                    elif price_position > 75 and price_relative > 10:
                        recommendations.append("The premium pricing relative to competitors requires clear value differentiation and consistent quality delivery to maintain. Ensure marketing communications emphasize differentiating factors that justify premium.")
                    else:
                        recommendations.append("The current pricing within the competitive range suggests opportunities for differentiation based on factors beyond price, including quality, service, features, or brand positioning.")

            # Add recommendation about cost structure if available
            cost_structure = pricing_data.get("current_pricing", {}).get("cost_structure", {})
            if cost_structure:
                margin_percentage = cost_structure.get("contribution_margin_percentage")
                breakeven = cost_structure.get("break_even_volume")

                if margin_percentage is not None and margin_percentage < 30:
                    recommendations.append(f"The relatively low contribution margin of {margin_percentage:.1f}% suggests a need to either increase prices or reduce variable costs to improve profitability and create buffer against volume fluctuations.")

                if breakeven is not None:
                    current_volume = pricing_data.get("current_pricing", {}).get("volume")
                    if current_volume and breakeven > current_volume * 0.8:
                        recommendations.append("The high break-even volume relative to current sales suggests vulnerability to downturns. Consider strategies to either increase prices, reduce fixed costs, or significantly increase volume to improve financial resilience.")

        else:
            # Basic recommendations with limited data
            if "competitive_analysis" in pricing_data:
                recommendations.append("Conduct comprehensive pricing analysis incorporating price elasticity data to determine optimal pricing based on profit, revenue, or market share objectives.")
                recommendations.append("Develop pricing strategy that balances competitive positioning with margin requirements and brand perception.")
            else:
                recommendations.append("Gather competitive pricing data and customer price sensitivity information to enable comprehensive pricing optimization analysis.")
                recommendations.append("Develop systematic approach to pricing decisions based on quantitative analysis rather than ad hoc adjustments.")

        return recommendations

# Example usage
if __name__ == "__main__":
    # This is just for demonstration purposes
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    agent = BusinessAgent()

    # Example business model analysis
    business_model_analysis = agent.analyze_business_model(
        industry="Technology",
        revenue_streams=["SaaS Subscriptions", "Professional Services", "Training"],
        cost_structure=["Engineering", "Sales & Marketing", "G&A"],
        key_resources=["Proprietary Technology", "Engineering Talent"],
        customer_segments=["Enterprise", "SMB"],
        competitive_advantage="Unique AI capabilities with patent-pending technology"
    )

    print("Business Model Analysis:", business_model_analysis)
