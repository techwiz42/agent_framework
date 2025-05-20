import pytest
from unittest.mock import MagicMock, patch
import logging

from app.services.agents.agent_interface import AgentInterface, agent_interface


class TestAgentInterface:
    """Tests for the AgentInterface class."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create a fresh instance for each test
        self.interface = AgentInterface()
        
        # Create mock agents
        self.mock_agent1 = MagicMock()
        self.mock_agent1.name = "TestAgent1"
        self.mock_agent1.description = "Test agent 1 description"
        
        self.mock_agent2 = MagicMock()
        self.mock_agent2.name = "TestAgent2"
        # Set description to None to test default behavior
        self.mock_agent2.description = None
        
        # Test thread IDs
        self.thread_id1 = "thread-123"
        self.thread_id2 = "thread-456"

    def test_register_base_agent(self):
        """Test registering base agents."""
        # Register the first agent
        self.interface.register_base_agent("AGENT1", self.mock_agent1)
        
        # Verify agent was registered
        assert "AGENT1" in self.interface.base_agents
        assert self.interface.base_agents["AGENT1"] == self.mock_agent1
        
        # Verify description was stored
        assert "AGENT1" in self.interface.agent_descriptions
        assert self.interface.agent_descriptions["AGENT1"] == "Test agent 1 description"
        
        # Register second agent with no description
        self.interface.register_base_agent("AGENT2", self.mock_agent2)
        
        # Verify default description was used
        assert "AGENT2" in self.interface.agent_descriptions
        assert self.interface.agent_descriptions["AGENT2"] == "AGENT2 agent"
        
        # Test case normalization
        self.interface.register_base_agent("agent3", self.mock_agent1)
        assert "AGENT3" in self.interface.base_agents

    def test_setup_conversation(self):
        """Test setting up agents for a conversation."""
        # Register base agents
        self.interface.register_base_agent("AGENT1", self.mock_agent1)
        self.interface.register_base_agent("AGENT2", self.mock_agent2)
        
        # Set up conversation
        self.interface.setup_conversation(self.thread_id1, ["AGENT1", "AGENT2"])
        
        # Verify conversation agents were set up
        assert self.thread_id1 in self.interface.conversation_agents
        assert "AGENT1" in self.interface.conversation_agents[self.thread_id1]
        assert "AGENT2" in self.interface.conversation_agents[self.thread_id1]
        
        # Test with invalid agent type
        self.interface.setup_conversation(self.thread_id2, ["AGENT1", "NONEXISTENT"])
        
        # Should only have valid agent
        assert self.thread_id2 in self.interface.conversation_agents
        assert "AGENT1" in self.interface.conversation_agents[self.thread_id2]
        assert "NONEXISTENT" not in self.interface.conversation_agents[self.thread_id2]
        
        # Test with lowercase agent type (should be normalized)
        self.interface.setup_conversation(self.thread_id2, ["agent2"])
        assert "AGENT2" in self.interface.conversation_agents[self.thread_id2]

    def test_get_agent(self):
        """Test retrieving agents for a conversation."""
        # Register base agents
        self.interface.register_base_agent("AGENT1", self.mock_agent1)
        self.interface.register_base_agent("AGENT2", self.mock_agent2)
        
        # Set up conversation with one agent
        self.interface.setup_conversation(self.thread_id1, ["AGENT1"])
        
        # Get existing agent
        agent = self.interface.get_agent(self.thread_id1, "AGENT1")
        assert agent == self.mock_agent1
        
        # Get non-existent agent type
        agent = self.interface.get_agent(self.thread_id1, "NONEXISTENT")
        assert agent is None
        
        # Test auto-setup of available base agent
        agent = self.interface.get_agent(self.thread_id1, "AGENT2")
        assert agent == self.mock_agent2
        assert "AGENT2" in self.interface.conversation_agents[self.thread_id1]
        
        # Test with lowercase (should normalize)
        agent = self.interface.get_agent(self.thread_id1, "agent1")
        assert agent == self.mock_agent1
        
        # Test with non-existent thread - Should return None, not create a new conversation
        agent = self.interface.get_agent("nonexistent-thread", "NONEXISTENT")
        assert agent is None

    def test_get_agent_types(self):
        """Test retrieving available agent types."""
        # Register base agents
        self.interface.register_base_agent("AGENT1", self.mock_agent1)
        self.interface.register_base_agent("AGENT2", self.mock_agent2)
        
        # Get all base agent types
        types = self.interface.get_agent_types()
        assert sorted(types) == ["AGENT1", "AGENT2"]
        
        # Set up conversation with subset of agents
        self.interface.setup_conversation(self.thread_id1, ["AGENT1"])
        
        # Get thread-specific agent types
        types = self.interface.get_agent_types(self.thread_id1)
        assert types == ["AGENT1"]
        
        # Test with non-existent thread
        types = self.interface.get_agent_types("nonexistent-thread")
        assert sorted(types) == ["AGENT1", "AGENT2"]  # Should return base agents

    def test_get_agent_descriptions(self):
        """Test retrieving agent descriptions."""
        # Register base agents
        self.interface.register_base_agent("AGENT1", self.mock_agent1)
        self.interface.register_base_agent("AGENT2", self.mock_agent2)
        
        # Get descriptions
        descriptions = self.interface.get_agent_descriptions()
        assert "AGENT1" in descriptions
        assert descriptions["AGENT1"] == "Test agent 1 description"
        assert "AGENT2" in descriptions
        assert descriptions["AGENT2"] == "AGENT2 agent"  # Default description

    def test_cleanup_conversation(self):
        """Test cleaning up conversation resources."""
        # Register base agents
        self.interface.register_base_agent("AGENT1", self.mock_agent1)
        self.interface.register_base_agent("AGENT2", self.mock_agent2)
        
        # Set up conversations
        self.interface.setup_conversation(self.thread_id1, ["AGENT1"])
        self.interface.setup_conversation(self.thread_id2, ["AGENT2"])
        
        # Verify both conversations exist
        assert self.thread_id1 in self.interface.conversation_agents
        assert self.thread_id2 in self.interface.conversation_agents
        
        # Clean up one conversation
        self.interface.cleanup_conversation(self.thread_id1)
        
        # Verify it was removed
        assert self.thread_id1 not in self.interface.conversation_agents
        assert self.thread_id2 in self.interface.conversation_agents
        
        # Test cleanup of non-existent thread (should not error)
        self.interface.cleanup_conversation("nonexistent-thread")

    def test_singleton_instance(self):
        """Test that the singleton instance works correctly."""
        # Modify the singleton instance
        agent_interface.register_base_agent("TEST_AGENT", self.mock_agent1)
        
        # Create a new reference
        interface_ref = agent_interface
        
        # Verify both references point to the same object
        assert interface_ref.base_agents == agent_interface.base_agents
        assert "TEST_AGENT" in interface_ref.base_agents
