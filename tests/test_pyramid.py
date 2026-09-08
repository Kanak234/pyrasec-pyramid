import json
import tempfile
from pathlib import Path

from pyramid import Block, Layer, StandalonePyramidBuilder


def test_layer_and_block_dataclasses():
    layer = Layer(
        index=0, depth=0, y=28.0, width=50.0, block_count=5,
        band="secure", color="#2EE6B0", critical=0, warning=0, secure=5, label="Root"
    )
    d = layer.to_dict()
    assert d["depth"] == 0
    assert d["width"] == 50.0
    assert d["block_count"] == 5

    block = Block(
        id="b_0_0", path="src/main.py", name="main.py", layer=0,
        x=0.0, y=28.0, z=0.0, size=4.0, color="#2EE6B0",
        band="secure", severity="INFO", finding_count=0, file_size=1024, mode="0644"
    )
    bd = block.to_dict()
    assert bd["name"] == "main.py"
    assert bd["file_size"] == 1024

def test_scan_tree():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create hierarchy
        root = Path(tmpdir)
        (root / "file1.txt").write_text("hello")
        (root / "sub1").mkdir()
        (root / "sub1" / "file2.txt").write_text("world")
        (root / "sub1" / "sub2").mkdir()
        (root / "sub1" / "sub2" / "file3.txt").write_text("deep")

        builder = StandalonePyramidBuilder(tmpdir)
        data = builder.scan_tree()

        assert "layers" in data
        assert "blocks" in data
        assert "summary" in data
        assert data["summary"]["total_files"] == 3
        assert data["summary"]["max_depth"] == 2
        assert len(data["layers"]) == 3
        assert len(data["blocks"]) == 3

def test_html_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("print('test')")
        template = root / "template.html"
        template.write_text("<html><head></head><body>/*__PYRAMID_DATA__*/</body></html>")
        output = root / "report.html"

        builder = StandalonePyramidBuilder(tmpdir)
        data = builder.scan_tree()
        builder.generate_html_report(data, str(template), str(output))

        assert output.exists()
        content = output.read_text()
        assert "main.py" in content
        assert "summary" in content

def test_sample_pyramid_json_validity():
    sample_path = Path("/home/kanak/repos_workdir/pyrasec-pyramid/examples/sample-pyramid.json")
    if sample_path.exists():
        with open(sample_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "pyramid" in data or "layers" in data or "blocks" in data
