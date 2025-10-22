#!/usr/bin/env python3
"""
Build Script for 1NST4-CH3K

This script creates standalone executables for Windows, macOS, and Linux
using PyInstaller.
"""

import os
import sys
import subprocess
from pathlib import Path


class Builder:
    """Build manager for creating executables."""

    def __init__(self):
        """Initialize the builder."""
        self.project_root = Path(__file__).parent
        self.main_script = self.project_root / "main.py"
        self.output_dir = self.project_root / "dist"

    def install_pyinstaller(self):
        """Install PyInstaller if not available."""
        try:
            import PyInstaller
            print("✅ PyInstaller already installed")
        except ImportError:
            print("📦 Installing PyInstaller...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "pyinstaller"
            ])

    def create_spec_file(self, platform: str = "auto"):
        """Create PyInstaller spec file."""
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('README.md', '.'),
        ('utils', 'utils'),
        ('core', 'core'),
        ('ui', 'ui'),
    ],
    hiddenimports=[
        'core.checker',
        'core.proxy',
        'core.threads',
        'ui.display',
        'utils.config',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='1nst4-ch3k',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='1nst4-ch3k',
)
'''
        spec_path = self.project_root / "1nst4-ch3k.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)

        print(f"📄 Created spec file: {spec_path}")
        return spec_path

    def build_executable(self, platform: str = "auto", onefile: bool = True):
        """
        Build executable using PyInstaller.

        Args:
            platform: Target platform (auto, win32, darwin, linux)
            onefile: Create single file executable
        """
        print(f"🔨 Building executable for {platform}...")

        cmd = ["pyinstaller"]

        if onefile:
            cmd.append("--onefile")
            print("📦 Building single file executable")

        cmd.extend([
            "--name", "1nst4-ch3k",
            "--console",
            "--clean",
            "--noconfirm"
        ])

        # Platform specific options
        if platform == "win32":
            cmd.extend([
                "--upx-dir", "upx394w",
                "--version-file", "version.txt"
            ])
        elif platform == "darwin":
            cmd.extend([
                "--target-arch", "universal2",
                "--codesign-identity", "Developer ID Application"
            ])

        cmd.append("main.py")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )

            if result.returncode == 0:
                print("✅ Build completed successfully!")
                self.print_build_info()
            else:
                print("❌ Build failed!")
                print(f"Error: {result.stderr}")
                return False

        except KeyboardInterrupt:
            print("\n🛑 Build cancelled by user")
            return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False

        return True

    def print_build_info(self):
        """Print information about the build."""
        print("\n📋 Build Information:")
        print("=" * 50)

        if self.output_dir.exists():
            executables = list(self.output_dir.glob("1nst4-ch3k*"))
            for exe in executables:
                size = exe.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"📦 {exe.name} ({size:.1f}MB)")

        print(f"\n📍 Output directory: {self.output_dir}")
        print("\n🚀 To run the executable:")
        if os.name == 'nt':  # Windows
            print("   .\\dist\\1nst4-ch3k.exe --help")
        else:  # Unix-like
            print("   ./dist/1nst4-ch3k --help")

    def create_version_file(self):
        """Create version info file for Windows."""
        version_content = '''
# UTF-8

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'1NST4-CH3K'),
        StringStruct(u'FileDescription', u'Instagram Account Checker'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'1nst4-ch3k'),
        StringStruct(u'LegalCopyright', u'Created by d4x3d'),
        StringStruct(u'OriginalFilename', u'1nst4-ch3k.exe'),
        StringStruct(u'ProductName', u'1NST4-CH3K'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0, 1200])])
  ]
)
'''
        with open("version.txt", 'w', encoding='utf-8') as f:
            f.write(version_content)

    def clean_build(self):
        """Clean previous build files."""
        print("🧹 Cleaning previous builds...")

        build_dirs = ["build", "dist", "*.spec"]
        for pattern in build_dirs:
            for path in self.project_root.glob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)

        print("✅ Clean completed")

    def run_build(self, platform: str = "auto", clean: bool = True, onefile: bool = True):
        """
        Run complete build process.

        Args:
            platform: Target platform
            clean: Clean previous builds first
            onefile: Create single file executable
        """
        print("🚀 Starting 1NST4-CH3K build process...")
        print("=" * 60)

        # Clean previous builds
        if clean:
            self.clean_build()

        # Install PyInstaller
        self.install_pyinstaller()

        # Create version file for Windows
        if platform == "win32":
            self.create_version_file()

        # Create spec file
        self.create_spec_file(platform)

        # Build executable
        success = self.build_executable(platform, onefile)

        if success:
            print("\n🎉 Build process completed successfully!")
            print("\n📝 Next steps:")
            print("1. Test the executable")
            print("2. Distribute to target systems")
            print("3. Consider code signing for Windows/macOS")
        else:
            print("\n💥 Build process failed!")
            sys.exit(1)


def main():
    """Main build function."""
    import argparse

    parser = argparse.ArgumentParser(description="Build 1NST4-CH3K executable")
    parser.add_argument(
        "--platform",
        choices=["auto", "win32", "darwin", "linux"],
        default="auto",
        help="Target platform (default: auto)"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Don't clean previous builds"
    )
    parser.add_argument(
        "--multi-file",
        action="store_true",
        help="Create multi-file build instead of single file"
    )

    args = parser.parse_args()

    builder = Builder()
    builder.run_build(
        platform=args.platform,
        clean=not args.no_clean,
        onefile=not args.multi_file
    )


if __name__ == "__main__":
    main()