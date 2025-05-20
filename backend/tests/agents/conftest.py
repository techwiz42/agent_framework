import pytest
from unittest.mock import MagicMock, patch
import asyncio
import os
import sys

# Add app directory to path if needed for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.name = "MockAgent"
    agent.description = "Mock agent for testing"
    agent.tools = []
    agent.input_guardrails = []
    agent.output_guardrails = []
    agent.handoffs = []
    return agent


@pytest.fixture
def mock_moderator_agent():
    """Create a mock moderator agent for testing."""
    agent = MagicMock()
    agent.name = "ModeratorAgent"
    agent.description = "Mock moderator agent for testing"
    
    # Create select_agent tool
    select_tool = MagicMock()
    select_tool.name = "select_agent"
    
    # Create collaboration tool
    collab_tool = MagicMock()
    collab_tool.name = "check_collaboration_need"
    
    # Create synthesis tool
    synth_tool = MagicMock()
    synth_tool.name = "synthesize_collaborative_responses"
    
    agent.tools = [select_tool, collab_tool, synth_tool]
    agent.input_guardrails = []
    agent.output_guardrails = []
    agent.handoffs = []
    return agent


@pytest.fixture
def mock_context():
    """Create a mock context for testing."""
    context = MagicMock()
    context.thread_id = "test-thread-123"
    context.owner_id = "test-owner-456"
    context.db = None
    context.buffer_context = "Buffer context"
    context.rag_results = {
        "documents": ["doc1", "doc2"],
        "metadatas": [{"source": "source1"}, {"source": "source2"}]
    }
    context.available_agents = {
        "MODERATOR": "Moderator agent",
        "SPECIALIST": "Specialist agent" 
    }
    context.selected_agent = None
    context.collaborators = []
    context.is_agent_selection = False
    return context


@pytest.fixture
def patch_openai():
    """Patch AsyncOpenAI for testing."""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock chat completions
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"primary_agent": "SPECIALIST", "supporting_agents": []}'
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = MagicMock(return_value=mock_response)
        
        yield mock_client


@pytest.fixture
def patch_deps():
    """Patch common dependencies for agent system testing."""
    patches = []
    
    # Patch agent_interface
    agent_interface_patch = patch('app.services.agents.agent_manager.agent_interface')
    mock_agent_interface = agent_interface_patch.start()
    patches.append(agent_interface_patch)
    
    # Patch buffer_manager
    buffer_manager_patch = patch('app.services.agents.agent_manager.buffer_manager')
    mock_buffer_manager = buffer_manager_patch.start()
    patches.append(buffer_manager_patch)
    
    # Patch rag_query_service
    rag_service_patch = patch('app.services.agents.agent_manager.rag_query_service')
    mock_rag_service = rag_service_patch.start()
    patches.append(rag_service_patch)
    
    # Patch collaboration_manager
    collab_manager_patch = patch('app.services.agents.agent_manager.collaboration_manager')
    mock_collab_manager = collab_manager_patch.start()
    patches.append(collab_manager_patch)
    
    # Patch Runner
    runner_patch = patch('app.services.agents.agent_manager.Runner')
    mock_runner = runner_patch.start()
    patches.append(runner_patch)
    
    # Create response structure
    mock_result = MagicMock()
    mock_result.final_output = "Test response"
    mock_runner.run = MagicMock(return_value=mock_result)
    
    yield {
        'agent_interface': mock_agent_interface,
        'buffer_manager': mock_buffer_manager,
        'rag_service': mock_rag_service,
        'collab_manager': mock_collab_manager,
        'runner': mock_runner
    }
    
    # Stop all patches
    for p in patches:
        p.stop()


@pytest.fixture
def event_loop():
    """Create an event loop for testing."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
