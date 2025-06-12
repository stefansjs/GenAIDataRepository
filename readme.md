# 3D Printer Configuration Repository

A distributed repository system for hosting 3D printer slicer configuration files, inspired by Homebrew and Python's PyPI. This repository provides a standardized structure for sharing printer profiles, filament settings, and process configurations across different slicers.

## Repository Structure

This repository follows a hierarchical structure that supports multiple slicers and configuration types:

```
repository-root/
├── index.json                    # Repository metadata and API info
├── slicers/                      # Slicer-specific configurations
│   ├── orcaslicer/              # OrcaSlicer configurations
│   │   ├── printers/            # Printer definitions
│   │   ├── filaments/           # Filament/Material profiles  
│   │   └── processes/           # Print/Process profiles
│   ├── prusaslicer/             # PrusaSlicer configurations
│   └── cura/                    # Ultimaker Cura configurations
├── metadata/                    # Additional metadata files
│   ├── manufacturers.json      # Printer manufacturer info
│   ├── material-types.json     # Material type definitions
│   └── tags.json              # Common tags for categorization
└── api/                        # API endpoint files
    └── v1/                     # API version 1
        ├── index.json          # API documentation
        ├── slicers.json        # Available slicers
        └── search.json         # Search capabilities
```

## Supported Slicers

- **OrcaSlicer** - Advanced slicer with Bambu Lab integration
- **PrusaSlicer** - Popular open-source slicer from Prusa Research  
- **Cura** - Ultimaker's widely-used slicer

## Configuration Types

### Printers
Printer definitions include machine specifications, build volumes, and hardware-specific settings. Printer configurations can optionally include additional assets like cover images, bed models, and textures.

**Example:** `/slicers/orcaslicer/printers/bambu/a1-mini.json`
**Assets:** `/slicers/orcaslicer/printers/bambu/a1-mini/cover.png`

### Filaments
Material profiles with temperature settings, flow rates, and material-specific parameters.

**Example:** `/slicers/orcaslicer/filaments/pla/generic-pla.json`

### Processes
Print quality profiles with layer heights, speeds, and advanced slicing settings.

**Example:** `/slicers/orcaslicer/processes/quality/0.2mm-fine.json`

## File Naming Convention

### General Rules
- Use lowercase with hyphens: `manufacturer-model-variant.json`
- No spaces, use hyphens instead
- ASCII characters only for maximum compatibility
- Maximum filename length: 100 characters

### Examples
- Printers: `bambu-a1-mini.json`, `prusa-mk3s-plus.json`
- Filaments: `generic-pla.json`, `bambu-pla-basic.json`
- Processes: `0.2mm-fine.json`, `vase-mode.json`

### Printer Assets
Printer configurations can include optional assets stored in a directory matching the configuration filename:

**Asset Types:**
- `cover.png` - Main printer image (320x240px recommended)
- `bed.stl` - 3D bed model for visualization
- `bed.svg` - Bed texture/outline for slicer UI
- `thumbnail.png` - Small preview image (64x64px)
- `manual.pdf` - Printer documentation
- `firmware/` - Firmware files directory

**Asset Directory Structure:**
```
slicers/orcaslicer/printers/bambu/
├── a1-mini.json              # Main configuration
└── a1-mini/                  # Assets directory
    ├── cover.png
    ├── bed.stl
    ├── bed.svg
    └── thumbnail.png
```

Assets are referenced in the configuration metadata:
```json
"assets": {
  "cover_image": "slicers/orcaslicer/printers/bambu/a1-mini/cover.png",
  "bed_model": "slicers/orcaslicer/printers/bambu/a1-mini/bed.stl",
  "bed_texture": "slicers/orcaslicer/printers/bambu/a1-mini/bed.svg"
}
```

## Usage

### GitHub Hosting
This repository can be hosted directly on GitHub with automatic access via:
- Raw file access: `https://raw.githubusercontent.com/user/repo/main/slicers/orcaslicer/printers/bambu/a1-mini.json`
- GitHub Pages: `https://user.github.io/repo/slicers/orcaslicer/printers/bambu/a1-mini.json`

### Self-Hosting
Deploy on any web server with directory browsing enabled:
- Apache: Enable `mod_autoindex` for directory listings
- Nginx: Enable `autoindex on` for directory browsing
- Static hosting: Works with any static file hosting service

### Client Integration
Clients can discover and fetch configurations using the namespace/repository pattern:

```bash
# Add a repository (similar to Homebrew tap)
slicer-config add-repo username/3d-printer-configs

# List available printers
slicer-config list printers --slicer orcaslicer

# Download a specific configuration
slicer-config get printer bambu/a1-mini --slicer orcaslicer
```

## API Endpoints

### Repository Information
- `GET /index.json` - Repository metadata and statistics
- `GET /api/v1/index.json` - API documentation and endpoints

### Browse Configurations
- `GET /slicers/` - List available slicers
- `GET /slicers/{slicer}/printers/` - Browse printer configurations
- `GET /slicers/{slicer}/filaments/` - Browse filament profiles
- `GET /slicers/{slicer}/processes/` - Browse process profiles

### Direct Access
- `GET /slicers/{slicer}/printers/{manufacturer}/{model}.json` - Get printer config
- `GET /slicers/{slicer}/filaments/{material}/{name}.json` - Get filament config
- `GET /slicers/{slicer}/processes/{category}/{name}.json` - Get process config

### Optional Dependency Resolution
- `GET /api/v1/dependencies/{slicer}/{type}/{path}` - Get dependency tree for a configuration (optional)
- `GET /api/v1/resolved/{slicer}/{type}/{path}` - Get fully resolved configuration with inheritance (optional)

### Query Parameters
- `format=json|raw` - Response format
- `include_dependencies=true` - Include dependency tree in response
- `resolve_inheritance=true` - Return fully resolved configuration
- `include_source_map=true` - Show which parent provided each property
- `slicer=orcaslicer` - Filter by slicer type
- `manufacturer=bambu` - Filter by manufacturer
- `material=pla` - Filter by material type
- `tags=enclosed,auto-leveling` - Filter by tags

## Configuration File Format

Each configuration file includes standardized metadata:

```json
{
  "metadata": {
    "name": "Configuration Name",
    "version": "1.0.0",
    "slicer": "orcaslicer",
    "type": "printer|filament|process",
    "manufacturer": "Manufacturer Name",
    "tags": ["tag1", "tag2"],
    "created": "2024-01-10T14:30:00Z",
    "updated": "2024-01-15T09:15:00Z",
    "author": "community",
    "license": "MIT",
    "description": "Configuration description",
    "compatibility": {
      "min_slicer_version": "1.8.0",
      "tested_versions": ["1.8.0", "1.9.0"]
    }
  },
  "config": {
    // Actual slicer configuration data
  }
}
```

## Optional Features

### Configuration Inheritance (Optional)
Repositories can optionally implement a dependency system where configurations inherit from parent configurations:

```json
{
  "config": {
    "name": "Generic PLA",
    "inherits": "fdm_filament_pla",
    "from": "system",
    "instantiation": "true"
  }
}
```

**Benefits of inheritance:**
- Reduces configuration duplication
- Easier maintenance of related configurations
- Hierarchical organization of settings

**Standalone configurations:**
- No dependencies required
- Self-contained configuration files
- Simpler implementation for basic repositories

See [Dependency System Documentation](docs/dependency-system.md) for full details.

## Contributing

1. Fork this repository
2. Add your configuration files following the naming convention
3. Include proper metadata in each file
4. Test configurations with the specified slicer versions
5. Submit a pull request

## License

This repository and its configurations are released under the MIT License. Individual configurations may have their own licenses as specified in their metadata.

## Community

- Report issues and request configurations via GitHub Issues
- Join discussions in GitHub Discussions
- Contribute configurations via Pull Requests
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

---

**Note:** This is a community-driven project. Always verify configurations before use and adjust settings as needed for your specific printer and materials.
