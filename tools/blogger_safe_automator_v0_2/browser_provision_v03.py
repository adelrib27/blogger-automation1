#!/usr/bin/env python3
"""Compatibilidade: usa a implementação consolidada em browser_provision.py."""

from browser_provision import main


if __name__ == "__main__":
    raise SystemExit(main())
