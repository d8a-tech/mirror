# Docker Mirror Setup Guide

This repository provides an automated solution for mirroring Docker Hub images to GitHub Container Registry (GHCR) using Skopeo, helping you avoid Docker Hub rate limits and retention policies.

## 🚀 Quick Start

1. **Fork or clone this repository**
2. **Edit `mirror-config.yaml`** to specify which images you want to mirror
3. **Push changes** - GitHub Actions will automatically mirror the images
4. **Use your mirrored images** with `ghcr.io/yourusername/imagename:tag`

## 📋 Prerequisites

### For GitHub Actions (Automatic)
- GitHub repository with Actions enabled
- No additional setup required - the workflow handles everything

### For Local Usage
- [Skopeo](https://github.com/containers/skopeo) installed
- [yq](https://github.com/mikefarah/yq) installed
- GitHub Personal Access Token with `write:packages` and `read:packages` permissions

## 🔧 Configuration

### Mirror Configuration File

Edit `mirror-config.yaml` to specify which images to mirror:

```yaml
mirrors:
  - source: "docker.io/library/nginx"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/nginx"
    tags:
      - "latest"
      - "alpine"
      - "1.25"

settings:
  public: true
  retry_attempts: 3
  retry_delay: 30
  max_concurrent_mirrors: 5
```

#### Configuration Options

**Mirror Entry:**
- `source`: Source Docker Hub image (e.g., `docker.io/library/nginx`)
- `destination`: Destination GHCR path (use `{{GITHUB_REPOSITORY_OWNER}}` placeholder)
- `tags`: List of tags to mirror

**Global Settings:**
- `public`: Whether mirrored images should be public (default: `true`)
- `retry_attempts`: Number of retry attempts for failed mirrors (default: `3`)
- `retry_delay`: Delay between retries in seconds (default: `30`)
- `max_concurrent_mirrors`: Maximum concurrent mirror operations (default: `5`)

### GitHub Actions Setup

The workflow is automatically configured and will run when:
- You push changes to `mirror-config.yaml`
- You push changes to the workflow file
- Weekly (Sundays at 2 AM UTC) to catch updates to `latest` tags
- Manually triggered via GitHub Actions UI

**Required Permissions:**
The workflow uses `GITHUB_TOKEN` which automatically has the necessary permissions for GHCR.

## 🏃‍♂️ Usage

### Automatic Mirroring (Recommended)

1. **Add images to mirror:**
   ```bash
   # Edit mirror-config.yaml
   vim mirror-config.yaml
   
   # Commit and push
   git add mirror-config.yaml
   git commit -m "Add new images to mirror"
   git push
   ```

2. **Monitor the workflow:**
   - Go to your repository's "Actions" tab
   - Watch the "Mirror Docker Images to GHCR" workflow
   - Check the summary for mirrored images

3. **Use your mirrored images:**
   ```bash
   # Instead of:
   docker pull nginx:latest
   
   # Use:
   docker pull ghcr.io/yourusername/nginx:latest
   ```

### Manual/Local Mirroring

1. **Install dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install skopeo
   
   # macOS
   brew install skopeo
   
   # Arch Linux
   sudo pacman -S skopeo
   
   # Install yq
   sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
   sudo chmod +x /usr/local/bin/yq
   ```

2. **Create GitHub Personal Access Token:**
   - Go to https://github.com/settings/tokens
   - Create a new token with these permissions:
     - `write:packages`
     - `read:packages`
     - `repo` (if repository is private)

3. **Run the mirror script:**
   ```bash
   # Method 1: Pass credentials as arguments
   ./scripts/mirror.sh mirror-config.yaml yourusername your_github_token
   
   # Method 2: Use environment variables
   export GITHUB_USERNAME=yourusername
   export GITHUB_TOKEN=your_github_token
   ./scripts/mirror.sh
   ```

## 📦 Example Configurations

### Basic Web Stack
```yaml
mirrors:
  - source: "docker.io/library/nginx"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/nginx"
    tags: ["latest", "alpine"]
  
  - source: "docker.io/library/postgres"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/postgres"
    tags: ["15", "15-alpine"]
  
  - source: "docker.io/library/redis"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/redis"
    tags: ["7-alpine"]
```

### Development Tools
```yaml
mirrors:
  - source: "docker.io/library/node"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/node"
    tags: ["18-alpine", "20-alpine", "latest"]
  
  - source: "docker.io/library/python"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/python"
    tags: ["3.11-slim", "3.12-slim"]
```

### Third-party Images
```yaml
mirrors:
  - source: "docker.io/traefik/traefik"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/traefik"
    tags: ["latest", "v3.0"]
  
  - source: "docker.io/grafana/grafana"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/grafana"
    tags: ["latest"]
```

## 🔍 Monitoring and Troubleshooting

### GitHub Actions Logs
- Go to your repository's "Actions" tab
- Click on the latest "Mirror Docker Images to GHCR" run
- Expand the "Parse config and mirror images" step for detailed logs

### Common Issues

**Authentication Errors:**
- Ensure your GitHub token has the correct permissions
- Check that the token hasn't expired

**Rate Limiting:**
- Docker Hub may rate limit pulls; the script includes retry logic
- Consider spreading mirrors across multiple runs

**Image Not Found:**
- Verify the source image and tag exist on Docker Hub
- Check for typos in the configuration

**Permission Denied:**
- Ensure your GitHub token has `write:packages` permission
- Check that you have permission to create packages in the target organization

### Viewing Mirrored Images
- Go to your GitHub profile or organization
- Click on "Packages" tab
- Your mirrored images will be listed there

## 🔄 Updating Images

### Automatic Updates
- The workflow runs weekly to catch updates to `latest` tags
- You can manually trigger the workflow from the Actions tab

### Manual Updates
```bash
# Re-run the mirror script to pull latest versions
./scripts/mirror.sh
```

## 🛡️ Security Considerations

1. **Token Security:**
   - Never commit GitHub tokens to your repository
   - Use GitHub Secrets for tokens in workflows
   - Regularly rotate your personal access tokens

2. **Image Verification:**
   - Skopeo preserves image signatures and metadata
   - Consider implementing additional security scanning

3. **Access Control:**
   - Set appropriate visibility for your mirrored images
   - Use private packages for sensitive images

## 📚 Additional Resources

- [Skopeo Documentation](https://github.com/containers/skopeo)
- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Hub Rate Limiting](https://docs.docker.com/docker-hub/download-rate-limit/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally using the mirror script
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details. 