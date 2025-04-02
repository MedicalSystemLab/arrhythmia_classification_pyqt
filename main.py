import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGridLayout, QGraphicsRectItem
import pyqtgraph as pg
from pyqtgraph import PlotWidget, mkPen, mkBrush, QtGui
from PyQt5.QtCore import QTimer
import pandas as pd

class TimeSeriesPlot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("실시간 시계열 데이터")
        self.setGeometry(100, 100, 800, 500)
        self.data = list(pd.read_excel('test.xlsx')["ecg"])
        self.index = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 그래프 위젯 설정
        layout = QGridLayout()
        central_widget.setLayout(layout)
        
        
        self.graph1 = PlotWidget()
        self.setup_graph(self.graph1, "그래프 1 (병합)")
        layout.addWidget(self.graph1, 0, 0, 1, 2)

        self.graph1.addItem(self.roi)
        roi_rect = QGraphicsRectItem(0, 0, 60, 1000)  # ROI 크기와 맞춤
        roi_rect.setBrush(QtGui.QBrush(QtGui.QColor(128, 128, 128, 128)))  # 회색, 50% 투명도
        roi_rect.setPen(pg.mkPen(None))  # 테두리 없음
        self.roi.addItem(roi_rect)  # ROI 내부에 추가

        self.graph2 = PlotWidget()
        self.setup_graph(self.graph2, "그래프 2")
        layout.addWidget(self.graph2, 1, 0)

        self.graph3 = PlotWidget()
        self.setup_graph(self.graph3, "그래프 3")
        layout.addWidget(self.graph3, 2, 0)
        # 데이터 초기화
        self.x = list(range(1000))  # 100개의 x축 데이터 (시간)
        self.y = [500] * 1000  # 초기값 0으로 설정

        # 선 그리기
        self.pen = mkPen(color="b", width=2)
        self.data_line = self.graph1.plot(self.x, self.y, pen=self.pen, name="Signal")
        
        # 타이머 설정 (50ms마다 update_data 호출)
        self.timer = QTimer()
        self.timer.setInterval(8)
        self.timer.timeout.connect(self.update_data)
        self.timer.start()
        
    def setup_graph(self, graph, title):
        """그래프 스타일 설정"""
        graph.setBackground("w")
        graph.setTitle(title, color="k", size="12pt")
        graph.setYRange(0, 1000, padding=0)  # Y축 고정
        graph.setMouseEnabled(x=False, y=False)  # 줌 & 스크롤 비활성화
        graph.getAxis("bottom").setStyle(showValues=False)
        graph.getAxis("left").setStyle(showValues=False)
        graph.getAxis("bottom").setTicks([])
        graph.getAxis("left").setTicks([])

    def update_data(self):
        """실시간 데이터 갱신"""
        try:
            new_value = self.data[self.index]
            self.index += 1
        except:
            new_calue = 0
        self.y = self.y[1:] + [new_value]  # 데이터 이동
        self.data_line.setData(self.x, self.y)  # 그래프 업데이트

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeSeriesPlot()
    window.show()
    sys.exit(app.exec_())
