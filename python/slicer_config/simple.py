#!/usr/bin/env python

"""
slicer_config_client.py - A reference client for the 3DP Profile Repository Spec.

This client interacts with profile repositories that follow the "Static Manifest" model.
It fetches a manifest file from a repository, allows users to list and install profiles,
and handles downloading profiles and their dependencies to a local directory.
"""

import json
import hashlib
import logging
from pathlib import Path
from urllib.parse import urljoin

import gnupg
import requests

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / '.slicer_profiles'
REPOSITORIES_FILE = 'repositories.json'


class RepoClient:
    """A client for a single 3DP profile repository."""

    def __init__(self, repo_url, cache_dir, gpg_homedir=None):
        self.repo_url = repo_url.rstrip('/')
        self.cache_dir = Path(cache_dir)
        self.gpg = gnupg.GPG(gnupghome=gpg_homedir)
        self.manifest = None
        self.profiles_by_uuid = {}

    def update(self):
        """Fetches the latest manifest from the repository."""
        manifest_url = f"{self.repo_url}/manifest.json"
        signature_url = f"{self.repo_url}/manifest.json.sig"

        logger.info("Fetching manifest from %s", manifest_url)
        try:
            manifest_resp = requests.get(manifest_url, timeout=10)
            manifest_resp.raise_for_status()
            manifest_data = manifest_resp.content

            logger.info("Fetching signature from %s", signature_url)
            sig_resp = requests.get(signature_url, timeout=10)
            sig_resp.raise_for_status()
            sig_data = sig_resp.content

        except requests.RequestException as e:
            logger.error("Failed to fetch manifest or signature from %s: %s", self.repo_url, e)
            return False

        verified = self.gpg.verify_data(sig_data, manifest_data)
        if not verified:
            logger.error("MANIFEST SIGNATURE VERIFICATION FAILED for %s. The repository is untrusted.", self.repo_url)
            logger.error("GPG status: %s", verified.status)
            # In a real slicer, you would need to ensure the publisher's public key is in the keyring.
            # For this example, we'll assume it is.
            return False

        logger.info("Manifest signature verified successfully. Key ID: %s", verified.key_id)

        try:
            self.manifest = json.loads(manifest_data)
            self._process_manifest()
            logger.info("Successfully updated manifest for namespace '%s'", self.manifest.get('namespace'))
        except json.JSONDecodeError as e:
            logger.error("Failed to parse manifest JSON: %s", e)
            return False
        return True

    def _process_manifest(self):
        """Processes the manifest for easy lookups."""
        if not self.manifest or 'profiles' not in self.manifest:
            logger.error("Manifest for %s is invalid or empty.", self.repo_url)
            return

        # In a real implementation, you'd check manifest['spec_version']
        # For now, we assume it's a compatible version.
        self.profiles_by_uuid = {p['uuid']: p for p in self.manifest['profiles']}

    def list_profiles(self):
        """Returns a list of all profiles in the repository."""
        if not self.manifest:
            return []
        return self.manifest.get('profiles', [])

    def find_profile_by_name(self, name):
        """Finds a profile by its name."""
        if not self.manifest:
            return None
        for profile in self.manifest.get('profiles', []):
            if profile['name'] == name:
                return profile
        return None

    def download_profile(self, profile_uuid):
        """
        Downloads a single profile and its dependencies.
        Returns a list of paths to the downloaded files.
        """
        download_queue = {profile_uuid}
        processed_uuids = set()
        downloaded_files = []

        # Resolve all dependencies
        while download_queue:
            uuid = download_queue.pop()
            if uuid in processed_uuids:
                continue

            profile = self.profiles_by_uuid.get(uuid)
            if not profile:
                logger.warning("Could not find profile with UUID %s, skipping.", uuid)
                continue

            # Add dependencies to the queue
            for dep_uuid in profile.get('dependencies', []):
                if dep_uuid not in processed_uuids:
                    download_queue.add(dep_uuid)

            # Download the file
            file_url = urljoin(self.repo_url, profile['path'])
            destination = self.cache_dir / profile['path']
            destination.parent.mkdir(parents=True, exist_ok=True)

            expected_checksum = self.manifest.get('checksums', {}).get(profile['path'])

            try:
                logger.info("Downloading %s to %s", file_url, destination)
                response = requests.get(file_url, timeout=10)
                response.raise_for_status()
                file_content = response.content

                if expected_checksum:
                    if not self._verify_checksum(file_content, expected_checksum):
                        logger.error("Checksum mismatch for %s. File may be corrupt or tampered with. Aborting.", profile['path'])
                        # Fail the entire download operation for security
                        return []
                    logger.info("Checksum verified for %s", profile['path'])

                with open(destination, 'wb') as f:
                    f.write(file_content)
                downloaded_files.append(destination)

            except requests.RequestException as e:
                logger.error("Failed to download profile %s: %s", file_url, e)
                # In a real app, you might want to fail the whole operation
                continue

            processed_uuids.add(uuid)

        return downloaded_files

    @staticmethod
    def _verify_checksum(file_content, expected_checksum):
        """Verifies the checksum of a file's content."""
        algo, value = expected_checksum.split(':', 1)
        if algo != 'sha256':
            logger.warning("Unsupported checksum algorithm: %s. Skipping verification.", algo)
            return True # Or False for stricter security
        h = hashlib.sha256()
        h.update(file_content)
        return h.hexdigest() == value


class RepositoryManager:
    """Manages a collection of profile repositories."""

    def __init__(self, config_dir, cache_dir, gpg_homedir):
        self.config_dir = Path(config_dir)
        self.cache_dir = Path(cache_dir)
        self.gpg_homedir = gpg_homedir
        self.config_dir.mkdir(exist_ok=True)
        self.repo_config_path = self.config_dir / REPOSITORIES_FILE
        self.repositories = self._load_repositories()
        self.clients = {
            url: RepoClient(url, self.cache_dir, self.gpg_homedir)
            for url in self.repositories
        }

    def _load_repositories(self):
        if not self.repo_config_path.exists():
            return {}
        with open(self.repo_config_path, 'r') as f:
            return json.load(f)

    def _save_repositories(self):
        with open(self.repo_config_path, 'w') as f:
            json.dump(self.repositories, f, indent=2)

    def add_repo(self, repo_url):
        # In a real app, you'd fetch the public key, show the user the fingerprint,
        # and ask for confirmation before adding.
        # For this CLI example, we'll just add it.
        if repo_url in self.repositories:
            logger.warning("Repository %s is already added.", repo_url)
            return
        logger.info("Adding repository: %s", repo_url)
        self.repositories[repo_url] = {} # In a real app, store the trusted key_id here
        self._save_repositories()
        self.clients[repo_url] = RepoClient(repo_url, self.cache_dir, self.gpg_homedir)
        print(f"Repository {repo_url} added.")

    def list_repos(self):
        if not self.repositories:
            print("No repositories configured.")
            return
        print("Configured repositories:")
        for url in self.repositories:
            print(f"  - {url}")

    def update_all(self):
        logger.info("Updating all repositories...")
        for url, client in self.clients.items():
            print(f"--- Updating {url} ---")
            client.update()

    def list_all_profiles(self, slicer=None):
        """Lists all profiles from all repositories, optionally filtered by slicer."""
        all_profiles = []
        for client in self.clients.values():
            if not client.manifest:
                client.update()
            if client.manifest:
                namespace = client.manifest.get('namespace')
                for profile in client.list_profiles():
                    if slicer and profile.get('slicer') != slicer:
                        continue
                    all_profiles.append((namespace, profile))
        return all_profiles

    def find_profile(self, profile_name, slicer):
        """Finds a profile across all repos, handling namespacing and slicer type."""
        # If a namespace is provided, search is targeted
        if '/' in profile_name:
            namespace, name = profile_name.split('/', 1)
            for client in self.clients.values():
                if client.manifest and client.manifest.get('namespace') == namespace.strip():
                    profile = client.find_profile_by_name(name.strip())
                    # Also check slicer type
                    if profile and profile.get('slicer') == slicer:
                        return profile  # Found a unique, specific match
            return None # Specific profile not found

        # If no namespace, search all and report conflicts
        found_profiles = []
        for client in self.clients.values():
            if not client.manifest:
                client.update() # Ensure manifest is loaded
            if client.manifest:
                profile = client.find_profile_by_name(profile_name)
                if profile:
                    if profile.get('slicer') == slicer:
                        found_profiles.append((client.manifest.get('namespace'), profile))

        if len(found_profiles) == 0:
            logger.error("Profile '%s' not found in any repository.", profile_name)
            return None
        if len(found_profiles) > 1:
            logger.error("Ambiguous profile name '%s'. Found in multiple namespaces:", profile_name)
            for namespace, profile in found_profiles:
                print(f"  - Use '{namespace}/{profile['name']}' to install this one.")
            return None # Indicate conflict

        return found_profiles[0][1]


def main():
    """Main command-line entry point."""
    parser = _create_arg_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)

    manager = RepositoryManager(config_dir=args.config_dir, cache_dir=args.cache_dir, gpg_homedir=args.gpg_homedir)

    if args.command == 'repo-add':
        manager.add_repo(args.url)
    elif args.command == 'repo-list':
        manager.list_repos()
    elif args.command == 'update':
        manager.update_all()
    elif args.command == 'list':
        profiles = manager.list_all_profiles(slicer=args.slicer)
        if not profiles:
            print("No profiles found for the specified criteria.")
            return

        print("Available profiles:")
        for namespace, profile in profiles:
            print(f"  - {namespace}/{profile['name']} (v{profile['version']}) [slicer: {profile.get('slicer')}]")

    elif args.command == 'install':
        profile_to_install = manager.find_profile(args.profile_name, slicer=args.slicer)
        if not profile_to_install:
            return 1

        print(f"Installing '{profile_to_install['name']}' and its dependencies...")
        # We need to find which client has this profile to download it
        for client in manager.clients.values():
            if client.profiles_by_uuid.get(profile_to_install['uuid']):
                downloaded = client.download_profile(profile_to_install['uuid'])
                break
        print("Downloaded files:")
        for f in downloaded:
            print(f"  - {f}")


def _setup_logging(verbosity):
    # setup logging based on verbosity
    verbosity_map = {
        0: logging.ERROR,
        1: logging.INFO,
        2: logging.DEBUG,
    }
    logging.basicConfig(level=verbosity_map.get(verbosity, logging.DEBUG),
                        format='%(asctime)s - %(levelname)s - %(message)s')


def _create_arg_parser():
    import argparse
    parser = argparse.ArgumentParser(description="A reference client for managing 3D printer profile repositories.")
    parser.add_argument('--config-dir', default=str(DEFAULT_CONFIG_DIR), help=f"Directory for configuration files. Defaults to {DEFAULT_CONFIG_DIR}")
    parser.add_argument('--cache-dir', default=str(DEFAULT_CONFIG_DIR / 'cache'),
                        help="Download location for profiles. Defaults to './profile_cache'.")
    parser.add_argument('--gpg-homedir', help="Path to the GPG home directory for key management. "
                                             "If not set, the system default is used.")
    parser.add_argument('--verbose', '-v', action='count', default=1, help="Increase output verbosity.")

    subparsers = parser.add_subparsers(dest='command', required=True)
    repo_add_parser = subparsers.add_parser('repo-add', help="Add a new profile repository.")
    repo_add_parser.add_argument('url', help="URL of the repository to add.")

    subparsers.add_parser('repo-list', help="List all configured repositories.")
    subparsers.add_parser('update', help="Fetch latest profiles from all repositories.")

    list_parser = subparsers.add_parser('list', help="List available profiles.")
    list_parser.add_argument('--slicer', help="Filter profiles for a specific slicer (e.g., 'cura', 'prusaslicer').")

    install_parser = subparsers.add_parser('install', help="Install a profile.")
    install_parser.add_argument('profile_name', help="Name of the profile to install (e.g., 'Prusa MK4' or 'voron_official/V0.2 Fast ABS').")
    install_parser.add_argument('--slicer', required=True, help="Specify the target slicer for the profile (e.g., 'cura', 'prusaslicer').")

    return parser


if __name__ == '__main__':
    main()
