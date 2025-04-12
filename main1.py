import sys

import requests
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

# API Ключи (из урока) - учебные
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"
STATIC_MAPS_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
GEOSEARCH_API_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

# API Серверы
GEOCODER_API_SERVER = "http://geocode-maps.yandex.ru/1.x/"
STATIC_MAPS_API_SERVER = "https://static-maps.yandex.ru/v1"
GEOSEARCH_API_SERVER = "https://search-maps.yandex.ru/v1/"

MAP_WIDTH, MAP_HEIGHT = 600, 450


class MapViewerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.lon = 37.617635  # Долгота
        self.lat = 55.755814  # Широта
        self.spn_lon = 0.05
        self.spn_lat = 0.02
        self.map_type = "map"

        self.initUI()
        self.load_map()

    def initUI(self):
        self.setWindowTitle('Интерактивная карта')
        self.setGeometry(100, 100, MAP_WIDTH, MAP_HEIGHT)

        self.image_label = QLabel(self)
        self.image_label.resize(MAP_WIDTH, MAP_HEIGHT)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        self.show()

    def load_map(self):
        ll = f"{self.lon:.6f},{self.lat:.6f}"
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MapViewerApp()
    sys.exit(app.exec())
