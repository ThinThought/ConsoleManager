#!/usr/bin/env python3
"""Compatibility shim that forwards to gamesdb.cli."""

from gamesdb.cli import main


if __name__ == "__main__":
    main()
