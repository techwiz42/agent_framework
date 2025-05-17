from typing import Any, Callable, List, Optional, Union, Type, Dict, TypeVar, Generic
import inspect
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# For now, we'll define some placeholders for the agents SDK
# In a full implementation, these would be imported from a proper SDK
class AgentHooks:
    """Base agent hooks class for handling agent events."""
    
    async def init_context(self, context: Any) -> None:
        """Initialize the context for an agent."""
        pass
    
    async def on_handoff(self, context: Any, agent: Any, source: Any) -> None:
        """Called when control is handed to another agent."""
        pass

class ModelSettings:
    """Settings for the agent model."""
    
    def __init__(
        self,
        tool_choice: Optional[str] = None,
        parallel_tool_calls: bool = True,
        temperature: float = 0.7,
        top_p: float = 1.0,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        max_tokens: Optional[int] = None,
        truncation: Optional[bool] = None
    ):
        self.tool_choice = tool_choice
        self.parallel_tool_calls = parallel_tool_calls
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.max_tokens = max_tokens
        self.truncation = truncation

class Tool:
    """Base tool class for agent tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

class FunctionTool(Tool):
    """Tool that wraps a function."""
    
    def __init__(
        self,
        name: str,
        description: str,
        params_json_schema: Dict[str, Any],
        on_invoke_tool: Callable
    ):
        super().__init__(name, description)
        self.params_json_schema = params_json_schema
        self.on_invoke_tool = on_invoke_tool
        self.schema = {
            "name": name,
            "description": description,
            "parameters": params_json_schema
        }

class RunContextWrapper:
    """Wrapper for the run context."""
    
    def __init__(self, context: Any):
        self.context = context

# Make BaseAgent generic over the context type
T = TypeVar('T')

class Agent(Generic[T]):
    """Base Agent class that will be extended."""
    
    def __init__(
        self,
        name: str,
        model: str,
        instructions: Union[str, Callable[[Any, Any], str]],
        tools: List[Tool] = None,
        model_settings: ModelSettings = None,
        hooks: AgentHooks = None
    ):
        self.name = name
        self.model = model
        self.instructions = instructions
        self.tools = tools or []
        self.model_settings = model_settings or ModelSettings()
        self.hooks = hooks
        self.description = ""

class BaseAgentHooks(AgentHooks):
    """Custom hooks for all agents to ensure context is properly initialized."""
    
    async def init_context(self, context: RunContextWrapper[Any]) -> None:
        """
        Initialize context for agents, ensuring conversation history is available.
        
        Args:
            context: The run context wrapper containing conversation data
        """
        # Call parent implementation
        await super().init_context(context)
        
        # Make sure the context has all expected attributes
        if hasattr(context, 'context'):
            agent_ctx = context.context
            logger.info(f"[CONTEXT_DEBUG] Initialized context, has buffer_context: {hasattr(agent_ctx, 'buffer_context')}")
            if hasattr(agent_ctx, 'buffer_context') and agent_ctx.buffer_context:
                logger.info(f"[CONTEXT_DEBUG] Buffer context length: {len(agent_ctx.buffer_context)} chars")
        else:
            logger.warning("[CONTEXT_DEBUG] Context initialized but no 'context' attribute found")

class BaseAgent(Agent[T]):
    """
    BaseAgent is a wrapper around the Agent SDK, providing compatibility with
    various LLM providers while maintaining a consistent interface.
    """
    
    def __init__(
        self,
        name: str = "Agent",
        model: str = settings.DEFAULT_AGENT_MODEL,
        instructions: Union[str, Callable[[RunContextWrapper[T], "Agent[T]"], str]] = "You are a helpful agent.",
        functions: List[Any] = None,
        tool_choice: Optional[str] = None,
        parallel_tool_calls: bool = True,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize a BaseAgent with the given parameters.
        
        Args:
            name: The name of the agent.
            model: The model to use for this agent.
            instructions: The system prompt for the agent.
            functions: A list of functions to be used as tools by the agent.
            tool_choice: The tool choice strategy to use.
            parallel_tool_calls: Whether to allow the agent to call multiple tools in parallel.
            max_tokens: Maximum number of tokens to generate in the response.
            **kwargs: Additional arguments to pass to the Agent constructor.
        """
        # Convert functions to tools if provided
        tools = []
        if functions:
            tools = self._convert_functions_to_tools(functions)
        
        # Extract 'tools' from kwargs if it exists to avoid duplicate parameters
        if 'tools' in kwargs:
            del kwargs['tools']
            
        # Initialize the parent Agent class
        model_settings_params = {
            "tool_choice": tool_choice,
            "parallel_tool_calls": parallel_tool_calls
        }
        
        # Add max_tokens to ModelSettings if provided
        if max_tokens is not None:
            model_settings_params["max_tokens"] = max_tokens
        
        # If instructions is a string, we wrap it in a function that will include conversation history
        if isinstance(instructions, str):
            base_instructions = instructions
            instructions = lambda ctx, agent: self._build_instructions_with_context(ctx, base_instructions)
            
        super().__init__(
            name=name,
            model=model,
            instructions=instructions,
            tools=tools,
            model_settings=ModelSettings(**model_settings_params),
            **kwargs
        )
        
        # Store the original functions for compatibility
        self._functions = functions or []
        
        # Add standard hooks if not provided
        self.hooks = kwargs.get('hooks', None)
        if not self.hooks:
            self.hooks = BaseAgentHooks()
    
    def _build_instructions_with_context(self, ctx, base_instructions):
        """
        Build agent instructions with conversation context included
        
        Args:
            ctx: The RunContextWrapper with context data
            base_instructions: The base instructions string
            
        Returns:
            Combined instructions with conversation history
        """
        # Add conversation history if available
        if hasattr(ctx, 'context') and hasattr(ctx.context, 'buffer_context') and ctx.context.buffer_context:
            logger.info(f"[CONTEXT_DEBUG] Including conversation context in instructions for {self.name}. Context length: {len(ctx.context.buffer_context)} chars")
            return f"{base_instructions}\n\n## Conversation History:\n{ctx.context.buffer_context}"
        else:
            if not hasattr(ctx, 'context'):
                logger.warning(f"[CONTEXT_DEBUG] No 'context' attribute found in ctx for {self.name}")
            elif not hasattr(ctx.context, 'buffer_context'):
                logger.warning(f"[CONTEXT_DEBUG] No 'buffer_context' attribute found in ctx.context for {self.name}")
            elif not ctx.context.buffer_context:
                logger.warning(f"[CONTEXT_DEBUG] Empty buffer_context for {self.name}")
            return base_instructions
    
    def _convert_functions_to_tools(self, functions: List[Any]) -> List[Tool]:
        """
        Convert a list of functions to a list of tools, validating schemas along the way.
        
        Args:
            functions: List of functions to convert to tools.
            
        Returns:
            List of Tool objects.
        """
        tools = []
        for func in functions:
            if isinstance(func, Tool):
                tools.append(func)
            else:
                try:
                    # Check if the function is already wrapped in a function_tool decorator
                    if hasattr(func, 'schema'):  # Check for the schema attribute directly
                        # The function already has a schema, this is likely an SDK function_tool
                        tools.append(func)
                    else:
                        # Create a FunctionTool from the function
                        # In a real implementation, this would use proper function_tool decorator
                        tool = self._create_function_tool(func)
                        tools.append(tool)
                except Exception as e:
                    logger.error(f"Error converting function {getattr(func, '__name__', 'unknown')} to tool: {str(e)}")
                    tools.append(self._create_sanitized_function_tool(func))
        return tools
    
    def _create_function_tool(self, func: Callable) -> FunctionTool:
        """
        Create a FunctionTool from a function.
        
        Args:
            func: The function to create a tool from.
            
        Returns:
            A FunctionTool.
        """
        func_name = getattr(func, "__name__", "unknown_function")
        
        # Get function signature to derive parameters
        sig = inspect.signature(func)
        params = sig.parameters
        
        # Create parameters schema
        properties = {}
        required = []
        
        for name, param in params.items():
            properties[name] = {
                "type": "string",  # Default to string as a safe type
                "description": f"Parameter {name} for function {func_name}"
            }
            
            # If parameter has no default value, mark it as required
            if param.default == inspect.Parameter.empty:
                required.append(name)
        
        params_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        # Create the tool
        return FunctionTool(
            name=func_name,
            description=getattr(func, "__doc__", f"Function {func_name}"),
            params_json_schema=params_schema,
            on_invoke_tool=lambda ctx, args: func(**args)
        )
    
    def _create_sanitized_function_tool(self, func: Callable) -> FunctionTool:
        """
        Create a sanitized function tool that will pass schema validation.
        
        Args:
            func: The function to create a tool from.
            
        Returns:
            A valid FunctionTool.
        """
        func_name = getattr(func, "__name__", "unknown_function")
        
        # Get function signature to derive parameters
        try:
            sig = inspect.signature(func)
            params = sig.parameters
            
            # Create a valid schema based on the function's signature
            properties = {}
            required = []
            
            for name, param in params.items():
                properties[name] = {
                    "type": "string",  # Default to string as a safe type
                    "description": f"Parameter {name} for function {func_name}"
                }
                
                # If parameter has no default value, mark it as required
                if param.default == inspect.Parameter.empty:
                    required.append(name)
            
            schema = {
                "type": "object",
                "properties": properties,
                "required": required
            }
            
            # Create a wrapper function that logs calls and returns an error message
            def safe_wrapper(*args, **kwargs):
                logger.warning(f"Called sanitized function {func_name}")
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = f"Error in function {func_name}: {str(e)}"
                    logger.error(error_msg)
                    return error_msg
            
            # Create the tool
            return FunctionTool(
                name=func_name,
                description=getattr(func, "__doc__", f"Function {func_name}"),
                params_json_schema=schema,
                on_invoke_tool=lambda ctx, args: safe_wrapper(**args)
            )
        
        except Exception as e:
            logger.error(f"Error creating sanitized function tool for {func_name}: {str(e)}")
            
            # Create a minimal valid schema as fallback
            schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            # Create a no-op function
            def no_op_function(*args, **kwargs):
                return f"Error: Function {func_name} is unavailable due to schema validation issues."
            
            # Return a no-op function tool
            return FunctionTool(
                name=func_name,
                description=f"Function {func_name} (sanitized)",
                params_json_schema=schema,
                on_invoke_tool=lambda ctx, args: no_op_function()
            )
    
    @property
    def functions(self) -> List[Any]:
        """
        Get the list of functions associated with this agent.
        
        Returns:
            The list of functions that can be called by this agent.
        """
        return self._functions
    
    @functions.setter
    def functions(self, value: List[Any]) -> None:
        """
        Set the list of functions for this agent and update the tools accordingly.
        
        Args:
            value: The new list of functions.
        """
        self._functions = value
        
        # Update the tools based on the new functions
        self.tools = self._convert_functions_to_tools(value)
    
    def add_function(self, func: Any) -> None:
        """
        Add a function to the agent's list of functions and tools.
        
        Args:
            func: The function to add.
        """
        self._functions.append(func)
        
        # Add the function as a tool
        if isinstance(func, Tool):
            self.tools.append(func)
        else:
            try:
                tool = self._create_function_tool(func)
                self.tools.append(tool)
            except Exception as e:
                logger.error(f"Error adding function {getattr(func, '__name__', 'unknown')}: {str(e)}")
                self.tools.append(self._create_sanitized_function_tool(func))
    
    def remove_function(self, func_name: str) -> None:
        """
        Remove a function from the agent's list of functions and tools.
        
        Args:
            func_name: The name of the function to remove.
        """
        # Remove from functions list
        self._functions = [f for f in self._functions if 
                          (hasattr(f, '__name__') and f.__name__ != func_name) or
                          (hasattr(f, 'name') and f.name != func_name)]
        
        # Remove from tools list
        self.tools = [t for t in self.tools if t.name != func_name]
    
    async def execute(self, context: RunContextWrapper[T], message: str) -> str:
        """
        Execute the agent with the given message and context.
        
        Args:
            context: The context wrapper for this execution.
            message: The user message to respond to.
            
        Returns:
            The agent's response.
        """
        # This is a simplified placeholder - in a real implementation, 
        # this would call the appropriate LLM API
        logger.info(f"Executing agent {self.name} with message: {message[:50]}...")
        
        # Initialize the context if hooks are provided
        if self.hooks:
            await self.hooks.init_context(context)
        
        # For now, return a placeholder response
        return f"Response from {self.name} agent (This is a placeholder)"