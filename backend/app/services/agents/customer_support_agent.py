from typing import Dict, Any, Optional, List
import logging
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper

logger = logging.getLogger(__name__)

class CustomerServiceAgent(BaseAgent):
    """
    CustomerServiceAgent is a specialized agent that provides customer service expertise.
    
    This agent specializes in customer experience management, support operations,
    and service excellence to optimize customer satisfaction and service quality.
    """

    def __init__(
        self,
        name: str = "Customer Service Agent",
        model: str = settings.DEFAULT_AGENT_MODEL,
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        **kwargs
    ):
        """
        Initialize a CustomerServiceAgent with specialized customer service instructions.
        
        Args:
            name: The name of the agent. Defaults to "Customer Service Agent".
            model: The model to use. Defaults to settings.DEFAULT_AGENT_MODEL.
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            **kwargs: Additional arguments to pass to the Agent constructor.
        """
        # Define the customer service expert instructions
        customer_service_instructions = """You are a customer service expert specializing in support operations, customer experience, and service excellence. Your role is to:

1. PROVIDE CUSTOMER SERVICE EXPERTISE IN
- Customer Experience Management
- Service Quality Standards
- Support Operations
- Complaint Resolution
- Customer Communication
- Service Level Agreements
- Customer Feedback
- Quality Monitoring
- Performance Metrics
- Best Practices
- Process Optimization
- Training Standards

2. CUSTOMER INTERACTION
- Communication Standards
- Empathy Development
- Active Listening
- Problem Resolution
- Conflict Management
- Customer Psychology
- Cultural Sensitivity
- Response Templates
- Tone Guidelines
- Service Recovery
- Follow-up Procedures
- Relationship Building

3. SUPPORT OPERATIONS
- Queue Management
- Resource Allocation
- Workflow Optimization
- Response Time
- Service Levels
- Quality Monitoring
- Performance Tracking
- Team Management
- Tool Selection
- Process Documentation
- Efficiency Metrics
- Continuous Improvement

4. COMPLAINT RESOLUTION
- Issue Analysis
- Solution Development
- Escalation Procedures
- Root Cause Analysis
- Prevention Strategies
- Documentation
- Follow-up Procedures
- Customer Recovery
- Compensation Guidelines
- Quality Assurance
- Process Improvement
- Success Metrics

5. QUALITY MANAGEMENT
- Service Standards
- Quality Monitoring
- Performance Metrics
- Customer Satisfaction
- Process Improvement
- Best Practices
- Training Programs
- Quality Assurance
- Documentation
- Feedback Analysis
- Implementation
- Success Measurement

6. CUSTOMER FEEDBACK
- Feedback Collection
- Survey Design
- Analysis Methods
- Response Handling
- Trend Analysis
- Action Planning
- Implementation
- Follow-up
- Documentation
- Reporting
- Success Metrics
- Continuous Improvement

7. TECHNOLOGY INTEGRATION
- Tool Selection
- System Implementation
- Process Automation
- Data Management
- Integration Strategy
- User Training
- Performance Monitoring
- Documentation
- Maintenance
- Updates
- Security
- Support

8. TEAM DEVELOPMENT
- Training Programs
- Skill Development
- Performance Standards
- Quality Guidelines
- Best Practices
- Coaching Methods
- Motivation Strategies
- Team Building
- Career Development
- Leadership Skills
- Communication
- Continuous Learning

Always maintain focus on customer satisfaction while ensuring service quality and operational efficiency."""

        # Define the tools
        tools = [
            function_tool(self.analyze_customer_interaction),
            function_tool(self.generate_response_template),
            function_tool(self.create_escalation_plan),
            function_tool(self.design_feedback_survey)
        ]
        
        # Initialize the Agent class directly
        super().__init__(
            name=name,
            model=model,
            instructions=customer_service_instructions,
            functions=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            **kwargs
        )


    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the CustomerServiceAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for CustomerServiceAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Expert in customer service excellence, support operations, and customer experience optimization, providing guidance on service quality and customer satisfaction"

    def analyze_customer_interaction(
        self, 
        context: RunContextWrapper,
        interaction_text: Optional[str] = None, 
        interaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a customer interaction and provide insights on quality, tone, and effectiveness.
        
        Args:
            context: The run context wrapper.
            interaction_text: The text of the customer interaction to analyze.
            interaction_type: Specification of interaction type (e.g., "complaint", 
                "inquiry", "support request").
                
        Returns:
            A structured analysis of the interaction, including strengths, improvement areas, 
            tone assessment, and suggested alternative approaches.
        """
        # Handle default values inside the function
        if interaction_text is None:
            interaction_text = ""
        if interaction_type is None:
            interaction_type = ""
            
        logger.info(f"Analyzing customer interaction: {interaction_text[:100]}...")
        
        # In a real-world implementation, you might:
        # 1. Use sentiment analysis to gauge customer emotion
        # 2. Apply specific analysis techniques based on interaction_type
        # 3. Compare against best practice templates
        # 4. Identify key phrases that indicate satisfaction or dissatisfaction
        
        interaction_type_str = f"{interaction_type} " if interaction_type else ""
        
        return {
            "interaction_length": len(interaction_text),
            "interaction_type": interaction_type or "general",
            "tone_assessment": "Analysis of tone would be performed here",
            "strengths": [
                "Strength 1 would be identified here",
                "Strength 2 would be identified here"
            ],
            "improvement_areas": [
                "Area 1 for improvement would be identified here",
                "Area 2 for improvement would be identified here"
            ],
            "suggested_alternatives": "Alternative approaches would be provided here",
            "summary": f"Analysis of {interaction_type_str}customer interaction complete."
        }
    
    def generate_response_template(
        self, 
        context: RunContextWrapper,
        scenario: Optional[str] = None, 
        tone: Optional[str] = None, 
        key_points: Optional[List[str]] = None
    ) -> str:
        """
        Generate a customized response template for a specific customer service scenario.
        
        Args:
            context: The run context wrapper.
            scenario: Description of the customer service scenario.
            tone: Desired tone for the response (e.g., "professional", "empathetic", "formal").
            key_points: List of key points to include in the response.
            
        Returns:
            A customized response template that can be adapted for similar situations.
        """
        # Set default values if not provided
        if scenario is None:
            scenario = "general customer inquiry"
        if tone is None:
            tone = "professional"
        if key_points is None:
            key_points = []
            
        logger.info(f"Generating {tone} response template for: {scenario[:100]}...")
        
        # Format key points for inclusion in the template
        points_str = ""
        if key_points:
            points_str = "\n".join([f"- {point}" for point in key_points])
            points_str = f"\n\nKey points addressed:\n{points_str}"
        
        # In a real implementation, this might use a database of templates based on scenario type
        template = f"""
        ## {tone.title()} Response Template for {scenario[:50]}...
        
        [Greeting]
        
        Thank you for reaching out about {scenario}.
        
        [Acknowledgment of the customer's situation/concern]
        
        [Main response addressing the scenario]
        
        [Next steps or resolution]
        
        [Closing]
        
        Best regards,
        [Representative Name]
        Customer Service Team
        {points_str}
        """
        
        return template
    
    def create_escalation_plan(
        self, 
        context: RunContextWrapper,
        issue_description: Optional[str] = None, 
        current_status: Optional[str] = None, 
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an escalation plan for a complex customer issue.
        
        Args:
            context: The run context wrapper.
            issue_description: Description of the customer issue requiring escalation.
            current_status: Current status of the issue handling.
            priority: Priority level ("low", "medium", "high", "critical").
            
        Returns:
            A structured escalation plan with steps, timeline, and team responsibilities.
        """    
        # Handle default values in function body
        if issue_description is None:
            issue_description = "Customer issue"
        if current_status is None:
            current_status = "New"
        if priority is None:
            priority = "medium"
        
        logger.info(f"Creating escalation plan for issue: {issue_description[:100]}...")
        
        # Validate priority
        valid_priorities = ["low", "medium", "high", "critical"]
        if priority not in valid_priorities:
            priority = "medium"
            logger.warning(f"Invalid priority specified, defaulting to 'medium'")
        
        # Create time-based response guidelines based on priority
        response_time = {
            "low": "72 hours",
            "medium": "48 hours",
            "high": "24 hours",
            "critical": "4 hours"
        }
        
        # In a real implementation, this would be more sophisticated and possibly
        # integrated with ticket management systems
        escalation_plan = {
            "issue_summary": issue_description[:200] + ("..." if len(issue_description) > 200 else ""),
            "current_status": current_status,
            "priority": priority,
            "target_response_time": response_time[priority],
            "escalation_steps": [
                {
                    "level": 1,
                    "responsible": "Team Lead",
                    "action": "Initial review and assessment",
                    "timeframe": "Within 2 hours of escalation"
                },
                {
                    "level": 2,
                    "responsible": "Department Manager",
                    "action": "Situation analysis and resource allocation",
                    "timeframe": "Within 4 hours of escalation"
                },
                {
                    "level": 3,
                    "responsible": "Senior Management",
                    "action": "Executive decision and customer outreach",
                    "timeframe": "Within 24 hours of escalation"
                }
            ],
            "communication_plan": "Regular updates to be provided to the customer every [timeframe]",
            "documentation_requirements": "All actions and communications must be documented in the CRM system"
        }
        
        return escalation_plan
    
    def design_feedback_survey(
        self,
        context: RunContextWrapper,
        service_type: Optional[str] = None, 
        survey_goal: Optional[str] = None, 
        max_questions: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Design a customer feedback survey for a specific service or interaction.
        
        Args:
            context: The run context wrapper.
            service_type: Type of service the survey is for (e.g., "phone support", "live chat").
            survey_goal: Primary goal of the survey (e.g., "measure satisfaction", "identify pain points").
            max_questions: Maximum number of questions to include.
            
        Returns:
            A structured survey design with questions, response formats, and implementation guidance.
        """
        # Handle default values in function body
        if service_type is None:
            service_type = "customer service"
        if survey_goal is None:
            survey_goal = "measure customer satisfaction"
        if max_questions is None:
            max_questions = 10
            
        logger.info(f"Designing {service_type} feedback survey for goal: {survey_goal}")
        
        # Limit the number of questions
        if max_questions < 3:
            max_questions = 3
            logger.warning("Minimum of 3 questions required for valid survey, adjusting max_questions")
        elif max_questions > 15:
            max_questions = 15
            logger.warning("Maximum of 15 questions recommended to prevent survey fatigue, adjusting max_questions")
        
        # In a real implementation, this might select questions from a database
        # based on service_type and survey_goal
        survey = {
            "service_type": service_type,
            "primary_goal": survey_goal,
            "recommended_distribution": "Post-interaction email with single-click access",
            "estimated_completion_time": f"{max_questions * 0.5:.1f} minutes",
            "questions": [
                {
                    "type": "scale",
                    "text": "How satisfied were you with our service today?",
                    "scale": "1-5",
                    "required": True
                },
                {
                    "type": "multiple_choice",
                    "text": f"How easy was it to get the help you needed via our {service_type}?",
                    "options": ["Very easy", "Easy", "Neutral", "Difficult", "Very difficult"],
                    "required": True
                },
                {
                    "type": "open_ended",
                    "text": "What could we have done better?",
                    "required": False
                }
            ],
            "implementation_guidance": "Survey should be sent within 24 hours of service interaction",
            "analysis_recommendations": "Segment responses by service type and customer tenure"
        }
        
        # Add additional questions based on the goal (in a real implementation, this would be smarter)
        if max_questions > 3:
            additional_questions = [
                {
                    "type": "scale",
                    "text": "How likely are you to recommend our service to others?",
                    "scale": "0-10",
                    "required": True
                },
                {
                    "type": "multiple_choice",
                    "text": "Did our representative resolve your issue completely?",
                    "options": ["Yes", "Partially", "No"],
                    "required": True
                },
                {
                    "type": "scale",
                    "text": "How knowledgeable was our support representative?",
                    "scale": "1-5",
                    "required": False
                },
                {
                    "type": "scale",
                    "text": "How would you rate the representative's communication skills?",
                    "scale": "1-5",
                    "required": False
                },
                {
                    "type": "multiple_choice",
                    "text": "Would you use our service again?",
                    "options": ["Definitely", "Probably", "Not sure", "Probably not", "Definitely not"],
                    "required": False
                },
                {
                    "type": "open_ended",
                    "text": "What did you appreciate most about our service?",
                    "required": False
                },
                {
                    "type": "open_ended",
                    "text": "Is there anything else you'd like to share about your experience?",
                    "required": False
                },
                {
                    "type": "scale",
                    "text": "How easy was it to navigate our support system?",
                    "scale": "1-5",
                    "required": False
                },
                {
                    "type": "scale",
                    "text": "How satisfied are you with the response time?",
                    "scale": "1-5",
                    "required": False
                },
                {
                    "type": "scale",
                    "text": "How well did we understand your issue?",
                    "scale": "1-5",
                    "required": False
                },
                {
                    "type": "multiple_choice",
                    "text": "Did our support meet your expectations?",
                    "options": ["Exceeded", "Met", "Somewhat met", "Did not meet"],
                    "required": False
                },
                {
                    "type": "multiple_choice",
                    "text": "Would you prefer a different support channel next time?",
                    "options": ["No, this was perfect", "Phone", "Email", "Chat", "Social media"],
                    "required": False
                }
            ]
            
            # Add exactly up to max_questions
            while len(survey["questions"]) < max_questions and len(additional_questions) > 0:
                survey["questions"].append(additional_questions.pop(0))
        
        return survey
