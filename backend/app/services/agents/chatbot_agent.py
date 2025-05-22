from typing import Dict, Any, Optional, List
import logging
from app.core.config import settings
from app.services.agents.base_agent import BaseAgent
from agents import Agent, function_tool, ModelSettings, RunContextWrapper
from agents.run_context import RunContextWrapper
import json

logger = logging.getLogger(__name__)

class ChatbotAgent(BaseAgent):
    """
    ChatbotAgent is a specialized agent that engages in friendly, succinct, and cogent conversations.
    
    This agent specializes in natural conversation flow, engaging responses, and maintaining
    context while being concise and clear in communication.
    """

    def __init__(
        self,
        name: str = "Chatbot Agent",
        model: str = settings.DEFAULT_AGENT_MODEL,
        tool_choice: Optional[str] = "auto",
        parallel_tool_calls: bool = True,
        **kwargs
    ):
        """
        Initialize a ChatbotAgent with specialized conversational instructions.
        
        Args:
            name: The name of the agent. Defaults to "Chatbot Agent".
            model: The model to use. Defaults to settings.DEFAULT_AGENT_MODEL.
            tool_choice: The tool choice strategy to use. Defaults to "auto".
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            **kwargs: Additional arguments to pass to the Agent constructor.
        """
        # Define the chatbot instructions
        chatbot_instructions = """You are a friendly, intelligent conversational assistant who engages in natural dialogue. Your communication style is:

1. CONVERSATIONAL PRINCIPLES
- Be friendly and approachable
- Keep responses succinct and to-the-point
- Maintain cogent, logical flow in conversations
- Show genuine interest in the user's thoughts
- Use natural, conversational language
- Adapt tone to match the conversation context

2. RESPONSE GUIDELINES
- Prioritize clarity over complexity
- Use simple, everyday language
- Avoid unnecessary jargon or formality
- Keep responses focused and relevant
- Be helpful without being verbose
- Use appropriate humor when suitable

3. ENGAGEMENT STRATEGIES
- Ask thoughtful follow-up questions
- Show active listening through acknowledgment
- Build on previous conversation points
- Remember context throughout the dialogue
- Offer relevant insights or perspectives
- Encourage continued conversation naturally

4. CONVERSATION FLOW
- Maintain natural transitions between topics
- Reference earlier points when relevant
- Summarize complex discussions clearly
- Guide conversations constructively
- Know when to change subjects gracefully
- Balance speaking and listening

5. EMOTIONAL INTELLIGENCE
- Recognize emotional cues in messages
- Respond with appropriate empathy
- Celebrate positive moments with users
- Provide support during challenges
- Maintain professional boundaries
- Use encouraging language

6. KNOWLEDGE SHARING
- Share information conversationally
- Explain complex topics simply
- Provide examples when helpful
- Admit when unsure about something
- Offer to explore topics together
- Connect ideas to user interests

7. CONVERSATION MANAGEMENT
- Keep track of discussion threads
- Circle back to unfinished topics
- Gracefully handle topic changes
- Maintain conversation momentum
- Know when to conclude naturally
- Leave conversations open-ended when appropriate

Remember: Every interaction should feel like a natural conversation with a knowledgeable, friendly companion who values the user's time and engagement."""

        # Define the tools
        tools = [
            function_tool(self.analyze_conversation_context),
            function_tool(self.craft_engaging_response),
            function_tool(self.suggest_conversation_direction),
            function_tool(self.extract_conversation_insights)
        ]
        
        # Initialize the Agent class directly
        super().__init__(
            name=name,
            model=model,
            instructions=chatbot_instructions,
            functions=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
            **kwargs
        )

    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for the ChatbotAgent.
        
        Args:
            context: The context wrapper object with conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Add any agent-specific context initialization here
        logger.info(f"Initialized context for ChatbotAgent")
        
    @property
    def description(self) -> str:
        """
        Get a description of this agent's capabilities.
        
        Returns:
            A string describing the agent's specialty.
        """
        return "Engaging conversationalist specializing in friendly, succinct, and cogent dialogue with natural flow and contextual awareness"

    def analyze_conversation_context(
        self, 
        context: RunContextWrapper,
        recent_messages: Optional[List[str]] = None,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze the conversation context to understand the user's needs, mood, and conversation direction.
        
        Args:
            context: The run context wrapper.
            recent_messages: List of recent messages in the conversation.
            user_message: The current user message to analyze.
                
        Returns:
            Analysis of conversation context including mood, intent, and engagement recommendations.
        """
        # Handle default values inside the function
        if recent_messages is None:
            recent_messages = []
        if user_message is None:
            user_message = ""
            
        logger.info(f"Analyzing conversation context for message: {user_message[:100]}...")
        
        # Build context string for analysis
        context_str = ""
        if recent_messages:
            context_str = "Recent conversation:\n" + "\n".join(recent_messages[-5:])  # Last 5 messages
            
        # Analyze the current message
        message_length = len(user_message.split())
        has_question = "?" in user_message
        has_exclamation = "!" in user_message
        
        # Determine conversation characteristics
        if message_length < 5:
            message_type = "brief"
        elif message_length < 20:
            message_type = "moderate"
        else:
            message_type = "detailed"
            
        # Analyze emotional indicators
        positive_indicators = ["thanks", "great", "awesome", "wonderful", "love", "appreciate", "good"]
        negative_indicators = ["problem", "issue", "wrong", "bad", "hate", "frustrated", "confused"]
        
        positive_count = sum(1 for word in positive_indicators if word.lower() in user_message.lower())
        negative_count = sum(1 for word in negative_indicators if word.lower() in user_message.lower())
        
        if positive_count > negative_count:
            detected_mood = "positive"
        elif negative_count > positive_count:
            detected_mood = "concerned"
        else:
            detected_mood = "neutral"
            
        # Determine user intent
        if has_question:
            primary_intent = "seeking_information"
        elif any(word in user_message.lower() for word in ["help", "how", "what", "why", "when", "where"]):
            primary_intent = "requesting_assistance"
        elif any(word in user_message.lower() for word in ["tell me", "explain", "describe"]):
            primary_intent = "learning"
        else:
            primary_intent = "sharing_thoughts"
            
        return {
            "user_message_length": message_length,
            "message_type": message_type,
            "has_question": has_question,
            "detected_mood": detected_mood,
            "primary_intent": primary_intent,
            "conversation_depth": len(recent_messages),
            "engagement_recommendations": {
                "response_style": "empathetic and helpful" if detected_mood == "concerned" else "friendly and engaging",
                "response_length": "brief" if message_type == "brief" else "moderate",
                "include_question": True if primary_intent != "seeking_information" else False,
                "tone": "supportive" if detected_mood == "concerned" else "conversational"
            },
            "context_summary": f"User appears {detected_mood} and is {primary_intent.replace('_', ' ')}. Message is {message_type}."
        }
    
    def craft_engaging_response(
        self, 
        context: RunContextWrapper,
        user_input: Optional[str] = None,
        response_style: Optional[str] = None,
        include_question: Optional[bool] = None,
        max_sentences: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Craft an engaging response that maintains conversation flow and addresses the user's needs.
        
        Args:
            context: The run context wrapper.
            user_input: The user's message to respond to.
            response_style: Desired response style (e.g., "friendly", "informative", "supportive").
            include_question: Whether to include a follow-up question.
            max_sentences: Maximum number of sentences in the response.
            
        Returns:
            A structured response with main content and optional follow-up.
        """
        # Set default values if not provided
        if user_input is None:
            user_input = "Hello!"
        if response_style is None:
            response_style = "friendly"
        if include_question is None:
            include_question = True
        if max_sentences is None:
            max_sentences = 3
            
        logger.info(f"Crafting {response_style} response to: {user_input[:50]}...")
        
        # Ensure max_sentences is reasonable
        if max_sentences < 1:
            max_sentences = 1
        elif max_sentences > 5:
            max_sentences = 5
            
        # Create response components based on style
        response_templates = {
            "friendly": {
                "greeting": "I appreciate you sharing that!",
                "acknowledgment": "I understand what you're saying.",
                "main_point": "Here's what I think might help:",
                "closing": "What do you think about that?"
            },
            "informative": {
                "greeting": "Thanks for your question.",
                "acknowledgment": "Let me provide some clarity on that.",
                "main_point": "Here's what you need to know:",
                "closing": "Would you like more details on any part?"
            },
            "supportive": {
                "greeting": "I hear you, and I'm here to help.",
                "acknowledgment": "That sounds challenging.",
                "main_point": "Let's work through this together:",
                "closing": "How are you feeling about this approach?"
            },
            "enthusiastic": {
                "greeting": "That's fantastic!",
                "acknowledgment": "I love your enthusiasm about this!",
                "main_point": "Here's something exciting to consider:",
                "closing": "What excites you most about this?"
            }
        }
        
        # Get appropriate template
        template = response_templates.get(response_style, response_templates["friendly"])
        
        # Build response structure
        response_structure = {
            "response_style": response_style,
            "components": {
                "acknowledgment": template["acknowledgment"],
                "main_response": template["main_point"],
                "follow_up": template["closing"] if include_question else ""
            },
            "suggested_response": f"{template['acknowledgment']} {template['main_point']}",
            "max_sentences": max_sentences,
            "response_guidelines": [
                f"Keep response to {max_sentences} sentences",
                f"Maintain {response_style} tone throughout",
                "Address the user's specific point",
                "Use natural, conversational language"
            ]
        }
        
        if include_question:
            response_structure["suggested_response"] += f" {template['closing']}"
            
        return response_structure
    
    def suggest_conversation_direction(
        self, 
        context: RunContextWrapper,
        current_topic: Optional[str] = None,
        conversation_history: Optional[List[str]] = None,
        user_interests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Suggest natural conversation directions based on current context and user engagement.
        
        Args:
            context: The run context wrapper.
            current_topic: The current topic being discussed.
            conversation_history: Recent conversation messages.
            user_interests: Known or inferred user interests.
            
        Returns:
            Suggestions for conversation direction with transitions and topic ideas.
        """    
        # Handle default values in function body
        if current_topic is None:
            current_topic = "general conversation"
        if conversation_history is None:
            conversation_history = []
        if user_interests is None:
            user_interests = []
            
        logger.info(f"Suggesting conversation directions from topic: {current_topic}")
        
        # Analyze conversation depth
        message_count = len(conversation_history)
        conversation_stage = "opening" if message_count < 3 else "developing" if message_count < 10 else "established"
        
        # Create topic transitions based on current topic
        related_topics = {
            "technology": ["innovation trends", "personal tech experiences", "future possibilities"],
            "hobbies": ["recent activities", "learning new skills", "community connections"],
            "work": ["career growth", "work-life balance", "interesting projects"],
            "travel": ["memorable experiences", "dream destinations", "local discoveries"],
            "general conversation": ["daily experiences", "current interests", "recent discoveries"]
        }
        
        # Get related topics or default
        topic_suggestions = related_topics.get(current_topic.lower(), related_topics["general conversation"])
        
        # Build transition phrases
        transition_phrases = {
            "opening": [
                "I'd love to hear more about",
                "That reminds me to ask about",
                "Speaking of which,"
            ],
            "developing": [
                "Building on what you said,",
                "That's interesting! It makes me wonder about",
                "Related to that,"
            ],
            "established": [
                "We've covered a lot! I'm curious about",
                "Circling back to something you mentioned,",
                "On a different note,"
            ]
        }
        
        suggestions = {
            "current_topic": current_topic,
            "conversation_stage": conversation_stage,
            "message_count": message_count,
            "suggested_directions": topic_suggestions[:3],
            "transition_options": transition_phrases.get(conversation_stage, transition_phrases["developing"]),
            "engagement_tactics": {
                "ask_for_elaboration": "Could you tell me more about that?",
                "share_related_thought": "That reminds me of...",
                "explore_deeper": "What's your perspective on...",
                "lighten_mood": "On a lighter note...",
                "personal_connection": "I find it interesting how..."
            },
            "natural_transitions": [
                f"{transition_phrases[conversation_stage][0]} {topic_suggestions[0]}",
                f"{transition_phrases[conversation_stage][1]} {topic_suggestions[1]}"
            ],
            "recommendation": f"For this {conversation_stage} conversation about {current_topic}, consider gently steering toward {topic_suggestions[0]} while maintaining engagement."
        }
        
        return suggestions
    
    def extract_conversation_insights(
        self,
        context: RunContextWrapper,
        messages: Optional[List[Dict[str, str]]] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract meaningful insights from the conversation to improve future interactions.
        
        Args:
            context: The run context wrapper.
            messages: List of message dictionaries with 'role' and 'content'.
            focus_areas: Specific areas to analyze (e.g., ["preferences", "concerns", "interests"]).
            
        Returns:
            Extracted insights about the user and conversation patterns.
        """
        # Handle default values in function body
        if messages is None:
            messages = []
        if focus_areas is None:
            focus_areas = ["interests", "communication_style", "engagement_patterns"]
            
        logger.info(f"Extracting insights from {len(messages)} messages")
        
        # Analyze message patterns
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        
        # Calculate engagement metrics
        avg_user_message_length = sum(len(m.get("content", "").split()) for m in user_messages) / max(len(user_messages), 1)
        total_questions = sum(1 for m in user_messages if "?" in m.get("content", ""))
        
        # Extract topics mentioned
        common_topics = {
            "interests": ["hobby", "like", "enjoy", "love", "favorite", "interested"],
            "concerns": ["worried", "concerned", "problem", "issue", "difficult"],
            "preferences": ["prefer", "rather", "better", "instead", "favorite"],
            "experiences": ["tried", "visited", "experienced", "learned", "discovered"]
        }
        
        detected_patterns = {}
        for category, keywords in common_topics.items():
            count = sum(1 for m in user_messages for keyword in keywords if keyword in m.get("content", "").lower())
            if count > 0:
                detected_patterns[category] = count
                
        # Build insights
        insights = {
            "conversation_metrics": {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "average_message_length": round(avg_user_message_length, 1),
                "questions_asked": total_questions,
                "engagement_level": "high" if len(user_messages) > 10 else "moderate" if len(user_messages) > 5 else "warming up"
            },
            "communication_patterns": {
                "prefers_detailed_responses": avg_user_message_length > 15,
                "asks_questions": total_questions > len(user_messages) * 0.3,
                "conversation_style": "inquisitive" if total_questions > 3 else "sharing" if avg_user_message_length > 20 else "casual"
            },
            "detected_themes": detected_patterns,
            "engagement_insights": {
                "most_engaged_topics": list(detected_patterns.keys())[:3] if detected_patterns else ["general conversation"],
                "conversation_depth": "deep" if avg_user_message_length > 25 else "moderate" if avg_user_message_length > 10 else "light",
                "interaction_preference": "interactive" if total_questions > 2 else "listening"
            },
            "recommendations": {
                "response_style": "detailed and thorough" if avg_user_message_length > 20 else "concise and clear",
                "engagement_approach": "ask follow-up questions" if not total_questions > 3 else "provide thoughtful answers",
                "topic_focus": list(detected_patterns.keys())[0] if detected_patterns else "explore interests"
            },
            "summary": f"User shows {detected_patterns.get('interests', 0)} interest indicators, "
                      f"{detected_patterns.get('concerns', 0)} concerns, and prefers "
                      f"{'detailed' if avg_user_message_length > 20 else 'concise'} exchanges."
        }
        
        return insights
