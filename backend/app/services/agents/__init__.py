from app.services.agents.moderator_agent import moderator_agent, ModeratorAgent
from app.services.agents.business_agent import business_agent, BusinessAgent
from app.services.agents.business_intelligence_agent import business_intelligence_agent, BusinessIntelligenceAgent
from app.services.agents.data_analysis_agent import data_analysis_agent, DataAnalysisAgent
from app.services.agents.web_search_agent import web_search_agent, WebSearchAgent
from app.services.agents.document_search_agent import document_search_agent, DocumentSearchAgent
from app.services.agents.monitor_agent import monitor_agent, MonitorAgent
from app.services.agents.agent_interface import agent_interface

# Register all agents with the moderator
moderator_agent.register_agent(business_agent)
moderator_agent.register_agent(business_intelligence_agent)
moderator_agent.register_agent(data_analysis_agent)
moderator_agent.register_agent(web_search_agent)
moderator_agent.register_agent(document_search_agent)
moderator_agent.register_agent(monitor_agent)

# Register all agents with the agent interface
agent_interface.register_base_agent("MODERATOR", moderator_agent)
agent_interface.register_base_agent("BUSINESS", business_agent)
agent_interface.register_base_agent("BUSINESSINTELLIGENCE", business_intelligence_agent)
agent_interface.register_base_agent("DATAANALYSIS", data_analysis_agent)
agent_interface.register_base_agent("WEBSEARCH", web_search_agent)
agent_interface.register_base_agent("DOCUMENTSEARCH", document_search_agent)
agent_interface.register_base_agent("MONITOR", monitor_agent)

# Update moderator with all agent descriptions
moderator_agent.update_instructions(agent_interface.get_agent_descriptions())

# Exports
__all__ = [
    "agent_interface",
    "moderator_agent",
    "business_agent",
    "business_intelligence_agent",
    "data_analysis_agent",
    "web_search_agent",
    "document_search_agent",
    "monitor_agent",
    "ModeratorAgent",
    "BusinessAgent",
    "BusinessIntelligenceAgent",
    "DataAnalysisAgent",
    "WebSearchAgent",
    "DocumentSearchAgent",
    "MonitorAgent"
]