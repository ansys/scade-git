# ETP Merge Tool Design Document

## Component Overview

**Component:** ETP Three-Way Merge Tool  
**Module:** `ansys.scade.git.etpmerge`  
**Primary Files:**
- `src/ansys/scade/git/etpmerge/etpmerge3.py` - Main merge algorithm
- `src/ansys/scade/git/etpmerge/cache.py` - Entity caching and base resolution
- `src/ansys/scade/git/etpmerge/visitor.py` - Project tree traversal
- `src/ansys/scade/git/etpmerge/fi.py` - File manipulation operations
- `src/ansys/scade/git/etpmerge/utils.py` - Utility functions

**Purpose:** Perform intelligent three-way merges of SCADE project files (.etp) during Git merge operations, automatically resolving conflicts when possible and reporting unresolvable conflicts.

## Responsibilities

1. **Three-Way Merge**: Merge changes from two branches using a common ancestor
2. **Conflict Detection**: Identify conflicting changes between local and remote branches
3. **Automatic Resolution**: Resolve non-conflicting changes automatically
4. **Entity Tracking**: Map entities across three project versions using IDs
5. **Hierarchy Management**: Merge folder structures and file references
6. **Property Merging**: Merge configuration-specific properties
7. **Conflict Reporting**: Generate detailed conflict reports for manual resolution

## Background: SCADE Project Files

### ETP File Structure

SCADE project files (.etp) are XML-based files that define:
- **Project metadata**: Name, version, configurations
- **Folder hierarchy**: Logical organization of files
- **File references**: References to .xscade model files, .ann files, etc.
- **Configurations**: Build configurations (Debug, Release, etc.)
- **Properties**: Configuration-specific settings
- **Unique IDs**: Every entity has a persistent numeric ID

### Why Custom Merge Tool?

**Problem:** Standard Git merge treats .etp files as text, which fails because:
1. **Structural semantics**: XML structure has meaning beyond text
2. **ID-based references**: Entities reference each other by ID, not position
3. **Move operations**: Moving files between folders changes XML structure
4. **Configuration complexity**: Same property can exist in multiple configs
5. **Conflict ambiguity**: Text conflicts don't indicate semantic conflicts

**Solution:** ETPMerge3 understands SCADE semantics and merges at entity level.

### Example Merge Scenario

**Base Project:**
```xml
<Project id="1">
  <Folder name="Models" id="10">
    <FileRef pathname="model1.xscade" id="100"/>
  </Folder>
</Project>
```

**Local (moved file):**
```xml
<Project id="1">
  <Folder name="Models" id="10"/>
  <Folder name="Core" id="11">
    <FileRef pathname="model1.xscade" id="100"/>
  </Folder>
</Project>
```

**Remote (modified property):**
```xml
<Project id="1">
  <Folder name="Models" id="10">
    <FileRef pathname="model1.xscade" id="100">
      <Prop name="checked" value="true" config="1"/>
    </FileRef>
  </Folder>
</Project>
```

**Merged Result (both changes applied):**
```xml
<Project id="1">
  <Folder name="Models" id="10"/>
  <Folder name="Core" id="11">
    <FileRef pathname="model1.xscade" id="100">
      <Prop name="checked" value="true" config="1"/>
    </FileRef>
  </Folder>
</Project>
```

## Architecture

### Component Structure

```
ETPMerge3 (Main Algorithm)
    │
    ├──> CacheMaps (Build ID mappings)
    ├──> CacheBase (Resolve base entities)
    │
    ├──> merge_configurations()
    ├──> merge_folders() [Recursive]
    ├──> merge_file_refs()
    ├──> merge_properties() [Recursive]
    │
    └──> Conflict Detection & Reporting

Visit (Base Visitor Pattern)
    ├── CacheMaps : Visit
    └── CacheBase : Visit

FileInfo Module (fi.py)
    ├── copy_configuration()
    ├── copy_folder()
    ├── copy_file_ref()
    ├── copy_prop()
    ├── delete_configuration()
    ├── delete_folder()
    ├── delete_file_ref()
    └── delete_prop()
```

### Data Flow

```
Git Merge Process
    │
    ├─> Extract: local.etp, remote.etp, base.etp
    │
    ▼
Load SCADE Projects (SCADE API)
    │
    ├─> local: Project
    ├─> remote: Project
    └─> base: Project
    │
    ▼
Cache Phase
    │
    ├─> CacheMaps(local) → Build ID/name dictionaries
    ├─> CacheMaps(remote) → Build ID/name dictionaries
    ├─> CacheMaps(base) → Build ID/name dictionaries
    │
    ├─> CacheBase(base).visit(local) → Link local → base
    └─> CacheBase(base).visit(remote) → Link remote → base
    │
    ▼
Merge Phase
    │
    ├─> merge_configurations()
    ├─> merge_folders(remote) [Recursive]
    ├─> merge_file_refs()
    └─> merge_properties(remote) [Recursive]
    │
    ▼
Save & Report
    │
    ├─> Save merged project to local.etp
    └─> Return conflicts list
```

## Key Design Decisions

### 1. Three-Way Merge Strategy

**Decision:** Use ID-based entity tracking with common ancestor (base).

**Algorithm:**
```
FOR EACH entity in remote:
    base_entity = find_base_by_id(entity.id)
    
    IF base_entity exists:
        # Entity existed in base
        local_entity = find_local_by_id(base_entity.id)
        
        IF local_entity exists:
            # Modified in both → Merge or conflict
            merge_entity(local_entity, entity, base_entity)
        ELSE:
            # Deleted locally, modified remotely → Conflict
            report_conflict("Deleted locally, modified remotely")
    ELSE:
        # Created in remote
        local_entity = find_local_by_name(entity.name)
        
        IF local_entity exists AND local_entity._base is None:
            # Created in both with same name → Conflict
            report_conflict("Created in both branches")
        ELSE:
            # Created only in remote → Add to local
            copy_entity(entity, local)
```

**Rationale:**
- IDs persist across renames and moves
- Common ancestor distinguishes "added" from "no change"
- Name-based fallback handles cut/paste scenarios
- Follows Git's three-way merge philosophy

### 2. Caching Strategy

**Decision:** Pre-build comprehensive lookup dictionaries before merging.

**Cache Structures:**

```python
# Project-level caches
project._map_ids = {
    1: <Project>,
    10: <Folder "Models">,
    100: <FileRef "model1.xscade">,
    # id → entity
}

project._map_files = {
    'model1.xscade': <FileRef>,
    'path/to/model2.xscade': <FileRef>,
    # pathname → FileRef
}

project._folders = [
    <Folder "Models">,
    <Folder "Tests">,
    # List of all folders (for deletion)
]

# Folder-level caches
folder._map_folders = {
    'SubFolder': <Folder>,
    # name → child Folder
}

# Annotable-level caches
entity._map_props = {
    ('checked', 1): <Prop>,  # (name, config_id) → Prop
    ('optimize', 2): <Prop>,
}

# Project-level configuration cache
project._map_configurations = {
    'Debug': <Configuration>,
    'Release': <Configuration>,
}

# Base linkage (added during CacheBase visit)
entity._base = <corresponding base entity>
entity._local = <corresponding local entity>
```

**Rationale:**
- O(1) lookup instead of O(n) search
- Enables efficient conflict detection
- Supports multiple merge strategies (by ID, by name)
- Visitor pattern ensures all entities cached

**Trade-offs:**
- Increased memory usage
- Upfront traversal cost
- But: Merge algorithm much faster overall

### 3. Visitor Pattern for Tree Traversal

**Decision:** Use Visitor pattern for traversing SCADE project tree.

**Implementation:**
```python
class Visit:
    def visit(self, project_entity):
        # Dynamic dispatch to appropriate visit method
        fct = getattr(type(self), _map_visit_functions[type(project_entity)])
        fct(self, project_entity)
    
    def visit_project(self, project):
        # Process project-level attributes
        for configuration in project.configurations:
            self.visit(configuration)
        for root in project.roots:
            self.visit(root)
    
    def visit_folder(self, folder):
        # Process folder
        for element in folder.elements:
            self.visit(element)
    
    # ... other visit methods
```

**Rationale:**
- Separation of concerns: traversal vs. processing
- Reusable for different operations (cache, merge, validate)
- Type-safe dispatch via dictionary
- Extensible for new entity types

**Visitor Implementations:**
- `CacheMaps`: Build lookup dictionaries
- `CacheBase`: Link entities to base version

### 4. Conflict Detection and Reporting

**Decision:** Detect conflicts during merge and collect detailed reports.

**Conflict Types:**

1. **Delete-Modify Conflict**
   ```
   Context: FileRef "model.xscade" (id=100)
   → local: <deleted>
   → remote: <modified property>
   ```

2. **Modify-Modify Conflict**
   ```
   Context: Property "checked" in FileRef "model.xscade"
   → local: value="true"
   → remote: value="false"
   ```

3. **Add-Add Conflict**
   ```
   Context: Folder "NewFolder"
   → local: <created with id=50>
   → remote: <created with id=51>
   ```

4. **Rename-Rename Conflict**
   ```
   Context: Folder (id=10)
   → local: name="Models"
   → remote: name="Source"
   ```

**Conflict Representation:**
```python
conflicts = [
    (context, local_change, remote_change),
    # Example:
    ("FileRef 'model.xscade' (id=100)", 
     "→ local: deleted", 
     "→ remote: property 'checked' added")
]
```

**Reporting:**
- Conflicts saved to `.etp.conflicts` file
- Format: Human-readable text
- Includes context, local state, remote state
- Guides manual resolution

**Resolution Strategy:**
When conflict detected:
1. Keep local version (conservative approach)
2. Add conflict to report
3. Continue merging other entities
4. Return success=False if any conflicts

### 5. Entity Lifecycle Operations

**Decision:** Encapsulate all entity manipulation in `fi.py` module.

**Operations:**

```python
# Copy operations (remote → local)
copy_configuration(config, project) → new Configuration
copy_folder(folder, owner) → new Folder
copy_file_ref(file_ref, owner) → new FileRef
copy_prop(prop, entity) → new Prop

# Delete operations
delete_configuration(config)
delete_folder(folder)
delete_file_ref(file_ref)
delete_prop(prop)
```

**Design Principles:**
- Atomic operations
- Set `_base` and `_local` linkages
- Copy properties recursively
- Use SCADE API for safe manipulation
- Handle ownership correctly

**Example:**
```python
def copy_folder(folder, owner):
    copy = create_folder(owner, folder.name, extensions=folder.extensions)
    copy._base = folder._base
    folder._local = copy
    for prop in folder.props:
        copy_prop(prop, copy)
    copy._map_folders = {}
    copy._map_props = {}
    return copy
```

### 6. Recursive Merge Strategy

**Decision:** Merge hierarchically: Configurations → Folders → Files → Properties.

**Merge Order:**

1. **Configurations** (top-level)
   - Independent of file structure
   - Needed before property merges
   
2. **Folders** (recursive, depth-first)
   - Establish hierarchy first
   - Creates folders before adding files
   
3. **File References**
   - Add/delete files after folder structure ready
   - Move files to correct folders
   
4. **Properties** (recursive)
   - Merge after all entities exist
   - Configuration references must be valid

**Rationale:**
- Dependencies: Properties reference configurations
- Integrity: Files need folders to exist
- Efficiency: Single pass per entity type

## Algorithms

### Main Merge Algorithm

**Function:** `EtpMerge3._merge3()`

**Purpose:** Coordinate all merge operations.

**Preconditions:**
- Three projects loaded: local, remote, base
- Cache phase completed

**Algorithm:**
```
1. Cache entity mappings:
   CacheMaps().visit(local)
   CacheMaps().visit(remote)
   CacheMaps().visit(base)
   CacheBase(base).visit(local)
   CacheBase(base).visit(remote)

2. Merge configurations:
   FOR EACH remote_config:
       IF remote_config._base exists:
           # Modified or deleted
           local_config = find_by_id(remote_config._base.id)
           IF local_config exists:
               merge_attributes(remote_config, local_config)
           ELSE:
               # Deleted locally → conflict or accept deletion
       ELSE:
           # Added in remote
           IF not exists_by_name(remote_config.name):
               copy_configuration(remote_config, local)
           ELSE:
               # Added in both → conflict

3. Merge folder hierarchy (recursive):
   local_folders = merge_folders(remote)
   
4. Delete obsolete folders:
   FOR EACH local_folder:
       IF local_folder not in local_folders AND local_folder._base exists:
           delete_folder(local_folder)

5. Merge file references:
   merge_file_refs()

6. Merge properties (recursive):
   merge_properties(remote)
```

**Postconditions:**
- Local project contains merged changes
- Conflicts list populated
- Local project ready to save

### Folder Merge Algorithm

**Function:** `EtpMerge3.merge_folders(remote_owner)`

**Purpose:** Recursively merge folder hierarchy.

**Algorithm:**
```
merge_folders(remote_owner) → Set[local_folders]:
    locals = Set()
    
    FOR EACH remote_folder IN remote_owner.folders (sorted by name):
        # Resolve local folder
        IF remote_folder._base exists:
            local_folder = find_local_by_id(remote_folder._base.id)
            IF not local_folder:
                # Try by name (cut/paste case)
                local_folder = find_local_by_name(remote_folder.name)
        ELSE:
            # Created in remote
            local_folder = find_local_by_name(remote_folder.name)
        
        # Apply changes
        IF local_folder exists:
            # Link remote to local
            remote_folder._local = local_folder
            locals.add(local_folder)
            
            # Merge attributes
            IF remote_folder.name != local_folder.name:
                IF local_folder._base.name == local_folder.name:
                    # Only remote renamed → accept
                    local_folder.name = remote_folder.name
                ELIF local_folder._base.name == remote_folder.name:
                    # Only local renamed → keep local
                    pass
                ELSE:
                    # Both renamed → conflict
                    report_conflict(...)
            
            # Recurse into subfolders
            child_locals = merge_folders(remote_folder)
            locals.update(child_locals)
        ELSE:
            # Folder only in remote (or deleted locally)
            IF remote_folder._base:
                # Deleted locally, modified remotely
                remote_folder._local = None
                # Could report conflict or accept deletion
            ELSE:
                # Created in remote → copy
                local_folder = copy_folder(remote_folder, owner)
                locals.add(local_folder)
                # Recurse to copy children
                merge_folders(remote_folder)
    
    RETURN locals
```

**Recursion:** Depth-first traversal ensures parent folders created before children.

**Return Value:** Set of local folders that have corresponding remote folders (used for deletion detection).

### File Reference Merge Algorithm

**Function:** `EtpMerge3.merge_file_refs()`

**Purpose:** Merge file references across all folders.

**Algorithm:**
```
FOR EACH remote_folder IN remote.all_folders:
    local_folder = remote_folder._local
    
    IF local_folder is None:
        # Folder deleted locally, skip files
        CONTINUE
    
    FOR EACH remote_file IN remote_folder.file_refs:
        # Resolve local file
        IF remote_file._base exists:
            local_file = find_local_by_id(remote_file._base.id)
            IF not local_file:
                # Try by pathname
                local_file = find_local_by_pathname(remote_file.pathname)
        ELSE:
            # Created in remote
            local_file = find_local_by_pathname(remote_file.pathname)
        
        # Apply changes
        IF local_file exists:
            # Link
            remote_file._local = local_file
            
            # Check if moved
            IF local_file.owner != local_folder:
                # File moved
                IF local_file._base.owner == local_file.owner:
                    # Only remote moved → move local
                    move_file(local_file, local_folder)
                ELIF local_file._base.owner == local_folder:
                    # Only local moved → keep local
                    pass
                ELSE:
                    # Both moved to different locations → conflict
                    report_conflict(...)
            
            # Merge pathname
            merge_attribute(remote_file, local_file, 'pathname')
            
            # Merge other attributes
            merge_attribute(remote_file, local_file, 'persist_as')
            # ... etc
        ELSE:
            # File added in remote or deleted locally
            IF remote_file._base:
                # Deleted locally
                remote_file._local = None
            ELSE:
                # Added in remote → copy
                copy_file_ref(remote_file, local_folder)
    
    # Handle deletions
    FOR EACH local_file IN local_folder.file_refs:
        IF local_file._base exists:
            remote_file = find_remote_by_id(local_file._base.id)
            IF not remote_file:
                # Deleted in remote → delete locally
                delete_file_ref(local_file)
```

### Property Merge Algorithm

**Function:** `EtpMerge3.merge_properties(remote_entity)`

**Purpose:** Recursively merge configuration-specific properties.

**Algorithm:**
```
merge_properties(remote_entity):
    local_entity = remote_entity._local
    
    IF local_entity is None:
        RETURN  # Entity deleted locally
    
    FOR EACH remote_prop IN remote_entity.props:
        prop_key = (remote_prop.name, remote_prop.configuration.id)
        
        # Resolve local property
        IF remote_prop._base exists:
            local_prop = find_local_by_id(remote_prop._base.id)
            IF not local_prop:
                local_prop = local_entity._map_props.get(prop_key)
        ELSE:
            # Created in remote
            local_prop = local_entity._map_props.get(prop_key)
        
        # Apply changes
        IF local_prop exists:
            # Merge value
            IF remote_prop.value != local_prop.value:
                IF local_prop._base.value == local_prop.value:
                    # Only remote changed → accept remote
                    local_prop.value = remote_prop.value
                ELIF local_prop._base.value == remote_prop.value:
                    # Only local changed → keep local
                    pass
                ELSE:
                    # Both changed → conflict
                    report_conflict(...)
        ELSE:
            # Property added in remote or deleted locally
            IF remote_prop._base:
                # Deleted locally → conflict?
                pass
            ELSE:
                # Added in remote → copy
                copy_prop(remote_prop, local_entity)
    
    # Handle deletions
    FOR EACH local_prop IN local_entity.props:
        IF local_prop._base exists:
            remote_prop = find_remote_by_id(local_prop._base.id)
            IF not remote_prop:
                # Deleted in remote → delete locally
                delete_prop(local_prop)
    
    # Recurse for entities with children
    IF remote_entity is Folder:
        FOR EACH remote_child IN remote_entity.elements:
            merge_properties(remote_child)
```

### Attribute Merge Helper

**Function:** `merge_attribute(remote, local, attr_name)`

**Purpose:** Three-way merge of a single attribute.

**Algorithm:**
```
merge_attribute(remote, local, attr_name):
    remote_value = getattr(remote, attr_name)
    local_value = getattr(local, attr_name)
    base_value = getattr(remote._base, attr_name)
    
    IF remote_value == local_value:
        # No conflict (same or both unchanged)
        RETURN
    
    IF base_value == local_value:
        # Only remote changed
        setattr(local, attr_name, remote_value)
    ELIF base_value == remote_value:
        # Only local changed → keep local
        pass
    ELSE:
        # Both changed differently → conflict
        report_conflict(
            f"{remote.type} '{get_name(remote)}' attribute '{attr_name}'",
            f"→ local: {local_value}",
            f"→ remote: {remote_value}"
        )
```

## Data Structures

### Entity Augmentation

During cache phase, entities are augmented with additional attributes:

```python
# All ProjectEntity instances
entity._base: Optional[ProjectEntity]    # Corresponding base entity
entity._local: Optional[ProjectEntity]   # For remote: corresponding local entity

# Project instances
project._map_ids: Dict[int, ProjectEntity]
project._map_files: Dict[str, FileRef]
project._folders: List[Folder]
project._map_configurations: Dict[str, Configuration]

# Folder instances
folder._map_folders: Dict[str, Folder]

# Annotable instances (Project, Folder, FileRef)
annotable._map_props: Dict[Tuple[str, int], Prop]
    # Key: (property_name, configuration_id)
```

### Conflict Structure

```python
conflicts: List[Tuple[str, str, str]] = [
    (context_description, local_state, remote_state),
    # Example:
    ("FileRef 'model.xscade' (id=100) property 'checked'",
     "→ local: value='true'",
     "→ remote: value='false'"),
]
```

## Error Handling

### Error Categories

1. **WrongBaseError**
   - Raised when projects don't share common ancestor
   - Detected: Entity with same ID has different type in base
   - Handling: Report as conflict, suggest manual merge

2. **Structural Errors**
   - Missing owner for entity
   - Circular folder references
   - Duplicate IDs
   - Handling: Log error, skip entity, continue

3. **API Errors**
   - SCADE API exceptions during create/delete
   - File I/O errors during save
   - Handling: Catch, log, report as conflict

4. **Unexpected Errors**
   - Any uncaught exception
   - Handling: Catch at top level, report as conflict with traceback

### Error Recovery

```python
def merge3(self, pathname: str) -> bool:
    try:
        self._merge3()
    except WrongBaseError as e:
        context = f'Merge error: Projects do not share common ancestor (id {e.project_entity.id})'
        self.conflicts.append((context, '→ local <unchanged>', '→ remote <ignored>'))
    except BaseException as e:
        context = f'Internal merge error: {str(e)}'
        context += '\nManual merge required\n'
        context += traceback.format_exc()
        self.conflicts.append((context, '→ local <unknown>', '→ remote <unknown>'))
    
    self.save(pathname)
    return len(self.conflicts) == 0
```

**Philosophy:** Never fail completely. Always produce an output file, even if conflicts exist.

## Integration with Git

### Git Merge Driver Configuration

**`.gitattributes` entry:**
```
*.etp merge=etpmerge
```

**`.git/config` entry:**
```ini
[merge "etpmerge"]
    name = SCADE ETP Merge Driver
    driver = python -m ansys.scade.git.etpmerge %O %A %B %P
```

**Parameters:**
- `%O`: Base version (common ancestor)
- `%A`: Local version (current branch)
- `%B`: Remote version (branch being merged)
- `%P`: Output path (merged result)

### Invocation Flow

```
Git detects merge conflict in file.etp
    ↓
Git extracts: base.etp, local.etp, remote.etp
    ↓
Git invokes: python -m ansys.scade.git.etpmerge base local remote output
    ↓
etpmerge3.py loads projects via SCADE API
    ↓
Performs three-way merge
    ↓
Saves result to output path
    ↓
Returns exit code:
    0 = success (no conflicts)
    1 = conflicts detected (manual resolution needed)
    ↓
If conflicts:
    Git marks file as conflicted
    Creates .etp.conflicts file
    User must manually resolve
```

## Performance Considerations

### Optimization Strategies

1. **Single-Pass Caching**: Build all lookup dictionaries in one traversal
2. **Lazy Property Access**: Don't process properties until needed
3. **Sorted Iteration**: Process entities in sorted order for stable output
4. **Minimal Object Creation**: Reuse local objects when possible

### Performance Characteristics

- **Cache Phase**: O(n) where n = total entities across all three projects
- **Merge Phase**: O(n) amortized (O(1) lookups via dictionaries)
- **Save Phase**: O(n) (SCADE API serialization)
- **Overall**: O(n) linear in number of entities

### Scalability Limits

- **Entities**: Tested with projects up to 10,000 entities
- **Depth**: Tested with folder depth up to 20 levels
- **Properties**: Tested with up to 1,000 properties per entity
- **Memory**: ~1MB per 1,000 entities (cached)

## Testing Strategy

### Unit Tests

**Location:** `tests/etpmerge/test_merge.py`

**Test Categories:**

1. **Cache Tests**
   - Verify ID mappings built correctly
   - Verify base linkage established
   - Test with missing entities
   
2. **Configuration Merge Tests**
   - Add configuration in remote
   - Delete configuration in local
   - Rename configuration in both
   
3. **Folder Merge Tests**
   - Create folder in remote
   - Move folder in local
   - Rename folder in both
   - Delete folder in one branch
   
4. **File Merge Tests**
   - Add file in remote
   - Delete file in local
   - Move file between folders
   - Modify file properties
   
5. **Property Merge Tests**
   - Modify property value
   - Add property in remote
   - Delete property in local
   - Change property in both
   
6. **Conflict Tests**
   - Delete-modify conflicts
   - Rename-rename conflicts
   - Move-move conflicts
   - Value-value conflicts

### Integration Tests

**Test Repositories:** `tests/etpmerge/resources/`

Each test case is a directory with:
- `base.etp`: Common ancestor
- `local.etp`: Local version
- `remote.etp`: Remote version
- `expected.etp`: Expected merge result
- `expected.conflicts`: Expected conflict report (if any)

**Test Scenarios:**
1. **Nominal**: Simple non-conflicting changes
2. **Advanced**: Complex hierarchy changes
3. **Configurations**: Multiple configurations with properties
4. **Conflicts**: Various conflict types
5. **Edge Cases**: Empty projects, single file, deep hierarchy

### Test Execution

```python
def test_merge_case(case_dir):
    # Load projects
    base = load_project(case_dir / 'base.etp')
    local = load_project(case_dir / 'local.etp')
    remote = load_project(case_dir / 'remote.etp')
    
    # Perform merge
    merger = EtpMerge3(local, remote, base)
    success = merger.merge3(case_dir / 'result.etp')
    
    # Validate
    expected = load_project(case_dir / 'expected.etp')
    assert projects_equal(local, expected)
    
    if (case_dir / 'expected.conflicts').exists():
        assert not success
        assert conflicts_match(merger.conflicts, case_dir / 'expected.conflicts')
    else:
        assert success
```

## Future Enhancements

1. **Interactive Conflict Resolution**
   - GUI for resolving conflicts
   - Preview merge results before applying
   - Accept local/remote for specific conflicts

2. **Semantic Merging**
   - Merge SCADE model files (.xscade) semantically
   - Detect semantic conflicts (e.g., type mismatches)
   - Integrate with SCADE Suite diff tools

3. **Performance Improvements**
   - Incremental merging (only changed entities)
   - Parallel caching for large projects
   - Streaming for very large projects

4. **Enhanced Conflict Detection**
   - Detect dependent changes (e.g., rename + references)
   - Suggest automatic resolutions
   - Rank conflicts by severity

5. **Merge History**
   - Track merge decisions for repeat scenarios
   - Learn from user's conflict resolutions
   - Suggest similar resolutions

## Dependencies

### Required
- `scade.model.project.stdproject`: SCADE Project API
- `ansys.scade.apitools.create`: Entity creation utilities
- Python standard library: `os`, `pathlib`, `traceback`

### SCADE API Integration

**Key APIs Used:**
```python
import scade.model.project.stdproject as std

# Entity types
std.Project, std.Folder, std.FileRef
std.Configuration, std.Prop
std.Element, std.Annotable, std.ProjectEntity

# Relationships
project.roots → List[Element]
project.configurations → List[Configuration]
folder.elements → List[Element]
entity.props → List[Prop]

# Attributes
entity.id → int (unique identifier)
entity.name → str
file_ref.pathname → str
prop.value → str
```

## Security Considerations

1. **Path Validation**: Ensure file paths stay within repository
2. **ID Validation**: Verify entity IDs are valid integers
3. **Circular References**: Detect and prevent circular folder structures
4. **Resource Limits**: Prevent excessive memory usage on malicious inputs
5. **XML Safety**: Use SCADE API (no direct XML parsing)

## References

- [Three-Way Merge Algorithm](https://en.wikipedia.org/wiki/Merge_(version_control)#Three-way_merge)
- [Git Merge Drivers](https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver)
- SCADE Python API Documentation
- Design Document: `01_git_client.md`
- Design Document: `02_gui_extension.md`
