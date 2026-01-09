"""
Metaball viewer CLI.

Usage:

To run the metaball viewer:

```bash
metaball-viewer
```
"""

import tyro
from metaball_viewer import MetaBallViewer
from metaball_viewer.configs import ViewerConfig

def main():
    cfg = tyro.cli(ViewerConfig)
    
    viewer = MetaBallViewer(cfg)
    viewer.run()