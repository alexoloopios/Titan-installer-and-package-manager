@echo off
echo Kompilacja Titan Installer z Nuitka...
echo.

python -m nuitka main.py ^
  --standalone ^
  --onefile ^
  --remove-output ^
  --msvc=14.3 ^
  --lto=no ^
  --no-pyi-file ^
  --windows-disable-console ^
  --company-name="TitoSoft" ^
  --product-name="Titan Computing Environment" ^
  --file-version=1.0.0.0 ^
  --product-version=1.0.0.0 ^
  --file-description="Titan Computing Environment Installer" ^
  --copyright="Copyright (C) 2026 TitoSoft" ^
  --output-filename=TitanInstaller.exe ^
  --include-data-dir=bin=bin ^
  --include-data-dir=sfx=sfx ^
  --include-data-file=czytajto.txt=czytajto.txt ^
  --include-data-file=.env=.env ^
  --enable-plugin=anti-bloat ^
  --assume-yes-for-downloads

echo.
echo Kompilacja zakonczona!
pause
