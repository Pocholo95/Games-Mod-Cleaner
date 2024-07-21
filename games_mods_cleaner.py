import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import json
from pathlib import Path
import winreg

# Constants
BACKUP_DIR = 'backups'

def is_dark_mode():
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize')
        value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
        return value == 0
    except (FileNotFoundError, OSError):
        return False

def get_system_language():
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(registry, r'SYSTEM\CurrentControlSet\Control\Nls\Language')
        value, _ = winreg.QueryValueEx(key, 'Default')
        return value
    except (FileNotFoundError, OSError):
        return '0409'  # Default to English (US)

def remove_directory(directory):
    """Remove a directory and its contents."""
    shutil.rmtree(directory, ignore_errors=False, onerror=None)
    print(f"Successfully removed directory: {directory}")

def create_backup(path):
    path = str(Path(path).resolve())
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), BACKUP_DIR)
    os.makedirs(backup_dir, exist_ok=True)
    backup_file_path = os.path.join(backup_dir, f'{os.path.basename(path)}_Backup.json')
    with open(backup_file_path, 'w') as f:
        json.dump(get_file_tree(path), f)

def restore_vanilla(path):
    path = str(Path(path).resolve())
    backup_file_path = os.path.join(BACKUP_DIR, f'{os.path.basename(path)}_Backup.json')

    if not os.path.exists(backup_file_path):
        messagebox.showerror('Error', 'No se encontró el archivo de copia de seguridad para esta ruta')
        return

    with open(backup_file_path, 'r') as f:
        backup_data = json.load(f)
    
    current_files = set()
    current_dirs = set()
    
    for root, dirs, files in os.walk(path):
        rel_root = Path(root).relative_to(Path(path))
        current_dirs.update({str(rel_root / dir_name) for dir_name in dirs})
        current_files.update({str(rel_root / file_name) for file_name in files})

    missing_files = [file for file in backup_data['files'] if file not in current_files]
    new_files = [file for file in current_files if file not in backup_data['files']]
    missing_folders = [folder for folder in backup_data['folders'] if folder not in current_dirs]
    new_folders = [folder for folder in current_dirs if folder not in backup_data['folders']]
    
    if not missing_files and not missing_folders:
        if not new_files and not new_folders:
            messagebox.showinfo("Sin Cambios", "No hay cambios en la lista de archivos.")
        elif new_files:
            if messagebox.askyesno("Archivos No Listados", f"Encontró {len(new_files)} archivos no listados. ¿Eliminar estos archivos?"):
                for file in new_files:
                    try:
                        os.remove(os.path.join(path, file))
                    except OSError as e:
                        print(f"Error al eliminar el archivo {file}: {e}")

    if missing_files:
        messagebox.showwarning("Archivos Faltantes", "Faltan los siguientes archivos:\n" + "\n".join(missing_files))
    
    if new_folders:
        if messagebox.askyesno("Nuevas Carpetas", f"Encontró {len(new_folders)} nuevas carpetas. ¿Eliminar estas carpetas?"):
            for folder in new_folders:
                remove_directory(os.path.join(path, folder))

def get_file_tree(path):
    result = {'folders': [], 'files': []}
    for root, dirs, files in os.walk(path):
        rel_path = Path(root).relative_to(Path(path))
        result['folders'].extend({str(rel_path / dir_name) for dir_name in dirs if not str(rel_path / dir_name).startswith('.')})
        result['files'].extend({str(rel_path / file_name) for file_name in files if not str(rel_path / file_name).startswith('.')})
    return result

class BackupMaker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Games Mod Cleaner")

        # Define window dimensions
        self.window_width = 500
        self.window_height = 250
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate x, y position to center the window
        x = (screen_width // 2) - (self.window_width // 2)
        y = (screen_height // 2) - (self.window_height // 2)

        # Set the window size and position
        self.root.geometry(f'{self.window_width}x{self.window_height}+{x}+{y}')
        self.root.resizable(False, False)

        self.is_dark = is_dark_mode()
        self.language = get_system_language()
        self.configure_theme()
        self.configure_texts()

        self.path_entry = tk.Entry(self.root, width=60, bd=0, relief=tk.FLAT, bg=self.entry_bg, fg=self.entry_fg, font=('Arial', 14))
        self.path_entry.pack(pady=20, padx=20)
        
        # Add placeholder text
        self.path_entry.insert(0, self.placeholder_text)
        self.path_entry.bind("<FocusIn>", self.on_entry_click)
        self.path_entry.bind("<FocusOut>", self.on_focus_out)

        self.make_backup_button = tk.Button(self.root, text=self.texts["create_backup"], command=self.create_backup_clicked, bg=self.button_bg, fg=self.button_fg, bd=0, relief=tk.FLAT, font=('Arial', 12))
        self.make_backup_button.pack(pady=10, padx=20, fill=tk.X)

        self.restore_button = tk.Button(self.root, text=self.texts["restore_backup"], command=self.restore_clicked, bg=self.button_bg, fg=self.button_fg, bd=0, relief=tk.FLAT, font=('Arial', 12))
        self.restore_button.pack(pady=10, padx=20, fill=tk.X)
    
    def on_entry_click(self, event):
        """Clear the placeholder text when the entry is clicked."""
        if self.path_entry.get() == self.placeholder_text:
            self.path_entry.delete(0, tk.END)
            self.path_entry.config(fg=self.entry_fg)

    def on_focus_out(self, event):
        """Restore the placeholder text if the entry is empty."""
        if self.path_entry.get() == "":
            self.path_entry.insert(0, self.placeholder_text)
            self.path_entry.config(fg='grey')

    def configure_theme(self):
        if self.is_dark:
            self.root.configure(bg="#333333")
            self.entry_bg = "#555555"
            self.entry_fg = "#ffffff"
            self.button_bg = "#777777"
            self.button_fg = "#ffffff"
        else:
            self.root.configure(bg="#f0f0f0")
            self.entry_bg = "#e0e0e0"
            self.entry_fg = "#333333"
            self.button_bg = "#cccccc"
            self.button_fg = "#333333"

    def configure_texts(self):
        if self.language == '0409':  # English (US)
            self.texts = {
                "create_backup": "List Files",
                "restore_backup": "Delate Mods",
                "error_path": "Path does not exist.",
                "backup_created": "The list file has been created in the backups folder.",
                "error_no_backup": "No list file found for this path",
                "no_changes": "There are no changes to the list of files.",
                "unlisted_files": "Found {} unlisted files. Delete them?",
                "missing_files": "The following files are missing:\n",
                "new_folders": "The following new folders were created:\n",
                "delete_folders": "Found {} new folders. Delete them?",
                "placeholder": "Enter path here"  # Placeholder text for English
            }
        else:  # Default to Spanish
            self.texts = {
                "create_backup": "Crear Lista",
                "restore_backup": "Borrar Mods",
                "error_path": "El path no existe.",
                "backup_created": "El archivo de copia de seguridad ha sido creado en la carpeta de backups.",
                "error_no_backup": "No se encontró archivo de lista seguridad para este path",
                "no_changes": "No hay cambios en la lista de archivos.",
                "unlisted_files": "Encontró {} archivos no listados. ¿Quieres borrarlos?",
                "missing_files": "Los siguientes archivos faltan:\n",
                "new_folders": "Las siguientes nuevas carpetas fueron creadas:\n",
                "delete_folders": "Encontró {} nuevas carpetas. ¿Quieres borrarlas?",
                "placeholder": "Ingrese el path aquí"  # Placeholder text for Spanish
            }
        self.placeholder_text = self.texts["placeholder"]

    def create_backup_clicked(self):
        path = self.path_entry.get().strip()
        if not os.path.exists(path):
            messagebox.showerror("Error", self.texts["error_path"])
            return
        create_backup(path)
        messagebox.showinfo("Backup Created", self.texts["backup_created"])

    def restore_clicked(self):
        path = self.path_entry.get().strip()
        if not os.path.exists(path):
            messagebox.showerror("Error", self.texts["error_path"])
            return
        restore_vanilla(path)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = BackupMaker()
    app.run()
