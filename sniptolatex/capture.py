"""Screen capture and clipboard helpers.

This module provides utilities to:
- Capture a stitched screenshot of all screens
- Crop to a user-selected rectangle
- Send the cropped image to a background AI request and copy the text result
"""

from typing import Optional
from concurrent.futures import ThreadPoolExecutor, Future

from PyQt5.QtCore import QPoint, QRect, Qt, QBuffer, QByteArray, QIODevice, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QGuiApplication, QPixmap, QPainter

from .ai import GeminiRequest
from .toast import Toast


class _ClipboardBridge(QObject):
    """Bridge to ensure clipboard writes happen on the Qt main thread.

    On Windows, the clipboard relies on COM which is initialized for the
    GUI thread. Emitting a signal from a worker thread to this object will
    schedule the slot on the main thread via a queued connection.
    """

    _copyRequested = pyqtSignal(str)
    _toastSuccessRequested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._copyRequested.connect(self._set_clipboard_text)
        self._toastSuccessRequested.connect(self._show_toast_success)

        # Lazily create UI elements only after QApplication exists
        self._toast = None

    def _ensure_toast(self) -> None:
        # Create toast only when a QApplication (QGuiApplication) exists
        if self._toast is None and QGuiApplication.instance() is not None:
            self._toast = Toast()

    def request_copy(self, text: str) -> None:
        self._copyRequested.emit(text)

    def show_loading(self) -> None:
        self._ensure_toast()
        if self._toast is not None:
            self._toast.show_loading()

    def request_toast_success(self) -> None:
        self._toastSuccessRequested.emit()

    @pyqtSlot(str)
    def _set_clipboard_text(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)

    def _show_toast_success(self) -> None:
        self._ensure_toast()
        if self._toast is not None:
            self._toast.show_success()


# Singleton living in the main thread (module imported on main thread)
_clipboard_bridge = _ClipboardBridge()

def capture_and_copy(capture_rect: QRect) -> None:
        """Capture a region and copy model output to the clipboard.

        Args:
            capture_rect (QRect): The selection rectangle relative to the
                virtual desktop origin (0,0 is the virtual top-left).
        """
        if capture_rect.width() <= 1 or capture_rect.height() <= 1:
            print("capture_rect is too small")
            return

        full = grab_full_desktop_pixmap()
        if full is None or full.isNull():
            print("full is None or full.isNull()")
            return

        bounded = capture_rect.intersected(QRect(QPoint(0, 0), full.size()))
        cropped = full.copy(bounded)
        cropped_png = pixmap_to_png_bytes(cropped)

        # Send to Gemini in background to avoid blocking the UI
        print("Sending to Gemini")
        _clipboard_bridge.show_loading()
        gemini = GeminiRequest()
        executor = ThreadPoolExecutor()
        future = executor.submit(gemini.send_image, cropped_png)
        future.add_done_callback(copy_response)

def copy_response(future: Future) -> None:
    """Copy the model result to the clipboard when the background task ends.

    Args:
        future (concurrent.futures.Future): The future representing the
            model request that returns the generated text.

    Raises:
        Exception: Propagates any exception raised by ``future.result()``
            if the background task failed.
    """
    # This callback runs in a worker thread. Do not touch GUI directly here.
    result = future.result()
    print(f"Model result: {result}")
    # Forward clipboard write to main thread to avoid CO_E_NOTINITIALIZED on Windows
    _clipboard_bridge.request_copy(result)
    # Show success toast on the main thread
    _clipboard_bridge.request_toast_success()

def get_virtual_geometry() -> QRect:
    """Return the union geometry across all monitors.

    Returns:
        QRect: The virtual desktop rectangle spanning all connected displays.
    """
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return QRect(0, 0, 0, 0)
    return screen.virtualGeometry()

def grab_full_desktop_pixmap() -> Optional[QPixmap]:
    """Capture all monitors and stitch into a single image.

    Returns:
        Optional[QPixmap]: The composed screenshot pixmap, or ``None`` if
        there is no primary screen or the virtual geometry is empty.
    """
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return None

    virtual_rect = screen.virtualGeometry()
    if virtual_rect.isNull() or virtual_rect.isEmpty():
        return None

    composed = QPixmap(virtual_rect.size())
    composed.fill(Qt.transparent)

    # Paint each screen's snapshot into the composed canvas at its offset
    with QPainter(composed) as painter:
        for s in screen.virtualSiblings():
            spix = s.grabWindow(0)
            if spix.isNull():
                continue
            top_left = s.geometry().topLeft() - virtual_rect.topLeft()
            painter.drawPixmap(top_left, spix)

    return composed

def pixmap_to_png_bytes(pixmap: QPixmap) -> Optional[bytes]:
    """Encode a QPixmap to PNG bytes.

    Args:
        pixmap (QPixmap): The image to encode.

    Returns:
        Optional[bytes]: PNG-encoded image data, or ``None`` if encoding
        fails or the buffer cannot be opened.
    """
    buffer_array = QByteArray()
    buffer = QBuffer(buffer_array)
    if not buffer.open(QIODevice.WriteOnly):
        return None
    ok = pixmap.save(buffer, 'PNG')
    buffer.close()
    if not ok:
        return None
    return bytes(buffer_array)


