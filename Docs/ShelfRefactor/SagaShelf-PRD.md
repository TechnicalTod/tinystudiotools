# Maya Shelf Button System - PRD

## Overview

The Maya Shelf Button System provides a dynamic, metadata-driven approach to organizing and displaying tools in Maya's shelf interface. This system automatically discovers tools from script directories, extracts metadata from docstrings, and builds shelf buttons without requiring manual configuration files or extensive boilerplate code.

## Purpose

- **Simplified Maintenance**: Eliminate repetitive code and centralize tool definitions
- **Self-Documentation**: Keep tool metadata with the code that implements it
- **Automatic Discovery**: New tools are automatically added to the shelf without manual registration
- **Consistent Interface**: Provide a uniform appearance and behavior across all tools
- **Extensibility**: Allow easy addition of new tools with minimal overhead

## User Stories

### Developer Stories

1. As a developer, I want to add new tools to the shelf without modifying the shelf builder code
2. As a developer, I want tool metadata to be defined in the same file as the tool implementation
3. As a developer, I want to control how my tools appear in the shelf (icons, tooltips, etc.)
4. As a developer, I want to organize related tools into logical groups with menus
5. As a developer, I want to avoid writing repetitive boilerplate code for each new tool

### Artist Stories

1. As an artist, I want a consistent and organized shelf interface
2. As an artist, I want tools to be logically grouped by function
3. As an artist, I want clear tooltips explaining what each tool does
4. As an artist, I want the shelf to load quickly without errors
5. As an artist, I want to easily find the tools I need

## Functional Requirements

### Core Functionality

- Auto-discover tools from script directories based on naming conventions
- Extract tool metadata from docstrings using a standardized format
- Build shelf buttons dynamically based on discovered tools
- Group related tools into dropdown menus
- Support spacers and visual organization elements
- Provide consistent error handling for all tools

### Tool Metadata Format

Tools should include a `SAGA_TOOL_CONFIG` JSON block in their docstrings with the following properties:

- `label`: Display name for the tool
- `tooltip`: Hover text description
- `icon`: Icon file name
- `category`: Tool category for grouping
- `entry_point`: Function to call (default: "launch")
- `shelf_button`: Whether to show on shelf (default: true)
- `menu_group`: Group name for menu organization

### Tool Discovery

- Scan all directories ending with "Tools" in the scripts path
- Discover Python modules with tool metadata
- Support both standalone tools and tools within modules
- Handle import errors gracefully
- Cache discovery results for performance

## Technical Requirements

### Code Structure

- Create a modular, object-oriented design
- Implement a tool discovery system
- Create a metadata parser for docstrings
- Build a shelf factory that creates buttons from metadata
- Implement consistent error handling and logging

### Performance Considerations

- Minimize startup time impact
- Use lazy loading for tool imports
- Cache discovery results
- Provide clear error messages for debugging

### Implementation Details

- Use regular expressions to extract metadata from docstrings
- Implement a tool resolver to dynamically import and call functions
- Create a shelf builder that works with the existing shelfCreate module
- Support all existing tool categories and functionality

## Out of Scope

- Complex configuration UI for shelf customization
- User-specific shelf preferences
- Custom shelf layouts beyond the standard format
- Integration with external tool systems

## Future Considerations

- User-customizable shelf layouts
- Tool usage analytics
- Keyboard shortcuts for tools
- Search functionality for finding tools
- Tool dependency management

## Success Metrics

- Reduced code size and complexity in shelf builder
- Faster and more reliable shelf loading
- Easier addition of new tools
- Consistent appearance across all tools
- Improved developer experience
