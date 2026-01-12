"""
Metaball viewer CLI.

Usage:

To run the metaball viewer:

```bash
metaball-viewer
```

Various configuration options are available:

╭───────────────────────────────────────────────────────────────────────────────────────╮
| Options       | Description                                   | Type   | Default      |
|---------------|-----------------------------------------------|--------|--------------|
| --mode        | Viewer mode: 'live' or 'replay'.              | str    | live         |
| --host        | Host address for the ZMQ subscriber.          | str    | 127.0.0.1    |
| --port        | Port number for the ZMQ subscriber.           | int    | 6666         |
| --data-path   | Path to the data folder for replay mode.      | str    | None         |
╰───────────────────────────────────────────────────────────────────────────────────────╯
"""

import tyro
from metaball_viewer import MetaBallViewer
from metaball_viewer.configs import ViewerConfig

def main():
    cfg = tyro.cli(ViewerConfig)
    
    viewer = MetaBallViewer(cfg)
    viewer.run()