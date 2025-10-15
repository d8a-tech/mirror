#!/usr/bin/env python3

import os
import sys
import yaml
import subprocess
import time
import gzip
import shutil
import tempfile
import requests
from typing import Dict, List, Any, Callable, Optional
from pathlib import Path


def load_config(config_file: str) -> Dict[str, Any]:
    """Load and parse the YAML configuration file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def check_tool_availability(tool: str) -> bool:
    """Check if a command-line tool is available."""
    # Different tools use different version flags
    version_flags = {
        "skopeo": ["--version"],
        "oras": ["version"],
    }
    
    flags = version_flags.get(tool, ["--version"])
    
    try:
        result = subprocess.run(
            [tool] + flags,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def verify_required_tools(tools: List[str]) -> None:
    """Verify that all required tools are available."""
    missing_tools = []
    for tool in tools:
        if not check_tool_availability(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"Error: Missing required tools: {', '.join(missing_tools)}")
        sys.exit(1)


# Transformer registry
TRANSFORMERS: Dict[str, Callable[[Path], Path]] = {}


def register_transformer(name: str):
    """Decorator to register a transformer function."""
    def decorator(func: Callable[[Path], Path]):
        TRANSFORMERS[name] = func
        return func
    return decorator


@register_transformer("gunzip")
def gunzip_transformer(input_path: Path) -> Path:
    """Decompress a gzip file."""
    output_path = input_path.with_suffix("")
    
    with gzip.open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    return output_path


def mirror_image(source: str, destination: str, tag: str, registry_owner: str, registry_username: str, registry_password: str, retry_attempts: int, retry_delay: int) -> bool:
    """Mirror a single Docker image using skopeo."""
    # Replace template variables
    destination = destination.replace("{{GITHUB_REPOSITORY_OWNER}}", registry_owner)
    
    source_full = f"{source}:{tag}"
    dest_full = f"{destination}:{tag}"
    
    print(f"Mirroring: {source_full} → {dest_full}")
    
    for attempt in range(1, retry_attempts + 1):
        try:
            cmd = [
                "skopeo", "copy",
                "--dest-creds", f"{registry_username}:{registry_password}",
                f"docker://{source_full}",
                f"docker://{dest_full}"
            ]
            
            print(f"Running: {' '.join(cmd[:3])} [credentials hidden] {' '.join(cmd[4:])}")
            
            # Stream output in real-time
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
            
            # Stream output line by line
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                return True
            else:
                print(f"Attempt {attempt} failed for {dest_full}")
                if attempt < retry_attempts:
                    print(f"Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    
        except Exception as e:
            print(f"Error on attempt {attempt}: {e}")
            if attempt < retry_attempts:
                time.sleep(retry_delay)
            
    
    print(f"Failed to mirror {source_full} after {retry_attempts} attempts")
    return False


def download_file(url: str, output_path: Path) -> None:
    """Download a file from a URL."""
    print(f"Downloading: {url}")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print(f"\nDownloaded to: {output_path}")


def apply_transforms(file_path: Path, transforms: List[Dict[str, Any]]) -> Path:
    """Apply a list of transforms to a file."""
    current_path = file_path
    
    for transform in transforms:
        transform_type = transform.get("type")
        
        if transform_type not in TRANSFORMERS:
            raise ValueError(f"Unknown transformer type: {transform_type}")
        
        print(f"Applying transform: {transform_type}")
        transformer = TRANSFORMERS[transform_type]
        current_path = transformer(current_path)
    
    return current_path

def oras_login(registry_username: str, registry_password: str) -> bool:
    """Login to OCI registry using oras."""
    cmd = [
        "oras", "login",
        "--username", registry_username,
        "--password", registry_password,
        "ghcr.io"
    ]

    print("Running oras login")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    
    for line in iter(process.stdout.readline, ''):
        print(line.rstrip())
        
    process.wait()
    
    if process.returncode == 0:
        return True
    else:
        print(f"Failed to login to OCI registry")
        return False

def push_file_to_registry(
    file_path: Path,
    destination: str,
    tags: List[str],
    registry_owner: str,
    registry_username: str,
    registry_password: str,
    mime_type: Optional[str] = None
) -> bool:
    """Push a file to OCI registry using oras with multiple tags."""
    # Replace template variables
    destination = destination.replace("{{GITHUB_REPOSITORY_OWNER}}", registry_owner)
    tags_str = ",".join(tags)
    dest_full = f"{destination}:{tags_str}"
    
    print(f"Pushing file to: {destination} with tags: {tags_str}")
    
    try:
        cmd = [
            "oras", "push",
            "--disable-path-validation",
            dest_full,
            f"{file_path}"

        ]
        
        if mime_type:
            # Set custom media type
            cmd.extend(["--artifact-type", mime_type])
        
        print(f"Running: {' '.join(cmd)}")
        
        # Stream output in real-time
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip())
        
        process.wait()
        
        if process.returncode == 0:
            print(f"Successfully pushed: {dest_full}")
            return True
        else:
            print(f"Failed to push {dest_full}")
            return False
            
    except Exception as e:
        print(f"Error pushing file: {e}")
        return False


def mirror_file(
    source: str,
    destination: str,
    tags: List[str],
    transforms: List[Dict[str, Any]],
    registry_owner: str,
    registry_username: str,
    registry_password: str,
    mime_type: Optional[str] = None,
    retry_attempts: int = 3,
    retry_delay: int = 1
) -> bool:
    """Download, transform, and push a file to OCI registry with multiple tags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Extract filename from URL
        filename = source.split("/")[-1]
        download_path = tmpdir_path / filename
        
        for attempt in range(1, retry_attempts + 1):
            try:
                # Download file
                download_file(source, download_path)
                
                # Apply transforms
                processed_path = download_path
                if transforms:
                    processed_path = apply_transforms(download_path, transforms)
                
                # Push to registry with all tags
                if push_file_to_registry(
                    processed_path,
                    destination,
                    tags,
                    registry_owner,
                    registry_username,
                    registry_password,
                    mime_type
                ):
                    return True
                else:
                    if attempt < retry_attempts:
                        print(f"Waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                        
            except Exception as e:
                print(f"Error on attempt {attempt}: {e}")
                if attempt < retry_attempts:
                    time.sleep(retry_delay)
        
        print(f"Failed to mirror {source} after {retry_attempts} attempts")
        return False


def main():
    """Main function to mirror Docker images and files."""
    config_file = "mirror-config.yaml"
    
    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found!")
        sys.exit(1)
    
    # Load configuration
    config = load_config(config_file)
    
    # Determine which tools are needed
    required_tools = []
    if config.get("docker"):
        required_tools.append("skopeo")
    if config.get("files"):
        required_tools.append("oras")
    
    # Verify required tools are available
    print("Checking required tools...")
    verify_required_tools(required_tools)
    print(f"All required tools available: {', '.join(required_tools)}")
    print()
    
    # Get registry owner (namespace) and auth credentials
    registry_owner = os.getenv("GITHUB_TARGET_REPO_OWNER") or os.getenv("GITHUB_REPOSITORY_OWNER") or os.getenv("GITHUB_ACTOR")
    registry_username = os.getenv("GITHUB_USERNAME") or os.getenv("GITHUB_ACTOR")
    registry_password = os.getenv("GITHUB_TOKEN")

    print(f"Registry owner (namespace): {registry_owner}")
    print(f"Registry username: {registry_username}")
    print(f"Registry password: *************...")
    
    if not registry_owner or not registry_username or not registry_password:
        print("GITHUB_TARGET_REPO_OWNER/GITHUB_REPOSITORY_OWNER, GITHUB_USERNAME/GITHUB_ACTOR and GITHUB_TOKEN are required")
        sys.exit(1)
    
    # Get global settings
    retry_attempts = config.get("settings", {}).get("retry_attempts", 3)
    retry_delay = config.get("settings", {}).get("retry_delay", 1)
    
    print(f"Global settings:")
    print(f"  - Retry attempts: {retry_attempts}")
    print(f"  - Retry delay: {retry_delay}s")
    print()
    
    failed_mirrors = 0
    
    # Process Docker images
    docker_mirrors = config.get("docker", [])
    if docker_mirrors:
        print(f"Found {len(docker_mirrors)} Docker image configurations to process")
        print()
        
        for i, mirror in enumerate(docker_mirrors):
            print(f"Processing Docker configuration {i + 1}/{len(docker_mirrors)}")
            
            source = mirror.get("source")
            destination = mirror.get("destination")
            tags = mirror.get("tags", [])
            
            print(f"  Source: {source}")
            print(f"  Destination: {destination}")
            print(f"  Tags to mirror: {len(tags)}")
            
            for tag in tags:
                print(f"    - {tag}")
                
                if not mirror_image(source, destination, tag, registry_owner, registry_username, registry_password, retry_attempts, retry_delay):
                    failed_mirrors += 1
            
            print()
    
    # Process files
    file_mirrors = config.get("files", [])
    if file_mirrors:
        print(f"Found {len(file_mirrors)} file configurations to process")
        print()

        if not oras_login(registry_username, registry_password):
            print("Failed to login to OCI registry")
            sys.exit(1)
        
        for i, file_config in enumerate(file_mirrors):
            print(f"Processing file configuration {i + 1}/{len(file_mirrors)}")
            
            source = file_config.get("source")
            destination = file_config.get("destination")
            tags = file_config.get("tags", [])
            transforms = file_config.get("transforms", [])
            mime_type = file_config.get("mime")
            
            print(f"  Source: {source}")
            print(f"  Destination: {destination}")
            print(f"  Tags to process: {len(tags)}")
            if transforms:
                print(f"  Transforms: {[t.get('type') for t in transforms]}")
            if mime_type:
                print(f"  MIME type: {mime_type}")
            
            for tag in tags:
                print(f"    - {tag}")
            
            # Process all tags for this file configuration at once
            if not mirror_file(
                source,
                destination,
                tags,
                transforms,
                registry_owner,
                registry_username,
                registry_password,
                mime_type,
                retry_attempts,
                retry_delay
            ):
                failed_mirrors += 1
            
            print()
    
    if failed_mirrors > 0:
        print(f"Failed mirrors: {failed_mirrors}")
        sys.exit(1)
    else:
        print("All mirrors completed successfully!")


if __name__ == "__main__":
    main()
