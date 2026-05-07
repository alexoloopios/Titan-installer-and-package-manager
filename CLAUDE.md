# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TCE (Titan Computing Environment) is a Polish-language software installation and management system. The codebase consists of several Python modules that work together to provide:

- **Package Installation**: TCE_manager.py handles .TCEPACKAGE file processing and installation
- **System Installation**: installer.py provides GUI-based system installer with audio feedback
- **Configuration Management**: settingsgui.py provides GUI for system settings
- **Main Launcher**: titan.py serves as the entry point coordinating all modules

## Core Architecture

### Main Components
- `titan.py` - Main entry point and module coordinator
- `installer.py` - System installer with wxPython GUI and pygame audio
- `TCE_manager.py` - Package manager for .TCEPACKAGE files
- `settingsgui.py` - Settings interface with system volume control
- `settings.py` - Cross-platform settings file management

### Key Features
- **Audio Feedback**: Uses pygame for system sounds stored in sfx/ directory
- **Package System**: Custom .TCEPACKAGE format with __script.TCE configuration files
- **Cross-Platform**: Supports Windows, Linux, and macOS with platform-specific paths
- **GUI Framework**: Built on wxPython for all user interfaces

## Development Commands

### Running the Application
```bash
python main.py
```

### Running Individual Components
```bash
python settingsgui.py    # Settings GUI only
python installer.py      # Installer GUI only
```

### Compilation
```bash
compile.bat              # Compile with Nuitka (creates TitanInstaller.exe)
```

### Dependencies
The project requires:
- wxPython (wx)
- pygame (optional, for audio)
- pycaw + comtypes (Windows volume control)
- winshell, winreg (Windows-specific features)
- nuitka (for compilation)

## File Structure

### Important Directories
- `bin/` - Contains 7-zip binaries (7z.exe, 7z.dll) and wget.exe
- `sfx/` - Audio files (.ogg, .wav) for system feedback sounds
- `__pycache__/` - Python bytecode cache

### Configuration Files
- `.env` - Contains API keys (GEMINI_API_KEY)
- `czytajto.txt` - Installation notes and warnings (Polish)
- `documentation.txt` - TCE package format specification (Polish)
- `version_info.txt` - Version metadata for compiled executable
- `app.manifest` - Windows manifest for UAC and compatibility
- `ANTIVIRUS_FALSE_POSITIVES.md` - Guide for resolving antivirus false positives

## Package Management

The TCE system uses .TCEPACKAGE files containing:
- Application files to be extracted to titan_data directory
- `__script.TCE` configuration file with metadata and install_tasks
- Support for cmd() commands in install_tasks for post-installation scripts

## Audio System

Each module has its own audio initialization:
- `installer.py` uses `SFX_PATHS` and `init_pygame_audio_installer()`
- `TCE_manager.py` uses `SFX_PATHS_TCE` and `init_pygame_audio_tce()`
- Sound files are referenced by keys and played via `play_sound_*()` functions

## Settings Management

Settings are stored in platform-specific locations:
- Windows: `%APPDATA%\titosoft\Titan\bg5settings.ini`
- Linux: `~/.config/titosoft/Titan/bg5settings.ini`
- macOS: `~/Library/Application Support/titosoft/Titan/bg5settings.ini`