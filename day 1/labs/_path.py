"""Makes `import agentcore` work when running a lab file directly.

Every lab starts with `import _path`. Without it, Python only searches the
labs/ folder and cannot see the agentcore package one level up.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
