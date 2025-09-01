# Reference Profile Repository

This directory is a reference implementation of the 3D Printing Profile Repository specification. It demonstrates the required file structure.

## Initialization

This repository does not contain a `manifest.json` by default. To initialize it, you must run the management script. This will generate the manifest, calculate checksums, and sign it with your GPG key.

Make sure you have a GPG key available.

```bash
# From the project root directory
python scripts/manage_repo.py repo --gpg-key-id "YOUR_GPG_KEY_ID"
```

Follow the interactive prompts to add the example profiles to the manifest. After the script completes, you can commit the newly created `manifest.json` and `manifest.json.sig` files.