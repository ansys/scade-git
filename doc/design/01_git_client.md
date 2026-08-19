# Git Client Design Document

## Component Overview

**Component:** Git Client
**Module:** `ansys.scade.git.extension.gitclient`
**Primary File:** `src/ansys/scade/git/extension/gitclient.py`
**Purpose:** Provides a Python abstraction layer for Git operations using the Dulwich library to manage SCADE project repositories.

## Responsibilities

1. **Repository Discovery**: Locate Git repositories in the file system hierarchy
2. **Git Operations**: Perform core Git operations (status, stage, unstage, commit, reset)
3. **Status Management**: Track and categorize file status across the repository
4. **Dulwich Integration**: Wrap Dulwich's pure-Python Git implementation for SCADE-specific needs
5. **Logging Abstraction**: Provide extensible logging interface for different environments (IDE vs command-line)

## Architecture

### Class Structure

```
GitClient (Abstract Base Class)
├── Attributes:
│   ├── repo_path: str          # Path to Git repository root
│   ├── repo_name: str          # Repository name
│   ├── branch: str             # Current branch name
│   ├── repo: Repo              # Dulwich Repo object
│   ├── files_status: dict      # Cache of file status information
│   └── dulwich_ok: bool        # Dulwich version validation flag
│
├── Abstract Methods:
│   └── log(text: str)          # Must be implemented by subclasses
│
└── Public Methods:
    ├── get_init_status() -> bool
    ├── refresh(project_path: str) -> bool
    ├── get_file_status(pathname: str) -> Tuple[str, GitStatus]
    ├── stage(files: List[str])
    ├── unstage(files: List[str])
    ├── commit(message: str, author: str, committer: str) -> bool
    └── reset_files(files: List[str])
```

### GitStatus Enumeration

Defines all possible file states in a Git repository:

- **added**: New file staged for commit
- **removed_staged**: Deleted file staged
- **modified_staged**: Modified file staged
- **removed_unstaged**: Deleted but not staged
- **modified_unstaged**: Modified but not staged
- **untracked**: New file not tracked
- **clean**: No changes
- **extern**: File outside repository
- **error**: File missing from filesystem and index
- **none**: Internal error state

## Key Design Decisions

### 1. Dulwich Library Choice

**Decision:** Use Dulwich instead of GitPython or subprocess calls to git binary.

**Rationale:**
- Pure Python implementation - no external dependencies on git binary
- Cross-platform compatibility (Windows, Linux, macOS)
- Programmatic access to Git internals
- Better performance for Python-based operations
- Consistent behavior across different Git versions

**Trade-offs:**
- Slightly less feature-complete than native git
- Performance may be slower for large repositories
- Less familiar API compared to standard git commands

### 2. Abstract Base Class Pattern

**Decision:** Make `GitClient` an abstract base class with abstract `log()` method.

**Rationale:**
- Allows different logging implementations (IDE output pane vs console)
- Separates concerns: Git operations from display/logging
- Enables testing without IDE dependencies
- Supports future extensions (GUI, command-line tool, web interface)

**Implementation:**
```python
class GitClient(metaclass=ABCMeta):
    @abstractmethod
    def log(self, text: str):
        """Log a message - must be implemented by subclass"""
        raise NotImplementedError('Abstract method call')
```

### 3. Repository Discovery Algorithm

**Decision:** Walk up directory tree to find `.git` directory.

**Algorithm:**
```python
def find_git_repo(local_proj_path: str) -> str:
    d = Path(local_proj_path)
    root = Path(d.root)
    disk = d.anchor

    while d != root and str(d) != disk:
        repo_path = d / '.git'
        if repo_path.is_dir():
            return str(d)
        d = d.parent

    return ''
```

**Rationale:**
- Standard Git behavior - respects repository hierarchy
- Allows SCADE projects to be subdirectories of Git repos
- Handles nested repository scenarios
- Works with both Windows and Unix path conventions

### 4. Status Caching Strategy

**Decision:** Cache file status in `files_status` dictionary during `refresh()` operations.

**Rationale:**
- Avoid repeated Git status queries (expensive operation)
- Improve UI responsiveness
- Support batch operations
- Enable quick status lookups for multiple files

**Cache Structure:**
```python
files_status = {
    'relative/path/to/file.etp': GitStatus.modified_staged,
    'another/file.xscade': GitStatus.clean,
    # ...
}
```

**Cache Invalidation:**
- Explicit refresh via `refresh(project_path)` method
- After any mutation operation (stage, unstage, commit, reset)
- On project load/reload in IDE

### 5. Version Validation

**Decision:** Check Dulwich version at initialization and turn off operations if incompatible.

**Implementation:**
```python
min_dulwich_ver = (0, 21, 3)

def __init__(self):
    dulwich_ver = dulwich.__version__
    if dulwich_ver < min_dulwich_ver:
        self.log('Error: Git extension turn off - incompatible Dulwich version')
        self.dulwich_ok = False
    else:
        self.dulwich_ok = True
```

**Rationale:**
- Prevent cryptic errors from API incompatibilities
- Clear error messaging for users
- Fail gracefully rather than crash
- Support multiple Python/SCADE versions

## Algorithms

### File Status Resolution

**Purpose:** Determine the current Git status of a file.

**Input:** path (absolute or relative)

**Output:** Tuple of (normalized_path, GitStatus)

**Algorithm:**
```
1. Normalize file path to repository-relative format
2. Check if file is within repository bounds
   - If outside: return (path, GitStatus.extern)
3. Query Dulwich repository for file status:
   - Check staging area (index)
   - Check working directory
   - Compare with HEAD commit
4. Categorize based on presence and state:
   - In index + changed in workdir: modified_unstaged
   - In index + not in workdir: removed_unstaged
   - In index + unchanged: clean or modified_staged
   - Not in index + in workdir: untracked
   - Not in index + not in workdir: error
5. Return (normalized_path, determined_status)
```

**Edge Cases:**
- Symbolic links: Follow to target
- Case-insensitive filesystems: Normalize case
- Submodules: Treat as single file
- Large files: Status check only (no content read)

### Stage Operation

**Purpose:** Add files to the Git staging area (index).

**Input:** List of file paths

**Algorithm:**
```
1. FOR EACH file in input list:
   a. Normalize path to repository-relative
   b. Validate file is within repository
   c. Check if file exists in working directory
      - If exists: Read content, compute hash
      - If deleted: Mark for removal
   d. Update index with file entry
2. Write updated index to disk
3. Clear status cache for modified files
4. Log success/failure for each file
```

**Concurrency:** Operations are atomic per-file but not transaction-based.

### Commit Operation

**Purpose:** Create a new commit with staged changes.

**Input:**
- message: Commit message text
- author: Author name and email
- committer: Committer name and email

**Algorithm:**
```
1. Validate repository state:
   - Repository exists and is initialized
   - Index has staged changes
   - No merge conflicts present
2. Create commit object:
   - Tree: Build from current index state
   - Parent: Current HEAD commit
   - Author: From input
   - Committer: From input
   - Message: From input
   - Timestamp: Current time
3. Write commit to object database
4. Update HEAD reference to new commit
5. Clear status cache (all files now clean)
6. Return success/failure
```

**Error Handling:**
- Empty commit message: Reject with error
- No staged changes: Reject with warning
- Write failures: Rollback and log error

## Data Structures

### files_status Dictionary

**Purpose:** Cache of file status information for quick lookup.

**Structure:**
```python
{
    'src/file1.etp': GitStatus.modified_staged,
    'src/file2.xscade': GitStatus.untracked,
    'README.md': GitStatus.clean,
    # Key: repository-relative path (str)
    # Value: GitStatus enum
}
```

**Characteristics:**
- Updated during `refresh()` operations
- Cleared after mutating operations
- Thread-safety: Not thread-safe (single IDE thread)
- Size: Grows with repository file count

## Integration Points

### Dulwich Library

**Integration Method:** Direct API calls via `dulwich.porcelain` module.

**Key Operations:**
- `porcelain.status()`: Get working tree status
- `porcelain.add()`: Stage files
- `porcelain.reset()`: Unstage files
- `porcelain.commit()`: Create commits
- `Repo()`: Repository object access

**Error Handling:** Dulwich exceptions are caught and logged via `log()` method.

### SCADE Project System

**Integration:** GitClient receives SCADE project paths and operates on associated repository.

**Workflow:**
```
SCADE IDE → GitExtension → GitClient → Dulwich → .git/
```

**Path Handling:**
- SCADE uses absolute paths
- Git uses repository-relative paths
- Conversion happens in GitClient methods

## Performance Considerations

### Optimization Strategies

1. **Status Caching**: Avoid repeated git status queries
2. **Batch Operations**: Group file operations when possible
3. **Lazy Loading**: Don't load file contents unnecessarily
4. **Path Normalization**: Cache normalized paths to avoid repeated conversions

### Performance Characteristics

- **Repository Discovery**: O(depth) where depth is directory tree depth
- **Status Refresh**: O(n) where n is number of tracked files
- **Stage/Unstage**: O(m) where m is number of files in operation
- **Commit**: O(n + m) where n is staged files, m is tree depth

### Scalability Limits

- Tested with repositories up to 1000 files
- Performance degrades linearly with file count
- Large binary files may slow operations
- Recommended: Use `.gitignore` for build outputs

## Error Handling

### Error Categories

1. **Initialization Errors**
   - Dulwich version mismatch → turn off extension, log error
   - Repository not found → Return empty status, log info

2. **Operation Errors**
   - File outside repository → Mark as extern, continue
   - Permission denied → Log error, skip file
   - Disk full → Fail operation, rollback if possible

3. **State Errors**
   - Merge conflicts → turn off certain operations, show warning
   - Detached HEAD → Allow read operations, warn on write
   - Corrupt repository → turn off extension, suggest repair

### Error Reporting

**Strategy:** All errors logged via abstract `log()` method.

**Levels:**
- Info: Repository not found, no changes to commit
- Warning: File skipped, operation partially succeeded
- Error: Operation failed, extension turn off

## Testing Strategy

### Unit Tests

**Location:** `tests/extension/test_gitclient.py`

**Coverage:**
- Repository discovery with various directory structures
- Status calculation for all GitStatus enum values
- Stage/unstage/commit operations
- Error conditions (missing repo, bad paths, etc.)
- Mock Dulwich to test GitClient logic independently

### Integration Tests

**Scenarios:**
- Real Git repository operations
- Multi-file staging and commits
- Branch operations
- Conflict scenarios

### Test Repositories

Use fixture repositories with known states:
- Empty repository
- Repository with staged changes
- Repository with conflicts
- Repository with submodules

## Future Enhancements

1. **Branch Operations**: Switch branches, create/delete branches
2. **Remote Operations**: Push, pull, fetch
3. **Diff Viewing**: Show file diffs in IDE
4. **Conflict Resolution**: Integrated merge conflict UI
5. **History Browsing**: View commit history, checkout specific commits
6. **Performance**: Parallel status checks for large repositories
7. **Git LFS Support**: Handle large file storage
8. **Submodule Support**: Better integration with submodules

## Dependencies

### Required
- `dulwich >= 0.21.3`: Pure-Python Git implementation
- `Python >= 3.7`: Minimum Python version

### Optional
- SCADE API: For IDE integration (not required for command-line tool usage)

## Security Considerations

1. **Path Traversal**: Validate all file paths stay within repository
2. **Command Injection**: Use Dulwich API (no shell commands)
3. **Credentials**: Never log or expose Git credentials
4. **Permissions**: Respect file system permissions
5. **Binary Safety**: Handle binary files safely (no content parsing)

## References

- [Dulwich Documentation](https://www.dulwich.io/docs/)
- [Git Internals](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
- SCADE Python API Documentation
