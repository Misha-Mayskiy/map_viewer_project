import sys
import requests

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6.QtCore import Qt

# API Ключи (из урока) - учебные
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"
STATIC_MAPS_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
GEOSEARCH_API_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

# API Серверы
GEOCODER_API_SERVER = "http://geocode-maps.yandex.ru/1.x/"
STATIC_MAPS_API_SERVER = "https://static-maps.yandex.ru/v1"
GEOSEARCH_API_SERVER = "https://search-maps.yandex.ru/v1/"

MAP_WIDTH, MAP_HEIGHT = 600, 450
ZOOM_FACTOR = 1.5
MIN_SPN = 0.0005
MAX_SPN = 80.0


class MapViewerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.lon = 37.617635
        self.lat = 55.755814
        self.spn_lon = 0.05
        self.spn_lat = 0.02
        self.map_type = "map"

        self.initUI()
        self.load_map()

    def initUI(self):
        self.setWindowTitle('Интерактивная карта (PgUp/PgDown для зума)')
        self.setGeometry(100, 100, MAP_WIDTH, MAP_HEIGHT)

        self.image_label = QLabel(self)
        self.image_label.resize(MAP_WIDTH, MAP_HEIGHT)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        self.show()

    def load_map(self):
        ll = f"{self.lon:.6f},{self.lat:.6f}"
        self.spn_lon = max(MIN_SPN, min(self.spn_lon, MAX_SPN))
        self.spn_lat = max(MIN_SPN, min(self.spn_lat, MAX_SPN))
        spn = f"{self.spn_lon:.6f},{self.spn_lat:.6f}"
        size = f"{MAP_WIDTH},{MAP_HEIGHT}"

        map_params = {
            "ll": ll,
            "spn": spn,
            "l": self.map_type,
            "size": size,
            "apikey": STATIC_MAPS_API_KEY
        }

        try:
            print(f"Запрос карты: ll={ll}, spn={spn}")
            response = requests.get(STATIC_MAPS_API_SERVER, params=map_params)
            response.raise_for_status()

            pixmap = QPixmap()
            loaded = pixmap.loadFromData(response.content)

            if loaded:
                self.image_label.setPixmap(pixmap)
                print("Карта успешно загружена и отображена.")
            else:
                print("Ошибка: Не удалось загрузить QPixmap из полученных данных.")
                self.image_label.setText("Ошибка загрузки карты")

        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при запросе карты: {e}")
            self.image_label.setText(f"Ошибка сети:\n{e}")
        except Exception as e:
            print(f"Непредвиденная ошибка при загрузке карты: {e}")
            self.image_label.setText(f"Ошибка:\n{e}")

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        map_updated = False

        if key == Qt.Key.Key_PageUp:
            print("Нажата PgUp (Zoom In)")
            new_spn_lon = self.spn_lon / ZOOM_FACTOR
            new_spn_lat = self.spn_lat / ZOOM_FACTOR
            # Check bounds before assigning
            if new_spn_lon >= MIN_SPN and new_spn_lat >= MIN_SPN:
                self.spn_lon = new_spn_lon
                self.spn_lat = new_spn_lat
                map_updated = True
            else:
                print("Достигнут минимальный масштаб")

        elif key == Qt.Key.Key_PageDown:
            print("Нажата PgDown (Zoom Out)")
            new_spn_lon = self.spn_lon * ZOOM_FACTOR
            new_spn_lat = self.spn_lat * ZOOM_FACTOR
            # Check bounds before assigning
            if new_spn_lon <= MAX_SPN and new_spn_lat <= MAX_SPN:
                self.spn_lon = new_spn_lon
                self.spn_lat = new_spn_lat
                map_updated = True
            else:
                print("Достигнут максимальный масштаб")

        if map_updated:
            self.load_map()
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MapViewerApp()
    sys.exit(app.exec())
