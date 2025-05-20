# Resolving Function Tool Schema Errors

## Problem Overview

When using the OpenAI function calling API, agent tools require JSON schemas that adhere to strict validation rules. The error we're encountering:

```
Invalid schema for function 'calculate': In context=('properties', 'context'), schema must have a 'type' key.
```

This happens because:

1. The `function_tool` decorator auto-generates schemas from function signatures
2. For parameters with complex type annotations (like `RunContextWrapper`), the schema generation doesn't always include a required `type` field
3. The OpenAI API rejects these schemas during validation

This primarily affects five agents that use the calculator tool:
- Accounting Agent
- Business Agent
- Finance Agent
- Data Analysis Agent
- Business Intelligence Agent

## Root Cause Analysis

The schema validation error occurs because the generated schema for the calculator tool's `context` parameter is missing a required `type` property. 

Here's the relevant parts of the generated schema:

```json
{
  "parameters": {
    "properties": {
      "context": {
        "description": "The run context wrapper.",
        // Missing "type": "object" here
      }
    }
  }
}
```

The OpenAI API requires that every property in a function schema has a `type` field, which can be one of: `object`, `array`, `string`, `number`, `boolean`, or `null`.

The function signature using the optional `RunContextWrapper` type doesn't generate a proper schema because:

1. The `function_tool` decorator uses reflection to analyze the function
2. Complex type annotations with generics or optional wrappers don't translate cleanly to JSON Schema
3. No post-processing validates and fixes the generated schema

## Solution Approaches

### Approach 1: Direct Schema Patching

We've implemented a solution in `manual_schema_fix.py` that:

1. Traverses all agent tools
2. Checks for missing schema properties
3. Adds the required `type` fields and other missing properties
4. Validates that the schemas can be properly serialized

This approach modifies the schema objects in memory, providing an immediate fix without changing code structure.

### Approach 2: Modify the Calculator Tool Implementation

In `agent_calculator_tool.py`, we:

1. Include explicit schema fixes in the `get_calculator_tool()` and `get_interpreter_tool()` functions
2. For any tool with a schema, ensure the `context` property has:
   - `"type": "object"`
   - `"additionalProperties": false`
   - `"properties": {}`
3. Apply similar fixes to other properties like `values` and `calculation_results`

### Approach 3: Long-term Refactoring

For a more sustainable solution:

1. **Create standalone calculator functions** without `RunContextWrapper` parameters:
   ```python
   def calculate(
       operation_type: str,
       operation: str,
       expression: Optional[str] = None,
       values: Optional[List[Union[int, float]]] = None
   ) -> Dict[str, Any]:
       """Perform calculations."""
       # Implementation without context
       ...
   ```

2. **Define explicit schemas** instead of relying on auto-generation:
   ```python
   def get_calculator_schema():
       return {
           "name": "calculate",
           "description": "Perform calculations",
           "parameters": {
               "type": "object",
               "properties": {
                   "operation_type": {
                       "type": "string",
                       "description": "Type of calculation",
                       "enum": ["arithmetic", "statistical", "financial", "health", "business"]
                   },
                   "operation": {
                       "type": "string",
                       "description": "The operation to perform"
                   },
                   "expression": {
                       "type": "string",
                       "description": "A mathematical expression to evaluate"
                   },
                   "values": {
                       "type": "array",
                       "items": {"type": "number"},
                       "description": "List of values for calculation"
                   }
               },
               "required": ["operation_type", "operation"]
           }
       }
   ```

3. **Create a schema validation utility** that checks tools before registration

## Implementation Steps

### Immediate Fix

1. Run `manual_schema_fix.py` to fix all agent tool schemas in memory
2. Test with `run_accounting_test.py` to verify the calculator tool works properly

### Medium-term Solution

1. Update `agent_calculator_tool.py` to include explicit schema fixes
2. Add schema validation in the `function_tool` usage pipeline
3. Create a pre-processing step that ensures all schemas have required fields

### Long-term Refactoring

1. Refactor calculator tools to avoid problematic parameters
2. Implement explicit schema definitions with proper validation
3. Create a comprehensive testing framework for tool schemas

## Testing and Verification

To verify the fix:

1. Run the schema fixer: `python manual_schema_fix.py`
2. Test an accounting agent: `python run_accounting_test.py`
3. Test the agent manager's process_conversation method with:
   ```python
   result = await agent_manager.process_conversation(
       message="Can you calculate the sum of 1, 2, 3, 4, and 5?",
       conversation_agents=["ACCOUNTING"],
       agents_config={},
       mention="ACCOUNTING"
   )
   ```

## Prevention Strategies

To prevent similar issues in the future:

1. **Schema Validation Pipeline**: Add a validation step for all tool schemas
   ```python
   def validate_tool_schema(schema):
       # Check required fields, types, etc.
       ...
       return fixed_schema
   ```

2. **Tool Registration Wrapper**: Create a wrapper for tool registration that applies fixes
   ```python
   def register_tool(agent, function):
       tool = function_tool(function)
       # Apply schema fixes
       tool.schema = validate_tool_schema(tool.schema)
       agent.add_function(tool)
   ```

3. **Schema Testing**: Add tests that validate all tool schemas against OpenAI's requirements

## Best Practices for Tool Development

When creating new agent tools:

1. Use simple parameter types where possible
2. Provide explicit schemas for complex types
3. Avoid optional complex types (use separate functions instead)
4. Always validate schemas before registering tools
5. Use schema aliases for common parameter patterns
6. Test tools directly with the OpenAI API before integration

## References

- OpenAI Function Calling API: https://platform.openai.com/docs/guides/function-calling
- JSON Schema specifications: https://json-schema.org/understanding-json-schema/
- OpenAI schema validation requirements: https://platform.openai.com/docs/guides/function-calling/function-calling