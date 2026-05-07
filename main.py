#!/usr/bin/env python
# -*- coding: utf-8 -*-

print("[DIAG] Skrypt titan_Launcher.py (główny) rozpoczął wczytywanie...")

import wx # Dla wx.App w TCE_manager, jeśli TCE_manager tworzy własną instancję
import sys
import os
import traceback

# --- Importy nowych modułów ---
try:
    import installer
    import TCE_manager
    print("[DIAG] Moduły installer i TCE_manager zaimportowane.")
except ImportError as e_mod_import:
    print(f"[BŁĄD KRYTYCZNY] Nie można zaimportować modułów installer lub TCE_manager: {e_mod_import}")
    traceback.print_exc()
    input("Naciśnij Enter, aby zakończyć z powodu błędu krytycznego importu...")
    sys.exit(1)
except Exception as e_mod_general: # Na wypadek innych błędów w modułach na poziomie importu
    print(f"[BŁĄD KRYTYCZNY] Nieoczekiwany błąd podczas importu modułów: {e_mod_general}")
    traceback.print_exc()
    input("Naciśnij Enter, aby zakończyć z powodu błędu krytycznego importu...")
    sys.exit(1)


try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    print(f"[DIAG] Katalog skryptu (SCRIPT_DIR): {SCRIPT_DIR}")
except Exception:
    SCRIPT_DIR = os.getcwd() # Fallback
    print(f"[OSTRZEŻENIE] Nie udało się ustalić SCRIPT_DIR, używam CWD: {SCRIPT_DIR}")

# --- Globalne Stałe dla tego pliku (minimalne) ---
COMMAND_LINE_ARG_TCE_PACKAGE = "--install-tcepackage"
PERSISTENT_PACKAGE_HANDLER_EXE_NAME = "TitanPackageHandler.exe" # Używane w installer.py i TCE_manager.py
HANDLER_CONFIG_FILENAME = "handler_paths.json" # Używane w installer.py i TCE_manager.py
METADATA_FILENAME_IN_PACKAGE = "__script.TCE" # Używane w TCE_manager.py

def main():
    print(f"[DIAG] __main__ blok osiągnięty. Argumenty: {sys.argv}")
    run_package_handler_mode = False
    package_file_arg = None

    # Utwórz słownik z podstawowymi ścieżkami i konfiguracją
    # Te wartości będą używane przez oba moduły do konstruowania własnych pełnych ścieżek
    base_config = {
        "SCRIPT_DIR": SCRIPT_DIR,
        "MAIN_INSTALLER_INSTALL_DIR": os.path.join(SCRIPT_DIR, "titan_data"),
        "MAIN_APP_EXE_PATH_FOR_SHORTCUT": os.path.join(SCRIPT_DIR, "titan_data", "titan.exe"),  # Środowisko Titan dla skrótu
        "BIN_DIR": os.path.join(SCRIPT_DIR, "bin"), # Katalog z wget.exe, 7z.exe
        "SFX_DIR": os.path.join(SCRIPT_DIR, "sfx"),
        "README_FILE": os.path.join(SCRIPT_DIR, "czytajto.txt"),
        # Stałe nazwy plików i argumentów
        "PERSISTENT_PACKAGE_HANDLER_EXE_NAME": PERSISTENT_PACKAGE_HANDLER_EXE_NAME,
        "COMMAND_LINE_ARG_TCE_PACKAGE": COMMAND_LINE_ARG_TCE_PACKAGE,
        "HANDLER_CONFIG_FILENAME": HANDLER_CONFIG_FILENAME,
        "METADATA_FILENAME_IN_PACKAGE": METADATA_FILENAME_IN_PACKAGE,
        # Domyślne ustawienia
        "CREATE_DESKTOP_SHORTCUT_DEFAULT": True, # Te wartości mogą być odczytywane przez installer.py
        "REGISTER_TCEPACKAGE_DEFAULT": True,
        # URL-e mogą być również tutaj, jeśli oba moduły ich potrzebują,
        # lub lepiej w module 'installer.py' jeśli tylko on ich używa.
        "URL_MAIN": "http://www.titosofttitan.com/titan/titan.main.7z",
        "URL_INTERPRETER": "http://www.titosofttitan.com/titan/titan.interpreter.7z",
        "URL_SOUND_THEMES": "http://www.titosofttitan.com/titan/titan.soundthemes.7z"
    }
    # Przekaż pełne ścieżki do narzędzi, aby moduły nie musiały ich budować
    base_config["WGET_PATH"] = os.path.join(base_config["BIN_DIR"], "wget.exe")
    base_config["SEVENZ_PATH"] = os.path.join(base_config["BIN_DIR"], "7z.exe")


    if len(sys.argv) > 1 and sys.argv[1] == base_config["COMMAND_LINE_ARG_TCE_PACKAGE"]:
        if len(sys.argv) > 2:
            package_file_arg = sys.argv[2]
            run_package_handler_mode = True
            print(f"[DIAG] Wykryto tryb obsługi pakietu dla: {package_file_arg}")
        else:
            print(f"[OSTRZEŻENIE] Argument {base_config['COMMAND_LINE_ARG_TCE_PACKAGE']} podany bez ścieżki pliku.")
    
    if run_package_handler_mode and package_file_arg:
        try:
            TCE_manager.handle_tce_package_cli(package_file_arg, base_config)
        except Exception as e_main_pkg:
            print(f"[BŁĄD KRYTYCZNY w TCE_manager.handle_tce_package_cli]: {e_main_pkg}")
            traceback.print_exc()
            # Próba wyświetlenia błędu w prostym oknie, jeśli wx jest dostępne
            try:
                app_err = wx.App()
                wx.MessageBox(f"Wystąpił krytyczny błąd podczas obsługi pakietu:\n{e_main_pkg}\n\nSprawdź konsolę po szczegóły.", "Błąd Krytyczny TCE Managera", wx.OK | wx.ICON_ERROR)
            except Exception:
                pass # Jeśli nawet to zawiedzie, błąd jest już w konsoli
    else:
        try:
            installer.run_main_installer(base_config)
        except Exception as e_main_inst:
            print(f"[BŁĄD KRYTYCZNY w installer.run_main_installer]: {e_main_inst}")
            traceback.print_exc()
            if not (wx.GetApp() and wx.GetApp().IsMainLoopRunning()): # Sprawdź, czy wx.App już działa
                 print("!!! BŁĄD KRYTYCZNY PRZED STARTEM GUI INSTALATORA !!!")
                 try: # Ostateczna próba poinformowania użytkownika
                     app_err = wx.App()
                     wx.MessageBox(f"Wystąpił krytyczny błąd podczas uruchamiania instalatora:\n{e_main_inst}\n\nSprawdź konsolę po szczegóły.", "Błąd Krytyczny Instalatora", wx.OK | wx.ICON_ERROR)
                 except Exception:
                     pass


    print("[DIAG] Główny blok __main__ zakończył działanie.")

if __name__ == "__main__":
    # Pygame quit jest teraz zarządzany wewnątrz modułów, gdy kończą swoją pracę z wx.App
    # lub w OnExit aplikacji wx.
    main()