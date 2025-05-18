# Domain-Specific Extension Guide for Agent Framework

This guide outlines how to extend the Agent Framework to support specialized domains beyond the existing capabilities. It provides step-by-step instructions for implementing new agent types, tools, and integrations to address specific business or technical domains.

## Table of Contents

1. [Understanding the Agent Architecture](#understanding-the-agent-architecture)
2. [Creating Domain-Specific Agents](#creating-domain-specific-agents)
3. [Developing Custom Tools](#developing-custom-tools)
4. [Integrating External Services](#integrating-external-services)
5. [Updating the Frontend](#updating-the-frontend)
6. [Testing and Validation](#testing-and-validation)
7. [Deployment Considerations](#deployment-considerations)
8. [Domain Extension Examples](#domain-extension-examples)

## Understanding the Agent Architecture

The Agent Framework uses a modular architecture with specialized agents coordinated by a moderator. Before extending the framework, it's essential to understand these key components:

### Core Components

1. **BaseAgent**: The foundation class in `base_agent.py` that all domain-specific agents extend.
2. **AgentInterface**: Manages agent registration and access in `agent_interface.py`.
3. **ModeratorAgent**: Routes queries to appropriate specialist agents.
4. **Function Tools**: Allow agents to perform specific actions, defined as Python functions.

### Agent Management Flow

1. The agent interface maintains templates of base agents.
2. Conversation-specific agent instances are created when needed.
3. The moderator analyzes user queries and routes them to specialist agents.
4. Specialist agents use domain-specific tools to respond to queries.

## Creating Domain-Specific Agents

To create a new domain-specific agent:

### 1. Create a New Agent File

Create a new Python file in `backend/app/services/agents/` named after your domain (e.g., `healthcare_agent.py`):

```python
from typing import Dict, List, Optional, Any, Union
import logging

from app.core.config import settings
from app.services.agents.base_agent import BaseAgent, AgentHooks, RunContextWrapper
from app.services.agents.common_context import CommonAgentContext

logger = logging.getLogger(__name__)

# Define domain-specific tools
async def analyze_medical_condition(condition: str, symptoms: Optional[str] = None) -> str:
    """
    Analyze a medical condition based on provided symptoms.
    
    Args:
        condition: The medical condition to analyze
        symptoms: Description of symptoms (optional)
        
    Returns:
        JSON string with analysis results
    """
    # Tool implementation
    # In a real implementation, this might query medical databases or use specialized models
    return "{\"analysis\": \"Medical condition analysis would appear here\"}"

async def recommend_treatment(condition: str, patient_data: Optional[str] = None) -> str:
    """
    Recommend treatment options for a medical condition.
    
    Args:
        condition: The medical condition requiring treatment
        patient_data: Additional patient information (optional)
        
    Returns:
        JSON string with treatment recommendations
    """
    # Tool implementation
    return "{\"treatments\": [\"Option 1\", \"Option 2\"]}"

# Define custom hooks (optional)
class HealthcareAgentHooks(AgentHooks):
    """Custom hooks for the healthcare agent."""
    
    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        await super().init_context(context)
        logger.info("Initialized context for HealthcareAgent")

# Create the agent class
class HealthcareAgent(BaseAgent):
    """
    Specialized agent for healthcare and medical information.
    Provides analysis of medical conditions, treatment recommendations,
    and general health information.
    """
    
    def __init__(self, name="HEALTHCARE"):
        super().__init__(
            name=name,
            model=settings.DEFAULT_AGENT_MODEL,
            instructions="""You are a healthcare information assistant.
            
Your role is to provide general health information, analyze medical conditions based on symptoms,
and suggest possible treatment options. You should be helpful but cautious, and always emphasize
that users should consult qualified healthcare professionals for personal medical advice.

When analyzing conditions or recommending treatments, use the specialized tools available to you.
Always provide balanced information and acknowledge the limitations of your knowledge.

IMPORTANT: You are not a substitute for professional medical advice, diagnosis, or treatment.
Always recommend consulting with qualified healthcare providers for personal health concerns.
""",
            functions=[
                analyze_medical_condition,
                recommend_treatment
            ],
            hooks=HealthcareAgentHooks()
        )
        
        # Add description property
        self.description = "Provides healthcare information, medical condition analysis, and treatment suggestions"

# Create the agent instance
healthcare_agent = HealthcareAgent()

# Expose the agent for importing by other modules
__all__ = ["healthcare_agent", "HealthcareAgent"]
```

### 2. Register the New Agent

The system will automatically detect and register your new agent. Simply create a file with your agent class and instance in the `backend/app/services/agents/` directory following the pattern in step 1.

The framework dynamically discovers new agent modules at runtime. Make sure your agent module includes:

1. A class that extends `BaseAgent` with a descriptive name
2. An instance of the agent created at the module level
3. An `__all__` list that includes the agent instance and class names

For example:

```python
# Create the agent instance
healthcare_agent = HealthcareAgent()

# Expose the agent for importing by other modules
__all__ = ["healthcare_agent", "HealthcareAgent"]
```

No explicit registration in the `__init__.py` file is needed as the framework will automatically find and register your agent.

### 3. Configure Agent Instructions

Design comprehensive instructions for your agent that define:
- The agent's purpose and domain expertise
- How it should respond to domain-specific questions
- Any limitations or ethical considerations
- When to use specialized tools vs. general knowledge

## Developing Custom Tools

Tools enable agents to perform specific actions within their domain. Each tool is a Python function that the agent can call.

### 1. Define Tool Functions

Create functions using the following pattern:

```python
async def domain_specific_tool(param1: str, param2: Optional[str] = None) -> str:
    """
    Clear description of what the tool does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)
        
    Returns:
        JSON string with results
    """
    # Tool implementation
    # Process inputs and generate outputs
    return "{\"result\": \"Tool output in JSON format\"}"
```

### 2. Add Tools to Your Agent

Add your tools to the agent's functions list:

```python
my_domain_agent = MyDomainAgent(
    name="MY_DOMAIN",
    functions=[
        domain_specific_tool_1,
        domain_specific_tool_2,
        domain_specific_tool_3
    ]
)
```

### 3. Tool Development Best Practices

- **Well-defined inputs/outputs**: Clearly document parameters and return values
- **Error handling**: Gracefully handle invalid inputs or external service failures
- **Logging**: Include appropriate logging for debugging and monitoring
- **Statelessness**: Design tools to be stateless and reusable
- **Return JSON**: Always return results as JSON strings for consistency

## Integrating External Services

Many domain-specific agents will need to integrate with external APIs or services.

### 1. Create a Service Integration

Create a new file in `backend/app/services/integrations/` for your service:

```python
# backend/app/services/integrations/medical_database_service.py
import logging
import aiohttp
from typing import Dict, List, Optional, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class MedicalDatabaseService:
    """
    Service for interacting with medical databases and APIs.
    """
    
    def __init__(self, api_key: str = settings.MEDICAL_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.medicaldatabase.example"
    
    async def search_conditions(self, query: str) -> Dict[str, Any]:
        """Search for medical conditions matching the query."""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with session.get(
                f"{self.base_url}/conditions/search",
                params={"q": query},
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error searching conditions: {response.status}")
                    return {"error": f"API error: {response.status}"}
    
    async def get_treatment_options(self, condition_id: str) -> Dict[str, Any]:
        """Get treatment options for a specific condition."""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with session.get(
                f"{self.base_url}/treatments/{condition_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error getting treatments: {response.status}")
                    return {"error": f"API error: {response.status}"}
```

### 2. Update Configuration

Add required environment variables to `backend/app/core/config.py`:

```python
# Add to Settings class
class Settings(BaseSettings):
    # ... existing settings
    
    # Medical Database API
    MEDICAL_API_KEY: str = ""
    
    # ...
```

### 3. Use the Service in Your Agent Tools

Import and use the service in your agent's tools:

```python
from app.services.integrations.medical_database_service import MedicalDatabaseService

# Create service instance
medical_db = MedicalDatabaseService()

async def analyze_medical_condition(condition: str, symptoms: Optional[str] = None) -> str:
    """Analyze a medical condition based on provided symptoms."""
    try:
        # Use the integration service
        results = await medical_db.search_conditions(condition)
        
        # Process and return results
        return json.dumps(results)
    except Exception as e:
        logger.error(f"Error in analyze_medical_condition: {str(e)}")
        return json.dumps({"error": str(e)})
```

## Updating the Frontend

The frontend will automatically detect new agents based on the API responses, so manual updates to the frontend code are not needed. When you create a new agent:

1. The backend API endpoints `/api/agents/available` and `/api/agents/descriptions` will automatically include your new agent
2. The frontend will dynamically display the new agent in the agent selection UI
3. The agent's description (set via `self.description` in your agent class) will be used for display purposes

No changes are required to:
- Agent type enums
- Agent description mappings
- Frontend component configurations

This dynamic approach ensures that adding new agents is a backend-only operation with no frontend code changes required.
```

### 3. Create Agent-Specific UI Components (Optional)

For specialized visualizations or interactions, create agent-specific components:

```typescript
// frontend/src/components/agent/HealthcareResults.tsx
import React from 'react';

interface TreatmentOption {
  name: string;
  description: string;
}

interface HealthcareResultsProps {
  condition: string;
  treatments: TreatmentOption[];
}

export const HealthcareResults: React.FC<HealthcareResultsProps> = ({ 
  condition, 
  treatments 
}) => {
  return (
    <div className="bg-white rounded-lg p-4 shadow-md">
      <h3 className="font-semibold text-lg mb-2">Condition: {condition}</h3>
      
      <h4 className="font-medium mt-3 mb-1">Treatment Options:</h4>
      <ul className="list-disc pl-5">
        {treatments.map((treatment, index) => (
          <li key={index} className="mb-2">
            <p className="font-medium">{treatment.name}</p>
            <p className="text-sm text-gray-600">{treatment.description}</p>
          </li>
        ))}
      </ul>
      
      <div className="mt-4 text-xs text-gray-500 italic">
        Note: This information is for educational purposes only and should not
        replace professional medical advice.
      </div>
    </div>
  );
};
```

## Testing and Validation

### 1. Create Unit Tests

Create tests for your agent and tools in `backend/tests/test_services/test_agents/`:

```python
# backend/tests/test_services/test_agents/test_healthcare_agent.py
import pytest
from unittest.mock import patch, AsyncMock

from app.services.agents.healthcare_agent import (
    healthcare_agent,
    analyze_medical_condition,
    recommend_treatment
)

class TestHealthcareAgent:
    
    def test_agent_initialization(self):
        """Test that the healthcare agent initializes correctly."""
        assert healthcare_agent.name == "HEALTHCARE"
        assert "healthcare information assistant" in healthcare_agent.instructions.lower()
        assert len(healthcare_agent.functions) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_medical_condition(self):
        """Test the analyze_medical_condition tool."""
        result = await analyze_medical_condition("diabetes", "frequent urination")
        assert "analysis" in result
    
    @pytest.mark.asyncio
    @patch('app.services.integrations.medical_database_service.MedicalDatabaseService.get_treatment_options')
    async def test_recommend_treatment(self, mock_get_treatment_options):
        """Test the recommend_treatment tool with a mocked service."""
        # Set up the mock
        mock_get_treatment_options.return_value = AsyncMock(return_value={
            "treatments": ["Insulin therapy", "Dietary changes"]
        })
        
        result = await recommend_treatment("diabetes")
        assert "treatments" in result
```

### 2. Create Integration Tests

Test the interaction between your agent and the rest of the system:

```python
# backend/tests/test_services/test_integration/test_healthcare_integration.py
import pytest
from unittest.mock import patch

from app.services.agents.agent_interface import agent_interface
from app.services.agents.moderator_agent import moderator_agent

class TestHealthcareIntegration:
    
    @pytest.mark.asyncio
    async def test_agent_registration(self):
        """Test that the healthcare agent is properly registered."""
        agents = agent_interface.get_agent_types()
        assert "HEALTHCARE" in agents
    
    @pytest.mark.asyncio
    @patch('app.services.agents.moderator_agent.ModeratorAgent.select_agent')
    async def test_moderator_routing(self, mock_select_agent):
        """Test that the moderator correctly routes healthcare queries."""
        # Set up the test
        mock_select_agent.return_value = "HEALTHCARE"
        
        # Test with a healthcare-related query
        result = await moderator_agent.select_agent(
            "What are the treatments for type 2 diabetes?"
        )
        
        assert result == "HEALTHCARE"
```

## Deployment Considerations

### 1. Environment Variables

Add any required environment variables to your deployment configuration:

```
# Add to .env file and deployment configuration
MEDICAL_API_KEY=your-medical-api-key
HEALTHCARE_MODEL=gpt-4  # Optional: use a specific model for healthcare
```

### 2. Documentation Updates

Update documentation to include:
- Agent capabilities and limitations
- Required environment variables
- Any special setup or integration requirements
- Usage examples for domain-specific functionality

### 3. Security and Compliance

For sensitive domains like healthcare:
- Ensure compliance with regulations (HIPAA, GDPR, etc.)
- Implement appropriate data protection measures
- Add relevant disclaimers to user interfaces
- Consider additional security measures for sensitive data

## Domain Extension Examples

Here are examples of how you might extend the framework for specific domains:

### Legal Domain

```python
# backend/app/services/agents/legal_agent.py
class LegalAgent(BaseAgent):
    """
    Specialized agent for legal information and assistance.
    """
    
    def __init__(self, name="LEGAL"):
        super().__init__(
            name=name,
            instructions="""You are a legal information assistant...""",
            functions=[
                analyze_legal_document,
                summarize_case_law,
                check_compliance
            ]
        )
        
        self.description = "Provides legal information, document analysis, and compliance guidance"
```

### E-commerce Domain

```python
# backend/app/services/agents/ecommerce_agent.py
class EcommerceAgent(BaseAgent):
    """
    Specialized agent for e-commerce operations and analysis.
    """
    
    def __init__(self, name="ECOMMERCE"):
        super().__init__(
            name=name,
            instructions="""You are an e-commerce operations specialist...""",
            functions=[
                analyze_product_performance,
                optimize_pricing,
                recommend_inventory_levels
            ]
        )
        
        self.description = "Analyzes e-commerce operations, product performance, and sales strategies"
```

### Education Domain

```python
# backend/app/services/agents/education_agent.py
class EducationAgent(BaseAgent):
    """
    Specialized agent for educational content and learning assistance.
    """
    
    def __init__(self, name="EDUCATION"):
        super().__init__(
            name=name,
            instructions="""You are an educational assistant...""",
            functions=[
                create_lesson_plan,
                generate_quiz_questions,
                explain_concept
            ]
        )
        
        self.description = "Creates educational content, lesson plans, and learning materials"
```

By following this guide, you can extend the Agent Framework to support virtually any domain, creating specialized agents with domain-specific tools and integrations that enhance the system's capabilities.