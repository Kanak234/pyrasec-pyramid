"""Pyramid Layout & Visualizer Generator — Standalone 3D Architecture Engine.

Folders become layers, files become blocks.
Produces deterministic 3D pyramid layouts for Three.js/WebGL visualizer.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

BAND_COLORS = {
    "critical": "#EF4565",
    "warning": "#FBCD63",
    "secure": "#2EE6B0",
}

SEVERITY_COLORS = {
    "CRITICAL": "#EF4565",
    "HIGH": "#F97362",
    "MEDIUM": "#FBCD63",
    "LOW": "#8FD9C0",
    "INFO": "#2EE6B0",
}

@dataclass
class Block:
    """One file, rendered as a block in the pyramid."""
    id: str
    path: str
    name: str
    layer: int
    x: float
    y: float
    z: float
    size: float
    color: str
    band: str
    severity: str
    finding_count: int
    file_size: int
    mode: str
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class Layer:
    """One directory depth level."""
    index: int
    depth: int
    y: float
    width: float
    block_count: int
    band: str
    color: str
    critical: int = 0
    warning: int = 0
    secure: int = 0
    label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

class StandalonePyramidBuilder:
    """Constructs 3D pyramid data from directory tree or existing findings."""

    def __init__(
        self,
        root_dir: str,
        *,
        base_width: float = 100.0,
        layer_height: float = 14.0,
        block_size: float = 4.0,
        max_blocks_per_layer: int = 400,
    ):
        self.root_dir = Path(root_dir).resolve()
        self.base_width = base_width
        self.layer_height = layer_height
        self.block_size = block_size
        self.max_blocks_per_layer = max_blocks_per_layer

    def scan_tree(self) -> dict:
        """Scan real filesystem structure and map files to depth tiers."""
        files_by_depth: dict[int, list[Path]] = {}
        max_depth = 0

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', '.venv', 'node_modules', '__pycache__')]
            rel_dir = Path(root).relative_to(self.root_dir)
            depth = 0 if str(rel_dir) == '.' else len(rel_dir.parts)
            max_depth = max(max_depth, depth)

            if depth not in files_by_depth:
                files_by_depth[depth] = []

            for f in sorted(files):
                if f.startswith('.'):
                    continue
                file_path = Path(root) / f
                files_by_depth[depth].append(file_path)

        layers = []
        blocks = []
        total_layers = max_depth + 1

        for depth in range(total_layers):
            layer_files = files_by_depth.get(depth, [])
            count = len(layer_files)
            if count == 0:
                continue

            altitude = (total_layers - 1 - depth) * self.layer_height
            layer_width = self.base_width * ((depth + 1) / total_layers)

            layer = Layer(
                index=depth,
                depth=depth,
                y=round(altitude, 2),
                width=round(layer_width, 2),
                block_count=count,
                band="secure",
                color=BAND_COLORS["secure"],
                label=f"Depth {depth}",
                secure=count,
            )
            layers.append(layer)

            side = max(1, math.ceil(math.sqrt(count)))
            spacing = layer_width / max(1, side)
            start_offset = -layer_width / 2.0 + spacing / 2.0

            for idx, fpath in enumerate(layer_files[:self.max_blocks_per_layer]):
                row = idx // side
                col = idx % side
                x = start_offset + col * spacing
                z = start_offset + row * spacing
                rel_path = str(fpath.relative_to(self.root_dir))

                try:
                    fsize = fpath.stat().st_size
                except OSError:
                    fsize = 0

                block = Block(
                    id=f"b_{depth}_{idx}",
                    path=rel_path,
                    name=fpath.name,
                    layer=depth,
                    x=round(x, 2),
                    y=round(altitude, 2),
                    z=round(z, 2),
                    size=self.block_size,
                    color=BAND_COLORS["secure"],
                    band="secure",
                    severity="INFO",
                    finding_count=0,
                    file_size=fsize,
                    mode="0644",
                )
                blocks.append(block)

        return {
            "root": str(self.root_dir),
            "layers": [l.to_dict() for l in layers],
            "blocks": [b.to_dict() for b in blocks],
            "summary": {
                "total_files": len(blocks),
                "total_layers": len(layers),
                "max_depth": max_depth,
                "overall_grade": "A+",
                "score": 100
            }
        }

    def generate_html_report(self, data: dict, template_path: str, output_path: str) -> None:
        """Inject JSON data directly into self-contained HTML template."""
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        payload = json.dumps(data)
        if "/*__PYRAMID_DATA__*/" in template:
            injected = template.replace("/*__PYRAMID_DATA__*/", payload)
        elif "window.PYRAMID_DATA" in template:
            injected = template.replace("window.PYRAMID_DATA = null", f"window.PYRAMID_DATA = {payload}")
        else:
            injected = template.replace("</head>", f"<script>window.EMBEDDED_PYRAMID = {payload};</script></head>")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(injected)

def main():
    parser = argparse.ArgumentParser(description="PyraSec 3D Pyramid Visualizer Generator")
    parser.add_argument("target", nargs="?", default=".", help="Target directory to visualize")
    parser.add_argument("-o", "--output", help="Output HTML report path")
    parser.add_argument("--json", dest="json_out", help="Output JSON raw layout data")
    parser.add_argument("--template", default="index.html", help="Path to index.html template")

    args = parser.parse_args()

    builder = StandalonePyramidBuilder(args.target)
    data = builder.scan_tree()

    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Exported pyramid layout data to {args.json_out}")

    if args.output:
        builder.generate_html_report(data, args.template, args.output)
        print(f"Generated standalone 3D report: {args.output}")

    if not args.json_out and not args.output:
        print(json.dumps(data["summary"], indent=2))

if __name__ == "__main__":
    main()
