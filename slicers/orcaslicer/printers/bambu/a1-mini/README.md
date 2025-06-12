# Bambu Lab A1 Mini Assets

This directory contains additional assets for the Bambu Lab A1 Mini printer configuration.

## Asset Files

- `cover.png` - Main printer image (320x240px recommended)
- `bed.stl` - 3D bed model for visualization
- `bed.svg` - Bed texture/outline for slicer UI
- `thumbnail.png` - Small preview image (64x64px recommended)

## Asset Sources

These assets should be sourced from:
1. Official manufacturer resources
2. Community contributions
3. Generated from CAD models
4. Photographed printer images

## Usage

Assets are referenced in the main printer configuration file (`a1-mini.json`) in the `metadata.assets` section:

```json
"assets": {
  "cover_image": "slicers/orcaslicer/printers/bambu/a1-mini/cover.png",
  "bed_model": "slicers/orcaslicer/printers/bambu/a1-mini/bed.stl",
  "bed_texture": "slicers/orcaslicer/printers/bambu/a1-mini/bed.svg",
  "thumbnail": "slicers/orcaslicer/printers/bambu/a1-mini/thumbnail.png"
}
```

## File Formats

- **Images**: PNG format preferred for compatibility
- **3D Models**: STL format for bed models
- **Vector Graphics**: SVG format for bed textures
- **Documentation**: Markdown or PDF formats

## Contributing

When contributing assets:
1. Ensure proper licensing and attribution
2. Use appropriate file sizes (balance quality vs. download size)
3. Follow the standardized naming convention
4. Test assets with the target slicer software
