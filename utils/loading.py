from PySide6.QtWidgets import QProgressDialog
from PySide6.QtCore import QThread, Signal, Qt


class LoadingWorker(QThread):
    """Background worker for async operations"""
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


def show_loading(parent, message="Loading..."):
    """
    Create a loading dialog
    
    Args:
        parent: Parent widget
        message: Loading message to display
        
    Returns:
        QProgressDialog: The loading dialog
    """
    dialog = QProgressDialog(message, None, 0, 0, parent)
    dialog.setWindowModality(Qt.WindowModal)
    dialog.setWindowTitle("Please Wait")
    dialog.setMinimumDuration(0)
    dialog.setCancelButton(None)
    dialog.setStyleSheet("""
        QProgressDialog {
            background: white;
            border-radius: 8px;
        }
        QLabel {
            color: #1e293b;
            font-size: 14px;
            padding: 20px;
        }
    """)
    return dialog