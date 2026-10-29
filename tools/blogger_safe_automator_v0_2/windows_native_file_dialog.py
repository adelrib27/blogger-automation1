#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from pathlib import Path


class NativeFileDialogError(RuntimeError):
    pass


if os.name == "nt":
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    WM_SETTEXT = 0x000C
    BM_CLICK = 0x00F5

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.EnumChildWindows.argtypes = [wintypes.HWND, EnumWindowsProc, wintypes.LPARAM]
    user32.EnumChildWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.IsWindowEnabled.argtypes = [wintypes.HWND]
    user32.IsWindowEnabled.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LRESULT
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.SetFocus.argtypes = [wintypes.HWND]
    user32.SetFocus.restype = wintypes.HWND
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL


def _require_windows() -> None:
    if os.name != "nt":
        raise NativeFileDialogError("Automação da caixa de arquivo nativa requer Windows.")


def _text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(max(length + 1, 512))
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value.strip()


def _class(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, len(buf))
    return buf.value


def _rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return (0, 0, 0, 0)
    return (rect.left, rect.top, rect.right, rect.bottom)


def _children(hwnd: int) -> list[int]:
    result: list[int] = []

    @EnumWindowsProc
    def callback(child, _lparam):
        result.append(int(child))
        return True

    if not user32.EnumChildWindows(hwnd, callback, 0):
        err = ctypes.get_last_error()
        if err:
            raise NativeFileDialogError(f"EnumChildWindows falhou: WinError {err}.")
    return result


def _top_level_windows() -> list[int]:
    result: list[int] = []

    @EnumWindowsProc
    def callback(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            result.append(int(hwnd))
        return True

    if not user32.EnumWindows(callback, 0):
        err = ctypes.get_last_error()
        raise NativeFileDialogError(f"EnumWindows falhou: WinError {err}.")
    return result


def _norm(value: str) -> str:
    return " ".join((value or "").strip().casefold().split())


def _button_matches(text: str, names: tuple[str, ...]) -> bool:
    return _norm(text) in {_norm(name) for name in names}


def _dialog_candidates() -> list[dict]:
    candidates = []
    for hwnd in _top_level_windows():
        if _class(hwnd) != "#32770":
            continue
        children = _children(hwnd)
        buttons = [
            child
            for child in children
            if _class(child) == "Button" and user32.IsWindowVisible(child)
        ]
        open_buttons = [
            child for child in buttons if _button_matches(_text(child), ("Abrir", "Open"))
        ]
        cancel_buttons = [
            child for child in buttons if _button_matches(_text(child), ("Cancelar", "Cancel"))
        ]
        if len(open_buttons) == 1 and len(cancel_buttons) == 1:
            candidates.append(
                {
                    "hwnd": hwnd,
                    "title": _text(hwnd),
                    "children": children,
                    "open_button": open_buttons[0],
                    "cancel_button": cancel_buttons[0],
                }
            )
    return candidates


def _select_filename_edit(dialog: dict) -> int:
    edits = [
        child
        for child in dialog["children"]
        if _class(child) == "Edit"
        and user32.IsWindowVisible(child)
        and user32.IsWindowEnabled(child)
    ]
    if not edits:
        raise NativeFileDialogError("Nenhum campo Edit visível foi encontrado na janela Abrir.")
    if len(edits) == 1:
        return edits[0]

    # Common Windows dialogs can expose more than one Edit (for example address/search).
    # The filename field is normally the lowest visible edit in the dialog.
    ranked = sorted(edits, key=lambda hwnd: (_rect(hwnd)[3], _rect(hwnd)[2] - _rect(hwnd)[0]), reverse=True)
    best = ranked[0]
    if len(ranked) > 1:
        best_rect = _rect(best)
        second_rect = _rect(ranked[1])
        # Fail closed when geometry is too similar to distinguish safely.
        if abs(best_rect[3] - second_rect[3]) < 8:
            details = [{"text": _text(h), "rect": _rect(h)} for h in ranked]
            raise NativeFileDialogError(f"Campos Edit ambíguos na janela Abrir: {details}")
    return best


def wait_for_open_dialog(timeout_seconds: float = 8.0) -> dict:
    _require_windows()
    deadline = time.monotonic() + timeout_seconds
    last_count = 0
    while time.monotonic() < deadline:
        candidates = _dialog_candidates()
        last_count = len(candidates)
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            raise NativeFileDialogError(
                f"Mais de uma janela nativa Abrir foi encontrada ({len(candidates)}); operação bloqueada."
            )
        time.sleep(0.15)
    raise NativeFileDialogError(
        f"Janela nativa Abrir não apareceu no prazo esperado (candidatos finais={last_count})."
    )


def choose_file_and_open(file_path: str, *, timeout_seconds: float = 8.0) -> dict:
    _require_windows()
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise NativeFileDialogError(f"Arquivo não encontrado: {path}")
    if path.name.lower() != "theme.xml":
        raise NativeFileDialogError("Por segurança, a seleção nativa aceita somente um arquivo chamado theme.xml.")

    dialog = wait_for_open_dialog(timeout_seconds=timeout_seconds)
    edit = _select_filename_edit(dialog)
    open_button = dialog["open_button"]

    user32.SetForegroundWindow(dialog["hwnd"])
    user32.SetFocus(edit)
    user32.SendMessageW(edit, WM_SETTEXT, 0, ctypes.cast(ctypes.c_wchar_p(str(path)), ctypes.c_void_p).value)
    time.sleep(0.2)

    observed = _text(edit)
    if os.path.normcase(os.path.normpath(observed)) != os.path.normcase(os.path.normpath(str(path))):
        raise NativeFileDialogError(
            f"O campo do arquivo não confirmou o caminho esperado. observado={observed!r} esperado={str(path)!r}"
        )

    user32.SendMessageW(open_button, BM_CLICK, 0, 0)

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not user32.IsWindow(dialog["hwnd"]):
            return {
                "native_dialog_title": dialog["title"],
                "selected_path": str(path),
                "open_clicked": True,
                "dialog_closed": True,
            }
        time.sleep(0.15)

    raise NativeFileDialogError("O botão Abrir foi acionado, mas a janela nativa permaneceu aberta.")
