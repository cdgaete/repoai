# src/repoai/__main__.py

import argparse
import os
import sys
from pathlib import Path

def parser():
    parser = argparse.ArgumentParser(description='RepoAI Streamlit App')
    parser.add_argument('--root_path', help='Root path for the project', type=str, default=os.getcwd())
    parser.add_argument('--port', help='Port for the Streamlit server', type=int, default=8501)
    parser.add_argument('--address', help='Address for the Streamlit server', type=str, default='localhost')
    return parser.parse_args()

def main():
    args = parser()

    root_path = Path(args.root_path)
    if not root_path.exists():
        raise FileNotFoundError(f'The specified root path does not exist: {root_path}')

    try:
        from streamlit.web import cli as stcli
    except ImportError as exc:
        raise ImportError("Streamlit is not installed. Please install it using 'pip install streamlit'.") from exc

    sys.argv = [
        "streamlit", "run",
        str(Path(__file__).parent / "server" / "app.py"),
        "--server.port", str(args.port),
        "--server.address", args.address,
        "--",
        f"--root_path={args.root_path}"
    ]
    sys.exit(stcli.main())

if __name__ == '__main__':
    main()