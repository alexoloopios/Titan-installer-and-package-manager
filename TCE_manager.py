# TCE_manager.py
print("[DIAG] Moduł TCE_manager.py rozpoczął wczytywanie...")

import wx
import subprocess
import os
import sys
import time
import re
import tempfile
import shutil
import json
import traceback
from installer_i18n import t

try:
    import pygame
except ImportError: pygame = None

# Zmienne globalne dla tego modułu
SFX_PATHS_TCE = {}
BASE_CONFIG_TCE = {} 

# --- Funkcje audio (specyficzne dla TCE Managera) ---
def init_pygame_audio_tce():
    if not pygame: print("[TCE_AUDIO] Pygame niezaładowany."); return False
    try:
        if not pygame.mixer.get_init(): 
            pygame.mixer.init()
            print("[TCE_AUDIO] Pygame mixer zainicjalizowany.")
        else:
            print("[TCE_AUDIO] Pygame mixer był już zainicjalizowany (prawdopodobnie przez inny moduł).")
        return True
    except Exception as e: print(f"[TCE_AUDIO][BŁĄD] Inicjalizacja Pygame mixer: {e}"); return False

def play_sound_tce(sfx_key_or_path): # Odtwarza dźwięk na podstawie klucza
    if not pygame or not pygame.mixer.get_init() or not SFX_PATHS_TCE: return
    sound_path = SFX_PATHS_TCE.get(sfx_key_or_path, sfx_key_or_path)
    if os.path.isfile(sound_path):
        try: pygame.mixer.Sound(sound_path).play()
        except Exception as e: print(f"[TCE_AUDIO][BŁĄD] Odtwarzanie {sound_path}: {e}")
    elif sfx_key_or_path in SFX_PATHS_TCE: print(f"[TCE_AUDIO][UWAGA] Brak pliku dla klucza '{sfx_key_or_path}': {sound_path}")
    else: print(f"[TCE_AUDIO][UWAGA] Nieznany klucz/ścieżka SFX: {sfx_key_or_path}")


def on_control_focus_event_tce(event): play_sound_tce("FOCUS"); event.Skip()


# --- Funkcje logiki pakietów (przeniesione i dostosowane) ---
def parse_script_tce_internal(file_path):
    metadata = {}
    metadata_filename = BASE_CONFIG_TCE.get('METADATA_FILENAME_IN_PACKAGE', '__script.TCE')
    if not os.path.isfile(file_path): print(f"[TCE_LOGIC][BŁĄD] Plik metadanych nie istnieje: {file_path}"); return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                match = re.match(r'^\s*([a-zA-Z0-9_]+)\s*=\s*"(.*?)"\s*$', line)
                if match: metadata[match.group(1).lower()] = match.group(2)
                else: print(f"[TCE_LOGIC][OSTRZEŻENIE] Niepoprawna linia w {metadata_filename}: {line}")
        return metadata
    except Exception as e: print(f"[TCE_LOGIC][BŁĄD] Parsowanie {metadata_filename}: {e}"); return None

def get_package_metadata_internal(tce_package_path, sevenz_exe_to_use):
    # ... (implementacja jak w titan_Launcher.py, używa BASE_CONFIG_TCE dla METADATA_FILENAME_IN_PACKAGE) ...
    print(f"[TCE_LOGIC] Odczyt metadanych z: {tce_package_path}")
    if not os.path.isfile(tce_package_path): print(f"[TCE_LOGIC][BŁĄD] Plik TCE nie istnieje: {tce_package_path}"); return None 
    if not os.path.isfile(sevenz_exe_to_use): print(f"[TCE_LOGIC][BŁĄD] 7z.exe nie znaleziony: {sevenz_exe_to_use}"); return None
    temp_dir = None
    metadata_filename = BASE_CONFIG_TCE.get('METADATA_FILENAME_IN_PACKAGE', '__script.TCE')
    try:
        temp_dir = tempfile.mkdtemp(prefix="tce_meta_")
        cmd_extract_meta = [sevenz_exe_to_use, 'e', tce_package_path, f'-o{temp_dir}', metadata_filename, '-y']
        process = subprocess.Popen(cmd_extract_meta, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            error_output = stderr.decode(errors='replace').strip(); stdout_decoded = stdout.decode(errors='replace')
            print(f"[TCE_LOGIC][BŁĄD] 7z (metadane) kod {process.returncode}: {error_output}")
            if "No files to process" in error_output or metadata_filename not in stdout_decoded : print(f"[TCE_LOGIC][BŁĄD] Nie znaleziono '{metadata_filename}' w archiwum.")
            return None
        metadata_file_path = os.path.join(temp_dir, metadata_filename)
        if not os.path.isfile(metadata_file_path): print(f"[TCE_LOGIC][BŁĄD] '{metadata_filename}' nie wypakowany."); return None
        metadata = parse_script_tce_internal(metadata_file_path)
        if not metadata or not metadata.get("name") or not metadata.get("version"): print(f"[TCE_LOGIC][BŁĄD] Metadane niekompletne."); return None 
        print(f"[TCE_LOGIC] Metadane odczytane: {metadata}"); return metadata
    except Exception as e: print(f"[TCE_LOGIC][BŁĄD KRYTYCZNY] get_package_metadata: {e}"); traceback.print_exc(); return None
    finally:
        if temp_dir and os.path.isdir(temp_dir):
            try: shutil.rmtree(temp_dir)
            except Exception: pass


def install_full_package_internal(tce_package_path, target_install_dir, sevenz_exe_to_use):
    # ... (implementacja jak w titan_Launcher.py) ...
    print(f"[TCE_LOGIC] Pełna instalacja: {tce_package_path} do {target_install_dir}")
    if not os.path.isfile(sevenz_exe_to_use): raise FileNotFoundError(f"Nie znaleziono 7z.exe: {sevenz_exe_to_use}")
    os.makedirs(target_install_dir, exist_ok=True)
    cmd = [sevenz_exe_to_use, "x", tce_package_path, f"-o{target_install_dir}", "-y"]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        stdout, stderr = process.communicate()
        if process.returncode != 0: raise Exception(f"7-Zip error: {stderr.decode(errors='replace')}")
    except Exception as e: print(f"[TCE_LOGIC][BŁĄD] Rozpakowywanie: {e}"); raise

# --- Klasa PackageConfirmDialog ---
class PackageConfirmDialog(wx.Dialog): # ... (implementacja jak w ostatniej wersji titan_Launcher.py, używa play_sound_tce i on_control_focus_event_tce) ...
    def __init__(self, parent, package_path, metadata):
        super().__init__(parent, title=t('package_dialog_title'), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)
        self.package_path = package_path; self.metadata = metadata if metadata else {}; self.result_action = wx.ID_CANCEL
        dialog_main_sizer = wx.BoxSizer(wx.VERTICAL); content_panel = wx.Panel(self); panel_vbox = wx.BoxSizer(wx.VERTICAL)
        self.list_box_display = wx.ListBox(content_panel, style=wx.LB_SINGLE, size=(-1, 300))
        self.list_box_display.Bind(wx.EVT_LISTBOX_DCLICK, self.on_listbox_action_activated)
        self.list_box_display.Bind(wx.EVT_LISTBOX, self.on_listbox_select_for_focus_sound_tce)
        self.list_box_display.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_tce)
        self.list_items_data = []
        known_keys_display = {
            "name": t('package_field_name'),
            "version": t('package_field_version'),
            "destination": t('package_field_destination'),
            "description": t('package_field_description'),
            "author": t('package_field_author'),
            "install_tasks": t('package_field_install_tasks'),
            "reqadmin": t('package_field_reqadmin')
        }
        display_order = ["name", "version", "destination", "description", "author", "install_tasks", "reqadmin"]; displayed_keys = set()
        for key in display_order:
            if key in self.metadata:
                label_text = known_keys_display.get(key, key.capitalize()); value_text = str(self.metadata.get(key, t('package_field_na')))
                self.list_items_data.append((f"{label_text}: {value_text}", None)); displayed_keys.add(key)
        for key, value in self.metadata.items():
            if key not in displayed_keys:
                label_text = key.capitalize(); value_text = str(value)
                self.list_items_data.append((f"{label_text}: {value_text}", None))
        self.install_action_string = t('package_action_install'); self.cancel_action_string = t('package_action_cancel')
        self.list_items_data.append((f"-> {self.install_action_string}", wx.ID_OK))
        self.list_items_data.append((f"-> {self.cancel_action_string}", wx.ID_CANCEL))
        for item_text, _action_data in self.list_items_data: self.list_box_display.Append(item_text)
        default_selection_idx = 0
        if self.list_box_display.GetCount() > 0:
            if default_selection_idx < self.list_box_display.GetCount(): self.list_box_display.SetSelection(default_selection_idx)
        panel_vbox.Add(wx.StaticText(content_panel, label=t('package_details_header')), 0, wx.ALL & ~wx.BOTTOM, 5)
        panel_vbox.Add(self.list_box_display, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        content_panel.SetSizer(panel_vbox); dialog_main_sizer.Add(content_panel, 1, wx.EXPAND)
        self.SetSizerAndFit(dialog_main_sizer); self.SetMinSize(wx.Size(500, 400)); self.CenterOnParent()
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down_dialog); self.Bind(wx.EVT_CLOSE, self.on_close_event_dialog); self.Bind(wx.EVT_SHOW, self.on_show_event)
    def on_listbox_select_for_focus_sound_tce(self, event): play_sound_tce("FOCUS"); event.Skip()
    def on_listbox_action_activated(self, event_or_index):
        selection_index = event_or_index if isinstance(event_or_index, int) else getattr(event_or_index, 'GetSelection', lambda: -1)()
        if selection_index != wx.NOT_FOUND:
            selected_listbox_string = self.list_box_display.GetString(selection_index); action_id_to_trigger = None
            for item_text, action_data in self.list_items_data:
                if item_text == selected_listbox_string: action_id_to_trigger = action_data; break
            if action_id_to_trigger is not None: self.result_action = action_id_to_trigger; play_sound_tce("CONTEXTMENUCLOSE"); self.EndModal(self.result_action)
        if hasattr(event_or_index, 'Skip'): event_or_index.Skip()
    def on_key_down_dialog(self, event):
        keycode = event.GetKeyCode(); focused_widget = wx.Window.FindFocus()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            if focused_widget == self.list_box_display or self.list_box_display.HasFocus():
                idx = self.list_box_display.GetSelection();
                if idx != wx.NOT_FOUND: self.on_listbox_action_activated(idx); return 
        elif keycode == wx.WXK_ESCAPE: self.result_action = wx.ID_CANCEL; play_sound_tce("CONTEXTMENUCLOSE"); self.EndModal(self.result_action); return
        event.Skip()
    def on_show_event(self, event):
        if event.IsShown(): 
            play_sound_tce("CONTEXTMENUOPEN")
            if self.list_box_display.GetCount() > 0: self.list_box_display.SetSelection(0) 
            self.list_box_display.SetFocus() 
        event.Skip()
    def on_close_event_dialog(self, event): play_sound_tce("CONTEXTMENUCLOSE"); self.EndModal(wx.ID_CANCEL)


# --- Główna funkcja obsługi pakietu z CLI ---
def handle_tce_package_cli(package_file_path, base_config_from_launcher):
    global BASE_CONFIG_TCE, SFX_PATHS_TCE
    BASE_CONFIG_TCE = base_config_from_launcher # Zapisz konfigurację dla tego modułu
    SFX_PATHS_TCE = { # Zbuduj ścieżki SFX dla tego modułu
        "CONTEXTMENUOPEN": os.path.join(BASE_CONFIG_TCE["SFX_DIR"], "contextmenu.ogg"),
        "CONTEXTMENUCLOSE": os.path.join(BASE_CONFIG_TCE["SFX_DIR"], "contextmenuclose.ogg"),
        "FOCUS": os.path.join(BASE_CONFIG_TCE["SFX_DIR"], "focus.ogg"),
    }

    print(f"[TCE_MANAGER] Rozpoczynam obsługę pakietu: {package_file_path}")
    app_pkg = wx.App(False) 
    
    handler_exe_abs_path = ""; base_install_dir_for_handler = ""; config_file_to_read = ""
    actual_sevenz_path = ""; actual_titan_data_path = ""
    try:
        # Użyj sys.argv[0] zamiast sys.executable (Nuitka onefile!)
        handler_exe_abs_path = os.path.abspath(sys.argv[0])
        # Katalog instalatora to katalog, gdzie jest titan.exe (nie dirname(dirname)!)
        base_install_dir_for_handler = os.path.dirname(handler_exe_abs_path)
        config_file_to_read = os.path.join(base_install_dir_for_handler, BASE_CONFIG_TCE["HANDLER_CONFIG_FILENAME"])
        print(f"[TCE_MANAGER] Szukam pliku konfiguracyjnego: {config_file_to_read}")
    except Exception as e_path: print(f"[TCE_MANAGER][BŁĄD] Ścieżki bazowe: {e_path}"); wx.MessageBox(t('tce_error_paths'), t('error_title'), wx.OK | wx.ICON_ERROR); return

    if os.path.isfile(config_file_to_read):
        try:
            with open(config_file_to_read, 'r') as f_cfg: config_data = json.load(f_cfg)
            actual_sevenz_path = config_data.get("sevenz_path_abs")
            actual_titan_data_path = config_data.get("titan_install_dir_abs")
        except Exception as e_read_cfg: print(f"[TCE_MANAGER][BŁĄD] Odczyt config: {e_read_cfg}"); traceback.print_exc()

    # Jeśli 7z.exe nie jest w konfiguracji lub nie istnieje, użyj bin\7z.exe jako fallback
    if not (actual_sevenz_path and os.path.isfile(actual_sevenz_path)):
        print("[TCE_MANAGER] 7z.exe nie znaleziony w konfiguracji, szukam w bin\\")
        try:
            # Ścieżka do bin\7z.exe względem lokalizacji titan.exe
            titan_exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            fallback_7z = os.path.join(titan_exe_dir, "bin", "7z.exe")
            if os.path.isfile(fallback_7z):
                actual_sevenz_path = fallback_7z
                print(f"[TCE_MANAGER] Używam 7z.exe z bin\\: {actual_sevenz_path}")
            else:
                print(f"[TCE_MANAGER][BŁĄD] 7z.exe nie znaleziony w bin\\: {fallback_7z}")
                wx.MessageBox(t('tce_error_7z_missing'), t('error_title'), wx.OK | wx.ICON_ERROR)
                return
        except Exception as e_fallback:
            print(f"[TCE_MANAGER][BŁĄD] Fallback 7z.exe: {e_fallback}")
            wx.MessageBox(t('tce_error_7z_missing'), t('error_title'), wx.OK | wx.ICON_ERROR)
            return

    if not (actual_titan_data_path and os.path.isdir(actual_titan_data_path)):
        # Podobny fallback dla titan_data
        print("[TCE_MANAGER] titan_data nie znaleziony w konfiguracji, szukam domyślnej lokalizacji")
        try:
            titan_exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            fallback_titan_data = os.path.join(titan_exe_dir, "titan_data")
            if os.path.isdir(fallback_titan_data):
                actual_titan_data_path = fallback_titan_data
                print(f"[TCE_MANAGER] Używam titan_data: {actual_titan_data_path}")
            else:
                print(f"[TCE_MANAGER][BŁĄD] titan_data nie znaleziony: {fallback_titan_data}")
                wx.MessageBox(t('tce_error_titan_dir_missing'), t('error_title'), wx.OK | wx.ICON_ERROR)
                return
        except Exception as e_fallback_titan:
            print(f"[TCE_MANAGER][BŁĄD] Fallback titan_data: {e_fallback_titan}")
            wx.MessageBox(t('tce_error_titan_dir_missing'), t('error_title'), wx.OK | wx.ICON_ERROR)
            return

    if not init_pygame_audio_tce(): wx.MessageBox(t('tce_error_audio'), t('error_title'), wx.OK | wx.ICON_WARNING)
    if not os.path.isfile(package_file_path): play_sound_tce("CONTEXTMENUCLOSE"); wx.MessageBox(t('tce_error_file_missing').format(package_file_path), t('error_title'), wx.OK | wx.ICON_ERROR); return
    
    try:
        metadata = get_package_metadata_internal(package_file_path, actual_sevenz_path)
        if metadata is None: play_sound_tce("CONTEXTMENUCLOSE"); wx.MessageBox(t('tce_error_metadata'), t('error_title'), wx.OK | wx.ICON_ERROR); return 
            
        confirm_dialog = PackageConfirmDialog(None, package_file_path, metadata)
        result = confirm_dialog.ShowModal(); confirm_dialog.Destroy()

        if result == wx.ID_OK:
            progress_dlg = None
            try:
                progress_dlg = wx.ProgressDialog(t('package_dialog_title'), t('tce_progress_installing').format(metadata.get('name', t('package_field_na'))), 100, None, wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT)
                progress_dlg.Update(0, t('tce_progress_preparing')); wx.YieldIfNeeded(); cancelled_by_user = False
                progress_dlg.Update(10, t('tce_progress_extracting')); wx.YieldIfNeeded()
                if hasattr(progress_dlg, 'WasCancelled') and progress_dlg.WasCancelled(): cancelled_by_user = True
                if not cancelled_by_user:
                    install_full_package_internal(package_file_path, actual_titan_data_path, actual_sevenz_path)
                    if hasattr(progress_dlg, 'WasCancelled') and progress_dlg.WasCancelled(): cancelled_by_user = True
                    elif progress_dlg: progress_dlg.Update(70, t('tce_progress_finalizing')); wx.YieldIfNeeded()

                if not cancelled_by_user and "install_tasks" in metadata:
                    tasks_str = metadata.get("install_tasks", "")
                    if tasks_str:
                        if progress_dlg: progress_dlg.Update(80, t('tce_progress_additional_tasks')); wx.YieldIfNeeded()
                        if metadata.get("reqadmin") == "1":
                            is_admin = False # Domyślnie nie jest adminem
                            if os.name == 'nt':
                                try: import ctypes; is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                                except Exception: print("[TCE_MANAGER][OSTRZEŻENIE] Nie można sprawdzić uprawnień admina.")
                            if not is_admin: wx.MessageBox(t('tce_warning_admin_required'), t('tce_warning_admin_title'), wx.OK | wx.ICON_WARNING)
                        for i, task_line in enumerate(tasks_str.splitlines()):
                            task_line = task_line.strip()
                            if not task_line: continue

                            cmd_match = re.match(r'^cmd\("(.+?)"\)$', task_line)
                            winget_match = re.match(r'^winget\("(.+?)"\)$', task_line)
                            dlg_match = re.match(r'^dlg\("(.+?)",\s*"(.+?)"\)$', task_line)

                            if hasattr(progress_dlg, 'WasCancelled') and progress_dlg.WasCancelled():
                                cancelled_by_user = True
                                break
                            
                            current_task_progress = 80 + int((i / len(tasks_str.splitlines())) * 15)

                            if cmd_match or winget_match:
                                if winget_match:
                                    package_name = winget_match.group(1)
                                    actual_command = f'winget install -e --id "{package_name}" --accept-package-agreements --accept-source-agreements'
                                    task_description = f"Winget: {package_name}"
                                else: # cmd_match
                                    actual_command = cmd_match.group(1)
                                    task_description = f"Cmd: {actual_command[:30]}..."
                                
                                print(f"[TCE_MANAGER] Wykonuję: {actual_command}")
                                if progress_dlg: 
                                    progress_dlg.Pulse(f"Zadanie: {task_description}")
                                    wx.YieldIfNeeded()

                                try:
                                    p_task = subprocess.Popen(actual_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', bufsize=1)
                                    
                                    while p_task.poll() is None:
                                        line = p_task.stdout.readline().strip()
                                        if line and progress_dlg:
                                            progress_dlg.Pulse(f"{task_description}\n{line[:100]}")
                                        
                                        wx.YieldIfNeeded() # Zapobiega zamarzaniu GUI
                                        if progress_dlg and progress_dlg.WasCancelled():
                                            p_task.terminate()
                                            cancelled_by_user = True
                                            print("[TCE_MANAGER] Zadanie anulowane przez użytkownika.")
                                            break
                                    
                                    if not cancelled_by_user:
                                        stdout, stderr = p_task.communicate()
                                        if p_task.returncode != 0:
                                            wx.MessageBox(t('tce_task_error').format(actual_command, p_task.returncode, stdout, stderr), t('tce_task_error_title'), wx.OK | wx.ICON_WARNING)

                                except Exception as e_cmd:
                                    if not cancelled_by_user:
                                        wx.MessageBox(t('tce_task_error_execution').format(actual_command, e_cmd), t('tce_task_error_title'), wx.OK | wx.ICON_ERROR)

                            elif dlg_match:
                                title, message = dlg_match.group(1), dlg_match.group(2)
                                print(f"[TCE_MANAGER] Wyświetlam dialog: Tytuł='{title}'")
                                if progress_dlg: progress_dlg.Update(current_task_progress, f"Dialog: {title}"); wx.YieldIfNeeded()
                                wx.MessageBox(message, title, wx.OK | wx.ICON_INFORMATION)

                            else:
                                print(f"[TCE_MANAGER][OSTRZEŻENIE] Nieznane zadanie w install_tasks: {task_line}")
                
                if not cancelled_by_user:
                    if progress_dlg: progress_dlg.Update(100, t('tce_progress_complete'))
                    wx.MessageBox(t('tce_success_installed').format(metadata.get('name', t('package_field_na'))), t('tce_success_title'), wx.OK | wx.ICON_INFORMATION)
                else: print("[TCE_MANAGER] Anulowano przez użytkownika.")
            except Exception as e_inst_pkg: print(f"[TCE_MANAGER][BŁĄD] {e_inst_pkg}"); traceback.print_exc(); wx.MessageBox(t('tce_error_installation').format(e_inst_pkg), t('error_title'), wx.OK | wx.ICON_ERROR)
            finally:
                if progress_dlg: progress_dlg.Destroy()
    except Exception as e_outer_pkg: print(f"[TCE_MANAGER][BŁĄD KRYTYCZNY] {e_outer_pkg}"); traceback.print_exc(); play_sound_tce("CONTEXTMENUCLOSE"); wx.MessageBox(t('tce_error_unexpected').format(e_outer_pkg), t('error_title'), wx.OK | wx.ICON_ERROR)
    finally:
        if pygame and pygame.mixer.get_init(): pygame.mixer.quit()
    print("[TCE_MANAGER] Zakończono.")

print("[DIAG] Moduł TCE_manager.py został wczytany.")