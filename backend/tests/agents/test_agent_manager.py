import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json

from app.services.agents.agent_manager import AgentManager
from app.services.agents.common_context import CommonAgentContext


class TestAgentManager:
    """Tests for the AgentManager class."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Patch agent_interface to avoid actual agent discovery
        self.agent_interface_patch = patch('app.services.agents.agent_manager.agent_interface')
        self.mock_agent_interface = self.agent_interface_patch.start()
        
        # Patch collaboration_manager
        self.collab_manager_patch = patch('app.services.agents.agent_manager.collaboration_manager')
        self.mock_collab_manager = self.collab_manager_patch.start()
        
        # Patch buffer_manager
        self.buffer_manager_patch = patch('app.services.agents.agent_manager.buffer_manager')
        self.mock_buffer_manager = self.buffer_manager_patch.start()
        
        # Patch rag_query_service
        self.rag_service_patch = patch('app.services.agents.agent_manager.rag_query_service')
        self.mock_rag_service = self.rag_service_patch.start()
        self.mock_rag_service.query_knowledge = AsyncMock()
        
        # Create mocked agents
        self.mock_moderator = MagicMock()
        self.mock_specialist = MagicMock()
        
        # Set up agent interface mock returns
        self.mock_agent_interface.get_agent_types.return_value = ["MODERATOR", "SPECIALIST"]
        self.mock_agent_interface.get_agent.side_effect = self._mock_get_agent
        self.mock_agent_interface.get_agent_descriptions.return_value = {
            "MODERATOR": "Moderator agent description",
            "SPECIALIST": "Specialist agent description"
        }
        
        # Create the agent manager
        with patch('app.services.agents.agent_manager.AgentManager._initialize_agents'):
            self.agent_manager = AgentManager()
            
    def teardown_method(self):
        """Clean up after each test."""
        self.agent_interface_patch.stop()
        self.collab_manager_patch.stop()
        self.buffer_manager_patch.stop()
        self.rag_service_patch.stop()
    
    def _mock_get_agent(self, thread_id, agent_type):
        """Mock for agent_interface.get_agent."""
        if agent_type == "MODERATOR":
            return self.mock_moderator
        elif agent_type == "SPECIALIST":
            return self.mock_specialist
        return None

    def test_get_agent_descriptions(self):
        """Test getting agent descriptions."""
        descriptions = self.agent_manager.get_agent_descriptions()
        
        # Should delegate to agent_interface
        self.mock_agent_interface.get_agent_descriptions.assert_called_once()
        assert descriptions == {
            "MODERATOR": "Moderator agent description",
            "SPECIALIST": "Specialist agent description"
        }

    def test_get_available_agents(self):
        """Test getting available agent types."""
        agents = self.agent_manager.get_available_agents()
        
        # Should delegate to agent_interface
        self.mock_agent_interface.get_agent_types.assert_called_once()
        assert agents == ["MODERATOR", "SPECIALIST"]

    def test_resolve_agent_name(self):
        """Test agent name resolution."""
        available_agents = ["MODERATOR", "SPECIALIST", "EXPERT"]
        
        # Exact match
        resolved = self.agent_manager._resolve_agent_name("SPECIALIST", available_agents)
        assert resolved == "SPECIALIST"
        
        # Case-insensitive match
        resolved = self.agent_manager._resolve_agent_name("moderator", available_agents)
        assert resolved == "MODERATOR"
        
        # Prefix match
        resolved = self.agent_manager._resolve_agent_name("SPEC", available_agents)
        assert resolved == "SPECIALIST"
        
        # Substring match
        resolved = self.agent_manager._resolve_agent_name("PERT", available_agents)
        assert resolved == "EXPERT"
        
        # No match, should default to MODERATOR
        resolved = self.agent_manager._resolve_agent_name("NONEXISTENT", available_agents)
        assert resolved == "MODERATOR"
        
        # No match, no MODERATOR, should use first agent
        resolved = self.agent_manager._resolve_agent_name("NONEXISTENT", ["SPECIALIST", "EXPERT"])
        assert resolved == "SPECIALIST"
        
        # Empty available agents (should not happen but test anyway)
        resolved = self.agent_manager._resolve_agent_name("ANYTHING", [])
        assert resolved == "ANYTHING"  # Returns original as last resort

    @pytest.mark.asyncio
    async def test_prepare_context(self):
        """Test context preparation."""
        # Setup
        thread_id = "thread-123"
        owner_id = "owner-456"
        message = "Test message"
        db = MagicMock()
        
        # Configure mocks
        self.mock_buffer_manager.conversation_buffer.format_context.return_value = "buffer context"
        self.mock_rag_service.query_knowledge.return_value = {
            "documents": ["doc1", "doc2"],
            "metadatas": [{"source": "source1"}, {"source": "source2"}]
        }
        
        # Call method
        context = await self.agent_manager._prepare_context(message, thread_id, owner_id, db)
        
        # Verify context is created correctly
        assert isinstance(context, CommonAgentContext)
        assert context.thread_id == thread_id
        assert context.owner_id == owner_id
        assert context.db == db
        assert context.buffer_context == "buffer context"
        assert context.rag_results is not None
        assert "documents" in context.rag_results
        
        # Verify agent types and descriptions were added
        assert hasattr(context, "available_agents")
        assert context.available_agents == {
            "MODERATOR": "Moderator agent description",
            "SPECIALIST": "Specialist agent description"
        }

    @pytest.mark.asyncio
    async def test_select_agent(self):
        """Test agent selection."""
        # Setup
        thread_id = "thread-123"
        message = "Test message"
        context = CommonAgentContext(thread_id=thread_id)
        context.available_agents = {
            "MODERATOR": "Moderator agent description",
            "SPECIALIST": "Specialist agent description"
        }
        
        # Configure mock moderator with select_agent tool
        mock_select_tool = MagicMock()
        mock_select_tool.name = "select_agent"
        mock_select_tool.on_invoke_tool = AsyncMock(return_value=json.dumps({
            "primary_agent": "SPECIALIST",
            "supporting_agents": ["MODERATOR"]
        }))
        self.mock_moderator.tools = [mock_select_tool]
        
        # Test with explicit mention
        result = await self.agent_manager._select_agent(message, context, thread_id, mention="SPECIALIST")
        assert result == "SPECIALIST"
        assert context.selected_agent == "SPECIALIST"
        
        # Test with no mention (should use moderator's select_agent tool)
        result = await self.agent_manager._select_agent(message, context, thread_id)
        assert result == "SPECIALIST"
        assert context.selected_agent == "SPECIALIST"
        assert context.collaborators == ["MODERATOR"]
        assert context.is_agent_selection
        
        # Verify tool was called with correct args
        mock_select_tool.on_invoke_tool.assert_called_with(
            context, 
            json.dumps({
                "query": message,
                "available_agents": "MODERATOR,SPECIALIST"
            })
        )

    @pytest.mark.asyncio
    async def test_handle_collaboration(self):
        """Test collaboration handling."""
        # Setup
        thread_id = "thread-123"
        message = "Test message"
        context = CommonAgentContext(thread_id=thread_id)
        primary_agent_type = "SPECIALIST"
        collaborators = ["MODERATOR"]
        response_callback = AsyncMock()
        
        # Configure mock collaboration manager
        self.mock_collab_manager.initiate_collaboration = AsyncMock(return_value="collab-123")
        self.mock_collab_manager.get_collaboration_result = AsyncMock(return_value="Collaborative response")
        
        # Call method
        response = await self.agent_manager._handle_collaboration(
            message, thread_id, primary_agent_type, collaborators, context, response_callback
        )
        
        # Verify collaboration was initiated correctly
        self.mock_collab_manager.initiate_collaboration.assert_called_with(
            query=message,
            primary_agent_name=primary_agent_type,
            available_agents=self.mock_agent_interface.get_agent_types.return_value,
            collaborating_agents=collaborators,
            thread_id=thread_id,
            streaming_callback=response_callback
        )
        
        # Verify result was fetched and returned
        self.mock_collab_manager.get_collaboration_result.assert_called_with("collab-123")
        assert response == "Collaborative response"
        
        # Test with empty collaborators
        response = await self.agent_manager._handle_collaboration(
            message, thread_id, primary_agent_type, [], context, response_callback
        )
        # Should fall back to single agent
        assert response is not None  # Result from Runner.run
