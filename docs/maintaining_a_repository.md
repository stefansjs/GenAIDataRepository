# Maintaining a Profile Repository

This guide is for repository owners and maintainers. It explains the workflow for adding new profiles, updating existing ones, and publishing the changes securely.

## 1. Guiding Principles

The goal is to make maintenance as simple and error-proof as possible.

*   **Single Source of Truth**: The profile files (`.ini`, `.json`, etc.) inside the `configs/` directory are the source of truth.
*   **Automate Everything Else**: The `manifest.json` and its signature (`manifest.json.sig`) should be generated automatically. **You should never edit the manifest by hand.**
*   **Git is Your Friend**: Use a Git repository to track changes and collaborate. The commit history will provide a human-readable log of profile updates.

## 2. Prerequisites

Before you begin, you will need:

1.  **A GPG Keypair**: You need a GPG key to sign your manifest, which proves your identity.
2.  **Python 3**: The helper script is written in Python.
3.  **Required Python Libraries**:
    ```bash
    pip install python-gnupg semver
    ```

### 2.1. Generating Your First GPG Key

If you don't have a GPG key, you can create one using the `gpg` command-line tool, which is available on most systems.

1.  **Run the key generation command:**
    ```bash
    gpg --full-generate-key
    ```

2.  **Follow the prompts:**
    *   When asked for the key type, the default (`RSA and RSA`) is a good choice.
    *   For the keysize, `4096` bits is recommended for strong security.
    *   Set an expiration date or choose `0` for a key that never expires.
    *   Enter your real name and email address. This information will be public.
    *   You will be prompted to enter a secure passphrase to protect your key.

3.  **Find your Key ID:**
    Once the key is generated, you need to find its ID to use it with the management script.
    ```bash
    gpg --list-secret-keys --keyid-format=long
    ```
    The output will look something like this:
    ```
    /Users/yourname/.gnupg/pubring.kbx
    ------------------------------------
    sec   rsa4096/A1B2C3D4E5F6G7H8 2024-05-23 [SC]
          11223344556677889900AABBCCDDEEFF11223344
    uid                 [ultimate] Your Name <your.email@example.com>
    ssb   rsa4096/H8G7F6E5D4C3B2A1 2024-05-23 [E]
    ```
    The long string of characters after the `/` on the `sec` line is your **Key ID**. In this example, it is `A1B2C3D4E5F6G7H8`. This is the value you will pass to the `--gpg-key-id` argument.

## 3. The Maintainer Workflow

The process for updating your repository is a simple, three-step process.

### Step 1: Add or Modify Profile Files

Make all your changes directly to the configuration files within the `repo/configs/` directory.

*   **To Add a New Profile**: Create a new file in the appropriate subdirectory (e.g., `repo/configs/prusaslicer/printer/MyNewPrinter.ini`).
*   **To Update an Existing Profile**: Simply edit the file in place.

### Step 2: Run the Management Script

We provide a helper script, `scripts/manage_repo.py`, that automates all the complex tasks. This script will:

1.  Scan the `configs/` directory for new or modified files.
2.  Prompt you for metadata (`name`, `slicer`, `type`) for any new profiles.
3.  Detect changes to existing profiles and ask you how to bump the version (major, minor, or patch).
4.  Generate a new, valid `manifest.json` with updated versions, timestamps, and SHA256 checksums.
5.  Sign the new manifest with your GPG key, creating `manifest.json.sig`.

To run the script, navigate to the root of the project and execute it, providing the path to your repository and your GPG Key ID.

```bash
# Example command
python scripts/manage_repo.py ./repo --gpg-key-id "your-gpg-key-id"
```

The script is interactive and will guide you through the process.

### Step 3: Commit and Push Your Changes

After the script has successfully run, you will see updated `manifest.json` and `manifest.json.sig` files.

Use Git to review, commit, and push all your changes (the profile files and the manifest files).

```bash
git add .
git commit -m "feat: Add Prusa MK4 profiles and update PLA settings"
git push
```

That's it! Clients pointing to your repository will now be able to see the updates.

## 4. Advanced: Managing Dependencies

The `manage_repo.py` script is designed to be simple and does not automatically resolve dependencies (e.g., a `process` profile that `inherits` from a `printer` profile).

If you need to define dependencies:

1.  Run the management script once to add the new profiles to the manifest. This will assign them unique UUIDs.
2.  **Manually edit `manifest.json`** to add the dependency UUIDs. This is the one exception to the "never edit the manifest" rule.

    ```json
    // Find your new profile
    {
      "uuid": "f6e5d4c3-b2a1-4f8e-9d6c-7b8a9f0e1d2c",
      "name": "0.20mm QUALITY @MK4",
      ...
      // Add the UUID of the profile it depends on
      "dependencies": ["a1b2c3d4-e5f6-4a9b-8c7d-1e2f3a4b5c6d"],
      ...
    }
    ```

3.  **Re-run the management script**. It will see that you modified the manifest but that the profile files themselves haven't changed. It will preserve your dependency edits and simply re-calculate the checksums and re-sign the file.

    ```bash
    # Re-run the script to update checksums and signature
    python scripts/manage_repo.py ./repo --gpg-key-id "your-gpg-key-id"
    ```

4.  Commit the final changes.
