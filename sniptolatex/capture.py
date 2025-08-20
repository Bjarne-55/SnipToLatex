from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtCore import QPoint, QRect, Qt, QBuffer, QByteArray, QIODevice
from PyQt5.QtGui import QGuiApplication, QPixmap, QPainter

from .ai import GeminiRequest

def capture_and_copy(capture_rect: QRect) -> None:
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

        print("Sending to Gemini")
        gemini = GeminiRequest()
        executor = ThreadPoolExecutor()
        future = executor.submit(gemini.send_image, cropped_png)
        future.add_done_callback(copy_response)

def copy_response(future) -> None:
    result = future.result()
    print(f"Model result: {result}")
    QGuiApplication.clipboard().setText(result)

def get_virtual_geometry() -> QRect:
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return QRect(0, 0, 0, 0)
    return screen.virtualGeometry()

def grab_full_desktop_pixmap() -> Optional[QPixmap]:
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return None

    virtual_rect = screen.virtualGeometry()
    if virtual_rect.isNull() or virtual_rect.isEmpty():
        return None

    composed = QPixmap(virtual_rect.size())
    composed.fill(Qt.transparent)

    with QPainter(composed) as painter:
        for s in screen.virtualSiblings():
            spix = s.grabWindow(0)
            if spix.isNull():
                continue
            top_left = s.geometry().topLeft() - virtual_rect.topLeft()
            painter.drawPixmap(top_left, spix)

    return composed

def pixmap_to_png_bytes(pixmap: QPixmap) -> Optional[bytes]:
    buffer_array = QByteArray()
    buffer = QBuffer(buffer_array)
    if not buffer.open(QIODevice.WriteOnly):
        return None
    ok = pixmap.save(buffer, 'PNG')
    buffer.close()
    if not ok:
        return None
    return bytes(buffer_array)


