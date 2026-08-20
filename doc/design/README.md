# Design Documentation Index

This directory contains detailed design documents for the Ansys SCADE Git Extensions project.

## Overview

Design documents provide in-depth technical specifications for implementing and maintaining the system components. Unlike the user-facing Sphinx documentation, these documents are intended for developers working on the codebase.

## Document Structure

Each design document follows a consistent structure:

1. **Component Overview** - Purpose and responsibilities
2. **Architecture** - Component structure and relationships
3. **Key Design Decisions** - Rationale for major choices
4. **Algorithms** - Detailed algorithmic descriptions
5. **Data Structures** - Internal data representations
6. **Integration Points** - How components interact
7. **Performance Considerations** - Optimization strategies
8. **Error Handling** - Error categories and recovery
9. **Testing Strategy** - Unit and integration tests
10. **Future Enhancements** - Planned improvements
11. **Dependencies** - Required libraries and tools
12. **Security Considerations** - Safety measures
13. **References** - Related documentation

## Design Documents

### [01. Git Client](01_git_client.md)

**Component:** `ansys.scade.git.extension.gitclient`

Provides Python abstraction layer for Git operations using Dulwich library. Manages repository discovery, status tracking, and Git operations (stage, commit, reset, etc.) for SCADE projects.

**Key Topics:**
- Dulwich integration
- Repository discovery algorithm
- File status management and caching
- Abstract logging interface
- Version validation strategy

### [02. GUI Extension](02_gui_extension.md)

**Components:** `ansys.scade.git.extension.gitextcore`, `ansys.scade.git.extension.gitextension`

Integrates Git version control into SCADE Suite IDE with GUI-based operations. Implements command pattern for Git operations and provides hierarchical browser for file status.

**Key Topics:**
- Command pattern implementation
- IDE abstraction layer
- Git browser design
- File status categorization
- User interaction flows
- Menu and toolbar structure

### [03. ETP Merge Tool](03_etp_merge.md)

**Component:** `ansys.scade.git.etpmerge`

Performs intelligent three-way merges of SCADE project files (.etp) during Git merge operations. Uses entity tracking and caching to automatically resolve conflicts when possible.

**Key Topics:**
- Three-way merge algorithm
- Entity ID tracking and caching
- Visitor pattern for tree traversal
- Conflict detection and reporting
- Folder hierarchy merging
- Property merging strategies

### [04. ALMGT Merge Tool](04_almgt_merge.md)

**Component:** `ansys.scade.git.almgtmerge`

Performs automatic three-way merges of SCADE traceability files (.almgt) with conflict-free resolution using set-based semantics.

**Key Topics:**
- Set-based merge semantics
- XML processing with lxml
- Traceability link management
- Conflict-free algorithm
- Two-level dictionary structure

## Relationship Between Components

```
┌─────────────────────────────────────────────────────────┐
│                    SCADE Suite IDE                      │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────▼──────────────┐
          │   GUI Extension (02)     │
          │  • Commands              │
          │  • Browser UI            │
          │  • Event Handling        │
          └───────────┬──────────────┘
                      │
          ┌───────────▼──────────────┐
          │   Git Client (01)        │
          │  • Dulwich Wrapper       │
          │  • Repository Ops        │
          │  • Status Management     │
          └──────────────────────────┘
                      │
                      │
          ┌───────────▼──────────────┐
          │     Git Repository       │
          │       (.git/)            │
          └───────────┬──────────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
┌──────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
│ ETP Merge(3)│ │ALMGT     │ │   Other     │
│ *.etp files │ │Merge (4) │ │   Files     │
│             │ │*.almgt   │ │             │
└─────────────┘ └──────────┘ └─────────────┘
  (merge driver)  (merge driver)  (text merge)
```

## Component Dependencies

```
GUI Extension (02)
    ├─> Git Client (01)
    │   └─> Dulwich
    └─> SCADE API

Git Client (01)
    └─> Dulwich

ETP Merge (03)
    └─> SCADE API

ALMGT Merge (04)
    └─> lxml
```

## Reading Guide

### For New Developers

1. Start with **01_git_client.md** to understand Git operations
2. Read **02_gui_extension.md** for IDE integration
3. Review **03_etp_merge.md** and **04_almgt_merge.md** for merge tools

### For Maintenance

- Refer to specific document for component being modified
- Check "Integration Points" sections for impact analysis
- Review "Testing Strategy" sections before changes

### For Feature Development

- Check "Future Enhancements" sections for planned work
- Review "Key Design Decisions" for architectural constraints
- Consult "Performance Considerations" for optimization guidance

## Design Principles

### Across All Components

1. **Separation of Concerns**
   - Clear component boundaries
   - Minimal coupling between modules
   - Well-defined interfaces

2. **Abstraction**
   - Abstract base classes for extensibility
   - IDE-agnostic command implementations
   - Platform-independent file operations

3. **Error Handling**
   - Graceful degradation
   - Informative error messages
   - No silent failures

4. **Performance**
   - Caching strategies
   - O(1) lookups via dictionaries
   - Minimal redundant operations

5. **Testability**
   - Mock-friendly interfaces
   - Isolated components
   - Comprehensive test coverage

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-06 | Initial design documentation created |

## Contributing to Design Docs

When modifying code, update corresponding design documents:

1. **Document New Features**: Add to "Future Enhancements" or create new section
2. **Update Decisions**: Revise "Key Design Decisions" if architectural changes
3. **Maintain Algorithms**: Keep algorithm descriptions in sync with code
4. **Document Dependencies**: Update when adding/removing libraries
5. **Update Diagrams**: Reflect structural changes in architecture diagrams

## Related Documentation

- **User Documentation**: [../source/architecture.rst](../source/architecture.rst)
- **API Documentation**: Auto-generated from docstrings
- **Contributing Guide**: [../../CONTRIBUTING.md](../../CONTRIBUTING.md)
- **README**: [../../README.rst](../../README.rst)

## Tools and Conventions

### Diagram Notation

- **Boxes**: Components or classes
- **Arrows**: Dependencies or data flow
- **Solid lines**: Direct dependencies
- **Dashed lines**: Optional or indirect dependencies

### Code Examples

All code examples use Python 3.7+ syntax (minimum SCADE version).

### Terminology

- **Entity**: SCADE project element (Project, Folder, FileRef, etc.)
- **LLR**: Low-Level Requirement (SCADE model element)
- **HLR**: High-Level Requirement (external requirement)
- **OID**: Object ID (unique identifier in SCADE)
- **ETP**: Extension file format for SCADE projects
- **ALMGT**: Traceability file format for SCADE

## Questions or Feedback

For questions about design documents or suggestions for improvements:
- Create an issue on [GitHub Issues](https://github.com/ansys/scade-git/issues)
- Discuss on [Ansys Developer Portal](https://discuss.ansys.com/)
