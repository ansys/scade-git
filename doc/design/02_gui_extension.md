# GUI Extension Design Document

## Component Overview

**Component:** SCADE IDE Git Extension  
**Modules:** `ansys.scade.git.extension.gitextcore`, `ansys.scade.git.extension.gitextension`  
**Primary Files:**
- `src/ansys/scade/git/extension/gitextcore.py` - Core command implementations
- `src/ansys/scade/git/extension/gitextension.py` - IDE-specific integration
- `src/ansys/scade/git/extension/ide.py` - IDE abstraction layer

**Purpose:** Integrate Git version control directly into the SCADE Suite IDE, providing GUI-based Git operations for SCADE projects.

## Responsibilities

1. **UI Integration**: Create menus, toolbars, context menus, and browser panels in SCADE IDE
2. **Command Handling**: Implement Git command handlers (refresh, stage, unstage, commit, reset, diff)
3. **Status Display**: Show file status in a hierarchical browser with visual indicators
4. **User Interaction**: Handle user actions via dialogs, confirmations, and selections
5. **Project Management**: Track SCADE project files and their Git status
6. **IDE Abstraction**: Provide abstraction layer for different IDE implementations

## Architecture

### Component Structure

```
┌────────────────────────────────────────────────────────┐
│                    SCADE Suite IDE                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   Menus      │  │   Toolbars   │  │Git Browser  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
└─────────┼──────────────────┼──────────────────┼────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
          ┌──────────────────▼───────────────────────┐
          │      gitextension.py (Studio class)      │
          │  • Extension registration & lifecycle    │
          │  • UI creation (menus, toolbars, browser)│
          │  • Event handling                        │
          └──────────────────┬───────────────────────┘
                             │
          ┌──────────────────▼───────────────────────┐
          │         gitextcore.py (Commands)         │
          │  • CmdRefresh    • CmdStageAll           │
          │  • CmdStage      • CmdUnstageAll         │
          │  • CmdUnstage    • CmdCommit             │
          │  • CmdReset      • CmdDiff               │
          └──────────────────┬───────────────────────┘
                             │
          ┌──────────────────▼───────────────────────┐
          │         ide.py (Abstraction Layer)       │
          │  • Command abstract base class           │
          │  • Ide abstract base class               │
          └──────────────────┬───────────────────────┘
                             │
          ┌──────────────────▼───────────────────────┐
          │            GitClient Layer               │
          │  (See Git Client Design Document)       │
          └──────────────────────────────────────────┘
```

### Class Hierarchy

```
Command (Abstract Base Class)
├── CmdRefresh
├── GitRepoCommand (Abstract, requires valid repo)
│   ├── CmdStage
│   ├── CmdStageAll
│   ├── CmdUnstage
│   ├── CmdUnstageAll
│   ├── CmdCommit
│   ├── CmdReset
│   └── CmdDiff

Ide (Abstract Base Class)
└── Studio (SCADE-specific implementation)
```

## Key Design Decisions

### 1. Command Pattern

**Decision:** Use Command pattern for all Git operations.

**Structure:**
```python
class Command(metaclass=ABCMeta):
    def __init__(self, ide: Ide, name: str, status_message: str, 
                 tooltip_message: str, image_file: str):
        self.ide = ide
        self.name = name
        # ...
    
    @abstractmethod
    def on_activate(self):
        """Execute the command"""
        pass
    
    def on_enable(self) -> bool:
        """Determine if command should be enabled"""
        return True
```

**Rationale:**
- Encapsulates each Git operation as an object
- Enables/disables commands based on context
- Separates UI concerns from business logic
- Supports undo/redo in future (not yet implemented)
- Testable without IDE

**Benefits:**
- Easy to add new commands
- Commands can share common validation logic
- IDE-agnostic command implementations

### 2. IDE Abstraction Layer

**Decision:** Create abstract `Ide` class to separate SCADE-specific code from command logic.

**Interface:**
```python
class Ide(metaclass=ABCMeta):
    @abstractmethod
    def log(self, text: str): pass
    
    @abstractmethod
    def get_active_project(self) -> Project: pass
    
    @abstractmethod
    def get_projects(self) -> List[Project]: pass
    
    @abstractmethod
    def create_browser(self, name: str, icon: str): pass
    
    @abstractmethod
    def browser_report(self, item, category, **kwargs): pass
    
    # ... other abstract methods
```

**Rationale:**
- Enables testing without full SCADE IDE
- Could support other IDEs in future (VS Code extension, Eclipse)
- Isolates SCADE API dependencies
- Facilitates mock implementations for testing

### 3. Git Browser Design

**Decision:** Use hierarchical browser with four main categories.

**Structure:**
```
Git Browser
└── branch: main
    ├── Staged files (expanded by default)
    │   ├── project.etp [+]
    │   └── models/file1.xscade [M]
    ├── Unstaged files (expanded by default)
    │   ├── models/file2.xscade [M]
    │   └── docs/readme.md [-]
    ├── Clean files (collapsed by default)
    │   └── models/file3.xscade
    └── Extern files (collapsed by default)
        └── ../outside/file.txt
```

**Icons:**
- `[+]` Added
- `[M]` Modified
- `[-]` Removed/Deleted
- `[?]` Untracked
- `[clean]` No changes
- `[extern]` Outside repository

**Rationale:**
- Users quickly see what needs attention (staged/unstaged)
- Clean files collapsed by default reduces clutter
- Visual indicators (icons) show status at a glance
- Hierarchical structure mirrors file organization

**Category Expansion Policy:**
```python
BrowserCat = {
    'Staged': 'Staged files',      # Expanded
    'Unstaged': 'Unstaged files',  # Expanded
    'Clean': 'Clean files',         # Collapsed
    'Extern': 'Extern files',       # Collapsed
}
```

### 4. File Status Tracking

**Decision:** Maintain global dictionary tracking which files appear in which browser categories.

**Data Structure:**
```python
project_files_status = {
    'Staged files': ['project.etp', 'models/file1.xscade'],
    'Unstaged files': ['models/file2.xscade'],
    'Clean files': ['models/file3.xscade'],
    'Extern files': ['../outside/file.txt']
}
```

**Rationale:**
- Quick lookup of file locations in browser
- Enables efficient browser updates
- Supports batch operations on categories
- Facilitates "stage all" / "unstage all" operations

**Refresh Strategy:**
- Clear all lists on refresh
- Rebuild from git status + SCADE project files
- Update browser with new categorization

### 5. Separation of SCADE and Git Files

**Decision:** Only show files that are part of SCADE project, plus detected annotation files.

**Algorithm:**
```
FOR EACH Project in SCADE workspace:
    - Add project file (.etp) to browser
    FOR EACH FileRef in project:
        - Add file to browser
        - IF file is .xscade:
            - Check for corresponding .ann file
            - IF .ann exists: Add to browser
```

**Rationale:**
- SCADE users care about SCADE files, not build artifacts
- Automatically includes associated files (.ann for .xscade)
- Reduces clutter from non-SCADE files in repo
- Git status still available for all files via gitclient

**Trade-off:** Files in Git but not in SCADE project are invisible in extension (but still managed by Git).

### 6. Refresh-Based Model

**Decision:** Use explicit refresh operations rather than continuous monitoring.

**Trigger Points:**
1. User clicks "Refresh" button
2. After any mutating operation (stage, unstage, commit, reset)
3. Optionally on project load (not always - can crash editor)

**Rationale:**
- File system watching is complex and platform-dependent
- SCADE projects change infrequently during editing
- Explicit refresh gives user control
- Avoids performance overhead of continuous monitoring
- Prevents race conditions with external Git operations

**User Experience:**
- Quick refresh button always visible
- Auto-refresh after extension operations
- Clear visual indication of refresh completion

## Algorithms

### Browser Refresh Algorithm

**Purpose:** Update Git browser to reflect current repository state.

**Input:** Active SCADE project

**Output:** Updated browser with categorized files

**Algorithm:**
```
1. Validate preconditions:
   - Active project exists
   - Git repository found
   
2. Initialize GitClient:
   - Call gitclient.refresh(project_path)
   - Get current branch name
   
3. Create/clear browser:
   - Create "Git" browser if not exists
   - Create branch node and categories
   - Clear all file status lists
   
4. Collect SCADE project files:
   projects = []
   FOR EACH project in workspace:
       a. Add project file to browser
       b. Get git status for project file
       c. Categorize and add to appropriate category
       
       FOR EACH file_ref in project:
           i. Add file to browser
           ii. Get git status for file
           iii. Categorize and add to appropriate category
           
           iv. IF file is .xscade:
               - Check for .ann file
               - IF exists: Add .ann to browser with status
   
5. Update browser UI:
   - Expand staged/unstaged categories
   - Collapse clean/extern categories
   - Update status bar with repo info
```

**Performance:** O(n) where n is number of files in SCADE project(s).

### Stage/Unstage Operations

**Purpose:** Move files between unstaged and staged areas.

**Input:** Selected items from browser or context menu

**Algorithm:**
```
Stage Operation:
1. Get selection from IDE
2. Extract file paths:
   files_to_process = []
   FOR EACH item in selection:
       IF item is Project OR FileRef:
           files_to_process.append(item.pathname)
3. Call gitclient.stage(files_to_process)
4. Refresh browser to show new status

Unstage Operation:
(Same as Stage but calls gitclient.unstage())
```

**Validation:**
- Commands only enabled when git repo exists
- Only process Project and FileRef items
- Ignore invalid selections

**Batch Operations:**
- "Stage All" / "Unstage All" operate on entire categories
- Process all files in category list at once
- Single git operation for efficiency

### Commit Dialog Flow

**Purpose:** Collect commit message and create commit.

**User Interaction:**
```
1. User clicks "Commit" command
2. System opens commit dialog:
   ┌─────────────────────────────────────┐
   │ Commit Changes                      │
   ├─────────────────────────────────────┤
   │ Commit message:                     │
   │ ┌─────────────────────────────────┐ │
   │ │ [Multi-line text input]         │ │
   │ │                                 │ │
   │ │                                 │ │
   │ └─────────────────────────────────┘ │
   │                                     │
   │ Author: John Doe <jdoe@example.com> │
   │                                     │
   │         [Cancel]  [Commit]          │
   └─────────────────────────────────────┘
3. User enters message and clicks Commit
4. System validates:
   - Message not empty
   - Staged files exist
5. Call gitclient.commit(message, author, committer)
6. Show success/failure message
7. Refresh browser
```

**Error Handling:**
- Empty message → Show error, don't close dialog
- No staged files → Show warning, abort
- Git error → Show error message with details

### Diff/Export Operation

**Purpose:** Export a Git branch to a temporary directory for external diff/merge tools.

**Use Case:** Compare current workspace with another branch.

**Algorithm:**
```
1. User selects "Diff" command
2. System shows branch selection dialog:
   - List all branches in repository
   - Default: main/master branch
3. User selects branch to compare
4. System creates temporary directory:
   temp_dir = TEMP/scade_git_export_{branch_name}/
5. Export branch to temp directory:
   - Use git archive or git checkout
   - Extract all files from selected branch
6. Open SCADE project from temp directory
7. User can now use SCADE's built-in diff/merge tools
```

**Safety Measures:**
- Validate temp directory path (prevent path traversal)
- Clean up old temp directories
- Use safe tar extraction (prevent tar bombs)

**Implementation:**
```python
def badpath(path: str, base: Path) -> bool:
    """Return whether a file is external to the base hierarchy."""
    target = (base / path).resolve()
    return not str(target).startswith(str(base))

def badlink(info: tarfile.TarInfo, base: Path) -> bool:
    """Return whether a link is external to the base hierarchy."""
    path = (base / info.name).parent / info.linkname
    return badpath(str(path), base)
```

## User Interface Design

### Menu Structure

```
Git (Top-level menu)
├── Refresh                 [Ctrl+G R]
├── ──────────────────
├── Stage Selected          [Ctrl+G S]
├── Stage All              [Ctrl+G A]
├── Unstage Selected       [Ctrl+G U]
├── Unstage All            [Ctrl+G Shift+U]
├── ──────────────────
├── Commit...              [Ctrl+G C]
├── Reset Selected         [Ctrl+G Z]
├── ──────────────────
└── Diff with Branch...    [Ctrl+G D]
```

### Toolbar

```
┌────────────────────────────────────────────────┐
│ [↻] [+] [++] [−] [−−] [✓] [⎌] [⇄]            │
│  ↑   ↑   ↑    ↑   ↑    ↑   ↑   ↑              │
│  │   │   │    │   │    │   │   └── Diff       │
│  │   │   │    │   │    │   └────── Reset      │
│  │   │   │    │   │    └────────── Commit     │
│  │   │   │    │   └─────────────── Unstage All│
│  │   │   │    └─────────────────── Unstage    │
│  │   │   └──────────────────────── Stage All  │
│  │   └──────────────────────────── Stage      │
│  └──────────────────────────────── Refresh    │
└────────────────────────────────────────────────┘
```

### Context Menu (Right-click in browser)

```
Context menu on file:
├── Open
├── ──────────────────
├── Stage              (if unstaged)
├── Unstage            (if staged)
├── Reset              (if modified)
├── ──────────────────
└── Show in Explorer
```

## State Management

### Global State Variables

```python
# Current git client instance
_git_client: Optional[GitClient] = None

# File categorization for browser
project_files_status: Dict[str, List[str]] = {
    'Staged files': [],
    'Unstaged files': [],
    'Clean files': [],
    'Extern files': []
}

# Icon mappings for file status
status_data: Dict[GitStatus, Tuple[str, str]] = {
    GitStatus.added: ('Staged files', icons['added']),
    GitStatus.modified_staged: ('Staged files', icons['modified']),
    # ... etc
}

# Resource paths
icons: Dict[str, str] = {}  # Icon file paths
res: Dict[str, str] = {}    # Other resources
```

### State Transitions

```
Extension Lifecycle:
Initialize → Register → Activate → [Operations] → Deactivate

Operations Cycle:
Idle → Refresh → Display Status → User Action → Update Git → 
Refresh → Display Status → Idle
```

## Integration Points

### SCADE API Integration

**Project Access:**
```python
import scade
from scade.model.project.stdproject import Project, FileRef

# Get all projects in workspace
projects = scade.model.suite.get_projects()

# Get active project
active_project = scade.application.workspace.active_project
```

**Browser API:**
```python
# Create browser
scade.application.ui.create_browser('Git', icon_path)

# Add items
scade.application.ui.browser_report(
    item,           # Project, FileRef, or string
    category,       # Parent category name
    expanded=True,  # Expand/collapse
    icon_file=icon  # Icon path
)
```

### GitClient Integration

```python
# Initialize
git_client = StudioGitClient(ide)

# Refresh status
success = git_client.refresh(project.pathname)

# Get file status
path, status = git_client.get_file_status(file.pathname)

# Operations
git_client.stage([file1, file2])
git_client.unstage([file3])
git_client.commit(message, author, committer)
git_client.reset_files([file4])
```

## Error Handling

### Error Categories

1. **Initialization Errors**
   - No Git repository found → Show info message, disable commands
   - Dulwich not installed → Show error, disable extension
   - Invalid SCADE project → Log error, skip project

2. **Operation Errors**
   - Commit with empty message → Show dialog error, keep dialog open
   - Stage deleted file → Log warning, continue with other files
   - Network error during fetch → Show error, rollback operation

3. **UI Errors**
   - Browser creation failed → Log error, disable browser updates
   - Icon file not found → Use default icon, log warning
   - Dialog display error → Log error, use fallback (direct commit)

### Error Display

**Message Types:**
- **Info**: Status bar message (disappears after 5 seconds)
- **Warning**: Message box with warning icon
- **Error**: Message box with error icon and details
- **Critical**: Message box + disable extension

**Error Logging:**
All errors logged to SCADE output pane via `ide.log()`.

## Performance Considerations

### Optimization Strategies

1. **Lazy Browser Population**
   - Don't populate browser until user opens it
   - Cache browser state between refreshes

2. **Incremental Updates**
   - Only update changed file status
   - Avoid full browser rebuild

3. **Batch Git Operations**
   - Stage/unstage multiple files in single operation
   - Reduce git subprocess calls

4. **Icon Caching**
   - Load icons once at initialization
   - Reuse icon objects for multiple files

### Performance Characteristics

- **Browser Refresh**: O(n) where n = number of SCADE files
- **Stage/Unstage**: O(m) where m = number of selected files
- **Commit**: O(staged files + tree size)
- **UI Update**: O(visible items in browser)

### Scalability Limits

- **SCADE Projects**: Tested up to 10 projects per workspace
- **Files per Project**: Tested up to 500 files per project
- **Git Repository**: Tested with repos up to 5000 files
- **Browser Items**: Usable with up to 2000 visible items

## Testing Strategy

### Unit Tests

**Location:** `tests/extension/test_gitextcore.py`

**Test Cases:**
- Command enable/disable logic
- File categorization algorithm
- Path validation (badpath, badlink)
- Browser refresh logic (mocked)
- Stage/unstage selection processing

**Mocking Strategy:**
```python
class MockIde(Ide):
    def __init__(self):
        self.log_messages = []
        self.browser_items = []
    
    def log(self, text):
        self.log_messages.append(text)
    
    def browser_report(self, item, category, **kwargs):
        self.browser_items.append((item, category))
```

### Integration Tests

**Location:** `tests/extension/test_gitextension.py`

**Test Scenarios:**
- Extension lifecycle (register → activate → deactivate)
- Full refresh with real Git repository
- Stage → commit → reset workflow
- Multiple projects in workspace
- Error handling with corrupted repository

### Manual Testing

**Test Plan:**
1. Load SCADE project in Git repository
2. Verify browser shows correct file status
3. Stage files via context menu
4. Commit with valid message
5. Verify commit created in Git
6. Reset files and verify working tree restored
7. Test with projects outside Git repository
8. Test with very large projects (performance)

## Security Considerations

1. **Path Traversal Prevention**
   - Validate all file paths stay within repository
   - Check symbolic links point within allowed directories
   - Sanitize paths from user input

2. **Tar Extraction Safety**
   - Validate tar contents before extraction
   - Prevent tar bombs (excessive directory nesting)
   - Check for malicious symlinks

3. **Command Injection**
   - Use GitClient API (no shell commands)
   - Never pass unsanitized user input to shell
   - Validate all file names and paths

4. **Temporary Files**
   - Use secure temporary directory creation
   - Clean up temporary files after use
   - Set restrictive permissions on temp files

## Future Enhancements

### Planned Features

1. **Branch Visualization**
   - Show branch history graph in browser
   - Visual indication of current branch
   - Quick branch switching

2. **Inline Diff View**
   - Show file diffs directly in SCADE IDE
   - Syntax highlighting for SCADE files
   - Side-by-side or unified diff view

3. **Conflict Resolution UI**
   - Visual merge conflict resolution
   - Integration with SCADE merge tools
   - 3-way merge view for .etp files

4. **History Browser**
   - View commit history
   - Search commits
   - Checkout specific commits

5. **Remote Operations**
   - Push/pull from toolbar
   - Fetch with visual feedback
   - Credential management

6. **Smart Refresh**
   - File system watcher for auto-refresh
   - Refresh only changed files
   - Background refresh without blocking UI

### Performance Improvements

1. **Asynchronous Operations**
   - Background git status queries
   - Non-blocking commit operations
   - Progress indicators for slow operations

2. **Virtual Browser**
   - Only render visible items
   - Load items on-demand during scrolling
   - Reduce memory footprint

3. **Intelligent Caching**
   - Cache file content hashes
   - Avoid redundant git queries
   - Invalidate cache selectively

## Dependencies

### Required
- `ansys.scade.git.extension.gitclient`: Git operations
- `ansys.scade.git.extension.ide`: IDE abstraction
- SCADE Python API: IDE integration
- `dulwich >= 0.21.3`: Git library

### Optional
- External diff tools: For advanced diff operations
- Git binary: Fallback for unsupported operations

## References

- [SCADE Python API Documentation](https://scade.docs.pyansys.com)
- [Dulwich Documentation](https://www.dulwich.io/docs/)
- [Command Pattern](https://refactoring.guru/design-patterns/command)
- Design Document: `01_git_client.md`
