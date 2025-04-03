import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGridLayout, QGraphicsRectItem
import pyqtgraph as pg
from PyQt5 import QtCore
from pyqtgraph import PlotWidget, mkPen, mkBrush, QtGui
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtCore import QTimer, QPropertyAnimation
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ultralytics import YOLO




class TimeSeriesPlot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.model = YOLO('./Last 200.pt')

        self.setWindowTitle("Arrhythmia Classification pyqt")
        self.setGeometry(100, 100, 900, 500)
        self.data = list(pd.read_excel('test.xlsx')["ecg"])
        self.index = 0
        self.interval1 = 8
        self.interval2 = 3000
        self.capture_len = 750

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 그래프 위젯 설정
        layout = QGridLayout()
        central_widget.setLayout(layout)
        
        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 1)
        layout.setRowStretch(2, 1)
        layout.setRowStretch(3, 1)
        layout.setRowStretch(4, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(4, 1)
        
        self.graph1 = PlotWidget()
        self.setup_graph(self.graph1, "Real-Time ECG")
        layout.addWidget(self.graph1, 0, 0, 1, 5)
        
        self.graph2 = PlotWidget()
        self.setup_graph(self.graph2, "t-SNE")
        layout.addWidget(self.graph2, 1, 0, 4, 3)

        self.graph3 = PlotWidget()
        self.setup_graph(self.graph3, "Captured ECG")
        layout.addWidget(self.graph3, 1, 3, 2, 2)

        self.graph4 = PlotWidget()
        self.setup_graph(self.graph4, "Detected Arrhythmia")
        layout.addWidget(self.graph4, 3, 3, 2, 2)

        # 데이터 초기화
        self.x = list(range(5000))  # 100개의 x축 데이터 (시간)
        self.y = [500] * len(self.x)  # 초기값 0으로 설정

        # 선 그리기
        self.pen = mkPen(color="k", width=2)
        self.main_data_line = self.graph1.plot(self.x, self.y, pen=self.pen, name="Signal")
        self.captured_data_line = self.graph3.plot(range(self.capture_len), [500] * self.capture_len, pen=self.pen, name="Captured Signal")

        self.timer1 = QTimer()
        self.timer1.setInterval(self.interval1)
        self.timer1.timeout.connect(self.update_data)
        self.timer1.start()

        self.timer2 = QTimer()
        self.timer2.setInterval(self.interval2)
        self.timer2.timeout.connect(self.capture_data)
        self.timer2.start()

        self.roi_rect = QGraphicsRectItem(len(self.x)-self.capture_len, 0, self.capture_len, 1000)
        self.roi_rect.setBrush(QtGui.QBrush(QtGui.QColor(128, 128, 128, 128)))
        self.roi_rect.setPen(pg.mkPen(None))
        self.graph1.addItem(self.roi_rect)
        
    def setup_graph(self, graph, title):
        graph.setBackground("w")
        graph.setTitle(title, color="k", size="12pt")
        graph.setYRange(0, 1000, padding=0)  # Y축 고정
        graph.setMouseEnabled(x=False, y=False)  # 줌 & 스크롤 비활성화
        graph.getAxis("bottom").setStyle(showValues=False)
        graph.getAxis("left").setStyle(showValues=False)
        graph.getAxis("bottom").setTicks([])
        graph.getAxis("left").setTicks([])
        graph.getPlotItem().hideButtons()

    def capture_data(self):
        self.start_roi_animation()
        captured_data_y = self.y[len(self.x) - self.capture_len:len(self.x)]
        self.captured_data_line.setData(range(len(captured_data_y)), captured_data_y)
        self.data_to_img = self.preprocessing_captured_ecg_data(captured_data_y)
        self.predict_result = self.model.predict(self.data_to_img, verbose=False, iou=0.4, conf=0.3, imgsz=320)[0].boxes
        boxes = []
        roi_boxes = []

        for cls, conf, loc in zip(self.predict_result.cls, self.predict_result.conf, self.predict_result.xyxy):
            data = {
                "cls" : int(cls.item()),
                "conf" : conf.item(),
                "loc" : loc.tolist()
            }
            boxes.append(data)

        # for data in boxes:


        print(boxes)
        
            
        # print(self.predict_result)

    def preprocessing_captured_ecg_data(self, data:list[int]):
        fig, ax = plt.subplots(figsize=(3.2, 3.2), dpi=100)

        ax.plot(data, color='black')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_axis_off()
        ax.set_xlim(0, len(data))
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        fig.canvas.draw()
        img_array = np.array(fig.canvas.renderer.buffer_rgba())  # (H, W, 4) RGBA 배열
        plt.close(fig)
        

        return img_array[:, :, :3] # RGB 배열 리턴

    def start_roi_animation(self):
        self.animation = QPropertyAnimation(self, b"roiColor")
        self.animation.setDuration(2000)
        self.animation.setStartValue(QColor(255, 255, 255, 255))
        self.animation.setEndValue(QColor(128, 128, 128, 128))
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.animation.valueChanged.connect(self.update_roi_color)
        self.animation.start()

    def update_roi_color(self, color):
        self.roi_rect.setBrush(QBrush(color))

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def update_data(self):
        """실시간 데이터 갱신"""
        try:
            new_value = self.data[self.index]
            self.index += 1
        except:
            new_value = 500
        self.y = self.y[1:] + [new_value]  # 데이터 이동
        self.main_data_line.setData(self.x, self.y)  # 그래프 업데이트

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeSeriesPlot()
    window.show()
    sys.exit(app.exec_())
