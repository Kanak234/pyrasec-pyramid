# PyraSec 3D Pyramid Visualizer

[![CI](https://github.com/Kanak234/pyrasec-pyramid/actions/workflows/ci.yml/badge.svg)](https://github.com/Kanak234/pyrasec-pyramid/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

An interactive 3D WebGL / Three.js visualizer for codebases and security vulnerability trees.

## Philosophy

- **Folders become layers**: The project root sits at the apex, and deeper directories expand outwards as the foundation.
- **Files become blocks**: Each file is rendered as a 3D block colored according to security findings (Critical: Red, Warning: Amber, Secure: Emerald).
- **Self-contained**: Operates locally over `file://` with no node servers or internet access required.

## Quick Start

### 1. View Standalone Demo
Open `index.html` in any modern web browser.

### 2. Generate 3D Pyramid for any Codebase
```bash
python3 pyramid.py /path/to/project -o report.html
```
Open `report.html` to explore the 3D topology of your repository.

### 3. Export Raw JSON Geometry
```bash
python3 pyramid.py /path/to/project --json pyramid.json
```

## Running Tests
```bash
pytest tests/ -v
```
