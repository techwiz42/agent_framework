# Prompt Injection Protection

This document explains the prompt injection protection system implemented in the Cyberiad platform.

## Overview

Prompt injection attacks attempt to manipulate AI models by including instructions in user inputs that override the model's intended behavior. Our protection system consists of multiple layers of defense:

1. **Input Sanitization**: Detecting and filtering suspicious patterns in user messages
2. **Input Wrapping**: Clearly delineating user content from system instructions
3. **Multiple Security Layers**: Implementing checks at both API and agent levels
4. **Extensible Pattern Registry**: Supporting environment variable and file-based custom patterns

## Implementation Details

### Input Sanitizer

The `InputSanitizer` class in `app/core/input_sanitizer.py` provides the core functionality for detecting and mitigating prompt injection attempts.

#### Detection Patterns

The sanitizer checks for several categories of suspicious patterns:

1. **System Instruction Override Attempts**: 
   - "ignore previous instructions"
   - "disregard above instructions"
   - "system prompt"
   - etc.

2. **Role-Playing Prompts**:
   - "You are now a..."
   - "I want you to act as..."
   - etc.

3. **Delimiter Injection**:
   - "```system"
   - "###instructions"
   - etc.

4. **Control Characters**: Invisible characters that might be used to obscure malicious content

#### Sanitization Process

When a user message is received:

1. The message is scanned for suspicious patterns
2. Detected patterns are replaced with `[FILTERED]` markers
3. Control characters are removed
4. The sanitized message is wrapped in `<user_message>` tags
5. The message is logged for review if suspicious content is detected

### Multi-Layer Protection

The protection is implemented at multiple levels:

1. **API Layer** (`websockets.py`): First check occurs as messages enter the system
2. **Agent Manager** (`agent_manager.py`): Second check before messages reach the LLM
3. **Context Tracking**: Original messages and detected patterns are stored for auditing

### Configuration Options

The protection system can be customized through:

1. **Environment Variables**:
   - `PROMPT_INJECTION_PATTERNS`: Comma-separated list of additional regex patterns to detect
   - `PROMPT_INJECTION_PATTERNS_FILE`: Path to a file containing additional patterns (one per line)

2. **Pattern File Format**:
   ```
   # This is a comment
   (?i)dangerous\s+pattern
   another_pattern
   ```

## Testing

Unit tests for the input sanitizer are available in `tests/test_input_sanitizer.py`.

## Security Recommendations

1. **Monitor Logs**: Regularly review logs for detected prompt injection attempts
2. **Update Patterns**: Add new patterns as new attack vectors are discovered
3. **Maintain Balance**: Adjust filters to balance security and usability

## Extending Protection

To add new protection patterns:

1. Add them to `SUSPICIOUS_PATTERNS`, `ROLE_PLAY_PATTERNS`, or `DELIMITER_PATTERNS` in the `InputSanitizer` class
2. Or use environment variables or pattern files for dynamic updates
3. Add corresponding test cases to ensure patterns work as expected

Remember that this protection is a mitigation strategy that reduces risk, but complete protection against all possible prompt injection attacks is an ongoing challenge.