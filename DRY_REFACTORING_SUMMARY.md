# DRY Principle Refactoring Summary

## Overview
Applied maximum DRY (Don't Repeat Yourself) principle throughout the codebase by creating reusable helper functions and eliminating code duplication.

## Key Improvements

### 1. State Data Access Helper (`utils/state_helpers.py`)
**Problem**: Repeated pattern of `state_data = await state.get_data()` followed by `lang = state_data.get("language", Defaults.LANGUAGE)` throughout the codebase.

**Solution**: Created `StateData` helper class with properties for common state values:
- `language` - automatically defaults to 'ru'
- `patient_id`, `patient_guid`, `step`, `add_patient`
- `phone_number`, `cart`, `service`, `patient_form`
- `selected_services_print`, `fetched_services`, etc.
- `limit`, `offset`, `count` for pagination

**Usage**:
```python
# Before:
state_data = await state.get_data()
lang = state_data.get("language", Defaults.LANGUAGE)
patient_id = state_data.get("patient_id")

# After:
state_data = await get_state_data(state)
lang = state_data.language
patient_id = state_data.patient_id
```

**Impact**: Eliminated 48+ instances of repetitive state access patterns.

### 2. Loading Message Helper (`utils/message_helpers.py`)
**Problem**: Repeated pattern of creating loading messages and manually deleting them:
```python
loading_msg = await message.answer(get_translation(lang, "loading"))
try:
    # do work
finally:
    await loading_msg.delete()
```

**Solution**: Created `loading_message` context manager:
```python
# Before:
loading_msg = await message.answer(get_translation(lang, "loading"))
try:
    result = await api_call()
finally:
    await loading_msg.delete()

# After:
async with loading_message(message, state) as _:
    result = await api_call()
```

**Impact**: Eliminated 10+ instances of loading message handling.

### 3. Language Helper (`utils/message_helpers.py`)
**Problem**: Repeated `lang = state_data.get("language", Defaults.LANGUAGE)` pattern.

**Solution**: Created `get_language()` helper function:
```python
# Before:
state_data = await state.get_data()
lang = state_data.get("language", Defaults.LANGUAGE)

# After:
lang = await get_language(state)
```

**Impact**: Simplified language access throughout the codebase.

### 4. Error Message Helper (`utils/message_helpers.py`)
**Problem**: Repeated pattern of sending error messages:
```python
await message.answer(get_translation(lang, 'try_again'))
```

**Solution**: Created `send_error_message()` helper:
```python
# Before:
lang = await get_language(state)
await message.answer(get_translation(lang, 'try_again'))

# After:
await send_error_message(message, state, 'try_again')
```

**Impact**: Centralized error message handling.

### 5. Keyboard Helper (`utils/keyboard_helpers.py`)
**Problem**: `get_main_keyboard()` function duplicated in 5+ files.

**Solution**: Centralized in `utils/keyboard_helpers.py`:
```python
# Before (in each handler file):
async def get_main_keyboard(state: FSMContext):
    from keyboards.default.main import get_main_keyboard as _get_main_keyboard
    return await _get_main_keyboard(state)

# After (import once):
from utils.keyboard_helpers import get_main_keyboard
```

**Impact**: Eliminated 5+ duplicate function definitions.

## Refactored Files

### Handlers
- ✅ `handlers/users/cart_handlers.py` - Uses all helper functions
- ✅ `handlers/users/service_handlers.py` - Uses all helper functions  
- ✅ `handlers/users/patient_handlers.py` - Uses all helper functions
- ✅ `handlers/users/start_refactored.py` - Uses all helper functions
- 🔄 `handlers/users/callback_handlers.py` - Partially refactored (main handler done)

### Utilities Created
- ✅ `utils/state_helpers.py` - StateData class and get_state_data()
- ✅ `utils/message_helpers.py` - Loading messages, language, error handling
- ✅ `utils/keyboard_helpers.py` - Centralized keyboard functions

## Code Reduction

- **State access patterns**: Reduced from 48+ instances to helper function calls
- **Loading messages**: Reduced from 10+ manual implementations to context manager usage
- **Language access**: Simplified from 30+ instances to helper function calls
- **Keyboard functions**: Eliminated 5+ duplicate definitions

## Benefits

1. **Maintainability**: Changes to state access patterns only need to be made in one place
2. **Consistency**: All handlers use the same patterns for common operations
3. **Readability**: Code is cleaner and more expressive
4. **Error Prevention**: Less chance of forgetting to delete loading messages or using wrong defaults
5. **Type Safety**: StateData class provides better IDE support and type hints

## Migration Guide

### For New Code
Always use the helper functions:
```python
from utils.state_helpers import get_state_data
from utils.message_helpers import loading_message, get_language, send_error_message
from utils.keyboard_helpers import get_main_keyboard

# Access state
state_data = await get_state_data(state)
lang = state_data.language  # or await get_language(state)

# Loading messages
async with loading_message(message, state) as _:
    result = await api_call()

# Error messages
await send_error_message(message, state, 'error_key')

# Keyboards
kb = await get_main_keyboard(state)
```

### Remaining Work
- Complete refactoring of `callback_handlers.py` helper functions
- Consider creating more specialized helpers for common patterns
- Add unit tests for helper functions

## Statistics

- **Files refactored**: 5 handler files
- **Helper modules created**: 3
- **Code duplication eliminated**: ~100+ lines
- **Patterns standardized**: 5 major patterns
