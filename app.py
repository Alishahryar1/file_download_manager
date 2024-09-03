import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QGridLayout, QHBoxLayout, QDialog, QLabel, QLineEdit, QDialogButtonBox, QCheckBox
import threading
import requests
import os
import uuid




class URLInputDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Add Download')
        self.setGeometry(100, 100, 300, 100)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.url_label = QLabel('Enter URL:')
        self.url_input = QLineEdit()

        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def getURL(self):
        return self.url_input.text()
    



class TopBarLayout(QHBoxLayout):

    def __init__(self):
        super().__init__()
        delete_button = QPushButton('Delete')
        self.addWidget(delete_button)
        delete_button.released.connect(self.deleteChecked)
        
        pause_button = QPushButton('Pause')
        self.addWidget(pause_button)
        pause_button.released.connect(self.pauseChecked)

        resume_button = QPushButton('Resume')
        self.addWidget(resume_button)
        resume_button.released.connect(self.resumeChecked)

        delete_all_button = QPushButton('Delete All')
        self.addWidget(delete_all_button)
        delete_all_button.released.connect(self.deleteAll)

    def deleteChecked(self):
        download_layout = self.parent().itemAtPosition(1, 1).layout()
        table = download_layout.itemAt(0).widget()
        i = 0
        while i < table.rowCount():
            cell_widget = table.cellWidget(i, 6)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    table.removeRow(i)
                    continue
            i += 1
    
    def pauseChecked(self):
        download_layout = self.parent().itemAtPosition(1, 1).layout()
        table = download_layout.itemAt(0).widget()
        i = 0
        while i < table.rowCount():
            cell_widget = table.cellWidget(i, 6)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    self.pauseDownload(i)
            i += 1
    
    def resumeChecked(self):
        download_layout = self.parent().itemAtPosition(1, 1).layout()
        table = download_layout.itemAt(0).widget()
        i = 0
        while i < table.rowCount():
            cell_widget = table.cellWidget(i, 6)
            if cell_widget:
                checkbox = cell_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    self.resumeDownload(i)
            i += 1

    def deleteAll(self):
        download_layout = self.parent().itemAtPosition(1, 1).layout()
        table = download_layout.itemAt(0).widget()
        table.setRowCount(0)

    def resumeDownload(self, row_position):
        pass

    def pauseDownload(self, row_position):
        pass




class SideBarLayout(QVBoxLayout):
    
    def __init__(self):
        super().__init__()
        self.downloads_button = QPushButton('Downloads')
        self.addWidget(self.downloads_button)
        self.addStretch()

        self.downloads_button.released.connect(self.showDownloads)

    def showDownloads(self):
        self.show()




class DownloadLayout(QVBoxLayout):

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        
        self.table = QTableWidget()
        column_headers = ['URL', 'Size (MB)', 'Status', 'Completed (%)', 'Time left', 'Transfer rate', 'Select']
        self.table.setColumnCount(len(column_headers))
        self.table.setHorizontalHeaderLabels(column_headers)
        self.table.verticalHeader().setVisible(False)

        add_button = QPushButton('Add download')
        add_button.released.connect(self.addDownload)

        self.addWidget(self.table)
        self.addWidget(add_button)
    
    def addDownload(self):
        dialog = URLInputDialog()
        if dialog.exec() == QDialog.Accepted:
            url = dialog.getURL()
        if not url:
            return
        
        response = requests.get(url, stream=True)
        size = response.headers.get('content-length')
        size = round(int(size)/1024**2, 1)
        
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        url = QTableWidgetItem(url)
        size = QTableWidgetItem(str(size))
        status = QTableWidgetItem('Status')
        completed = QTableWidgetItem('Completed (%)')
        time_left = QTableWidgetItem('Time left')
        transfer_rate = QTableWidgetItem('Transfer rate')

        self.table.setItem(row_position, 0, url)
        self.table.setItem(row_position, 1, size)
        self.table.setItem(row_position, 2, status)
        self.table.setItem(row_position, 3, completed)
        self.table.setItem(row_position, 4, time_left)
        self.table.setItem(row_position, 5, transfer_rate)

        checkbox = QCheckBox()
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row_position, 6, checkbox_widget)

        self.startDownload(url.text(), row_position)

    def startDownload(self, url, row_position):
        thread = threading.Thread(target=self.downloadFile, args=(url, row_position))
        thread.start()

    def downloadFile(self, url, row_position):
        response = requests.get(url, stream=True, allow_redirects=True, timeout=10)
        size = response.headers.get('content-length')
        size = int(size)
        downloaded = 0
        temp_filename = uuid.uuid4().hex
        filename = os.path.basename(url)
        with self.lock:
            with open(temp_filename, 'wb') as file:
                for data in response.iter_content(chunk_size=1024):
                    downloaded += len(data)
                    file.write(data)
                    self.updateProgress(row_position, downloaded, size)
        os.rename(temp_filename, filename)

    def updateProgress(self, row_position, downloaded, size):
        completed = round(downloaded/size * 100, 2)
        time_left = 'Time left'
        transfer_rate = 'Transfer rate'

        self.table.item(row_position, 3).setText(str(completed))
        self.table.item(row_position, 4).setText(str(time_left))
        self.table.item(row_position, 5).setText(str(transfer_rate))




class MainWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()
        self.setWindowTitle('Internet Download Manager')
        self.showMaximized()

        self.main_layout = QGridLayout()

        self.top_bar_layout = TopBarLayout()
        self.download_layout = DownloadLayout()
        self.side_bar_layout = SideBarLayout()
        
        self.main_layout.addLayout(self.top_bar_layout, 0, 0)
        self.main_layout.addLayout(self.side_bar_layout, 1, 0)
        self.main_layout.addLayout(self.download_layout, 1, 1)

        self.setLayout(self.main_layout)
        

    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())