# 1NST4-CH3K - Instagram Account Checker

<div align="center">
  <img src="./image.png" alt="1NST4-CH3K Logo" width="80%">
  <p><strong>🔥 Instagram account validation tool with proxy support and multi-threading 🔥</strong></p>
</div>

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Made by d4x3d](https://img.shields.io/badge/made%20by-d4x3d-red.svg)](https://github.com/d4x3d)
## Features
- Multi-threaded checking
- Proxy rotation and health checking
- Beautiful CLI with colors
- Rate limiting and error handling

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/d4x3d/1NST4-CH3K.git
   cd 1NST4-CH3K
   uv venv .venv && source .venv/bin/activate
   uv add requests click rich pyyaml pydantic
   ```

2. **Run:**
   ```bash
   python main.py --help
   ```

## Usage

- Single email: `python main.py --email user@example.com`
- From file: `python main.py --file accounts.txt --threads 10`
- With proxies: `python main.py --file accounts.txt --proxy proxies.txt`

## Options

| Option | Description |
|--------|-------------|
| `--email` | Single email to check |
| `--file` | File with emails |
| `--threads` | Number of threads |
| `--proxy` | Proxy file |
| `--output` | Output file |

## License
MIT License - [d4x3d](https://github.com/d4x3d)

---

<div align="center">
  <p><strong>⭐ Star if useful! ⭐</strong></p>
</div>
