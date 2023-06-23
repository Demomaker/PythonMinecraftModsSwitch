import os
import json
import shutil
import time
import re

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class SwitchModsThread(QThread):
    switch_mods_finished = pyqtSignal()
    switch_mods_error = pyqtSignal(str)

    def __init__(self, mod_switcher_controller):
        super().__init__()
        self.mod_switcher_controller = mod_switcher_controller

    def run(self):
        # Add your mod switching logic here
        selected_minecraft_version = self.mod_switcher_controller.selected_minecraft_version
        selected_modding_environment = self.mod_switcher_controller.selected_modding_environment
        current_inactive_mods_folder = self.mod_switcher_controller.selected_inactive_mods_folder + "/" + selected_minecraft_version + "/" + selected_modding_environment

        try:
            # Clear the active mods folder
            self.mod_switcher_controller.clear_mods_folder(self.mod_switcher_controller.active_mods_folder)

            # Create Inactive Mods Folder if it doesn't exist
            self.mod_switcher_controller.create_inactive_mods_folder(self.mod_switcher_controller.selected_inactive_mods_folder, selected_minecraft_version, selected_modding_environment)

            # Copy the contents of the selected inactive mods folder to the active mods folder
            self.mod_switcher_controller.copy_mods(current_inactive_mods_folder, self.mod_switcher_controller.active_mods_folder)

            # Save app settings
            self.mod_switcher_controller.save_app_settings()

            # Show success message
            self.switch_mods_finished.emit()
        except Exception as e:
            # Handle the exception accordingly
            self.switch_mods_error.emit(str(e))

    def __del__(self):
        self.wait()

class ModSwitcherController(QWidget):
    def __init__(self):
        super().__init__()
        self.DEFAULT_ACTIVE_MODS_FOLDER = os.getenv("APPDATA") + "/.minecraft/mods"
        self.selected_minecraft_version = None
        self.selected_modding_environment = None
        self.selected_inactive_mods_folder = None
        self.active_mods_folder = None
        self.setup_ui()
        self.load_app_settings()
        self.refresh_ui()

    def setup_ui(self):
        self.setObjectName("root")
        self.resize(400, 300)
        layout = QVBoxLayout(self)

        label1 = QLabel("Minecraft Version:")
        layout.addWidget(label1)

        self.minecraft_version_combobox = QComboBox()
        self.minecraft_version_combobox.currentIndexChanged.connect(self.update_minecraft_version)
        layout.addWidget(self.minecraft_version_combobox)

        label2 = QLabel("Modding Environment:")
        layout.addWidget(label2)

        self.modding_environment_combobox = QComboBox()
        self.modding_environment_combobox.currentIndexChanged.connect(self.update_modding_environment)
        layout.addWidget(self.modding_environment_combobox)

        label3 = QLabel("Inactive Mods Folder:")
        layout.addWidget(label3)

        inactive_mods_folder_layout = QHBoxLayout()
        self.inactive_mods_folder_textfield = QLineEdit()
        self.inactive_mods_folder_textfield.setReadOnly(True)
        inactive_mods_folder_layout.addWidget(self.inactive_mods_folder_textfield)

        select_inactive_mods_folder_button = QPushButton("Select Folder")
        select_inactive_mods_folder_button.clicked.connect(self.select_inactive_mods_folder)
        inactive_mods_folder_layout.addWidget(select_inactive_mods_folder_button)

        layout.addLayout(inactive_mods_folder_layout)

        label4 = QLabel("Active Mods Folder:")
        layout.addWidget(label4)

        active_mods_folder_layout = QHBoxLayout()
        self.active_mods_folder_textfield = QLineEdit()
        self.active_mods_folder_textfield.setReadOnly(True)
        active_mods_folder_layout.addWidget(self.active_mods_folder_textfield)

        select_active_mods_folder_button = QPushButton("Select Folder")
        select_active_mods_folder_button.clicked.connect(self.select_active_mods_folder)
        active_mods_folder_layout.addWidget(select_active_mods_folder_button)

        layout.addLayout(active_mods_folder_layout)

        self.switch_mods_button = QPushButton("Switch Mods")
        self.switch_mods_button.clicked.connect(self.switch_mods)
        layout.addWidget(self.switch_mods_button)

        self.progress_indicator = QProgressBar()
        self.progress_indicator.setVisible(False)
        layout.addWidget(self.progress_indicator)

    def update_minecraft_version(self, index):
        self.selected_minecraft_version = self.minecraft_version_combobox.currentText()
        self.save_app_settings()

    def update_modding_environment(self, index):
        self.selected_modding_environment = self.modding_environment_combobox.currentText()
        self.save_app_settings()

    def switch_mods(self):
        if self.selected_inactive_mods_folder is None or self.active_mods_folder is None:
            self.show_alert("Error", "Please select inactive and active mods folders.")
            return

        self.progress_indicator.setVisible(True)
        self.switch_mods_button.setDisabled(True)

        switch_mods_thread = SwitchModsThread(self)
        switch_mods_thread.switch_mods_finished.connect(self.handle_switch_mods_finished)
        switch_mods_thread.switch_mods_error.connect(self.handle_switch_mods_error)
        switch_mods_thread.start()

    def handle_switch_mods_finished(self):
        self.save_app_settings()
        self.show_success_message("Success", "Mods switched successfully.")
        self.progress_indicator.setVisible(False)
        self.switch_mods_button.setDisabled(False)

    def handle_switch_mods_error(self, error_message):
        self.show_alert("Error", error_message)
        self.progress_indicator.setVisible(False)
        self.switch_mods_button.setDisabled(False)

    def create_inactive_mods_folder(self, inactive_mods_folder, minecraft_version, modding_environment):
        self.create_folder_if_not_exist(inactive_mods_folder)
        self.create_folder_if_not_exist(os.path.join(inactive_mods_folder, minecraft_version))
        self.create_folder_if_not_exist(os.path.join(inactive_mods_folder, minecraft_version, modding_environment))

    def create_folder_if_not_exist(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)

    def select_inactive_mods_folder(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Inactive Mods Folder")
        if selected_folder:
            self.selected_inactive_mods_folder = selected_folder
            self.inactive_mods_folder_textfield.setText(selected_folder)
            self.refresh_ui()
            self.save_app_settings()

    def select_active_mods_folder(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Active Mods Folder")
        if selected_folder:
            self.active_mods_folder = selected_folder
            self.active_mods_folder_textfield.setText(selected_folder)
            self.refresh_ui()
            self.save_app_settings()

    def refresh_ui(self):
        self.active_mods_folder_textfield.setText(self.active_mods_folder)
        self.inactive_mods_folder_textfield.setText(self.selected_inactive_mods_folder)
        self.populate_versions()
        self.populate_modding_environments()

        # Set the default index of the combo boxes based on saved values
        minecraft_version_index = self.minecraft_version_combobox.findText(self.selected_minecraft_version)
        if minecraft_version_index != -1:
            self.minecraft_version_combobox.setCurrentIndex(minecraft_version_index)

        modding_environment_index = self.modding_environment_combobox.findText(self.selected_modding_environment)
        if modding_environment_index != -1:
            self.modding_environment_combobox.setCurrentIndex(modding_environment_index)

    def clear_mods_folder(self, mods_folder):
        if os.path.exists(mods_folder):
            for root, _, files in os.walk(mods_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    os.remove(file_path)

    def copy_mods(self, source_folder, destination_folder):
        if os.path.exists(source_folder):
            for root, _, files in os.walk(source_folder):
                for file in files:
                    source_file_path = os.path.join(root, file)
                    destination_file_path = os.path.join(destination_folder, os.path.relpath(source_file_path, source_folder))
                    os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
                    shutil.copy2(source_file_path, destination_file_path)

    def save_app_settings(self):
        selected_minecraft_version = self.minecraft_version_combobox.currentText()
        selected_modding_environment = self.modding_environment_combobox.currentText()

        app_settings = {
            "inactive_mods_folder": self.selected_inactive_mods_folder,
            "active_mods_folder": self.active_mods_folder,
            "minecraft_version": selected_minecraft_version,
            "modding_environment": selected_modding_environment,
        }

        with open("app_settings.json", "w") as file:
            json.dump(app_settings, file)

    def load_app_settings(self):
        if os.path.exists("app_settings.json"):
            with open("app_settings.json", "r") as file:
                app_settings = json.load(file)
                self.selected_inactive_mods_folder = app_settings.get("inactive_mods_folder")
                self.active_mods_folder = app_settings.get("active_mods_folder")
                self.selected_minecraft_version = app_settings.get("minecraft_version")
                self.selected_modding_environment = app_settings.get("modding_environment")

        if not self.active_mods_folder or not os.path.exists(self.active_mods_folder):
            self.active_mods_folder = self.DEFAULT_ACTIVE_MODS_FOLDER

    def populate_versions(self):
        versions_folder = os.path.join(self.active_mods_folder, "..", "versions")
        if os.path.exists(versions_folder):
            versions = [
                folder
                for folder in os.listdir(versions_folder)
                if os.path.isdir(os.path.join(versions_folder, folder))
                   and re.match(r"\d+\.\d+(\.\d+)?", folder)
            ]
            self.minecraft_version_combobox.clear()
            self.minecraft_version_combobox.addItems(versions)

    def populate_modding_environments(self):
        self.modding_environment_combobox.clear()
        self.modding_environment_combobox.addItems(["Forge", "Fabric"])

    def show_alert(self, title, message):
        alert = QMessageBox()
        alert.setWindowTitle(title)
        alert.setText(message)
        alert.setIcon(QMessageBox.Critical)
        alert.exec_()

    def show_success_message(self, title, message):
        alert = QMessageBox()
        alert.setWindowTitle(title)
        alert.setText(message)
        alert.setIcon(QMessageBox.Information)
        alert.exec_()

    # Add methods for handling additional functionality, such as adding files to the inactive mods folder,
    # opening download links, etc.

if __name__ == '__main__':
    app = QApplication([])
    window = ModSwitcherController()
    window.show()
    app.exec_()