from typing import Dict, Any, Optional, List, Tuple, Union
import logging
import math
import json
from decimal import Decimal
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from app.services.agents.agent_calculator_tool import get_calculator_tool, get_interpreter_tool

logger = logging.getLogger(__name__)

class DataAnalysisAgent(BaseAgent):
    """
    DataAnalysisAgent is a specialized agent that provides data analysis, statistical operations,
    and quantitative insights across various domains.
    
    This agent specializes in analyzing datasets, performing statistical tests, generating 
    visualizations, and providing data-driven recommendations.
    """

    def __init__(
        self,
        name: str = "Data Analysis Expert",
        model: str = settings.DEFAULT_AGENT_MODEL,
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        **kwargs
    ):
        """
        Initialize a DataAnalysisAgent with specialized data analysis instructions.
        
        Args:
            name: The name of the agent. Defaults to "Data Analysis Expert".
            model: The model to use for the agent. Defaults to settings.DEFAULT_AGENT_MODEL.
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            **kwargs: Additional arguments to pass to the Agent constructor.
        """
        # Define the data analysis expert instructions
        data_analysis_instructions = """"Wherever possible, you must use tools to respond. Do not guess. If a tool is avalable, always call the tool to perform the action. You are a data analysis expert agent specializing in numerical analysis, statistics, visualization, and data-driven insights. Your role is to:

1. PROVIDE DATA ANALYSIS EXPERTISE IN
- Statistical Analysis
- Data Exploration
- Pattern Recognition
- Correlation Analysis
- Regression Analysis
- Time Series Analysis
- Numerical Calculations
- Data Visualization
- Outlier Detection
- Hypothesis Testing
- Confidence Intervals
- Data Sampling

2. ANALYTICAL APPROACHES
- Descriptive Statistics
- Inferential Statistics
- Predictive Modeling
- Exploratory Data Analysis
- Distribution Analysis
- Multivariate Analysis
- Cross-Sectional Analysis
- Longitudinal Analysis
- Segmentation Analysis
- Cluster Analysis
- Factor Analysis
- Anomaly Detection

3. CALCULATION CAPABILITIES
- Perform complex mathematical operations
- Calculate summary statistics
- Perform correlation and regression analysis
- Analyze data distributions
- Identify trends and patterns
- Calculate financial metrics
- Perform time series analysis
- Generate quantitative insights

4. VISUALIZATION RECOMMENDATIONS
- Choose appropriate chart types
- Design effective visualizations
- Highlight key insights
- Create clear representations
- Select appropriate scales
- Design dashboards
- Explain visual patterns
- Recommend visualization tools

5. RESPONSE STRUCTURE
- Begin with key findings
- Provide detailed analysis steps
- Include supporting calculations
- Present clear data interpretations
- Include statistical context
- Provide actionable recommendations
- Explain limitations and assumptions
- Suggest follow-up analyses

Always maintain analytical rigor and statistical validity while explaining insights in clear, understandable terms."""

        # Get the calculator tools - already properly patched from the utility functions
        calculator_tool = get_calculator_tool()
        interpreter_tool = get_interpreter_tool()
        
        # Define the tools - use the already patched instances
        tools = [
            calculator_tool,
            interpreter_tool,
            function_tool(self.analyze_dataset),
            function_tool(self.perform_statistical_analysis),
            function_tool(self.analyze_correlation),
            function_tool(self.perform_regression_analysis),
            function_tool(self.analyze_time_series),
            function_tool(self.identify_outliers),
            function_tool(self.generate_visualizations),
            function_tool(self.segment_data),
        ]
        
        # Initialize the Agent class directly
        super().__init__(
            name=name,
            model=model,
            instructions=data_analysis_instructions,
            functions=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            max_tokens=4096,
            
            **kwargs
        )


    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the DataAnalysisAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for DataAnalysisAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Expert in data analysis, statistical methods, and numerical operations, providing quantitative insights and data-driven recommendations"

    def analyze_dataset(
        self, 
        dataset: Optional[List[Dict[str, Any]]] = None,
        analysis_goals: Optional[List[str]] = None,
        variables_of_interest: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive exploratory data analysis on a dataset.
        
        Args:
            dataset: List of dictionaries representing the dataset (each dictionary is a row).
            analysis_goals: Optional list of specific analysis goals or questions.
            variables_of_interest: Optional list of specific variables to focus on.
            
        Returns:
            A structured analysis of the dataset including summary statistics, data quality assessment,
            and key insights.
        """
        # Validate input parameters
        if dataset is None:
            dataset = []
            
        logger.info(f"Analyzing dataset with {len(dataset)} rows")
        
        # Set default values for optional parameters
        analysis_goals = analysis_goals or ["Explore data distributions", "Identify key patterns", "Assess data quality"]
        
        # Extract column names if variables_of_interest not specified
        if not variables_of_interest and dataset:
            variables_of_interest = list(dataset[0].keys())
        
        # Analyze data types and missing values
        data_types = {}
        missing_values = {}
        value_counts = {}
        
        for variable in variables_of_interest:
            # Collect all non-None values for the variable
            values = [row.get(variable) for row in dataset if variable in row and row[variable] is not None]
            
            # Count missing values
            missing_count = sum(1 for row in dataset if variable not in row or row[variable] is None)
            missing_percentage = (missing_count / len(dataset)) * 100 if dataset else 0
            missing_values[variable] = {
                "count": missing_count,
                "percentage": missing_percentage
            }
            
            # Determine data type
            if values:
                if all(isinstance(v, (int, float)) for v in values):
                    data_types[variable] = "numeric"
                elif all(isinstance(v, str) for v in values):
                    data_types[variable] = "categorical"
                else:
                    data_types[variable] = "mixed"
                
                # Calculate value counts for categorical variables
                if data_types[variable] in ["categorical", "mixed"] and len(values) <= 100:  # Limit to avoid large outputs
                    count_dict = {}
                    for value in values:
                        if value in count_dict:
                            count_dict[value] += 1
                        else:
                            count_dict[value] = 1
                    
                    # Convert to list of (value, count) pairs sorted by count
                    value_counts[variable] = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10 values
        
        # Calculate summary statistics for numeric variables
        summary_statistics = {}
        for variable in variables_of_interest:
            if variable in data_types and data_types[variable] == "numeric":
                values = [float(row.get(variable)) for row in dataset if variable in row 
                          and row[variable] is not None and isinstance(row[variable], (int, float))]
                
                if values:
                    stats = self._calculate_summary_statistics(values)
                    summary_statistics[variable] = stats
        
        # Generate data quality insights
        data_quality_insights = self._generate_data_quality_insights(missing_values, data_types, dataset)
        
        # Generate variable insights
        variable_insights = self._generate_variable_insights(summary_statistics, value_counts)
        
        # Prepare the response
        analysis_results = {
            "dataset_summary": {
                "rows": len(dataset),
                "columns": len(variables_of_interest),
                "data_types": data_types
            },
            "data_quality_assessment": {
                "missing_values": missing_values,
                "quality_insights": data_quality_insights
            },
            "summary_statistics": summary_statistics,
            "categorical_variables": {
                variable: counts for variable, counts in value_counts.items()
            },
            "insights_and_recommendations": {
                "variable_insights": variable_insights,
                "analysis_recommendations": self._generate_analysis_recommendations(
                    data_types, missing_values, summary_statistics, analysis_goals)
            }
        }
        
        return analysis_results   
   
    def perform_statistical_analysis(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        analysis_type: Optional[str] = None,
        variables: Optional[List[str]] = None,
        group_by: Optional[str] = None,
        confidence_level: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis on a dataset.
        
        Args:
            dataset: List of dictionaries representing the dataset (each dictionary is a row).
            analysis_type: Type of statistical analysis to perform (e.g., "descriptive", "comparative", "inferential").
            variables: List of variables to include in the analysis.
            group_by: Variable to group the data by for comparative analysis.
            confidence_level: Confidence level for statistical tests (between 0 and 1).
            
        Returns:
            A dictionary containing the results of the statistical analysis.
        """
        # Set default values for optional parameters
        if dataset is None:
            dataset = []
            
        if analysis_type is None:
            analysis_type = "descriptive"
            
        if confidence_level is None:
            confidence_level = 0.95
            
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
            
        elif analysis_type == "comparative":
            if not group_by:
                return {"error": "Comparative analysis requires 'group_by' parameter"}
            
            results["comparative_analysis"] = self._perform_comparative_analysis(
                dataset, variables, group_by, confidence_level
            )
            
        elif analysis_type == "distribution":
            # Filter for numeric variables only
            numeric_variables = self._filter_numeric_variables(dataset, variables)
            if not numeric_variables:
                return {"error": "Distribution analysis requires at least one numeric variable"}
            
            results["distribution_analysis"] = self._analyze_distributions(dataset, numeric_variables)
            
        elif analysis_type == "hypothesis":
            # This is a simplified implementation; a full implementation would support various hypothesis tests
            if len(variables) < 1:
                return {"error": "Hypothesis testing requires at least one variable"}
            
            results["hypothesis_tests"] = self._perform_basic_hypothesis_tests(
                dataset, variables, confidence_level
            )
        
        else:
            return {"error": f"Unsupported analysis type: {analysis_type}"}
        
        # Add analysis summary
        results["summary"] = self._generate_analysis_summary(results, analysis_type)
        
        return results
    
    def analyze_correlation(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[List[str]] = None,
        correlation_method: Optional[str] = None,
        min_correlation: Optional[float] = None,
        include_visualization: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Analyze correlations between variables in the dataset.
        
        Args:
            dataset: List of dictionaries representing the dataset.
            variables: Optional list of specific variables to analyze correlations for.
            correlation_method: Method to use for correlation ("pearson", "spearman").
            min_correlation: Minimum correlation coefficient to consider significant.
            include_visualization: Whether to include visualization specifications.
            
        Returns:
            A dictionary containing correlation matrix and insights.
        """
        # Set default values for optional parameters
        if dataset is None:
            dataset = []
            
        if correlation_method is None:
            correlation_method = "pearson"
            
        if min_correlation is None:
            min_correlation = 0.3
            
        if include_visualization is None:
            include_visualization = True
        
        logger.info(f"Analyzing correlations using {correlation_method} method")
        
        # Validate dataset
        if not dataset:
            return {"error": "Empty dataset provided"}
        
        # Extract numeric variables if variables not specified
        if not variables:
            variables = list(dataset[0].keys())
        
        # Filter for numeric variables only
        numeric_variables = self._filter_numeric_variables(dataset, variables)
        if len(numeric_variables) < 2:
            return {"error": "Correlation analysis requires at least 2 numeric variables"}
        
        # Calculate correlation matrix
        correlation_matrix = self._calculate_correlation_matrix(dataset, numeric_variables, correlation_method)
        
        # Identify significant correlations
        significant_correlations = []
        for var1 in numeric_variables:
            for var2 in numeric_variables:
                if var1 == var2:
                    continue  # Skip self-correlations
                
                corr = correlation_matrix.get(var1, {}).get(var2)
                if corr is not None and abs(corr) >= min_correlation:
                    significant_correlations.append({
                        "variable1": var1,
                        "variable2": var2,
                        "correlation": corr,
                        "strength": self._interpret_correlation_strength(corr),
                        "direction": "positive" if corr > 0 else "negative"
                    })
        
        # Sort significant correlations by absolute value
        significant_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        # Generate correlation insights
        correlation_insights = self._generate_correlation_insights(significant_correlations)
        
        # Prepare visualization recommendation if requested
        visualization_recommendation = None
        if include_visualization:
            visualization_recommendation = {
                "chart_type": "heatmap",
                "description": "A correlation heatmap would be an effective visualization for this correlation matrix.",
                "alternative_charts": ["scatter matrix", "network diagram"],
                "implementation_tip": "Use a diverging color scheme, with darker colors indicating stronger correlations."
            }
        
        # Prepare the result
        result = {
            "correlation_method": correlation_method,
            "variables_analyzed": numeric_variables,
            "correlation_matrix": correlation_matrix,
            "significant_correlations": significant_correlations,
            "correlation_insights": correlation_insights
        }
        
        if visualization_recommendation:
            result["visualization_recommendation"] = visualization_recommendation
        
        return result
    
    def perform_regression_analysis(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        dependent_variable: Optional[str] = None,
        independent_variables: Optional[List[str]] = None,
        regression_type: Optional[str] = None,
        include_diagnostics: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Perform regression analysis to model relationships between variables.
        
        Args:
            dataset: List of dictionaries representing the dataset.
            dependent_variable: The target variable to predict.
            independent_variables: List of predictor variables.
            regression_type: Type of regression analysis ("linear", "multiple", "logistic").
            include_diagnostics: Whether to include detailed diagnostics.
            
        Returns:
            Dictionary containing regression results and diagnostics.
        """
        # Set default values for optional parameters
        if dataset is None:
            dataset = []
            
        if dependent_variable is None:
            dependent_variable = ""
            
        if independent_variables is None:
            independent_variables = []
            
        if regression_type is None:
            regression_type = "linear"
            
        if include_diagnostics is None:
            include_diagnostics = True
            
        logger.info(f"Performing {regression_type} regression analysis")
        
        # Validate dataset
        if not dataset:
            return {"error": "Empty dataset provided"}
        
        # Validate regression type
        if regression_type not in ["linear", "multiple", "logistic"]:
            return {"error": f"Unsupported regression type: {regression_type}"}
        
        # For logistic regression, check that dependent variable is binary
        if regression_type == "logistic":
            # Extract values for dependent variable
            y_values = [row.get(dependent_variable) for row in dataset 
                       if dependent_variable in row and row[dependent_variable] is not None]
            
            # Check if values are binary-like
            unique_values = set(y_values)
            
            # Try to convert string values to numeric if possible
            try:
                unique_values = set(float(v) if isinstance(v, str) else v for v in unique_values)
            except ValueError:
                pass
            
            if len(unique_values) > 2:
                return {"error": "Logistic regression requires a binary dependent variable"}
        
        # Perform the appropriate regression analysis
        if len(independent_variables) == 1 and regression_type == "linear":
            # Simple linear regression
            regression_results = self._perform_simple_linear_regression(
                dataset, dependent_variable, independent_variables[0]
            )
        elif regression_type == "logistic":
            # Logistic regression
            regression_results = self._perform_logistic_regression(
                dataset, dependent_variable, independent_variables
            )
        else:
            # Multiple linear regression
            regression_results = self._perform_multiple_linear_regression(
                dataset, dependent_variable, independent_variables
            )
        
        # Add regression diagnostics if requested
        if include_diagnostics and "error" not in regression_results:
            diagnostics = self._calculate_regression_diagnostics(
                dataset, dependent_variable, independent_variables, 
                regression_results, regression_type
            )
            regression_results["diagnostics"] = diagnostics
        
        # Generate insights and recommendations
        if "error" not in regression_results:
            insights_and_recommendations = self._generate_regression_insights(regression_results, regression_type)
            regression_results["insights_and_recommendations"] = insights_and_recommendations
        
        return regression_results
    
    def analyze_time_series(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        time_variable: Optional[str] = None,
        value_variables: Optional[List[str]] = None,
        analysis_components: Optional[List[str]] = None,
        forecast_periods: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze time series data to identify trends, seasonality, and patterns.
        
        Args:
            dataset: List of dictionaries representing time series data.
            time_variable: The name of the time/date variable.
            value_variables: List of variables to analyze over time.
            analysis_components: Components to analyze ("trend", "seasonality", "cycles", "outliers").
            forecast_periods: Number of periods to forecast ahead.
            
        Returns:
            Dictionary containing time series analysis results and forecasts.
        """
        # Set default values for optional parameters
        if dataset is None:
            dataset = []
            
        if time_variable is None:
            time_variable = ""
            
        if value_variables is None:
            value_variables = []
            
        if analysis_components is None:
            analysis_components = ["trend", "seasonality", "cycles", "outliers"]
            
        if forecast_periods is None:
            forecast_periods = 0
            
        logger.info(f"Analyzing time series for {len(value_variables)} variables")
        
        # Validate dataset
        if not dataset:
            return {"error": "Empty dataset provided"}
        
        # Set default analysis components if not specified
        analysis_components = analysis_components or ["trend", "seasonality", "outliers"]
        
        # Sort dataset by time variable if possible
        try:
            sorted_data = sorted(dataset, key=lambda x: x.get(time_variable, 0))
        except:
            # If sorting fails, assume data is already in chronological order
            sorted_data = dataset
        
        # Extract time points
        time_points = [row.get(time_variable) for row in sorted_data if time_variable in row]
        
        # Prepare results structure
        results = {
            "time_variable": time_variable,
            "value_variables": value_variables,
            "time_points": time_points,
            "analysis_components": analysis_components,
            "time_series_analysis": {}
        }
        
        # Analyze each value variable
        for variable in value_variables:
            # Extract time series for this variable
            time_series = []
            for row in sorted_data:
                if variable in row and row[variable] is not None and isinstance(row[variable], (int, float)):
                    time_series.append(float(row[variable]))
                else:
                    # Use None for missing values
                    time_series.append(None)
            
            # Filter out None values for calculations
            clean_series = [v for v in time_series if v is not None]
            if not clean_series:
                continue
            
            # Initialize variable results
            variable_results = {}
            
            # Analyze trend if requested
            if "trend" in analysis_components:
                trend_analysis = self._analyze_time_series_trend(clean_series)
                variable_results["trend_analysis"] = trend_analysis
            
            # Analyze seasonality if requested and enough data points
            if "seasonality" in analysis_components and len(clean_series) >= 8:  # Need at least 2 seasons of quarterly data
                seasonality_analysis = self._analyze_seasonality(clean_series)
                variable_results["seasonality_analysis"] = seasonality_analysis
            
            # Detect outliers if requested
            if "outliers" in analysis_components:
                outliers = self._detect_time_series_outliers(clean_series)
                variable_results["outliers"] = outliers
            
            # Generate simple forecast if requested
            if forecast_periods and forecast_periods > 0:
                forecast = self._generate_simple_forecast(clean_series, forecast_periods)
                variable_results["forecast"] = forecast
            
            # Add to overall results
            results["time_series_analysis"][variable] = variable_results
        
        # Generate insights and recommendations
        results["insights_and_recommendations"] = self._generate_time_series_insights(
            results["time_series_analysis"], analysis_components
        )
        
        return results
    
    def identify_outliers(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[List[str]] = None,
        method: Optional[str] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Identify outliers in the dataset using various detection methods.
        
        Args:
            dataset: List of dictionaries representing the dataset.
            variables: List of variables to check for outliers.
            method: Outlier detection method ("zscore", "iqr", "percentile").
            threshold: Threshold for determining outliers (interpretation depends on method).
            
        Returns:
            Dictionary containing identified outliers and insights.
        """
        # Set default values for optional parameters
        if dataset is None:
            dataset = []
            
        if variables is None:
            variables = []
            
        if method is None:
            method = "zscore"
            
        if threshold is None:
            if method == "zscore":
                threshold = 3.0
            elif method == "iqr":
                threshold = 1.5
            elif method == "percentile":
                threshold = 0.95
            else:
                threshold = 3.0
            
        logger.info(f"Identifying outliers using {method} method")
        
        # Validate dataset
        if not dataset:
            return {"error": "Empty dataset provided"}
        
        # Extract numeric variables if variables not specified
        if not variables:
            variables = list(dataset[0].keys())
        
        # Filter for numeric variables only
        numeric_variables = self._filter_numeric_variables(dataset, variables)
        if not numeric_variables:
            return {"error": "Outlier detection requires at least one numeric variable"}
        
        # Set default thresholds based on method
        if threshold is None:
            if method == "zscore":
                threshold = 3.0
            elif method == "iqr":
                threshold = 1.5
            elif method == "percentile":
                threshold = 5.0  # 5th and 95th percentiles
            else:
                threshold = 3.0  # Default
        
        # Prepare method details
        method_details = {
            "zscore": {
                "name": "Z-Score Method",
                "description": f"Identifies values that are more than {threshold} standard deviations from the mean.",
                "threshold": threshold
            },
            "iqr": {
                "name": "Interquartile Range (IQR) Method",
                "description": f"Identifies values below Q1-{threshold}*IQR or above Q3+{threshold}*IQR.",
                "threshold": threshold
            },
            "percentile": {
                "name": "Percentile Method",
                "description": f"Identifies values below the {threshold}th percentile or above the {100-threshold}th percentile.",
                "threshold": threshold
            }
        }
        
        # Initialize results
        results = {
            "detection_method": method_details.get(method, {"name": "Custom Method", "threshold": threshold}),
            "variables_analyzed": numeric_variables,
            "outliers_detected": {}
        }
        
        # Detect outliers for each variable
        total_outliers = 0
        
        for variable in numeric_variables:
            # Extract values
            values = [float(row.get(variable)) for row in dataset if variable in row 
                     and row[variable] is not None and isinstance(row[variable], (int, float))]
            
            if not values:
                continue
            
            # Detect outliers using the specified method
            outlier_indices = []
            if method == "zscore":
                outlier_indices = self._detect_outliers_zscore(values, threshold)
            elif method == "iqr":
                outlier_indices = self._detect_outliers_iqr(values, threshold)
            elif method == "percentile":
                outlier_indices = self._detect_outliers_percentile(values, threshold)
            else:
                # Default to Z-score
                outlier_indices = self._detect_outliers_zscore(values, threshold)
            
            # Record outliers if found
            if outlier_indices:
                outlier_values = [values[i] for i in outlier_indices]
                results["outliers_detected"][variable] = {
                    "count": len(outlier_values),
                    "percentage": (len(outlier_values) / len(values)) * 100,
                    "values": outlier_values[:10] if len(outlier_values) > 10 else outlier_values,  # Limit to first 10
                    "summary": {
                        "min": min(outlier_values) if outlier_values else None,
                        "max": max(outlier_values) if outlier_values else None,
                        "mean": sum(outlier_values) / len(outlier_values) if outlier_values else None
                    }
                }
                total_outliers += len(outlier_values)
        
        # Add summary statistics
        results["summary"] = {
            "total_outliers_detected": total_outliers,
            "variables_with_outliers": len(results["outliers_detected"])
        }
        
        # Generate insights and recommendations
        results["insights_and_recommendations"] = self._generate_outlier_insights(
            results["outliers_detected"], method
        )
        
        return results
    
    def generate_visualizations(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        visualization_type: Optional[str] = None,
        variables: Optional[List[str]] = None,
        title: Optional[str] = None,
        additional_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate visualization recommendations based on data and visualization type.
        
        Args:
            dataset: List of dictionaries representing the dataset.
            visualization_type: Type of visualization to generate (e.g., "bar", "line", "scatter").
            variables: List of variables to include in the visualization.
            title: Optional title for the visualization.
            additional_options: Optional additional visualization options.
            
        Returns:
            Dictionary containing visualization specifications and recommendations.
        """
        # Set default values for optional parameters
        if dataset is None:
            dataset = []
            
        if visualization_type is None:
            visualization_type = "auto"
            
        if variables is None:
            variables = []
            
        if title is None:
            title = "Data Visualization"
            
        if additional_options is None:
            additional_options = {}
            
        logger.info(f"Generating {visualization_type} visualization for {', '.join(variables)}")
        
        # Validate dataset
        if not dataset:
            return {"error": "Empty dataset provided"}
        
        # Set default title if not provided
        if not title:
            title = f"{visualization_type.capitalize()} of {', '.join(variables)}"
        
        # Initialize additional options if not provided
        additional_options = additional_options or {}
        
        # Generate visualization specification based on type
        visualization_spec = self._generate_visualization_spec(
            visualization_type, variables, title, additional_options
        )
        
        # Validate variables exist in dataset
        missing_variables = [var for var in variables if var not in dataset[0]]
        if missing_variables:
            return {"error": f"Variables not found in dataset: {', '.join(missing_variables)}"}
        
        # Analyze data characteristics to provide customization recommendations
        data_characteristics = self._analyze_data_for_visualization(dataset, variables)
        
        # Generate recommendations for effective visualization
        recommendations = self._generate_visualization_recommendations(
            visualization_type, variables, data_characteristics
        )
        
        # Return visualization information
        result = {
            "visualization_type": visualization_type,
            "variables": variables,
            "title": title,
            "specification": visualization_spec,
            "data_characteristics": data_characteristics,
            "recommendations": recommendations
        }
        
        return result
    
    def segment_data(
        self,
        dataset: Optional[List[Dict[str, Any]]] = None,
        segmentation_variables: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        min_segment_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Segment the dataset and analyze differences between segments.
        
        Args:
            dataset: List of dictionaries representing the dataset.
            segmentation_variables: Variables to use for segmentation.
            metrics: Metrics to calculate for each segment.
            min_segment_size: Minimum number of records for a valid segment.
            
        Returns:
            Dictionary containing segment analysis and comparisons.
        """
        # Set default values for optional parameters
        if dataset is None:
            dataset = []
            
        if segmentation_variables is None:
            segmentation_variables = []
            
        if metrics is None:
            metrics = []
            
        if min_segment_size is None:
            min_segment_size = 5
            
        logger.info(f"Segmenting data using {', '.join(segmentation_variables)}")
        
        # Validate dataset
        if not dataset:
            return {"error": "Empty dataset provided"}
        
        # Set default minimum segment size if not specified
        if min_segment_size is None:
            min_segment_size = max(5, int(len(dataset) * 0.05))  # 5% of dataset or at least 5 rows
        
        # Validate segmentation variables and metrics exist in dataset
        all_variables = segmentation_variables + metrics
        missing_variables = [var for var in all_variables if var not in dataset[0]]
        if missing_variables:
            return {"error": f"Variables not found in dataset: {', '.join(missing_variables)}"}
        
        # Determine if metrics are numeric
        numeric_metrics = self._filter_numeric_variables(dataset, metrics)
        if not numeric_metrics:
            return {"error": "Segmentation requires at least one numeric metric"}
        
        # Create segments based on segmentation variables
        segments = self._create_segments(dataset, segmentation_variables)
        
        # Filter out segments that are too small
        segments = {key: data for key, data in segments.items() if len(data) >= min_segment_size}
        
        if not segments:
            return {"error": f"No segments meet the minimum size requirement of {min_segment_size} rows"}
        
        # Calculate metrics for each segment
        segment_metrics = {}
        for segment_name, segment_data in segments.items():
            segment_metrics[segment_name] = {
                "size": len(segment_data),
                "percentage": (len(segment_data) / len(dataset)) * 100,
                "metrics": {}
            }
            
            # Calculate metrics for this segment
            for metric in numeric_metrics:
                values = [float(row.get(metric)) for row in segment_data if metric in row 
                         and row[metric] is not None and isinstance(row[metric], (int, float))]
                
                if values:
                    # Calculate basic statistics for this metric
                    segment_metrics[segment_name]["metrics"][metric] = {
                        "mean": sum(values) / len(values),
                        "median": self._calculate_median(values),
                        "std_dev": self._calculate_standard_deviation(values),
                        "min": min(values),
                        "max": max(values)
                    }
        
        # Compare metrics across segments
        metric_comparisons = self._compare_segments(segment_metrics, numeric_metrics)
        
        # Generate insights about segments
        segment_insights = self._generate_segment_insights(segment_metrics, metric_comparisons)
        
        # Return segmentation results
        result = {
            "segmentation_variables": segmentation_variables,
            "metrics_analyzed": numeric_metrics,
            "total_segments": len(segments),
            "segment_details": segment_metrics,
            "metric_comparisons": metric_comparisons,
            "segment_insights": segment_insights
        }
        
        return result
    
    # Helper methods for analyze_dataset
    
    def _calculate_summary_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate summary statistics for a list of numeric values."""
        if not values:
            return {}
        
        # Sort values for quartile calculations
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate quartiles
        q1_idx = n // 4
        q2_idx = n // 2  # median
        q3_idx = (3 * n) // 4
        
        q1 = sorted_values[q1_idx]
        median = sorted_values[q2_idx] if n % 2 == 1 else (sorted_values[q2_idx-1] + sorted_values[q2_idx]) / 2
        q3 = sorted_values[q3_idx]
        
        # Calculate mean
        mean = sum(values) / n
        
        # Calculate variance and standard deviation
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)
        
        # Calculate additional statistics
        stats = {
            "count": n,
            "mean": mean,
            "median": median,
            "std_dev": std_dev,
            "variance": variance,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "q1": q1,
            "q3": q3,
            "iqr": q3 - q1
        }
        
        return stats
    
    def _generate_data_quality_insights(
        self,
        missing_values: Dict[str, Dict[str, Any]],
        data_types: Dict[str, str],
        dataset: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights about data quality."""
        insights = []
        
        # Check for variables with high missing values
        high_missing = [
            var for var, info in missing_values.items() 
            if info["percentage"] > 10  # More than 10% missing
        ]
        
        if high_missing:
            if len(high_missing) > 3:
                insights.append(f"{len(high_missing)} variables have more than 10% missing values, which may impact analysis quality.")
            else:
                insights.append(f"Variables {', '.join(high_missing)} have more than 10% missing values, which may impact analysis quality.")
        
        # Check for mixed data types
        mixed_types = [var for var, type_name in data_types.items() if type_name == "mixed"]
        if mixed_types:
            insights.append(f"Variables {', '.join(mixed_types)} have mixed data types, which may require cleaning or transformation.")
        
        # Check dataset size
        if len(dataset) < 30:
            insights.append("The dataset has fewer than 30 rows, which may limit statistical reliability.")
        
        # Add generic insight if no specific issues found
        if not insights:
            insights.append("The dataset appears to have good overall quality with limited missing values and consistent data types.")
        
        return insights
    
    def _generate_variable_insights(
        self,
        summary_statistics: Dict[str, Dict[str, float]],
        value_counts: Dict[str, List[Tuple[Any, int]]]
    ) -> Dict[str, List[str]]:
        """Generate insights about variables based on their statistics."""
        variable_insights = {}
        
        # Generate insights for numeric variables
        for var, stats in summary_statistics.items():
            var_insights = []
            
            # Check for skewness using mean and median difference
            if "mean" in stats and "median" in stats:
                mean_median_diff = (stats["mean"] - stats["median"]) / stats["std_dev"] if stats["std_dev"] > 0 else 0
                if abs(mean_median_diff) > 0.5:
                    skew_direction = "right" if mean_median_diff > 0 else "left"
                    var_insights.append(f"The distribution appears {skew_direction}-skewed (mean {stats['mean']:.2f}, median {stats['median']:.2f}).")
            
            # Check for outliers using IQR
            if "q1" in stats and "q3" in stats and "iqr" in stats:
                lower_bound = stats["q1"] - 1.5 * stats["iqr"]
                upper_bound = stats["q3"] + 1.5 * stats["iqr"]
                potential_outliers = (stats["min"] < lower_bound) or (stats["max"] > upper_bound)
                
                if potential_outliers:
                    var_insights.append(f"Potential outliers detected (values outside the range of {lower_bound:.2f} to {upper_bound:.2f}).")
            
            # Check for high variance
            if "mean" in stats and "std_dev" in stats and stats["mean"] != 0:
                cv = stats["std_dev"] / abs(stats["mean"])  # Coefficient of variation
                if cv > 1.0:
                    var_insights.append(f"High variability detected (coefficient of variation: {cv:.2f}).")
            
            # Add insights for this variable
            if var_insights:
                variable_insights[var] = var_insights
        
        # Generate insights for categorical variables
        for var, counts in value_counts.items():
            var_insights = []
            
            # Check for dominant categories
            if counts and len(counts) > 1:
                top_value, top_count = counts[0]
                total_count = sum(count for _, count in counts)
                
                if top_count > total_count * 0.75:
                    var_insights.append(f"Dominant category detected: '{top_value}' accounts for {(top_count/total_count)*100:.1f}% of values.")
                
                # Check for long tail distribution
                if len(counts) > 5:
                    top_5_pct = sum(count for _, count in counts[:5]) / total_count
                    if top_5_pct > 0.9:
                        var_insights.append(f"Long tail distribution detected: top 5 categories account for {top_5_pct*100:.1f}% of values.")
            
            # Add insights for this variable
            if var_insights and var not in variable_insights:
                variable_insights[var] = var_insights
        
        return variable_insights
    
    def _generate_analysis_recommendations(
        self,
        data_types: Dict[str, str],
        missing_values: Dict[str, Dict[str, Any]],
        summary_statistics: Dict[str, Dict[str, float]],
        analysis_goals: List[str]
    ) -> List[str]:
        """Generate recommendations for further analysis based on data characteristics."""
        recommendations = []
        
        # Identify numeric variables
        numeric_vars = [var for var, type_name in data_types.items() if type_name == "numeric"]
        
        # Identify categorical variables
        categorical_vars = [var for var, type_name in data_types.items() if type_name == "categorical"]
        
        # Recommend correlation analysis if multiple numeric variables exist
        if len(numeric_vars) >= 2:
            recommendations.append(f"Perform correlation analysis on numeric variables {', '.join(numeric_vars[:3])} (and others) to identify relationships.")
        
        # Recommend distribution analysis for numeric variables with potential outliers
        outlier_candidates = []
        for var, stats in summary_statistics.items():
            if "iqr" in stats and stats["iqr"] > 0:
                lower_bound = stats["q1"] - 1.5 * stats["iqr"]
                upper_bound = stats["q3"] + 1.5 * stats["iqr"]
                if stats["min"] < lower_bound or stats["max"] > upper_bound:
                    outlier_candidates.append(var)
        
        if outlier_candidates:
            recommendations.append(f"Analyze distributions and consider outlier treatment for variables {', '.join(outlier_candidates[:3])}{'...' if len(outlier_candidates) > 3 else ''}.")
        
        # Recommend missing value treatment if significant missing values exist
        high_missing = [var for var, info in missing_values.items() if info["percentage"] > 5]
        if high_missing:
            recommendations.append(f"Address missing values in {', '.join(high_missing[:3])}{'...' if len(high_missing) > 3 else ''} before proceeding with advanced analysis.")
        
        # Recommend segmentation analysis if categorical variables exist
        if categorical_vars and numeric_vars:
            recommendations.append(f"Consider segmentation analysis using categorical variables {', '.join(categorical_vars[:2])} to compare differences in {', '.join(numeric_vars[:2])}.")
        
        # Add goal-specific recommendations
        for goal in analysis_goals:
            goal_lower = goal.lower()
            
            if "correlation" in goal_lower or "relationship" in goal_lower:
                if len(numeric_vars) >= 2:
                    recommendations.append("Use scatter plots and correlation matrix to visualize relationships between numerical variables.")
                    
            elif "pattern" in goal_lower or "cluster" in goal_lower:
                if len(numeric_vars) >= 2:
                    recommendations.append("Consider clustering analysis to identify natural groupings in the data.")
                    
            elif "predict" in goal_lower or "forecast" in goal_lower:
                if len(numeric_vars) >= 2:
                    recommendations.append("Consider regression analysis to build predictive models using the available variables.")
        
        return recommendations
    
    # Helper methods for perform_statistical_analysis
    
    def _calculate_descriptive_statistics(
        self, 
        dataset: List[Dict[str, Any]], 
        variables: List[str],
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate descriptive statistics for specified variables, optionally grouped."""
        # If grouping is requested
        if group_by:
            # Group data
            grouped_data = {}
            for row in dataset:
                if group_by not in row:
                    continue  # Skip rows without group variable
                    
                group_value = row.get(group_by)
                if group_value not in grouped_data:
                    grouped_data[group_value] = []
                grouped_data[group_value].append(row)
            
            # Calculate stats for each group
            group_stats = {}
            for group_value, group_dataset in grouped_data.items():
                group_stats[group_value] = self._calculate_stats_for_variables(group_dataset, variables)
            
            return {
                "grouped_by": group_by,
                "groups": group_stats
            }
        
        # If no grouping
        return self._calculate_stats_for_variables(dataset, variables)
    
    def _calculate_stats_for_variables(self, dataset: List[Dict[str, Any]], variables: List[str]) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics for each variable in the dataset."""
        stats = {}
        
        for variable in variables:
            # Extract values for this variable
            values = [row.get(variable) for row in dataset if variable in row and row[variable] is not None]
            
            # Skip empty columns
            if not values:
                continue
            
            # Check if values are numeric
            if all(isinstance(v, (int, float)) for v in values):
                # Calculate numeric statistics
                numeric_values = [float(v) for v in values]
                
                var_stats = {
                    "count": len(numeric_values),
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "range": max(numeric_values) - min(numeric_values),
                    "sum": sum(numeric_values),
                    "mean": sum(numeric_values) / len(numeric_values),
                    "data_type": "numeric"
                }
                
                # Calculate median
                sorted_values = sorted(numeric_values)
                n = len(sorted_values)
                if n % 2 == 0:
                    var_stats["median"] = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
                else:
                    var_stats["median"] = sorted_values[n//2]
                
                # Calculate variance
                if len(numeric_values) > 1:
                    mean = var_stats["mean"]
                    variance = sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)
                    var_stats["variance"] = variance
                    var_stats["std_dev"] = variance ** 0.5
                
                # Calculate quartiles
                if n >= 4:
                    var_stats["q1"] = sorted_values[n//4]
                    var_stats["q3"] = sorted_values[(3*n)//4]
                    var_stats["iqr"] = var_stats["q3"] - var_stats["q1"]
                
            else:
                # For categorical data, calculate frequency distribution
                value_counts = {}
                for value in values:
                    if value in value_counts:
                        value_counts[value] += 1
                    else:
                        value_counts[value] = 1
                
                # Get most common value(s)
                max_count = max(value_counts.values())
                most_common = [k for k, v in value_counts.items() if v == max_count]
                
                var_stats = {
                    "count": len(values),
                    "unique_values": len(value_counts),
                    "most_common": most_common[0] if len(most_common) == 1 else most_common,
                    "frequency": value_counts,
                    "data_type": "categorical"
                }
            
            stats[variable] = var_stats
        
        return stats
    
    def _perform_comparative_analysis(
        self,
        dataset: List[Dict[str, Any]],
        variables: List[str],
        group_by: str,
        confidence_level: float
    ) -> Dict[str, Any]:
        """Perform comparative analysis of variables between groups."""
        # Group data
        grouped_data = {}
        for row in dataset:
            if group_by not in row:
                continue  # Skip rows without group variable
                
            group_value = row.get(group_by)
            if group_value not in grouped_data:
                grouped_data[group_value] = []
            grouped_data[group_value].append(row)
        
        if len(grouped_data) < 2:
            return {"error": "Comparative analysis requires at least two groups"}
        
        # Calculate statistics for each group
        group_stats = {}
        for group_value, group_dataset in grouped_data.items():
            group_stats[group_value] = self._calculate_stats_for_variables(group_dataset, variables)
        
        # Perform comparisons between groups
        comparisons = {}
        
        # Get numeric variables
        numeric_vars = []
        for var in variables:
            is_numeric = all(
                isinstance(group_stats[group].get(var, {}).get("mean"), (int, float))
                for group in group_stats
                if var in group_stats[group]
            )
            if is_numeric:
                numeric_vars.append(var)
        
        # Compare means and variances for numeric variables
        for var in numeric_vars:
            var_comparisons = []
            groups = [group for group in group_stats if var in group_stats[group]]
            
            # Need at least two groups with this variable
            if len(groups) < 2:
                continue
            
            # Calculate overall statistics
            all_values = []
            for group in groups:
                group_var_stats = group_stats[group][var]
                if "mean" in group_var_stats:  # Ensure numeric variable
                    all_values.extend([
                        row.get(var) for row in grouped_data[group]
                        if var in row and row[var] is not None and isinstance(row[var], (int, float))
                    ])
            
            if not all_values:
                continue
            
            overall_mean = sum(all_values) / len(all_values)
            
            # Compare each pair of groups
            for i, group1 in enumerate(groups):
                for group2 in groups[i+1:]:
                    # Get values for both groups
                    values1 = [
                        float(row.get(var)) for row in grouped_data[group1]
                        if var in row and row[var] is not None and isinstance(row[var], (int, float))
                    ]
                    values2 = [
                        float(row.get(var)) for row in grouped_data[group2]
                        if var in row and row[var] is not None and isinstance(row[var], (int, float))
                    ]
                    
                    if not values1 or not values2:
                        continue
                    
                    # Get means
                    mean1 = sum(values1) / len(values1)
                    mean2 = sum(values2) / len(values2)
                    
                    # Calculate mean difference
                    mean_diff = mean1 - mean2
                    
                    # Calculate pooled standard deviation for t-test
                    n1 = len(values1)
                    n2 = len(values2)
                    
                    var1 = sum((x - mean1) ** 2 for x in values1) / n1
                    var2 = sum((x - mean2) ** 2 for x in values2) / n2
                    
                    # Pooled standard deviation
                    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
                    
                    # Calculate t-statistic
                    if pooled_std > 0:
                        t_stat = mean_diff / (pooled_std * math.sqrt(1/n1 + 1/n2))
                    else:
                        t_stat = 0
                    
                    # Determine significance
                    # This is a simplified approach without proper p-value calculation
                    significant = abs(t_stat) > 2.0  # Approximately 95% confidence
                    
                    # Add comparison
                    var_comparisons.append({
                        "groups_compared": [group1, group2],
                        "mean_difference": mean_diff,
                        "percentage_difference": (mean_diff / ((mean1 + mean2) / 2)) * 100 if (mean1 + mean2) != 0 else 0,
                        "t_statistic": t_stat,
                        "significant_difference": significant,
                        "group1_mean": mean1,
                        "group2_mean": mean2
                    })
            
            comparisons[var] = var_comparisons
        
        return {
            "group_statistics": group_stats,
            "comparisons": comparisons
        }
    
    def _analyze_distributions(
        self,
        dataset: List[Dict[str, Any]],
        variables: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze the distribution characteristics of numeric variables."""
        distribution_analysis = {}
        
        for variable in variables:
            # Extract values
            values = [float(row.get(variable)) for row in dataset if variable in row 
                     and row[variable] is not None and isinstance(row[variable], (int, float))]
            
            if not values:
                continue
            
            # Calculate basic statistics
            n = len(values)
            mean = sum(values) / n
            
            # Calculate variance and standard deviation
            variance = sum((x - mean) ** 2 for x in values) / n
            std_dev = math.sqrt(variance)
            
            # Sort values for quantile calculations
            sorted_values = sorted(values)
            
            # Calculate quartiles
            q1 = sorted_values[n // 4]
            median = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            q3 = sorted_values[(3 * n) // 4]
            iqr = q3 - q1
            
            # Calculate skewness
            if std_dev > 0:
                skewness = sum((x - mean) ** 3 for x in values) / (n * std_dev ** 3)
            else:
                skewness = 0
            
            # Calculate kurtosis
            if std_dev > 0:
                kurtosis = sum((x - mean) ** 4 for x in values) / (n * std_dev ** 4) - 3
            else:
                kurtosis = 0
            
            # Determine distribution shape based on skewness and kurtosis
            shape = "approximately normal"
            if abs(skewness) > 1:
                shape = "highly skewed"
            elif abs(skewness) > 0.5:
                shape = "moderately skewed"
                
            skew_direction = "right-skewed (positive)" if skewness > 0 else "left-skewed (negative)" if skewness < 0 else "symmetric"
            
            # Check for potential outliers using IQR method
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [x for x in values if x < lower_bound or x > upper_bound]
            
            # Generate histogram bins (simplified)
            num_bins = min(10, n // 5) if n > 10 else 5
            bin_width = (max(values) - min(values)) / num_bins if max(values) > min(values) else 1
            
            histogram = []
            for i in range(num_bins):
                bin_lower = min(values) + i * bin_width
                bin_upper = min(values) + (i + 1) * bin_width
                bin_count = sum(1 for x in values if bin_lower <= x < bin_upper or (i == num_bins - 1 and x == bin_upper))
                
                histogram.append({
                    "bin_range": [bin_lower, bin_upper],
                    "count": bin_count,
                    "percentage": (bin_count / n) * 100
                })
            
            # Store distribution analysis
            distribution_analysis[variable] = {
                "statistics": {
                    "mean": mean,
                    "median": median,
                    "std_dev": std_dev,
                    "min": min(values),
                    "max": max(values),
                    "range": max(values) - min(values),
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "skewness": skewness,
                    "kurtosis": kurtosis
                },
                "shape": {
                    "distribution_shape": shape,
                    "skew_direction": skew_direction,
                    "peakedness": "leptokurtic (heavy-tailed)" if kurtosis > 0.5 else "platykurtic (light-tailed)" if kurtosis < -0.5 else "mesokurtic"
                },
                "outliers": {
                    "count": len(outliers),
                    "percentage": (len(outliers) / n) * 100 if n > 0 else 0,
                    "values": outliers[:10] if len(outliers) > 10 else outliers  # Limit to first 10
                },
                "histogram": histogram
            }
            
            # Add normality assessment
            if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
                distribution_analysis[variable]["normality"] = "Distribution appears approximately normal"
            else:
                reasons = []
                if abs(skewness) >= 0.5:
                    reasons.append(f"skewness of {skewness:.2f}")
                if abs(kurtosis) >= 0.5:
                    reasons.append(f"kurtosis of {kurtosis:.2f}")
                
                distribution_analysis[variable]["normality"] = f"Distribution deviates from normal ({', '.join(reasons)})"
        
        return distribution_analysis
    
    def _perform_basic_hypothesis_tests(
        self,
        dataset: List[Dict[str, Any]],
        variables: List[str],
        confidence_level: float
    ) -> Dict[str, Dict[str, Any]]:
        """Perform basic hypothesis tests on numeric variables."""
        hypothesis_tests = {}
        
        for variable in variables:
            # Extract values
            values = [float(row.get(variable)) for row in dataset if variable in row 
                     and row[variable] is not None and isinstance(row[variable], (int, float))]
            
            if not values:
                continue
            
            # One-sample t-test against mean=0
            n = len(values)
            sample_mean = sum(values) / n
            
            # Calculate sample standard deviation
            if n > 1:
                variance = sum((x - sample_mean) ** 2 for x in values) / (n - 1)  # Use (n-1) for sample
                std_dev = math.sqrt(variance)
                
                # Calculate t-statistic
                test_value = 0  # Testing against mean=0
                t_stat = (sample_mean - test_value) / (std_dev / math.sqrt(n))
                
                # Get critical value for the given confidence level
                alpha = 1 - confidence_level
                # This is an approximation, as proper t-distribution would require more complex computation
                critical_value = 1.96  # Approximately for 95% confidence
                if confidence_level >= 0.99:
                    critical_value = 2.58
                elif confidence_level >= 0.90:
                    critical_value = 1.64
                
                # Determine if null hypothesis is rejected
                null_rejected = abs(t_stat) > critical_value
                
                # Store test results
                hypothesis_tests[variable] = {
                    "test_type": "one-sample t-test",
                    "null_hypothesis": f"The population mean equals {test_value}",
                    "alternative_hypothesis": f"The population mean does not equal {test_value}",
                    "sample_size": n,
                    "sample_mean": sample_mean,
                    "sample_std_dev": std_dev,
                    "t_statistic": t_stat,
                    "critical_value": critical_value,
                    "confidence_level": confidence_level,
                    "null_hypothesis_rejected": null_rejected,
                    "conclusion": f"{'Reject' if null_rejected else 'Fail to reject'} the null hypothesis that the mean equals {test_value}."
                }
            else:
                hypothesis_tests[variable] = {
                    "error": "Insufficient data for hypothesis testing (need at least 2 values)"
                }
        
        return hypothesis_tests
    
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
                except (ValueError, TypeError):
                    return False
        return False
    
    def _generate_analysis_summary(self, results: Dict[str, Any], analysis_type: str) -> str:
        """Generate a summary of the analysis results."""
        if analysis_type == "descriptive":
            stats = results.get("descriptive_statistics", {})
            if "grouped_by" in stats:
                return f"Descriptive statistics calculated for {len(results.get('variables_analyzed', []))} variables across {len(stats.get('groups', {}))} groups defined by {stats.get('grouped_by')}."
            
            # Count numeric and categorical variables
            num_numeric = 0
            num_categorical = 0
            
            for var_stats in stats.values():
                if isinstance(var_stats, dict):
                    data_type = var_stats.get("data_type")
                    if data_type == "numeric":
                        num_numeric += 1
                    elif data_type == "categorical":
                        num_categorical += 1
            
            return f"Descriptive statistics calculated for {results.get('sample_size', 'unknown')} data points across {num_numeric} numeric and {num_categorical} categorical variables."
        
        elif analysis_type == "comparative":
            comparisons = results.get("comparative_analysis", {}).get("comparisons", {})
            significant_diffs = 0
            
            for var, var_comparisons in comparisons.items():
                for comparison in var_comparisons:
                    if comparison.get("significant_difference", False):
                        significant_diffs += 1
            
            return f"Comparative analysis identified {significant_diffs} significant differences across {len(comparisons)} variables between groups."
        
        elif analysis_type == "distribution":
            distributions = results.get("distribution_analysis", {})
            normal_vars = sum(1 for var_data in distributions.values() 
                             if "normality" in var_data and "approximately normal" in var_data["normality"])
            
            return f"Distribution analysis of {len(distributions)} variables found {normal_vars} with approximately normal distributions and {len(distributions) - normal_vars} with non-normal characteristics."
        
        elif analysis_type == "hypothesis":
            tests = results.get("hypothesis_tests", {})
            rejected = sum(1 for test in tests.values() if test.get("null_hypothesis_rejected", False))
            
            return f"Hypothesis testing of {len(tests)} variables resulted in rejecting the null hypothesis for {rejected} variables at the {results.get('confidence_level', 0.95)*100}% confidence level."
        
        else:
            return f"Analysis completed for {analysis_type} with {results.get('sample_size', 'unknown')} data points."
    
    # Helper methods for analyze_correlation
    
    def _calculate_correlation_matrix(
        self,
        dataset: List[Dict[str, Any]],
        variables: List[str],
        method: str = "pearson"
    ) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix between numeric variables."""
        # Initialize correlation matrix
        correlation_matrix = {var: {other_var: None for other_var in variables} for var in variables}
        
        # Extract values for each variable
        var_values = {}
        for var in variables:
            var_values[var] = [float(row.get(var, 0)) for row in dataset if var in row 
                              and row[var] is not None and isinstance(row[var], (int, float))]
        
        # Calculate correlation for each pair of variables
        for var1 in variables:
            for var2 in variables:
                # Diagonal elements (correlation with self) are always 1
                if var1 == var2:
                    correlation_matrix[var1][var2] = 1.0
                    continue
                
                # If already calculated (matrix is symmetric)
                if correlation_matrix[var2][var1] is not None:
                    correlation_matrix[var1][var2] = correlation_matrix[var2][var1]
                    continue
                
                # Get values for both variables
                values1 = var_values[var1]
                values2 = var_values[var2]
                
                # Ensure same length by using only rows where both variables have values
                common_indices = []
                for i, (row) in enumerate(dataset):
                    if (var1 in row and row[var1] is not None and isinstance(row[var1], (int, float)) and
                        var2 in row and row[var2] is not None and isinstance(row[var2], (int, float))):
                        common_indices.append(i)
                
                # Extract common values
                values1 = [float(dataset[i][var1]) for i in common_indices]
                values2 = [float(dataset[i][var2]) for i in common_indices]
                
                # Skip if insufficient data
                if len(values1) < 2:
                    correlation_matrix[var1][var2] = None
                    continue
                
                # Calculate correlation based on method
                if method.lower() == "pearson":
                    correlation = self._calculate_pearson_correlation(values1, values2)
                elif method.lower() == "spearman":
                    correlation = self._calculate_spearman_correlation(values1, values2)
                else:
                    # Default to Pearson
                    correlation = self._calculate_pearson_correlation(values1, values2)
                
                correlation_matrix[var1][var2] = correlation
        
        return correlation_matrix
    
    def _calculate_pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient between two lists of values."""
        if len(x) != len(y) or len(x) < 2:
            return None
        
        n = len(x)
        
        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        # Calculate covariance and variances
        covariance = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        var_x = sum((val - mean_x) ** 2 for val in x) / n
        var_y = sum((val - mean_y) ** 2 for val in y) / n
        
        # Handle division by zero
        if var_x == 0 or var_y == 0:
            return 0
        
        # Calculate correlation
        correlation = covariance / (math.sqrt(var_x) * math.sqrt(var_y))
        
        # Ensure correlation is in [-1, 1]
        return max(-1.0, min(1.0, correlation))
    
    def _calculate_spearman_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Spearman rank correlation coefficient between two lists of values."""
        if len(x) != len(y) or len(x) < 2:
            return None
        
        n = len(x)
        
        # Convert values to ranks
        rank_x = self._rank_values(x)
        rank_y = self._rank_values(y)
        
        # Calculate Pearson correlation on ranks
        return self._calculate_pearson_correlation(rank_x, rank_y)
    
    def _rank_values(self, values: List[float]) -> List[float]:
        """Convert values to ranks."""
        # Create (value, index) pairs
        indexed_values = [(value, i) for i, value in enumerate(values)]
        
        # Sort by value
        indexed_values.sort(key=lambda x: x[0])
        
        # Assign ranks (handling ties with average rank)
        ranks = [0] * len(values)
        i = 0
        while i < len(indexed_values):
            # Find all tied values
            j = i
            while j < len(indexed_values) - 1 and indexed_values[j][0] == indexed_values[j + 1][0]:
                j += 1
            
            # Assign average rank to all tied values
            avg_rank = (i + j) / 2 + 1  # +1 because ranks start at 1
            for k in range(i, j + 1):
                ranks[indexed_values[k][1]] = avg_rank
            
            i = j + 1
        
        return ranks
    
    def _interpret_correlation_strength(self, correlation: float) -> str:
        """Interpret the strength of a correlation coefficient."""
        if correlation is None:
            return "unknown"
        
        abs_corr = abs(correlation)
        
        if abs_corr < 0.1:
            return "negligible"
        elif abs_corr < 0.3:
            return "weak"
        elif abs_corr < 0.5:
            return "moderate"
        elif abs_corr < 0.7:
            return "strong"
        else:
            return "very strong"
    
    def _generate_correlation_insights(self, significant_correlations: List[Dict[str, Any]]) -> List[str]:
        """Generate insights based on significant correlations."""
        if not significant_correlations:
            return ["No significant correlations were found between the analyzed variables."]
        
        insights = []
        
        # Highlight strongest positive correlation
        positive_correlations = [c for c in significant_correlations if c["correlation"] > 0]
        if positive_correlations:
            strongest_positive = max(positive_correlations, key=lambda x: x["correlation"])
            insights.append(
                f"Strongest positive correlation ({strongest_positive['correlation']:.2f}) exists between "
                f"{strongest_positive['variable1']} and {strongest_positive['variable2']}, indicating they "
                f"tend to increase together."
            )
        
        # Highlight strongest negative correlation
        negative_correlations = [c for c in significant_correlations if c["correlation"] < 0]
        if negative_correlations:
            strongest_negative = min(negative_correlations, key=lambda x: x["correlation"])
            insights.append(
                f"Strongest negative correlation ({strongest_negative['correlation']:.2f}) exists between "
                f"{strongest_negative['variable1']} and {strongest_negative['variable2']}, indicating "
                f"they tend to move in opposite directions."
            )
        
        # Highlight total number of strong correlations
        strong_correlations = [c for c in significant_correlations if abs(c["correlation"]) >= 0.7]
        if strong_correlations:
            insights.append(
                f"Found {len(strong_correlations)} strong correlations (|r| ≥ 0.7), suggesting several "
                f"important relationships in the data."
            )
        
        # Add insight about correlation clusters if applicable
        if len(significant_correlations) > 5:
            insights.append(
                f"The presence of multiple significant correlations suggests potential underlying "
                f"factors that may influence multiple variables simultaneously."
            )
        
        return insights
    
    # Helper methods for perform_regression_analysis
    
    def _perform_simple_linear_regression(
        self, 
        dataset: List[Dict[str, Any]], 
        dependent_var: str, 
        independent_var: str
    ) -> Dict[str, Any]:
        """Perform simple linear regression with one independent variable."""
        # Extract data points with both variables
        data_points = [
            (float(row[independent_var]), float(row[dependent_var]))
            for row in dataset
            if (independent_var in row and row[independent_var] is not None and 
                dependent_var in row and row[dependent_var] is not None and
                isinstance(row[independent_var], (int, float)) and
                isinstance(row[dependent_var], (int, float)))
        ]
        
        if len(data_points) < 2:
            return {"error": "Insufficient data points for regression (need at least 2)"}
        
        # Extract x and y values
        x_values = [point[0] for point in data_points]
        y_values = [point[1] for point in data_points]
        n = len(data_points)
        
        # Calculate means
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # Calculate coefficient (slope)
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        # Handle division by zero
        if denominator == 0:
            return {"error": "Cannot calculate regression: no variance in independent variable"}
        
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
        
        # Calculate adjusted R-squared
        adjusted_r_squared = 1 - ((1 - r_squared) * (n - 1) / (n - 2)) if n > 2 else 0
        
        # Calculate standard error of estimate
        se_estimate = math.sqrt(ss_residual / (n - 2)) if n > 2 else 0
        
        # Create equation string
        equation = f"{dependent_var} = {intercept:.4f} + {slope:.4f} × {independent_var}"
        
        # Calculate F-statistic
        ms_regression = (ss_total - ss_residual) / 1  # 1 degree of freedom for simple regression
        ms_residual = ss_residual / (n - 2) if n > 2 else 0
        f_statistic = ms_regression / ms_residual if ms_residual > 0 else 0
        
        return {
            "regression_type": "simple_linear",
            "dependent_variable": dependent_var,
            "independent_variable": independent_var,
            "sample_size": n,
            "coefficient": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "adjusted_r_squared": adjusted_r_squared,
            "standard_error": se_estimate,
            "f_statistic": f_statistic,
            "equation": equation,
            "predictions": predictions[:10] if len(predictions) > 10 else predictions,  # Limit output size
            "residuals": residuals[:10] if len(residuals) > 10 else residuals  # Limit output size
        }
    
    def _perform_multiple_linear_regression(
        self, 
        dataset: List[Dict[str, Any]], 
        dependent_var: str, 
        independent_vars: List[str]
    ) -> Dict[str, Any]:
        """Perform multiple linear regression with multiple independent variables."""
        # Extract data points with all variables
        valid_rows = []
        for row in dataset:
            if (dependent_var in row and row[dependent_var] is not None and 
                isinstance(row[dependent_var], (int, float)) and
                all(var in row and row[var] is not None and isinstance(row[var], (int, float)) 
                    for var in independent_vars)):
                valid_rows.append(row)
        
        if len(valid_rows) < len(independent_vars) + 1:
            return {"error": f"Insufficient data points for regression (need at least {len(independent_vars) + 1})"}
        
        # Extract X and y values
        X = [[float(row[var]) for var in independent_vars] for row in valid_rows]
        y = [float(row[dependent_var]) for row in valid_rows]
        n = len(valid_rows)
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
            return {"error": "Could not solve regression equation. Matrix may be singular."}
        
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
        
        # Calculate standard error of estimate
        se_estimate = math.sqrt(ss_residual / (n - p - 1)) if n > p + 1 else 0
        
        # Calculate F-statistic
        ms_regression = (ss_total - ss_residual) / p
        ms_residual = ss_residual / (n - p - 1) if n > p + 1 else 0
        f_statistic = ms_regression / ms_residual if ms_residual > 0 else 0
        
        # Create equation string
        equation_terms = [f"{intercept:.4f}"]
        for i, var in enumerate(independent_vars):
            coef = beta_coefficients[i]
            sign = "+" if coef >= 0 else ""
            equation_terms.append(f"{sign} {coef:.4f} × {var}")
        
        equation = f"{dependent_var} = {' '.join(equation_terms)}"
        
        return {
            "regression_type": "multiple_linear",
            "dependent_variable": dependent_var,
            "independent_variables": independent_vars,
            "sample_size": n,
            "intercept": intercept,
            "coefficients": dict(zip(independent_vars, beta_coefficients)),
            "r_squared": r_squared,
            "adjusted_r_squared": adjusted_r_squared,
            "standard_error": se_estimate,
            "f_statistic": f_statistic,
            "equation": equation,
            "predictions": predictions[:10] if len(predictions) > 10 else predictions,  # Limit output size
            "residuals": residuals[:10] if len(residuals) > 10 else residuals  # Limit output size
        }
    
    def _perform_logistic_regression(
        self, 
        dataset: List[Dict[str, Any]], 
        dependent_var: str, 
        independent_vars: List[str]
    ) -> Dict[str, Any]:
        """Perform logistic regression for binary classification."""
        # Note: This is a simplified implementation of logistic regression
        # A full implementation would use techniques like gradient descent
        
        # Extract data points with all variables
        valid_rows = []
        for row in dataset:
            if (dependent_var in row and row[dependent_var] is not None and
                all(var in row and row[var] is not None and isinstance(row[var], (int, float)) 
                    for var in independent_vars)):
                valid_rows.append(row)
        
        if len(valid_rows) < len(independent_vars) + 1:
            return {"error": f"Insufficient data points for regression (need at least {len(independent_vars) + 1})"}
        
        # Extract X values
        X = [[float(row[var]) for var in independent_vars] for row in valid_rows]
        
        # Extract y values and convert to binary (0 or 1)
        y_raw = [row[dependent_var] for row in valid_rows]
        
        # Try to convert to numeric if string
        y_values = []
        for val in y_raw:
            if isinstance(val, (int, float)):
                y_values.append(1 if val > 0 else 0)
            elif isinstance(val, str):
                # Try common binary encodings
                if val.lower() in ["1", "true", "yes", "positive", "t", "y"]:
                    y_values.append(1)
                else:
                    y_values.append(0)
            else:
                y_values.append(0)  # Default for unknown types
        
        n = len(valid_rows)
        p = len(independent_vars)
        
        # Simple implementation of logistic regression
        # In a real implementation, this would use iterative methods like gradient descent
        # Here we'll use a very basic approximation
        
        # First perform linear regression
        linear_result = self._perform_multiple_linear_regression(valid_rows, dependent_var, independent_vars)
        
        if "error" in linear_result:
            return linear_result
        
        # Use linear coefficients as initial estimates
        intercept = linear_result["intercept"]
        coefficients = [linear_result["coefficients"][var] for var in independent_vars]
        
        # Calculate predictions (probabilities using logistic function)
        probabilities = []
        for x in X:
            logit = intercept + sum(beta * x[i] for i, beta in enumerate(coefficients))
            probability = 1 / (1 + math.exp(-logit)) if logit > -100 else 0
            probabilities.append(probability)
        
        # Convert probabilities to binary predictions
        predictions = [1 if p >= 0.5 else 0 for p in probabilities]
        
        # Calculate accuracy, precision, recall
        true_positives = sum(1 for i in range(n) if predictions[i] == 1 and y_values[i] == 1)
        false_positives = sum(1 for i in range(n) if predictions[i] == 1 and y_values[i] == 0)
        true_negatives = sum(1 for i in range(n) if predictions[i] == 0 and y_values[i] == 0)
        false_negatives = sum(1 for i in range(n) if predictions[i] == 0 and y_values[i] == 1)
        
        accuracy = (true_positives + true_negatives) / n if n > 0 else 0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Create equation string
        equation_terms = [f"{intercept:.4f}"]
        for i, var in enumerate(independent_vars):
            coef = coefficients[i]
            sign = "+" if coef >= 0 else ""
            equation_terms.append(f"{sign} {coef:.4f} × {var}")
        
        logit_equation = f"logit(P) = {' '.join(equation_terms)}"
        probability_equation = f"P({dependent_var}=1) = 1 / (1 + e^-logit(P))"
        
        return {
            "regression_type": "logistic",
            "dependent_variable": dependent_var,
            "independent_variables": independent_vars,
            "sample_size": n,
            "intercept": intercept,
            "coefficients": dict(zip(independent_vars, coefficients)),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "confusion_matrix": {
                "true_positives": true_positives,
                "false_positives": false_positives,
                "true_negatives": true_negatives,
                "false_negatives": false_negatives
            },
            "logit_equation": logit_equation,
            "probability_equation": probability_equation,
            "probabilities": probabilities[:10] if len(probabilities) > 10 else probabilities,  # Limit output size
            "note": "This is a simplified implementation of logistic regression and may not be optimal for all datasets."
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
    
    def _calculate_regression_diagnostics(
        self,
        dataset: List[Dict[str, Any]],
        dependent_var: str,
        independent_vars: List[str],
        regression_results: Dict[str, Any],
        regression_type: str
    ) -> Dict[str, Any]:
        """Calculate diagnostic measures for regression analysis."""
        # Extract data points with all variables
        valid_rows = []
        for row in dataset:
            if (dependent_var in row and row[dependent_var] is not None and 
                isinstance(row[dependent_var], (int, float)) and
                all(var in row and row[var] is not None and isinstance(row[var], (int, float)) 
                    for var in independent_vars)):
                valid_rows.append(row)
        
        n = len(valid_rows)
        
        # Extract actual values
        y_actual = [float(row[dependent_var]) for row in valid_rows]
        
        # Get predictions
        predictions = regression_results.get("predictions", [])
        
        # Limit to same length if needed
        min_len = min(len(y_actual), len(predictions))
        y_actual = y_actual[:min_len]
        predictions = predictions[:min_len]
        
        # Calculate residuals
        residuals = [y_actual[i] - predictions[i] for i in range(min_len)]
        
        # Calculate mean squared error
        mse = sum(res ** 2 for res in residuals) / len(residuals) if residuals else 0
        
        # Calculate root mean squared error
        rmse = math.sqrt(mse)
        
        # Calculate mean absolute error
        mae = sum(abs(res) for res in residuals) / len(residuals) if residuals else 0
        
        # Calculate mean absolute percentage error
        mape = sum(abs(res / actual) * 100 for res, actual in zip(residuals, y_actual) if actual != 0) / sum(1 for y in y_actual if y != 0) if y_actual else 0
        
        # Check for heteroscedasticity (using a simple approach)
        hetero_corr = self._calculate_pearson_correlation([abs(res) for res in residuals], predictions) if len(residuals) >= 2 else 0
        heteroscedasticity = abs(hetero_corr) > 0.3
        
        # Check for autocorrelation (using a simple Durbin-Watson test)
        dw_stat = sum((residuals[i] - residuals[i-1]) ** 2 for i in range(1, len(residuals))) / sum(res ** 2 for res in residuals) if len(residuals) > 1 and sum(res ** 2 for res in residuals) > 0 else 2.0
        autocorrelation = dw_stat < 1.0 or dw_stat > 3.0
        
        # For multicollinearity, check correlations between independent variables
        multicollinearity = False
        var_correlations = []
        
        if len(independent_vars) > 1:
            # Calculate correlation matrix for independent variables
            ind_var_correlation = self._calculate_correlation_matrix(valid_rows, independent_vars)
            
            # Check for high correlations
            for i, var1 in enumerate(independent_vars):
                for var2 in independent_vars[i+1:]:
                    corr = ind_var_correlation[var1][var2]
                    if corr is not None and abs(corr) > 0.7:
                        multicollinearity = True
                        var_correlations.append({
                            "variables": [var1, var2],
                            "correlation": corr
                        })
        
        # Create diagnostics dictionary
        diagnostics = {
            "error_metrics": {
                "mean_squared_error": mse,
                "root_mean_squared_error": rmse,
                "mean_absolute_error": mae,
                "mean_absolute_percentage_error": mape
            },
            "residuals_analysis": {
                "residuals_mean": sum(residuals) / len(residuals) if residuals else 0,
                "residuals_std": math.sqrt(sum(res ** 2 for res in residuals) / len(residuals) - (sum(residuals) / len(residuals)) ** 2) if len(residuals) > 1 else 0,
                "heteroscedasticity_detected": heteroscedasticity,
                "autocorrelation_detected": autocorrelation,
                "durbin_watson_statistic": dw_stat
            }
        }
        
        # Add multicollinearity information if applicable
        if len(independent_vars) > 1:
            diagnostics["multicollinearity"] = {
                "detected": multicollinearity,
                "high_correlations": var_correlations
            }
        
        return diagnostics
    
    def _generate_regression_insights(self, regression_results: Dict[str, Any], regression_type: str) -> Dict[str, List[str]]:
        """Generate insights and recommendations based on regression results."""
        insights = []
        recommendations = []
        
        if regression_type in ["linear", "multiple"]:
            # Check model fit
            r_squared = regression_results.get("r_squared", 0)
            adjusted_r_squared = regression_results.get("adjusted_r_squared", 0)
            
            if r_squared < 0.3:
                insights.append(f"The model explains only {r_squared:.1%} of the variance in {regression_results.get('dependent_variable')}, suggesting a weak relationship.")
                recommendations.append("Consider exploring additional variables or different model specifications.")
            elif r_squared < 0.7:
                insights.append(f"The model explains {r_squared:.1%} of the variance in {regression_results.get('dependent_variable')}, indicating a moderate fit.")
            else:
                insights.append(f"The model explains {r_squared:.1%} of the variance in {regression_results.get('dependent_variable')}, indicating a strong fit.")
            
            # Check coefficients
            if regression_type == "linear":
                coefficient = regression_results.get("coefficient")
                if coefficient is not None:
                    if coefficient > 0:
                        insights.append(f"A one-unit increase in {regression_results.get('independent_variable')} is associated with a {coefficient:.4f} unit increase in {regression_results.get('dependent_variable')}.")
                    else:
                        insights.append(f"A one-unit increase in {regression_results.get('independent_variable')} is associated with a {-coefficient:.4f} unit decrease in {regression_results.get('dependent_variable')}.")
            else:  # multiple
                coefficients = regression_results.get("coefficients", {})
                if coefficients:
                    # Identify variables with largest absolute coefficients
                    sorted_vars = sorted(coefficients.items(), key=lambda x: abs(x[1]), reverse=True)
                    top_var, top_coef = sorted_vars[0]
                    
                    if len(sorted_vars) > 1:
                        insights.append(f"The variables are ranked by importance as follows: {', '.join(var for var, _ in sorted_vars)}.")
            
            # Check diagnostics if available
            diagnostics = regression_results.get("diagnostics", {})
            
            if diagnostics:
                # Check for heteroscedasticity
                if diagnostics.get("residuals_analysis", {}).get("heteroscedasticity_detected", False):
                    insights.append("Heteroscedasticity detected: The model's prediction errors vary across different levels of the predictors.")
                    recommendations.append("Consider transformations (e.g., log) of the dependent or independent variables.")
                
                # Check for autocorrelation
                if diagnostics.get("residuals_analysis", {}).get("autocorrelation_detected", False):
                    insights.append("Autocorrelation detected: Residuals show a pattern over the sequence of observations.")
                    recommendations.append("If using time series data, consider time series-specific modeling approaches.")
                
                # Check for multicollinearity
                if diagnostics.get("multicollinearity", {}).get("detected", False):
                    corrs = diagnostics.get("multicollinearity", {}).get("high_correlations", [])
                    var_pairs = [f"{pair['variables'][0]} and {pair['variables'][1]}" for pair in corrs[:2]]
                    insights.append(f"Multicollinearity detected between variables: {', '.join(var_pairs)}.")
                    recommendations.append("Consider removing one of the correlated variables or using dimensionality reduction techniques.")
        
        elif regression_type == "logistic":
            # Check model performance
            accuracy = regression_results.get("accuracy", 0)
            precision = regression_results.get("precision", 0)
            recall = regression_results.get("recall", 0)
            f1_score = regression_results.get("f1_score", 0)
            
            insights.append(f"The model achieves {accuracy:.1%} accuracy, with precision {precision:.1%} and recall {recall:.1%}.")
            
            if f1_score < 0.5:
                insights.append("The model's F1 score is low, indicating challenges in balancing precision and recall.")
                recommendations.append("Consider collecting more data or exploring different predictor variables.")
            elif f1_score < 0.8:
                insights.append("The model's F1 score indicates moderate performance.")
            else:
                insights.append("The model's F1 score indicates strong performance.")
            
            # Confusion matrix insights
            confusion = regression_results.get("confusion_matrix", {})
            if confusion:
                false_positives = confusion.get("false_positives", 0)
                false_negatives = confusion.get("false_negatives", 0)
                
                if false_positives > false_negatives * 2:
                    insights.append("The model shows a tendency toward false positives.")
                    recommendations.append("Consider adjusting the classification threshold if precision is more important than recall.")
                elif false_negatives > false_positives * 2:
                    insights.append("The model shows a tendency toward false negatives.")
                    recommendations.append("Consider adjusting the classification threshold if recall is more important than precision.")
            
            # Check coefficients
            coefficients = regression_results.get("coefficients", {})
            if coefficients:
                # Identify variables with largest absolute coefficients
                sorted_vars = sorted(coefficients.items(), key=lambda x: abs(x[1]), reverse=True)
                top_var, top_coef = sorted_vars[0]
                
                effect = "positive" if top_coef > 0 else "negative"
                insights.append(f"{top_var} has the strongest {effect} effect on the probability of {regression_results.get('dependent_variable')}.")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("Validate the model with new data to ensure it generalizes well beyond the training dataset.")
            recommendations.append("Consider the practical significance of the findings alongside statistical significance.")
        
        return {
            "insights": insights,
            "recommendations": recommendations
        }
    
    # Helper methods for analyze_time_series
    
    def _analyze_time_series_trend(self, time_series: List[float]) -> Dict[str, Any]:
        """Analyze the trend component of a time series."""
        if len(time_series) < 3:
            return {"error": "Insufficient data points for trend analysis"}
        
        n = len(time_series)
        
        # Calculate simple moving average for smoothing (window size of 3 or 5)
        window_size = min(5, max(3, n // 10))
        
        smoothed_series = []
        half_window = window_size // 2
        
        for i in range(n):
            # Determine window bounds
            start = max(0, i - half_window)
            end = min(n, i + half_window + 1)
            
            # Calculate average for this window
            window_values = time_series[start:end]
            smoothed_series.append(sum(window_values) / len(window_values))
        
        # Calculate linear trend using least squares regression
        x_values = list(range(n))
        mean_x = sum(x_values) / n
        mean_y = sum(time_series) / n
        
        # Calculate trend line coefficients
        numerator = sum((x_values[i] - mean_x) * (time_series[i] - mean_y) for i in range(n))
        denominator = sum((x - mean_x) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = mean_y - slope * mean_x
        
        # Generate trend line values
        trend_line = [intercept + slope * x for x in x_values]
        
        # Calculate overall change and percentage change
        if time_series[0] != 0:
            percentage_change = ((time_series[-1] - time_series[0]) / abs(time_series[0])) * 100
        else:
            percentage_change = float('inf') if time_series[-1] > 0 else float('-inf') if time_series[-1] < 0 else 0
        
        # Determine trend direction
        if slope > 0.001:
            trend_direction = "increasing"
        elif slope < -0.001:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        # Calculate trend strength using R-squared
        ss_total = sum((y - mean_y) ** 2 for y in time_series)
        ss_residual = sum((time_series[i] - trend_line[i]) ** 2 for i in range(n))
        
        if ss_total == 0:
            r_squared = 1
        else:
            r_squared = 1 - (ss_residual / ss_total)
        
        return {
            "trend_direction": trend_direction,
            "slope": slope,
            "intercept": intercept,
            "overall_change": time_series[-1] - time_series[0],
            "percentage_change": percentage_change,
            "trend_line": trend_line,
            "smoothed_series": smoothed_series,
            "trend_strength": r_squared,
            "trend_equation": f"y = {intercept:.4f} + {slope:.4f}t"
        }
    
    def _analyze_seasonality(self, time_series: List[float]) -> Dict[str, Any]:
        """Analyze the seasonality component of a time series."""
        n = len(time_series)
        
        # Need enough data points to detect seasonality
        if n < 8:
            return {"error": "Insufficient data points for seasonality analysis"}
        
        # Try different seasonal periods (2, 3, 4, 6, 12) 
        # and pick the one with the strongest autocorrelation
        candidate_periods = [p for p in [2, 3, 4, 6, 12] if n >= 2 * p]
        
        if not candidate_periods:
            return {"error": "Insufficient data points for the candidate seasonal periods"}
        
        best_period = 0
        best_acf = 0
        period_scores = {}
        
        for period in candidate_periods:
            # Calculate autocorrelation at this lag
            # This is a simple estimation of seasonality strength
            acf = self._calculate_autocorrelation(time_series, period)
            period_scores[period] = acf
            
            if abs(acf) > abs(best_acf):
                best_acf = acf
                best_period = period
        
        # If no strong seasonality found
        if abs(best_acf) < 0.3:
            seasonality_detected = False
            best_period = 0
        else:
            seasonality_detected = True
        
        # If seasonality detected, calculate seasonal component
        seasonal_component = []
        if seasonality_detected and best_period > 0:
            # Calculate average value for each position in the season
            seasonal_means = [0] * best_period
            seasonal_counts = [0] * best_period
            
            for i, value in enumerate(time_series):
                pos = i % best_period
                seasonal_means[pos] += value
                seasonal_counts[pos] += 1
            
            # Calculate average for each position
            for i in range(best_period):
                if seasonal_counts[i] > 0:
                    seasonal_means[i] /= seasonal_counts[i]
            
            # Generate seasonal component by repeating the pattern
            for i in range(n):
                pos = i % best_period
                seasonal_component.append(seasonal_means[pos])
            
            # Normalize seasonal component to sum to zero
            mean_component = sum(seasonal_component) / len(seasonal_component)
            seasonal_component = [s - mean_component for s in seasonal_component]
        
        return {
            "seasonality_detected": seasonality_detected,
            "best_period": best_period,
            "autocorrelation": best_acf if seasonality_detected else None,
            "period_scores": period_scores,
            "seasonal_component": seasonal_component if seasonality_detected else [],
            "seasonal_pattern": [seasonal_component[i] for i in range(best_period)] if seasonality_detected and best_period > 0 else []
        }
    
    def _calculate_autocorrelation(self, time_series: List[float], lag: int) -> float:
        """Calculate autocorrelation at specified lag."""
        n = len(time_series)
        if lag >= n:
            return 0
        
        # Calculate mean
        mean = sum(time_series) / n
        
        # Calculate variance
        variance = sum((x - mean) ** 2 for x in time_series) / n
        if variance == 0:
            return 0
        
        # Calculate autocorrelation
        acf = sum((time_series[i] - mean) * (time_series[i - lag] - mean) for i in range(lag, n)) / ((n - lag) * variance)
        
        return acf
    
    def _detect_time_series_outliers(self, time_series: List[float]) -> List[Dict[str, Any]]:
        """Detect outliers in time series data."""
        n = len(time_series)
        if n < 4:
            return []
        
        outliers = []
        
        # Calculate moving average and standard deviation
        window_size = min(5, max(3, n // 10))
        half_window = window_size // 2
        
        for i in range(n):
            # Determine window bounds (exclude the current point)
            window_indices = list(range(max(0, i - half_window), i)) + list(range(i + 1, min(n, i + half_window + 1)))
            
            if not window_indices:
                continue
            
            window_values = [time_series[j] for j in window_indices]
            window_mean = sum(window_values) / len(window_values)
            
            # Calculate window standard deviation
            window_var = sum((x - window_mean) ** 2 for x in window_values) / len(window_values)
            window_std = math.sqrt(window_var)
            
            # Detect outlier using z-score
            if window_std > 0:
                z_score = (time_series[i] - window_mean) / window_std
                
                if abs(z_score) > 3:  # Common threshold for outliers
                    outliers.append({
                        "index": i,
                        "value": time_series[i],
                        "z_score": z_score,
                        "window_mean": window_mean,
                        "window_std": window_std
                    })
        
        return outliers
    
    def _generate_simple_forecast(self, time_series: List[float], periods: int) -> List[float]:
        """Generate a simple forecast using trend extrapolation."""
        n = len(time_series)
        if n < 2:
            return [time_series[0]] * periods if time_series else [0] * periods
        
        # Calculate trend with simple linear regression
        x_values = list(range(n))
        mean_x = sum(x_values) / n
        mean_y = sum(time_series) / n
        
        numerator = sum((x_values[i] - mean_x) * (time_series[i] - mean_y) for i in range(n))
        denominator = sum((x - mean_x) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = mean_y - slope * mean_x
        
        # Generate forecast values
        forecast = [intercept + slope * (n + i) for i in range(periods)]
        
        return forecast
    
    def _generate_time_series_insights(
        self, 
        time_series_results: Dict[str, Dict[str, Any]],
        analysis_components: List[str]
    ) -> Dict[str, List[str]]:
        """Generate insights from time series analysis results."""
        insights = []
        recommendations = []
        
        # Check if we have results for any variables
        if not time_series_results:
            return {
                "insights": ["No valid time series data was found for analysis."],
                "recommendations": ["Ensure the time variable is correctly formatted and numeric variables are available for analysis."]
            }
        
        # Process each variable's results
        trend_directions = {}
        seasonality_detected = False
        outliers_detected = False
        
        for var, results in time_series_results.items():
            # Check for trend analysis
            if "trend_analysis" in results and "trend_direction" in results["trend_analysis"]:
                trend_data = results["trend_analysis"]
                direction = trend_data["trend_direction"]
                trend_directions[var] = direction
                
                # Generate trend insight
                if direction == "increasing":
                    insights.append(f"{var} shows an increasing trend with an overall change of {trend_data['overall_change']:.2f} ({trend_data['percentage_change']:.1f}%).")
                elif direction == "decreasing":
                    insights.append(f"{var} shows a decreasing trend with an overall change of {trend_data['overall_change']:.2f} ({abs(trend_data['percentage_change']):.1f}%).")
                else:
                    insights.append(f"{var} remains relatively stable over time with minimal overall change.")
                
                # Add insight about trend strength if available
                if "trend_strength" in trend_data:
                    strength = trend_data["trend_strength"]
                    if strength > 0.7:
                        insights.append(f"The trend for {var} is strong (R² = {strength:.2f}), suggesting a consistent pattern over time.")
                    elif strength > 0.3:
                        insights.append(f"The trend for {var} is moderate (R² = {strength:.2f}), with some variability around the trend line.")
                    else:
                        insights.append(f"The trend for {var} is weak (R² = {strength:.2f}), indicating high variability or potential non-linear patterns.")
            
            # Check for seasonality analysis
            if "seasonality_analysis" in results:
                seasonality_data = results["seasonality_analysis"]
                if seasonality_data.get("seasonality_detected", False):
                    seasonality_detected = True
                    period = seasonality_data.get("best_period", 0)
                    
                    if period > 0:
                        pattern_type = f"{period}-period"
                        if period == 4:
                            pattern_type = "quarterly"
                        elif period == 12:
                            pattern_type = "monthly"
                        elif period == 7:
                            pattern_type = "weekly"
                        
                        insights.append(f"{var} exhibits a {pattern_type} seasonal pattern with an autocorrelation of {seasonality_data.get('autocorrelation', 0):.2f}.")
                else:
                    insights.append(f"No significant seasonality was detected for {var}.")
            
            # Check for outliers
            if "outliers" in results:
                outliers = results["outliers"]
                if outliers:
                    outliers_detected = True
                    insights.append(f"{len(outliers)} outliers detected in {var}, which may indicate unusual events or data issues.")
            
            # Check for forecast
            if "forecast" in results:
                forecast = results["forecast"]
                if forecast:
                    last_value = results.get("trend_analysis", {}).get("trend_line", [])[-1] if "trend_analysis" in results else None
                    if last_value is not None:
                        forecast_change = ((forecast[-1] - last_value) / abs(last_value)) * 100 if last_value != 0 else float('inf')
                        insights.append(f"The forecast for {var} suggests a {'increase' if forecast[-1] > last_value else 'decrease'} of approximately {abs(forecast_change):.1f}% over the forecast period.")
        
        # Generate overall insights based on patterns across variables
        if len(trend_directions) > 1:
            increasing_vars = [var for var, direction in trend_directions.items() if direction == "increasing"]
            decreasing_vars = [var for var, direction in trend_directions.items() if direction == "decreasing"]
            
            if increasing_vars and decreasing_vars:
                insights.append(f"Variables show mixed trends: {', '.join(increasing_vars)} increasing while {', '.join(decreasing_vars)} decreasing.")
            elif increasing_vars and len(increasing_vars) == len(trend_directions):
                insights.append(f"All analyzed variables show increasing trends, suggesting overall growth in the system.")
            elif decreasing_vars and len(decreasing_vars) == len(trend_directions):
                insights.append(f"All analyzed variables show decreasing trends, suggesting overall contraction in the system.")
        
        # Generate recommendations
        if "trend" in analysis_components:
            recommendations.append("Consider forecasting future values using more advanced time series methods such as ARIMA or exponential smoothing.")
            
            if any(direction == "increasing" for direction in trend_directions.values()):
                recommendations.append("For variables with increasing trends, monitor growth rates and consider capacity planning.")
            
            if any(direction == "decreasing" for direction in trend_directions.values()):
                recommendations.append("For variables with decreasing trends, investigate potential causes and develop mitigation strategies if needed.")
        
        if seasonality_detected:
            recommendations.append("Account for seasonal patterns in planning and forecasting to anticipate regular fluctuations.")
        
        if outliers_detected:
            recommendations.append("Investigate detected outliers to determine if they represent data issues or important events that warrant attention.")
        
        if "forecast" in analysis_components:
            recommendations.append("Validate forecast accuracy by comparing predictions against new data as it becomes available.")
            recommendations.append("For improved forecast accuracy, consider using more sophisticated methods that account for both trend and seasonality components.")
        
        return {
            "insights": insights,
            "recommendations": recommendations
        }
    
    # Helper methods for identify_outliers
    
    def _detect_outliers_zscore(self, values: List[float], threshold: float) -> List[int]:
        """Detect outliers using Z-score method."""
        n = len(values)
        if n < 2:
            return []
        
        # Calculate mean and standard deviation
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)
        
        # If standard deviation is zero or very small, no outliers
        if std_dev < 1e-10:
            return []
        
        # Identify outliers
        outlier_indices = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev)
            if z_score > threshold:
                outlier_indices.append(i)
        
        return outlier_indices
    
    def _detect_outliers_iqr(self, values: List[float], threshold: float) -> List[int]:
        """Detect outliers using Interquartile Range (IQR) method."""
        n = len(values)
        if n < 4:  # Need at least 4 points for meaningful quartiles
            return []
        
        # Sort values
        sorted_values = sorted(values)
        
        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        iqr = q3 - q1
        
        # If IQR is zero or very small, no outliers
        if iqr < 1e-10:
            return []
        
        # Calculate bounds
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        # Identify outliers
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        return outlier_indices
    
    def _detect_outliers_percentile(self, values: List[float], threshold: float) -> List[int]:
        """Detect outliers using percentile method."""
        n = len(values)
        if n < 2:
            return []
        
        # Sort values
        sorted_values = sorted(values)
        
        # Calculate percentile indices
        lower_idx = max(0, int(n * threshold / 100) - 1)
        upper_idx = min(n - 1, int(n * (1 - threshold / 100)))
        
        # Get percentile values
        lower_bound = sorted_values[lower_idx]
        upper_bound = sorted_values[upper_idx]
        
        # Identify outliers
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        return outlier_indices
    
    def _generate_outlier_insights(self, outliers_detected: Dict[str, Dict[str, Any]], method: str) -> Dict[str, List[str]]:
        """Generate insights and recommendations based on outlier detection results."""
        insights = []
        recommendations = []
        
        # Check if any outliers were detected
        if not outliers_detected:
            insights.append("No significant outliers were detected in the analyzed variables.")
            recommendations.append("The data appears to be relatively clean from an outlier perspective.")
            return {"insights": insights, "recommendations": recommendations}
        
        # Count total outliers and affected variables
        total_outliers = sum(info.get("count", 0) for info in outliers_detected.values())
        variables_with_outliers = len(outliers_detected)
        
        insights.append(f"Detected {total_outliers} outliers across {variables_with_outliers} variables using the {method} method.")
        
        # Analyze variables with high outlier percentages
        high_outlier_vars = [
            var for var, info in outliers_detected.items()
            if info.get("percentage", 0) > 5  # More than 5% outliers
        ]
        
        if high_outlier_vars:
            if len(high_outlier_vars) > 3:
                insights.append(f"{len(high_outlier_vars)} variables have more than 5% outliers, which may indicate data quality issues or highly skewed distributions.")
            else:
                insights.append(f"Variables {', '.join(high_outlier_vars)} have more than 5% outliers, which may indicate data quality issues or highly skewed distributions.")
        
        # Generate variable-specific insights for up to 3 variables
        for i, (var, info) in enumerate(outliers_detected.items()):
            if i > 2:  # Limit to 3 variables to avoid overwhelming
                break
                
            count = info.get("count", 0)
            percentage = info.get("percentage", 0)
            summary = info.get("summary", {})
            
            if count > 0:
                if summary.get("min") is not None and summary.get("max") is not None:
                    insights.append(f"{var} contains {count} outliers ({percentage:.1f}%) ranging from {summary['min']} to {summary['max']}.")
                else:
                    insights.append(f"{var} contains {count} outliers ({percentage:.1f}%).")
        
        # Generate recommendations based on outlier detection results
        if total_outliers > 0:
            recommendations.append("Investigate the source of outliers to determine if they represent data errors or meaningful extreme values.")
            
            if any(info.get("percentage", 0) > 10 for info in outliers_detected.values()):
                recommendations.append("For variables with a high percentage of outliers, consider data transformation (e.g., log transform) or use robust statistical methods.")
            
            if method == "zscore":
                recommendations.append("The Z-Score method assumes normally distributed data. If your data is skewed, consider using the IQR method instead.")
            
            recommendations.append("When analyzing data with outliers, consider their impact on summary statistics and model performance.")
        
        return {
            "insights": insights,
            "recommendations": recommendations
        }
    
    # Helper methods for generate_visualizations
    
    def _generate_visualization_spec(
        self,
        visualization_type: str,
        variables: List[str],
        title: str,
        additional_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a specification for the requested visualization type."""
        # Base specification
        spec = {
            "title": title,
            "variables": variables,
            "type": visualization_type
        }
        
        # Add type-specific configuration
        if visualization_type == "scatter":
            if len(variables) < 2:
                return {"error": "Scatter plot requires at least two variables"}
                
            spec.update({
                "x_axis": variables[0],
                "y_axis": variables[1],
                "color_by": variables[2] if len(variables) > 2 else None,
                "size_by": variables[3] if len(variables) > 3 else None
            })
            
        elif visualization_type == "bar":
            if len(variables) < 2:
                return {"error": "Bar chart requires at least two variables"}
                
            spec.update({
                "x_axis": variables[0],
                "y_axis": variables[1],
                "group_by": variables[2] if len(variables) > 2 else None,
                "orientation": additional_options.get("orientation", "vertical")
            })
            
        elif visualization_type == "line":
            if len(variables) < 2:
                return {"error": "Line chart requires at least two variables"}
                
            spec.update({
                "x_axis": variables[0],
                "y_axis": variables[1:],
                "include_markers": additional_options.get("include_markers", True)
            })
            
        elif visualization_type == "histogram":
            if len(variables) < 1:
                return {"error": "Histogram requires at least one variable"}
                
            spec.update({
                "variables": variables,
                "bins": additional_options.get("bins", 10),
                "density": additional_options.get("density", False)
            })
            
        elif visualization_type == "boxplot":
            if len(variables) < 1:
                return {"error": "Box plot requires at least one variable"}
                
            spec.update({
                "variables": variables,
                "group_by": additional_options.get("group_by"),
                "orientation": additional_options.get("orientation", "vertical")
            })
            
        elif visualization_type == "heatmap":
            if len(variables) < 3:
                return {"error": "Heatmap requires at least three variables (x, y, and value)"}
                
            spec.update({
                "x_axis": variables[0],
                "y_axis": variables[1],
                "value": variables[2],
                "color_scheme": additional_options.get("color_scheme", "viridis")
            })
            
        elif visualization_type == "pie":
            if len(variables) < 2:
                return {"error": "Pie chart requires at least two variables (category and value)"}
                
            spec.update({
                "category": variables[0],
                "value": variables[1],
                "donut": additional_options.get("donut", False)
            })
        
        # Add any additional options
        for key, value in additional_options.items():
            if key not in spec:
                spec[key] = value
        
        return spec
    
    def _analyze_data_for_visualization(self, dataset: List[Dict[str, Any]], variables: List[str]) -> Dict[str, Any]:
        """Analyze data characteristics relevant for visualization choices."""
        characteristics = {}
        
        for variable in variables:
            # Extract values
            values = [row.get(variable) for row in dataset if variable in row and row[variable] is not None]
            
            if not values:
                characteristics[variable] = {"error": "No valid values found"}
                continue
            
            # Check data type
            is_numeric = all(isinstance(v, (int, float)) for v in values)
            is_categorical = all(isinstance(v, str) for v in values)
            
            if is_numeric:
                # Calculate numeric characteristics
                min_val = min(values)
                max_val = max(values)
                range_val = max_val - min_val
                unique_count = len(set(values))
                
                # Check if appears to be continuous or discrete
                is_continuous = unique_count > min(10, len(values) / 2) and not all(isinstance(v, int) for v in values)
                
                characteristics[variable] = {
                    "data_type": "numeric",
                    "subtype": "continuous" if is_continuous else "discrete",
                    "range": [min_val, max_val],
               "range": [min_val, max_val],
                    "unique_values": unique_count,
                    "zero_contains": min_val <= 0 <= max_val
                }
            elif is_categorical:
                # Calculate categorical characteristics
                value_counts = {}
                for value in values:
                    if value in value_counts:
                        value_counts[value] += 1
                    else:
                        value_counts[value] = 1
                
                unique_count = len(value_counts)
                
                characteristics[variable] = {
                    "data_type": "categorical",
                    "unique_values": unique_count,
                    "most_common": max(value_counts.items(), key=lambda x: x[1])[0] if value_counts else None,
                    "is_high_cardinality": unique_count > 10
                }
            else:
                characteristics[variable] = {
                    "data_type": "mixed",
                    "unique_values": len(set(values))
                }
        
        return characteristics
    
    def _generate_visualization_recommendations(
        self,
        visualization_type: str,
        variables: List[str],
        data_characteristics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Generate recommendations for effective visualization based on data characteristics."""
        design_recommendations = []
        alternative_visualizations = []
        
        # Check if we have valid characteristics for all variables
        missing_chars = [var for var in variables if var not in data_characteristics or "error" in data_characteristics[var]]
        if missing_chars:
            design_recommendations.append(f"Ensure all variables have valid data: {', '.join(missing_chars)} lack complete information.")
            return {
                "design_recommendations": design_recommendations,
                "alternative_visualizations": ["Consider checking data quality before visualization"]
            }
        
        # Recommendations for scatter plots
        if visualization_type == "scatter":
            x_var, y_var = variables[0], variables[1]
            
            # Check if variables are numeric
            if data_characteristics[x_var].get("data_type") != "numeric" or data_characteristics[y_var].get("data_type") != "numeric":
                design_recommendations.append("Scatter plots work best with numeric variables. Consider transforming categorical variables or using alternative visualizations.")
                alternative_visualizations = ["bar", "heatmap"]
            else:
                # Recommend adding trend line if appropriate
                design_recommendations.append("Consider adding a trend line to highlight the relationship direction.")
                
                # Recommend color coding by a third variable if available
                if len(variables) > 2:
                    third_var = variables[2]
                    if data_characteristics[third_var].get("data_type") == "categorical":
                        if data_characteristics[third_var].get("is_high_cardinality", False):
                            design_recommendations.append(f"The third variable ({third_var}) has many unique values. Consider grouping categories for clearer visualization.")
                        else:
                            design_recommendations.append(f"Color points by {third_var} to reveal patterns across categories.")
                    else:
                        design_recommendations.append(f"Use a color gradient based on {third_var} to show how the relationship varies with this third dimension.")
                
                # Recommend size coding by a fourth variable if available
                if len(variables) > 3:
                    fourth_var = variables[3]
                    if data_characteristics[fourth_var].get("data_type") == "numeric":
                        design_recommendations.append(f"Vary point size based on {fourth_var} to add another dimension to the visualization.")
                
                # Suggest alternatives
                alternative_visualizations = ["bubble chart", "connected scatter plot", "3D scatter plot"]
        
        # Recommendations for bar charts
        elif visualization_type == "bar":
            x_var, y_var = variables[0], variables[1]
            
            # Check variable types
            x_is_categorical = data_characteristics[x_var].get("data_type") == "categorical"
            y_is_numeric = data_characteristics[y_var].get("data_type") == "numeric"
            
            if not x_is_categorical and not y_is_numeric:
                design_recommendations.append("Bar charts work best with a categorical variable on one axis and a numeric variable on the other.")
                alternative_visualizations = ["line", "scatter"]
            
            # Check cardinality
            if x_is_categorical and data_characteristics[x_var].get("is_high_cardinality", False):
                design_recommendations.append(f"The variable {x_var} has many unique values. Consider grouping categories or using a horizontal orientation.")
                alternative_visualizations.append("treemap")
            
            # Recommend grouping if a third variable is available
            if len(variables) > 2:
                third_var = variables[2]
                if data_characteristics[third_var].get("data_type") == "categorical":
                    if data_characteristics[third_var].get("is_high_cardinality", False):
                        design_recommendations.append(f"The third variable ({third_var}) has many unique values. Consider filtering to key categories for grouped bars.")
                    else:
                        design_recommendations.append(f"Group bars by {third_var} to show patterns across categories.")
                        alternative_visualizations.append("grouped bar chart")
            
            # Suggest alternatives
            if not alternative_visualizations:
                alternative_visualizations = ["grouped bar", "stacked bar", "lollipop chart"]
        
        # Recommendations for line charts
        elif visualization_type == "line":
            x_var = variables[0]
            y_vars = variables[1:]
            
            # Check if x variable is suitable for sequential data
            if data_characteristics[x_var].get("data_type") == "categorical" and data_characteristics[x_var].get("is_high_cardinality", False):
                design_recommendations.append(f"The variable {x_var} has many unique values. Consider using a time variable or a continuous numeric variable for the x-axis.")
            
            # Check number of y variables
            if len(y_vars) > 5:
                design_recommendations.append("Plotting too many lines can lead to cluttered visualizations. Consider focusing on key variables or using small multiples.")
            
            # Recommend dual axis if variables have very different scales
            if len(y_vars) == 2:
                y1_range = data_characteristics[y_vars[0]].get("range", [0, 1])
                y2_range = data_characteristics[y_vars[1]].get("range", [0, 1])
                
                y1_magnitude = max(abs(y1_range[0]), abs(y1_range[1]))
                y2_magnitude = max(abs(y2_range[0]), abs(y2_range[1]))
                
                if y1_magnitude > 10 * y2_magnitude or y2_magnitude > 10 * y1_magnitude:
                    design_recommendations.append("The y variables have very different scales. Consider using a dual-axis chart or normalizing the values.")
            
            # Suggest alternatives
            alternative_visualizations = ["area chart", "stacked area chart", "connected scatter plot"]
        
        # Recommendations for histograms
        elif visualization_type == "histogram":
            for var in variables:
                # Check if variable is numeric
                if data_characteristics[var].get("data_type") != "numeric":
                    design_recommendations.append(f"Histograms require numeric variables. {var} appears to be categorical.")
                    alternative_visualizations = ["bar chart", "count plot"]
                else:
                    # Recommend appropriate bin count
                    unique_count = data_characteristics[var].get("unique_values", 10)
                    if unique_count <= 5:
                        design_recommendations.append(f"{var} has few unique values. Consider using a bar chart instead of a histogram.")
                        alternative_visualizations = ["bar chart", "density plot"]
                    elif unique_count > 100:
                        design_recommendations.append(f"{var} has many unique values. Use an appropriate bin count (e.g., Sturges' rule or Square root rule) for optimal visualization.")
            
            # If multiple variables
            if len(variables) > 1:
                design_recommendations.append("For multiple variables, consider using overlaid histograms with transparency or small multiples for comparison.")
                alternative_visualizations = ["kernel density plot", "box plots", "violin plots"]
            else:
                alternative_visualizations = ["density plot", "rug plot", "cumulative histogram"]
        
        # Recommendations for box plots
        elif visualization_type == "boxplot":
            for var in variables:
                # Check if variable is numeric
                if data_characteristics[var].get("data_type") != "numeric":
                    design_recommendations.append(f"Box plots require numeric variables. {var} appears to be categorical and might be better used as a grouping variable.")
            
            # For single variable
            if len(variables) == 1 and data_characteristics[variables[0]].get("data_type") == "numeric":
                design_recommendations.append("Consider adding a grouping variable to compare distributions across categories.")
                alternative_visualizations = ["histogram", "violin plot", "strip plot"]
            
            # For multiple variables
            if len(variables) > 1:
                all_numeric = all(data_characteristics[var].get("data_type") == "numeric" for var in variables)
                if all_numeric:
                    design_recommendations.append("When comparing multiple numeric variables, ensure they are on similar scales or consider standardizing them.")
                
                alternative_visualizations = ["violin plots", "strip plots", "swarm plots"]
        
        # Recommendations for heatmaps
        elif visualization_type == "heatmap":
            if len(variables) < 3:
                design_recommendations.append("Heatmaps typically require three variables: two categorical or binned variables for axes and one numeric variable for color intensity.")
                alternative_visualizations = ["scatter plot", "contour plot"]
            else:
                x_var, y_var, value_var = variables[0], variables[1], variables[2]
                
                # Check axis variables
                for axis_var in [x_var, y_var]:
                    if data_characteristics[axis_var].get("data_type") == "numeric" and data_characteristics[axis_var].get("subtype") == "continuous":
                        design_recommendations.append(f"{axis_var} is continuous. Consider binning it for the heatmap or using a contour plot instead.")
                
                # Check value variable
                if data_characteristics[value_var].get("data_type") != "numeric":
                    design_recommendations.append(f"The value variable ({value_var}) should be numeric for a heatmap. Consider using a count of occurrences instead.")
                
                # Recommend color scheme
                if data_characteristics[value_var].get("zero_contains", False):
                    design_recommendations.append("The data includes both positive and negative values. Consider using a diverging color palette centered at zero.")
                
                alternative_visualizations = ["contour plot", "2D histogram", "tile plot"]
        
        # Recommendations for pie charts
        elif visualization_type == "pie":
            if len(variables) < 2:
                design_recommendations.append("Pie charts require at least two variables: a categorical variable for segments and a numeric variable for segment sizes.")
                alternative_visualizations = ["bar chart"]
            else:
                category_var, value_var = variables[0], variables[1]
                
                # Check category variable
                if data_characteristics[category_var].get("data_type") != "categorical":
                    design_recommendations.append(f"The category variable ({category_var}) should be categorical for a pie chart.")
                
                # Check value variable
                if data_characteristics[value_var].get("data_type") != "numeric":
                    design_recommendations.append(f"The value variable ({value_var}) should be numeric for a pie chart.")
                
                # Check category cardinality
                if data_characteristics[category_var].get("is_high_cardinality", False):
                    design_recommendations.append(f"The category variable ({category_var}) has many unique values. Consider grouping small categories or using a bar chart instead.")
                    alternative_visualizations = ["treemap", "bar chart"]
                
                # General pie chart advice
                design_recommendations.append("Pie charts work best with a small number of categories (ideally ≤ 7). Add percentage labels and consider using a donut chart for better readability.")
                
                if not alternative_visualizations:
                    alternative_visualizations = ["donut chart", "bar chart", "treemap"]
        
        # General recommendations for all visualization types
        design_recommendations.append("Use clear, descriptive titles and axis labels to provide context.")
        design_recommendations.append("Consider your audience when choosing color schemes and ensure accessibility for color-blind viewers.")
        
        return {
            "design_recommendations": design_recommendations,
            "alternative_visualizations": alternative_visualizations
        }
    
    # Helper methods for segment_data
    
    def _create_segments(self, dataset: List[Dict[str, Any]], segmentation_variables: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Create segments based on segmentation variables."""
        segments = {}
        
        # Create segment key for each row
        for row in dataset:
            # Skip rows that don't have all segmentation variables
            if not all(var in row for var in segmentation_variables):
                continue
            
            # Create segment key as concatenated values
            segment_values = []
            for var in segmentation_variables:
                value = row[var]
                if value is None:
                    value = "None"
                elif not isinstance(value, str):
                    value = str(value)
                segment_values.append(f"{var}={value}")
            
            segment_key = ", ".join(segment_values)
            
            # Add row to appropriate segment
            if segment_key not in segments:
                segments[segment_key] = []
            segments[segment_key].append(row)
        
        return segments
    
    def _compare_segments(
        self,
        segment_metrics: Dict[str, Dict[str, Any]],
        metrics: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Compare metrics across segments to identify significant differences."""
        # If only one segment, return empty comparison
        if len(segment_metrics) <= 1:
            return {}
        
        comparisons = {}
        
        # Calculate overall metrics across all segments (weighted by segment size)
        overall_metrics = {}
        total_size = sum(info["size"] for info in segment_metrics.values())
        
        for metric in metrics:
            weighted_sum = 0
            weighted_count = 0
            
            for segment, info in segment_metrics.items():
                if metric in info["metrics"]:
                    segment_mean = info["metrics"][metric].get("mean")
                    segment_size = info["size"]
                    
                    if segment_mean is not None:
                        weighted_sum += segment_mean * segment_size
                        weighted_count += segment_size
            
            overall_metrics[metric] = weighted_sum / weighted_count if weighted_count > 0 else None
        
        # Compare each segment to overall metrics
        for metric in metrics:
            metric_comparisons = []
            
            if overall_metrics[metric] is None:
                continue
            
            for segment, info in segment_metrics.items():
                if metric in info["metrics"]:
                    segment_mean = info["metrics"][metric].get("mean")
                    
                    if segment_mean is not None:
                        # Calculate percentage difference from overall
                        if overall_metrics[metric] != 0:
                            pct_diff = ((segment_mean - overall_metrics[metric]) / abs(overall_metrics[metric])) * 100
                        else:
                            pct_diff = float('inf') if segment_mean > 0 else float('-inf') if segment_mean < 0 else 0
                        
                        # Determine if difference is significant (using a simple threshold)
                        is_significant = abs(pct_diff) > 10  # More than 10% difference
                        
                        metric_comparisons.append({
                            "segment": segment,
                            "segment_mean": segment_mean,
                            "overall_mean": overall_metrics[metric],
                            "absolute_difference": segment_mean - overall_metrics[metric],
                            "percentage_difference": pct_diff,
                            "is_significant": is_significant,
                            "direction": "higher" if segment_mean > overall_metrics[metric] else "lower"
                        })
            
            # Sort by absolute percentage difference
            metric_comparisons.sort(key=lambda x: abs(x["percentage_difference"]), reverse=True)
            
            comparisons[metric] = metric_comparisons
        
        return comparisons
    
    def _generate_segment_insights(
        self,
        segment_metrics: Dict[str, Dict[str, Any]],
        metric_comparisons: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[str]]:
        """Generate insights based on segment analysis."""
        if not segment_metrics:
            return {
                "insights": ["No valid segments were found for analysis."],
                "recommendations": ["Ensure the segmentation variables have valid values."]
            }
        
        insights = []
        recommendations = []
        
        # General segmentation insights
        segment_count = len(segment_metrics)
        largest_segment = max(segment_metrics.items(), key=lambda x: x[1]["size"])
        largest_segment_name = largest_segment[0]
        largest_segment_pct = (largest_segment[1]["size"] / sum(info["size"] for info in segment_metrics.values())) * 100
        
        insights.append(f"Analysis identified {segment_count} distinct segments, with the largest segment ({largest_segment_name}) accounting for {largest_segment_pct:.1f}% of the data.")
        
        # Check for segment size distribution
        small_segments = [segment for segment, info in segment_metrics.items() if info["percentage"] < 5]
        if small_segments:
            insights.append(f"Found {len(small_segments)} small segments (< 5% of total), which may indicate specific niches or potential outliers.")
        
        # Analyze significant differences across metrics
        significant_differences = {}
        for metric, comparisons in metric_comparisons.items():
            # Filter for significant differences
            sig_diffs = [comp for comp in comparisons if comp["is_significant"]]
            if sig_diffs:
                significant_differences[metric] = sig_diffs
        
        # Generate insights for significant differences
        if significant_differences:
            total_sig_diffs = sum(len(diffs) for diffs in significant_differences.values())
            insights.append(f"Found {total_sig_diffs} significant differences (>10% from overall) across {len(significant_differences)} metrics.")
            
            # Highlight top differences for each metric (up to 3 metrics)
            for i, (metric, diffs) in enumerate(significant_differences.items()):
                if i >= 3:  # Limit to 3 metrics to avoid overwhelming
                    break
                
                # Take top 2 differences
                top_diffs = diffs[:2]
                for diff in top_diffs:
                    segment = diff["segment"]
                    pct_diff = diff["percentage_difference"]
                    direction = diff["direction"]
                    
                    insights.append(
                        f"Segment '{segment}' shows {abs(pct_diff):.1f}% {direction} {metric} compared to the overall average."
                    )
        else:
            insights.append("No significant differences found between segments, suggesting relatively homogeneous behavior across the defined segments.")
        
        # Generate recommendations
        if segment_count > 10:
            recommendations.append("Consider consolidating segments into broader categories for more meaningful analysis.")
        
        if significant_differences:
            # Recommend prioritizing segments with largest differences
            top_segments = set()
            for metric, diffs in significant_differences.items():
                for diff in diffs[:2]:  # Consider top 2 differences per metric
                    top_segments.add(diff["segment"])
            
            if top_segments:
                segments_str = ", ".join(f"'{segment}'" for segment in list(top_segments)[:3])
                recommendations.append(f"Focus further analysis on segments with significant differences: {segments_str}" + 
                                      ("..." if len(top_segments) > 3 else ""))
            
            # Recommend tailored strategies
            recommendations.append("Develop tailored strategies for segments with significantly different metrics to address their specific characteristics.")
        
        if small_segments:
            recommendations.append("For very small segments, evaluate whether they represent valuable niches or should be merged with other segments.")
        
        # Always recommend validation
        recommendations.append("Validate segmentation results with additional data or time periods to ensure stability of the identified patterns.")
        
        return {
            "insights": insights,
            "recommendations": recommendations
        }
    
    # Other helper methods
    
    def _calculate_median(self, values: List[float]) -> float:
        """Calculate the median of a list of values."""
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]
    
    def _calculate_standard_deviation(self, values: List[float]) -> float:
        """Calculate the standard deviation of a list of values."""
        n = len(values)
        if n < 2:
            return 0
        
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        return math.sqrt(variance)


# Create a singleton instance of the DataAnalysisAgent
_instance = None

def get_data_analysis_agent(**kwargs):
    """
    Get or create a singleton instance of the DataAnalysisAgent.
    
    Args:
        **kwargs: Additional arguments to pass to the DataAnalysisAgent constructor if a new instance is created.
        
    Returns:
        The singleton instance of the DataAnalysisAgent.
    """
    global _instance
    if _instance is None:
        _instance = DataAnalysisAgent(**kwargs)
    return _instance     


