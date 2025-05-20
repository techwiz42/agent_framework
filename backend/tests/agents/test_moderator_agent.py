import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import inspect

from app.services.agents.moderator_agent import (
    ModeratorAgent,
    moderator_agent,
    get_openai_client
)


class TestModeratorAgent:
    """Tests for the ModeratorAgent class and related functions."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Patch OpenAI client
        self.openai_patch = patch('app.services.agents.moderator_agent.AsyncOpenAI')
        self.mock_openai = self.openai_patch.start()
        self.mock_client = MagicMock()
        self.mock_openai.return_value = self.mock_client
        
        # Patch agent_interface
        self.agent_interface_patch = patch('app.services.agents.moderator_agent.agent_interface')
        self.mock_agent_interface = self.agent_interface_patch.start()
        
        # Mock context for tool tests
        self.mock_context = MagicMock()
        self.mock_inner_context = MagicMock()
        self.mock_context.context = self.mock_inner_context
        
        # Test data
        self.query = "Test query for agent selection"
        self.available_agents = "MODERATOR,SPECIALIST,EXPERT"
        
    def teardown_method(self):
        """Clean up after each test."""
        self.openai_patch.stop()
        self.agent_interface_patch.stop()

    @pytest.mark.asyncio
    async def test_get_openai_client(self):
        """Test getting the OpenAI client"""
        client = get_openai_client()
        assert client is not None
        self.mock_openai.assert_called_once()
        
        # Second call should create a new client (function doesn't cache)
        client2 = get_openai_client()
        assert self.mock_openai.call_count == 2

    def test_moderator_agent_initialization(self):
        """Test the ModeratorAgent initialization."""
        # Create a new agent
        agent = ModeratorAgent()
        
        # Verify basic properties
        assert agent.name == "MODERATOR"
        assert agent.description == "Routes queries to specialist agent experts"
        assert len(agent.tools) == 3
        assert len(agent.input_guardrails) == 1
        assert hasattr(agent, 'handoffs')
        assert agent.handoffs == []
        assert hasattr(agent, '_registered_agents')
        assert agent._registered_agents == {}
        
        # Verify tool configuration
        tool_names = set()
        for tool in agent.tools:
            if hasattr(tool, 'name'):
                tool_names.add(tool.name)
        
        assert "select_agent" in tool_names
        assert "check_collaboration_need" in tool_names
        assert "synthesize_collaborative_responses" in tool_names
        
        # Verify moderator_agent singleton exists
        assert moderator_agent is not None
        assert moderator_agent.name == "MODERATOR"

    def test_register_agent(self):
        """Test registering an agent with the moderator."""
        # Create a moderator and mock agent to register
        moderator = ModeratorAgent()
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"
        mock_agent.description = "Test agent description"
        
        # Register the agent
        moderator.register_agent(mock_agent)
        
        # Verify agent was registered
        assert "TEST" in moderator._registered_agents
        assert moderator._registered_agents["TEST"] == "Test agent description"
        
        # Test registering moderator itself (should skip)
        handoffs_count = len(moderator.handoffs)  # Save current count
        mock_moderator = MagicMock()
        mock_moderator.name = "MODERATOR"
        moderator.register_agent(mock_moderator)
        assert len(moderator.handoffs) == handoffs_count  # Should not change

    def test_update_instructions(self):
        """Test updating the moderator instructions."""
        # Create moderator
        moderator = ModeratorAgent()
        original_instructions = moderator.instructions
        
        # Create agent descriptions
        agent_descriptions = {
            "SPECIALIST": "Specialist agent description",
            "EXPERT": "Expert agent description"
        }
        
        # Update instructions
        moderator.update_instructions(agent_descriptions)
        
        # Verify instructions were updated
        assert moderator.instructions != original_instructions
        assert "AVAILABLE SPECIALIST AGENTS:" in moderator.instructions
        assert "SPECIALIST: Specialist agent description" in moderator.instructions
        assert "EXPERT: Expert agent description" in moderator.instructions
        
        # Verify registered agents were updated
        assert moderator._registered_agents == agent_descriptions
        
        # Test updating again with additional agents
        more_descriptions = {
            "NEWAGENT": "New agent description"
        }
        moderator.update_instructions(more_descriptions)
        
        # Verify all agents are in the instructions
        assert "SPECIALIST: Specialist agent description" in moderator.instructions
        assert "EXPERT: Expert agent description" in moderator.instructions
        assert "NEWAGENT: New agent description" in moderator.instructions
        
        # Verify with no agents
        moderator = ModeratorAgent()
        moderator.update_instructions({})
        assert "No specialist agents available" in moderator.instructions

    def test_get_async_openai_client(self):
        """Test the get_async_openai_client method"""
        moderator = ModeratorAgent()
        client = moderator.get_async_openai_client()
        
        assert client is not None
        self.mock_openai.assert_called_once()
