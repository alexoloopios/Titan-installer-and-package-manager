# installer.py
print("[DIAG] Moduł installer.py rozpoczął wczytywanie...")

import wx
import subprocess
import threading
import re
import os
import sys
import time
import shutil
import traceback
import json
import settings
from installer_i18n import t, get_current_language

try:
    import winshell
except ImportError: winshell = None
try:
    import winreg
except ImportError: winreg = None
try:
    import pygame
except ImportError: pygame = None

# Zmienne globalne dla tego modułu (dostępne dla wszystkich klas i funkcji w tym pliku)
installing_sound_channel = None
SFX_PATHS = {} 
BASE_CONFIG = {} # Będzie wypełnione w run_main_installer

# =============== FUNKCJE AUDIO (dla instalatora) ===============
def init_pygame_audio_installer():
    if not pygame: print("[INSTALLER_AUDIO] Pygame niezaładowany."); return False
    try:
        if not pygame.mixer.get_init(): 
            pygame.mixer.init()
            print("[INSTALLER_AUDIO] Pygame mixer zainicjalizowany.")
        else:
            print("[INSTALLER_AUDIO] Pygame mixer był już zainicjalizowany.")
        return True
    except Exception as e: print(f"[INSTALLER_AUDIO][BŁĄD] Inicjalizacja Pygame mixer: {e}"); return False

def play_sound_installer(sfx_key_or_path):
    if not pygame or not pygame.mixer.get_init() or not SFX_PATHS: return
    sound_path = SFX_PATHS.get(sfx_key_or_path, sfx_key_or_path) 
    if os.path.isfile(sound_path):
        try: pygame.mixer.Sound(sound_path).play()
        except Exception as e: print(f"[INSTALLER_AUDIO][BŁĄD] Odtwarzanie {sound_path}: {e}")
    elif sfx_key_or_path in SFX_PATHS: print(f"[INSTALLER_AUDIO][UWAGA] Brak pliku dla klucza '{sfx_key_or_path}': {sound_path}")
    else: print(f"[INSTALLER_AUDIO][UWAGA] Nieznany klucz/ścieżka SFX: {sfx_key_or_path}")


def play_looping_sound_installer(sfx_key):
    global installing_sound_channel
    if not pygame or not pygame.mixer.get_init() or not SFX_PATHS: return
    sound_path = SFX_PATHS.get(sfx_key)
    if installing_sound_channel and installing_sound_channel.get_busy(): installing_sound_channel.stop()
    if sound_path and os.path.isfile(sound_path):
        try: installing_sound_channel = pygame.mixer.Sound(sound_path).play(loops=-1)
        except Exception as e: print(f"[INSTALLER_AUDIO][BŁĄD] Pętla {sound_path}: {e}")
    elif sound_path: print(f"[INSTALLER_AUDIO][UWAGA] Brak pliku dla pętli: {sound_path}")

def stop_looping_sound_installer():
    global installing_sound_channel
    if not pygame or not pygame.mixer.get_init() or not installing_sound_channel: return
    installing_sound_channel.stop(); installing_sound_channel = None

def on_control_focus_event_installer(event): play_sound_installer("FOCUS"); event.Skip()

# =============== OKNO 0.5 (SettingsDialog) ===============
class SettingsDialog(wx.Dialog):
    def __init__(self, parent, current_create_shortcut, current_register_extension):
        super().__init__(parent, title=t('settings_dialog_title'), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.create_shortcut_val = current_create_shortcut
        self.register_extension_val = current_register_extension
        self.language_val = get_current_language()
        self.background_music_val = True
        dialog_main_sizer = wx.BoxSizer(wx.VERTICAL)
        content_panel = wx.Panel(self); panel_content_sizer = wx.BoxSizer(wx.VERTICAL)
        self.cb_shortcut = wx.CheckBox(content_panel, label=t('cb_desktop_shortcut'))
        self.cb_shortcut.SetValue(self.create_shortcut_val); self.cb_shortcut.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        st_shortcut_desc = wx.StaticText(content_panel, label=t('desc_desktop_shortcut'))
        shortcut_box = wx.StaticBox(content_panel, label=t('section_shortcut')); shortcut_sizer = wx.StaticBoxSizer(shortcut_box, wx.VERTICAL)
        shortcut_sizer.Add(self.cb_shortcut, 0, wx.EXPAND | wx.ALL, 5)
        shortcut_sizer.Add(st_shortcut_desc, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        panel_content_sizer.Add(shortcut_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.cb_register = wx.CheckBox(content_panel, label=t('cb_register_extension'))
        self.cb_register.SetValue(self.register_extension_val); self.cb_register.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        st_register_desc1 = wx.StaticText(content_panel, label=t('desc_register_extension'))
        register_box = wx.StaticBox(content_panel, label=t('section_package_handling')); register_sizer = wx.StaticBoxSizer(register_box, wx.VERTICAL)
        register_sizer.Add(self.cb_register, 0, wx.EXPAND | wx.ALL, 5)
        register_sizer.Add(st_register_desc1, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        panel_content_sizer.Add(register_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Background music option
        self.cb_background_music = wx.CheckBox(content_panel, label=t('cb_background_music'))
        self.cb_background_music.SetValue(self.background_music_val)
        self.cb_background_music.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        self.cb_background_music.Bind(wx.EVT_CHECKBOX, self.on_background_music_changed)
        st_background_music_desc = wx.StaticText(content_panel, label=t('desc_background_music'))
        background_music_box = wx.StaticBox(content_panel, label=t('section_background_music'))
        background_music_sizer = wx.StaticBoxSizer(background_music_box, wx.VERTICAL)
        background_music_sizer.Add(self.cb_background_music, 0, wx.EXPAND | wx.ALL, 5)
        background_music_sizer.Add(st_background_music_desc, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        panel_content_sizer.Add(background_music_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Language selection
        lang_box = wx.StaticBox(content_panel, label=t('section_language')); lang_sizer = wx.StaticBoxSizer(lang_box, wx.VERTICAL)
        lang_choice_sizer = wx.BoxSizer(wx.HORIZONTAL)
        st_lang = wx.StaticText(content_panel, label=t('language_select_label'))
        lang_choice_sizer.Add(st_lang, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        # Language choices with display names
        self.lang_codes = ['pl', 'en']
        self.lang_names = [t('language_pl'), t('language_en')]
        self.lang_choice = wx.Choice(content_panel, choices=self.lang_names)
        # Set current language
        current_lang = get_current_language()
        if current_lang in self.lang_codes:
            self.lang_choice.SetSelection(self.lang_codes.index(current_lang))
        else:
            self.lang_choice.SetSelection(0)
        self.lang_choice.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        lang_choice_sizer.Add(self.lang_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        lang_sizer.Add(lang_choice_sizer, 0, wx.EXPAND | wx.ALL, 5)
        st_lang_desc = wx.StaticText(content_panel, label=t('desc_language'))
        lang_sizer.Add(st_lang_desc, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        panel_content_sizer.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        content_panel.SetSizer(panel_content_sizer)
        dialog_main_sizer.Add(content_panel, 1, wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, 5)
        btn_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        ok_button_sd = self.FindWindowById(wx.ID_OK)
        if ok_button_sd: ok_button_sd.SetLabel(t('btn_confirm')); ok_button_sd.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        cancel_button_sd = self.FindWindowById(wx.ID_CANCEL)
        if cancel_button_sd: cancel_button_sd.SetLabel(t('btn_cancel')); cancel_button_sd.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        dialog_main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        self.SetSizerAndFit(dialog_main_sizer); self.SetMinSize(self.GetSize()); self.CenterOnParent()
        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK); self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CLOSE, self.on_close_event); self.Bind(wx.EVT_SHOW, self.on_show_event)
    def on_show_event(self, event):
        if event.IsShown(): play_sound_installer("DLGOPEN")
        event.Skip()
    
    def on_background_music_changed(self, event):
        """Handle background music checkbox change - immediately stop music if disabled"""
        if not self.cb_background_music.GetValue():
            # If music is being disabled, stop any currently playing background music
            stop_looping_sound_installer()
        event.Skip()
    def on_ok(self, event):
        self.create_shortcut_val = self.cb_shortcut.GetValue()
        self.register_extension_val = self.cb_register.GetValue()
        # Get language code from selection
        lang_index = self.lang_choice.GetSelection()
        if lang_index >= 0 and lang_index < len(self.lang_codes):
            self.language_val = self.lang_codes[lang_index]
        else:
            self.language_val = 'pl'
        self.background_music_val = self.cb_background_music.GetValue()
        play_sound_installer("DLGCLOSE")
        self.EndModal(wx.ID_OK)
    def on_cancel(self, event): play_sound_installer("DLGCLOSE"); self.EndModal(wx.ID_CANCEL)
    def on_close_event(self, event): play_sound_installer("DLGCLOSE"); self.EndModal(wx.ID_CANCEL)
    def should_create_shortcut(self): return self.create_shortcut_val
    def should_register_extension(self): return self.register_extension_val
    def get_selected_language(self): return self.language_val
    def get_background_music_enabled(self): return self.background_music_val

# =============== OKNO 1 (StartFrame) ===============
class StartFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(500, 400))
        panel = wx.Panel(self)
        wx.StaticText(panel, label=t('start_frame_message'), pos=(10,10))
        content = self.read_czytajto()
        self.tc_readme = wx.TextCtrl(panel, value=content, pos=(10,40), size=(460,250), style=wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_SUNKEN)
        self.tc_readme.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        btn_next = wx.Button(panel, label=t('btn_next'), pos=(390,310)); btn_next.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        btn_cancel = wx.Button(panel, label=t('btn_cancel'), pos=(300,310)); btn_cancel.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        btn_next.Bind(wx.EVT_BUTTON, self.on_next); btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.Bind(wx.EVT_SHOW, self.on_show); self.Bind(wx.EVT_CLOSE, self.on_close_frame_event); self.CenterOnScreen()
    def on_show(self, event):
        if event.IsShown(): play_sound_installer("DLGOPEN")
        event.Skip()
    def read_czytajto(self):
        readme_file_path = BASE_CONFIG.get("README_FILE", "czytajto.txt")
        if os.path.isfile(readme_file_path):
            try:
                with open(readme_file_path, "r", encoding="utf-8", errors="replace") as f: return f.read()
            except Exception as e: return t('readme_read_error').format(readme_file_path)
        return t('readme_not_found').format(readme_file_path)
    def on_next(self, event):
        play_sound_installer("DLGOPEN"); self.Hide(); app = wx.GetApp()
        frame = ComponentsFrame(None, t('components_frame_title'), app_settings=app); frame.Show()
    def on_cancel(self, event): play_sound_installer("DLGCLOSE"); self.Close()
    def on_close_frame_event(self, event): play_sound_installer("DLGCLOSE"); self.Destroy()

# =============== OKNO 2 (ComponentsFrame) ===============
class ComponentsFrame(wx.Frame):
    def __init__(self, parent, title, app_settings):
        super().__init__(parent, title=title)
        self.app_settings = app_settings; panel = wx.Panel(self); v_sizer = wx.BoxSizer(wx.VERTICAL)
        st_info = wx.StaticText(panel, label=t('components_select_message')); v_sizer.Add(st_info, 0, wx.ALL, 10)
        cb_box = wx.StaticBox(panel, label=t('section_components')); cb_box_sizer = wx.StaticBoxSizer(cb_box, wx.VERTICAL)
        self.cb_tce = wx.CheckBox(panel, label=t('cb_tce_env')); self.cb_tce.SetValue(True)
        self.cb_tce.Bind(wx.EVT_CHECKBOX, self.on_tce_clicked); self.cb_tce.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        cb_box_sizer.Add(self.cb_tce, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self.cb_interp = wx.CheckBox(panel, label=t('cb_interpreter')); self.cb_interp.SetValue(True)
        self.cb_interp.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer); cb_box_sizer.Add(self.cb_interp, 0, wx.EXPAND | wx.ALL, 5)

        # ZMIANA: Dodatkowe tematy dźwiękowe są teraz odznaczalne
        self.cb_sound = wx.CheckBox(panel, label=t('cb_sound_themes'))
        self.cb_sound.SetValue(True) # Nadal domyślnie zaznaczone
        self.cb_sound.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        # Usunięto: self.cb_sound.Bind(wx.EVT_CHECKBOX, self.on_sound_clicked)
        cb_box_sizer.Add(self.cb_sound, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        v_sizer.Add(cb_box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10); v_sizer.AddSpacer(10)

        # Opcja usunięcia plików przed instalacją
        cleanup_box = wx.StaticBox(panel, label=t('section_update')); cleanup_sizer = wx.StaticBoxSizer(cleanup_box, wx.VERTICAL)
        self.cb_delete_before = wx.CheckBox(panel, label=t('cb_delete_before'))
        self.cb_delete_before.SetValue(False)
        self.cb_delete_before.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        cleanup_sizer.Add(self.cb_delete_before, 0, wx.EXPAND | wx.ALL, 5)
        st_cleanup_desc = wx.StaticText(panel, label=t('desc_delete_before'))
        cleanup_sizer.Add(st_cleanup_desc, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        v_sizer.Add(cleanup_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10); v_sizer.AddSpacer(10)
        btn_settings = wx.Button(panel, label=t('btn_settings'))
        btn_settings.Bind(wx.EVT_BUTTON, self.on_settings); btn_settings.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        v_sizer.Add(btn_settings, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10); v_sizer.AddSpacer(10)
        btn_install = wx.Button(panel, label=t('btn_install'))
        btn_install.Bind(wx.EVT_BUTTON, self.on_install); btn_install.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        v_sizer.Add(btn_install, 0, wx.EXPAND | wx.ALL, 10) 
        panel.SetSizer(v_sizer); self.Layout(); v_sizer.Fit(self); self.SetMinSize(self.GetSize());
        self.Bind(wx.EVT_SHOW, self.on_show); self.Bind(wx.EVT_CLOSE, self.on_close_frame_event); self.CenterOnScreen()

    def on_show(self, event):
        if event.IsShown(): play_sound_installer("DLGOPEN")
        event.Skip()
    def on_close_frame_event(self, event): play_sound_installer("DLGCLOSE"); stop_looping_sound_installer(); self.Destroy()
    def on_tce_clicked(self, event): # Ta metoda pozostaje, TCE jest nieodznaczalne
        if not self.cb_tce.GetValue(): self.cb_tce.SetValue(True)
    # Usunięto metodę on_sound_clicked(self, event)

    def on_settings(self, event):
        dlg = SettingsDialog(self, self.app_settings.create_desktop_shortcut, self.app_settings.register_tcepackage_extension)
        if dlg.ShowModal() == wx.ID_OK:
            self.app_settings.create_desktop_shortcut = dlg.should_create_shortcut()
            self.app_settings.register_tcepackage_extension = dlg.should_register_extension()
            # Save language setting
            selected_language = dlg.get_selected_language()
            settings.set_setting('language', selected_language, 'general')
            print(f"[INSTALLER] Język ustawiony na: {selected_language}")
            # Save background music setting
            self.app_settings.background_music_enabled = dlg.get_background_music_enabled()
            print(f"[INSTALLER] Muzyka w tle ustawiona na: {self.app_settings.background_music_enabled}")
        dlg.Destroy() 
    def on_install(self, event):
        # Check if background music is enabled from app settings
        background_music_enabled = getattr(self.app_settings, 'background_music_enabled', True)
        if background_music_enabled:
            play_looping_sound_installer("INSTALLING")
        else:
            # Stop any currently playing background music if disabled
            stop_looping_sound_installer()

        self.Hide()
        install_frame = InstallFrame(None, t('install_frame_title')); install_frame.selected_components = {
            'TCE': self.cb_tce.GetValue(), 'Interpreter': self.cb_interp.GetValue(),
            'SoundThemes': self.cb_sound.GetValue() # Wartość będzie teraz brana z checkboxa
            }
        install_frame.app_settings = self.app_settings
        install_frame.delete_before_install = self.cb_delete_before.GetValue()
        install_frame.Show()

# =============== NOWE OKNO FinishDialog ===============
class FinishDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=t('finish_dialog_title'), style=wx.DEFAULT_DIALOG_STYLE | wx.CAPTION)
        print("[GUI DEBUG] Tworzenie FinishDialog...")
        self._should_launch_titan = True

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        st_message = wx.StaticText(panel, label=t('finish_message'))
        st_message.Wrap(300)
        vbox.Add(st_message, 0, wx.ALL | wx.ALIGN_CENTER, border=20) # flag=0 dla StaticText

        self.cb_launch_titan = wx.CheckBox(panel, label=t('cb_launch_titan'))
        self.cb_launch_titan.SetValue(self._should_launch_titan)
        self.cb_launch_titan.Bind(wx.EVT_CHECKBOX, self.on_checkbox_change)
        self.cb_launch_titan.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        vbox.Add(self.cb_launch_titan, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_LEFT, border=15) # flag=0

        btn_finish = wx.Button(panel, label=t('btn_finish'))
        btn_finish.SetDefault() 
        btn_finish.Bind(wx.EVT_BUTTON, self.on_finish)
        btn_finish.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)
        hbox_buttons.AddStretchSpacer(prop=1)
        hbox_buttons.Add(btn_finish, 0, wx.ALIGN_CENTER) 
        hbox_buttons.AddStretchSpacer(prop=1)
        vbox.Add(hbox_buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10) # flag=0

        panel.SetSizer(vbox)
        vbox.Fit(self)
        self.SetMinSize(self.GetSize())
        self.CenterOnParent()

        self.Bind(wx.EVT_SHOW, self.on_show_event)
        self.Bind(wx.EVT_CLOSE, self.on_close_dialog_event)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        print("[GUI DEBUG] FinishDialog utworzone.")
        
    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN or event.GetKeyCode() == wx.WXK_NUMPAD_ENTER:
            self.on_finish(None) 
        elif event.GetKeyCode() == wx.WXK_ESCAPE:
            self._should_launch_titan = False # Anulowanie przez Esc nie uruchamia
            play_sound_installer("DLGCLOSE")
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def on_show_event(self, event):
        if event.IsShown():
            play_sound_installer("DLGOPEN") 
            self.cb_launch_titan.SetFocus() 
        event.Skip()

    def on_checkbox_change(self, event):
        self._should_launch_titan = self.cb_launch_titan.GetValue()
        # Nie ma potrzeby Skip() dla EVT_CHECKBOX, jeśli nie ma innych handlerów
        # event.Skip() 

    def on_finish(self, event):
        self._should_launch_titan = self.cb_launch_titan.GetValue()
        play_sound_installer("DLGCLOSE")
        self.EndModal(wx.ID_OK)

    def on_close_dialog_event(self, event): 
        self._should_launch_titan = False 
        play_sound_installer("DLGCLOSE")
        self.EndModal(wx.ID_CANCEL) 

    def ShouldLaunchTitan(self):
        return self._should_launch_titan

# =============== OKNO 2.5 (TitanConfigDialog - wykryto istniejącą instalację) ===============
class TitanConfigDialog(wx.Dialog):
    """Dialog wyświetlany gdy wykryto katalog titan_data (istniejąca instalacja)."""
    RESULT_LAUNCH = wx.ID_YES
    RESULT_UPDATE = wx.ID_NO
    RESULT_MANAGE_TCE = wx.ID_APPLY

    def __init__(self, parent):
        super().__init__(parent, title=t('config_dialog_title'), style=wx.DEFAULT_DIALOG_STYLE)
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        st_info = wx.StaticText(panel, label=t('config_message'))
        st_info.Wrap(350)
        vbox.Add(st_info, 0, wx.ALL, 15)

        btn_launch = wx.Button(panel, label=t('btn_launch_titan'))
        btn_launch.Bind(wx.EVT_BUTTON, self.on_launch)
        btn_launch.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        vbox.Add(btn_launch, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_update = wx.Button(panel, label=t('btn_update_titan'))
        btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        btn_update.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        vbox.Add(btn_update, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_manage_tce = wx.Button(panel, label=t('btn_manage_tce_integration'))
        btn_manage_tce.Bind(wx.EVT_BUTTON, self.on_manage_tce)
        btn_manage_tce.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        vbox.Add(btn_manage_tce, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        vbox.Fit(self)
        self.SetMinSize(self.GetSize())
        self.CenterOnScreen()
        self.Bind(wx.EVT_SHOW, self.on_show_event)
        self.Bind(wx.EVT_CLOSE, self.on_close_event)

    def on_show_event(self, event):
        if event.IsShown(): play_sound_installer("DLGOPEN")
        event.Skip()

    def on_launch(self, event):
        play_sound_installer("DLGCLOSE")
        self.EndModal(self.RESULT_LAUNCH)

    def on_update(self, event):
        play_sound_installer("DLGCLOSE")
        self.EndModal(self.RESULT_UPDATE)

    def on_manage_tce(self, event):
        play_sound_installer("DLGCLOSE")
        self.EndModal(self.RESULT_MANAGE_TCE)

    def on_close_event(self, event):
        play_sound_installer("DLGCLOSE")
        self.EndModal(wx.ID_CANCEL)

# =============== OKNO 2.6 (TCEIntegrationDialog - zarządzanie integracją pakietów) ===============
class TCEIntegrationDialog(wx.Dialog):
    """Dialog do zarządzania integracją pakietów .TCEPACKAGE z Windows."""

    def __init__(self, parent):
        super().__init__(parent, title=t('tce_integration_dialog_title'), style=wx.DEFAULT_DIALOG_STYLE)
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        st_info = wx.StaticText(panel, label=t('tce_integration_message'))
        st_info.Wrap(350)
        vbox.Add(st_info, 0, wx.ALL, 15)

        # Sprawdź czy integracja jest już zarejestrowana
        self.is_registered = self.check_tce_registration()

        status_text = t('tce_integration_status_registered') if self.is_registered else t('tce_integration_status_not_registered')
        self.st_status = wx.StaticText(panel, label=status_text)
        self.st_status.Wrap(350)
        vbox.Add(self.st_status, 0, wx.ALL, 10)

        btn_register = wx.Button(panel, label=t('btn_register_tce_integration'))
        btn_register.Bind(wx.EVT_BUTTON, self.on_register)
        btn_register.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        if self.is_registered:
            btn_register.Enable(False)
        vbox.Add(btn_register, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_unregister = wx.Button(panel, label=t('btn_unregister_tce_integration'))
        btn_unregister.Bind(wx.EVT_BUTTON, self.on_unregister)
        btn_unregister.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        if not self.is_registered:
            btn_unregister.Enable(False)
        vbox.Add(btn_unregister, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_close = wx.Button(panel, label=t('btn_close'))
        btn_close.Bind(wx.EVT_BUTTON, self.on_close_button)
        btn_close.Bind(wx.EVT_SET_FOCUS, on_control_focus_event_installer)
        vbox.Add(btn_close, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        vbox.Fit(self)
        self.SetMinSize(self.GetSize())
        self.CenterOnScreen()
        self.Bind(wx.EVT_SHOW, self.on_show_event)
        self.Bind(wx.EVT_CLOSE, self.on_close_event)

    def check_tce_registration(self):
        """Sprawdza czy rozszerzenie .TCEPACKAGE jest zarejestrowane w rejestrze."""
        if not winreg or os.name != 'nt':
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.TCEPACKAGE")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"[TCE_INTEGRATION] Błąd sprawdzania rejestracji: {e}")
            return False

    def on_show_event(self, event):
        if event.IsShown():
            play_sound_installer("DLGOPEN")
        event.Skip()

    def on_register(self, event):
        """Rejestruje integrację pakietów TCE z Windows."""
        play_sound_installer("DLGOPEN")
        try:
            # Użyj funkcji rejestracji z odpowiednimi ścieżkami
            handler_exe = os.path.abspath(os.path.join(BASE_CONFIG["SCRIPT_DIR"], "titan.exe"))
            if not os.path.isfile(handler_exe):
                wx.MessageBox(t('tce_error_titan_exe_missing').format(handler_exe), t('error_title'), wx.OK | wx.ICON_ERROR)
                return

            register_tcepackage_integration(handler_exe, BASE_CONFIG["SCRIPT_DIR"])

            wx.MessageBox(t('tce_integration_registered_success'), t('tce_success_title'), wx.OK | wx.ICON_INFORMATION)

            # Odśwież status
            self.is_registered = True
            self.st_status.SetLabel(t('tce_integration_status_registered'))
            self.FindWindowByLabel(t('btn_register_tce_integration')).Enable(False)
            self.FindWindowByLabel(t('btn_unregister_tce_integration')).Enable(True)
            self.Layout()

        except Exception as e:
            print(f"[TCE_INTEGRATION] Błąd rejestracji: {e}")
            traceback.print_exc()
            wx.MessageBox(t('tce_error_registration').format(e), t('error_title'), wx.OK | wx.ICON_ERROR)

    def on_unregister(self, event):
        """Wyrejestrowuje integrację pakietów TCE z Windows."""
        play_sound_installer("DLGOPEN")

        # Potwierdzenie przed usunięciem
        dlg = wx.MessageDialog(self,
                               t('tce_unregister_confirm'),
                               t('tce_unregister_confirm_title'),
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()

        try:
            unregister_tcepackage_integration()

            wx.MessageBox(t('tce_integration_unregistered_success'), t('tce_success_title'), wx.OK | wx.ICON_INFORMATION)

            # Odśwież status
            self.is_registered = False
            self.st_status.SetLabel(t('tce_integration_status_not_registered'))
            self.FindWindowByLabel(t('btn_register_tce_integration')).Enable(True)
            self.FindWindowByLabel(t('btn_unregister_tce_integration')).Enable(False)
            self.Layout()

        except Exception as e:
            print(f"[TCE_INTEGRATION] Błąd wyrejestrowania: {e}")
            traceback.print_exc()
            wx.MessageBox(t('tce_error_unregistration').format(e), t('error_title'), wx.OK | wx.ICON_ERROR)

    def on_close_button(self, event):
        play_sound_installer("DLGCLOSE")
        self.EndModal(wx.ID_OK)

    def on_close_event(self, event):
        play_sound_installer("DLGCLOSE")
        self.EndModal(wx.ID_CANCEL)

# =============== FUNKCJE POMOCNICZE DO ZARZĄDZANIA INTEGRACJĄ TCE ===============
def register_tcepackage_integration(handler_exe_path, base_install_dir):
    """Rejestruje rozszerzenie .TCEPACKAGE w rejestrze Windows."""
    if not winreg or os.name != 'nt':
        print("[TCE_INTEGRATION] Pomijam - nie Windows lub brak winreg")
        raise Exception(t('tce_error_windows_only'))

    print(f"[TCE_INTEGRATION] Rejestracja integracji: {handler_exe_path}")

    prog_id = "Titan.TCEPackageFile"
    ext = ".TCEPACKAGE"
    cmd_arg = BASE_CONFIG["COMMAND_LINE_ARG_TCE_PACKAGE"]
    cmd = f'"{handler_exe_path}" {cmd_arg} "%1"'

    try:
        # Rejestracja w HKEY_CURRENT_USER (nie wymaga admina)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}") as key:
            winreg.SetValue(key, None, winreg.REG_SZ, prog_id)
            print(f"[TCE_INTEGRATION] {ext} -> {prog_id}")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}") as key:
            winreg.SetValue(key, None, winreg.REG_SZ, "Pakiet danych środowiska Titan")
            with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                winreg.SetValue(cmd_key, None, winreg.REG_SZ, cmd)
                print(f"[TCE_INTEGRATION] Komenda zarejestrowana: {cmd}")

        # Tworzenie pliku .reg do ręcznej rejestracji
        try:
            reg_file_path = os.path.join(base_install_dir, "register_tcepackage.reg")
            handler_exe_escaped = handler_exe_path.replace("\\", "\\\\")
            cmd_escaped = cmd.replace("\\", "\\\\").replace('"', '\\"')

            reg_content = f'''Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Classes\\{ext}]
@="{prog_id}"

[HKEY_CURRENT_USER\\Software\\Classes\\{prog_id}]
@="Pakiet danych środowiska Titan"

[HKEY_CURRENT_USER\\Software\\Classes\\{prog_id}\\shell\\open\\command]
@="{cmd_escaped}"
'''
            with open(reg_file_path, 'w', encoding='utf-16le') as f_reg:
                f_reg.write('\ufeff')  # BOM dla UTF-16 LE
                f_reg.write(reg_content)
            print(f"[TCE_INTEGRATION] Plik .reg utworzony: {reg_file_path}")
        except Exception as e_reg_file:
            print(f"[TCE_INTEGRATION][UWAGA] Nie utworzono pliku .reg: {e_reg_file}")

        print("[TCE_INTEGRATION] Rejestracja zakończona sukcesem.")

    except PermissionError:
        print("[TCE_INTEGRATION][BŁĄD] Brak uprawnień")
        raise Exception(t('status_extension_permission_error'))
    except Exception as e_reg:
        print(f"[TCE_INTEGRATION][BŁĄD] {e_reg}")
        traceback.print_exc()
        raise

def unregister_tcepackage_integration():
    """Wyrejestrowuje rozszerzenie .TCEPACKAGE z rejestru Windows."""
    if not winreg or os.name != 'nt':
        print("[TCE_INTEGRATION] Pomijam - nie Windows lub brak winreg")
        raise Exception(t('tce_error_windows_only'))

    print("[TCE_INTEGRATION] Wyrejestrowanie integracji")

    prog_id = "Titan.TCEPackageFile"
    ext = ".TCEPACKAGE"

    try:
        # Usuń klucz rozszerzenia
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}")
            print(f"[TCE_INTEGRATION] Usunięto klucz: {ext}")
        except FileNotFoundError:
            print(f"[TCE_INTEGRATION] Klucz {ext} nie istniał")

        # Usuń klucz ProgID (wraz z podkluczami)
        try:
            # Najpierw usuń podklucze
            key_path = f"Software\\Classes\\{prog_id}\\shell\\open\\command"
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except FileNotFoundError:
                pass

            key_path = f"Software\\Classes\\{prog_id}\\shell\\open"
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except FileNotFoundError:
                pass

            key_path = f"Software\\Classes\\{prog_id}\\shell"
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            except FileNotFoundError:
                pass

            # Teraz usuń główny klucz
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}")
            print(f"[TCE_INTEGRATION] Usunięto klucz: {prog_id}")
        except FileNotFoundError:
            print(f"[TCE_INTEGRATION] Klucz {prog_id} nie istniał")

        print("[TCE_INTEGRATION] Wyrejestrowanie zakończone sukcesem.")

    except PermissionError:
        print("[TCE_INTEGRATION][BŁĄD] Brak uprawnień")
        raise Exception(t('status_extension_permission_error'))
    except Exception as e_unreg:
        print(f"[TCE_INTEGRATION][BŁĄD] {e_unreg}")
        traceback.print_exc()
        raise

# =============== OKNO 3 (InstallFrame) ===============
class InstallFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(650, 200))
        self.app_settings = None; panel = wx.Panel(self)
        self.st_status = wx.StaticText(panel, label=t('status_starting'), pos=(10,10), size=(600,25))
        self.prg = wx.Gauge(panel, range=100, pos=(10,40), size=(600,25), style=wx.GA_HORIZONTAL)
        self.selected_components = {}
        self.delete_before_install = False
        # Dla asynchronicznej instalacji komponentów
        self.component_status = {}
        self.status_lock = threading.Lock()
        self.completed_count = 0
        self.total_count = 0
        self.Bind(wx.EVT_SHOW, self.on_show); self.Bind(wx.EVT_CLOSE, self.on_close_frame_event); self.CenterOnScreen()

    def on_show(self, event):
        if event.IsShown():
            play_sound_installer("DLGOPEN")
            install_dir_path = BASE_CONFIG["MAIN_INSTALLER_INSTALL_DIR"]
            try: os.makedirs(install_dir_path, exist_ok=True)
            except OSError as e: wx.MessageBox(t('error_create_dir').format(install_dir_path, e), t('error_title'), wx.OK|wx.ICON_ERROR, self); self.Close(); return
            install_thread = threading.Thread(target=self.do_installation, daemon=True); install_thread.start()
        event.Skip()
    def on_close_frame_event(self, event): stop_looping_sound_installer(); play_sound_installer("DLGCLOSE"); self.Destroy()

    def update_component_progress(self, comp_name, stage, progress):
        """Aktualizacja postępu pojedynczego komponentu (thread-safe)."""
        with self.status_lock:
            if comp_name not in self.component_status:
                self.component_status[comp_name] = {'stage': 'pending', 'progress': 0, 'completed': False}

            self.component_status[comp_name]['stage'] = stage
            self.component_status[comp_name]['progress'] = progress

            # Oblicz globalny postęp
            total_progress = 0
            for comp_data in self.component_status.values():
                total_progress += comp_data['progress']

            avg_progress = int(total_progress / self.total_count) if self.total_count > 0 else 0
            status_text = f"{comp_name}: {stage}"

            self.post_update(status_text, avg_progress)

    def mark_component_completed(self, comp_name):
        """Oznacz komponent jako ukończony (thread-safe)."""
        with self.status_lock:
            if comp_name in self.component_status:
                self.component_status[comp_name]['completed'] = True
                self.component_status[comp_name]['progress'] = 100
            self.completed_count += 1
            print(f"[ASYNC] Komponent '{comp_name}' ukończony ({self.completed_count}/{self.total_count})")

    def install_single_component(self, comp_name, url, fname_7z, install_dir, sevenz_path, wget_path):
        """Instaluje pojedynczy komponent (pobieranie + rozpakowywanie) - uruchamiane w wątku."""
        try:
            print(f"[ASYNC] Rozpoczynam instalację komponentu: {comp_name}")
            archive_local_path = os.path.join(BASE_CONFIG["SCRIPT_DIR"], fname_7z)

            # Callback do aktualizacji postępu pobierania (0-50% zakresu komponentu)
            def download_progress_callback(progress_percent):
                # Mapuj 0-100% pobierania na 0-50% komponentu
                self.update_component_progress(comp_name, f"{t('status_downloading')} ({progress_percent}%)", progress_percent // 2)

            # Pobieranie
            print(f"[ASYNC] {comp_name}: Rozpoczynam pobieranie...")
            if not self.wget_download_with_callback(url, archive_local_path, wget_path, download_progress_callback):
                print(f"[ASYNC] {comp_name}: Błąd pobierania.")
                self.update_component_progress(comp_name, t('status_download_error'), 0)
                return False

            # Callback do aktualizacji postępu rozpakowywania (50-100% zakresu komponentu)
            def extract_progress_callback(progress_percent):
                # Mapuj 0-100% rozpakowywania na 50-100% komponentu
                self.update_component_progress(comp_name, f"{t('status_extracting')} ({progress_percent}%)", 50 + progress_percent // 2)

            # Rozpakowywanie
            print(f"[ASYNC] {comp_name}: Rozpoczynam rozpakowywanie...")
            if not self.sevenz_extract_with_callback(archive_local_path, install_dir, sevenz_path, extract_progress_callback):
                print(f"[ASYNC] {comp_name}: Błąd rozpakowywania.")
                self.update_component_progress(comp_name, t('status_extract_error'), 50)
                return False

            # Usuwanie archiwum
            try:
                if os.path.exists(archive_local_path):
                    os.remove(archive_local_path)
                    print(f"[ASYNC] {comp_name}: Usunięto archiwum {archive_local_path}")
            except Exception as e_rm:
                print(f"[ASYNC] {comp_name}: Nie usunięto {archive_local_path}: {e_rm}")

            # Oznacz jako ukończone
            self.mark_component_completed(comp_name)
            return True

        except Exception as e:
            print(f"[ASYNC] {comp_name}: Wyjątek podczas instalacji: {e}")
            traceback.print_exc()
            self.update_component_progress(comp_name, f"Błąd: {e}", 0)
            return False

    def do_installation(self):
        print("[INSTALL THREAD] Rozpoczęto wątek instalacji.")
        current_install_dir = os.path.abspath(BASE_CONFIG["MAIN_INSTALLER_INSTALL_DIR"])
        current_sevenz_path = os.path.abspath(BASE_CONFIG["SEVENZ_PATH"])
        current_wget_path = os.path.abspath(BASE_CONFIG["WGET_PATH"])
        installation_ok = False
        try:
            # Usunięcie folderu ustawień TCE (jeśli wybrano)
            if self.delete_before_install:
                settings_dir = os.path.join(os.getenv('APPDATA', ''), 'titosoft')
                if os.path.isdir(settings_dir):
                    self.post_update(t('status_deleting_settings'), 1)
                    print(f"[INSTALL THREAD] Usuwanie folderu ustawień: {settings_dir}")
                    try:
                        shutil.rmtree(settings_dir, ignore_errors=True)
                        print("[INSTALL THREAD] Folder ustawień usunięty.")
                    except Exception as e_rm:
                        print(f"[INSTALL THREAD][BŁĄD] Usuwanie folderu ustawień: {e_rm}")
                        traceback.print_exc()
                else:
                    print(f"[INSTALL THREAD] Folder ustawień nie istnieje: {settings_dir}")

            selected = self.selected_components
            tasks = []
            if selected.get('TCE'): tasks.append((t('component_tce'), BASE_CONFIG["URL_MAIN"], "titan.main.7z"))
            if selected.get('Interpreter'): tasks.append((t('component_interpreter'), BASE_CONFIG["URL_INTERPRETER"], "titan.interpreter.7z"))
            if selected.get('SoundThemes'): tasks.append((t('component_sound_themes'), BASE_CONFIG["URL_SOUND_THEMES"], "titan.soundthemes.7z"))

            if not tasks:
                self.post_update(t('status_no_components'), 0)
                time.sleep(2)
                wx.CallAfter(self.Close)
                return

            # Inicjalizuj liczniki
            self.total_count = len(tasks)
            self.completed_count = 0

            print(f"[INSTALL THREAD] Rozpoczynam równoległe pobieranie i rozpakowywanie {self.total_count} komponentów...")

            # Uruchom wątki dla każdego komponentu
            threads = []
            for comp_name, url, fname_7z in tasks:
                comp_thread = threading.Thread(
                    target=self.install_single_component,
                    args=(comp_name, url, fname_7z, current_install_dir, current_sevenz_path, current_wget_path),
                    daemon=True
                )
                comp_thread.start()
                threads.append(comp_thread)
                print(f"[INSTALL THREAD] Uruchomiono wątek dla komponentu: {comp_name}")

            # Czekaj na zakończenie wszystkich wątków
            print("[INSTALL THREAD] Oczekiwanie na zakończenie wszystkich komponentów...")
            for comp_thread in threads:
                comp_thread.join()

            print(f"[INSTALL THREAD] Wszystkie komponenty zakończone ({self.completed_count}/{self.total_count})")

            # Konfiguracja handlera pakietów (w katalogu instalatora, nie w titan_data)
            self.post_update(t('status_configuring_packages'), 94)
            try:
                config_file_for_handler = os.path.join(BASE_CONFIG["SCRIPT_DIR"], BASE_CONFIG["HANDLER_CONFIG_FILENAME"])
                config_data = {"sevenz_path_abs": current_sevenz_path, "titan_install_dir_abs": current_install_dir }
                with open(config_file_for_handler, 'w') as f_cfg: json.dump(config_data, f_cfg, indent=2)
                print(f"[INSTALL THREAD] Plik konfiguracyjny zapisany: {config_file_for_handler}")
            except Exception as e_cfg: print(f"[BŁĄD] Nie zapisano konfiguracji handlera: {e_cfg}"); traceback.print_exc()

            # Tworzenie skrótu na pulpicie
            self.post_update(t('status_post_install'), 95)
            print("[INSTALL THREAD] Rozpoczynam zadania poinstalacyjne...")
            try:
                if self.app_settings and self.app_settings.create_desktop_shortcut:
                    print("[INSTALL THREAD] Tworzenie skrótu na pulpicie...")
                    self.create_desktop_shortcut_task(current_install_dir)
                    print("[INSTALL THREAD] Skrót utworzony (lub pominięty).")
            except Exception as e_shortcut:
                print(f"[INSTALL THREAD][BŁĄD] Tworzenie skrótu nie powiodło się: {e_shortcut}")
                traceback.print_exc()

            # Rejestracja rozszerzenia .TCEPACKAGE (tylko wpisy rejestrowe, szybkie)
            try:
                if self.app_settings and self.app_settings.register_tcepackage_extension:
                    print("[INSTALL THREAD] Rejestracja rozszerzenia .TCEPACKAGE...")
                    self.register_tcepackage_extension_task(current_install_dir)
                    print("[INSTALL THREAD] Rejestracja zakończona.")
            except Exception as e_reg:
                print(f"[INSTALL THREAD][BŁĄD] Rejestracja rozszerzenia nie powiodła się: {e_reg}")
                traceback.print_exc()

            installation_ok = True
        except Exception as e_install:
            print(f"[BŁĄD WĄTKU INSTALACJI] {e_install}")
            traceback.print_exc()
            self.post_update(t('tce_error_installation').format(e_install), 0)
        finally:
            stop_looping_sound_installer()
            print("[INSTALL THREAD] Zatrzymano muzykę instalacji.")

            # Zawsze wyświetl dialog zakończenia (nawet jeśli wystąpiły błędy)
            if installation_ok:
                self.post_update(t('status_finalizing'), 100)
                try: play_sound_installer("CONFIGURATION")
                except Exception: pass

            print("[INSTALL THREAD] Przygotowuję dialog zakończenia...")

            def show_finish_dialog_and_conditionally_launch():
                print("[FINISH DIALOG] Funkcja show_finish_dialog_and_conditionally_launch wywołana.")
                try:
                    if not wx.GetApp():
                        print("[FINISH DIALOG] wx.GetApp() zwróciło None, przerywam.")
                        return
                    try:
                        if self.IsBeingDeleted():
                            print("[FINISH DIALOG] InstallFrame jest usuwany, przerywam.")
                            return
                    except Exception:
                        print("[FINISH DIALOG] Nie można sprawdzić stanu InstallFrame, przerywam.")
                        return

                    print("[FINISH DIALOG] Tworzę FinishDialog...")
                    finish_dialog = FinishDialog(self)
                    print("[FINISH DIALOG] FinishDialog utworzony, wywołuję ShowModal()...")
                    dialog_result_id = finish_dialog.ShowModal()
                    print(f"[FINISH DIALOG] ShowModal() zwrócił: {dialog_result_id}")
                    should_launch_titan = False
                    if dialog_result_id == wx.ID_OK:
                        should_launch_titan = finish_dialog.ShouldLaunchTitan()
                        print(f"[FINISH DIALOG] Użytkownik wybrał uruchomienie Titana: {should_launch_titan}")
                    finish_dialog.Destroy()
                    print("[FINISH DIALOG] Dialog zniszczony.")
                    if should_launch_titan:
                        titan_exe_path = os.path.abspath(BASE_CONFIG["MAIN_APP_EXE_PATH_FOR_SHORTCUT"])
                        print(f"[FINISH DIALOG] Próbuję uruchomić: {titan_exe_path}")
                        if os.path.isfile(titan_exe_path):
                            try:
                                subprocess.Popen([titan_exe_path])
                                print("[FINISH DIALOG] Titan uruchomiony.")
                            except Exception as e_launch:
                                print(f"[FINISH DIALOG] Błąd uruchamiania: {e_launch}")
                                wx.MessageBox(t('error_launch_titan').format(e_launch), t('error_title'), wx.OK | wx.ICON_ERROR, self)
                        else:
                            print(f"[FINISH DIALOG] Plik nie istnieje: {titan_exe_path}")
                            wx.MessageBox(t('error_titan_not_found').format(titan_exe_path), t('error_title'), wx.OK | wx.ICON_ERROR, self)
                    print("[FINISH DIALOG] Zamykam okno instalacji...")
                    self.Close()
                    print("[FINISH DIALOG] Zamykam aplikację instalatora...")
                    wx.CallAfter(wx.GetApp().ExitMainLoop)
                    print("[FINISH DIALOG] Funkcja zakończona.")
                except Exception as e_finish:
                    print(f"[FINISH DIALOG][BŁĄD] Wyjątek w finish dialog: {e_finish}")
                    traceback.print_exc()
                    try:
                        self.Close()
                        wx.CallAfter(wx.GetApp().ExitMainLoop)
                    except Exception: pass

            print("[INSTALL THREAD] Wywołuję wx.CallAfter dla dialogu zakończenia...")
            try:
                wx.CallAfter(show_finish_dialog_and_conditionally_launch)
            except Exception:
                print("[INSTALL THREAD][BŁĄD] Nie udało się wywołać wx.CallAfter dla dialogu zakończenia.")
            print("[INSTALL THREAD] Wątek instalacji kończy pracę.")

    def create_desktop_shortcut_task(self, base_install_dir):
        """Tworzy skrót na pulpicie używając PowerShell (bez COM, aby uniknąć zawieszania)."""
        self.post_update(t('status_creating_shortcut'), 96)
        try:
            program_target = os.path.abspath(BASE_CONFIG["MAIN_APP_EXE_PATH_FOR_SHORTCUT"])
            abs_base_install_dir = os.path.abspath(base_install_dir)
            print(f"[SHORTCUT] Tworzenie skrótu do: {program_target}")
            print(f"[SHORTCUT] Katalog roboczy: {abs_base_install_dir}")

            if not os.path.exists(program_target):
                self.post_update(t('status_shortcut_file_missing').format(program_target), 96)
                print(f"[SHORTCUT] BŁĄD: Plik {program_target} nie istnieje!")
                if os.path.exists(abs_base_install_dir):
                    print(f"[SHORTCUT] Pliki w {abs_base_install_dir}:")
                    try:
                        for item in os.listdir(abs_base_install_dir):
                            print(f"  - {item}")
                    except Exception:
                        pass
                return

            # Znajdź folder Desktop
            desktop_path = None
            if winreg and os.name == 'nt':
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                        r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                    desktop_path, _ = winreg.QueryValueEx(key, "Desktop")
                    winreg.CloseKey(key)
                    desktop_path = os.path.expandvars(desktop_path)
                    if not os.path.exists(desktop_path):
                        desktop_path = None
                except Exception:
                    desktop_path = None

            if not desktop_path:
                for path in [
                    os.path.join(os.path.expanduser("~"), "Desktop"),
                    os.path.join(os.path.expanduser("~"), "Pulpit"),
                    os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
                    os.path.join(os.path.expanduser("~"), "OneDrive", "Pulpit"),
                    os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
                    os.path.join(os.environ.get("USERPROFILE", ""), "Pulpit"),
                ]:
                    if path and os.path.exists(path):
                        desktop_path = path
                        break

            if not desktop_path or not os.path.exists(desktop_path):
                print("[SHORTCUT] Nie znaleziono folderu Desktop.")
                self.post_update(t('status_shortcut_desktop_not_found'), 96)
                return

            sc_path = os.path.join(desktop_path, "Titan.lnk")
            print(f"[SHORTCUT] Tworzenie skrótu w: {sc_path}")

            # Użyj PowerShell - bezpieczne, bez COM w procesie Pythona
            ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{sc_path}")
$Shortcut.TargetPath = "{program_target}"
$Shortcut.WorkingDirectory = "{abs_base_install_dir}"
$Shortcut.Description = "Uruchom Titan"
$Shortcut.Save()
'''
            print("[SHORTCUT] Uruchamiam PowerShell z timeout 15s...")
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                    capture_output=True, text=True, timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                if result.returncode == 0 and os.path.exists(sc_path):
                    print(f"[SHORTCUT] Skrót utworzony pomyślnie: {sc_path}")
                    self.post_update(t('status_shortcut_created'), 97)
                else:
                    print(f"[SHORTCUT] Błąd PowerShell (rc={result.returncode}): {result.stderr}")
                    self.post_update(t('status_shortcut_error'), 96)
            except subprocess.TimeoutExpired:
                print("[SHORTCUT] PowerShell przekroczył timeout!")
                self.post_update(t('status_shortcut_timeout'), 96)
            except Exception as e_ps:
                print(f"[SHORTCUT] Wyjątek PowerShell: {e_ps}")
                self.post_update(t('status_shortcut_error'), 96)

        except Exception as e:
            self.post_update(t('status_shortcut_error'), 96)
            print(f"[BŁĄD SKRÓTU] {e}")
            traceback.print_exc()
        finally:
            print("[SHORTCUT] create_desktop_shortcut_task zakończona.")

    def register_tcepackage_extension_task(self, base_install_dir):
        """Rejestruje rozszerzenie .TCEPACKAGE w rejestrze Windows.
        Uproszczona wersja - tylko wpisy rejestrowe, bez kopiowania plików i COM."""
        self.post_update(t('status_registering_extension'), 98)
        if not winreg or os.name != 'nt':
            print("[REJESTRACJA] Pomijam - nie Windows lub brak winreg")
            return
        try:
            # Użyj titan.exe jako handlera dla .tcepackage (nie instalatora!)
            # titan.exe jest w katalogu głównym (SCRIPT_DIR), nie w titan_data
            handler_exe = os.path.abspath(os.path.join(BASE_CONFIG["SCRIPT_DIR"], "titan.exe"))
            print(f"[REJESTRACJA] Handler exe (titan.exe): {handler_exe}")

            # Sprawdź czy instalator istnieje
            if not os.path.isfile(handler_exe):
                print(f"[REJESTRACJA][BŁĄD] Instalator nie istnieje: {handler_exe}")
                self.post_update(t('status_extension_error'), 98)
                return

            prog_id = "Titan.TCEPackageFile"
            ext = ".TCEPACKAGE"
            cmd_arg = BASE_CONFIG["COMMAND_LINE_ARG_TCE_PACKAGE"]
            cmd = f'"{handler_exe}" {cmd_arg} "%1"'
            print(f"[REJESTRACJA] Komenda: {cmd}")

            # Rejestracja w HKEY_CURRENT_USER (nie wymaga admina)
            self.post_update(t('status_registering_registry'), 98)
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}") as key:
                winreg.SetValue(key, None, winreg.REG_SZ, prog_id)
                print(f"[REJESTRACJA] {ext} -> {prog_id}")

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{prog_id}") as key:
                winreg.SetValue(key, None, winreg.REG_SZ, "Pakiet danych środowiska Titan")
                with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                    winreg.SetValue(cmd_key, None, winreg.REG_SZ, cmd)
                    print(f"[REJESTRACJA] Komenda zarejestrowana.")

            # Tworzenie pliku .reg do ręcznej rejestracji
            try:
                reg_file_path = os.path.join(base_install_dir, "register_tcepackage.reg")
                # Escape backslashes dla formatu .reg (podwójne backslashes)
                handler_exe_escaped = handler_exe.replace("\\", "\\\\")
                cmd_escaped = cmd.replace("\\", "\\\\").replace('"', '\\"')

                reg_content = f'''Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Classes\\{ext}]
@="{prog_id}"

[HKEY_CURRENT_USER\\Software\\Classes\\{prog_id}]
@="Pakiet danych środowiska Titan"

[HKEY_CURRENT_USER\\Software\\Classes\\{prog_id}\\shell\\open\\command]
@="{cmd_escaped}"
'''
                with open(reg_file_path, 'w', encoding='utf-16le') as f_reg:
                    f_reg.write('\ufeff')  # BOM dla UTF-16 LE
                    f_reg.write(reg_content)
                print(f"[REJESTRACJA] Plik .reg utworzony: {reg_file_path}")
            except Exception as e_reg_file:
                print(f"[REJESTRACJA][UWAGA] Nie utworzono pliku .reg: {e_reg_file}")

            self.post_update(t('status_extension_registered'), 99)
            print("[REJESTRACJA] Sukces.")

        except PermissionError:
            self.post_update(t('status_extension_permission_error'), 98)
            print("[REJESTRACJA][BŁĄD] Brak uprawnień")
        except Exception as e_reg:
            self.post_update(t('status_extension_error'), 98)
            print(f"[BŁĄD REJESTRACJI] {e_reg}")
            traceback.print_exc()
        finally:
            print("[REJESTRACJA] register_tcepackage_extension_task zakończona.")
    def wget_download_with_callback(self, url, outfile, wget_exe_path, progress_callback):
        """Pobieranie z wget z callbackiem postępu."""
        cmd = [wget_exe_path, "--progress=bar:force", "--no-check-certificate", "-O", outfile, url]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace',
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except Exception as e:
            print(f"[WGET BŁĄD] {e}")
            return False

        regex = re.compile(r"(\d+)%")
        for line in proc.stdout:
            mo = regex.search(line)
            if mo:
                progress_callback(int(mo.group(1)))

        return proc.wait() == 0

    def wget_download(self, url, outfile, task_label_prefix, wget_exe_path):
        """Pobieranie z wget (wersja ze starym interfejsem dla kompatybilności)."""
        cmd = [wget_exe_path, "--progress=bar:force", "--no-check-certificate", "-O", outfile, url]
        try: proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except Exception as e: print(f"[WGET BŁĄD] {e}"); return False
        regex = re.compile(r"(\d+)%");
        for line in proc.stdout:
            mo = regex.search(line)
            if mo: self.post_update(f"{task_label_prefix} - {mo.group(1)}%", int(mo.group(1)))
        return proc.wait() == 0
    def sevenz_extract_with_callback(self, archive, target_dir_abs, sevenz_exe_abs, progress_callback):
        """Rozpakowanie archiwum 7z z callbackiem postępu."""
        cmd = [sevenz_exe_abs, "x", archive, f"-o{target_dir_abs}", "-y", "-bso0", "-bsp1"]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace',
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except Exception as e:
            print(f"[7Z BŁĄD] {e}")
            return False

        # Regex do wychwycenia procentów z 7z (np. "  5%" lub "100%")
        re_percent = re.compile(r'\s*(\d+)%')
        last_percent = 0
        extracted_any = False

        for line in proc.stdout:
            line_stripped = line.strip()
            mo = re_percent.search(line_stripped)
            if mo:
                extracted_any = True
                percent = int(mo.group(1))
                if percent > last_percent:
                    last_percent = percent
                    progress_callback(percent)

        ret_code = proc.wait()

        # Jeśli rozpakowywanie się powiodło, zgłoś 100%
        if ret_code == 0:
            progress_callback(100)

        return ret_code == 0

    def sevenz_extract(self, archive, task_label_prefix, target_dir_abs, sevenz_exe_abs):
        """Rozpakowanie archiwum 7z z paskiem postępu opartym na procentach (stary interfejs)."""
        cmd = [sevenz_exe_abs, "x", archive, f"-o{target_dir_abs}", "-y", "-bso0", "-bsp1"]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace',
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except Exception as e:
            print(f"[7Z BŁĄD] {e}")
            return False

        # Regex do wychwycenia procentów z 7z (np. "  5%" lub "100%")
        re_percent = re.compile(r'\s*(\d+)%')
        last_percent = 0
        extracted_any = False

        for line in proc.stdout:
            line_stripped = line.strip()
            # Szukaj procentów w linii
            mo = re_percent.search(line_stripped)
            if mo:
                extracted_any = True
                percent = int(mo.group(1))
                if percent > last_percent:
                    last_percent = percent
                    self.post_update(f"{task_label_prefix} - {percent}%", percent)

        ret_code = proc.wait()

        # Jeśli rozpakowywanie się powiodło, pokaż 100%
        if ret_code == 0:
            if extracted_any:
                self.post_update(f"{task_label_prefix} - Zakończono.", 100)
            else:
                # Brak procentów w output, ale operacja się powiodła
                self.post_update(f"{task_label_prefix} - Przetworzono.", 100)

        return ret_code == 0
    def post_update(self, text, gauge_val):
        try:
            if wx.GetApp() and wx.GetApp().IsMainLoopRunning() and not self.IsBeingDeleted():
                wx.CallAfter(self._update_gui, text, gauge_val)
            else:
                print(f"[STATUS UPDATE POZA GUI] {text} ({gauge_val}%)")
        except Exception:
            print(f"[STATUS UPDATE POZA GUI] {text} ({gauge_val}%)")
    def _update_gui(self, text, val): # ... (jak poprzednio) ...
        try:
            if self and hasattr(self, 'st_status') and self.st_status and hasattr(self, 'prg') and self.prg : self.st_status.SetLabel(text); self.prg.SetValue(max(0, min(val, 100)))
        except: pass

# =============== GŁÓWNA APLIKACJA INSTALATORA ===============
class TitanInstallerApp(wx.App):
    def __init__(self, redirect, base_paths_config):
        print("[INSTALLER_APP DEBUG] TitanInstallerApp.__init__")
        self.base_paths = base_paths_config
        global BASE_CONFIG, SFX_PATHS 
        BASE_CONFIG = self.base_paths # Ustaw globalny BASE_CONFIG dla tego modułu
        SFX_PATHS = {
            "STARTUP": os.path.join(BASE_CONFIG["SFX_DIR"], "startup.ogg"),
            "DLGOPEN": os.path.join(BASE_CONFIG["SFX_DIR"], "dlgopen.ogg"),
            "DLGCLOSE": os.path.join(BASE_CONFIG["SFX_DIR"], "dlgclose.ogg"),
            "INSTALLING": os.path.join(BASE_CONFIG["SFX_DIR"], "installingapps.ogg"),
            "FOCUS": os.path.join(BASE_CONFIG["SFX_DIR"], "focus.ogg"),
            "CONFIGURATION": os.path.join(BASE_CONFIG["SFX_DIR"], "success.ogg"),
        }
        self.create_desktop_shortcut = self.base_paths.get("CREATE_DESKTOP_SHORTCUT_DEFAULT", False)
        self.register_tcepackage_extension = self.base_paths.get("REGISTER_TCEPACKAGE_DEFAULT", False)
        self.background_music_enabled = True  # Default to enabled
        self.timer = None; self.start_frame_instance = None
        super().__init__(redirect)

    def OnInit(self):
        print("[INSTALLER_APP DEBUG] TitanInstallerApp.OnInit - Rozpoczęto")
        # Inicjalizacja audio
        if not init_pygame_audio_installer():
            wx.MessageBox(t('error_audio_init'), t('error_title'), wx.OK | wx.ICON_WARNING)

        # Sprawdź czy katalog titan_data istnieje (istniejąca instalacja)
        titan_data_dir = BASE_CONFIG["MAIN_INSTALLER_INSTALL_DIR"]
        if os.path.isdir(titan_data_dir):
            print(f"[APP DEBUG] Wykryto katalog titan_data: {titan_data_dir}")
            play_sound_installer("STARTUP")
            config_dlg = TitanConfigDialog(None)
            result = config_dlg.ShowModal()
            config_dlg.Destroy()

            if result == TitanConfigDialog.RESULT_LAUNCH:
                # Uruchom Titana
                titan_exe = BASE_CONFIG["MAIN_APP_EXE_PATH_FOR_SHORTCUT"]
                print(f"[APP DEBUG] Użytkownik wybrał uruchomienie Titana: {titan_exe}")
                if os.path.isfile(titan_exe):
                    try: subprocess.Popen([titan_exe])
                    except Exception as e: wx.MessageBox(t('error_launch_titan_short').format(e), t('error_title'), wx.OK | wx.ICON_ERROR)
                else:
                    wx.MessageBox(t('error_file_not_found').format(titan_exe), t('error_title'), wx.OK | wx.ICON_ERROR)
                return False
            elif result == TitanConfigDialog.RESULT_UPDATE:
                # Zaktualizuj Titana - usuń titan_data i kontynuuj instalację
                print(f"[APP DEBUG] Użytkownik wybrał aktualizację. Usuwanie: {titan_data_dir}")
                try:
                    shutil.rmtree(titan_data_dir, ignore_errors=True)
                    print("[APP DEBUG] Katalog titan_data usunięty.")
                except Exception as e_rm:
                    print(f"[APP DEBUG][BŁĄD] Usuwanie titan_data: {e_rm}")
                # Kontynuuj do instalatora (poniżej)
            elif result == TitanConfigDialog.RESULT_MANAGE_TCE:
                # Zarządzaj integracją pakietów TCE
                print("[APP DEBUG] Użytkownik wybrał zarządzanie integracją TCE.")
                tce_manage_dlg = TCEIntegrationDialog(None)
                tce_result = tce_manage_dlg.ShowModal()
                tce_manage_dlg.Destroy()
                return False  # Zakończ aplikację po zarządzaniu integracją
            else:
                # Anulowano
                print("[APP DEBUG] Użytkownik anulował dialog konfiguracji.")
                return False

        print("[INSTALLER_APP DEBUG] Uruchamianie instalatora GUI.")
        play_sound_installer("STARTUP"); print("[INSTALLER_APP DEBUG] Dźwięk startowy.")
        self.start_frame_instance = StartFrame(None, t('start_frame_title'))
        self.timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.DoShowStartFrame, self.timer)
        self.timer.Start(4000, wx.TIMER_ONE_SHOT); print("[INSTALLER_APP DEBUG] Timer uruchomiony.")
        return True

    def DoShowStartFrame(self, event):
        print("[APP DEBUG] TitanInstallerApp.DoShowStartFrame - Timer zadziałał.")
        if self.timer: self.timer.Stop(); self.timer = None
        if self.start_frame_instance:
            if hasattr(self.start_frame_instance, 'IsBeingDeleted') and self.start_frame_instance.IsBeingDeleted(): print("[APP DEBUG][OSTRZEŻENIE] StartFrame w trakcie usuwania."); return
            if not self.start_frame_instance.IsShown(): self.start_frame_instance.Show(); print("[APP DEBUG] StartFrame.Show() wywołane.")
            else: print("[APP DEBUG] StartFrame już był widoczny.")
        else: print("[APP DEBUG][BŁĄD] self.start_frame_instance nie istnieje!")
    
    def OnExit(self):
        print("[APP DEBUG] TitanInstallerApp.OnExit")
        if self.timer: self.timer.Stop(); self.timer = None
        if pygame and pygame.mixer.get_init(): pygame.mixer.quit(); print("[INSTALLER_APP DEBUG] Pygame mixer zamknięty.")
        return 0

# --- Główna funkcja uruchamiająca ten moduł ---
def run_main_installer(base_paths_config_from_launcher):
    global BASE_CONFIG, SFX_PATHS # Ustaw globalne dla tego modułu
    BASE_CONFIG = base_paths_config_from_launcher
    SFX_PATHS = {
        "STARTUP": os.path.join(BASE_CONFIG["SFX_DIR"], "startup.ogg"),
        "DLGOPEN": os.path.join(BASE_CONFIG["SFX_DIR"], "dlgopen.ogg"),
        "DLGCLOSE": os.path.join(BASE_CONFIG["SFX_DIR"], "dlgclose.ogg"),
        "INSTALLING": os.path.join(BASE_CONFIG["SFX_DIR"], "installingapps.ogg"),
        "FOCUS": os.path.join(BASE_CONFIG["SFX_DIR"], "focus.ogg"),
        "CONFIGURATION": os.path.join(BASE_CONFIG["SFX_DIR"], "success.ogg"),
    }
    print("[INSTALLER_MODULE] Uruchamianie głównego instalatora...")
    app = TitanInstallerApp(False, base_paths_config_from_launcher)
    app.MainLoop()
    print("[INSTALLER_MODULE] Główny instalator zakończył działanie.")

print("[DIAG] Moduł installer.py został wczytany.")