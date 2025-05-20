# Fixing Schema Validation Errors in OpenAI Agents SDK Function Tools

## Common Error Types

When using the OpenAI Agents SDK, you may encounter schema validation errors when defining function tools for your agents. These usually appear as:

```
openai.BadRequestError: Error code: 400 - {'error': {'message': "Invalid schema for function 'function_name': ...", 'type': 'invalid_request_error', 'param': 'tools[x].parameters', 'code': 'invalid_function_parameters'}}
```

## Error 1: Extra Required Parameters

### Error Message

```
'required' is required to be supplied and to be an array including every key in properties. Extra required key 'parameter_name' supplied.
```

### Problem

This error occurs when a parameter is listed in the `required` field of the JSON schema, but it doesn't exist in the `properties` field or isn't properly defined. This typically happens with non-optional parameters in your function definition.

### Solution

Make all function parameters optional by giving them default values, usually `None`:

```python
# BEFORE - will cause errors
def analyze_data(
    self,
    required_param: Dict[str, Any], 
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    # Function implementation
    
# AFTER - fixed version
def analyze_data(
    self,
    required_param: Optional[Dict[str, Any]] = None, 
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    # Add validation inside the function
    if required_param is None:
        required_param = {}
    
    # Rest of function implementation
```

## Error 2: Default Values in Schema

### Error Message

```
'default' is not permitted.
```

### Problem

This error occurs when you try to use default values in your function parameters. The OpenAI API doesn't allow `default` values in the JSON schema for function parameters.

### Solution

1. Remove default values from parameters (other than `None`)
2. Handle defaults inside the function implementation:

```python
# BEFORE - will cause errors
def analyze_segment(
    self,
    segment_name: Optional[str] = None,
    analysis_type: Optional[str] = "detailed", # This will cause problems
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # Function implementation
    
# AFTER - fixed version
def analyze_segment(
    self,
    segment_name: Optional[str] = None,
    analysis_type: Optional[str] = None, # Use None as default
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # Set defaults inside the function
    analysis_type = analysis_type or "detailed"
    
    # Rest of function implementation
```

## General Best Practices

1. **Make all parameters optional** with `None` as the default value
2. **Handle default values inside the function** body, not in the parameter definition
3. **Add type hints** using `Optional[Type]` for all parameters
4. **Validate inputs inside the function** since all parameters are optional
5. **Use meaningful docstrings** since they're used to generate schemas for the LLM

## Example Implementation Pattern

```python
def function_tool_template(
    self,
    param1: Optional[str] = None,
    param2: Optional[int] = None,
    param3: Optional[Dict[str, Any]] = None,
    param4: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Description of what this function does.
    
    Args:
        param1: Description of parameter 1.
        param2: Description of parameter 2.
        param3: Description of parameter 3.
        param4: Description of parameter 4.
    
    Returns:
        A dictionary containing the results.
    """
    # Set default values
    param1 = param1 or "default value"
    param2 = param2 or 0
    param3 = param3 or {}
    param4 = param4 or []
    
    # Function implementation
    result = {
        "param1": param1,
        "param2": param2,
        # ... rest of implementation
    }
    
    return result
```

This pattern ensures that your function tools will pass OpenAI's schema validation while maintaining the desired functionality.
