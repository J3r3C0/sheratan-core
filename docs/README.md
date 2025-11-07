# Sheratan Core API Documentation

This directory contains the generated API documentation for Sheratan Core.

The documentation is automatically generated from `openapi.yaml` and deployed to GitHub Pages.

## Viewing the Documentation

The live documentation is available at: https://j3rec0.github.io/sheratan-core/

## Building Locally

To build the documentation locally, you can use redoc-cli:

```bash
npm install -g redoc-cli
redoc-cli build openapi.yaml -o docs/index.html
```

## Automatic Deployment

The documentation is automatically deployed to GitHub Pages when:
- Changes are pushed to the `main` branch that affect `openapi.yaml`
- The workflow is manually triggered via the "Actions" tab

The deployment workflow can be found at `.github/workflows/openapi-docs.yml`.
