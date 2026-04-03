# Loreo Forge

Loreo Forge is a PyQt5 desktop application for AI-assisted story creation, editing, and project management. It integrates a local Ollama LLM client for generation tasks, uses SQLite for per-story persistence, and provides modular views, controllers, and utilities.

This README reflects the repository files present in this workspace and describes their roles. Any file not present in the workspace is intentionally omitted.

Key changes and highlights (from current codebase)
- Added a dedicated Chapter-by-Parts generator view and UI wiring (`ui/views/chapter_parts_generator_view.py`, registered in `ui/views/__init__.py`).
- Theme engine and runtime theme switching via `ui/theme_engine.py`.
- Enhanced AI stack:
  - Streaming-supporting Ollama client (`ai/ollama_client.py`).
  - Token-aware context manager (`ai/context_manager.py`) and Jinja2 `PromptBuilder` (`ai/prompt_builder.py`).
  - Prompt templates under `ai/templates/` (chapter, outline, world-building templates).
- Increased generation token limits and updated model defaults in `config/default_settings.yaml`, `config/models.yaml`, and `config/settings.py`.
- Migration scripts to update existing story databases: `migrate_database.py` and `migrate_timeline_and_selective_editing.py`.
- Robust diagnostics and verification scripts: `verify_views.py` and `utils/diagnose_views.py`.

Top-level files
- `main.py` — Application entrypoint and startup diagnostics (dependency and Ollama checks, directory setup, logger/init, database migration hooks, and launching the GUI).
- `check_dependencies.py` — Simple dependency check utility.
- `migrate_database.py` — Migration helper to add missing columns to existing story DBs.
- `migrate_timeline_and_selective_editing.py` — Adds timeline support and selective-editing columns.
- `verify_views.py` — View verification script that tests imports and common initialization issues.
- `requirements.txt` — Project Python dependencies.

Package and directory overview (files included in this workspace)

- `ai/` — AI integration
  - `__init__.py` — package exports for AI components.
  - `exceptions.py` — AI-specific exception types (connection, model not found, timeouts, context limits, invalid prompts).
  - `ollama_client.py` — Ollama HTTP client with streaming and retry logic.
  - `context_manager.py` — Builds and optimizes context pulled from the database for generation requests.
  - `prompt_builder.py` — Jinja2-based prompt templating and validation.
  - `templates/` — Jinja2 templates: `chapter_generation.txt`, `outline_generation.txt`, `world_building.txt`, `character_expansion.txt`.

- `config/` — Settings and configuration
  - `__init__.py` — exposes `settings` instance.
  - `settings.py` — Application settings manager; contains updated defaults (token limits, model defaults, UI defaults).
  - `default_settings.yaml` — Default configuration (includes AI defaults and generation parameters).
  - `user_settings.yaml` — User overrides persisted on disk.
  - `models.yaml` — Named model presets and recommended parameters.

- `core/` — Application core
  - `application.py` — `LoreoForgeApp`: QApplication subclass for initialization, theme and font setup.
  - `story_manager.py` — Story registry and per-story lifecycle management (creation, activation, deletion including physical DB deletion).

- `controllers/` — Controllers bridging UI and business logic
  - `ai_controller.py` — Coordinates generation requests: context gathering, prompt building, Ollama calls, streaming results to UI; includes background worker thread.
  - `story_controller.py` — Story CRUD operations and signals.

- `database/` — Persistence layer
  - `__init__.py` — exports for database API.
  - `db_manager.py` — `DatabaseManager` providing connection pooling, CRUD, transactions, and AI-oriented queries.
  - `master_db.py` — Master registry database (`loreo_master.db`) and management.
  - `schema.py` — Schema definitions for master and per-story DBs.
  - `migrations.py` — Migration helper used by the migration scripts.

- `models/` — Domain models
  - `__init__.py` — model exports.
  - `base.py` — `BaseModel` ORM-like base with serialization and change tracking.
  - `story.py`, `chapter.py`, `character.py`, `creature.py`, `location.py`, `arc.py`, `item.py`, `lore.py`, `organization.py`, `power_system.py`, `creature.py`, `timeline_state.py` — domain entity classes used across UI and AI.

- `ui/` — User interface
  - `main_window.py` — Main application window wiring (menu, toolbar, sidebar, view stack); imports `ChapterPartsGeneratorView` and integrates theme engine.
  - `theme_engine.py` — Theme and stylesheet management.
  - `components/` — Reusable controls
    - `__init__.py` — component exports.
    - `sidebar.py` — Navigation sidebar (now includes 'Chapter by Parts Generator' entry).
    - `search_widget.py` — Live search with autocomplete and navigation support.
  - `views/` — Application views (all inherit from `BaseView`):
    - `__init__.py` — registers available views (includes `ChapterPartsGeneratorView`).
    - `base_view.py` — shared view behaviour (CRUD helpers, validation, auto-save hooks).
    - `dashboard_view.py`, `story_view.py`, `characters_view.py`, `chapters_list_view.py`, `chapter_generator_view.py`, `chapter_parts_generator_view.py`, `world_view.py`, `lore_view.py`, `bestiary_view.py`, `organizations_view.py`, `items_view.py`, `powers_view.py`, `settings_view.py`.

- `utils/` — Utilities
  - `__init__.py` — exposes logging helpers.
  - `logger.py` — Centralized logging setup and `LoggerMixin`.
  - `exception_handler.py` — Application-level exception types and simple handler classes.
  - `diagnose_views.py` — View import and registration diagnostic script.

- `tests/` — Test suite (pytest/unittest mixed tests present)
  - `__init__.py`, `test_ai_client.py`, `test_database.py`, `test_main.py`, `test_models.py` — unit and integration tests for AI, database, main launcher, and models.

Runtime data and artifacts
- `data/stories/` (created at runtime) — per-story SQLite files, exports, and backups.
- `logs/` (created at runtime) — application logs managed by `utils/logger.py`.

Getting started (quick)
1. Create and activate a virtualenv:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Verify dependencies and run:

```powershell
python check_dependencies.py
python main.py
```

3. Run tests:

```powershell
pytest -q
```

If you'd like, I can run the test suite, open specific files to expand any section, or produce a concise CHANGELOG describing the notable diffs (token limits, new views, streaming support, migrations). 


### New Features & Enhancements

#### Core Application Features
- **Comprehensive Startup Diagnostics** (`main.py`)
  - Multi-phase startup sequence with detailed status reporting
  - Dependency verification with user-friendly feedback
  - Ollama connection validation with model availability checking
  - Directory structure initialization and validation
  - Database system operational testing
  
- **Database Migration Support** (`migrate_database.py`)
  - Automated schema updates for existing databases
  - Safe column additions without data loss
  - Multi-story database support with proper isolation
  - Automatic backup before migration operations

- **Robust View Validation** (`verify_views.py`)
  - Comprehensive view file existence checking
  - Import testing for all 11 views
  - Signal connection validation
  - Common issue detection with helpful diagnostics
  - Cross-platform compatibility verification

#### UI/View System (All 11 Views Complete)
- **Dashboard View**: Home screen with story overview, statistics, and quick actions
- **Story View**: Comprehensive story metadata editor with title, genre, synopsis, tone, and publication tracking
- **Characters View**: Full character CRUD with voice patterns, dialogue characteristics, arc stages, and appearance tracking
- **Chapters List View**: Chapter browser with complete metadata, arc association, POV character selection, and auto-save
- **Chapter Generator View**: AI-assisted chapter generation with streaming display, context selection, and editing capabilities
- **World View**: Location/place management with type classification, atmosphere, climate, and civilization levels
- **Lore View**: Lore entry organization with category-based structure, timeline connections, and cross-referencing
- **Bestiary View**: Creature database with comprehensive categorization, behavior, abilities, and environmental preferences
- **Organizations View**: Faction management with structure, hierarchy, member rosters, and alliance tracking
- **Powers View**: Magic systems and spells with mechanics, effects, rarity classification, and prerequisites
- **Settings View**: Application configuration for theme, AI models, generation parameters, and export preferences

#### Data Models (8 Complete Models)
- **Story Model**: Multi-arc story projects with complete metadata
- **Chapter Model**: Rich chapter management with arc/POV association and featured characters
- **Character Model**: Comprehensive character profiles with voice consistency tracking
- **Location Model**: Detailed world locations with climate and civilization tracking
- **Arc Model**: Plot structure with thematic elements and chapter markers
- **Lore Model**: World-building entries with categorization and timeline
- **Creature Model**: Bestiary entries with abilities, weaknesses, and environmental preferences
- **Organization Model**: Faction management with hierarchies and relationships

#### AI Integration Features
- **Context-Aware Generation**: Intelligent context gathering from database
- **Prompt Builder**: Jinja2-based templating with custom filters and validation
- **Multiple AI Templates**:
  - `outline_generation.txt`: Story outline creation with act structure
  - `chapter_generation.txt`: Chapter content with continuity maintenance
  - `character_expansion.txt`: Character detail development
  - `world_building.txt`: World element generation (culture, history, geography)

#### User Experience Enhancements
- **Edit Mode Toggles**: All views support edit/view mode for better UI clarity
- **Auto-Save Functionality**: Automatic saving on all data modifications
- **Form Validation**: Comprehensive input validation with user feedback
- **Streaming Generation Display**: Real-time AI output streaming in chapter generator
- **Multi-Story Management**: Seamless switching between story projects

### Implementation Completeness
- ✅ **11/11 UI Views** fully implemented with complete CRUD operations
- ✅ **8/8 Core Data Models** with comprehensive property support
- ✅ **Ollama Integration** with connection validation and model management
- ✅ **Database System** with per-story isolation and auto-initialization
- ✅ **Theme Engine** with multiple built-in themes and real-time switching
- ✅ **AI Generation** with prompt building and context management
- ✅ **Edit Mode** toggles across all views for better UX
- ✅ **Auto-Save** functionality throughout the application
- ✅ **Form Validation** and error handling on all inputs

---

## Project Structure & File Documentation

### Root Level Files

#### `main.py` (205 lines)
The primary application entry point implementing a comprehensive multi-phase startup sequence:

**Startup Phases:**
1. **Dependency Check** - Verifies PyQt5, requests, and PyYAML availability
2. **Directory Initialization** - Creates data structure with `config/`, `logs/`, `data/stories/`
3. **Logging Setup** - Initializes file and console logging with rotating handlers
4. **Ollama Connection Check** - Tests Ollama server connectivity and lists available models
5. **Database Initialization** - Tests master database and story database connectivity
6. **AI Client Testing** - Validates AI integration functionality
7. **PyQt5 Application Launch** - Initializes GUI with main window

**Key Functions:**
- `check_dependencies()` - Verifies critical Python packages
- `check_ollama_connection()` - Tests Ollama availability with model listing
- `main()` - Orchestrates startup sequence with diagnostic output

**Output:** Displays startup status with ✓/✗ indicators for each system component

#### `requirements.txt` (26 packages)
Organized Python package dependencies by functionality:

**UI & Display**
- `PyQt5>=5.15.9` - Desktop GUI framework
- Fonts and icons for UI theming

Loreo Forge is a desktop application for AI-assisted story creation, editing, and project management. It integrates a local Ollama LLM client for generation tasks, uses SQLite for per-story persistence, and provides a PyQt5 GUI with modular views and controllers.

This README summarizes the repository contents and describes the purpose of the top-level files and folders present in this workspace as of this commit. It excludes any files that are not present in the project tree.

Summary of top-level files
- `main.py` — Application entrypoint. Runs startup diagnostics (dependency checks, directory setup, logger initialization, Ollama connection check, and database initialization) and launches the PyQt5 application.
- `check_dependencies.py` — Standalone utility to verify required Python packages and provide pip-install suggestions for any missing dependencies.
- `migrate_database.py` — Script to apply safe schema migrations to per-story databases (backs up databases, checks `PRAGMA table_info`, and adds missing fields transactionally).
- `migrate_timeline_and_selective_editing.py` — Migration script for timeline / selective-editing related schema changes (keeps history and performs validation).
- `verify_views.py` — Diagnostic script that imports and validates UI view modules, checks signal connections, and reports common view initialization issues.
- `README.md` — This file.
- `requirements.txt` — Pin list of Python dependencies used by the project.

Package / directory overview

- `ai/` — AI integration layer
  - `__init__.py` — package marker and exports.
  - `context_manager.py` — Builds and selects relevant story context for generation requests, enforces token limits and relevance scoring.
  - `exceptions.py` — Custom exception hierarchy for AI and Ollama-related errors (e.g., `OllamaConnectionError`, `ModelNotFoundError`, `GenerationTimeoutError`).
  - `ollama_client.py` — Client wrapper around Ollama API: connection tests, model listing, streaming generation, retry logic, and health checks.
  - `prompt_builder.py` — Jinja2-based prompt construction and template caching with custom template filters and validation.
  - `templates/` — Prompt templates used by the `PromptBuilder` (outline, chapter, character, world-building templates).

- `config/` — Configuration and settings
  - `__init__.py` — exposes settings API.
  - `settings.py` — Settings manager: loads `default_settings.yaml` and `user_settings.yaml`, path resolution, and cross-platform directory initialization.
  - `default_settings.yaml` — Default application configuration values.
  - `user_settings.yaml` — User overrides persisted at runtime (created on first run).
  - `models.yaml` — Static model metadata (model capabilities, recommended parameters).

- `core/` — Core application logic and state
  - `application.py` — `LoreoForgeApp`: QApplication wrapper that handles lifecycle, font and theme initialization, and window management.
  - `story_manager.py` — Manages story projects, active-story context, and paths to per-story databases. Ensures per-story isolation and default story creation.

- `controllers/` — MVC controllers bridging UI and core logic
  - `ai_controller.py` — Coordinates generation requests: context assembly (`ContextManager`), prompt rendering (`PromptBuilder`), calls to `OllamaClient`, streaming to the UI, and cancellation.
  - `story_controller.py` — Story CRUD and activation signals.
  - (Other controllers present in the folder include `character_controller.py`, `chapter_controller.py`, `world_controller.py` — each provides domain CRUD + validation and database persistence.)

- `database/` — Data persistence and schema
  - `db_manager.py` — High-level database API for per-story databases: connection management, CRUD operations, transactions, and context queries used by AI context building.
  - `master_db.py` — Master registry (single SQLite) tracking created stories, active story, and global metadata.
  - `schema.py` — SQL schema definitions for master and per-story databases; includes table and index creation and recommended SQLite pragmas.
  - `migrations.py` — Migration helpers referenced by migration scripts.

- `models/` — Domain models
  - Common base and entity models: `base.py` (shared model behavior), `story.py`, `chapter.py`, `character.py`, `location.py`, `arc.py`, `lore.py`, `creature.py`, and `timeline_state.py`.
  - Each model implements serialization (`to_dict`/`from_dict`), property accessors, modified-state tracking, and validation.

- `ui/` — PyQt UI code
  - `main_window.py` — Main application window with menu, toolbar, status bar, content stack and view registration.
  - `theme_engine.py` — Theme loader and Qt stylesheet generator; handles built-in theme application and real-time switching.
  - `components/` — Reusable UI controls (e.g., `search_widget.py`, `sidebar.py`).
  - `views/` — View modules, each inheriting from a `BaseView` and implementing `setup_ui()`, `load_data()`, `save_data()`:
    - `dashboard_view.py`, `story_view.py`, `characters_view.py`, `chapters_list_view.py`, `chapter_generator_view.py`, `world_view.py`, `lore_view.py`, `bestiary_view.py`, `organizations_view.py`, `powers_view.py`, `settings_view.py`.

- `utils/` — Utilities
  - `logger.py` — Central logging setup with rotating file handler and `LoggerMixin` for classes.
  - `exception_handler.py` — Global exception handling and user-facing error dialogs.
  - `diagnose_views.py` — Helper to perform view import and registration checks.

- `data/` — Runtime data directory (created at runtime)
  - `stories/` — Per-story SQLite databases, export files, and backups.

- `tests/` — Pytest unit and integration tests
  - `test_main.py`, `test_models.py`, `test_database.py`, `test_ai_client.py` — focused tests for the major subsystems.

Development, running, and testing

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Quick checks and start:

```powershell
python check_dependencies.py
python main.py
```

3. Run tests with `pytest`:

```powershell
pytest -q
```

Design notes and conventions
- Per-story isolation: each story uses its own SQLite file under `data/stories/`; the `master_db` tracks story metadata.
- AI integration: `ai/` modules handle prompt building, token-aware context assembly, and robust Ollama interaction with streaming and retries.
- MVC pattern: views (UI) are thin and emit signals to controllers which perform validation and call core services (database, AI).

If you want, I can now run the tests or open any specific file to verify and expand any section further.
Database schema migration and update utility:

**Capabilities:**
- Detects existing databases in `data/stories/`
- Adds missing columns safely without data loss
- Tracks applied migrations with logging
- Creates automatic backups before updates
- Tests database integrity post-migration

**Migrations Provided:**
- `model_used` - Tracks which AI model generated content
- `edited` - Boolean flag for manual edits
- `generation_metadata` - JSON storage for generation parameters

**Usage:** `python migrate_database.py` - Automatically processes all story databases

**Safety Features:**
- PRAGMA table_info checks for existing columns
- Transactional updates with rollback support
- Backup creation before modifications
- Detailed success/failure reporting

#### `verify_views.py` (203 lines)
Comprehensive view validation and diagnostics tool:

**Verification Steps:**
1. **File Existence Check** - Confirms all 10 expected view files exist
2. **Import Testing** - Attempts to import each view class
3. **Signal Connection Validation** - Verifies proper PyQt5 signal setup
4. **View Registration Check** - Tests that views are registered in MainWindow
5. **Common Issue Detection** - Identifies 15+ common initialization problems
6. **Cross-Platform Testing** - Validates paths and imports on Windows/Linux/Mac

**Expected Views:**
- dashboard_view.py, story_view.py, characters_view.py, world_view.py
- bestiary_view.py, lore_view.py, powers_view.py, chapter_generator_view.py
- chapters_list_view.py, settings_view.py

**Usage:** `python verify_views.py`

**Output:** Detailed check results with ✓/✗ indicators and troubleshooting suggestions

**Benefits:**
- Quick view system health check
- Catch import errors before runtime
- Verify signal connections
- Identify path and configuration issues
- Useful after adding/modifying views

---

## Core Directories

### `ai/` - AI Integration Layer
Complete abstraction layer for local AI-powered content generation through Ollama.

#### Components

- **`ollama_client.py` (Main Client)**
  - **Connection Management**: `test_connection()` validates Ollama server availability
  - **Model Operations**: List available models, switch models, verify availability
  - **Content Generation**: Streaming support for real-time output, automatic retry logic
  - **Context Management**: Validates context length against model limits, handles overflow
  - **Metrics Tracking**: Records request count, token usage, generation time statistics
  - **Error Handling**: Specific exceptions for different failure modes
  - **Configuration**: Configurable timeouts (default 300s), retry policies, retry delays
  - **Status Checking**: Health checks with model information and capability detection
  
- **`context_manager.py` (Context Gathering)**
  - **Database Queries**: Retrieves story elements (characters, locations, chapters, arcs) for context
  - **Relevance Scoring**: Selects most important context within token limits
  - **Context Building**: Constructs narrative context from multiple database tables
  - **Token Optimization**: Estimates token usage and prioritizes important elements
  - **Custom Settings**: Supports specialized context gathering for different generation tasks
  - **Coherence Maintenance**: Ensures context consistency across multiple generation calls
  - **Cross-Reference Handling**: Maintains relationships between story elements in context
  
- **`prompt_builder.py` (Prompt Generation)**
  - **Jinja2 Templating**: Dynamic prompt construction with template variables
  - **Template Validation**: Pre-generation validation with helpful error messages
  - **In-Memory Registry**: Caches compiled templates for performance
  - **Custom Filters**: Text formatting, truncation, list structuring for clean prompts
  - **Variable Injection**: Context variables automatically injected into templates
  - **Error Handling**: Comprehensive error messages for template issues
  - **Template Functions**: Custom functions available within templates (date formatting, etc.)
  
- **`exceptions.py` (Error Hierarchy)**
  - `OllamaConnectionError` - Connection/network failures
  - `ModelNotFoundError` - Requested model unavailable
  - `GenerationTimeoutError` - Generation exceeds timeout threshold
  - `ContextLengthExceededError` - Context exceeds model token limit
  - `InvalidPromptError` - Prompt validation failures
  - `GenerationError` - Generic generation failures
  
- **`templates/` (Prompt Templates)**
  - **`outline_generation.txt`**: Story outline creation with three-act structure, chapter distribution
  - **`chapter_generation.txt`**: Chapter content with continuity, POV consistency, plot point integration
  - **`character_expansion.txt`**: Character detail development (background, motivations, voice)
  - **`world_building.txt`**: World element generation (cultures, history, geography, climate)
  - **Template Format**: Jinja2 with custom filters for clean output
  - **Variable Injection**: Models, characters, locations, previous content automatically available

### `config/` - Configuration Management
Centralized configuration system managing application settings, environment variables, and paths.

- **`__init__.py`**: Package initialization
- **`settings.py`**: Core settings manager providing:
  - Application metadata (name, version, organization)
  - Directory path management (data, stories, logs, assets, templates)
  - Default values for fonts, themes, and AI models
  - Database configuration and connection parameters
  - Ollama integration settings and timeout configurations
  - User settings loading from YAML with fallback to defaults
  - Directory creation and validation on initialization
  - Settings retrieval with type safety and default values
  - Path resolution for cross-platform compatibility
- **`default_settings.yaml`**: Default application configuration including:
  - Application metadata and versioning
  - Startup behavior (splash screen, update checks, last story loading)
  - Logging configuration (level, file rotation, backup count)
  - UI preferences (theme, fonts, layout)
  - AI generation parameters (model, temperature, token limits)
  - Export format defaults
- **`user_settings.yaml`**: User-customized settings (created on first run):
  - Overrides for default settings
  - Persisted across application sessions
  - Theme and UI preference customization
  - Model selection and generation parameters
  - Output path customization
  - Export format preferences
- **`models.yaml`**: Configuration for available AI models:
  - Model names and version specifications
  - Model-specific parameters (context length, temperature ranges)
  - Hardware requirements and estimated VRAM usage
  - Performance characteristics and generation speeds

### `core/` - Core Application Logic
Central business logic and application state management coordinating all major subsystems.

- **`__init__.py`**: Package initialization and exports
- **`application.py`** (LoreoForgeApp - Main Application Class)
  - **QApplication Extension**: Extends PyQt5's QApplication with custom functionality
  - **Lifecycle Management**: Handles initialization, running, and shutdown
  - **Window Management**: Creates and manages main application window
  - **Metadata Setup**: 
    - Application name: "Loreo Forge"
    - Version tracking
    - Organization identification
  - **Font Initialization**: Loads and applies application fonts
  - **Theme Initialization**: Applies initial theme on startup
  - **Icon Setup**: Window icon and application branding
  - **Logging Integration**: LoggerMixin provides logging capabilities
  - **Window Lifecycle**: Tracks main window registration and events
  - **Command-Line Handling**: Parses command-line arguments
  - **Event Loop**: Manages the Qt event loop for GUI responsiveness

- **`story_manager.py`** (StoryManager - Story Project Management)
  - **Project Registry**: Manages multiple story projects
  - **Active Story Context**: Tracks currently active story
  - **Context Caching**: Caches active story data for performance
  - **Story Creation**: Creates new story projects with metadata
    - Title, genre, synopsis, tone, target audience
  - **Story Activation**: Switches active story and loads database
  - **Database Isolation**: Each story has separate database file
  - **Story Listing**: Retrieves all available stories
  - **Story Retrieval**: Gets specific story by ID or name
  - **Story Deletion**: Removes story project and database
  - **Default Story**: Auto-creates default story on first run
  - **Master Database Integration**: Works with MasterDatabase for registry
  - **Metadata Persistence**: Saves story metadata to master database
  - **Database Path Management**: Maintains paths to story databases

### `models/` - Data Models
Object-oriented representations of domain entities with shared base functionality, validation, and serialization.

#### Base Model & Entity Classes

- **`base.py`** (BaseModel - Abstract Foundation)
  - **ID Management**: Unique identifier tracking for all models
  - **Data Dictionary**: Internal `_data` dictionary for property storage
  - **Property Access**: `get()`, `set()`, `__getitem__()`, `__setitem__()` methods
  - **Modified Tracking**: Tracks which properties have been changed
  - **Dirty State**: `is_modified()` checks if model needs saving
  - **Timestamp Management**: 
    - `created_at` - Model creation timestamp
    - `modified_at` - Last modification timestamp
    - Auto-updates on property changes
  - **Serialization**: `to_dict()` converts model to dictionary
  - **Deserialization**: `from_dict()` creates model from dictionary
  - **String Representation**: `__str__()` and `__repr__()` methods
  - **Equality Comparison**: `__eq__()` for model comparison
  - **Type Hints**: Full type annotations for IDE support
  - **Extensibility**: Easy to extend with new model types

- **`story.py`** (Story Model - Project Definition)
  - **Project Metadata**:
    - Title, genre, setting, tone
    - Synopsis and detailed notes
    - Target audience classification
  - **Content Tracking**:
    - Total word count
    - Chapter count
    - Character count
  - **Status Tracking**: Draft, In-Progress, Completed
  - **Arc Management**: Associated story arcs
  - **Statistics**: Computes story statistics on demand
  - **Publication Info**: Publication date, status tracking

- **`chapter.py`** (Chapter Model - Story Chapters)
  - **Chapter Properties**:
    - Chapter number and sequential ordering
    - Rich text content support
    - Summary and detailed notes
  - **Metadata**:
    - Word count calculations
    - Status (draft, in-progress, final)
    - Revision history tracking
  - **Relationships**:
    - Arc association
    - Point-of-view character
    - Featured characters list (JSON stored)
  - **Content Organization**:
    - Plot points documentation
    - Mood and atmosphere description
    - Scene organization and management
  - **Tracking**: Appearance frequencies for characters

- **`character.py`** (Character Model - Story Characters)
  - **Basic Information**:
    - Name, role, archetype
    - Age and status (Alive, Deceased, Unknown)
  - **Physical Description**:
    - Appearance traits
    - Visual characteristics
  - **Psychology & Personality**:
    - Personality traits
    - Motivation and goals
    - Background and history
  - **Voice Consistency**:
    - Voice pattern documentation
    - Dialogue characteristics
    - Voice print generation
  - **Relationships**:
    - Character-to-character relationships
    - Family connections
    - Rivalry and alliance tracking
  - **Development**:
    - Character arc tracking
    - Arc development stage
    - Appearance frequency statistics

- **`location.py`** (Location/Place Model - Story Settings)
  - **Location Identification**:
    - Name, region, coordinates
    - Location type (City, Forest, Castle, etc.)
  - **Description & Atmosphere**:
    - Description text
    - Atmosphere and mood
    - Environmental characteristics
  - **Population & Civilization**:
    - Population size
    - Civilization level
    - Cultural characteristics
  - **Geography**:
    - Climate and weather
    - Terrain and geography
    - Environmental resources
  - **Points of Interest**:
    - Landmarks and notable locations
    - Historical significance
  - **Connections**:
    - Travel times to other locations
    - Associated characters and events

- **`arc.py`** (Arc Model - Plot Structure)
  - **Arc Organization**:
    - Arc number and sequencing
    - Arc title and description
  - **Structure**:
    - Starting chapter marker
    - Ending chapter marker
    - Story beats and key events
  - **Content**:
    - Detailed narrative arc
    - Emotional progression
    - Resolution and conclusion
  - **Thematic Elements**:
    - Thematic elements tracking
    - Motifs and patterns
    - Story implications
  - **Characters**:
    - Character involvement
    - Character arcs within arc
  - **Metadata**:
    - Arc category classification
    - Custom descriptions

- **`lore.py`** (Lore Model - World-Building)
  - **Organization**:
    - Lore category (history, mythology, culture, technology, custom)
    - Custom category support
  - **Content**:
    - Detailed narrative content
    - Historical or background information
  - **Relationships**:
    - Associated characters
    - Associated locations
    - Associated organizations
  - **Cross-References**:
    - Related lore entries
    - Timeline connections
    - Story implications
  - **Metadata**:
    - Visibility flags
    - Importance rating
    - Modification tracking

- **`creature.py`** (Creature Model - Bestiary)
  - **Classification**:
    - Creature name and type
    - Category (Beast, Monster, Dragon, Undead, etc.)
    - Rarity level
  - **Physical Traits**:
    - Appearance description
    - Size and weight
    - Notable physical features
  - **Behavior & Temperament**:
    - Behavioral patterns
    - Temperament classification
    - Intelligence level
    - Social structure
  - **Abilities & Weaknesses**:
    - Special abilities and powers
    - Known weaknesses
    - Attack methods
  - **Ecology**:
    - Environmental preferences
    - Habitat and distribution
    - Diet and feeding behavior
    - Ecological role
  - **Lifecycle**:
    - Lifespan
    - Maturation stages
    - Reproduction method
  - **Special Properties**:
    - Sentience flag
    - Magical properties flag
    - Hostility flag
    - Population tracking

### `database/` - Data Persistence
Comprehensive database management system with per-story isolation, schema handling, and complete CRUD operations.

#### Database Architecture

- **`db_manager.py`** (DatabaseManager - Main Interface)
  - **Connection Management**: Multi-database support with connection pooling
  - **Per-Story Isolation**: Each story gets its own SQLite database file
  - **Database Registration**: Maintains path mapping for story databases
  - **Connection Lifecycle**: Create, reuse, close connections efficiently
  - **CRUD Operations**: Complete Create, Read, Update, Delete for all entities
    - Characters, Chapters, Locations, Arcs, Lore, Creatures, Organizations, Powers
  - **Query Building**: SQL query construction with parameter sanitization (SQL injection prevention)
  - **Transaction Management**: `begin_transaction()`, `commit()`, `rollback()` for atomic operations
  - **Data Validation**: Validates data before database operations
  - **Context Building**: Special queries for AI context retrieval
    - Get recent chapters for context
    - Retrieve character information
    - Fetch world elements for generation
  - **Error Handling**: Custom exceptions for connection/query failures
  - **Connection Timeout**: Configurable timeout with retry logic
  - **Automatic Schema**: Creates tables automatically on first connection

- **`master_db.py`** (MasterDatabase - Story Registry)
  - **Central Registry**: Single SQLite database (`loreo_master.db`) managing all stories
  - **Stories Table**: Metadata for each story project
    - ID (unique identifier)
    - Title, Genre, Synopsis
    - Target Audience, Tone
    - Created Date, Modified Date
    - Status (Draft, In-Progress, Completed)
  - **Active Story Tracking**: Stores which story is currently active
  - **Story Creation**: Creates new story entries with auto-generated IDs
  - **Story Queries**: Retrieve all stories, get specific story, filter by criteria
  - **Connection Pooling**: Efficient connection reuse for master database
  - **Schema Initialization**: Creates master schema on first run
  - **Separate from Story Data**: Master DB is distinct from per-story databases

- **`schema.py`** (DatabaseSchema - Schema Definitions)
  - **Master Schema Creation**: Creates stories registry table structure
  - **Per-Story Schema Creation**: Defines complete story database schema
  - **Entity Tables**: Definitions for all story entities
    - Characters table (id, story_id, name, role, archetype, personality, background, etc.)
    - Chapters table (id, story_id, number, title, content, word_count, arc_id, pov_character_id, etc.)
    - Locations table (id, story_id, name, region, description, type, population, etc.)
    - Arcs table (id, story_id, arc_number, title, description, start_chapter, end_chapter, etc.)
    - Lore table (id, story_id, title, category, content, timeline_date, etc.)
    - Creatures table (id, story_id, name, category, appearance, abilities, habitat, etc.)
    - Organizations table (id, story_id, name, type, structure, description, etc.)
    - Powers table (id, story_id, name, category, mechanics, rarity, prerequisites, etc.)
  - **Index Creation**: Performance indexes on frequently queried fields
  - **Foreign Keys**: Referential integrity between related entities
  - **Constraints**: Unique constraints and NOT NULL requirements
  - **Schema Versioning**: Version tracking for future migrations
  - **SQLite Optimizations**: Journal mode (WAL), synchronous settings
  - **Table Constraints**: Proper data type definitions and field constraints

- **`migrations.py`** (Database Migration Scripts)
  - **Version Control**: Track schema changes by version number
  - **Backward Compatibility**: Migrations work with existing data
  - **Data Transformation**: Scripts for data format changes
  - **Rollback Procedures**: Can undo failed migrations
  - **Safety Checks**: Validates data before and after migration

### `controllers/` - Application Controllers
MVC pattern implementation bridging UI and business logic with PyQt5 signal/slot event handling.

#### Core Controllers

- **`story_controller.py`** (StoryController - Story Management)
  - **Story Operations**: Create, read, update, delete with full validation
  - **Story Creation**: Accepts metadata (title, genre, synopsis, tone, target_audience)
  - **Story Loading**: Activates story context and loads from database
  - **Story Updating**: Modifies metadata with change tracking
  - **Story Deletion**: Removes story with optional confirmation
  - **Story Listing**: Retrieves and filters available stories
  - **Signal Emissions**:
    - `story_created(story_id)` - New story created
    - `story_updated(story_id)` - Story metadata changed
    - `story_deleted(story_id)` - Story removed
    - `story_activated(story_id)` - Story context switched
  - **Integration**: Works with `StoryManager` for registry operations
  - **Error Handling**: Propagates errors through signal mechanism

- **`ai_controller.py`** (AIController - AI Operations)
  - **Generation Coordination**: Orchestrates content generation requests
  - **Model Management**: Model switching, availability checking, capability detection
  - **Generation Parameters**: Temperature, token limits, context settings
  - **Context Assembly**: Coordinates with `ContextManager` for relevant context
  - **Prompt Building**: Works with `PromptBuilder` for template rendering
  - **Ollama Integration**: Direct calls to `OllamaClient` for generation
  - **Response Handling**: Processes and streams generation results
  - **Error Recovery**: Retry logic and error handling for generation failures
  - **Progress Updates**: Signal emissions for long-running operations
  - **Cancellation Support**: Allows user to cancel ongoing generation

### `ui/` - User Interface
PyQt5-based graphical interface with modular view architecture, comprehensive components, and theming system.

#### Core UI Components

- **`main_window.py`** (MainWindow - Application Window)
  - **Window Layout**: Main application window with organized sections
  - **Menu Bar**: File, Edit, View, Help menus with standard actions
    - File: New Story, Open, Save, Export, Exit
    - Edit: Undo, Redo, Cut, Copy, Paste
    - View: Theme selection, View toggles
    - Help: About, Documentation, Support
  - **Toolbar**: Quick access buttons for common actions
    - New story/chapter/character buttons
    - View navigation buttons
    - Save and sync buttons
    - Generation status indicators
  - **Sidebar**: Navigation panel with:
    - Story list browser
    - Quick navigation buttons
    - View selection menu
    - Story metadata display
    - Recent stories quick access
  - **Status Bar**: Bottom information display with:
    - Current story name
    - Word count tracking
    - AI generation status indicator
    - Ollama connection status
    - Progress indicators
  - **Content Stack**: View switching mechanism
    - Manages active view display
    - Smooth transitions between views
  - **View Management**: 
    - View registration system
    - Lifecycle management
    - Signal routing between views
  - **Window Persistence**: Remembers window state
    - Size and position
    - Active view
    - Sidebar width
  - **Keyboard Shortcuts**: Application-wide shortcut management
  - **Geometry**: Window centering and size calculations

- **`theme_engine.py`** (ThemeEngine - Visual Theming)
  - **Theme System**: Game-like visual aesthetics with multiple themes
  - **Built-in Themes**:
    - Obsidian Night - Dark theme with cool tones
    - Iron Dusk - Industrial aesthetic
    - Crimson Dawn - Red/warm color scheme
    - Forest Twilight - Green/natural tones
    - Custom themes supported
  - **Dynamic Loading**: Themes load and apply at runtime
  - **Color Palette**: Per-theme color definitions
    - Background colors
    - Text colors
    - Accent colors
    - Highlight colors
  - **Font Configuration**:
    - Font family selection
    - Font size adjustment
    - Monospace for code areas
  - **Style Sheets**: Qt stylesheet generation from themes
  - **Persistence**: Saves theme choice across sessions
  - **Real-Time Switching**: Change themes without restart
  - **Dark/Light Mode**: Support for both display modes
  - **Customization**: Users can create custom themes
  - **Export**: Save custom themes for sharing

#### UI Components

- **`components/dialogs.py`** (Custom Dialogs)
  - **Story Creation Dialogs**: Create new story projects
  - **Quick Entry Dialogs**: Fast character/location creation
  - **Generation Config**: Configure AI generation parameters
  - **Confirmation Dialogs**: Destructive operation confirmations
  - **File Dialogs**: Open/save/export file selection
  - **Color Picker**: Theme color customization
  - **Error Dialogs**: Display error messages with context

- **`components/sidebar.py`** (Navigation Sidebar)
  - **Story Browser**: List of all stories with quick access
  - **View Menu**: Navigation to different views
  - **Quick Links**: Frequently accessed views
  - **Story Info**: Current story metadata display
  - **Recent Items**: Recently used stories and items
  - **Favorites**: Marked favorite items for quick access

#### UI Views (10 Complete Views)

- **`base_view.py`** (BaseView - Abstract Foundation)
  - **Common Infrastructure**: Base class for all views
  - **UI Setup**: `setup_ui()` method pattern
  - **Data Loading**: `load_data()` method pattern
  - **Data Saving**: `save_data()` method pattern
  - **Modified Tracking**: Tracks unsaved changes
  - **Story Context**: Automatic story context awareness
  - **Signal Support**: PyQt5 signal emission capabilities
  - **Logging**: LoggerMixin provides logging methods
  - **Error Handling**: Built-in error handling patterns
  - **Auto-Save**: Optional auto-save on data changes
  - **Edit Mode**: Toggle between edit/view modes

- **`dashboard_view.py`** (Dashboard - Home Screen)
  - **Quick Statistics**: Story overview and statistics
  - **Word Count Summary**: Total and recent word counts
  - **Recent Activity**: Recently modified items
  - **Quick Actions**: Fast access buttons
    - New story
    - New chapter
    - New character
  - **Story Selection**: Browse and select stories
  - **Getting Started**: Help and tutorials for new users
  - **Quick Stats**: Character count, chapter count, arc count
  - **Activity Feed**: Timeline of recent changes

- **`story_view.py`** (Story Manager - Project Overview)
  - **Metadata Editor**: Edit story information
    - Title, genre, setting
    - Tone, target audience
    - Synopsis (rich text)
    - Detailed notes
  - **Status Tracking**: Publication and project status
  - **Statistics Display**: 
    - Total word count
    - Chapter count
    - Character count
    - Arc count
  - **Arc Overview**: Visual arc structure display
  - **Chapter List**: Quick chapter preview
  - **Edit/View Mode**: Toggle between editing and viewing
  - **Auto-Save**: Saves on data changes

- **`characters_view.py`** (Character Manager - Full CRUD)
  - **Character Browser**: Searchable list of characters
    - Quick search/filter
    - Sort options
    - Favorite marking
  - **Character Editor**: Comprehensive form with multiple sections
    - **Basic Info**: Name, role, archetype, age, status
    - **Appearance**: Physical description, visual traits
    - **Personality**: Personality traits, motivations, goals
    - **Background**: Background story, history
    - **Voice**: Voice patterns, dialogue characteristics
    - **Relationships**: Character relationships and connections
    - **Development**: Character arc, arc stage
    - **Tracking**: Appearance frequency statistics
  - **Character Preview**: Quick character view
  - **Relationship Mapper**: Visual relationship display
  - **Create/Edit/Delete**: Full CRUD with confirmation
  - **AI Expansion**: Integration point for AI character development
  - **Edit Mode Toggle**: Switch between view/edit
  - **Auto-Save**: Automatic save on changes

- **`chapters_list_view.py`** (Chapter Manager - Full CRUD)
  - **Chapter Browser**: List of all chapters
    - Chapter list with numbers and titles
    - Filtering and sorting
    - Quick preview
  - **Chapter Editor**: Complete chapter form
    - Chapter content editor
    - Title and number
    - Word count display
    - Chapter metadata
  - **Metadata Fields**:
    - Arc association
    - POV character
    - Featured characters list
    - Status (draft, in-progress, final)
    - Mood and atmosphere
    - Plot points
    - Summary and notes
  - **Create/Edit/Delete**: Full CRUD operations with confirmation
  - **Reordering**: Drag-to-reorder chapters
  - **Word Count**: Real-time word count calculation
  - **Edit Mode**: Toggle form visibility
  - **Auto-Save**: Automatic saving

- **`chapter_generator_view.py`** (AI Chapter Generation)
  - **Generation Form**: Configuration panel
    - Chapter selection (which chapter to generate after)
    - Generation parameters
    - Context selection
    - Model selection
  - **Context Builder**: Select relevant context
    - Previous chapters
    - Character list
    - Location list
    - Arc information
  - **Generation Controls**:
    - Generate button
    - Cancel button
    - Progress indicator
  - **Output Display**: Real-time generation streaming
    - Live text display
    - Formatting preservation
    - Editing during generation
  - **Post-Generation**:
    - Accept/reject workflow
    - Edit generated content
    - Save to chapter
    - Discard option
  - **Streaming**: Real-time token streaming from AI

- **`world_view.py`** (World Builder - Full CRUD)
  - **Location Manager**: Location browser and editor
    - Location list with search/filter
    - Location creation/editing/deletion
  - **Location Properties**:
    - Name, region, coordinates
    - Type classification
    - Description (rich text)
    - Atmosphere and mood
    - Climate and environment
    - Population and civilization
    - Landmarks and points of interest
    - Historical significance
  - **Travel Calculator**: Distance/time between locations
  - **Lore Integration**: Link lore to locations
  - **Organization Support**: Faction territory assignment
  - **Edit/View Mode**: Toggle editing
  - **Auto-Save**: Automatic persistence

- **`lore_view.py`** (Lore Management - Full CRUD)
  - **Lore Browser**: Searchable lore entry list
    - Filter by category
    - Search functionality
    - Favorite marking
  - **Lore Editor**: Comprehensive lore form
    - Title and category
    - Content editor (rich text)
    - Timeline date assignment
    - Related entries linking
  - **Categories**:
    - History
    - Mythology
    - Culture
    - Technology
    - Custom categories
  - **Cross-References**: Link to characters, locations, orgs
  - **Timeline View**: Visual timeline of lore entries
  - **Create/Edit/Delete**: Full CRUD operations
  - **Edit Mode**: Toggle editing
  - **Auto-Save**: Automatic saving

- **`bestiary_view.py`** (Creature Database - Full CRUD)
  - **Creature Browser**: Searchable creature list
    - Filter by category/rarity
    - Quick preview
    - Favorites
  - **Creature Editor**: Comprehensive creature form
    - **Basic Info**: Name, category, rarity
    - **Appearance**: Physical description, features
    - **Behavior**: Temperament, intelligence, social
    - **Abilities**: Special powers and abilities
    - **Weaknesses**: Vulnerabilities and weaknesses
    - **Ecology**: Habitat, diet, ecological role
    - **Properties**: Sentience, magic, hostility flags
    - **Statistics**: Strength, intelligence, agility
    - **Lifecycle**: Lifespan, maturation stages
    - **Population**: Population and distribution
  - **Create/Edit/Delete**: Full CRUD operations
  - **Edit Mode**: Toggle form visibility
  - **Auto-Save**: Automatic saving

- **`organizations_view.py`** (Faction Manager - Full CRUD)
  - **Organization Browser**: List of organizations/factions
    - Search and filter
    - Organization preview
  - **Organization Editor**: Comprehensive form
    - **Basic Info**: Name, type, status
    - **Structure**: Hierarchy and organization
    - **Leadership**: Leader information
    - **Members**: Member roster and ranks
    - **Goals**: Organization goals and motivations
    - **History**: Background and history
    - **Territory**: Territory and influence map
    - **Relationships**: Alliances and rivalries
    - **Resources**: Assets and capabilities
  - **Relationship Mapper**: Visual relationship display
  - **Member Management**: Add/remove members
  - **Create/Edit/Delete**: Full CRUD operations
  - **Edit Mode**: Toggle editing
  - **Auto-Save**: Automatic saving

- **`powers_view.py`** (Magic/Powers System - Full CRUD)
  - **Power Browser**: Searchable power/spell list
    - Filter by category/rarity
    - Power preview
  - **Power Editor**: Comprehensive form
    - **Definition**: Name, category, type
    - **Mechanics**: How the power works
    - **Effects**: What the power does
    - **Scope**: Range, duration, targets
    - **Cost**: Energy/mana requirements
    - **Rarity**: Power level and availability
    - **Prerequisites**: Learning requirements
    - **Restrictions**: Limitations and rules
    - **Interactions**: How it interacts with other powers
    - **Notes**: Custom information
  - **Character Assignment**: Assign powers to characters
  - **Rule Documentation**: System rules and mechanics
  - **Create/Edit/Delete**: Full CRUD operations
  - **Edit Mode**: Toggle editing
  - **Auto-Save**: Automatic saving

- **`settings_view.py`** (Application Settings)
  - **Theme Settings**: 
    - Theme selection dropdown
    - Font configuration
    - Font size adjustment
    - Dark/light mode
  - **AI Settings**:
    - Model selection
    - Temperature adjustment
    - Token limit configuration
    - Timeout settings
  - **Generation Settings**:
    - Default parameters
    - Context size
    - Retry settings
  - **Logging Settings**:
    - Log level selection
    - Log file management
    - Debug options
  - **Export Settings**:
    - Default export format
    - Export directory
    - Template selection
  - **Directory Settings**:
    - Data directory
    - Story directory
    - Export directory
  - **Preferences**:
    - Auto-save interval
    - UI preferences
    - Keyboard shortcuts
  - **Reset Options**: Restore defaults

### `utils/` - Utility Functions
Cross-cutting utility modules providing logging, validation, formatting, and diagnostics.

#### Utility Modules

- **`logger.py`** (Logging Infrastructure)
  - **Application Logger**: `setup_logger()` initializes application-wide logging
  - **Dual Output**: File logging to `logs/loreo_forge.log` + console output
  - **Separate Formatters**: 
    - File format: timestamp, level, source location, message
    - Console format: colored output with level indicators
  - **Rotating File Handler**: Automatic log rotation (max 10 files, 5MB each)
  - **Log Directory**: Auto-creates and maintains `logs/` directory
  - **LoggerMixin Class**: Provides logging methods to all classes
    - `self.logger` - Logger instance
    - `self.log_info()`, `self.log_error()`, `self.log_warning()`, etc.
  - **Configurable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - **Context Logging**: Includes filename, function, line number
  - **Integration**: Works with Python's standard logging module
  - **Performance**: Minimal overhead, efficient filtering

- **`exception_handler.py`** (Global Exception Management)
  - **Centralized Catching**: Global exception handler for uncaught errors
  - **Error Recovery**: Non-fatal error recovery strategies
  - **User Feedback**: User-friendly error messages in dialogs
  - **Stack Traces**: Full stack trace logging for debugging
  - **Error Categorization**: Specialized handling for different error types
  - **AI Errors**: Special handling for generation failures
  - **Database Errors**: Connection and query error handling
  - **Validation Errors**: Clear messaging for input validation
  - **Crash Prevention**: Graceful shutdown on critical errors
  - **Error Context**: Includes operation context in error messages
  - **Recovery Suggestions**: Helpful recovery steps for users

- **`validators.py`** (Input Validation)
  - **Story Validation**: Validates story metadata (title, genre, synopsis, tone)
  - **Character Validation**: Character name, role, attributes, relationships
  - **Location Validation**: Location name, type, description completeness
  - **Chapter Validation**: Chapter number, content, metadata
  - **Arc Validation**: Arc structure, chapter markers, ordering
  - **Text Field Validation**: 
    - Length checks (min/max bounds)
    - Required field checking
    - Whitespace trimming
  - **File Path Validation**: Valid paths, accessible, proper permissions
  - **Email Validation**: RFC-compliant email checking
  - **URL Validation**: Valid URL format checking
  - **Custom Rules**: Extensible validation framework
  - **Error Messages**: Clear, actionable validation feedback

- **`formatters.py`** (Text Formatting & Display)
  - **Word Count Calculation**: Language-aware word splitting, punctuation handling
  - **Character Count**: Unicode-aware character counting
  - **Text Truncation**: Smart truncation with ellipsis preservation
  - **Time Formatting**: 
    - Creation/modification date display
    - Relative time ("2 hours ago")
    - ISO format timestamps
  - **Number Formatting**: Thousands separators, float precision
  - **Duration Formatting**: Hours, minutes, seconds display
  - **Status Badges**: Visual status indicators and styling
  - **Markdown Rendering**: Convert markdown to displayable text
  - **Rich Text**: Preserve formatting in displays

- **`exporter.py`** (Story Export System)
  - **Export Formats**: 
    - DOCX (Microsoft Word with formatting)
    - PDF (with custom layouts)
    - EPUB (e-reader compatible)
    - Markdown (version control friendly)
    - Plain Text (universal compatibility)
  - **Template System**: Customizable export templates
  - **Cover Generation**: Automatic cover page creation
  - **TOC Generation**: Automatic table of contents
  - **Metadata Embedding**: Story info in document properties
  - **Chapter Formatting**: Consistent chapter styling
  - **Character Export**: Include character list/descriptions
  - **World Export**: Export world-building elements
  - **Batch Export**: Export entire story to multiple formats

- **`diagnose_views.py`** (View Diagnostics)
  - **View File Checking**: Confirms all view files exist
  - **Import Testing**: Attempts to import each view module
  - **Cross-Platform Validation**: Path compatibility checks
  - **Detailed Output**: File-by-file diagnostic reporting
  - **Common Issues**: Identifies 15+ common view problems
  - **Troubleshooting**: Provides solutions for identified issues
  - **Integration Points**: Verifies view registration in MainWindow

### `tests/` - Unit and Integration Tests
Comprehensive test suite for application components with pytest framework.

- **`test_main.py`** (Application Entry Point Tests)
  - Python version validation testing
  - Directory structure creation verification
  - Logging initialization testing
  - Dependency checking verification
  - Application startup sequence testing

- **`test_models.py`** (Data Model Tests)
  - Model initialization and property access
  - Data serialization and deserialization
  - Validation logic testing
  - Relationship handling between models
  - Timestamp management (creation, modification)
  - Model identity and equality comparison
  - Individual model tests for each entity type

- **`test_database.py`** (Database Operation Tests)
  - Connection management and pooling
  - CRUD operations (create, read, update, delete) for all entities
  - Transaction handling and rollback testing
  - Schema creation and validation
  - Data integrity constraints verification
  - Query building and execution
  - Migration testing and validation

- **`test_ai_client.py`** (Ollama Integration Tests)
  - Connection testing to Ollama server
  - Model listing and availability verification
  - Prompt generation and validation
  - Content generation with timeout handling
  - Error handling and recovery
  - Retry logic verification
  - Token counting and context validation
  - Streaming output testing

- **`test_controllers.py`** (Controller Logic Tests)
  - Signal emission verification
  - CRUD operation delegation
  - Error handling and user notification
  - Data validation in controllers
  - Event propagation
  - Controller initialization and setup

### `assets/` - Static Resources
Non-code resources and media files for the application.

- **`fonts/`** (Font Assets)
  - Application-wide font files
  - Monospace fonts for code/text display areas
  - Special character fonts for symbols/icons
  - Font configuration for theme engine

- **`icons/`** (Icon Resources)
  - Application logo for window title bar
  - Menu icons (File, Edit, View, Help)
  - Toolbar action icons (New, Save, Export)
  - View navigation icons
  - Status indicators and badges
  - Dialog window icons
  - Category/type indicator icons

- **`themes/`** (Theme Definitions)
  - JSON or YAML theme configuration files
  - Color palette definitions per theme
  - Style sheet templates
  - Theme metadata and descriptions
  - Font specifications per theme
  - Custom theme examples

### `data/` - User Data Directory
Runtime data storage for user-created content and story databases.

- **`stories/`** (Story Databases & Exports)
  - **Database Files**: Individual SQLite databases per story
    - Format: `story_name.db`
    - Isolated data per story project
    - Automatic creation on first save
  - **Export Files**: Generated story exports
    - DOCX (Word documents)
    - PDF (formatted documents)
    - EPUB (e-book formats)
    - Markdown files
    - Text files
  - **Backups**: Story database backups
    - Automatic backups before migrations
    - User-initiated backup creation
    - Version history tracking
  - **Temporary Files**: Working files during generation
    - Draft saves
    - Generation buffer files
    - Export work files

### `logs/` - Application Logs
Application logging output and diagnostic information.

- **Main Log File**: `loreo_forge.log`
  - Application startup/shutdown events
  - User actions and operations
  - Error and warning messages
  - Debug information

- **Rotating Log Files**: Timestamped log archives
  - Automatic rotation when size exceeds limit
  - Maintains last 10 log files
  - Compression of archived logs

- **Log Levels**:
  - DEBUG: Detailed diagnostic information
  - INFO: General application events
  - WARNING: Warning messages for potential issues
  - ERROR: Error messages with stack traces
  - CRITICAL: Critical failures and crashes

- **Log Contents**:
  - AI generation logs (prompts, parameters, responses)
  - Database operation logs (queries, transactions)
  - UI event logs (view switches, user actions)
  - Connection logs (Ollama, database, file I/O)
  - Error logs with full stack traces

### Story Management
- **Create and manage multiple story projects** with separate databases per story for complete isolation
- **Track comprehensive story metadata** including genre, synopsis, target audience, tone, and themes
- **Generate story outlines with AI assistance** (ready for Phase 6 implementation)
- **Story statistics and analytics** including word counts, chapter counts, character tracking
- **Multi-story workflow** with quick switching and active story context

### Character Development
- **Create and manage story characters** with detailed profiles and extensive attributes
  - Name, role, archetype, age, status (Alive/Deceased/Unknown)
  - Physical appearance and descriptions
  - Personality, motivation, goals, and background
  - Voice patterns and dialogue characteristics for consistency
- **AI-powered character expansion** (ready for Phase 6 implementation)
- **Character relationships and arcs** tracking interactions and development across story
- **Character appearance tracking** monitoring featured appearances in chapters
- **Character arc development** with stage-based progression
- **Customizable character attributes** extensible for various story genres and styles

### World Building
- **Develop detailed story worlds and settings** with locations, geography, and climate
  - Location types, descriptions, and atmosphere
  - Climate characteristics and environmental resources
  - Population and civilization levels
  - Key landmarks and points of interest
- **Manage locations, lore, and world elements** organized by category and timeline
- **Organize factions, organizations, and hierarchies** with comprehensive tracking
  - Organization structure and leadership
  - Member rosters and faction relationships
  - Territory and influence management
- **Technology and magic systems** with rules, mechanics, and restrictions
  - Power/spell definitions and classifications
  - Effect descriptions and interaction rules
  - Power level and rarity tracking
  - Prerequisites and learning conditions
- **Creatures and bestiaries** cataloging creatures with full details
  - Appearance, behavior, and special abilities
  - Weaknesses, diet, and ecological role
  - Creature statistics and classification
  - Sentience, magical properties, and hostility flags

### Chapter Management
- **Create, edit, and organize chapters** with full CRUD operations
  - Chapter numbering, sequencing, and reordering
  - Rich text content editing
  - Word count calculations
- **Chapter metadata and tracking**
  - Arc association and POV character designation
  - Featured characters association
  - Plot points and thematic elements
  - Chapter status (draft, in-progress, final)
  - Mood and atmosphere configuration
  - Summary and detailed notes
- **Maintain story continuity** through context management
- **Chapter previews and quick reference** summaries
- **Auto-save functionality** on data changes

### Content Export
- **Export stories in multiple formats** (DOCX, PDF, EPUB, Markdown) - Phase 6
- **Customizable export templates** for consistent formatting
- **Markdown support** for version control and collaboration
- **Cover page generation** with story metadata
- **Table of contents** automatic generation
- **Metadata embedding** in exported documents

### Intelligent Context Management
- **Automatic context gathering** from database for generation tasks
- **Optimized token usage** selecting relevant context within model limits
- **Context coherence** maintenance across generation calls
- **Custom context settings** for specialized generation tasks

### Local AI Integration
- **Seamless Ollama integration** for local model management
- **Multiple model support** with easy switching
- **Configurable generation parameters** (temperature, token limits, context length)
- **Streaming support** for real-time output display (Phase 6)
- **Graceful fallback** when Ollama unavailable with feature disabling
- **Comprehensive error handling** with user-friendly messages

---

## Architecture & Data Flow

### Data Storage Architecture

**Master Database**: Single SQLite database (`loreo_master.db`) containing:
- Stories registry (metadata, timestamps, status)
- Active story context
- User preferences and settings

**Per-Story Databases**: Individual SQLite database per story containing:
- Chapters and content
- Characters and attributes
- Locations and world elements
- Arcs and plot structure
- Lore entries and background
- All related metadata and relationships

### Request Flow Example: Chapter Generation

1. **User initiates chapter generation** in `ChapterGeneratorView`
2. **View emits signal** with generation parameters
3. **Controller receives signal** and validates input
4. **AIController orchestrates**:
   - Gathers context via `ContextManager` from database
   - Builds prompt via `PromptBuilder` with templates
   - Sends request to `OllamaClient`
5. **OllamaClient**:
   - Validates context length
   - Sends streaming request to Ollama
   - Returns content chunks
6. **Controller streams results** back to view
7. **View displays** generated content with editing capabilities
8. **User accepts** and saves to database via `DatabaseManager`

### Configuration Hierarchy

Settings are loaded in priority order:
1. **User settings** (`user_settings.yaml`) - highest priority
2. **Default settings** (`default_settings.yaml`) - fallback
3. **Hardcoded defaults** in `Settings` class - last resort

### Error Handling Strategy

- **AI Errors**: Specific exceptions (`OllamaConnectionError`, `GenerationTimeoutError`, etc.)
- **Database Errors**: Custom exceptions with context information
- **Validation Errors**: Clear user feedback before operations
- **UI Errors**: Dialog messages with recovery suggestions
- **Logging**: All errors logged with stack traces for debugging

## Technology Stack

### Frontend
- **PyQt5** (5.15.9+): Cross-platform desktop GUI framework
- **Python** (3.8+): Core programming language
- **Custom Theme Engine**: Game-like visual theming system

### Backend & Data
- **SQLite**: Local database engine with per-story isolation
- **ChromaDB** (0.4.0+): Vector database for semantic search and context retrieval

### AI Integration
- **Ollama**: Local LLM server for on-device AI processing
- **Jinja2** (3.1.2+): Template engine for prompt generation
- **sentence-transformers** (2.2.0+): NLP and semantic embeddings

### Document Export
- **python-docx** (0.8.11+): DOCX/Microsoft Word generation
- **fpdf** (1.7.2+): PDF generation
- **ebooklib** (0.18+): EPUB e-book generation

### Development & Testing
- **pytest** (7.4.0+): Unit and integration testing framework
- **pytest-cov** (4.1.0+): Code coverage reporting

### Utilities
- **PyYAML** (6.0+): Configuration file parsing
- **requests** (2.31.0+): HTTP client for Ollama API
- **python-dateutil** (2.8.2+): Date and time utilities
- **psutil** (5.9.0+): System monitoring

---

## Getting Started

### Prerequisites
- **Python 3.8** or higher (3.10+ recommended)
- **Ollama** (https://ollama.ai) installed and running
  - Download and install Ollama for your platform
  - Start Ollama: `ollama serve`
  - Download a model: `ollama pull llama2` or `ollama pull llama3.1:8b`
- **pip** (Python package manager, typically included with Python)
- **Git** (for cloning the repository, optional)

### Installation Steps

1. **Clone or download the repository:**
```bash
git clone <repository-url>
cd "Loreo Forge"
```

2. **Create a Python virtual environment (recommended):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Verify dependencies:**
```bash
python check_dependencies.py
```

5. **Verify Ollama is running:**
- Ollama should be listening on `http://localhost:11434`
- The application will show a warning if Ollama is unavailable but will still function with limited features

6. **Run the application:**
```bash
python main.py
```

The application will:
- Create necessary directory structures
- Initialize the database system
- Check Ollama availability
- Launch the main GUI window

### First-Time Setup

1. **Create your first story** using the dashboard or File menu
2. **Configure settings** (optional) in the Settings view:
   - Select your preferred AI model
   - Customize theme and UI preferences
   - Adjust generation parameters
3. **Start building** your story with characters, world, and chapters
4. **Generate content** using AI assistance for any story element

### Configuration

Edit `config/user_settings.yaml` to customize (created on first run):

```yaml
ui:
  theme: "Obsidian Night"
  font_family: "Segoe UI"
  font_size: 12

ai:
  model: "llama3.1:8b"
  temperature: 0.7
  max_tokens: 4096

generation:
  chapter_word_count: 3000
  enable_streaming: true
```

### Troubleshooting

**"Ollama is not running"**
- Ensure Ollama is downloaded and installed
- Start Ollama with `ollama serve`
- Check that it's accessible at `http://localhost:11434`

**"Module not found" errors**
- Run `pip install -r requirements.txt` again
- Check that you're in the correct virtual environment
- Run `python check_dependencies.py` for detailed diagnostics

**Database connection errors**
- Ensure the `data/` directory is writable
- Check disk space availability
- Delete `data/loreo_master.db` to reset (you will lose story list)

**UI rendering issues**
- Try changing the theme in Settings
- Ensure PyQt5 is properly installed
- Run `verify_views.py` to check UI components

### Running Tests
```bash
pytest
pytest --cov  # with coverage report
pytest -v     # verbose output
pytest tests/test_models.py::TestStory  # specific test class
```

---

## Development Guide

### Project Architecture Principles
- **Model-View-Controller (MVC)**: Clear separation of concerns with controllers bridging UI and business logic
- **Signal/Slot System**: PyQt5 signal/slot for loose coupling between components
- **Per-Story Databases**: Complete data isolation for each story project
- **Logging Integration**: `LoggerMixin` provides consistent logging across all classes
- **Exception Hierarchy**: Specific exception types for different error categories

### Code Organization
- **All model classes inherit from `BaseModel`** for consistency and shared functionality
- **Controllers follow the MVC pattern** with base controller functionality in `BaseController`
- **Views are modular** and can be independently tested and developed
- **Custom exceptions provide specific error handling** with context information
- **Logging is available through `LoggerMixin`** class for any component

### Extending the Application

**Adding a new view:**
1. Create new file in `ui/views/` inheriting from `BaseView`
2. Implement `setup_ui()`, `load_data()`, and `save_data()` methods
3. Register in `ui/views/__init__.py`
4. Add to `MainWindow._create_main_layout()`
5. Create tests in `tests/`

**Adding a new data model:**
1. Create new file in `models/` inheriting from `BaseModel`
2. Implement properties and methods
3. Add schema definition to `database/schema.py`
4. Create tests in `tests/test_models.py`

**Integrating with AI:**
1. Update prompt templates in `ai/templates/`
2. Modify `ContextManager` if context gathering changes needed
3. Use `PromptBuilder` for template rendering
4. Call `OllamaClient` methods for generation
5. Handle specific exceptions from `ai/exceptions.py`

---

## License

---

## Contributing

---
