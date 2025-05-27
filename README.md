# Docker Mirror 🪞

A Skopeo-based solution that automatically mirrors Docker Hub images to GitHub Container Registry (GHCR), helping you bypass Docker Hub rate limits and retention policies.

## ✨ Features

- 🔄 **Automatic mirroring** via GitHub Actions
- 📝 **YAML configuration** for easy management
- 🔁 **Retry logic** with configurable attempts and delays
- 📊 **Detailed logging** and summary reports
- 🏠 **Local execution** support for testing
- 🔒 **Secure** token handling
- 📅 **Scheduled updates** to catch latest tag changes

## 🚀 Quick Start

1. **Fork this repository** or use it as a template
2. **Edit `mirror-config.yaml`** to specify your images:
   ```yaml
   mirrors:
     - source: "docker.io/library/nginx"
       destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/nginx"
       tags: ["latest", "alpine"]
   ```
3. **Commit and push** - GitHub Actions will automatically mirror your images
4. **Use your mirrored images**:
   ```bash
   docker pull ghcr.io/yourusername/nginx:latest
   ```

## 📋 What's Included

- **`mirror-config.yaml`** - Configuration file with example images
- **`.github/workflows/mirror-images.yml`** - GitHub Actions workflow
- **`scripts/mirror.sh`** - Local execution script
- **`SETUP.md`** - Detailed setup and usage guide

## 🔧 Configuration Example

```yaml
mirrors:
  # Official images
  - source: "docker.io/library/nginx"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/nginx"
    tags: ["latest", "alpine", "1.25"]
  
  - source: "docker.io/library/postgres"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/postgres"
    tags: ["15", "15-alpine"]

  # Third-party images
  - source: "docker.io/traefik/traefik"
    destination: "ghcr.io/{{GITHUB_REPOSITORY_OWNER}}/traefik"
    tags: ["latest", "v3.0"]

settings:
  public: true
  retry_attempts: 3
  retry_delay: 30
```

## 🏃‍♂️ Usage

### Automatic (Recommended)
Just edit `mirror-config.yaml` and push - GitHub Actions handles the rest!

### Manual/Local
```bash
# Install dependencies (skopeo, yq)
sudo apt-get install skopeo

# Run the mirror script
./scripts/mirror.sh mirror-config.yaml yourusername your_github_token
```

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Complete setup and usage guide
- **[GitHub Container Registry Migration Guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/migrating-to-the-container-registry-from-the-docker-registry)**

## 🎯 Why Use This?

- **Avoid Docker Hub rate limits** (100 pulls/6h for anonymous, 200/6h for free accounts)
- **Bypass retention policies** (inactive images deleted after 6 months)
- **Faster pulls** from GitHub's CDN
- **Better integration** with GitHub-hosted projects
- **Free public packages** on GitHub

## 🔍 Monitoring

- Check the **Actions** tab for workflow runs
- View mirrored packages in your **Packages** tab
- Monitor logs for detailed mirror status

## 🤝 Contributing

Contributions welcome! Please read the setup guide and test locally before submitting PRs.

## 📄 License

MIT License - see [LICENSE.md](LICENSE.md) for details.

---

**Based on the GitHub Container Registry migration documentation and best practices from the Docker community.**
