# 3D Printer Configuration Repository Structure

## Overview
This document defines the directory structure and file naming conventions for hosting 3D printer slicer configuration files in a distributed repository system similar to Homebrew or Python's PyPI.

## Directory Structure

```
repository-root/
├── index.json                          # Repository metadata and index
├── slicers/                            # Slicer-specific configurations
│   ├── orcaslicer/                     # OrcaSlicer configurations
│   │   ├── printers/                   # Printer definitions
│   │   │   ├── bambu/                  # Manufacturer grouping
│   │   │   │   ├── a1-mini.json        # Main printer configuration
│   │   │   │   ├── a1-mini/            # Optional assets directory
│   │   │   │   │   ├── cover.png       # Printer cover image
│   │   │   │   │   ├── bed.stl         # 3D bed model
│   │   │   │   │   ├── bed.svg         # Bed texture/outline
│   │   │   │   │   └── thumbnail.png   # Small preview image
│   │   │   │   ├── a1.json
│   │   │   │   ├── a1/                 # Assets for A1
│   │   │   │   │   ├── cover.png
│   │   │   │   │   ├── bed.stl
│   │   │   │   │   └── bed.svg
│   │   │   │   └── x1-carbon.json
│   │   │   ├── prusa/
│   │   │   │   ├── mk3s.json
│   │   │   │   ├── mk3s/               # Assets for MK3S
│   │   │   │   │   ├── cover.png
│   │   │   │   │   ├── bed.stl
│   │   │   │   │   └── bed.svg
│   │   │   │   ├── mk4.json
│   │   │   │   └── mk4/
│   │   │   │       ├── cover.png
│   │   │   │       ├── bed.stl
│   │   │   │       └── bed.svg
│   │   │   └── creality/
│   │   │       ├── ender3-v2.json
│   │   │       ├── ender3-v2/
│   │   │       │   ├── cover.png
│   │   │       │   ├── bed.stl
│   │   │       │   └── bed.svg
│   │   │       └── cr10s.json
│   │   ├── filaments/                  # Filament/Material profiles
│   │   │   ├── pla/
│   │   │   │   ├── generic-pla.json
│   │   │   │   ├── bambu-pla-basic.json
│   │   │   │   └── prusament-pla.json
│   │   │   ├── petg/
│   │   │   │   ├── generic-petg.json
│   │   │   │   └── bambu-petg-basic.json
│   │   │   └── abs/
│   │   │       ├── generic-abs.json
│   │   │       └── bambu-abs.json
│   │   └── processes/                  # Print/Process profiles
│   │       ├── quality/
│   │       │   ├── 0.2mm-fine.json
│   │       │   ├── 0.3mm-standard.json
│   │       │   └── 0.4mm-draft.json
│   │       ├── speed/
│   │       │   ├── slow-detailed.json
│   │       │   ├── normal.json
│   │       │   └── fast-draft.json
│   │       └── specialty/
│   │           ├── miniatures.json
│   │           ├── vase-mode.json
│   │           └── supports-heavy.json
│   ├── prusaslicer/                    # PrusaSlicer configurations
│   │   ├── printers/
│   │   ├── filaments/
│   │   └── processes/
│   └── cura/                           # Ultimaker Cura configurations
│       ├── printers/
│       ├── materials/
│       └── profiles/
├── metadata/                           # Additional metadata files
│   ├── manufacturers.json              # List of printer manufacturers
│   ├── material-types.json             # Standard material type definitions
│   └── tags.json                       # Common tags for categorization
└── api/                                # API endpoint files for programmatic access
    ├── v1/
    │   ├── index.json                  # API version 1 index
    │   ├── slicers.json                # Available slicers
    │   └── search.json                 # Search endpoint metadata
    └── latest -> v1/                   # Symlink to latest API version
```

## File Naming Convention

### General Rules
- Use lowercase with hyphens for separation: `manufacturer-model-variant.json`
- No spaces, use hyphens instead
- File extensions: `.json` for JSON, `.toml` for TOML
- Maximum filename length: 100 characters
- ASCII characters only for maximum compatibility

### Printer Files
Format: `{manufacturer}-{model}-{variant}.{ext}`
Examples:
- `bambu-a1-mini.json`
- `prusa-mk3s-plus.json`
- `creality-ender3-v2.json`
- `voron-2.4-350mm.json`

### Filament/Material Files
Format: `{brand}-{material}-{variant}.{ext}`
Examples:
- `generic-pla.json`
- `bambu-pla-basic.json`
- `prusament-petg-orange.json`
- `hatchbox-abs-black.json`

### Process/Profile Files
Format: `{category}-{description}.{ext}` or `{layer-height}-{quality}.{ext}`
Examples:
- `0.2mm-fine.json`
- `0.3mm-standard.json`
- `vase-mode.json`
- `miniatures-high-detail.json`
- `speed-draft.json`

### Printer Asset Files
Assets are stored in a directory matching the printer configuration filename (without extension).

**Required Asset Naming:**
- `cover.png` - Main printer image (recommended: 320x240px, PNG format)
- `bed.stl` - 3D bed model for visualization (STL format)
- `bed.svg` - Bed texture/outline for slicer UI (SVG format)

**Optional Asset Naming:**
- `thumbnail.png` - Small preview image (recommended: 64x64px)
- `logo.png` - Manufacturer logo
- `manual.pdf` - Printer manual or setup guide
- `firmware/` - Directory for firmware files
- `gcode/` - Directory for sample G-code files

**Asset Directory Examples:**
- `slicers/orcaslicer/printers/bambu/a1-mini/cover.png`
- `slicers/orcaslicer/printers/prusa/mk3s/bed.stl`
- `slicers/orcaslicer/printers/creality/ender3-v2/bed.svg`

## Repository Index File (index.json)

```json
{
  "name": "3d-printer-configs",
  "version": "1.0.0",
  "description": "Community 3D printer configuration repository",
  "api_version": "v1",
  "last_updated": "2024-01-15T10:30:00Z",
  "supported_slicers": [
    "orcaslicer",
    "prusaslicer", 
    "cura"
  ],
  "statistics": {
    "total_printers": 150,
    "total_filaments": 89,
    "total_processes": 45
  },
  "endpoints": {
    "api": "/api/v1/",
    "browse": "/slicers/",
    "search": "/api/v1/search.json"
  }
}
```

## Individual Configuration File Structure

Each configuration file should include metadata:

```json
{
  "metadata": {
    "name": "Bambu Lab A1 Mini",
    "version": "1.2.0",
    "slicer": "orcaslicer",
    "slicer_version": "1.8.0+",
    "type": "printer",
    "manufacturer": "Bambu Lab",
    "model": "A1 Mini",
    "tags": ["bambu", "enclosed", "auto-leveling"],
    "created": "2024-01-10T14:30:00Z",
    "updated": "2024-01-15T09:15:00Z",
    "author": "community",
    "license": "MIT",
    "description": "Official Bambu Lab A1 Mini printer profile",
    "compatibility": {
      "min_slicer_version": "1.8.0",
      "tested_versions": ["1.8.0", "1.8.1", "1.9.0"]
    }
  },
  "config": {
    // Actual slicer configuration data here
  }
}
```

## Benefits of This Structure

### GitHub Hosting
- Direct browsing through GitHub's web interface
- Raw file access via `raw.githubusercontent.com`
- Version control and history tracking
- Community contributions via pull requests
- Automatic hosting via GitHub Pages

### Self-Hosting with Apache
- Directory browsing enabled by default
- RESTful URL structure
- Easy to mirror and cache
- Standard HTTP serving

### Client Discovery
- Predictable URL patterns
- JSON index files for programmatic access
- Hierarchical browsing
- Search and filtering capabilities

## URL Examples

### GitHub Hosted
```
https://raw.githubusercontent.com/user/3d-configs/main/slicers/orcaslicer/printers/bambu/a1-mini.json
https://user.github.io/3d-configs/slicers/orcaslicer/filaments/pla/generic-pla.json
```

### Self-Hosted
```
https://configs.example.com/slicers/orcaslicer/printers/bambu/a1-mini.json
https://configs.example.com/api/v1/index.json
```

This structure provides flexibility for both hosting methods while maintaining consistency and discoverability.
