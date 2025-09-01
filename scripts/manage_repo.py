#!/usr/bin/env python

"""
manage_repo.py - A helper script for maintaining a 3DP profile repository.

This script automates the process of generating and signing the manifest.json file.
It scans the configs directory, detects new and updated profiles, and handles
versioning, checksum calculation, and GPG signing.
"""

import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import gnupg
import semver


def get_file_checksum(path):
    """Calculates the SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def prompt_for_new_profile_meta(path):
    """Interactively prompts the user for metadata for a new profile."""
    print(f"\n--- Found new profile: {path.name} ---")
    try:
        slicer = path.parts[-3]
        profile_type = path.parts[-2]
        print(f"Guessed slicer: '{slicer}', type: '{profile_type}'")
    except IndexError:
        slicer = input("Enter slicer (e.g., 'prusaslicer', 'cura'): ")
        profile_type = input("Enter profile type (e.g., 'printer', 'process'): ")

    name = input(f"Enter profile display name (default: {path.stem}): ") or path.stem
    return name, slicer, profile_type


def bump_version_interactive(current_version):
    """Interactively prompts the user for a version bump."""
    print(f"Current version: {current_version}")
    bump = input("Choose version bump (major, minor, patch) [default: patch]: ").lower()
    ver = semver.Version.parse(current_version)
    if bump == 'major':
        return ver.bump_major()
    if bump == 'minor':
        return ver.bump_minor()
    return ver.bump_patch()


def main():
    parser = argparse.ArgumentParser(description="Manage a 3DP profile repository.")
    parser.add_argument('repo_path', type=Path, help="Path to the repository directory.")
    parser.add_argument('--gpg-key-id', required=True, help="GPG Key ID to use for signing.")
    parser.add_argument('--non-interactive', action='store_true', help="Run in non-interactive mode for CI.")
    args = parser.parse_args()

    manifest_path = args.repo_path / 'manifest.json'
    configs_path = args.repo_path / 'configs'

    # Load existing manifest or create a new one
    if manifest_path.exists():
        print("Loading existing manifest...")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        print("No manifest found, creating a new one.")
        namespace = input("Enter a namespace for this repository: ") if not args.non_interactive else "default_namespace"
        manifest = {
            "spec_version": "1.0",
            "namespace": namespace,
            "profiles": [],
            "checksums": {}
        }

    profiles_by_path = {p['path']: p for p in manifest['profiles']}
    all_current_paths = set()
    new_checksums = {}

    # Walk the configs directory and process files
    for config_file in sorted(configs_path.glob('**/*.*')):
        if config_file.name.startswith('.') or config_file.name.endswith(('.md', '.sig')):
            continue

        relative_path_str = str(config_file.relative_to(args.repo_path))
        all_current_paths.add(relative_path_str)
        checksum = get_file_checksum(config_file)
        new_checksums[relative_path_str] = checksum

        # Check if it's an existing profile
        if relative_path_str in profiles_by_path:
            profile = profiles_by_path[relative_path_str]
            # Check if updated
            if manifest['checksums'].get(relative_path_str) != checksum:
                print(f"\n--- Profile '{profile['name']}' has been updated. ---")
                if args.non_interactive:
                    new_version = semver.Version.parse(profile['version']).bump_patch()
                    print(f"Bumping version (patch): {profile['version']} -> {new_version}")
                else:
                    new_version = bump_version_interactive(profile['version'])

                profile['version'] = str(new_version)
                profile['last_updated'] = datetime.now(timezone.utc).isoformat()

        # Handle new profiles
        else:
            if args.non_interactive:
                print(f"\n--- Found new profile: {config_file.name} (non-interactive) ---")
                name = config_file.stem
                slicer = config_file.parts[-3]
                profile_type = config_file.parts[-2]
                print(f"Guessed metadata: name='{name}', slicer='{slicer}', type='{profile_type}'")
            else:
                name, slicer, profile_type = prompt_for_new_profile_meta(config_file)

            new_profile = {
                "uuid": str(uuid.uuid4()),
                "name": name,
                "type": profile_type,
                "slicer": slicer,
                "version": "0.1.0",
                "path": relative_path_str,
                "dependencies": [],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            manifest['profiles'].append(new_profile)

    # Handle deleted profiles
    existing_paths = set(profiles_by_path.keys())
    deleted_paths = existing_paths - all_current_paths
    if deleted_paths:
        print("\n--- The following profiles have been deleted: ---")
        for path in deleted_paths:
            print(f"  - {path}")

        if args.non_interactive or input("Remove them from the manifest? (y/n) [y]: ").lower() != 'n':
            manifest['profiles'] = [p for p in manifest['profiles'] if p['path'] not in deleted_paths]
            print("Profiles removed from manifest.")

    # Update checksums and save manifest
    manifest['checksums'] = new_checksums
    manifest_json_str = json.dumps(manifest, indent=2)

    print(f"\nWriting updated manifest to {manifest_path}...")
    with open(manifest_path, 'w') as f:
        f.write(manifest_json_str)

    # Sign the manifest
    signature_path = args.repo_path / 'manifest.json.sig'
    print(f"Signing manifest with key {args.gpg_key_id}...")
    try:
        gpg = gnupg.GPG()
        # Ensure the key is available
        if not any(key['keyid'].endswith(args.gpg_key_id) for key in gpg.list_keys()):
             raise ValueError(f"GPG Key ID {args.gpg_key_id} not found in keyring.")

        signed_data = gpg.sign(
            manifest_json_str,
            keyid=args.gpg_key_id,
            detach=True,
            clearsign=False
        )

        if not signed_data.data:
            raise RuntimeError(f"GPG signing failed. Status: {signed_data.status}")

        with open(signature_path, 'wb') as f:
            f.write(signed_data.data)

        print(f"Signature written to {signature_path}")
        print("\nRepository update complete!")

    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(f"\n--- GPG SIGNING FAILED ---")
        print(f"Error: {e}")
        print("Please ensure GnuPG is installed and the specified key is available.")
        # Clean up the failed signature file if it was created
        if signature_path.exists():
            signature_path.unlink()

if __name__ == '__main__':
    main()