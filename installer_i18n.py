# installer_i18n.py
# Internationalization module for TCE Installer and Package Manager
print("[DIAG] Moduł installer_i18n.py rozpoczął wczytywanie...")

import locale
import settings

# ============================================================================
# Language Detection and Management
# ============================================================================

def detect_system_language():
    """
    Detects the system language.
    Returns 'pl' for Polish systems, 'en' for all others.
    """
    try:
        # Get system locale
        system_locale = locale.getdefaultlocale()
        if system_locale and system_locale[0]:
            lang_code = system_locale[0].lower()
            # Check if Polish
            if lang_code.startswith('pl'):
                return 'pl'
        # Default to English for all non-Polish systems
        return 'en'
    except Exception as e:
        print(f"[I18N] Error detecting system language: {e}")
        return 'en'  # Safe fallback


def get_installer_language():
    """
    Gets the installer language with priority:
    1. Saved setting in settings file
    2. Detected system language
    3. Default to Polish

    If no setting exists, detects and saves the system language.
    """
    try:
        # Try to get saved language setting
        saved_lang = settings.get_setting('language', default=None, section='general')

        if saved_lang:
            print(f"[I18N] Using saved language: {saved_lang}")
            return saved_lang

        # No saved setting - detect system language
        detected_lang = detect_system_language()
        print(f"[I18N] No saved language setting. Detected system language: {detected_lang}")

        # Save the detected language for future use
        try:
            settings.set_setting('language', detected_lang, section='general')
            print(f"[I18N] Saved detected language to settings: {detected_lang}")
        except Exception as e:
            print(f"[I18N] Warning: Could not save language setting: {e}")

        return detected_lang

    except Exception as e:
        print(f"[I18N] Error in get_installer_language: {e}")
        return 'pl'  # Safe fallback to Polish


# ============================================================================
# Translation Dictionaries
# ============================================================================

TRANSLATIONS = {
    'pl': {
        # ===== SettingsDialog =====
        'settings_dialog_title': 'Ustawienia instalatora',
        'cb_desktop_shortcut': 'Dodaj skrót na pulpit',
        'desc_desktop_shortcut': '  Tworzy skrót do programu Titan na pulpicie.',
        'section_shortcut': 'Skrót',
        'cb_register_extension': 'Zarejestruj rozszerzenie .TCEPACKAGE',
        'desc_register_extension': '  Rejestruje rozszerzenie .TCEPACKAGE, aby otwierać\n  pakiety danych bezpośrednio w środowisku Titan.\n  (Może wymagać uprawnień administratora).',
        'section_package_handling': 'Obsługa pakietów .TCEPACKAGE',
        'cb_background_music': 'Włącz muzykę w tle w trakcie instalacji',
        'desc_background_music': '  Odtwarza muzykę w tle podczas instalacji komponentów.',
        'section_background_music': 'Muzyka w tle',
        'section_language': 'Język / Language',
        'language_select_label': 'Wybierz język TCE / Select TCE language:',
        'desc_language': '  Ustawia język interfejsu środowiska Titan.\n  Sets the language of the Titan environment interface.',
        'btn_confirm': 'Zatwierdź',
        'btn_cancel': 'Anuluj',
        'language_pl': 'Polski',
        'language_en': 'English',

        # ===== StartFrame =====
        'start_frame_title': 'Konfigurator środowiska Titan',
        'start_frame_message': 'Zanim zaczniesz konfigurować Titana, przeczytaj to! Instalujesz wersję beta!',
        'btn_next': 'Dalej >',
        'readme_read_error': 'Błąd odczytu pliku \'{0}\'.',
        'readme_not_found': 'Błąd: Plik \'{0}\' nie został znaleziony.',

        # ===== ComponentsFrame =====
        'components_frame_title': 'Wybierz komponenty i ustawienia',
        'components_select_message': 'Wybierz komponenty, które chcesz zainstalować:',
        'section_components': 'Komponenty',
        'cb_tce_env': 'Środowisko TCE (niezbędne)',
        'cb_interpreter': 'Interpreter (Python)',
        'cb_sound_themes': 'Dodatkowe tematy dźwiękowe',
        'section_update': 'Aktualizacja',
        'cb_delete_before': 'Wyczyść ustawienia TCE',
        'desc_delete_before': '  Usuwa folder z ustawieniami TCE (%APPDATA%\\titosoft).',
        'btn_settings': 'Ustawienia instalatora...',
        'btn_install': 'Instaluj',

        # ===== FinishDialog =====
        'finish_dialog_title': 'Instalacja zakończona',
        'finish_message': 'Środowisko TCE zostało pomyślnie zainstalowane.',
        'cb_launch_titan': 'Uruchom środowisko Titan',
        'btn_finish': 'Zakończ',

        # ===== TitanConfigDialog =====
        'config_dialog_title': 'Konfigurator środowiska Titan',
        'config_message': 'Wykryto zainstalowane środowisko Titan.\nCo chcesz zrobić?',
        'btn_launch_titan': 'Uruchom Titana',
        'btn_update_titan': 'Zaktualizuj Titana',
        'btn_manage_tce_integration': 'Zarządzaj integracją pakietów TCE',

        # ===== TCEIntegrationDialog =====
        'tce_integration_dialog_title': 'Zarządzanie integracją pakietów TCE',
        'tce_integration_message': 'Zarządzaj integracją plików .TCEPACKAGE z systemem Windows.\nMożesz zarejestrować lub wyrejestrować rozszerzenie .TCEPACKAGE.',
        'tce_integration_status_registered': 'Status: Integracja jest zarejestrowana ✓',
        'tce_integration_status_not_registered': 'Status: Integracja nie jest zarejestrowana ✗',
        'btn_register_tce_integration': 'Zarejestruj integrację',
        'btn_unregister_tce_integration': 'Wyrejestruj integrację',
        'btn_close': 'Zamknij',
        'tce_error_titan_exe_missing': 'Błąd: Nie znaleziono pliku titan.exe:\n{0}',
        'tce_integration_registered_success': 'Integracja pakietów TCE została pomyślnie zarejestrowana.\n\nTeraz możesz otwierać pliki .TCEPACKAGE bezpośrednio w systemie.',
        'tce_integration_unregistered_success': 'Integracja pakietów TCE została wyrejestrowana.',
        'tce_error_registration': 'Błąd rejestracji integracji:\n{0}',
        'tce_error_unregistration': 'Błąd wyrejestrowania integracji:\n{0}',
        'tce_unregister_confirm': 'Czy na pewno chcesz wyrejestrować integrację pakietów TCE?\n\nPliki .TCEPACKAGE nie będą już automatycznie otwierane w Titanie.',
        'tce_unregister_confirm_title': 'Potwierdzenie',
        'tce_error_windows_only': 'Ta funkcja jest dostępna tylko w systemie Windows.',

        # ===== InstallFrame =====
        'install_frame_title': 'Instalacja Titan',
        'status_starting': 'Rozpoczynanie instalacji...',
        'status_deleting_old': 'Usuwanie starych plików programu...',
        'status_deleting_settings': 'Usuwanie ustawień TCE...',
        'status_no_components': 'Nie wybrano żadnych komponentów.',
        'status_configuring_packages': 'Konfigurowanie obsługi pakietów...',
        'status_post_install': 'Wykonywanie zadań poinstalacyjnych...',
        'status_creating_shortcut': 'Tworzenie skrótu...',
        'status_shortcut_created': 'Skrót utworzony.',
        'status_shortcut_error': 'Błąd tworzenia skrótu.',
        'status_shortcut_timeout': 'Timeout tworzenia skrótu.',
        'status_shortcut_file_missing': 'Plik {0} nie istnieje. Pomijam.',
        'status_shortcut_desktop_not_found': 'Nie znaleziono folderu Desktop.',
        'status_registering_extension': 'Rejestracja .TCEPACKAGE...',
        'status_registering_registry': 'Rejestracja w rejestrze...',
        'status_extension_registered': 'Rozszerzenie zarejestrowane.',
        'status_extension_permission_error': 'Brak uprawnień do rejestracji.',
        'status_extension_error': 'Błąd rejestracji.',
        'status_finalizing': 'Finalizowanie instalacji...',
        'status_downloading': 'Pobieranie',
        'status_extracting': 'Rozpakowywanie',
        'status_download_error': 'Błąd pobierania',
        'status_extract_error': 'Błąd rozpakowywania',

        # Component names
        'component_tce': 'Środowisko TCE',
        'component_interpreter': 'Interpreter (Python)',
        'component_sound_themes': 'Dodatkowe tematy dźwiękowe',

        # Error messages
        'error_create_dir': 'Nie można utworzyć {0}\nBłąd: {1}',
        'error_launch_titan': 'Nie udało się uruchomić Titana.\nBłąd: {0}',
        'error_titan_not_found': 'Nie można znaleźć: {0}',
        'error_audio_init': 'Błąd inicjalizacji audio.',
        'error_launch_titan_short': 'Błąd uruchamiania Titana: {0}',
        'error_file_not_found': 'Nie znaleziono pliku: {0}',
        'error_title': 'Błąd',
        'warning_title': 'Ostrzeżenie',

        # ===== PackageConfirmDialog (TCE_manager) =====
        'package_dialog_title': 'Instalacja pakietu TCE',
        'package_details_header': 'Szczegóły pakietu i akcje:',
        'package_field_name': 'Nazwa',
        'package_field_version': 'Wersja',
        'package_field_destination': 'Przeznaczenie',
        'package_field_description': 'Opis',
        'package_field_author': 'Autor',
        'package_field_install_tasks': 'Zadania instalacyjne',
        'package_field_reqadmin': 'Wymaga admina',
        'package_field_na': 'N/A',
        'package_action_install': 'Instaluj ten pakiet',
        'package_action_cancel': 'Anuluj instalację',

        # ===== TCE Package Handler Messages =====
        'tce_error_paths': 'Błąd ścieżek.',
        'tce_error_7z_missing': 'Błąd: Brak 7z.exe (config).',
        'tce_error_titan_dir_missing': 'Błąd: Brak katalogu Titana (config).',
        'tce_error_audio': 'Błąd audio.',
        'tce_error_file_missing': 'Brak pliku: {0}',
        'tce_error_metadata': 'Błąd metadanych.',
        'tce_progress_installing': 'Instalowanie: {0}...',
        'tce_progress_preparing': 'Przygotowywanie...',
        'tce_progress_extracting': 'Rozpakowywanie plików...',
        'tce_progress_finalizing': 'Finalizowanie...',
        'tce_progress_additional_tasks': 'Dodatkowe zadania...',
        'tce_progress_complete': 'Zakończono.',
        'tce_warning_admin_required': 'Zadania mogą wymagać uprawnień admina.',
        'tce_warning_admin_title': 'Uprawnienia',
        'tce_task_error': 'Błąd zadania \'{0}\' (kod: {1}).\n{2}\n{3}',
        'tce_task_error_title': 'Błąd zadania',
        'tce_task_error_execution': 'Błąd wykonania zadania \'{0}\':\n{1}',
        'tce_success_installed': 'Pakiet \'{0}\' zainstalowany.',
        'tce_success_title': 'Sukces',
        'tce_error_installation': 'Błąd instalacji pakietu: {0}',
        'tce_error_unexpected': 'Nieoczekiwany błąd: {0}',
    },

    'en': {
        # ===== SettingsDialog =====
        'settings_dialog_title': 'Installer Settings',
        'cb_desktop_shortcut': 'Add desktop shortcut',
        'desc_desktop_shortcut': '  Creates a shortcut to the Titan program on the desktop.',
        'section_shortcut': 'Shortcut',
        'cb_register_extension': 'Register .TCEPACKAGE extension',
        'desc_register_extension': '  Registers the .TCEPACKAGE extension to open\n  data packages directly in the Titan environment.\n  (May require administrator privileges).',
        'section_package_handling': '.TCEPACKAGE Package Handling',
        'cb_background_music': 'Enable background music during installation',
        'desc_background_music': '  Plays background music during component installation.',
        'section_background_music': 'Background Music',
        'section_language': 'Język / Language',
        'language_select_label': 'Wybierz język TCE / Select TCE language:',
        'desc_language': '  Ustawia język interfejsu środowiska Titan.\n  Sets the language of the Titan environment interface.',
        'btn_confirm': 'Confirm',
        'btn_cancel': 'Cancel',
        'language_pl': 'Polski',
        'language_en': 'English',

        # ===== StartFrame =====
        'start_frame_title': 'Titan Environment Configurator',
        'start_frame_message': 'Before you start configuring Titan, read this! You are installing a beta version!',
        'btn_next': 'Next >',
        'readme_read_error': 'Error reading file \'{0}\'.',
        'readme_not_found': 'Error: File \'{0}\' not found.',

        # ===== ComponentsFrame =====
        'components_frame_title': 'Select Components and Settings',
        'components_select_message': 'Select the components you want to install:',
        'section_components': 'Components',
        'cb_tce_env': 'TCE Environment (required)',
        'cb_interpreter': 'Interpreter (Python)',
        'cb_sound_themes': 'Additional Sound Themes',
        'section_update': 'Update',
        'cb_delete_before': 'Clear TCE settings',
        'desc_delete_before': '  Removes the TCE settings folder (%APPDATA%\\titosoft).',
        'btn_settings': 'Installer Settings...',
        'btn_install': 'Install',

        # ===== FinishDialog =====
        'finish_dialog_title': 'Installation Complete',
        'finish_message': 'The TCE environment has been successfully installed.',
        'cb_launch_titan': 'Launch Titan Environment',
        'btn_finish': 'Finish',

        # ===== TitanConfigDialog =====
        'config_dialog_title': 'Titan Environment Configurator',
        'config_message': 'Detected installed Titan environment.\nWhat would you like to do?',
        'btn_launch_titan': 'Launch Titan',
        'btn_update_titan': 'Update Titan',
        'btn_manage_tce_integration': 'Manage TCE Package Integration',

        # ===== TCEIntegrationDialog =====
        'tce_integration_dialog_title': 'TCE Package Integration Management',
        'tce_integration_message': 'Manage .TCEPACKAGE file integration with Windows.\nYou can register or unregister the .TCEPACKAGE extension.',
        'tce_integration_status_registered': 'Status: Integration is registered ✓',
        'tce_integration_status_not_registered': 'Status: Integration is not registered ✗',
        'btn_register_tce_integration': 'Register Integration',
        'btn_unregister_tce_integration': 'Unregister Integration',
        'btn_close': 'Close',
        'tce_error_titan_exe_missing': 'Error: titan.exe file not found:\n{0}',
        'tce_integration_registered_success': 'TCE package integration has been successfully registered.\n\nYou can now open .TCEPACKAGE files directly in the system.',
        'tce_integration_unregistered_success': 'TCE package integration has been unregistered.',
        'tce_error_registration': 'Integration registration error:\n{0}',
        'tce_error_unregistration': 'Integration unregistration error:\n{0}',
        'tce_unregister_confirm': 'Are you sure you want to unregister TCE package integration?\n\n.TCEPACKAGE files will no longer open automatically in Titan.',
        'tce_unregister_confirm_title': 'Confirmation',
        'tce_error_windows_only': 'This feature is only available on Windows.',

        # ===== InstallFrame =====
        'install_frame_title': 'Titan Installation',
        'status_starting': 'Starting installation...',
        'status_deleting_old': 'Removing old program files...',
        'status_deleting_settings': 'Removing TCE settings...',
        'status_no_components': 'No components selected.',
        'status_configuring_packages': 'Configuring package handling...',
        'status_post_install': 'Performing post-installation tasks...',
        'status_creating_shortcut': 'Creating shortcut...',
        'status_shortcut_created': 'Shortcut created.',
        'status_shortcut_error': 'Error creating shortcut.',
        'status_shortcut_timeout': 'Shortcut creation timeout.',
        'status_shortcut_file_missing': 'File {0} does not exist. Skipping.',
        'status_shortcut_desktop_not_found': 'Desktop folder not found.',
        'status_registering_extension': 'Registering .TCEPACKAGE...',
        'status_registering_registry': 'Registering in registry...',
        'status_extension_registered': 'Extension registered.',
        'status_extension_permission_error': 'Insufficient permissions for registration.',
        'status_extension_error': 'Registration error.',
        'status_finalizing': 'Finalizing installation...',
        'status_downloading': 'Downloading',
        'status_extracting': 'Extracting',
        'status_download_error': 'Download error',
        'status_extract_error': 'Extraction error',

        # Component names
        'component_tce': 'TCE Environment',
        'component_interpreter': 'Interpreter (Python)',
        'component_sound_themes': 'Additional Sound Themes',

        # Error messages
        'error_create_dir': 'Cannot create {0}\nError: {1}',
        'error_launch_titan': 'Failed to launch Titan.\nError: {0}',
        'error_titan_not_found': 'Cannot find: {0}',
        'error_audio_init': 'Audio initialization error.',
        'error_launch_titan_short': 'Error launching Titan: {0}',
        'error_file_not_found': 'File not found: {0}',
        'error_title': 'Error',
        'warning_title': 'Warning',

        # ===== PackageConfirmDialog (TCE_manager) =====
        'package_dialog_title': 'TCE Package Installation',
        'package_details_header': 'Package details and actions:',
        'package_field_name': 'Name',
        'package_field_version': 'Version',
        'package_field_destination': 'Destination',
        'package_field_description': 'Description',
        'package_field_author': 'Author',
        'package_field_install_tasks': 'Installation Tasks',
        'package_field_reqadmin': 'Requires Admin',
        'package_field_na': 'N/A',
        'package_action_install': 'Install this package',
        'package_action_cancel': 'Cancel installation',

        # ===== TCE Package Handler Messages =====
        'tce_error_paths': 'Path error.',
        'tce_error_7z_missing': 'Error: 7z.exe not found (config).',
        'tce_error_titan_dir_missing': 'Error: Titan directory not found (config).',
        'tce_error_audio': 'Audio error.',
        'tce_error_file_missing': 'File not found: {0}',
        'tce_error_metadata': 'Metadata error.',
        'tce_progress_installing': 'Installing: {0}...',
        'tce_progress_preparing': 'Preparing...',
        'tce_progress_extracting': 'Extracting files...',
        'tce_progress_finalizing': 'Finalizing...',
        'tce_progress_additional_tasks': 'Additional tasks...',
        'tce_progress_complete': 'Complete.',
        'tce_warning_admin_required': 'Tasks may require administrator privileges.',
        'tce_warning_admin_title': 'Permissions',
        'tce_task_error': 'Task \'{0}\' error (code: {1}).\n{2}\n{3}',
        'tce_task_error_title': 'Task Error',
        'tce_task_error_execution': 'Task \'{0}\' execution error:\n{1}',
        'tce_success_installed': 'Package \'{0}\' installed.',
        'tce_success_title': 'Success',
        'tce_error_installation': 'Package installation error: {0}',
        'tce_error_unexpected': 'Unexpected error: {0}',
    }
}


# ============================================================================
# Translation Function
# ============================================================================

# Initialize the current language
_current_language = get_installer_language()
print(f"[I18N] Installer language set to: {_current_language}")


def t(key, **kwargs):
    """
    Translates the given key to the current language.

    Args:
        key: Translation key
        **kwargs: Optional format arguments for string formatting

    Returns:
        Translated string, with formatting applied if kwargs provided.
        Returns the key itself if translation not found (fail-safe).
    """
    global _current_language

    # Get translation dictionary for current language
    lang_dict = TRANSLATIONS.get(_current_language, TRANSLATIONS.get('pl', {}))

    # Get translated string, fallback to key if not found
    translated = lang_dict.get(key, key)

    # Apply formatting if kwargs provided
    if kwargs:
        try:
            translated = translated.format(**kwargs)
        except (KeyError, IndexError) as e:
            print(f"[I18N] Warning: Format error for key '{key}': {e}")
            # Return unformatted string on error
            pass

    return translated


def get_current_language():
    """Returns the current installer language code."""
    return _current_language


def set_current_language(lang_code):
    """
    Sets the current installer language.
    Note: This only affects the current session.
    Use settings.set_setting() to persist the change.
    """
    global _current_language
    if lang_code in TRANSLATIONS:
        _current_language = lang_code
        print(f"[I18N] Current language changed to: {lang_code}")
        return True
    else:
        print(f"[I18N] Warning: Unknown language code: {lang_code}")
        return False


print("[DIAG] Moduł installer_i18n.py został wczytany.")
