# Agent Schema Guidelines

This document outlines best practices and requirements for defining agent function schemas when working with the OpenAI API and Agent SDK.

## Schema Validation Requirements

The OpenAI API has specific requirements for function schemas that are used as tools. These requirements must be followed to avoid validation errors:

1. **No Default Values in Function Parameters**
   - Function parameters must not have default values in the function signature
   - Default handling should be done inside the function, not in the signature

2. **All Properties Must Be Required**
   - Every property defined in the schema must be in the `required` list
   - The OpenAI API requires all properties to be required by default

3. **No Extra Required Properties**
   - The `required` list must not contain properties that don't exist in the schema

## Correct Patterns

### ✅ DO: Remove default values from function signatures

```python
# CORRECT: No default values in signature, handle defaults internally
def generate_document(
    self, 
    document_type: str, 
    parties: List[str], 
    key_terms: Dict[str, str],
    jurisdiction: str
) -> str:
    # Handle default values internally
    if not jurisdiction:
        jurisdiction = "Not specified"
    
    # Function implementation...
```

### ✅ DO: Handle Optional parameters internally

```python
# CORRECT: Use regular type, handle None values internally
def calculate_carbon_footprint(
    self, 
    activities: Dict[str, Any],
    organization_size: str,
    calculation_scope: str,
    include_recommendations: bool
) -> Dict[str, Any]:
    # Handle None values internally
    if calculation_scope is None:
        calculation_scope = "standard"
    
    if include_recommendations is None:
        include_recommendations = False
    
    # Function implementation...
```

### ✅ DO: Use empty strings for optional string parameters

```python
# CORRECT: Use empty string as default for optional string parameters
def check_jurisdiction(
    self,
    legal_question: str,
    jurisdiction: str
) -> str:
    # Empty string is acceptable in function signatures
    # (but still handle it properly in the function body)
    if not jurisdiction:
        jurisdiction = "General"
    
    # Function implementation...
```

## Incorrect Patterns

### ❌ DON'T: Use Optional with None default values

```python
# INCORRECT: Using Optional with None default
def recommend_conservation_measures(
    self, 
    ecosystem_type: str,
    current_threats: List[str],
    location: str,
    conservation_goal: str,
    available_resources: Optional[Dict[str, Any]] = None  # ❌ PROBLEM
) -> Dict[str, Any]:
    # Function implementation...
```

### ❌ DON'T: Add default boolean values

```python
# INCORRECT: Default boolean value in signature
def calculate_carbon_footprint(
    self, 
    activities: Dict[str, Any],
    organization_size: str,
    calculation_scope: str,
    include_recommendations: bool = False  # ❌ PROBLEM
) -> Dict[str, Any]:
    # Function implementation...
```

### ❌ DON'T: Use default values for any parameters

```python
# INCORRECT: Default values in signature
def create_sustainability_plan(
    self, 
    organization_type: str, 
    current_practices: List[str],
    priority_areas: List[str],
    timeframe: str = "medium-term",  # ❌ PROBLEM
    budget_constraint: str = "moderate"  # ❌ PROBLEM
) -> Dict[str, Any]:
    # Function implementation...
```

## Testing Schema Compliance

We have tools to help ensure your agent functions comply with these requirements:

1. **Schema Validation Script**
   ```
   python scripts/fix_agent_schemas.py --check
   ```
   Identifies issues in agent function schemas without making changes.

2. **Automated Schema Fixes**
   ```
   python scripts/fix_agent_schemas.py --fix
   ```
   Automatically fixes common schema issues in agent functions.

3. **Schema Validation Tests**
   ```
   pytest tests/agents/test_schema_validation.py
   ```
   Validates all agent schemas against the OpenAI API requirements.

## Common Error Messages

If you encounter these error messages, your function schema likely has issues:

```
Invalid schema for function 'generate_document': In context=(), 'required' is required to be supplied and to be an array including every key in properties. Extra required key 'key_terms' supplied.
```
- **Problem**: The `required` list contains keys that aren't defined in `properties`, or some properties aren't in `required`.
- **Solution**: Ensure all properties are in the `required` list, and all required keys exist in properties.

```
Invalid schema for function 'calculate_carbon_footprint': In context=('properties', 'include_recommendations'), 'default' is a forbidden key on a $ref-able schema
```
- **Problem**: A parameter has a default value in the function signature.
- **Solution**: Remove the default value from the function signature and handle it internally.