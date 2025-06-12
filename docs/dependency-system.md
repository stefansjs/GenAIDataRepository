# Configuration Dependency System (Optional Feature)

The 3D Printer Configuration Repository optionally supports configuration inheritance through a dependency system. This feature allows configurations to inherit settings from parent configurations, reducing duplication and making maintenance easier.

**Note: This is an optional feature. Repositories can choose to implement dependency resolution or use standalone configurations without inheritance.**

## Overview

Configuration files can inherit from other configurations using the `inherits` property. This creates a hierarchy where child configurations override parent configurations, similar to object-oriented inheritance.

### Inheritance Chain Example

```
Generic PLA → fdm_filament_pla → fdm_filament_common
```

In this example:
- `fdm_filament_common` provides base settings for all filaments
- `fdm_filament_pla` inherits from common and adds PLA-specific settings
- `Generic PLA` inherits from PLA base and adds brand-specific overrides

## Configuration Structure

### Inheritance Properties

Each configuration can include these inheritance-related properties in the `config` section:

```json
{
  "config": {
    "type": "filament",
    "name": "Generic PLA",
    "inherits": "fdm_filament_pla",
    "from": "system",
    "instantiation": "true"
  }
}
```

- **`inherits`**: Name of the parent configuration to inherit from
- **`from`**: Source type of the parent (`system`, `vendor`, `user`)
- **`instantiation`**: Whether this config can be used directly (`true`/`false`)

### Inheritance Types

#### System Configurations
Built-in base configurations provided by the slicer software.
- Search paths: `/slicers/{slicer}/base/`, `/slicers/{slicer}/system/`
- Example: `fdm_filament_common`, `fdm_filament_pla`

#### Vendor Configurations  
Manufacturer-specific base configurations.
- Search paths: `/slicers/{slicer}/{type}/{manufacturer}/base/`
- Example: `bambu_pla_base`, `prusa_petg_base`

#### User Configurations
User-created base configurations.
- Search paths: `/slicers/{slicer}/{type}/user/`, `/slicers/{slicer}/user/{type}/`
- Example: Custom profiles created by users

## API Endpoints

### Get Dependencies

Get the complete dependency tree for a configuration:

```
GET /api/v1/dependencies/{slicer}/{type}/{path}
```

**Example:**
```
GET /api/v1/dependencies/orcaslicer/filaments/pla/generic-pla.json
```

**Response:**
```json
{
  "target": {
    "name": "Generic PLA",
    "path": "/slicers/orcaslicer/filaments/pla/generic-pla.json",
    "inherits": "fdm_filament_pla",
    "from": "system"
  },
  "dependencies": [
    {
      "name": "fdm_filament_common",
      "path": "/slicers/orcaslicer/filaments/base/fdm_filament_common.json",
      "inherits": null,
      "from": "system"
    },
    {
      "name": "fdm_filament_pla", 
      "path": "/slicers/orcaslicer/filaments/base/fdm_filament_pla.json",
      "inherits": "fdm_filament_common",
      "from": "system"
    }
  ],
  "resolution_order": [
    "fdm_filament_common",
    "fdm_filament_pla",
    "Generic PLA"
  ]
}
```

### Get Resolved Configuration

Get a fully resolved configuration with all inheritance applied:

```
GET /api/v1/resolved/{slicer}/{type}/{path}?include_source_map=true
```

**Example:**
```
GET /api/v1/resolved/orcaslicer/filaments/pla/generic-pla.json?include_source_map=true
```

**Response:**
```json
{
  "resolved_config": {
    "type": "filament",
    "name": "Generic PLA",
    "filament_type": ["PLA"],
    "temperature": [210],
    "bed_temperature": [60]
  },
  "source_map": {
    "type": "fdm_filament_common",
    "name": "Generic PLA", 
    "filament_type": "fdm_filament_pla",
    "temperature": "fdm_filament_pla",
    "bed_temperature": "fdm_filament_pla"
  },
  "inheritance_chain": [
    "fdm_filament_common",
    "fdm_filament_pla",
    "Generic PLA"
  ]
}
```

## Query Parameters

### For Configuration Requests

- **`include_dependencies=true`**: Include dependency tree in response
- **`resolve_inheritance=true`**: Return fully resolved configuration

### For Dependency Requests

- **`format=tree`**: Return hierarchical tree format
- **`depth=3`**: Limit dependency resolution depth
- **`include_metadata=true`**: Include metadata for each dependency

### For Resolved Configuration Requests

- **`include_source_map=true`**: Show which parent provided each property
- **`validate=true`**: Validate the resolved configuration

## Resolution Algorithm

The dependency resolver uses a depth-first search algorithm with the following rules:

1. **Child Overrides Parent**: Child configurations override parent values
2. **Resolution Order**: Dependencies are resolved from root to leaf
3. **Circular Detection**: Circular dependencies are detected and reported as errors
4. **Caching**: Configurations are cached to improve performance

### Merge Strategy

When merging configurations:
- Simple values (strings, numbers, booleans) are overridden
- Arrays are replaced entirely by child values
- Objects are merged recursively

## Creating Inheritance Hierarchies

### Best Practices

1. **Create Base Configurations**: Start with broad base configurations
2. **Material-Specific Bases**: Create material-specific intermediate bases
3. **Brand-Specific Overrides**: Add brand/model-specific final configurations
4. **Minimal Overrides**: Only override what's necessary in child configs

### Example Hierarchy

```
fdm_filament_common (base for all filaments)
├── fdm_filament_pla (PLA-specific settings)
│   ├── Generic PLA (generic PLA profile)
│   ├── Bambu PLA Basic (Bambu-specific PLA)
│   └── Prusament PLA (Prusa-specific PLA)
├── fdm_filament_abs (ABS-specific settings)
│   ├── Generic ABS
│   └── Bambu ABS
└── fdm_filament_petg (PETG-specific settings)
    ├── Generic PETG
    └── Prusament PETG
```

## Implementation Example

Here's how to create a new filament configuration with inheritance:

```json
{
  "metadata": {
    "name": "Bambu PLA Basic",
    "version": "1.0.0",
    "slicer": "orcaslicer",
    "type": "filament",
    "manufacturer": "Bambu Lab",
    "material": "PLA"
  },
  "config": {
    "type": "filament",
    "name": "Bambu PLA Basic",
    "inherits": "fdm_filament_pla",
    "from": "system",
    "instantiation": "true",
    "filament_colour": "#1976D2",
    "temperature": [220],
    "first_layer_temperature": [225],
    "compatible_printers": [
      "Bambu Lab A1 Mini 0.4 nozzle",
      "Bambu Lab A1 0.4 nozzle",
      "Bambu Lab X1 Carbon 0.4 nozzle"
    ]
  }
}
```

This configuration:
- Inherits all settings from `fdm_filament_pla`
- Overrides color and temperatures for Bambu-specific values
- Specifies compatible printers
- Can be instantiated directly (`instantiation: true`)

## Error Handling

The dependency system handles several error conditions:

- **Configuration Not Found**: Returns 404 if a configuration or its dependencies don't exist
- **Circular Dependencies**: Returns 400 with details about the circular reference
- **Invalid Inheritance**: Returns 400 if inheritance properties are malformed
- **Depth Limit Exceeded**: Returns 400 if dependency chain exceeds maximum depth

## Testing Dependencies

Use the provided Python script to test dependency resolution:

```bash
python api/v1/dependency_resolver.py
```

This will demonstrate dependency resolution for the Generic PLA configuration and show both the dependency tree and fully resolved configuration.
