#!/bin/bash

# Docker Image Mirror Script
# This script mirrors Docker Hub images to GitHub Container Registry using Skopeo
# Usage: ./scripts/mirror.sh [config-file] [github-username] [github-token]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONFIG_FILE="${1:-mirror-config.yaml}"
GITHUB_USERNAME="${2:-}"
GITHUB_TOKEN="${3:-}"

# Function to print colored output
print_status() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${NC}"
}

print_error() {
    print_status "$RED" "❌ $1"
}

print_success() {
    print_status "$GREEN" "✅ $1"
}

print_warning() {
    print_status "$YELLOW" "⚠️  $1"
}

print_info() {
    print_status "$BLUE" "ℹ️  $1"
}

# Check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v skopeo &> /dev/null; then
        print_error "Skopeo is not installed. Please install it first."
        echo "  Ubuntu/Debian: sudo apt-get install skopeo"
        echo "  macOS: brew install skopeo"
        echo "  Arch Linux: sudo pacman -S skopeo"
        exit 1
    fi
    
    if ! command -v yq &> /dev/null; then
        print_error "yq is not installed. Please install it first."
        echo "  Download from: https://github.com/mikefarah/yq/releases"
        exit 1
    fi
    
    print_success "All dependencies are available"
}

# Check authentication
check_auth() {
    if [[ -z "$GITHUB_USERNAME" ]]; then
        print_error "GitHub username not provided"
        echo "Usage: $0 [config-file] [github-username] [github-token]"
        echo "Or set GITHUB_USERNAME environment variable"
        exit 1
    fi
    
    if [[ -z "$GITHUB_TOKEN" ]]; then
        print_error "GitHub token not provided"
        echo "Usage: $0 [config-file] [github-username] [github-token]"
        echo "Or set GITHUB_TOKEN environment variable"
        echo ""
        echo "To create a token:"
        echo "1. Go to https://github.com/settings/tokens"
        echo "2. Create a new token with 'write:packages' and 'read:packages' permissions"
        exit 1
    fi
}

# Function to mirror a single image
mirror_image() {
    local source="$1"
    local destination="$2"
    local tag="$3"
    local retry_attempts="$4"
    local retry_delay="$5"
    local attempt=1
    
    # Replace template variables
    destination="${destination//\{\{GITHUB_REPOSITORY_OWNER\}\}/$GITHUB_USERNAME}"
    
    local source_full="${source}:${tag}"
    local dest_full="${destination}:${tag}"
    
    print_info "Mirroring: $source_full → $dest_full"
    
    while [[ $attempt -le $retry_attempts ]]; do
        if skopeo copy \
            --dest-creds="${GITHUB_USERNAME}:${GITHUB_TOKEN}" \
            "docker://$source_full" \
            "docker://$dest_full"; then
            print_success "Successfully mirrored: $dest_full"
            return 0
        else
            print_error "Attempt $attempt failed for $dest_full"
            if [[ $attempt -lt $retry_attempts ]]; then
                print_warning "Waiting ${retry_delay}s before retry..."
                sleep "$retry_delay"
            fi
            ((attempt++))
        fi
    done
    
    print_error "Failed to mirror $source_full after $retry_attempts attempts"
    return 1
}

# Main function
main() {
    print_info "Docker Image Mirror Script"
    echo "=========================="
    
    # Check if running in GitHub Actions
    if [[ -n "$GITHUB_ACTIONS" ]]; then
        GITHUB_USERNAME="$GITHUB_ACTOR"
        GITHUB_TOKEN="$GITHUB_TOKEN"
    else
        # Use environment variables if not provided as arguments
        GITHUB_USERNAME="${GITHUB_USERNAME:-$2}"
        GITHUB_TOKEN="${GITHUB_TOKEN:-$3}"
    fi
    
    check_dependencies
    check_auth
    
    # Check if config file exists
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Configuration file $CONFIG_FILE not found!"
        exit 1
    fi
    
    print_info "Using configuration file: $CONFIG_FILE"
    print_info "GitHub username: $GITHUB_USERNAME"
    
    # Get global settings
    RETRY_ATTEMPTS=$(yq '.settings.retry_attempts // 3' "$CONFIG_FILE")
    RETRY_DELAY=$(yq '.settings.retry_delay // 30' "$CONFIG_FILE")
    PUBLIC=$(yq '.settings.public // true' "$CONFIG_FILE")
    
    print_info "Global settings:"
    echo "  - Retry attempts: $RETRY_ATTEMPTS"
    echo "  - Retry delay: ${RETRY_DELAY}s"
    echo "  - Public images: $PUBLIC"
    echo ""
    
    # Get number of mirror configurations
    MIRROR_COUNT=$(yq '.mirrors | length' "$CONFIG_FILE")
    print_info "Found $MIRROR_COUNT image configurations to process"
    echo ""
    
    # Track success/failure
    TOTAL_MIRRORS=0
    SUCCESSFUL_MIRRORS=0
    FAILED_MIRRORS=0
    
    # Process each mirror configuration
    for i in $(seq 0 $((MIRROR_COUNT - 1))); do
        print_info "Processing configuration $((i + 1))/$MIRROR_COUNT"
        
        SOURCE=$(yq ".mirrors[$i].source" "$CONFIG_FILE")
        DESTINATION=$(yq ".mirrors[$i].destination" "$CONFIG_FILE")
        
        echo "  Source: $SOURCE"
        echo "  Destination: $DESTINATION"
        
        # Get tags for this mirror
        TAG_COUNT=$(yq ".mirrors[$i].tags | length" "$CONFIG_FILE")
        echo "  Tags to mirror: $TAG_COUNT"
        
        for j in $(seq 0 $((TAG_COUNT - 1))); do
            TAG=$(yq ".mirrors[$i].tags[$j]" "$CONFIG_FILE")
            echo "    - $TAG"
            
            ((TOTAL_MIRRORS++))
            
            if mirror_image "$SOURCE" "$DESTINATION" "$TAG" "$RETRY_ATTEMPTS" "$RETRY_DELAY"; then
                ((SUCCESSFUL_MIRRORS++))
            else
                ((FAILED_MIRRORS++))
            fi
        done
        
        echo ""
    done
    
    # Summary
    print_info "Mirror Summary:"
    echo "  - Total mirrors attempted: $TOTAL_MIRRORS"
    echo "  - Successful: $SUCCESSFUL_MIRRORS"
    echo "  - Failed: $FAILED_MIRRORS"
    
    if [[ $FAILED_MIRRORS -gt 0 ]]; then
        print_warning "Some mirrors failed. Check the logs above for details."
        exit 1
    else
        print_success "All mirrors completed successfully!"
    fi
}

# Run main function
main "$@" 