# 1NST4-CH3K - Instagram Account Checker

<div align="center">
  <p><strong>🔥 A powerful Instagram account validation tool with proxy support, multi-threading, and beautiful CLI interface 🔥</strong></p>
</div>

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Made by d4x3d](https://img.shields.io/badge/made%20by-d4x3d-red.svg)](https://github.com/d4x3d)

</div>

## 🌟 Features

- **🚀 High Performance**: Multi-threaded checking with configurable thread pools
- **📡 Proxy Support**: Full proxy rotation and health checking
- **🎨 Beautiful UI**: Instagram-themed CLI with colors and ASCII art
- **⚡ Rate Limiting**: Intelligent rate limiting with adaptive controls
- **📊 Rich Output**: Live progress tracking and detailed results
- **🔧 Configurable**: YAML configuration files and command-line options
- **📦 Cross-Platform**: Single executable bundling for any system
- **🛡️ Error Handling**: Robust error handling and retry mechanisms

## 📸 Screenshots

<div align="center">
  <img src="assets/banner.png" alt="1NST4-CH3K Banner" width="80%">
  <p><em>Beautiful ASCII art banner with Instagram-themed styling</em></p>
</div>

<div align="center">
  <img src="assets/interface.png" alt="CLI Interface" width="80%">
  <p><em>Rich CLI interface with live progress and results</em></p>
</div>

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/d4x3d/1NST4-CH3K.git
   cd 1NST4-CH3K
   ```

2. **Set up virtual environment:**
   ```bash
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   uv add requests click rich pyyaml pydantic
   ```

4. **Run the tool:**
   ```bash
   python main.py --help
   ```

### Basic Usage

#### Check a single email:
```bash
python main.py --email user@example.com
```

#### Check multiple accounts from file:
```bash
python main.py --file accounts.txt --threads 10 --delay 2.0
```

#### Use with proxies:
```bash
python main.py --file accounts.txt --proxy proxies.txt --threads 20
```

#### Save results to file:
```bash
python main.py --file accounts.txt --output results.json
```

## 📖 Command Line Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--email` | `-e` | Single email/username to check | `--email user@example.com` |
| `--file` | `-f` | File containing emails/usernames | `--file accounts.txt` |
| `--threads` | `-t` | Number of threads | `--threads 10` |
| `--delay` | `-d` | Delay between requests (seconds) | `--delay 2.0` |
| `--proxy` | | Proxy list file | `--proxy proxies.txt` |
| `--output` | `-o` | Output file (JSON/CSV) | `--output results.json` |
| `--batch` | | Batch mode (same as --file) | `--batch accounts.txt` |

## 📁 Project Structure

```
1NST4-CH3K/
├── main.py                 # Entry point
├── core/                   # Core functionality
│   ├── checker.py         # Instagram API checker
│   ├── proxy.py           # Proxy management
│   └── threads.py         # Threading utilities
├── ui/                    # User interface
│   └── display.py         # CLI display and formatting
├── utils/                 # Utilities
│   └── config.py          # Configuration management
├── data/                  # Data files
│   ├── config.yaml       # Default configuration
│   └── proxies.txt       # Sample proxy list
├── output/               # Generated output files
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## ⚙️ Configuration

Create a `config.yaml` file to customize settings:

```yaml
checker:
  timeout: 10
  delay_between_requests: 1.0
  max_threads: 5
  requests_per_second: 1.0
  proxy_file: "proxies.txt"
  show_colors: true
  show_progress: true
```

## 📋 Input File Formats

### Email List (accounts.txt):
```
user1@example.com
user2@gmail.com
instagram@handle.com
```

### Proxy List (proxies.txt):
```
# HTTP proxies
192.168.1.1:8080
proxy.example.com:3128

# HTTP with authentication
proxy.example.com:8080:user:pass

# SOCKS5 proxies
socks5://proxy.example.com:1080
```

## 🔧 Advanced Features

### Proxy Management

The tool supports multiple proxy formats and automatic health checking:

- **HTTP/HTTPS proxies**: `host:port`
- **Authenticated proxies**: `host:port:username:password`
- **SOCKS5 proxies**: `socks5://host:port`
- **Auto-rotation**: Proxies are rotated automatically
- **Health checking**: Dead proxies are automatically removed

### Threading & Performance

- **Thread pools**: Configurable number of worker threads
- **Rate limiting**: Built-in rate limiting to avoid detection
- **Adaptive rate control**: Automatically adjusts based on response times
- **Connection pooling**: Efficient HTTP connection management

### Output Formats

#### JSON Output:
```json
[
  {
    "email": "user@example.com",
    "result": "valid",
    "message": "Account exists",
    "response_time": 1.23
  }
]
```

#### CSV Output:
```csv
email,result,message,response_time
user@example.com,valid,Account exists,1.23
```

## 🛠️ Development

### Adding New Features

1. **Core functionality**: Add to `core/` modules
2. **UI components**: Modify `ui/display.py`
3. **Configuration**: Update `utils/config.py`
4. **Tests**: Add test files in `tests/` directory

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Add docstrings for public functions
- Handle exceptions gracefully

## 📦 Building Executable

### Using PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole main.py
```

### Using PyOxidizer:
```bash
pip install pyoxidizer
pyoxidizer build
```

## 🔒 Security & Ethics

⚠️ **Important Disclaimers:**

- This tool is for educational purposes only
- Respect Instagram's Terms of Service
- Use proxies responsibly and legally
- Do not use for spam or malicious activities
- The author is not responsible for misuse

## 🐛 Troubleshooting

### Common Issues

**CSRF Token Errors:**
- Instagram may have updated their API
- Try using different proxies
- Increase delay between requests

**Proxy Connection Errors:**
- Check proxy format in proxy file
- Verify proxy credentials
- Test proxies with `curl` or similar tools

**Threading Issues:**
- Reduce thread count if experiencing crashes
- Increase delay between requests
- Check system resource usage

## 📈 Performance Tips

1. **Use quality proxies** for better success rates
2. **Adjust thread count** based on your system resources
3. **Increase delays** to avoid rate limiting
4. **Use proxy rotation** for better anonymity
5. **Monitor response times** and adjust accordingly

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

**Created by:** [d4x3d](https://github.com/d4x3d)
**Tool Name:** 1NST4-CH3K
**Powered by:** Python, Rich, Requests, and the open-source community

---

<div align="center">
  <p><strong>⭐ If you find this tool useful, please give it a star! ⭐</strong></p>
  <p>Made with ❤️ for the security research community</p>
</div>