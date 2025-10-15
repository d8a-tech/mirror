# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Docker image mirroring tool that automatically mirrors Docker Hub images to GitHub Container Registry (GHCR) to bypass Docker Hub rate limits and retention policies. It uses external tools like `skopeo` (for Docker images) and `oras` (for OCI artifacts) to perform the actual mirroring operations.

## Development Commands

### Installation and Setup
```bash
# Install with uv (preferred)
uv install

# Install in development mode with pip
pip install -e .

# Run the mirror tool
mirror  # Uses mirror-config.yaml in current directory
python -m mirror.main  # Alternative way to run
```

### Configuration
The tool reads from `mirror-config.yaml` which defines:
- Docker images to mirror (source, destination, tags)
- Files to download and push as OCI artifacts (with optional transforms like gunzip)
- Global settings (retry attempts, delays, public/private visibility)

## Code Architecture

### Core Components

**mirror/main.py** - The main application file containing:
- `main()` - Entry point that processes both Docker images and files
- `mirror_image()` - Handles Docker image mirroring via skopeo
- `mirror_file()` - Downloads files, applies transforms, pushes to OCI registry via oras
- `TRANSFORMERS` registry - Pluggable file transformation system (currently supports gunzip)

### Key Functions

- **Tool verification**: `verify_required_tools()` checks for skopeo/oras availability
- **Authentication**: Uses GitHub environment variables (GITHUB_TOKEN, GITHUB_ACTOR, etc.)
- **Retry logic**: Built-in retry with configurable attempts and delays
- **File transformations**: Extensible transformer system using decorators
- **Streaming output**: Real-time output from subprocess commands

### Dependencies

- External tools: `skopeo` (Docker mirroring), `oras` (OCI artifact handling)
- Python dependencies: PyYAML, requests
- Environment variables: GITHUB_TOKEN, GITHUB_ACTOR/GITHUB_USERNAME, GITHUB_REPOSITORY_OWNER/GITHUB_TARGET_REPO_OWNER

## Working with Transformers

To add new file transformers:
1. Create a function that takes `Path` input and returns `Path` output
2. Decorate with `@register_transformer("name")`
3. The transformer will be automatically available in config files

Example:
```python
@register_transformer("my_transform")
def my_transformer(input_path: Path) -> Path:
    # Process file
    return output_path
```

## Environment Setup

Required environment variables for GitHub Actions or local development:
- `GITHUB_TOKEN` - GitHub personal access token with package write permissions
- `GITHUB_ACTOR` or `GITHUB_USERNAME` - GitHub username
- `GITHUB_REPOSITORY_OWNER` or `GITHUB_TARGET_REPO_OWNER` - Target repository owner