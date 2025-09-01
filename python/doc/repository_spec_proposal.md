# 3D Printing Profile Repository: A Proposal

## 1. Introduction & Motivation

The 3D printing community thrives on sharing knowledge, but the process of sharing slicer profiles is fragmented and insecure. Hobbyists and manufacturers alike rely on forum posts, ZIP files, and manual imports. This system lacks several critical features:

*   **Versioning**: Users have no reliable way to know if their profile is outdated or to receive updates.
*   **Namespacing**: If multiple sources (e.g., Prusa and a community member) release a profile for the same printer, name collisions are inevitable, leading to confusion.
*   **Security**: There is no mechanism to verify that a downloaded profile is from a trusted source and hasn't been maliciously altered. A harmful profile could damage a printer.
*   **Discoverability**: Finding profiles requires manual searching across various platforms.

This document proposes a **decentralized, secure, and simple specification** for a 3D printing profile repository. The goal is to create a system that is easy enough for a hobbyist to host on a personal GitHub repository, yet robust enough for manufacturers and slicer developers to adopt.

## 2. Core Concepts: The "Static Manifest" Model

The proposed model is inspired by the simplicity of Homebrew's "taps" and the security of Linux package managers like APT. It avoids the need for complex server-side applications, relying instead on a set of static files served over standard HTTPS.

A "profile repository" is a collection of static files served from a base URL over HTTPS. The client only needs to be an HTTP client.

While using a **Git repository** (e.g., on GitHub) is the simplest way for maintainers to manage and host these files,
it is **not a technical requirement for the protocol**. Any standard web server is sufficient.

### 2.1. Repository Structure

A client only needs to know the root URL of the repository. All discovery starts from a single `manifest.json` file.

```
/
├── manifest.json         # Machine-readable index of all profiles, versions, and checksums.
├── manifest.json.sig     # GPG signature for the manifest file.
├── public-key.asc        # The repository owner's public GPG key.
├── repository.json       # (Optional) Human-readable metadata (author, description, etc.).
└── configs/
    ├── prusaslicer/
    │   ├── printer/
    │   │   └── Prusa_MK4.ini
    │   ├── filament/
    │   │   └── Prusament_PLA.ini
    │   └── process/
    │       └── 0.20mm_QUALITY.ini
    └── cura/
        ├── definition/
        │   └── ultimaker_s5.def.json
        └── quality/
            └── normal.xml
```

### 2.2. The Manifest File

The `manifest.json` is the heart of the system. It is the single source of truth that a client needs to download to understand the repository's contents and check for updates.

```json
{
  "spec_version": "1.0",
  "namespace": "prusa_official",
  "profiles": [
    {
      "uuid": "a1b2c3d4-e5f6-4a9b-8c7d-1e2f3a4b5c6d",
      "name": "Prusa MK4",
      "type": "printer",
      "slicer": "prusaslicer",
      "version": "1.2.0",
      "path": "configs/prusaslicer/printer/Prusa_MK4.ini",
      "dependencies": [],
      "last_updated": "2024-05-21T10:00:00Z"
    },
    {
      "uuid": "f6e5d4c3-b2a1-4f8e-9d6c-7b8a9f0e1d2c",
      "name": "0.20mm QUALITY @MK4",
      "type": "process",
      "slicer": "prusaslicer",
      "version": "1.0.1",
      "path": "configs/prusaslicer/process/0.20mm_QUALITY.ini",
      "dependencies": ["a1b2c3d4-e5f6-4a9b-8c7d-1e2f3a4b5c6d"],
      "last_updated": "2024-05-22T11:30:00Z"
    }
  ],
  "checksums": {
    "configs/prusaslicer/printer/Prusa_MK4.ini": "sha256:deadbeef...",
    "configs/prusaslicer/process/0.20mm_QUALITY.ini": "sha256:c0ffee12..."
  }
}
```

Key fields:
*   `uuid`: A stable, unique identifier. Allows a profile to be renamed without breaking dependencies.
*   `version`: A version string (ideally SemVer) that allows clients to detect updates.
*   `dependencies`: A list of other profile `uuid`s this profile depends on.
*   `checksums`: A map of file paths to their SHA256 checksums, ensuring file integrity.

## 3. Versioning, Namespacing, and Conflict Resolution

### 3.1. Versioning

A slicer can periodically fetch the `manifest.json` from each of a user's configured repositories. By comparing the `version` of a profile in the manifest with the version of the locally installed profile, the slicer can detect an available update and prompt the user.

### 3.2. Namespacing and Conflict Resolution

This system uses explicit namespacing to prevent conflicts.

1.  **Repository URL**: The URL of the repository itself is the first-level identifier (e.g., `github.com/voron-design/slicer-profiles`).
2.  **Manifest Namespace**: The `namespace` field inside the `manifest.json` provides a short, human-friendly identifier (e.g., `"voron_official"`).

If a user adds two repositories that both contain a profile named `"V0.2 Fast ABS"`, the system does **not** attempt to automatically resolve this. Instead, the profiles are presented to the user with their full, unambiguous names:

*   `voron_official / V0.2 Fast ABS`
*   `my_personal_mods / V0.2 Fast ABS`

The user makes the explicit choice of which one to install or use. This prevents ambiguity and ensures the user is always in control.

## 4. Security: Trust Through Digital Signatures

To protect against identity spoofing and malicious profile distribution, the system uses GPG for cryptographic verification.

1.  **Authenticity**: The repository owner signs the `manifest.json` file with their private GPG key, producing `manifest.json.sig`. A client (slicer) verifies this signature using the owner's public key. If the signature is invalid, the entire repository is considered untrusted and rejected.

2.  **Integrity**: The manifest contains SHA256 checksums for every profile file it references. After downloading a profile, the client computes its checksum and verifies it against the value in the trusted manifest. This guarantees that the profile file has not been altered or corrupted since the manifest was signed.

### Client-Side Trust Management

When a user adds a new repository, the client workflow is as follows:

1.  Fetch the repository's `public-key.asc`.
2.  Display the key's unique fingerprint to the user.
3.  Ask the user to confirm that they trust this identity.
4.  Store the repository URL and its trusted key fingerprint in a local configuration.

This one-time trust decision establishes a secure chain of trust for all future updates from that source.

## 5. Call for Discussion

This proposal aims to be a starting point. We invite slicer developers, 3D printer manufacturers, filament producers, and community members to review this specification. We believe that by working together, we can build a simple, open, and secure standard that benefits the entire 3D printing ecosystem.

Key questions for discussion:

*   Is the `manifest.json` structure sufficient? Are there missing fields?
*   Is the GPG-based security model both adequate and accessible?
*   How should slicers best manage the UI/UX for adding repositories and resolving conflicts?