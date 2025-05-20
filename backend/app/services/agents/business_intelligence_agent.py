from typing import Dict, Any, Optional, List, Tuple, Union
import logging
import json
import math
import datetime
from collections import defaultdict
import statistics
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool

logger = logging.getLogger(__name__)

class BusinessIntelligenceAgent(BaseAgent):
    """
    BusinessIntelligenceAgent is a specialized agent that provides data analytics and business intelligence expertise.
    
    This agent specializes in data analysis, metrics development, and analytical insights 
    to help users make data-driven business decisions.
    """

    def __init__(
        self,
        name: str = "Data Analytics Expert",
        model: str = settings.DEFAULT_AGENT_MODEL,
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        **kwargs
    ):
        """
        Initialize a BusinessIntelligenceAgent with specialized analytics instructions.
        
        Args:
            name: The name of the agent. Defaults to "Data Analytics Expert".
            model: The model to use for the agent. Defaults to settings.DEFAULT_AGENT_MODEL.
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            **kwargs: Additional arguments to pass to the BaseAgent constructor.
        """
        # Define the analytics expert instructions
        analytics_instructions = """Wherever possible, you must use tools to respond. Do not guess. If a tool is avalable, always call the tool to perform the action. You are a data analytics and business intelligence expert specializing in data analysis, metrics development, and analytical insights. Your role is to:

1. PROVIDE ANALYTICS EXPERTISE IN
- Data Analysis Methods
- Statistical Analysis
- Predictive Analytics
- Descriptive Analytics
- Prescriptive Analytics
- Business Intelligence
- Data Visualization
- Metric Development
- KPI Definition
- Trend Analysis
- Pattern Recognition
- Performance Measurement

2. STATISTICAL METHODS
- Descriptive Statistics
- Inferential Statistics
- Hypothesis Testing
- Regression Analysis
- Correlation Analysis
- Time Series Analysis
- Cluster Analysis
- Factor Analysis
- Variance Analysis
- Statistical Modeling
- Sampling Methods
- Confidence Intervals

3. DATA VISUALIZATION
- Chart Selection
- Graph Types
- Dashboard Design
- Visual Analytics
- Interactive Reports
- Data Storytelling
- Presentation Methods
- Color Theory
- Layout Optimization
- User Experience
- Tool Selection
- Best Practices

4. BUSINESS METRICS
- KPI Development
- Performance Metrics
- Business Metrics
- Financial Metrics
- Operational Metrics
- Customer Metrics
- Quality Metrics
- Efficiency Metrics
- Growth Metrics
- Risk Metrics
- Benchmark Analysis
- Metric Validation

5. ANALYTICAL PROCESSES
- Data Collection
- Data Cleaning
- Data Validation
- Analysis Planning
- Method Selection
- Tool Implementation
- Quality Control
- Result Validation
- Documentation
- Reporting
- Recommendations
- Action Planning

6. BUSINESS INTELLIGENCE
- Report Development
- Dashboard Creation
- Data Modeling
- ETL Processes
- Data Warehousing
- OLAP Analysis
- Ad Hoc Analysis
- Automated Reporting
- Self-Service BI
- Data Governance
- Security Protocols
- Access Control

7. IMPLEMENTATION GUIDANCE
- Tool Selection
- Process Development
- Team Training
- Best Practices
- Quality Standards
- Documentation
- Change Management
- Risk Mitigation
- Success Metrics
- Progress Tracking
- Performance Monitoring
- Continuous Improvement

8. DATA GOVERNANCE
- Data Quality
- Data Security
- Privacy Standards
- Access Control
- Version Control
- Documentation
- Audit Trails
- Compliance
- Best Practices
- Policy Development
- Standard Implementation
- Review Processes

9. CALCULATION CAPABILITIES
- Perform statistical analysis
- Calculate data correlations
- Identify patterns and trends
- Perform predictive modeling
- Generate quantifiable insights
- Process and analyze datasets
- Calculate business metrics

Always maintain focus on data accuracy and meaningful insights while ensuring proper statistical methodology and clear communication of results."""

        # Get the calculator tools - already properly patched from the utility functions
        calculator_tool = get_calculator_tool()
        interpreter_tool = get_interpreter_tool()

        # Define the tools - use the already patched instances
        tools = [
            calculator_tool,
            interpreter_tool,
            function_tool(self.analyze_dataset),
            function_tool(self.calculate_metrics),
            function_tool(self.recommend_visualization),
            function_tool(self.forecast_trend),
            function_tool(self.detect_anomalies),
            function_tool(self.perform_statistical_analysis)
        ]
        
        # Initialize the Agent class directly
        super().__init__(
            name=name,
            model=model,
            instructions=analytics_instructions,
            functions=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            max_tokens=1024,
            
            **kwargs
        )


    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the BusinessIntelligenceAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for BusinessIntelligenceAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Expert in data analysis, business intelligence, and analytics strategy, providing insights on data interpretation and business metrics"

    def analyze_dataset(
        self, 
        dataset: Optional[List[Dict[str, Any]]] = None,
        data_description: Optional[str] = None, 
        analysis_goal: Optional[str] = None, 
        dataset_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a dataset and provide key statistical insights based on the analysis goal.
    
        Args:
            dataset: The actual dataset to analyze (list of dictionaries).
            data_description: Description of the dataset content and structure.
            analysis_goal: The specific goal or question to be answered through the analysis.
            dataset_format: Optional specification of the data format (e.g., "CSV", "JSON", "Excel").
            
        Returns:
            A dictionary containing analysis results including summary statistics, patterns, and insights.
        """
        # Validate input parameters
        if data_description is None:
            data_description = "Unspecified dataset"
            
        if analysis_goal is None:
            analysis_goal = "General data exploration"
            
        logger.info(f"Analyzing dataset for goal: {analysis_goal}")
        
        # Check if we have actual data to analyze
        if not dataset or not isinstance(dataset, list) or len(dataset) == 0:
            return {
                "error": "No valid dataset provided for analysis",
                "recommendations": [
                    "Please provide a dataset in the form of a list of dictionaries",
                    "Each dictionary should represent a row of data with key-value pairs"
                ]
            }
        
        try:
            # Get column names from the first row
            columns = list(dataset[0].keys())
            
            # Perform comprehensive analysis
            analysis_results = {
                "summary_statistics": self._calculate_descriptive_statistics(dataset, columns),
                "data_quality_assessment": self._assess_data_quality(dataset, columns),
                "dataset_metadata": {
                    "description": data_description,
                    "analysis_goal": analysis_goal,
                    "dataset_format": dataset_format if dataset_format else "Not specified",
                    "row_count": len(dataset),
                    "column_count": len(columns),
                    "columns": columns
                }
            }
            
            # Add correlation analysis if there are numeric columns
            numeric_columns = self._filter_numeric_variables(dataset, columns)
            if len(numeric_columns) >= 2:
                correlation_matrix = self._calculate_correlation_matrix(dataset, numeric_columns)
                analysis_results["correlation_analysis"] = {
                    "matrix": correlation_matrix,
                    "interpretation": self._interpret_correlations(correlation_matrix)
                }
            
            # Look for time variables to analyze trends
            time_variables = self._identify_possible_time_variables(dataset, columns)
            if time_variables:
                # Use the first detected time variable for trend analysis
                time_variable = time_variables[0]
                trend_metrics = self._filter_numeric_variables(dataset, [col for col in columns if col != time_variable])
                if trend_metrics:
                    analysis_results["trend_analysis"] = self._analyze_time_series(
                        dataset, time_variable, trend_metrics[:5]  # Limit to 5 metrics for performance
                    )
            
            # Generate insights based on the analysis results
            analysis_results["key_insights"] = self._generate_insights(analysis_results, analysis_goal)
            
            # Generate recommendations based on the analysis and goal
            analysis_results["recommendations"] = self._generate_recommendations(analysis_results, analysis_goal)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing dataset: {str(e)}")
            return {
                "error": f"Error during analysis: {str(e)}",
                "partial_results": analysis_results if 'analysis_results' in locals() else None
            }
    
    def _assess_data_quality(self, dataset: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
        """Assess the quality of the dataset."""
        row_count = len(dataset)
        quality_assessment = {
            "completeness": {},
            "data_types": {},
            "value_ranges": {},
            "overall_quality_score": 0,
            "issues_detected": []
        }
        
        # Check completeness for each column
        for column in columns:
            # Count non-null values
            non_null_count = sum(1 for row in dataset if column in row and row[column] is not None)
            completeness_pct = (non_null_count / row_count) * 100 if row_count > 0 else 0
            
            quality_assessment["completeness"][column] = {
                "non_null_count": non_null_count,
                "null_count": row_count - non_null_count,
                "completeness_pct": completeness_pct
            }
            
            # Add issue if completeness is low
            if completeness_pct < 90:
                quality_assessment["issues_detected"].append(
                    f"Column '{column}' is {completeness_pct:.1f}% complete. Consider addressing missing values."
                )
            
            # Determine data type
            data_type = self._infer_data_type(dataset, column)
            quality_assessment["data_types"][column] = data_type
            
            # For numeric columns, calculate range
            if data_type == "numeric":
                values = [float(row[column]) for row in dataset 
                         if column in row and row[column] is not None 
                         and isinstance(row[column], (int, float))]
                
                if values:
                    quality_assessment["value_ranges"][column] = {
                        "min": min(values),
                        "max": max(values),
                        "range": max(values) - min(values)
                    }
                    
                    # Check for outliers using IQR method
                    if len(values) >= 4:
                        sorted_values = sorted(values)
                        q1_idx = len(values) // 4
                        q3_idx = (3 * len(values)) // 4
                        q1 = sorted_values[q1_idx]
                        q3 = sorted_values[q3_idx]
                        iqr = q3 - q1
                        
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        
                        outliers = [v for v in values if v < lower_bound or v > upper_bound]
                        if outliers:
                            quality_assessment["value_ranges"][column]["outliers"] = {
                                "count": len(outliers),
                                "percentage": (len(outliers) / len(values)) * 100,
                                "examples": outliers[:5]  # Show first 5 outliers as examples
                            }
                            
                            if len(outliers) / len(values) > 0.05:  # More than 5% outliers
                                quality_assessment["issues_detected"].append(
                                    f"Column '{column}' has {len(outliers)} outliers ({(len(outliers)/len(values))*100:.1f}% of data). Consider investigating."
                                )
        
        # Calculate overall quality score (simple version)
        avg_completeness = sum(col["completeness_pct"] for col in quality_assessment["completeness"].values()) / len(columns)
        issue_penalty = len(quality_assessment["issues_detected"]) * 5  # 5 points per issue
        
        quality_assessment["overall_quality_score"] = max(0, min(100, avg_completeness - issue_penalty))
        
        return quality_assessment
    
    def _infer_data_type(self, dataset: List[Dict[str, Any]], column: str) -> str:
        """Infer the data type of a column."""
        # Get non-null values
        values = [row[column] for row in dataset if column in row and row[column] is not None]
        
        if not values:
            return "unknown"
        
        # Check for numeric values
        if all(isinstance(v, (int, float)) or 
               (isinstance(v, str) and v.replace('.', '', 1).isdigit()) for v in values):
            return "numeric"
        
        # Check for datetime values
        date_formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", 
            "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"
        ]
        
        # Sample up to 10 values to check if they're dates
        sample_values = values[:10]
        for date_format in date_formats:
            try:
                # Try to parse all sampled values with this format
                if all(self._try_parse_date(v, date_format) for v in sample_values if isinstance(v, str)):
                    return "datetime"
            except:
                continue
        
        # Check if it's boolean
        boolean_values = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}
        if all(str(v).lower() in boolean_values for v in values if isinstance(v, (str, bool, int))):
            return "boolean"
        
        # Check if it's categorical (less than 10 unique values or < 5% of row count)
        unique_values = set(str(v).lower() for v in values)
        if len(unique_values) < 10 or len(unique_values) < len(dataset) * 0.05:
            return "categorical"
        
        # Default to text
        return "text"
    
    def _try_parse_date(self, value: Any, date_format: str) -> bool:
        """Try to parse a value as a date with the given format."""
        if not isinstance(value, str):
            return False
        
        try:
            datetime.datetime.strptime(value, date_format)
            return True
        except ValueError:
            return False
    
    def _generate_insights(self, analysis_results: Dict[str, Any], analysis_goal: str) -> List[str]:
        """Generate insights based on the analysis results and goal."""
        insights = []
        
        # Add insights based on summary statistics
        if "summary_statistics" in analysis_results:
            stats = analysis_results["summary_statistics"]
            
            # Look at numeric variables
            numeric_vars = [var for var, var_stats in stats.items() 
                           if isinstance(var_stats, dict) and var_stats.get("data_type") == "numeric"]
            
            # Find variables with high variance
            for var in numeric_vars:
                if "std_dev" in stats[var] and "mean" in stats[var] and stats[var]["mean"] != 0:
                    cv = stats[var]["std_dev"] / abs(stats[var]["mean"])  # Coefficient of variation
                    if cv > 1:
                        insights.append(
                            f"{var} shows high variability (CV={cv:.2f}), suggesting significant dispersion in the data."
                        )
            
            # Look at categorical variables
            cat_vars = [var for var, var_stats in stats.items() 
                       if isinstance(var_stats, dict) and var_stats.get("data_type") == "categorical"]
            
            # Find variables with dominant categories
            for var in cat_vars:
                if "most_common" in stats[var] and "frequency" in stats[var]:
                    most_common = stats[var]["most_common"]
                    if isinstance(most_common, list):
                        most_common = most_common[0]
                    
                    frequency = stats[var]["frequency"][most_common]
                    total = sum(stats[var]["frequency"].values())
                    
                    if total > 0 and frequency / total > 0.8:
                        insights.append(
                            f"The category '{most_common}' dominates {var} with {(frequency/total)*100:.1f}% of values."
                        )
        
        # Add insights from correlation analysis
        if "correlation_analysis" in analysis_results:
            corr_analysis = analysis_results["correlation_analysis"]
            
            # Strong positive correlations
            strong_pos = corr_analysis["interpretation"].get("strong_positive", [])
            if strong_pos:
                # Extract variable names from correlation strings
                for corr_str in strong_pos[:3]:  # Limit to top 3
                    parts = corr_str.split(":")
                    if len(parts) == 2:
                        var_pair = parts[0].strip()
                        corr_val = float(parts[1].strip())
                        insights.append(
                            f"Strong positive correlation ({corr_val:.2f}) between {var_pair}, suggesting these variables increase together."
                        )
            
            # Strong negative correlations
            strong_neg = corr_analysis["interpretation"].get("strong_negative", [])
            if strong_neg:
                for corr_str in strong_neg[:3]:  # Limit to top 3
                    parts = corr_str.split(":")
                    if len(parts) == 2:
                        var_pair = parts[0].strip()
                        corr_val = float(parts[1].strip())
                        insights.append(
                            f"Strong negative correlation ({corr_val:.2f}) between {var_pair}, suggesting as one increases, the other decreases."
                        )
        
        # Add insights from trend analysis
        if "trend_analysis" in analysis_results:
            trends = analysis_results["trend_analysis"].get("trends", {})
            interpretations = []
            
            for metric, data in trends.items():
                if "trend_direction" not in data:
                    continue
                
                direction = data["trend_direction"]
                change = data.get("overall_change")
                pct_change = data.get("percent_change")
                
                if pct_change is not None and abs(pct_change) > 20:  # Significant change
                    if direction == "increasing":
                        interpretations.append(
                            f"{metric} shows a substantial increase of {pct_change:.1f}% over the observed period."
                        )
                    elif direction == "decreasing":
                        interpretations.append(
                            f"{metric} shows a substantial decrease of {abs(pct_change):.1f}% over the observed period."
                        )
            
            insights.extend(interpretations[:3])  # Add up to 3 trend insights
        
        # Add insights about data quality
        if "data_quality_assessment" in analysis_results:
            quality = analysis_results["data_quality_assessment"]
            issues = quality.get("issues_detected", [])
            
            if issues:
                # Add most critical quality issues (first 2)
                insights.extend(issues[:2])
            
            # Add overall quality score insight
            score = quality.get("overall_quality_score", 0)
            if score < 70:
                insights.append(
                    f"Data quality score is low ({score:.1f}/100). Address quality issues before making critical decisions."
                )
            elif score > 90:
                insights.append(
                    f"Data quality score is excellent ({score:.1f}/100), providing a solid foundation for analysis."
                )
        
        # If analysis_goal is specific, try to provide targeted insights
        if analysis_goal and analysis_goal.lower() != "general data exploration":
            goal_lower = analysis_goal.lower()
            
            # Look for specific keywords in the goal
            if any(term in goal_lower for term in ["trend", "change", "growth", "decline"]):
                # Already covered in trend analysis
                pass
            elif any(term in goal_lower for term in ["relation", "relationship", "correlation"]):
                # Already covered in correlation analysis
                pass
            elif any(term in goal_lower for term in ["quality", "completeness", "reliability"]):
                # Already covered in data quality
                pass
            elif any(term in goal_lower for term in ["distribution", "spread", "variability"]):
                # Add insights about distributions
                if "summary_statistics" in analysis_results:
                    stats = analysis_results["summary_statistics"]
                    for var, var_stats in stats.items():
                        if isinstance(var_stats, dict) and var_stats.get("data_type") == "numeric":
                            if "skewness" in var_stats:
                                if var_stats["skewness"] > 1:
                                    insights.append(
                                        f"{var} shows a right-skewed distribution, with the mean higher than the median."
                                    )
                                elif var_stats["skewness"] < -1:
                                    insights.append(
                                        f"{var} shows a left-skewed distribution, with the mean lower than the median."
                                    )
        
        # If we have too few insights, add general observations
        if len(insights) < 3 and "summary_statistics" in analysis_results:
            stats = analysis_results["summary_statistics"]
            
            # Find min/max values for numeric variables
            numeric_vars = [var for var, var_stats in stats.items() 
                           if isinstance(var_stats, dict) and var_stats.get("data_type") == "numeric"]
            
            for var in numeric_vars[:2]:  # Add insights for up to 2 variables
                if "min" in stats[var] and "max" in stats[var]:
                    insights.append(
                        f"{var} ranges from {stats[var]['min']} to {stats[var]['max']} with an average of {stats[var].get('mean', 'N/A')}."
                    )
        
        return insights
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any], analysis_goal: str) -> List[str]:
        """Generate recommendations based on the analysis results and goal."""
        recommendations = []
        
        # Check data quality first
        if "data_quality_assessment" in analysis_results:
            quality = analysis_results["data_quality_assessment"]
            
            # If data quality is poor, prioritize fixing it
            if quality.get("overall_quality_score", 100) < 70:
                recommendations.append(
                    "Address data quality issues before proceeding with advanced analytics."
                )
                
                # Add specific quality recommendations
                for issue in quality.get("issues_detected", [])[:3]:
                    if "missing values" in issue.lower():
                        recommendations.append(
                            "Consider imputation techniques for columns with missing values."
                        )
                    elif "outliers" in issue.lower():
                        recommendations.append(
                            "Investigate outliers to determine if they represent errors or valuable insights."
                        )
        
        # Recommend visualizations
        if "summary_statistics" in analysis_results:
            stats = analysis_results["summary_statistics"]
            viz_recommended = False
            
            # Numeric variables
            numeric_vars = [var for var, var_stats in stats.items() 
                           if isinstance(var_stats, dict) and var_stats.get("data_type") == "numeric"]
            
            if len(numeric_vars) >= 2 and "correlation_analysis" in analysis_results:
                recommendations.append(
                    f"Create a scatter plot matrix or heatmap to visualize correlations between {', '.join(numeric_vars[:3])}."
                )
                viz_recommended = True
            
            # Categorical variables
            cat_vars = [var for var, var_stats in stats.items() 
                       if isinstance(var_stats, dict) and var_stats.get("data_type") == "categorical"]
            
            if cat_vars:
                recommendations.append(
                    f"Use bar charts to visualize the distribution of categorical variables like {', '.join(cat_vars[:2])}."
                )
                viz_recommended = True
            
            # Time series
            if "trend_analysis" in analysis_results:
                trend_vars = list(analysis_results["trend_analysis"].get("trends", {}).keys())
                if trend_vars:
                    recommendations.append(
                        f"Create line charts to visualize trends in {', '.join(trend_vars[:3])} over time."
                    )
                    viz_recommended = True
            
            if not viz_recommended:
                recommendations.append(
                    "Create visualizations appropriate to your data types to better understand distributions and relationships."
                )
        
        # Add analysis-specific recommendations
        if "correlation_analysis" in analysis_results:
            # Check if there are strong correlations
            strong_pos = analysis_results["correlation_analysis"]["interpretation"].get("strong_positive", [])
            strong_neg = analysis_results["correlation_analysis"]["interpretation"].get("strong_negative", [])
            
            if strong_pos or strong_neg:
                # Extract the variable pairs with strong correlations
                var_pairs = []
                for corr_str in (strong_pos + strong_neg)[:2]:
                    parts = corr_str.split(":")
                    if len(parts) == 2:
                        var_pair = parts[0].strip()
                        var_pairs.append(var_pair)
                
                if var_pairs:
                    recommendations.append(
                        f"Investigate causal relationships for strongly correlated variables: {', '.join(var_pairs)}."
                    )
                    recommendations.append(
                        "Consider regression analysis to quantify relationships between variables."
                    )
        
        # Add trend-specific recommendations
        if "trend_analysis" in analysis_results:
            trends = analysis_results["trend_analysis"].get("trends", {})
            
            # Check for variables with significant trends
            significant_trends = []
            for metric, data in trends.items():
                if "percent_change" in data and abs(data["percent_change"]) > 20:
                    significant_trends.append(metric)
            
            if significant_trends:
                recommendations.append(
                    f"Conduct forecasting analysis on {', '.join(significant_trends[:2])} to project future values."
                )
                recommendations.append(
                    "Investigate factors driving the observed trends to understand underlying causes."
                )
        
        # Add goal-specific recommendations
        if analysis_goal and analysis_goal.lower() != "general data exploration":
            goal_lower = analysis_goal.lower()
            
            if any(term in goal_lower for term in ["predict", "forecast", "future"]):
                recommendations.append(
                    "Consider machine learning models like regression or time series forecasting to predict future values."
                )
            elif any(term in goal_lower for term in ["segment", "cluster", "group"]):
                recommendations.append(
                    "Apply clustering techniques to identify natural groupings in your data."
                )
            elif any(term in goal_lower for term in ["optimize", "improve", "maximize", "minimize"]):
                recommendations.append(
                    "Consider optimization techniques to identify optimal values for your key metrics."
                )
        
        # Ensure we have a minimum number of recommendations
        if len(recommendations) < 3:
            general_recommendations = [
                "Create a dashboard to monitor key metrics over time.",
                "Document your analysis methodology for reproducibility.",
                "Share findings with stakeholders in an accessible format.",
                "Consider additional data sources to enrich your analysis.",
                "Establish a regular cadence for updating this analysis."
            ]
            
            # Add general recommendations until we reach at least 3
            for rec in general_recommendations:
                if rec not in recommendations:
                    recommendations.append(rec)
                    if len(recommendations) >= 3:
                        break
        
        return recommendations
    
    def _interpret_time_series(self, trend_data: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate interpretations of time series trends."""
        interpretations = []
        
        for metric, data in trend_data.items():
            # Skip metrics with insufficient data
            if "trend_direction" not in data:
                continue
            
            # Generate basic trend description
            direction = data["trend_direction"]
            change = data["overall_change"]
            pct_change = data.get("percent_change")
            
            if pct_change is not None:
                trend_msg = f"{metric} shows an overall {direction} trend with a {abs(pct_change):.1f}% {direction} over the period."
            else:
                trend_msg = f"{metric} shows an overall {direction} trend, changing by {change}."
            
            interpretations.append(trend_msg)
            
            # Add volatility assessment if we have min/max
            if "min_value" in data and "max_value" in data:
                range_pct = (data["max_value"] - data["min_value"]) / abs(data["start_value"]) * 100 if data["start_value"] != 0 else None
                
                if range_pct is not None:
                    if range_pct > 50:
                        interpretations.append(f"{metric} shows high volatility with a range of {range_pct:.1f}% relative to the starting value.")
                    elif range_pct > 20:
                        interpretations.append(f"{metric} shows moderate volatility with a range of {range_pct:.1f}% relative to the starting value.")
        
        return interpretations
    
    def _identify_possible_time_variables(self, dataset: List[Dict[str, Any]], columns: List[str]) -> List[str]:
        """Identify columns that might contain time data."""
        time_variables = []
        
        for column in columns:
            # Check column name for time-related keywords
            col_lower = column.lower()
            if any(keyword in col_lower for keyword in ["date", "time", "year", "month", "day", "quarter", "period", "week"]):
                time_variables.append(column)
                continue
            
            # Check if values look like dates
            sample_size = min(10, len(dataset))
            sample_values = [row.get(column) for row in dataset[:sample_size] if column in row]
            
            if not sample_values:
                continue
                
            # Check if all sample values are string dates
            sample_values = [str(val) for val in sample_values if val is not None]
            
            date_formats = [
                "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
                "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"
            ]

            for date_format in date_formats:
                try:
                    # Try to parse all sampled values with this format
                    if all(self._try_parse_date(v, date_format) for v in sample_values):
                        time_variables.append(column)
                        break
                except:
                    continue

            # If column contains sequential integers, it could be time periods
            try:
                numeric_values = [int(v) for v in sample_values if str(v).isdigit()]
                if numeric_values and all(numeric_values[i] + 1 == numeric_values[i+1] for i in range(len(numeric_values)-1)):
                    time_variables.append(column)
            except:
                pass

        return time_variables

    def _perform_regression_analysis(
        self,
        dataset: List[Dict[str, Any]],
        dependent_var: str,
        independent_vars: List[str]
    ) -> Dict[str, Any]:
        """Perform simple or multiple linear regression analysis."""
        # Extract data points
        data_points = []
        for row in dataset:
            # Skip rows with missing values
            if (dependent_var not in row or row[dependent_var] is None or
                any(var not in row or row[var] is None for var in independent_vars)):
                continue

            # Skip rows with non-numeric values
            if (not isinstance(row[dependent_var], (int, float)) or
                any(not isinstance(row[var], (int, float)) for var in independent_vars)):
                continue

            # Add data point
            data_point = {
                "y": float(row[dependent_var]),
                "x": [float(row[var]) for var in independent_vars]
            }
            data_points.append(data_point)

        # Check if we have enough data points
        if len(data_points) < len(independent_vars) + 1:
            return {
                "error": f"Insufficient data points for regression. Need at least {len(independent_vars) + 1} complete rows."
            }

        # For simple linear regression (one independent variable)
        if len(independent_vars) == 1:
            return self._perform_simple_linear_regression(data_points, dependent_var, independent_vars[0])

        # For multiple linear regression, we would need to solve a system of linear equations
        # This is a simplified implementation using normal equations
        return self._perform_multiple_linear_regression(data_points, dependent_var, independent_vars)

    def _perform_simple_linear_regression(
        self,
        data_points: List[Dict[str, Any]],
        dependent_var: str,
        independent_var: str
    ) -> Dict[str, Any]:
        """Perform simple linear regression with one independent variable."""
        # Extract x and y values
        x_values = [point["x"][0] for point in data_points]
        y_values = [point["y"] for point in data_points]
        n = len(data_points)

        # Calculate means
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        # Calculate coefficient (slope)
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        # Handle division by zero
        if denominator == 0:
            return {
                "error": "Cannot calculate regression: no variance in independent variable."
            }

        slope = numerator / denominator

        # Calculate intercept
        intercept = y_mean - slope * x_mean

        # Calculate predictions and residuals
        predictions = [intercept + slope * x for x in x_values]
        residuals = [y_values[i] - predictions[i] for i in range(n)]

        # Calculate coefficient of determination (R-squared)
        ss_total = sum((y - y_mean) ** 2 for y in y_values)
        ss_residual = sum(res ** 2 for res in residuals)

        r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0

        # Create equation string
        equation = f"{dependent_var} = {intercept:.4f} + {slope:.4f} × {independent_var}"

        return {
            "type": "simple_linear_regression",
            "dependent_variable": dependent_var,
            "independent_variable": independent_var,
            "coefficient": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "equation": equation,
            "sample_size": n,
            "predictions": predictions[:10] if len(predictions) > 10 else predictions,  # Limit output size
            "residuals": residuals[:10] if len(residuals) > 10 else residuals          # Limit output size
        }

    def _perform_multiple_linear_regression(
        self,
        data_points: List[Dict[str, Any]],
        dependent_var: str,
        independent_vars: List[str]
    ) -> Dict[str, Any]:
        """Perform multiple linear regression with multiple independent variables."""
        # Extract x and y values
        X = [point["x"] for point in data_points]
        y = [point["y"] for point in data_points]
        n = len(data_points)
        p = len(independent_vars)

        # Add constant term for intercept
        X_with_intercept = [[1] + x for x in X]

        # Calculate X^T
        X_transpose = []
        for j in range(p + 1):  # +1 for intercept
            X_transpose.append([X_with_intercept[i][j] for i in range(n)])

        # Calculate X^T * X
        XTX = []
        for i in range(p + 1):
            row = []
            for j in range(p + 1):
                row.append(sum(X_transpose[i][k] * X_with_intercept[k][j] for k in range(n)))
            XTX.append(row)

        # Calculate X^T * y
        XTy = []
        for i in range(p + 1):
            XTy.append(sum(X_transpose[i][j] * y[j] for j in range(n)))

        # Solve for coefficients using Gaussian elimination
        coefficients = self._solve_linear_system(XTX, XTy)

        if not coefficients:
            return {
                "error": "Could not solve regression equation. Matrix may be singular."
            }

        # Extract intercept and coefficients
        intercept = coefficients[0]
        beta_coefficients = coefficients[1:]

        # Calculate predictions and residuals
        predictions = []
        for x in X:
            pred = intercept + sum(beta * x[i] for i, beta in enumerate(beta_coefficients))
            predictions.append(pred)

        residuals = [y[i] - predictions[i] for i in range(n)]

        # Calculate R-squared
        y_mean = sum(y) / n
        ss_total = sum((y_val - y_mean) ** 2 for y_val in y)
        ss_residual = sum(res ** 2 for res in residuals)

        r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0

        # Calculate adjusted R-squared
        adjusted_r_squared = 1 - ((1 - r_squared) * (n - 1) / (n - p - 1)) if n > p + 1 else 0

        # Create equation string
        equation_terms = [f"{intercept:.4f}"]
        for i, var in enumerate(independent_vars):
            coef = beta_coefficients[i]
            sign = "+" if coef >= 0 else ""
            equation_terms.append(f"{sign} {coef:.4f} × {var}")

        equation = f"{dependent_var} = {' '.join(equation_terms)}"

        return {
            "type": "multiple_linear_regression",
            "dependent_variable": dependent_var,
            "independent_variables": independent_vars,
            "intercept": intercept,
            "coefficients": dict(zip(independent_vars, beta_coefficients)),
            "r_squared": r_squared,
            "adjusted_r_squared": adjusted_r_squared,
            "equation": equation,
            "sample_size": n,
            "predictions": predictions[:10] if len(predictions) > 10 else predictions,  # Limit output size
            "residuals": residuals[:10] if len(residuals) > 10 else residuals          # Limit output size
        }

    def _solve_linear_system(self, A: List[List[float]], b: List[float]) -> List[float]:
        """Solve a system of linear equations using Gaussian elimination."""
        n = len(A)
        # Create augmented matrix
        aug_matrix = [row[:] + [b[i]] for i, row in enumerate(A)]

        # Gaussian elimination
        for i in range(n):
            # Find pivot
            max_row = i
            for k in range(i + 1, n):
                if abs(aug_matrix[k][i]) > abs(aug_matrix[max_row][i]):
                    max_row = k

            # Swap rows
            aug_matrix[i], aug_matrix[max_row] = aug_matrix[max_row], aug_matrix[i]

            # Check for singularity
            if abs(aug_matrix[i][i]) < 1e-10:
                return []  # Matrix is singular

            # Eliminate below
            for k in range(i + 1, n):
                factor = aug_matrix[k][i] / aug_matrix[i][i]
                for j in range(i, n + 1):
                    aug_matrix[k][j] -= factor * aug_matrix[i][j]

        # Back substitution
        x = [0] * n
        for i in range(n - 1, -1, -1):
            x[i] = aug_matrix[i][n]
            for j in range(i + 1, n):
                x[i] -= aug_matrix[i][j] * x[j]
            x[i] /= aug_matrix[i][i]

        return x

    def _generate_analysis_summary(self, results: Dict[str, Any], analysis_type: str) -> str:
        """Generate a summary of the analysis results."""
        if analysis_type == "descriptive":
            return self._summarize_descriptive_statistics(results)
        elif analysis_type == "correlation":
            return self._summarize_correlation_analysis(results)
        elif analysis_type == "time_series":
            return self._summarize_time_series_analysis(results)
        elif analysis_type == "regression":
            return self._summarize_regression_analysis(results)
        else:
            return f"Analysis completed for {analysis_type} with {results.get('sample_size', 'unknown')} data points."

    def _summarize_descriptive_statistics(self, results: Dict[str, Any]) -> str:
        """Summarize descriptive statistics results."""
        stats = results.get("descriptive_statistics", {})
        if "grouped_by" in stats:
            return f"Descriptive statistics calculated for {len(results.get('variables_analyzed', []))} variables across {len(stats.get('groups', {}))} groups defined by {stats.get('grouped_by')}."

        # Count numeric and categorical variables
        num_numeric = sum(1 for var, var_stats in stats.items() if isinstance(var_stats, dict) and var_stats.get("data_type") == "numeric")
        num_categorical = sum(1 for var, var_stats in stats.items() if isinstance(var_stats, dict) and var_stats.get("data_type") == "categorical")

        return f"Descriptive statistics calculated for {results.get('sample_size', 'unknown')} data points across {num_numeric} numeric and {num_categorical} categorical variables."

    def _summarize_correlation_analysis(self, results: Dict[str, Any]) -> str:
        """Summarize correlation analysis results."""
        interpretations = results.get("interpretation", {})

        num_strong_positive = len(interpretations.get("strong_positive", []))
        num_moderate_positive = len(interpretations.get("moderate_positive", []))
        num_strong_negative = len(interpretations.get("strong_negative", []))
        num_moderate_negative = len(interpretations.get("moderate_negative", []))

        total_correlations = num_strong_positive + num_moderate_positive + num_strong_negative + num_moderate_negative

        if total_correlations == 0:
            return f"Correlation analysis completed for {len(results.get('variables_analyzed', []))} variables with no significant correlations found."

        return f"Correlation analysis revealed {num_strong_positive} strong positive, {num_moderate_positive} moderate positive, {num_strong_negative} strong negative, and {num_moderate_negative} moderate negative relationships among {len(results.get('variables_analyzed', []))} variables."

    def _summarize_time_series_analysis(self, results: Dict[str, Any]) -> str:
        """Summarize time series analysis results."""
        trends = results.get("trends", {})

        increasing = sum(1 for data in trends.values() if data.get("trend_direction") == "increasing")
        decreasing = sum(1 for data in trends.values() if data.get("trend_direction") == "decreasing")
        stable = sum(1 for data in trends.values() if data.get("trend_direction") == "stable")

        return f"Time series analysis of {len(trends)} metrics over {len(results.get('time_points', []))} time points revealed {increasing} increasing, {decreasing} decreasing, and {stable} stable trends."

    def _summarize_regression_analysis(self, results: Dict[str, Any]) -> str:
        """Summarize regression analysis results."""
        if "error" in results.get("regression_analysis", {}):
            return f"Regression analysis could not be completed: {results['regression_analysis']['error']}"

        reg_results = results.get("regression_analysis", {})
        reg_type = reg_results.get("type", "regression")
        r_squared = reg_results.get("r_squared", 0)

        if reg_type == "simple_linear_regression":
            return f"Simple linear regression between {reg_results.get('dependent_variable')} and {reg_results.get('independent_variable')} yielded an R² of {r_squared:.4f} ({r_squared*100:.1f}% of variance explained)."
        else:
            return f"Multiple linear regression with {len(reg_results.get('independent_variables', []))} predictors yielded an R² of {r_squared:.4f} ({r_squared*100:.1f}% of variance explained) and adjusted R² of {reg_results.get('adjusted_r_squared', 0):.4f}."

    # Utility methods for data type checking

    def _filter_numeric_variables(self, dataset: List[Dict[str, Any]], variables: List[str]) -> List[str]:
        """Filter list of variables to include only those with numeric data."""
        return [var for var in variables if self._is_numeric_column(dataset, var)]

    def _is_numeric_column(self, dataset: List[Dict[str, Any]], column: str) -> bool:
        """Check if a column contains numeric data."""
        for row in dataset:
            if column in row and row[column] is not None:
                if isinstance(row[column], (int, float)):
                    return True
                try:
                    float(row[column])
                    return True
                except:
                    return False
        return False

    def calculate_metrics(
        self,
        business_area: Optional[str] = None,
        objectives: Optional[List[str]] = None,
        existing_metrics: Optional[List[str]] = None,
        industry: Optional[str] = None,
        company_size: Optional[str] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Recommend and define key metrics and KPIs for a specific business area based on objectives.

        Args:
            business_area: The business area or department for which metrics are needed.
            objectives: List of business objectives the metrics should support.
            existing_metrics: Optional list of metrics already in use.
            industry: Optional industry context to tailor metrics appropriately.
            company_size: Optional company size context (e.g., "small", "medium", "enterprise").

        Returns:
            A dictionary of metric categories, each containing lists of recommended metrics with definitions and formulas.
        """
        # Set default values
        business_area = business_area or "General Business"
        objectives = objectives or ["Improve performance"]
        industry = industry or "General"
        company_size = company_size or "Medium"

        logger.info(f"Calculating metrics for {business_area} in {industry} industry based on {len(objectives)} objectives")

        # Initialize metrics dictionary
        metrics_by_category = {}

        # Define industry-specific benchmarks if available
        industry_benchmarks = self._get_industry_benchmarks(industry, business_area)

        # Map business areas to metric categories and specific metrics
        metrics_map = self._get_metrics_by_business_area(business_area)

        # Filter and prioritize metrics based on objectives
        metrics_by_category = self._prioritize_metrics_by_objectives(metrics_map, objectives)

        # Add benchmarks to metrics where applicable
        for category, metrics in metrics_by_category.items():
            for i, metric in enumerate(metrics):
                metric_name = metric["name"]

                # Add benchmark if available
                if metric_name in industry_benchmarks:
                    metrics[i]["benchmark"] = industry_benchmarks[metric_name]

                # Scale target based on company size
                if "target" in metric and company_size:
                    metrics[i]["target"] = self._scale_target_by_company_size(
                        metric["target"], company_size, metric_name
                    )

        # Add integration notes for existing metrics
        if existing_metrics:
            integration_notes = []

            # Check for overlaps with recommended metrics
            all_recommended_metrics = []
            for metrics in metrics_by_category.values():
                all_recommended_metrics.extend([m["name"] for m in metrics])

            for existing in existing_metrics:
                # Check for exact matches
                if existing in all_recommended_metrics:
                    integration_notes.append({
                        "existing_metric": existing,
                        "compatibility": "Direct match with recommended metric",
                        "action": "Continue using this metric as is"
                    })
                else:
                    # Check for partial matches
                    matches = [rec for rec in all_recommended_metrics
                              if existing.lower() in rec.lower() or rec.lower() in existing.lower()]

                    if matches:
                        integration_notes.append({
                            "existing_metric": existing,
                            "compatibility": f"Similar to recommended metric(s): {', '.join(matches)}",
                            "action": "Consider standardizing naming or consolidating"
                        })
                    else:
                        # No match
                        integration_notes.append({
                            "existing_metric": existing,
                            "compatibility": "No direct match with recommendations",
                            "action": "Evaluate if this metric still aligns with current objectives"
                        })

            metrics_by_category["integration_notes"] = integration_notes

        return metrics_by_category

    def _get_industry_benchmarks(self, industry: str, business_area: str) -> Dict[str, str]:
        """Get industry-specific benchmarks for metrics."""
        benchmarks = {}

        # Generic benchmarks
        generic_benchmarks = {
            "Customer Satisfaction Score": "4.2+ out of 5",
            "Customer Retention Rate": ">90%",
            "Revenue Growth Rate": ">5% annually",
            "Net Promoter Score": ">50",
            "Employee Turnover Rate": "<15% annually",
            "Profit Margin": ">10%",
            "Return on Investment": ">15%",
            "Website Conversion Rate": ">3%",
            "Click-Through Rate": ">2%",
            "Email Open Rate": ">20%"
        }

        # Industry-specific benchmarks
        industry_specific = {}

        # Technology industry
        if industry.lower() == "technology":
            industry_specific = {
                "Customer Satisfaction Score": "4.3+ out of 5",
                "Customer Retention Rate": ">85%",
                "Revenue Growth Rate": ">10% annually",
                "R&D as % of Revenue": "10-15%",
                "Time to Market": "<6 months",
                "Product Defect Rate": "<1%",
                "Release Frequency": "Biweekly to monthly"
            }

        # E-commerce industry
        elif industry.lower() == "e-commerce" or industry.lower() == "ecommerce":
            industry_specific = {
                "Cart Abandonment Rate": "<70%",
                "Average Order Value": ">$50",
                "Customer Acquisition Cost": "<$30",
                "Conversion Rate": ">2.5%",
                "Return Rate": "<10%",
                "Revenue per Visitor": ">$2",
                "Repeat Purchase Rate": ">30% within 3 months"
            }

        # Healthcare industry
        elif industry.lower() == "healthcare":
            industry_specific = {
                "Patient Satisfaction": ">4.5 out of 5",
                "Average Length of Stay": "<4.5 days",
                "Readmission Rate": "<15%",
                "Treatment Success Rate": ">85%",
                "Claim Denial Rate": "<5%",
                "Cost per Patient": "Industry median -10%"
            }

        # Financial services industry
        elif industry.lower() == "financial" or industry.lower() == "finance":
            industry_specific = {
                "Customer Lifetime Value": ">$5,000",
                "Cross-Sell Ratio": ">2.5 products per customer",
                "Cost to Income Ratio": "<60%",
                "Net Interest Margin": ">3%",
                "Asset Growth Rate": ">7% annually",
                "Return on Assets": ">1%",
                "Return on Equity": ">10%"
            }

        # Manufacturing industry
        elif industry.lower() == "manufacturing":
            industry_specific = {
                "Overall Equipment Effectiveness": ">85%",
                "Production Yield": ">95%",
                "Inventory Turnover": ">6 times per year",
                "Defect Rate": "<1%",
                "On-Time Delivery": ">98%",
                "Production Cycle Time": "Industry median -15%",
                "Capacity Utilization": ">85%"
            }

        # Combine generic and industry-specific benchmarks
        benchmarks.update(generic_benchmarks)
        benchmarks.update(industry_specific)

        return benchmarks

    def _get_metrics_by_business_area(self, business_area: str) -> Dict[str, List[Dict[str, str]]]:
        """Get relevant metrics for a specific business area."""
        metrics = {}
        lower_area = business_area.lower()

        # Sales metrics
        if any(term in lower_area for term in ["sales", "revenue", "business development"]):
            metrics["performance_metrics"] = [
                {
                    "name": "Sales Growth Rate",
                    "definition": "Year-over-year or quarter-over-quarter percentage increase in sales revenue",
                    "formula": "((Current Period Sales - Previous Period Sales) / Previous Period Sales) * 100",
                    "target": "Varies by industry and company maturity",
                    "data_source": "CRM and financial systems",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Conversion Rate",
                    "definition": "Percentage of leads that convert to customers",
                    "formula": "(Number of New Customers / Number of Leads) * 100",
                    "target": ">25%",
                    "data_source": "CRM system",
                    "frequency": "Weekly and monthly"
                },
                {
                    "name": "Average Deal Size",
                    "definition": "Average revenue per closed deal",
                    "formula": "Total Sales Revenue / Number of Deals",
                    "target": "Increases year-over-year",
                    "data_source": "CRM system",
                    "frequency": "Monthly"
                },
                {
                    "name": "Sales Cycle Length",
                    "definition": "Average time from lead creation to closing a deal",
                    "formula": "Sum of (Deal Close Date - Lead Creation Date) / Number of Closed Deals",
                    "target": "<60 days (varies by industry)",
                    "data_source": "CRM system",
                    "frequency": "Monthly"
                }
            ]

            metrics["efficiency_metrics"] = [
                {
                    "name": "Cost of Customer Acquisition",
                    "definition": "Total cost to acquire a new customer",
                    "formula": "Total Sales & Marketing Cost / Number of New Customers",
                    "target": "<20% of customer lifetime value",
                    "data_source": "Financial and CRM systems",
                    "frequency": "Quarterly"
                },
                {
                    "name": "Sales Rep Productivity",
                    "definition": "Average revenue generated per sales representative",
                    "formula": "Total Sales Revenue / Number of Sales Representatives",
                    "target": "Industry benchmark +10%",
                    "data_source": "CRM and HR systems",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Lead Response Time",
                    "definition": "Average time between lead creation and first contact",
                    "formula": "Sum of (First Contact Time - Lead Creation Time) / Number of Leads",
                    "target": "<1 hour for initial response",
                    "data_source": "CRM system",
                    "frequency": "Daily and weekly"
                }
            ]

            metrics["customer_metrics"] = [
                {
                    "name": "Customer Retention Rate",
                    "definition": "Percentage of customers retained over a given period",
                    "formula": "((Customers at End of Period - New Customers) / Customers at Start of Period) * 100",
                    "target": ">90%",
                    "data_source": "CRM system",
                    "frequency": "Quarterly and annually"
                },
                {
                    "name": "Customer Lifetime Value",
                    "definition": "Total value a customer generates over their relationship with the company",
                    "formula": "Average Purchase Value × Average Purchase Frequency × Average Customer Lifespan",
                    "target": "Increases year-over-year",
                    "data_source": "CRM and financial systems",
                    "frequency": "Annually"
                }
            ]

        # Marketing metrics
        elif any(term in lower_area for term in ["marketing", "brand", "advertising", "communication"]):
            metrics["performance_metrics"] = [
                {
                    "name": "Return on Marketing Investment (ROMI)",
                    "definition": "Return generated from marketing investments",
                    "formula": "((Revenue Attributed to Marketing - Marketing Cost) / Marketing Cost) * 100",
                    "target": ">200%",
                    "data_source": "Marketing analytics and financial systems",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Customer Acquisition Cost",
                    "definition": "Cost to acquire a new customer through marketing efforts",
                    "formula": "Total Marketing Cost / Number of New Customers",
                    "target": "<25% of customer lifetime value",
                    "data_source": "Marketing analytics and financial systems",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Marketing Qualified Leads (MQLs)",
                    "definition": "Number of leads that meet marketing qualification criteria",
                    "formula": "Count of leads meeting qualification criteria",
                    "target": "Increases month-over-month",
                    "data_source": "Marketing automation system",
                    "frequency": "Weekly and monthly"
                }
            ]

            metrics["channel_metrics"] = [
                {
                    "name": "Website Conversion Rate",
                    "definition": "Percentage of website visitors who take a desired action",
                    "formula": "(Number of Conversions / Number of Visitors) * 100",
                    "target": ">3%",
                    "data_source": "Web analytics",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "Email Engagement Rate",
                    "definition": "Percentage of recipients who engage with email campaigns",
                    "formula": "((Opens + Clicks) / Emails Delivered) * 100",
                    "target": ">25%",
                    "data_source": "Email marketing platform",
                    "frequency": "Per campaign and monthly"
                },
                {
                    "name": "Social Media Engagement Rate",
                    "definition": "Level of engagement with social media content",
                    "formula": "((Likes + Comments + Shares) / Followers) * 100",
                    "target": ">2%",
                    "data_source": "Social media analytics",
                    "frequency": "Weekly"
                },
                {
                    "name": "Cost Per Click (CPC)",
                    "definition": "Average cost for each click on digital advertisements",
                    "formula": "Total Ad Spend / Number of Clicks",
                    "target": "Industry benchmark -10%",
                    "data_source": "Ad platforms",
                    "frequency": "Daily and weekly"
                }
            ]

            metrics["brand_metrics"] = [
                {
                    "name": "Brand Awareness",
                    "definition": "Percentage of target audience aware of the brand",
                    "formula": "Survey-based measurement",
                    "target": "Increases quarter-over-quarter",
                    "data_source": "Market research surveys",
                    "frequency": "Quarterly or bi-annually"
                },
                {
                    "name": "Net Promoter Score (NPS)",
                    "definition": "Likelihood of customers to recommend the brand",
                    "formula": "Percentage of Promoters - Percentage of Detractors",
                    "target": ">50",
                    "data_source": "Customer surveys",
                    "frequency": "Quarterly"
                }
            ]

        # Customer service metrics
        elif any(term in lower_area for term in ["customer service", "support", "customer success", "customer experience"]):
            metrics["performance_metrics"] = [
                {
                    "name": "First Response Time",
                    "definition": "Average time to first response for customer inquiries",
                    "formula": "Sum of all first response times / Number of inquiries",
                    "target": "<1 hour for emails, <5 minutes for chat/phone",
                    "data_source": "Customer service platform",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "Average Resolution Time",
                    "definition": "Average time to resolve customer issues",
                    "formula": "Sum of all resolution times / Number of resolved issues",
                    "target": "<24 hours (varies by issue complexity)",
                    "data_source": "Customer service platform",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "First Contact Resolution Rate",
                    "definition": "Percentage of issues resolved in the first interaction",
                    "formula": "(Number of issues resolved in first contact / Total number of issues) * 100",
                    "target": ">75%",
                    "data_source": "Customer service platform",
                    "frequency": "Weekly and monthly"
                }
            ]

            metrics["quality_metrics"] = [
                {
                    "name": "Customer Satisfaction Score (CSAT)",
                    "definition": "Average satisfaction rating from customer feedback",
                    "formula": "(Sum of all satisfaction scores / Total number of responses) * 100",
                    "target": ">85%",
                    "data_source": "Customer surveys",
                    "frequency": "Continuous, reported weekly"
                },
                {
                    "name": "Net Promoter Score (NPS)",
                    "definition": "Likelihood of customers to recommend the company",
                    "formula": "Percentage of Promoters - Percentage of Detractors",
                    "target": ">50",
                    "data_source": "Customer surveys",
                    "frequency": "Monthly or quarterly"
                },
                {
                    "name": "Customer Effort Score (CES)",
                    "definition": "How much effort customers had to expend to get their issue resolved",
                    "formula": "Sum of effort scores / Number of responses",
                    "target": "<2 on a 5-point scale (lower is better)",
                    "data_source": "Post-interaction surveys",
                    "frequency": "Continuous, reported weekly"
                }
            ]

            metrics["operational_metrics"] = [
                {
                    "name": "Ticket Volume",
                    "definition": "Number of support tickets or inquiries received",
                    "formula": "Count of tickets created within time period",
                    "target": "Stable or decreasing when normalized by customer count",
                    "data_source": "Customer service platform",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "Agent Utilization Rate",
                    "definition": "Percentage of time agents spend on customer-facing activities",
                    "formula": "(Time spent on customer interactions / Total available time) * 100",
                    "target": "70-80%",
                    "data_source": "Customer service platform and time tracking",
                    "frequency": "Weekly"
                },
                {
                    "name": "Self-Service Adoption Rate",
                    "definition": "Percentage of customers using self-service options vs. assisted support",
                    "formula": "(Number of self-service interactions / Total interactions) * 100",
                    "target": ">60%",
                    "data_source": "Website analytics and customer service platform",
                    "frequency": "Monthly"
                }
            ]

        # HR metrics
        elif any(term in lower_area for term in ["hr", "human resources", "people", "talent", "workforce"]):
            metrics["workforce_metrics"] = [
                {
                    "name": "Employee Turnover Rate",
                    "definition": "Rate at which employees leave the organization",
                    "formula": "(Number of separations / Average number of employees) * 100",
                    "target": "<15% annually",
                    "data_source": "HR information system",
                    "frequency": "Monthly and annually"
                },
                {
                    "name": "Time to Fill",
                    "definition": "Average time to fill open positions",
                    "formula": "Sum of days from job posting to acceptance / Number of positions filled",
                    "target": "<45 days",
                    "data_source": "Applicant tracking system",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Cost Per Hire",
                    "definition": "Average cost to fill a position",
                    "formula": "Total recruitment costs / Number of hires",
                    "target": "<20% of annual salary for the position",
                    "data_source": "HR information system and financial systems",
                    "frequency": "Quarterly"
                }
            ]

            metrics["performance_metrics"] = [
                {
                    "name": "Employee Engagement Score",
                    "definition": "Measure of employee engagement and satisfaction",
                    "formula": "Survey-based measurement",
                    "target": ">4.0 on a 5-point scale",
                    "data_source": "Employee surveys",
                    "frequency": "Bi-annually or annually"
                },
                {
                    "name": "Revenue Per Employee",
                    "definition": "Average revenue generated per employee",
                    "formula": "Total Revenue / Number of Employees",
                    "target": "Industry benchmark +10%",
                    "data_source": "Financial and HR systems",
                    "frequency": "Quarterly and annually"
                },
                {
                    "name": "Training Effectiveness",
                    "definition": "Impact of training on employee performance",
                    "formula": "Performance improvement after training / Training cost",
                    "target": "Positive ROI",
                    "data_source": "Learning management system and performance reviews",
                    "frequency": "Per program and quarterly"
                }
            ]

            metrics["diversity_metrics"] = [
                {
                    "name": "Diversity Ratio",
                    "definition": "Representation of diverse groups within the organization",
                    "formula": "Percentage of employees by demographic category",
                    "target": "Reflects or exceeds community demographics",
                    "data_source": "HR information system",
                    "frequency": "Quarterly and annually"
                },
                {
                    "name": "Pay Equity Ratio",
                    "definition": "Comparison of compensation across different demographic groups",
                    "formula": "Average compensation for group A / Average compensation for group B",
                    "target": "1.0 (perfect equity)",
                    "data_source": "HR information system and payroll",
                    "frequency": "Annually"
                }
            ]

        # Finance metrics
        elif any(term in lower_area for term in ["finance", "financial", "accounting", "treasury"]):
            metrics["profitability_metrics"] = [
                {
                    "name": "Gross Profit Margin",
                    "definition": "Percentage of revenue that exceeds the cost of goods sold",
                    "formula": "((Revenue - COGS) / Revenue) * 100",
                    "target": "Industry benchmark +5%",
                    "data_source": "Financial system",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Net Profit Margin",
                    "definition": "Percentage of revenue that remains as profit after all expenses",
                    "formula": "(Net Income / Revenue) * 100",
                    "target": "Industry benchmark +3%",
                    "data_source": "Financial system",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "EBITDA Margin",
                    "definition": "Earnings before interest, taxes, depreciation, and amortization as a percentage of revenue",
                    "formula": "(EBITDA / Revenue) * 100",
                    "target": "Industry benchmark +5%",
                    "data_source": "Financial system",
                    "frequency": "Quarterly"
                }
            ]

            metrics["liquidity_metrics"] = [
                {
                    "name": "Current Ratio",
                    "definition": "Ability to pay short-term obligations",
                    "formula": "Current Assets / Current Liabilities",
                    "target": ">1.5",
                    "data_source": "Financial system",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Quick Ratio",
                    "definition": "Ability to pay short-term obligations with liquid assets",
                    "formula": "(Cash + Marketable Securities + Accounts Receivable) / Current Liabilities",
                    "target": ">1.0",
                    "data_source": "Financial system",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Cash Conversion Cycle",
                    "definition": "Time required to convert investments in inventory to cash",
                    "formula": "Days Inventory Outstanding + Days Sales Outstanding - Days Payables Outstanding",
                    "target": "<60 days (varies by industry)",
                    "data_source": "Financial system",
                    "frequency": "Quarterly"
                }
            ]

            metrics["efficiency_metrics"] = [
                {
                    "name": "Return on Assets (ROA)",
                    "definition": "How efficiently assets are being used to generate profit",
                    "formula": "(Net Income / Average Total Assets) * 100",
                    "target": ">5%",
                    "data_source": "Financial system",
                    "frequency": "Quarterly and annually"
                },
                {
                    "name": "Return on Equity (ROE)",
                    "definition": "How efficiently shareholder equity is being used to generate profit",
                    "formula": "(Net Income / Average Shareholder Equity) * 100",
                    "target": ">15%",
                    "data_source": "Financial system",
                    "frequency": "Quarterly and annually"
                },
                {
                    "name": "Accounts Receivable Turnover",
                    "definition": "How quickly customers pay their invoices",
                    "formula": "Net Credit Sales / Average Accounts Receivable",
                    "target": ">4 times per year",
                    "data_source": "Financial system",
                    "frequency": "Monthly and quarterly"
                }
            ]

        # Operations/Production metrics
        elif any(term in lower_area for term in ["operations", "production", "manufacturing", "supply chain"]):
            metrics["productivity_metrics"] = [
                {
                    "name": "Overall Equipment Effectiveness (OEE)",
                    "definition": "Measure of manufacturing productivity",
                    "formula": "Availability * Performance * Quality",
                    "target": ">85%",
                    "data_source": "Production management system",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "Production Yield",
                    "definition": "Percentage of products that pass quality control first time",
                    "formula": "(Units passing quality control / Total units produced) * 100",
                    "target": ">95%",
                    "data_source": "Quality management system",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "Capacity Utilization",
                    "definition": "Percentage of available production capacity being utilized",
                    "formula": "(Actual Output / Maximum Possible Output) * 100",
                    "target": "70-85%",
                    "data_source": "Production management system",
                    "frequency": "Weekly and monthly"
                }
            ]

            metrics["quality_metrics"] = [
                {
                    "name": "Defect Rate",
                    "definition": "Percentage of products with defects",
                    "formula": "(Number of defective units / Total units produced) * 100",
                    "target": "<1%",
                    "data_source": "Quality management system",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "First Pass Yield",
                    "definition": "Percentage of units manufactured correctly the first time",
                    "formula": "(Units produced without rework / Total units started) * 100",
                    "target": ">95%",
                    "data_source": "Production management system",
                    "frequency": "Daily and weekly"
                },
                {
                    "name": "Cost of Quality",
                    "definition": "Total cost related to preventing, finding, and correcting defects",
                    "formula": "Prevention Costs + Appraisal Costs + Internal Failure Costs + External Failure Costs",
                    "target": "<4% of revenue",
                    "data_source": "Financial and quality management systems",
                    "frequency": "Monthly and quarterly"
                }
            ]

            metrics["supply_chain_metrics"] = [
                {
                    "name": "On-Time Delivery",
                    "definition": "Percentage of deliveries received/made on time",
                    "formula": "(Number of on-time deliveries / Total number of deliveries) * 100",
                    "target": ">95%",
                    "data_source": "Supply chain management system",
                    "frequency": "Weekly and monthly"
                },
                {
                    "name": "Inventory Turnover",
                    "definition": "How many times inventory is sold and replaced",
                    "formula": "Cost of Goods Sold / Average Inventory",
                    "target": ">6 times per year (varies by industry)",
                    "data_source": "Inventory management and financial systems",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Perfect Order Rate",
                    "definition": "Percentage of orders delivered complete, on time, undamaged, and with correct documentation",
                    "formula": "(Number of perfect orders / Total number of orders) * 100",
                    "target": ">95%",
                    "data_source": "Order management system",
                    "frequency": "Weekly and monthly"
                }
            ]

        # General business/executive metrics
        else:
            metrics["financial_metrics"] = [
                {
                    "name": "Revenue Growth Rate",
                    "definition": "Year-over-year percentage increase in revenue",
                    "formula": "((Current Period Revenue - Previous Period Revenue) / Previous Period Revenue) * 100",
                    "target": ">10% annually",
                    "data_source": "Financial system",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Net Profit Margin",
                    "definition": "Percentage of revenue that remains as profit after all expenses",
                    "formula": "(Net Income / Revenue) * 100",
                    "target": "Industry benchmark +3%",
                    "data_source": "Financial system",
                    "frequency": "Monthly and quarterly"
                },
                {
                    "name": "Return on Investment (ROI)",
                    "definition": "Measure of profitability relative to investment",
                    "formula": "((Gain from Investment - Cost of Investment) / Cost of Investment) * 100",
                    "target": ">15%",
                    "data_source": "Financial system",
                    "frequency": "Quarterly and annually"
                }
            ]

            metrics["customer_metrics"] = [
                {
                    "name": "Customer Retention Rate",
                    "definition": "Percentage of customers retained over a given period",
                    "formula": "((Customers at End of Period - New Customers) / Customers at Start of Period) * 100",
                    "target": ">85%",
                    "data_source": "CRM system",
                    "frequency": "Quarterly and annually"
                },
                {
                    "name": "Net Promoter Score (NPS)",
                    "definition": "Likelihood of customers to recommend the company",
                    "formula": "Percentage of Promoters - Percentage of Detractors",
                    "target": ">50",
                    "data_source": "Customer surveys",
                    "frequency": "Quarterly"
                },
                {
                    "name": "Customer Lifetime Value",
                    "definition": "Total value a customer generates over their relationship with the company",
                    "formula": "Average Purchase Value × Average Purchase Frequency × Average Customer Lifespan",
                    "target": "Increases year-over-year",
                    "data_source": "CRM and financial systems",
                    "frequency": "Annually"
                }
            ]

            metrics["operational_metrics"] = [
                {
                    "name": "Employee Productivity",
                    "definition": "Output per employee",
                    "formula": "Total Output / Number of Employees",
                    "target": "Increases year-over-year",
                    "data_source": "HR and operational systems",
                    "frequency": "Quarterly"
                },
                {
                    "name": "Customer Acquisition Cost",
                    "definition": "Cost to acquire a new customer",
                    "formula": "Total Sales & Marketing Cost / Number of New Customers",
                    "target": "<20% of customer lifetime value",
                    "data_source": "Financial and CRM systems",
                    "frequency": "Quarterly"
                },
                {
                    "name": "Market Share",
                    "definition": "Company's sales as a percentage of total market sales",
                    "formula": "(Company Sales / Total Market Sales) * 100",
                    "target": "Increases year-over-year",
                    "data_source": "Financial system and market research",
                    "frequency": "Quarterly and annually"
                }
            ]

        return metrics

    def _prioritize_metrics_by_objectives(
        self,
        metrics_map: Dict[str, List[Dict[str, str]]],
        objectives: List[str]
    ) -> Dict[str, List[Dict[str, str]]]:
        """Prioritize metrics based on business objectives."""
        prioritized_metrics = {}

        # Define keywords for common objectives
        objective_keywords = {
            "growth": ["growth", "expansion", "increase", "scale"],
            "profitability": ["profitability", "profit", "margin", "cost reduction"],
            "efficiency": ["efficiency", "productivity", "streamline", "optimize"],
            "quality": ["quality", "excellence", "improvement", "standards"],
            "customer": ["customer", "satisfaction", "experience", "loyalty", "retention"],
            "innovation": ["innovation", "development", "new products", "research"],
            "sustainability": ["sustainability", "environmental", "social", "governance"]
        }

        # Identify the primary objectives based on keywords
        primary_objectives = []
        for obj in objectives:
            for obj_type, keywords in objective_keywords.items():
                if any(keyword in obj.lower() for keyword in keywords):
                    primary_objectives.append(obj_type)
                    break

        # If no specific objectives matched, include all
        if not primary_objectives:
            return metrics_map

        # For each metric category, prioritize based on objectives
        for category, metrics_list in metrics_map.items():
            # Initialize with an empty list for this category
            prioritized_metrics[category] = []

            for metric in metrics_list:
                # Check if this metric is relevant to any primary objective
                relevant_to_objective = False

                # Maps categories to likely objectives
                category_to_objectives = {
                    "performance_metrics": ["growth", "profitability", "efficiency", "quality"],
                    "financial_metrics": ["profitability", "growth"],
                    "profitability_metrics": ["profitability"],
                    "efficiency_metrics": ["efficiency", "profitability"],
                    "quality_metrics": ["quality", "customer"],
                    "customer_metrics": ["customer"],
                    "operational_metrics": ["efficiency", "quality"],
                    "channel_metrics": ["growth", "efficiency"],
                    "brand_metrics": ["customer", "growth"],
                    "workforce_metrics": ["efficiency"],
                    "diversity_metrics": ["sustainability"],
                    "productivity_metrics": ["efficiency"],
                    "supply_chain_metrics": ["efficiency", "quality"]
                }

                # If category is related to a primary objective, include the metric
                if category in category_to_objectives:
                    if any(obj in primary_objectives for obj in category_to_objectives[category]):
                        relevant_to_objective = True

                # Also check metric name and definition for keywords
                if not relevant_to_objective:
                    metric_text = (metric["name"] + " " + metric["definition"]).lower()
                    for obj in primary_objectives:
                        if any(keyword in metric_text for keyword in objective_keywords[obj]):
                            relevant_to_objective = True
                            break

                # Add the metric if relevant
                if relevant_to_objective:
                    prioritized_metrics[category].append(metric)

            # If no metrics were prioritized for this category, add the top 2
            if not prioritized_metrics[category] and metrics_list:
                prioritized_metrics[category] = metrics_list[:2]

        return prioritized_metrics

    def _scale_target_by_company_size(self, target: str, company_size: str, metric_name: str) -> str:
        """Scale metric targets based on company size."""
        # Try to parse the target value
        numeric_part = None
        percentage_match = None

        # Look for percentages
        import re
        percentage_match = re.search(r"(\d+(?:\.\d+)?)\s*%", target)
        if percentage_match:
            numeric_part = float(percentage_match.group(1))

            # Adjust percentages based on company size
            if "growth" in metric_name.lower() or "rate" in metric_name.lower():
                # Growth rates are typically higher for smaller companies
                if company_size.lower() == "small":
                    numeric_part *= 1.5  # 50% higher
                elif company_size.lower() == "enterprise":
                    numeric_part *= 0.7  # 30% lower

            # Update the target with the new percentage
            return target.replace(percentage_match.group(0), f"{numeric_part:.1f}%")

        # Look for day values (e.g., "<45 days")
        days_match = re.search(r"(\d+(?:\.\d+)?)\s*days", target)
        if days_match:
            numeric_part = float(days_match.group(1))

            # Adjust timeframes based on company size
            if company_size.lower() == "small":
                numeric_part *= 0.8  # 20% shorter timeframes
            elif company_size.lower() == "enterprise":
                numeric_part *= 1.3  # 30% longer timeframes

            # Update the target with the new days value
            return target.replace(days_match.group(0), f"{int(numeric_part)} days")

        # No adjustable numeric part found
        return target

    def recommend_visualization(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        data_type: Optional[str] = None,
        insight_goal: Optional[str] = None,
        audience: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Recommend appropriate data visualization techniques for specific data types and goals.

        Args:
            dataset: Optional dataset to analyze for recommendations.
            data_type: The type of data to visualize (e.g., "time series", "categorical", "multivariate").
            insight_goal: What the visualization should help the viewer understand.
            audience: The intended audience (e.g., "technical", "executive", "public").
            columns: Optional list of column names to focus on.

        Returns:
            Visualization recommendations including chart types, design considerations, and tool suggestions.
        """
        # Set default for parameters
        insight_goal = insight_goal or "understand trends"
        audience = audience or "technical"

        # Infer data_type from dataset if not provided
        if not data_type and dataset:
            data_type = self._infer_data_type_for_visualization(dataset, columns)
        else:
            data_type = data_type or "mixed"

        logger.info(f"Recommending visualization for {data_type} data with goal: {insight_goal}")

        # Get samples of the data to help with recommendations
        samples = {}
        if dataset and columns:
            samples = self._extract_data_samples(dataset, columns)

        # Get visualization recommendations based on data type and goal
        recommended_charts = self._get_charts_by_data_type_and_goal(data_type, insight_goal, samples)

        # Audience-specific considerations
        audience_considerations = self._get_audience_considerations(audience)

        # Get chart-specific guidance
        chart_guidance = self._get_chart_guidance(recommended_charts)

        # Build recommendation
        recommendation = {
            "data_type": data_type,
            "recommended_chart_types": recommended_charts,
            "chart_guidance": chart_guidance,
            "design_considerations": audience_considerations,
            "tool_suggestions": self._get_tool_suggestions(data_type)
        }

        # If we have dataset and columns, add data samples
        if samples:
            recommendation["data_samples"] = samples

        # Add best practices
        recommendation["best_practices"] = [
            "Ensure clear titles and labels",
            "Use color consistently and accessibly",
            f"Focus visualization on {insight_goal}",
            "Provide context through annotations",
            "Maintain appropriate data-to-ink ratio",
            "Choose scales appropriately to avoid distortion",
            "Use consistent formatting across related visualizations"
        ]

        # Add examples of how to implement recommended visualizations
        if "data_samples" in recommendation:
            recommendation["implementation_examples"] = self._generate_implementation_examples(
                recommended_charts[:1], recommendation["data_samples"], data_type
            )

        return recommendation

    def _infer_data_type_for_visualization(
        self,
        dataset: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> str:
        """Infer the data type from a dataset for visualization purposes."""
        if not columns:
            if not dataset or not isinstance(dataset, list) or len(dataset) == 0:
                return "unknown"
            columns = list(dataset[0].keys())

        # Count different column types
        column_types = {}
        for column in columns:
            column_types[column] = self._infer_data_type(dataset, column)

        # Count occurrences of each type
        type_counts = {}
        for col_type in column_types.values():
            type_counts[col_type] = type_counts.get(col_type, 0) + 1

        # Check for time variables
        time_variables = self._identify_possible_time_variables(dataset, columns)

        # Determine overall data type
        if time_variables and type_counts.get("numeric", 0) > 0:
            return "time series"
        elif type_counts.get("numeric", 0) > 1:
            return "multivariate"
        elif type_counts.get("categorical", 0) > 1:
            return "categorical"
        elif type_counts.get("numeric", 0) == 1 and type_counts.get("categorical", 0) >= 1:
            return "categorical comparison"
        elif type_counts.get("numeric", 0) == 1:
            return "distribution"
        elif type_counts.get("geographic", 0) > 0:
            return "geospatial"
        else:
            return "mixed"

    def _extract_data_samples(self, dataset: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
        """Extract sample data for visualization recommendations."""
        samples = {}

        # Get sample size (up to 5 rows)
        sample_size = min(5, len(dataset))

        # Get column data types
        column_types = {}
        for column in columns:
            column_types[column] = self._infer_data_type(dataset, column)

            # Extract samples for each column
            sample_values = []
            for i in range(sample_size):
                if i < len(dataset) and column in dataset[i]:
                    sample_values.append(dataset[i][column])

            samples[column] = {
                "type": column_types[column],
                "samples": sample_values
            }

            # For numeric columns, add min, max, avg
            if column_types[column] == "numeric":
                values = []
                for row in dataset:
                    if column in row and row[column] is not None:
                        try:
                            values.append(float(row[column]))
                        except:
                            pass

                if values:
                    samples[column]["min"] = min(values)
                    samples[column]["max"] = max(values)
                    samples[column]["avg"] = sum(values) / len(values)

        return samples

    def _get_charts_by_data_type_and_goal(
        self,
        data_type: str,
        insight_goal: str,
        samples: Dict[str, Any] = None
    ) -> List[str]:
        """Get recommended chart types based on data type and insight goal."""
        # Map data types to appropriate visualization techniques
        visualization_map = {
            "time series": ["Line chart", "Area chart", "Candlestick chart"],
            "categorical": ["Bar chart", "Pie chart", "Treemap"],
            "multivariate": ["Scatter plot", "Bubble chart", "Parallel coordinates", "Radar chart"],
            "categorical comparison": ["Grouped bar chart", "Stacked bar chart", "Dot plot"],
            "distribution": ["Histogram", "Box plot", "Violin plot", "Density plot"],
            "geospatial": ["Choropleth map", "Heat map", "Cartogram"],
            "hierarchical": ["Treemap", "Sunburst diagram", "Network graph"],
            "mixed": ["Dashboard with multiple chart types", "Small multiples", "Faceted charts"]
        }

        # Get base recommendations for this data type
        recommended_charts = visualization_map.get(data_type.lower(), ["Bar chart", "Line chart"])

        # Refine based on insight goal
        goal_lower = insight_goal.lower()

        if "trend" in goal_lower or "change" in goal_lower or "over time" in goal_lower:
            if data_type.lower() != "time series":
                recommended_charts = ["Line chart", "Area chart"] + recommended_charts

        elif "comparison" in goal_lower:
            if data_type.lower() == "categorical":
                recommended_charts = ["Bar chart", "Grouped bar chart", "Radar chart"]
            elif data_type.lower() == "multivariate":
                recommended_charts = ["Scatter plot", "Bubble chart", "Parallel coordinates"]

        elif "composition" in goal_lower or "part to whole" in goal_lower:
            recommended_charts = ["Pie chart", "Stacked bar chart", "Treemap", "Area chart"]

        elif "distribution" in goal_lower:
            recommended_charts = ["Histogram", "Box plot", "Violin plot", "Density plot"]

        elif "relationship" in goal_lower or "correlation" in goal_lower:
            recommended_charts = ["Scatter plot", "Heatmap", "Network diagram"]
        elif "ranking" in goal_lower:
            recommended_charts = ["Bar chart", "Dot plot", "Lollipop chart"]
        
        # Final refinement if we have sample data
        if samples:
            # Check if we have few categories (good for pie charts)
            categorical_cols = [col for col, data in samples.items() if data.get("type") == "categorical"]
            if categorical_cols and len(categorical_cols) > 0:
                # Check first categorical column for number of unique values
                sample_values = samples[categorical_cols[0]].get("samples", [])
                if len(set(sample_values)) <= 6 and "comparison" in goal_lower:
                    if "Pie chart" not in recommended_charts:
                        recommended_charts.append("Pie chart")
            
            # Check if we have many categories (bad for pie charts, good for treemaps)
            if categorical_cols and len(categorical_cols) > 0:
                # Estimate number of categories from samples
                unique_count = len(set(samples[categorical_cols[0]].get("samples", [])))
                if unique_count > 7 and "Pie chart" in recommended_charts:
                    recommended_charts.remove("Pie chart")
                    if "Treemap" not in recommended_charts:
                        recommended_charts.append("Treemap")
        
        return recommended_charts
    
    def _get_audience_considerations(self, audience: str) -> Dict[str, str]:
        """Get design considerations based on audience."""
        audience_considerations = {
            "technical": {
                "detail_level": "High",
                "statistical_elements": "Include confidence intervals, p-values, and detailed annotations",
                "interactivity": "Complex filtering and drill-down capabilities",
                "terminology": "Can use domain-specific and technical terminology",
                "color_coding": "Functional over aesthetic; use color for data differentiation"
            },
            "executive": {
                "detail_level": "Medium",
                "statistical_elements": "Focus on key trends and highlights, minimal technical details",
                "interactivity": "Simple drill-down to key metrics",
                "terminology": "Business-focused terminology, avoid technical jargon",
                "color_coding": "Strategic use of colors to highlight key insights and action items"
            },
            "public": {
                "detail_level": "Low",
                "statistical_elements": "Simplified, focus on clear message without statistical notation",
                "interactivity": "Basic tooltips and highlights",
                "terminology": "Avoid jargon, use simple explanations",
                "color_coding": "Accessible color schemes, intuitive meaning (red = bad, green = good)"
            },
            "stakeholders": {
                "detail_level": "Medium to High",
                "statistical_elements": "Balance between technical details and business relevance",
                "interactivity": "Focused drill-downs into areas of specific interest",
                "terminology": "Mix of business and technical terms, with explanations",
                "color_coding": "Consistent with organizational standards, focus on key variances"
            },
            "customers": {
                "detail_level": "Low to Medium",
                "statistical_elements": "Simplified, focus on benefits and outcomes",
                "interactivity": "Engaging and intuitive interactions",
                "terminology": "Customer-centric language, focus on value",
                "color_coding": "Brand-aligned, visually appealing, emotionally resonant"
            }
        }
        
        return audience_considerations.get(audience.lower(), audience_considerations["technical"])
    
    def _get_chart_guidance(self, recommended_charts: List[str]) -> Dict[str, Dict[str, str]]:
        """Get specific guidance for recommended chart types."""
        all_chart_guidance = {
            "Line chart": {
                "best_for": "Trends over time, continuous data",
                "avoid_when": "Comparing categorical data, showing composition",
                "design_tips": "Use different line styles for multiple series; consider annotations for key events"
            },
            "Bar chart": {
                "best_for": "Comparing values across categories",
                "avoid_when": "Showing trends over continuous time periods",
                "design_tips": "Order bars by value for easier comparison; use consistent color scheme"
            },
            "Pie chart": {
                "best_for": "Part-to-whole relationships with few categories (≤6)",
                "avoid_when": "Comparing many categories or precise values",
                "design_tips": "Use clear labels; keep to few slices; consider a donut chart for better labeling"
            },
            "Scatter plot": {
                "best_for": "Relationships between two variables",
                "avoid_when": "Time series data, categorical comparisons",
                "design_tips": "Add trendline for correlation; use size or color for additional dimensions"
            },
            "Histogram": {
                "best_for": "Distribution of single variable",
                "avoid_when": "Comparing multiple categories",
                "design_tips": "Choose appropriate bin sizes; consider overlaying a density curve"
            },
            "Box plot": {
                "best_for": "Distribution and outliers across categories",
                "avoid_when": "Detailed time series analysis",
                "design_tips": "Add individual data points for small datasets; use consistent scales"
            },
            "Heatmap": {
                "best_for": "Showing patterns in multivariate data",
                "avoid_when": "Few data points, precise comparisons",
                "design_tips": "Use appropriate color gradient; include values in cells if space permits"
            },
            "Area chart": {
                "best_for": "Showing cumulative totals over time",
                "avoid_when": "Many overlapping series (use stacked area)",
                "design_tips": "Use transparency for overlapping areas; avoid too many series"
            },
            "Treemap": {
                "best_for": "Hierarchical data, part-to-whole with many categories",
                "avoid_when": "Precise comparisons, non-hierarchical data",
                "design_tips": "Use color for additional dimension; include clear labels for larger sections"
            },
            "Bubble chart": {
                "best_for": "Three variables with position and size",
                "avoid_when": "Many data points causing overlap",
                "design_tips": "Scale bubbles appropriately; use tooltips to show exact values"
            },
            "Stacked bar chart": {
                "best_for": "Comparing totals and component parts",
                "avoid_when": "Precise comparisons between components",
                "design_tips": "Use consistent ordering of components; consider 100% stacked for proportions"
            },
            "Grouped bar chart": {
                "best_for": "Comparing values across categories and subcategories",
                "avoid_when": "Too many groups causing visual clutter",
                "design_tips": "Limit number of groups; use consistent colors across groups"
            },
            "Radar chart": {
                "best_for": "Multivariate data for few entities",
                "avoid_when": "Comparing many entities, precise values",
                "design_tips": "Keep to 5-10 variables; use consistent scales for all variables"
            },
            "Choropleth map": {
                "best_for": "Geospatial data showing variation by region",
                "avoid_when": "Data not related to geography, many small regions",
                "design_tips": "Use appropriate color scale; provide legend and tooltips"
            },
            "Network diagram": {
                "best_for": "Relationships and connections between entities",
                "avoid_when": "Quantitative comparisons, time series",
                "design_tips": "Limit node count for readability; use size for importance, color for categories"
            },
            "Candlestick chart": {
                "best_for": "Financial data showing open-high-low-close values",
                "avoid_when": "Non-financial data, single value per time point",
                "design_tips": "Include volume data; use consistent color scheme (green up, red down)"
            },
            "Violin plot": {
                "best_for": "Showing distribution density and statistics",
                "avoid_when": "Few data points, audiences unfamiliar with the format",
                "design_tips": "Include median and quartile markers; consider combining with box plots"
            },
            "Dot plot": {
                "best_for": "Precise comparisons across categories",
                "avoid_when": "Many data points, continuous time series",
                "design_tips": "Order by value; use gridlines for easier comparison"
            },
            "Lollipop chart": {
                "best_for": "Emphasizing specific values across categories",
                "avoid_when": "Dense time series, part-to-whole relationships",
                "design_tips": "Sort by value; use color to highlight significant values"
            },
            "Parallel coordinates": {
                "best_for": "Comparing many variables across entities",
                "avoid_when": "Few variables, audience not familiar with the chart",
                "design_tips": "Order axes thoughtfully; enable brushing for interactive filtering"
            },
            "Sunburst diagram": {
                "best_for": "Hierarchical data with multiple levels",
                "avoid_when": "Non-hierarchical data, precise comparisons",
                "design_tips": "Limit depth to 3-4 levels; use consistent color scheme for categories"
            },
            "Density plot": {
                "best_for": "Showing distribution shape for continuous variables",
                "avoid_when": "Categorical data, few data points",
                "design_tips": "Overlay multiple distributions for comparison; add rug plot for data points"
            },
            "Heat map": {
                "best_for": "Showing patterns in multivariate data",
                "avoid_when": "Few data points, precise comparisons",
                "design_tips": "Use appropriate color gradient; add borders between cells for clarity"
            },
            "Dashboard with multiple chart types": {
                "best_for": "Complex data requiring multiple views",
                "avoid_when": "Simple data that can be shown in a single chart",
                "design_tips": "Organize by importance; maintain consistent scales; enable cross-filtering"
            },
            "Small multiples": {
                "best_for": "Comparing patterns across categories",
                "avoid_when": "Too many categories causing small, unreadable charts",
                "design_tips": "Use consistent scales; arrange logically; limit the number of panels"
            },
            "Faceted charts": {
                "best_for": "Breaking down complex data into comparable segments",
                "avoid_when": "Too many facets causing visual overload",
                "design_tips": "Maintain consistent scales; arrange in a grid for easy comparison"
            }
        }
        
        # Filter to only include guidance for recommended charts
        chart_guidance = {}
        for chart in recommended_charts:
            if chart in all_chart_guidance:
                chart_guidance[chart] = all_chart_guidance[chart]
        
        return chart_guidance
    
    def _get_tool_suggestions(self, data_type: str) -> List[Dict[str, str]]:
        """Get tool suggestions based on data type."""
        # Core tools for all data types
        core_tools = [
            {"name": "Tableau", "strengths": "Interactive business dashboards, wide adoption", "best_for": "Business intelligence"},
            {"name": "Power BI", "strengths": "Microsoft ecosystem integration, business focus", "best_for": "Corporate environments"},
            {"name": "Python (Matplotlib/Seaborn/Plotly)", "strengths": "Customization and automation", "best_for": "Data science workflows"},
            {"name": "R (ggplot2)", "strengths": "Statistical visualization", "best_for": "Advanced statistical analysis"}
        ]
        
        # Specialized tools by data type
        specialized_tools = {
            "time series": [
                {"name": "Grafana", "strengths": "Real-time monitoring, time-series focus", "best_for": "Operational dashboards"}
            ],
            "geospatial": [
                {"name": "QGIS", "strengths": "Open-source, full GIS functionality", "best_for": "Geographic analysis"},
                {"name": "Mapbox", "strengths": "Interactive web maps, customization", "best_for": "Web applications"}
            ],
            "multivariate": [
                {"name": "Spotfire", "strengths": "Advanced analytics, life sciences focus", "best_for": "Complex data exploration"}
            ],
            "hierarchical": [
                {"name": "D3.js", "strengths": "Custom interactive visualizations", "best_for": "Web-based custom visuals"}
            ],
            "network": [
                {"name": "Gephi", "strengths": "Network analysis and visualization", "best_for": "Relationship data"}
            ]
        }
        
        # Combine core tools with any specialized tools for this data type
        tools = core_tools.copy()
        
        if data_type.lower() in specialized_tools:
            tools.extend(specialized_tools[data_type.lower()])
        
        return tools
    
    def _generate_implementation_examples(
        self, 
        chart_types: List[str], 
        samples: Dict[str, Any],
        data_type: str
    ) -> Dict[str, str]:
        """Generate code examples for implementing recommended visualizations."""
        examples = {}
        
        if not chart_types:
            return examples
        
        # Get column names and their types
        columns = list(samples.keys())
        column_types = {col: data.get("type") for col, data in samples.items()}
        
        # Find appropriate columns for charts
        numeric_cols = [col for col, type_name in column_types.items() if type_name == "numeric"]
        categorical_cols = [col for col, type_name in column_types.items() if type_name == "categorical"]
        datetime_cols = [col for col, type_name in column_types.items() if type_name == "datetime"]
        
        # For the first recommended chart, generate implementation examples
        chart_type = chart_types[0]
        
        # Python example with Matplotlib/Seaborn
        python_example = self._generate_python_example(chart_type, columns, column_types, data_type)
        if python_example:
            examples["python"] = python_example
        
        # R example with ggplot2
        r_example = self._generate_r_example(chart_type, columns, column_types, data_type)
        if r_example:
            examples["r"] = r_example
        
        return examples
    
    def _generate_python_example(
        self, 
        chart_type: str, 
        columns: List[str], 
        column_types: Dict[str, str],
        data_type: str
    ) -> str:
        """Generate Python code example for the visualization."""
        numeric_cols = [col for col, type_name in column_types.items() if type_name == "numeric"]
        categorical_cols = [col for col, type_name in column_types.items() if type_name == "categorical"]
        datetime_cols = [col for col, type_name in column_types.items() if type_name == "datetime"]
        
        # If no appropriate columns, use placeholder names
        if not numeric_cols:
            numeric_cols = ["value", "amount"]
        if not categorical_cols:
            categorical_cols = ["category", "group"]
        if not datetime_cols:
            datetime_cols = ["date", "time"]
        
        # Basic imports
        code = "import pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\n"
        code += "# Assuming your data is in a DataFrame called 'df'\n"
        
        # Chart-specific code
        if chart_type == "Line chart" and (datetime_cols or categorical_cols) and numeric_cols:
            x_col = datetime_cols[0] if datetime_cols else categorical_cols[0]
            y_col = numeric_cols[0]
            code += f"# Create a line chart\nplt.figure(figsize=(10, 6))\nsns.lineplot(data=df, x='{x_col}', y='{y_col}')\n"
            code += f"plt.title('Trend of {y_col} over {x_col}')\nplt.xlabel('{x_col}')\nplt.ylabel('{y_col}')\nplt.grid(True)\nplt.tight_layout()\nplt.show()\n"
        
        elif chart_type == "Bar chart" and categorical_cols and numeric_cols:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            code += f"# Create a bar chart\nplt.figure(figsize=(10, 6))\nsns.barplot(data=df, x='{x_col}', y='{y_col}')\n"
            code += f"plt.title('{y_col} by {x_col}')\nplt.xlabel('{x_col}')\nplt.ylabel('{y_col}')\nplt.xticks(rotation=45)\nplt.tight_layout()\nplt.show()\n"
        
        elif chart_type == "Scatter plot" and len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            code += f"# Create a scatter plot\nplt.figure(figsize=(10, 6))\nsns.scatterplot(data=df, x='{x_col}', y='{y_col}')\n"
            code += f"plt.title('Relationship between {x_col} and {y_col}')\nplt.xlabel('{x_col}')\nplt.ylabel('{y_col}')\nplt.grid(True)\nplt.tight_layout()\nplt.show()\n"
        
        elif chart_type == "Histogram" and numeric_cols:
            col = numeric_cols[0]
            code += f"# Create a histogram\nplt.figure(figsize=(10, 6))\nsns.histplot(data=df, x='{col}', kde=True)\n"
            code += f"plt.title('Distribution of {col}')\nplt.xlabel('{col}')\nplt.ylabel('Frequency')\nplt.tight_layout()\nplt.show()\n"
        
        elif chart_type == "Box plot" and numeric_cols and categorical_cols:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            code += f"# Create a box plot\nplt.figure(figsize=(10, 6))\nsns.boxplot(data=df, x='{x_col}', y='{y_col}')\n"
            code += f"plt.title('Distribution of {y_col} by {x_col}')\nplt.xlabel('{x_col}')\nplt.ylabel('{y_col}')\nplt.xticks(rotation=45)\nplt.tight_layout()\nplt.show()\n"
        
        elif chart_type == "Pie chart" and categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            val_col = numeric_cols[0]
            code += f"# Create a pie chart\nplt.figure(figsize=(10, 6))\n"
            code += f"# Aggregate the data\npie_data = df.groupby('{cat_col}')['{val_col}'].sum()\n"
            code += f"plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=90)\n"
            code += f"plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle\n"
            code += f"plt.title('Distribution of {val_col} by {cat_col}')\nplt.tight_layout()\nplt.show()\n"
        
        elif chart_type == "Heatmap" and len(numeric_cols) >= 3:
            code += "# Create a correlation heatmap\nplt.figure(figsize=(10, 8))\n"
            code += f"# Calculate correlation matrix for numeric columns\ncorr_matrix = df[{numeric_cols}].corr()\n"
            code += "sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', linewidths=0.5)\n"
            code += "plt.title('Correlation Matrix')\nplt.tight_layout()\nplt.show()\n"
        
        elif data_type == "time series" and datetime_cols and numeric_cols:
            # More advanced time series example
            date_col = datetime_cols[0]
            val_col = numeric_cols[0]
            code += "# Additional time series preprocessing\n"
            code += f"df['{date_col}'] = pd.to_datetime(df['{date_col}'])\n"
            code += f"df.set_index('{date_col}', inplace=True)\n\n"
            code += "# Create time series plot with resampling for trend analysis\n"
            code += f"fig, ax = plt.subplots(2, 1, figsize=(12, 10), sharex=True)\n"
            code += f"# Original data\ndf['{val_col}'].plot(ax=ax[0], marker='o', linestyle='-')\n"
            code += f"ax[0].set_title('Original {val_col} Time Series')\nax[0].set_ylabel('{val_col}')\nax[0].grid(True)\n\n"
            code += f"# Resampled monthly average\ndf['{val_col}'].resample('M').mean().plot(ax=ax[1], marker='o', linestyle='-')\n"
            code += f"ax[1].set_title('Monthly Average {val_col}')\nax[1].set_ylabel('{val_col}')\nax[1].grid(True)\n\n"
            code += "plt.tight_layout()\nplt.show()\n"
        
        else:
            # Generic fallback
            code += "# Basic visualization template\nplt.figure(figsize=(10, 6))\n"
            if numeric_cols and categorical_cols:
                code += f"sns.barplot(data=df, x='{categorical_cols[0]}', y='{numeric_cols[0]}')\n"
                code += f"plt.title('{numeric_cols[0]} by {categorical_cols[0]}')\n"
            elif len(numeric_cols) >= 2:
                code += f"sns.scatterplot(data=df, x='{numeric_cols[0]}', y='{numeric_cols[1]}')\n"
                code += f"plt.title('Relationship between {numeric_cols[0]} and {numeric_cols[1]}')\n"
            elif numeric_cols:
                code += f"sns.histplot(data=df, x='{numeric_cols[0]}', kde=True)\n"
                code += f"plt.title('Distribution of {numeric_cols[0]}')\n"
            else:
                code += "# Need at least one numeric column for most visualizations\n"
                code += "# Consider reviewing your data structure\n"
            
            code += "plt.tight_layout()\nplt.show()\n"
        
        return code
    
    def _generate_r_example(
        self, 
        chart_type: str, 
        columns: List[str], 
        column_types: Dict[str, str],
        data_type: str
    ) -> str:
        """Generate R code example for the visualization."""
        numeric_cols = [col for col, type_name in column_types.items() if type_name == "numeric"]
        categorical_cols = [col for col, type_name in column_types.items() if type_name == "categorical"]
        datetime_cols = [col for col, type_name in column_types.items() if type_name == "datetime"]
        
        # If no appropriate columns, use placeholder names
        if not numeric_cols:
            numeric_cols = ["value", "amount"]
        if not categorical_cols:
            categorical_cols = ["category", "group"]
        if not datetime_cols:
            datetime_cols = ["date", "time"]
        
        # Basic imports
        code = "library(tidyverse)\nlibrary(ggplot2)\n\n"
        code += "# Assuming your data is in a data frame called 'df'\n"
        
        # Chart-specific code
        if chart_type == "Line chart" and (datetime_cols or categorical_cols) and numeric_cols:
            x_col = datetime_cols[0] if datetime_cols else categorical_cols[0]
            y_col = numeric_cols[0]
            code += "# Create a line chart\n"
            code += f"ggplot(df, aes(x = {x_col}, y = {y_col})) +\n"
            code += "  geom_line() +\n"
            code += "  geom_point() +\n"
            if datetime_cols:
                code += "  scale_x_date(date_breaks = 'month', date_labels = '%b %Y') +\n"
            code += f"  labs(title = 'Trend of {y_col} over {x_col}',\n"
            code += f"       x = '{x_col}',\n"
            code += f"       y = '{y_col}') +\n"
            code += "  theme_minimal() +\n"
            code += "  theme(axis.text.x = element_text(angle = 45, hjust = 1))\n"
        
        elif chart_type == "Bar chart" and categorical_cols and numeric_cols:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            code += "# Create a bar chart\n"
            code += f"ggplot(df, aes(x = {x_col}, y = {y_col})) +\n"
            code += "  geom_bar(stat = 'identity', fill = 'steelblue') +\n"
            code += f"  labs(title = '{y_col} by {x_col}',\n"
            code += f"       x = '{x_col}',\n"
            code += f"       y = '{y_col}') +\n"
            code += "  theme_minimal() +\n"
            code += "  theme(axis.text.x = element_text(angle = 45, hjust = 1))\n"
        
        elif chart_type == "Scatter plot" and len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            code += "# Create a scatter plot\n"
            code += f"ggplot(df, aes(x = {x_col}, y = {y_col})) +\n"
            code += "  geom_point(alpha = 0.7) +\n"
            code += "  geom_smooth(method = 'lm', se = TRUE) +\n"
            code += f"  labs(title = 'Relationship between {x_col} and {y_col}',\n"
            code += f"       x = '{x_col}',\n"
            code += f"       y = '{y_col}') +\n"
            code += "  theme_minimal()\n"
        
        elif chart_type == "Histogram" and numeric_cols:
            col = numeric_cols[0]
            code += "# Create a histogram\n"
            code += f"ggplot(df, aes(x = {col})) +\n"
            code += "  geom_histogram(binwidth = NULL, fill = 'steelblue', color = 'white') +\n"
            code += "  geom_density(aes(y = ..count.. * max(..count..)), color = 'red') +\n"
            code += f"  labs(title = 'Distribution of {col}',\n"
            code += f"       x = '{col}',\n"
            code += "       y = 'Frequency') +\n"
            code += "  theme_minimal()\n"
        
        elif chart_type == "Box plot" and numeric_cols and categorical_cols:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            code += "# Create a box plot\n"
            code += f"ggplot(df, aes(x = {x_col}, y = {y_col})) +\n"
            code += "  geom_boxplot(fill = 'steelblue', alpha = 0.7) +\n"
            code += f"  labs(title = 'Distribution of {y_col} by {x_col}',\n"
            code += f"       x = '{x_col}',\n"
            code += f"       y = '{y_col}') +\n"
            code += "  theme_minimal() +\n"
            code += "  theme(axis.text.x = element_text(angle = 45, hjust = 1))\n"
        
        elif chart_type == "Pie chart" and categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            val_col = numeric_cols[0]
            code += "# Create a pie chart using ggplot2\n"
            code += f"# First, aggregate the data\npie_data <- df %>%\n"
            code += f"  group_by({cat_col}) %>%\n"
            code += f"  summarize(value = sum({val_col}, na.rm = TRUE))\n\n"
            code += "# Calculate percentages and positions\npie_data <- pie_data %>%\n"
            code += "  mutate(percentage = value / sum(value) * 100,\n"
            code += "         ypos = cumsum(percentage) - 0.5 * percentage)\n\n"
            code += "# Create the plot\n"
            code += "ggplot(pie_data, aes(x = '', y = percentage, fill = reorder(get(cat_col), -percentage))) +\n"
            code += "  geom_bar(stat = 'identity', width = 1, color = 'white') +\n"
            code += "  coord_polar('y', start = 0) +\n"
            code += "  geom_text(aes(y = ypos, label = paste0(round(percentage, 1), '%')), color = 'white') +\n"
            code += f"  labs(title = 'Distribution of {val_col} by {cat_col}',\n"
            code += "       fill = cat_col) +\n"
            code += "  theme_minimal() +\n"
            code += "  theme(axis.title = element_blank(),\n"
            code += "        axis.text = element_blank(),\n"
            code += "        panel.grid = element_blank())\n"
        
        elif chart_type == "Heatmap" and len(numeric_cols) >= 3:
            code += "# Create a correlation heatmap\n"
            code += f"# Calculate correlation matrix for numeric columns\ncorr_matrix <- df %>%\n"
            code += f"  select({', '.join(numeric_cols)}) %>%\n"
            code += "  cor(use = 'pairwise.complete.obs')\n\n"
            code += "# Convert to long format for ggplot\ncorr_df <- as.data.frame(as.table(corr_matrix)) %>%\n"
            code += "  rename(Var1 = Var1, Var2 = Var2, Correlation = Freq)\n\n"
            code += "# Create the heatmap\n"
            code += "ggplot(corr_df, aes(x = Var1, y = Var2, fill = Correlation)) +\n"
            code += f"geom_tile() +\n"
            code += "  scale_fill_gradient2(low = 'blue', high = 'red', mid = 'white', midpoint = 0) +\n"
            code += "  geom_text(aes(label = round(Correlation, 2)), color = 'black', size = 3) +\n"
            code += "  labs(title = 'Correlation Heatmap') +\n"
            code += "  theme_minimal() +\n"
            code += "  theme(axis.text.x = element_text(angle = 45, hjust = 1))\n"

        elif data_type == "time series" and datetime_cols and numeric_cols:
            # More advanced time series example
            date_col = datetime_cols[0]
            val_col = numeric_cols[0]
            code += "# Time series analysis in R\n"
            code += f"# Ensure date column is properly formatted\ndf${date_col} <- as.Date(df${date_col})\n\n"
            code += "# Create time series visualization with decomposition\n"
            code += f"# First, create the main time series plot\np1 <- ggplot(df, aes(x = {date_col}, y = {val_col})) +\n"
            code += "  geom_line() +\n"
            code += "  geom_point(size = 1) +\n"
            code += f"  labs(title = '{val_col} Over Time',\n"
            code += f"       x = '{date_col}',\n"
            code += f"       y = '{val_col}') +\n"
            code += "  theme_minimal()\n\n"
            code += "# Create monthly aggregation\n"
            code += f"monthly_data <- df %>%\n"
            code += f"  mutate(month = floor_date({date_col}, 'month')) %>%\n"
            code += f"  group_by(month) %>%\n"
            code += f"  summarize(mean_{val_col} = mean({val_col}, na.rm = TRUE))\n\n"
            code += f"# Plot monthly trend\np2 <- ggplot(monthly_data, aes(x = month, y = mean_{val_col})) +\n"
            code += "  geom_line() +\n"
            code += "  geom_point(size = 2) +\n"
            code += f"  labs(title = 'Monthly Average {val_col}',\n"
            code += "       x = 'Month',\n"
            code += f"       y = 'Average {val_col}') +\n"
            code += "  theme_minimal()\n\n"
            code += "# Combine plots using patchwork\n"
            code += "library(patchwork)\n"
            code += "p1 / p2\n"

        else:
            # Generic fallback
            code += "# Basic visualization template\n"
            if numeric_cols and categorical_cols:
                code += f"ggplot(df, aes(x = {categorical_cols[0]}, y = {numeric_cols[0]})) +\n"
                code += "  geom_bar(stat = 'identity', fill = 'steelblue') +\n"
                code += f"  labs(title = '{numeric_cols[0]} by {categorical_cols[0]}',\n"
                code += f"       x = '{categorical_cols[0]}',\n"
                code += f"       y = '{numeric_cols[0]}') +\n"
                code += "  theme_minimal() +\n"
                code += "  theme(axis.text.x = element_text(angle = 45, hjust = 1))\n"
            elif len(numeric_cols) >= 2:
                code += f"ggplot(df, aes(x = {numeric_cols[0]}, y = {numeric_cols[1]})) +\n"
                code += "  geom_point() +\n"
                code += "  geom_smooth(method = 'lm') +\n"
                code += f"  labs(title = 'Relationship between {numeric_cols[0]} and {numeric_cols[1]}',\n"
                code += f"       x = '{numeric_cols[0]}',\n"
                code += f"       y = '{numeric_cols[1]}') +\n"
                code += "  theme_minimal()\n"
            elif numeric_cols:
                code += f"ggplot(df, aes(x = {numeric_cols[0]})) +\n"
                code += "  geom_histogram(binwidth = NULL, fill = 'steelblue', color = 'white') +\n"
                code += f"  labs(title = 'Distribution of {numeric_cols[0]}',\n"
                code += f"       x = '{numeric_cols[0]}',\n"
                code += "       y = 'Count') +\n"
                code += "  theme_minimal()\n"
            else:
                code += "# Need at least one numeric column for most visualizations\n"
                code += "# Consider reviewing your data structure\n"

        return code

    def forecast_trend(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        time_column: Optional[str] = None,
        value_column: Optional[str] = None,
        historical_data_description: Optional[str] = None,
        forecast_period: Optional[str] = None,
        confidence_level: Optional[float] = None,
        seasonality: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate a forecast based on historical data and parameters.

        Args:
            dataset: Required dataset to use for forecasting.
            time_column: Required column name containing time/date information.
            value_column: Required column name containing the values to forecast.
            historical_data_description: Description of the historical data (period covered, key metrics, etc.)
            forecast_period: The time period to forecast (e.g., "3 months", "1 year")
            confidence_level: The confidence level for prediction intervals (default: 0.95)
            seasonality: Whether to account for seasonality in the forecast (default: auto-detect)

        Returns:
            Forecast results including predicted values, confidence intervals, and methodology notes.
        """
        # Set default values for optional parameters
        historical_data_description = historical_data_description or "Time series data"
        forecast_period = forecast_period or "3 months"
        confidence_level = confidence_level or 0.95

        # Check for required parameters
        if not dataset:
            logger.warning("No dataset provided for forecasting")
            return {
                "error": "Missing required dataset for forecasting",
                "missing_information": ["Dataset containing time series data points"],
                "required": "Please provide a valid dataset (list of dictionaries) for time series forecasting"
            }
            
        if not time_column:
            logger.warning("No time column specified for forecasting")
            available_columns = list(dataset[0].keys()) if dataset and len(dataset) > 0 else []
            return {
                "error": "Missing required time column for forecasting",
                "missing_information": ["Column name containing time/date information"],
                "available_columns": available_columns,
                "required": "Please specify a column containing date/time information"
            }
            
        if not value_column:
            logger.warning("No value column specified for forecasting")
            available_columns = list(dataset[0].keys()) if dataset and len(dataset) > 0 else []
            return {
                "error": "Missing required value column for forecasting",
                "missing_information": ["Column name containing the values to forecast"],
                "available_columns": available_columns,
                "required": "Please specify a column containing numeric values to forecast"
            }

        # Extract forecast period as a number of time units
        forecast_units = self._parse_forecast_period(forecast_period)
        if not forecast_units:
            return {
                "error": f"Unable to parse forecast period: {forecast_period}. Please use format like '3 months' or '1 year'."
            }

        logger.info(f"Generating {forecast_period} forecast with {confidence_level} confidence level")

        # Perform actual forecasting
        try:
            return self._perform_time_series_forecast(
                dataset,
                time_column,
                value_column,
                forecast_units,
                confidence_level,
                seasonality
            )
        except Exception as e:
            logger.error(f"Error performing forecast: {str(e)}")
            return {
                "error": f"Error performing forecast: {str(e)}",
                "forecast_summary": {
                    "status": "failed",
                    "error_details": str(e)
                }
            }

    def _parse_forecast_period(self, forecast_period: str) -> Optional[Dict[str, int]]:
        """Parse forecast period string into number of units."""
        import re

        # Extract number and time unit from string
        match = re.match(r'(\d+)\s*(\w+)', forecast_period)
        if not match:
            return None

        number, unit = match.groups()
        number = int(number)
        unit = unit.lower().rstrip('s')  # Remove plural 's' if present

        # Map to standard time units
        unit_mapping = {
            'day': 'days',
            'week': 'weeks',
            'month': 'months',
            'quarter': 'quarters',
            'year': 'years'
        }

        if unit not in unit_mapping:
            return None

        return {unit_mapping[unit]: number}

    def _perform_time_series_forecast(
        self,
        dataset: List[Dict[str, Any]],
        time_column: str,
        value_column: str,
        forecast_units: Dict[str, int],
        confidence_level: float = 0.95,
        seasonality: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Perform time series forecasting on the dataset."""
        # Extract time and value from dataset
        time_values = []
        values = []

        # Process the data
        for row in dataset:
            if time_column in row and value_column in row:
                try:
                    # Convert time to datetime if not already
                    time_value = row[time_column]
                    if isinstance(time_value, str):
                        # Try various date formats
                        date_formats = [
                            "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
                            "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"
                        ]

                        for date_format in date_formats:
                            try:
                                time_value = datetime.datetime.strptime(time_value, date_format)
                                break
                            except ValueError:
                                continue

                    # Convert value to float
                    value = float(row[value_column])

                    time_values.append(time_value)
                    values.append(value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing row: {row}, Error: {str(e)}")
                    continue

        # Check if we have enough data points
        if len(values) < 4:
            return {
                "error": f"Insufficient data points for forecasting. Need at least 4, found {len(values)}."
            }

        # Sort data by time
        sorted_data = sorted(zip(time_values, values), key=lambda x: x[0])
        sorted_times, sorted_values = zip(*sorted_data)

        # Analyze time series characteristics
        time_series_info = self._analyze_time_series_characteristics(sorted_times, sorted_values, seasonality)

        # Generate forecast based on characteristics
        forecast_results = self._generate_time_series_forecast(
            sorted_times,
            sorted_values,
            forecast_units,
            confidence_level,
            time_series_info
        )

        return forecast_results

    def _analyze_time_series_characteristics(
        self,
        times: List[Any],
        values: List[float],
        seasonality_param: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Analyze time series characteristics for forecasting."""
        # Determine time frequency
        time_diffs = [(times[i+1] - times[i]).total_seconds() for i in range(len(times)-1)]
        avg_time_diff = sum(time_diffs) / len(time_diffs)

        # Map seconds to time units
        if avg_time_diff < 3600:  # Less than hour
            frequency = "minutes"
        elif avg_time_diff < 86400:  # Less than day
            frequency = "hours"
        elif avg_time_diff < 604800:  # Less than week
            frequency = "days"
        elif avg_time_diff < 2592000:  # Less than month
            frequency = "weeks"
        elif avg_time_diff < 7776000:  # Less than 3 months
            frequency = "months"
        else:
            frequency = "quarters"

        # Check for trend
        if len(values) >= 3:
            # Simple linear regression to detect trend
            x = list(range(len(values)))
            mean_x = sum(x) / len(x)
            mean_y = sum(values) / len(values)

            numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(len(values)))
            denominator = sum((x[i] - mean_x) ** 2 for i in range(len(values)))

            if denominator != 0:
                slope = numerator / denominator
                trend_strength = abs(slope) / (max(values) - min(values)) * len(values)

                if trend_strength > 0.1:
                    trend = "increasing" if slope > 0 else "decreasing"
                    trend_significance = "strong" if trend_strength > 0.3 else "moderate"
                else:
                    trend = "stable"
                    trend_significance = "weak"
            else:
                trend = "stable"
                trend_significance = "weak"
        else:
            trend = "unknown"
            trend_significance = "unknown"

        # Detect seasonality
        detected_seasonality = False
        seasonal_period = None

        if len(values) >= 12:
            # Only detect seasonality for longer time series
            # Simple autocorrelation-based detection for common seasonalities
            possible_periods = [7, 12, 4, 52]  # weekly, monthly, quarterly, yearly
            max_correlation = 0

            for period in possible_periods:
                if len(values) > period * 2:
                    # Calculate autocorrelation for this period
                    correlation = sum(values[i] * values[i + period] for i in range(len(values) - period)) / \
                                 (sum(values[i]**2 for i in range(len(values) - period)) ** 0.5 *
                                  sum(values[i + period]**2 for i in range(len(values) - period)) ** 0.5)

                    if correlation > max_correlation and correlation > 0.3:
                        max_correlation = correlation
                        seasonal_period = period

            if seasonal_period:
                detected_seasonality = True

        # Override with parameter if provided
        if seasonality_param is not None:
            detected_seasonality = seasonality_param

        # Return characteristics
        return {
            "frequency": frequency,
            "trend": trend,
            "trend_significance": trend_significance,
            "seasonality_detected": detected_seasonality,
            "seasonal_period": seasonal_period,
            "data_points": len(values),
            "first_date": times[0],
            "last_date": times[-1],
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values)
        }

    def _generate_time_series_forecast(
        self,
        times: List[Any],
        values: List[float],
        forecast_units: Dict[str, int],
        confidence_level: float,
        time_series_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate time series forecast based on historical data."""
        # Determine which forecasting method to use
        if time_series_info["seasonality_detected"]:
            method = "Triple Exponential Smoothing (Holt-Winters)"
        elif time_series_info["trend"] != "stable":
            method = "Double Exponential Smoothing (Holt's Method)"
        else:
            method = "Simple Moving Average"

        # Determine forecast horizon
        unit, count = list(forecast_units.items())[0]

        # Convert to number of data points based on frequency
        if unit == "days" and time_series_info["frequency"] == "days":
            horizon = count
        elif unit == "weeks" and time_series_info["frequency"] == "days":
            horizon = count * 7
        elif unit == "months" and time_series_info["frequency"] == "days":
            horizon = count * 30
        elif unit == "months" and time_series_info["frequency"] == "weeks":
            horizon = count * 4
        elif unit == "quarters" and time_series_info["frequency"] == "months":
            horizon = count * 3
        elif unit == "years" and time_series_info["frequency"] == "months":
            horizon = count * 12
        elif unit == "years" and time_series_info["frequency"] == "quarters":
            horizon = count * 4
        else:
            # Default proportional to data length
            horizon = int(count * len(values) / 4)

        # Generate forecast dates
        last_date = times[-1]
        forecast_dates = []

        for i in range(1, horizon + 1):
            if unit == "days":
                forecast_date = last_date + datetime.timedelta(days=i)
            elif unit == "weeks":
                forecast_date = last_date + datetime.timedelta(weeks=i)
            elif unit == "months":
                new_month = ((last_date.month - 1 + i) % 12) + 1
                new_year = last_date.year + ((last_date.month - 1 + i) // 12)
                forecast_date = last_date.replace(year=new_year, month=new_month)
            elif unit == "quarters":
                new_month = ((last_date.month - 1 + i*3) % 12) + 1
                new_year = last_date.year + ((last_date.month - 1 + i*3) // 12)
                forecast_date = last_date.replace(year=new_year, month=new_month)
            elif unit == "years":
                forecast_date = last_date.replace(year=last_date.year + i)
            else:
                forecast_date = last_date + datetime.timedelta(days=i*30)  # Default

            forecast_dates.append(forecast_date)

        # Generate forecast values using simplified forecasting methods
        forecast_values = []

        if method == "Simple Moving Average":
            # Use last 3 values for prediction
            window_size = min(3, len(values))
            last_window = values[-window_size:]
            avg_value = sum(last_window) / window_size

            # Flat prediction
            forecast_values = [avg_value] * horizon

        elif method == "Double Exponential Smoothing (Holt's Method)":
            # Implement simplified Holt's method
            alpha = 0.7  # Level smoothing
            beta = 0.2   # Trend smoothing

            # Initialize
            level = values[0]
            trend = values[1] - values[0] if len(values) > 1 else 0

            # Update level and trend with each observation
            for value in values[1:]:
                prev_level = level
                level = alpha * value + (1 - alpha) * (level + trend)
                trend = beta * (level - prev_level) + (1 - beta) * trend

            # Generate forecast
            for i in range(horizon):
                forecast_values.append(level + (i + 1) * trend)

        elif method == "Triple Exponential Smoothing (Holt-Winters)":
            # Simplified Holt-Winters adaptation without full seasonal component
            alpha = 0.7  # Level smoothing
            beta = 0.2   # Trend smoothing
            gamma = 0.1  # Seasonal smoothing

            # Use detected seasonal period or default
            seasonal_period = time_series_info.get("seasonal_period", 4)

            # Initialize level and trend
            level = values[0]
            trend = values[1] - values[0] if len(values) > 1 else 0

            # Initialize seasonal components
            seasons = len(values) // seasonal_period
            if seasons >= 1:
                seasonal = []
                for i in range(seasonal_period):
                    if i < len(values):
                        seasonal.append(values[i] / level)
                    else:
                        seasonal.append(1.0)
            else:
                seasonal = [1.0] * seasonal_period

            # Generate forecast with seasonal adjustments
            for i in range(horizon):
                season_idx = i % seasonal_period
                forecast_values.append((level + (i + 1) * trend) * seasonal[season_idx])

        # Calculate confidence intervals
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        z_score = 1.96  # Approximately 95% confidence interval
        if confidence_level == 0.90:
            z_score = 1.645
        elif confidence_level == 0.99:
            z_score = 2.576

        margin_of_error = z_score * std_dev / (len(values) ** 0.5)

        # Adjust error margins based on forecast distance
        confidence_intervals = []
        for i in range(horizon):
            # Increase uncertainty for further forecasts
            distance_factor = 1 + (i / horizon)
            interval = margin_of_error * distance_factor

            lower_bound = forecast_values[i] - interval
            upper_bound = forecast_values[i] + interval

            confidence_intervals.append({
                "lower": lower_bound,
                "upper": upper_bound
            })

        # Detect seasonal patterns
        seasonal_factors = None
        if time_series_info["seasonality_detected"] and time_series_info["seasonal_period"]:
            seasonal_factors = {
                "period_length": time_series_info["seasonal_period"],
                "period_type": self._get_seasonal_period_type(time_series_info["seasonal_period"]),
                "factors": []
            }

        # Calculate overall trend for forecast
        if len(forecast_values) > 0:
            forecast_start = forecast_values[0]
            forecast_end = forecast_values[-1]
            forecast_change = forecast_end - forecast_start
            forecast_pct_change = (forecast_change / forecast_start * 100) if forecast_start != 0 else 0

            if forecast_change > 0:
                forecast_trend = "increasing"
            elif forecast_change < 0:
                forecast_trend = "decreasing"
            else:
                forecast_trend = "stable"
        else:
            forecast_trend = "unknown"
            forecast_pct_change = 0

        # Build forecast results
        forecast_results = {
            "forecast_summary": {
                "model": method,
                "forecast_period": list(forecast_units.keys())[0] + " " + str(list(forecast_units.values())[0]),
                "confidence_level": confidence_level,
                "data_points_used": len(values),
                "time_range": f"{times[0]} to {times[-1]}",
                "trend_direction": forecast_trend,
                "predicted_change": f"{forecast_pct_change:.2f}%"
            },
            "time_series_characteristics": time_series_info,
            "forecast_data": {
                "dates": [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in forecast_dates],
                "predicted_values": forecast_values,
                "confidence_intervals": confidence_intervals
            }
        }

        if seasonal_factors:
            forecast_results["seasonal_factors"] = seasonal_factors

        forecast_results["cautions"] = self._generate_forecast_cautions(
            forecast_results["time_series_characteristics"],
            forecast_units
        )

        return forecast_results

    def _get_seasonal_period_type(self, period: int) -> str:
        """Map a seasonal period to a human-readable description."""
        seasonal_map = {
            4: "quarterly",
            7: "weekly",
            12: "monthly",
            52: "weekly (yearly)",
            365: "daily (yearly)"
        }

        return seasonal_map.get(period, f"Every {period} data points")

    def _generate_forecast_cautions(
        self,
        time_series_info: Dict[str, Any],
        forecast_units: Dict[str, int]
    ) -> List[str]:
        """Generate appropriate cautions for the forecast."""
        cautions = []

        # Check data points quantity
        if time_series_info["data_points"] < 10:
            cautions.append(
                f"Limited historical data ({time_series_info['data_points']} points) may reduce forecast accuracy."
            )

        # Check forecast horizon
        unit, count = list(forecast_units.items())[0]
        if unit == "years" and count > 1:
            cautions.append(
                f"Long-term forecasts ({count} years) are inherently less reliable and should be used with caution."
            )

        # Check for seasonality detection
        if time_series_info["seasonality_detected"] and time_series_info["data_points"] < 24:
            cautions.append(
                "Seasonal patterns detected, but limited historical cycles may affect seasonal adjustment accuracy."
            )

        # Check for external factors
        cautions.append(
            "This forecast is based solely on historical patterns and does not account for external factors or market changes."
        )

        # Add general statistical caveat
        cautions.append(
            f"Prediction intervals represent {int(0.95*100)}% confidence, but unexpected events may cause actual values to fall outside these ranges."
        )

        return cautions

    def _generate_forecast_error_message(
        self,
        historical_data_description: str,
        forecast_period: str,
        confidence_level: float
    ) -> Dict[str, Any]:
        """Generate an error message when no dataset is provided for forecasting."""
        # Parse forecast period
        forecast_units = self._parse_forecast_period(forecast_period)
        
        if not forecast_units:
            unit, count = "unknown", 0
        else:
            unit, count = list(forecast_units.items())[0]

        # Generate an error message with required information
        return {
            "error": "Missing required data for forecasting",
            "missing_information": [
                "Dataset containing time series data points",
                "Time column (containing dates or time periods)",
                "Value column (containing the values to forecast)"
            ],
            "request_parameters": {
                "provided": {
                    "historical_data_description": historical_data_description,
                    "forecast_period": forecast_period,
                    "confidence_level": confidence_level
                },
                "required": [
                    "dataset - A list of dictionaries containing the time series data",
                    "time_column - Column name containing date/time information",
                    "value_column - Column name containing the numeric values to forecast"
                ]
            }
        }

    def detect_anomalies(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        columns: Optional[List[str]] = None,
        data_pattern_description: Optional[str] = None,
        sensitivity: Optional[str] = None,
        anomaly_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze data for unusual patterns, outliers, or anomalies.

        Args:
            dataset: Required dataset to analyze for anomalies.
            columns: Required list of columns to analyze for anomalies.
            data_pattern_description: Description of the usual patterns in the data.
            sensitivity: How sensitive the detection should be ("low", "medium", "high").
            anomaly_types: Optional list of specific anomaly types to look for.

        Returns:
            Analysis results including detected anomalies, methodology used, and recommendations.
        """
        # Set defaults for all parameters
        data_pattern_description = data_pattern_description or "Standard time series data"
        sensitivity = sensitivity or "medium"
        anomaly_types = anomaly_types or ["outliers", "pattern breaks", "seasonal deviations"]

        logger.info(f"Detecting anomalies with {sensitivity} sensitivity")

        # Create sensitivity parameters mapping
        sensitivity_map = {
            "low": {"threshold": 3.0, "false_positive_risk": "Low", "false_negative_risk": "High"},
            "medium": {"threshold": 2.0, "false_positive_risk": "Medium", "false_negative_risk": "Medium"},
            "high": {"threshold": 1.5, "false_positive_risk": "High", "false_negative_risk": "Low"}
        }

        # Get sensitivity threshold
        sensitivity_settings = sensitivity_map.get(sensitivity.lower(), sensitivity_map["medium"])

        # Check if required parameters are provided
        if not dataset:
            logger.warning("No dataset provided for anomaly detection")
            return {
                "error": "Missing required dataset for anomaly detection",
                "missing_information": ["Dataset containing data points to analyze"],
                "required": "Please provide a valid dataset (list of dictionaries) to analyze for anomalies"
            }
            
        if not columns:
            logger.warning("No columns specified for anomaly detection")
            return {
                "error": "Missing required columns for anomaly detection",
                "missing_information": ["Specific columns to analyze for anomalies"],
                "available_columns": list(dataset[0].keys()) if dataset and len(dataset) > 0 else [],
                "required": "Please specify which columns to analyze for anomalies"
            }

        # Perform actual anomaly detection
        try:
            return self._perform_anomaly_detection(
                dataset,
                columns,
                anomaly_types,
                sensitivity_settings["threshold"]
            )
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {
                "error": f"Error detecting anomalies: {str(e)}",
                "methodology": {
                    "status": "failed",
                    "error_details": str(e)
                }
            }

    def _perform_anomaly_detection(
        self,
        dataset: List[Dict[str, Any]],
        columns: List[str],
        anomaly_types: List[str],
        threshold: float
    ) -> Dict[str, Any]:
        """Perform actual anomaly detection on the dataset."""
        # Initialize results
        results = {
            "methodology": {
                "detection_methods": [],
                "sensitivity_settings": {"threshold": threshold},
                "columns_analyzed": columns
            },
            "detected_anomalies": [],
            "anomaly_summary": {},
            "recommendations": []
        }

        # Process each column for anomalies
        for column in columns:
            # Extract column values
            values = []
            for row in dataset:
                if column in row and row[column] is not None:
                    try:
                        # Try to convert to float for numeric analysis
                        value = float(row[column])
                        values.append(value)
                    except (ValueError, TypeError):
                        # Skip non-numeric values
                        pass

            # Skip columns with insufficient data
            if len(values) < 3:
                continue

            # Determine column type and apply appropriate anomaly detection
            if "outliers" in anomaly_types:
                outliers = self._detect_statistical_outliers(values, threshold)

                if outliers:
                    anomaly = {
                        "type": "Outlier",
                        "column": column,
                        "count": len(outliers),
                        "percentage": (len(outliers) / len(values)) * 100,
                        "values": outliers[:5],  # Limit to first 5 outliers
                        "significance": "High" if len(outliers) > len(values) * 0.05 else "Medium",
                        "description": f"Statistical outliers detected in {column} based on {threshold} standard deviations",
                        "recommended_action": "Investigate these data points for potential errors or special cases"
                    }

                    results["detected_anomalies"].append(anomaly)

                    # Add detection method if not already added
                    method = "Statistical outlier detection (Z-score method)"
                    if method not in results["methodology"]["detection_methods"]:
                        results["methodology"]["detection_methods"].append(method)

            # Check for pattern breaks or change points if we have enough data
            if "pattern breaks" in anomaly_types and len(values) >= 10:
                change_points = self._detect_change_points(values)

                if change_points:
                    anomaly = {
                        "type": "Pattern Break",
                        "column": column,
                        "count": len(change_points),
                        "positions": change_points[:3],  # Limit to first 3 change points
                        "significance": "High" if len(change_points) <= 2 else "Medium",
                        "description": f"Significant shifts in data patterns detected in {column}",
                        "recommended_action": "Investigate what caused these shifts in the data pattern"
                    }

                    results["detected_anomalies"].append(anomaly)

                    # Add detection method if not already added
                    method = "Change point detection (CUSUM algorithm)"
                    if method not in results["methodology"]["detection_methods"]:
                        results["methodology"]["detection_methods"].append(method)

            # Check for seasonal deviations if we have enough data
            if "seasonal deviations" in anomaly_types and len(values) >= 24:
                seasonal_anomalies = self._detect_seasonal_anomalies(values, threshold)

                if seasonal_anomalies:
                    anomaly = {
                        "type": "Seasonal Deviation",
                        "column": column,
                        "count": len(seasonal_anomalies),
                        "positions": seasonal_anomalies[:3],  # Limit to first 3 seasonal anomalies
                        "significance": "Medium",
                        "description": f"Deviations from expected seasonal patterns detected in {column}",
                        "recommended_action": "Check if these deviations align with known changes or events"
                    }

                    results["detected_anomalies"].append(anomaly)

                    # Add detection method if not already added
                    method = "Seasonal decomposition analysis"
                    if method not in results["methodology"]["detection_methods"]:
                        results["methodology"]["detection_methods"].append(method)

        # Add summary information
        results["anomaly_summary"] = {
            "total_anomalies_detected": len(results["detected_anomalies"]),
            "columns_with_anomalies": len(set(anomaly["column"] for anomaly in results["detected_anomalies"])),
            "anomaly_types_found": list(set(anomaly["type"] for anomaly in results["detected_anomalies"]))
        }

        # Generate recommendations based on findings
        results["recommendations"] = self._generate_anomaly_recommendations(results["detected_anomalies"])

        return results

    def _detect_statistical_outliers(self, values: List[float], threshold: float) -> List[float]:
        """Detect statistical outliers using Z-score method."""
        if len(values) < 3:
            return []

        # Calculate mean and standard deviation
        mean = sum(values) / len(values)
        std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

        # Detect outliers using Z-score method
        outliers = []
        for value in values:
            z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
            if z_score > threshold:
                outliers.append(value)

        return outliers

    def _detect_change_points(self, values: List[float]) -> List[int]:
        """Detect change points using a simplified CUSUM algorithm."""
        if len(values) < 10:
            return []

        # Simplified CUSUM detection
        change_points = []
        window_size = min(5, len(values) // 4)

        for i in range(window_size, len(values) - window_size):
            left_window = values[i-window_size:i]
            right_window = values[i:i+window_size]

            left_mean = sum(left_window) / len(left_window)
            right_mean = sum(right_window) / len(right_window)

            # Calculate pooled standard deviation
            left_var = sum((x - left_mean) ** 2 for x in left_window) / len(left_window)
            right_var = sum((x - right_mean) ** 2 for x in right_window) / len(right_window)
            pooled_std = ((left_var + right_var) / 2) ** 0.5

            # Calculate test statistic
            if pooled_std > 0:
                test_statistic = abs(left_mean - right_mean) / pooled_std

                # If the difference is significant, mark as change point
                if test_statistic > 2.5:  # Fixed threshold for simplicity
                    change_points.append(i)

        # Merge nearby change points
        if change_points:
            merged_points = [change_points[0]]
            for point in change_points[1:]:
                if point - merged_points[-1] > window_size:
                    merged_points.append(point)

            return merged_points

        return []

    def _detect_seasonal_anomalies(self, values: List[float], threshold: float) -> List[int]:
        """Detect deviations from seasonal patterns."""
        if len(values) < 24:  # Need enough data to detect seasonality
            return []

        # Try common seasonal periods
        seasonal_periods = [7, 12, 4]  # weekly, monthly, quarterly
        best_period = None
        best_score = 0

        for period in seasonal_periods:
            if len(values) >= period * 2:
                # Calculate autocorrelation for this period
                n = len(values) - period
                numerator = sum(values[i] * values[i + period] for i in range(n))
                denominator = (sum(values[i]**2 for i in range(n)) *
                               sum(values[i + period]**2 for i in range(n))) ** 0.5

                if denominator > 0:
                    correlation = numerator / denominator
                    if correlation > best_score:
                        best_score = correlation
                        best_period = period

        # If no strong seasonality, return empty
        if best_period is None or best_score < 0.3:
            return []

        # Decompose the time series using the seasonal period
        trend = []
        seasonal = [0] * best_period
        residuals = []

        # Calculate seasonal components (simplified)
        for i in range(best_period):
            season_values = [values[j] for j in range(i, len(values), best_period)]
            if season_values:
                seasonal[i] = sum(season_values) / len(season_values)

        # Normalize seasonal components
        seasonal_mean = sum(seasonal) / best_period
        seasonal = [s - seasonal_mean for s in seasonal]

        # Calculate trend and residuals
        for i in range(len(values)):
            season_idx = i % best_period
            deseasonalized = values[i] - seasonal[season_idx]
            trend.append(deseasonalized)

            # For simplicity, use moving average for the trend
            window_size = min(best_period, (len(values) - i))
            if i >= window_size:
                trend_value = sum(trend[i-window_size:i]) / window_size
                residual = values[i] - (trend_value + seasonal[season_idx])
                residuals.append(residual)
            else:
                residuals.append(0)

        # Detect anomalies in residuals
        anomalies = []
        if residuals:
            residual_mean = sum(residuals) / len(residuals)
            residual_std = (sum((r - residual_mean) ** 2 for r in residuals) / len(residuals)) ** 0.5

            for i in range(len(residuals)):
                if residual_std > 0:
                    z_score = abs(residuals[i] - residual_mean) / residual_std
                    if z_score > threshold:
                        anomalies.append(i)

        return anomalies

    def _generate_anomaly_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on detected anomalies."""
        recommendations = []

        # Count anomaly types
        anomaly_counts = {}
        for anomaly in anomalies:
            anomaly_type = anomaly["type"]
            anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1

        # Generate specific recommendations for each type
        if "Outlier" in anomaly_counts:
            outlier_columns = set(anomaly["column"] for anomaly in anomalies if anomaly["type"] == "Outlier")

            if len(outlier_columns) > 1:
                recommendations.append(
                    f"Investigate outliers across multiple columns ({', '.join(list(outlier_columns)[:3])}...) to identify potential systematic issues."
                )

            recommendations.append(
                "Review outlier handling strategy: ignore (if valid), correct (if errors), or exclude (if outliers distort analysis)."
            )

        if "Pattern Break" in anomaly_counts:
            recommendations.append(
                "Identify events or changes that coincide with detected pattern breaks, which may explain the shifts."
            )
            recommendations.append(
                "Consider segmenting your analysis before and after significant pattern breaks."
            )

        if "Seasonal Deviation" in anomaly_counts:
            recommendations.append(
                "Analyze seasonal deviations in the context of known events or changes in business practices."
            )
            recommendations.append(
                "Update forecasting models to account for newly identified seasonal variations."
            )

        # Add general recommendations
        if anomalies:
            recommendations.append(
                "Document all anomalies for future reference and pattern recognition."
            )

            if len(anomalies) > 5:
                recommendations.append(
                    "Consider implementing automated anomaly detection for ongoing monitoring of your data."
                )
        else:
            recommendations.append(
                "No significant anomalies detected at current sensitivity. Consider increasing sensitivity if needed."
            )

        return recommendations

    def _generate_anomaly_detection_error_message(
        self,
        data_pattern_description: str,
        anomaly_types: List[str],
        sensitivity_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate an error message when no dataset is provided for anomaly detection."""
        # Create description of what would be used if data was provided
        detection_methods = []

        if "outliers" in anomaly_types:
            detection_methods.append(
                f"Statistical outlier detection with {sensitivity_settings['threshold']} standard deviation threshold"
            )

        if "pattern breaks" in anomaly_types:
            detection_methods.append(
                "Change point detection to identify significant shifts in data patterns"
            )

        if "seasonal deviations" in anomaly_types:
            detection_methods.append(
                "Seasonal decomposition analysis to identify deviations from expected seasonal patterns"
            )

        # Generate an error message with required information
        return {
            "error": "Missing required data for anomaly detection",
            "missing_information": [
                "Dataset containing data points to analyze",
                "Specific columns to analyze for anomalies"
            ],
            "request_parameters": {
                "provided": {
                    "data_pattern_description": data_pattern_description,
                    "sensitivity": sensitivity_settings['false_positive_risk'],
                    "anomaly_types": anomaly_types
                },
                "required": [
                    "dataset - A list of dictionaries containing the data to analyze",
                    "columns - Specific columns to analyze for anomalies"
                ]
            }
        }

    def perform_statistical_analysis(
        self,
        analysis_type: Optional[str] = None,
        dataset: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[List[str]] = None,
        group_by: Optional[str] = None,
        confidence_level: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis on dataset with various methods.

        Args:
            analysis_type: Type of analysis to perform ("descriptive", "correlation", "regression", "time_series").
            dataset: List of dictionaries containing the data to analyze.
            variables: Optional list of specific variables/columns to analyze.
            group_by: Optional column to use for grouping data.
            confidence_level: Confidence level for statistical tests (0-1).

        Returns:
            Dictionary containing the statistical analysis results.
        """
        # Set default values
        analysis_type = analysis_type or "descriptive"
        confidence_level = confidence_level or 0.95

        logger.info(f"Performing {analysis_type} statistical analysis")

        # Validate dataset
        if not dataset:
            return {"error": "Empty dataset provided"}

        # Extract column names if variables not specified
        if not variables:
            variables = list(dataset[0].keys())

        # Initialize results dictionary
        results = {
            "analysis_type": analysis_type,
            "variables_analyzed": variables,
            "sample_size": len(dataset)
        }

        # Process data differently based on analysis type
        if analysis_type == "descriptive":
            results["descriptive_statistics"] = self._calculate_descriptive_statistics(dataset, variables, group_by)

        elif analysis_type == "correlation":
            # Filter for numeric columns only
            numeric_variables = self._filter_numeric_variables(dataset, variables)
            if len(numeric_variables) < 2:
                return {"error": "Correlation analysis requires at least 2 numeric variables"}

            results["correlation_matrix"] = self._calculate_correlation_matrix(dataset, numeric_variables)
            results["interpretation"] = self._interpret_correlations(results["correlation_matrix"])

        elif analysis_type == "time_series":
            time_variable = group_by or self._identify_possible_time_variables(dataset, variables)[0]
            if not time_variable:
                return {"error": "Time series analysis requires a time variable. Please specify using 'group_by' parameter."}

            # Get the metrics for time series analysis (all numeric except time variable)
            numeric_variables = self._filter_numeric_variables(dataset, [v for v in variables if v != time_variable])
            if not numeric_variables:
                return {"error": "Time series analysis requires at least one numeric variable to track over time"}

            results["time_series_analysis"] = self._analyze_time_series(dataset, time_variable, numeric_variables)

        elif analysis_type == "regression":
            if len(variables) < 2:
                return {"error": "Regression analysis requires at least two variables (dependent and independent)"}

            # First variable is assumed to be dependent, rest are independent
            dependent_var = variables[0]
            independent_vars = variables[1:]

            # Ensure variables are numeric
            all_vars = [dependent_var] + independent_vars
            if not all(self._is_numeric_column(dataset, var) for var in all_vars):
                return {"error": "Regression analysis requires all variables to be numeric"}

            results["regression_analysis"] = self._perform_regression_analysis(
                dataset, dependent_var, independent_vars
            )

        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}

        # Add analysis summary
        results["summary"] = self._generate_analysis_summary(results, analysis_type)

        return results

