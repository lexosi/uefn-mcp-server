"""Auto-start MCP listener when UEFN editor opens.

Place this file (or a copy) in your UEFN project's Content/Python/ directory.
It will be executed automatically when the editor starts.

Also copy uefn_listener.py to the same directory so it can be imported.
"""

import unreal


def _start_mcp():
    """Import and start the MCP listener."""
    try:
        import uefn_listener

        # Importing the module already auto-starts the listener. Calling
        # start_listener() again is idempotent: it returns the already-bound
        # port if a listener is running, or starts one if it is not.
        port = uefn_listener.start_listener()
        unreal.log(f"[MCP] Listener running on port {port}")
    except ImportError:
        unreal.log_warning(
            "[MCP] uefn_listener.py not found in Python path. "
            "Copy it to Content/Python/ or add its directory to sys.path."
        )
    except Exception as e:
        unreal.log_error(f"[MCP] Auto-start failed: {e}")


_start_mcp()
