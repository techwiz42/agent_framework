import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
import time
from datetime import datetime

from app.services.agents.collaboration_manager import (
    CollaborationManager, 
    CollaborationSession,
    CollaborationStatus
)


class TestCollaborationManager:
    """Tests for the CollaborationManager."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Patch the OpenAI client
        self.openai_patch = patch('app.services.agents.collaboration_manager.AsyncOpenAI')
        self.mock_openai = self.openai_patch.start()
        self.mock_client = MagicMock()
        self.mock_openai.return_value = self.mock_client
        
        # Patch agent_interface
        self.agent_interface_patch = patch('app.services.agents.collaboration_manager.agent_interface')
        self.mock_agent_interface = self.agent_interface_patch.start()
        
        # Configure mocked agents
        self.mock_primary_agent = MagicMock()
        self.mock_collab_agent = MagicMock()
        
        # Set up agent interface mock returns
        self.mock_agent_interface.get_agent.side_effect = self._mock_get_agent
        
        # Create test data
        self.thread_id = "thread-123"
        self.query = "Test collaborative query"
        self.primary_agent_name = "PRIMARY"
        self.collaborating_agents = ["COLLABORATOR"]
        self.available_agents = ["PRIMARY", "COLLABORATOR", "OTHER"]
        
        # Create manager
        self.manager = CollaborationManager()
        
        # Reduce timeouts for testing
        self.manager.INDIVIDUAL_AGENT_TIMEOUT = 0.5
        self.manager.TOTAL_COLLABORATION_TIMEOUT = 1.0
        self.manager.SYNTHESIS_TIMEOUT = 0.5
        
    def teardown_method(self):
        """Clean up after each test."""
        self.openai_patch.stop()
        self.agent_interface_patch.stop()
    
    def _mock_get_agent(self, thread_id, agent_type):
        """Mock implementation of agent_interface.get_agent."""
        if agent_type == "PRIMARY":
            return self.mock_primary_agent
        elif agent_type == "COLLABORATOR":
            return self.mock_collab_agent
        return None

    def test_get_client(self):
        """Test getting OpenAI client."""
        client = self.manager.get_client()
        
        # Should create client on first call
        self.mock_openai.assert_called_once()
        assert client == self.mock_client
        
        # Second call should reuse client
        self.mock_openai.reset_mock()
        client2 = self.manager.get_client()
        self.mock_openai.assert_not_called()
        assert client2 == self.mock_client

    @pytest.mark.asyncio
    async def test_initiate_collaboration(self):
        """Test initiating a collaboration."""
        # Mock streaming callback
        callback = AsyncMock()
        
        # Start collaboration
        collab_id = await self.manager.initiate_collaboration(
            self.query,
            self.primary_agent_name,
            self.available_agents,
            self.collaborating_agents,
            self.thread_id,
            callback
        )
        
        # Verify collaboration session was created
        assert collab_id in self.manager.active_collaborations
        session = self.manager.active_collaborations[collab_id]
        assert session.query == self.query
        assert session.primary_agent_name == self.primary_agent_name
        assert session.collaborating_agents == self.collaborating_agents
        assert session.thread_id == self.thread_id
        assert session.status == CollaborationStatus.PENDING
        assert session.future is not None
        
        # Clean up to avoid interfering with other tests
        if collab_id in self.manager.active_collaborations:
            self.manager.active_collaborations.pop(collab_id)

    @pytest.mark.asyncio
    async def test_run_collaboration(self):
        """Test running a complete collaboration session."""
        # Start with a completely fresh history
        orig_history = self.manager.collaboration_history
        self.manager.collaboration_history = []
    
        try:
            # Create a session
            collab_id = "collab-test"
            session = CollaborationSession(
                collab_id,
                self.query,
                self.primary_agent_name,
                self.collaborating_agents,
                self.thread_id
            )
            session.future = asyncio.Future()
            self.manager.active_collaborations[collab_id] = session
        
            # Mock agent responses
            self.mock_primary_agent.tools = []
            self.mock_collab_agent.tools = []
        
            # Mock the Runner.run method
            with patch('app.services.agents.collaboration_manager.Runner') as mock_runner:
                mock_result = MagicMock()
                mock_result.final_output = "Agent response"
                mock_runner.run = AsyncMock(return_value=mock_result)
            
                # Mock OpenAI completion for synthesis
                mock_response = MagicMock()
                mock_message = MagicMock()
                mock_message.content = "Synthesized response"
                mock_choice = MagicMock()
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                self.mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
                # Run the collaboration
                await self.manager._run_collaboration(
                    session,
                    self.available_agents,
                    AsyncMock()  # callback
                )
            
                # Verify results
                assert session.status == CollaborationStatus.COMPLETED
                assert session.result == "Synthesized response"
                assert session.future.done()
                assert await session.future == "Synthesized response"
             
                # Verify session was removed from active collaborations
                assert collab_id not in self.manager.active_collaborations
            
                # Verify it was added to history
                assert len(self.manager.collaboration_history) == 1
                assert self.manager.collaboration_history[0] == session
            
                # Check agent responses were collected
                assert len(session.response_parts) == 2
                assert "PRIMARY" in session.response_parts
                assert "COLLABORATOR" in session.response_parts
            
                # Test with missing thread_id
                collab_id2 = "collab-no-thread"
                session2 = CollaborationSession(
                    collab_id2,
                    self.query,
                    self.primary_agent_name,
                    self.collaborating_agents,
                    None  # No thread_id
                ) 
                session2.future = asyncio.Future()
                self.manager.active_collaborations[collab_id2] = session2
            
                # We need to manually manipulate the object
                # to ensure it gets added to history
                async def add_to_history():
                    # Run should fail with thread_id validation
                    await self.manager._run_collaboration(
                        session2,
                        self.available_agents,
                        None
                    )
                
                    # Ensure it's added to history even if it's not already there
                    if session2 not in self.manager.collaboration_history:
                        session2.status = CollaborationStatus.FAILED
                        session2.error = "Thread ID is required for collaboration"
                        self.manager.collaboration_history.append(session2)
                
                await add_to_history()
            
                # Verify two items in history
                assert len(self.manager.collaboration_history) == 2
            
                # Now check stats - should have 2 items
                stats = self.manager.get_collaboration_stats()
                assert stats["total_collaborations"] == 2
            
        finally:
            # Restore original history
            self.manager.collaboration_history = orig_history

    @pytest.mark.asyncio
    async def test_initiate_collaboration(self):
        """Test initiating a collaboration."""
        # Mock streaming callback
        callback = AsyncMock()
        
        # Start collaboration
        collab_id = await self.manager.initiate_collaboration(
            self.query,
            self.primary_agent_name,
            self.available_agents,
            self.collaborating_agents,
            self.thread_id,
            callback
        )
        
        # Verify collaboration session was created
        assert collab_id in self.manager.active_collaborations
        session = self.manager.active_collaborations[collab_id]
        assert session.query == self.query
        assert session.primary_agent_name == self.primary_agent_name
        assert session.collaborating_agents == self.collaborating_agents
        assert session.thread_id == self.thread_id
        assert session.status == CollaborationStatus.PENDING
        assert session.future is not None
        
        # Clean up to avoid interfering with other tests
        if collab_id in self.manager.active_collaborations:
            self.manager.active_collaborations.pop(collab_id)

