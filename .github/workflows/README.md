# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the frappe-hrms-tools repository.

## Available Workflows

### Docker Build and Push (`docker-build.yml`)

Automatically builds and tests the CV Analysis Service Docker image.

**Triggers:**
- Push to `main` branch (builds and pushes to registry)
- Push to `claude/**` branches (builds only)
- Pull requests to `main` (builds and tests only)
- Manual workflow dispatch

**Features:**
- ✅ Builds Docker image for CV Analysis Service
- ✅ Runs health checks to verify the image works
- ✅ Pushes to GitHub Container Registry (ghcr.io) on main branch
- ✅ Uses layer caching for faster builds
- ✅ Multi-tagging strategy (branch, sha, latest)

**Image Registry:**
- Registry: `ghcr.io`
- Image: `ghcr.io/tekdi/frappe-hrms-tools/cv-analysis-service`

**Image Tags:**
- `latest` - Latest build from main branch
- `main` - Latest build from main branch
- `<branch-name>` - Latest build from specific branch
- `<branch-name>-<sha>` - Specific commit from a branch

## Using the Docker Images

### Pull from GitHub Container Registry

```bash
# Pull latest version
docker pull ghcr.io/tekdi/frappe-hrms-tools/cv-analysis-service:latest

# Pull specific version
docker pull ghcr.io/tekdi/frappe-hrms-tools/cv-analysis-service:main
```

### Run the container

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e DEFAULT_LLM_PROVIDER=openai \
  --name cv-analysis \
  ghcr.io/tekdi/frappe-hrms-tools/cv-analysis-service:latest
```

### Using with docker-compose

```yaml
services:
  cv-analysis-service:
    image: ghcr.io/tekdi/frappe-hrms-tools/cv-analysis-service:latest
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEFAULT_LLM_PROVIDER=openai
    volumes:
      - ./database:/app/database
```

## Manual Workflow Dispatch

You can manually trigger the Docker build workflow:

1. Go to **Actions** tab in GitHub
2. Select **Docker Build and Push** workflow
3. Click **Run workflow**
4. Choose:
   - Branch to build from
   - Whether to push the image to registry

## Authentication for Private Images

If the repository is private, you'll need to authenticate:

```bash
# Create a GitHub Personal Access Token with read:packages scope
# Then login:
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Now you can pull images
docker pull ghcr.io/tekdi/frappe-hrms-tools/cv-analysis-service:latest
```

## Workflow Status Badge

Add this badge to your README to show build status:

```markdown
[![Docker Build](https://github.com/tekdi/frappe-hrms-tools/actions/workflows/docker-build.yml/badge.svg)](https://github.com/tekdi/frappe-hrms-tools/actions/workflows/docker-build.yml)
```

## Troubleshooting

### Build fails with "permission denied"

The workflow needs `packages: write` permission. This should be automatic for the repository, but if issues persist:
1. Go to repository **Settings**
2. Navigate to **Actions** → **General**
3. Under "Workflow permissions", ensure "Read and write permissions" is selected

### Image push fails

Ensure:
1. The workflow has `packages: write` permission
2. You're pushing to the main branch or using manual dispatch
3. GitHub Container Registry is enabled for your organization

### Tests fail

The workflow runs basic health checks on the built image. If tests fail:
1. Check the logs in the Actions tab
2. Verify the Dockerfile is correct
3. Ensure the service starts properly without API keys (it should still return health status)

## Development

To test the workflow locally before pushing:

```bash
# Build the image
docker build -t cv-analysis-service:test ./services/hrms-tools

# Test it
docker run -d --name test -p 8000:8000 cv-analysis-service:test
curl http://localhost:8000/api/v1/health
docker stop test && docker rm test
```

## Related Documentation

- [Docker Build and Push Action](https://github.com/docker/build-push-action)
- [Docker Metadata Action](https://github.com/docker/metadata-action)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
