# Python 2D Shooter

Physics-based 2D shooter game developed in Python adhering to ECS (Entity-Component System) demonstrating Convex Collision Detection and Resolution using the Separating Axis Theorem (SAT) and Minimum Translation Vector (MTV).

## Getting Started

### Requirements

- Python 3.14
- pip

### Installation

Clone the repository and navigate to its root directory.

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Usage

With the virtual environment activated, from any directory:

```bash
shooter
```

Or, to see console output while developing:

```bash
python -m game
```

## Building an executable

Install the build tools into your virtual environment, from the repository root:

```bash
python -m pip install -e ".[build]"
```

Then build:

**Windows (PowerShell)**

```powershell
pyinstaller --noconfirm --windowed --name Shooter --paths src --add-data "src/assets;assets" run.py
```

**Linux / macOS**

```bash
pyinstaller --noconfirm --windowed --name Shooter --paths src --add-data "src/assets:assets" run.py
```

The result is in `dist/Shooter/`. Distribute the whole folder (zip it), not just the executable.

If the executable closes immediately, rebuild without `--windowed` and run it from a terminal to see the error.
