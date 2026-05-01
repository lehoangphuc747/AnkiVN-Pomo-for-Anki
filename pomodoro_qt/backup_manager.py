"""UI-facing backup import/export orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from aqt.qt import QFileDialog, QMessageBox, QWidget

from .backup import BackupError, build_backup, read_backup, write_backup
from .i18n import tr
from .models import PomodoroSettings


class BackupManager:
    def __init__(
        self,
        get_settings: Callable[[], PomodoroSettings],
        get_state: Callable[[], dict],
        get_analytics: Callable[[], dict],
        save_runtime_state: Callable[[], None],
        apply_imported_backup: Callable[[PomodoroSettings, dict, dict], None],
    ) -> None:
        self._get_settings = get_settings
        self._get_state = get_state
        self._get_analytics = get_analytics
        self._save_runtime_state = save_runtime_state
        self._apply_imported_backup = apply_imported_backup

    def export_backup(self, parent: QWidget) -> None:
        self._save_runtime_state()
        file_path = _save_file_name(
            parent,
            tr("backup.export_title"),
            _default_backup_path(),
            tr("backup.file_filter"),
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path = f"{file_path}.json"
        try:
            payload = build_backup(self._get_settings(), self._get_state(), self._get_analytics())
            write_backup(file_path, payload)
        except Exception as exc:
            _show_warning(parent, tr("backup.export_error_title"), tr("backup.export_error", error=exc))
            return
        _show_info(parent, tr("backup.export_success_title"), tr("backup.export_success", path=file_path))

    def import_backup(self, parent: QWidget) -> bool:
        file_path = _open_file_name(parent, tr("backup.import_title"), "", tr("backup.file_filter"))
        if not file_path:
            return False
        try:
            imported_settings, imported_state, imported_analytics = read_backup(file_path)
        except BackupError as exc:
            _show_warning(parent, tr("backup.import_error_title"), tr("backup.import_error", error=tr(exc.key)))
            return False
        except Exception as exc:
            _show_warning(parent, tr("backup.import_error_title"), tr("backup.import_error", error=exc))
            return False
        if not _confirm_replace(parent):
            return False
        try:
            self._apply_imported_backup(imported_settings, imported_state, imported_analytics)
        except Exception as exc:
            _show_warning(parent, tr("backup.import_error_title"), tr("backup.import_error", error=exc))
            return False
        _show_info(parent, tr("backup.import_success_title"), tr("backup.import_success"))
        return True


def _default_backup_path() -> str:
    filename = datetime.now().strftime("pomodoro-backup-%Y%m%d-%H%M%S.json")
    return str(Path.home() / filename)


def _save_file_name(parent: QWidget, title: str, default_path: str, file_filter: str) -> str:
    result = QFileDialog.getSaveFileName(parent, title, default_path, file_filter)
    return _dialog_path(result)


def _open_file_name(parent: QWidget, title: str, default_path: str, file_filter: str) -> str:
    result = QFileDialog.getOpenFileName(parent, title, default_path, file_filter)
    return _dialog_path(result)


def _dialog_path(result) -> str:
    if isinstance(result, tuple):
        return str(result[0] or "")
    return str(result or "")


def _confirm_replace(parent: QWidget) -> bool:
    buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    result = QMessageBox.question(
        parent,
        tr("backup.confirm_replace_title"),
        tr("backup.confirm_replace"),
        buttons,
        QMessageBox.StandardButton.No,
    )
    return _enum_value(result) == _enum_value(QMessageBox.StandardButton.Yes)


def _show_info(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.information(parent, title, text)


def _show_warning(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.warning(parent, title, text)


def _enum_value(value) -> int:
    return int(value.value) if hasattr(value, "value") else int(value)
