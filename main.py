from PySide6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    from utils.fonts import apply_font
    import utils.theme as T
    T.FONT = f"'{apply_font(app)}', 'Segoe UI', sans-serif"

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
