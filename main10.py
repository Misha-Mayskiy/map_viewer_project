import sys
import requests

from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QCheckBox, QLineEdit, QPushButton, QHBoxLayout)
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6.QtCore import Qt

# Используем учебные ключи из предыдущего кода
GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"
STATIC_MAPS_API_KEY = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
GEOSEARCH_API_KEY = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

# API Серверы
GEOCODER_API_SERVER = "http://geocode-maps.yandex.ru/1.x/"
STATIC_MAPS_API_SERVER = "https://static-maps.yandex.ru/v1"
GEOSEARCH_API_SERVER = "https://search-maps.yandex.ru/v1/"

MAP_WIDTH, MAP_HEIGHT = 600, 450
ZOOM_FACTOR = 1.5
MOVE_STEP_FACTOR = 0.8
MIN_SPN = 0.0005
MAX_SPN = 80.0
MIN_LAT, MAX_LAT = -85.0, 85.0
MIN_LON, MAX_LON = -180.0, 180.0


class MapViewerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.theme_checkbox = QCheckBox("Тёмная тема", self)
        self.postal_code_checkbox = QCheckBox("Добавить индекс", self)  # Новый чекбокс
        self.reset_button = QPushButton("Сброс", self)
        self.address_display = QLabel("", self)
        self.address_label = QLabel("Полный адрес:", self)
        self.image_label = QLabel(self)
        self.search_button = QPushButton("Искать", self)
        self.search_input = QLineEdit(self)
        self.lon = 37.617635
        self.lat = 55.755814
        self.spn_lon = 0.05
        self.spn_lat = 0.02
        self.map_type = "map"
        self.current_theme = "light"
        self.marker_coords = None
        self.current_full_address = ""  # Хранит полный адрес
        self.current_postal_code = None  # Хранит индекс отдельно
        self.include_postal_code = False  # Состояние чекбокса индекса

        self.initUI()
        self.load_map()

    def initUI(self):
        self.setWindowTitle('Карта v0.9')
        self.setGeometry(100, 100, MAP_WIDTH, MAP_HEIGHT + 120)

        self.search_input.setPlaceholderText("Введите адрес для поиска...")

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.reset_button)

        self.image_label.resize(MAP_WIDTH, MAP_HEIGHT)
        self.image_label.setStyleSheet("background-color: lightgray;")

        self.address_display.setWordWrap(True)
        self.address_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # --- Control Checkboxes ---
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.theme_checkbox)
        controls_layout.addWidget(self.postal_code_checkbox)  # Добавили в layout
        controls_layout.addStretch(1)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(self.address_label)
        main_layout.addWidget(self.address_display)
        main_layout.addLayout(controls_layout)
        self.setLayout(main_layout)

        self.search_button.clicked.connect(self.search_object)
        self.search_input.returnPressed.connect(self.search_object)
        self.reset_button.clicked.connect(self.reset_search_result)
        self.theme_checkbox.stateChanged.connect(self.toggle_theme)
        # Соединяем сигнал нового чекбокса
        self.postal_code_checkbox.stateChanged.connect(self.toggle_postal_code)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.show()

    def load_map(self):
        self.lon = max(MIN_LON, min(self.lon, MAX_LON))
        self.lat = max(MIN_LAT, min(self.lat, MAX_LAT))
        self.spn_lon = max(MIN_SPN, min(self.spn_lon, MAX_SPN))
        self.spn_lat = max(MIN_SPN, min(self.spn_lat, MAX_SPN))

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

        if self.current_theme == "dark":
            map_params["theme"] = "dark"

        if self.marker_coords:
            marker_lon, marker_lat = self.marker_coords
            map_params["pt"] = f"{marker_lon:.6f},{marker_lat:.6f},pm2rdm"

        try:
            print(f"Запрос карты: ll={ll}, spn={spn}, theme={self.current_theme}")
            response = requests.get(STATIC_MAPS_API_SERVER, params=map_params)
            response.raise_for_status()

            pixmap = QPixmap()
            loaded = pixmap.loadFromData(response.content)

            if loaded:
                self.image_label.setPixmap(pixmap)
            else:
                print("Ошибка: Не удалось загрузить QPixmap из полученных данных.")
                self.image_label.setText("Ошибка загрузки карты")
                self.clear_search_state()

        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при запросе карты: {e}")
            self.image_label.setText(f"Ошибка сети:\n{e}")
            self.clear_search_state()
        except Exception as e:
            print(f"Непредвиденная ошибка при загрузке карты: {e}")
            self.image_label.setText(f"Ошибка:\n{e}")
            self.clear_search_state()

    def toggle_theme(self, state):
        if state == Qt.CheckState.Checked.value:
            self.current_theme = "dark"
            print("Переключена тема: Тёмная")
        else:
            self.current_theme = "light"
            print("Переключена тема: Светлая")
        self.load_map()

    def toggle_postal_code(self, state):
        """Обрабатывает изменение состояния чекбокса индекса."""
        self.include_postal_code = (state == Qt.CheckState.Checked.value)
        print(f"Отображение индекса: {'Включено' if self.include_postal_code else 'Выключено'}")
        self.update_address_display()  # Обновляем отображение адреса

    def search_object(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            print("Поисковый запрос пуст.")
            return
        print(f"Выполняется поиск: '{search_query}'")
        # Очищаем предыдущие результаты перед новым поиском
        self.clear_search_state()
        self.geocode_and_update_map(search_query)

    def reset_search_result(self):
        if self.marker_coords or self.current_full_address:
            print("Сброс результата поиска (удаление метки и адреса).")
            self.clear_search_state()
            self.search_input.clear()  # Очищаем поле ввода при сбросе
            self.load_map()
        else:
            print("Нет активного результата поиска для сброса.")

    def clear_search_state(self):
        """Вспомогательная функция для сброса состояния поиска."""
        self.marker_coords = None
        self.current_full_address = ""
        self.current_postal_code = None
        self.update_address_display()  # Обновляем (очищаем) отображение адреса

    def update_address_display(self):
        """Форматирует и отображает адрес в зависимости от состояния."""
        if not self.current_full_address:
            self.address_display.clear()
            return

        display_text = self.current_full_address
        # Добавляем индекс, если он есть и чекбокс включен
        if self.include_postal_code and self.current_postal_code:
            display_text += f", {self.current_postal_code}"

        self.address_display.setText(display_text)

    def geocode_and_update_map(self, address_to_find):
        geocoder_params = {
            "apikey": GEOCODER_API_KEY,
            "geocode": address_to_find,
            "format": "json",
            "results": 1
        }
        try:
            response = requests.get(GEOCODER_API_SERVER, params=geocoder_params)
            response.raise_for_status()
            json_response = response.json()

            feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]
            if not feature_member:
                print(f"Ошибка геокодера: Объект '{address_to_find}' не найден.")
                # self.reset_search_result() # Сброс уже сделан в search_object
                self.load_map()
                return

            geo_object = feature_member[0]["GeoObject"]
            point_str = geo_object["Point"]["pos"]
            found_lon, found_lat = map(float, point_str.split(" "))

            # --- Извлечение Адреса и Индекса ---
            try:
                address_meta = geo_object["metaDataProperty"]["GeocoderMetaData"]
                self.current_full_address = address_meta.get("text", "Адрес не найден")
                address_details = address_meta.get("Address", {})
                self.current_postal_code = address_details.get("postal_code")  # Получаем индекс

                print(f"Найден адрес: {self.current_full_address}")
                if self.current_postal_code:
                    print(f"Найден индекс: {self.current_postal_code}")
                else:
                    print("Почтовый индекс не найден.")

                # Обновляем отображение сразу после получения данных
                self.update_address_display()

            except (KeyError, TypeError):
                print("Не удалось извлечь адрес/индекс из ответа геокодера.")
                self.current_full_address = "Адрес/индекс не найден"
                self.current_postal_code = None
                self.update_address_display()

            self.lon = found_lon
            self.lat = found_lat
            self.marker_coords = (found_lon, found_lat)
            print(f"Установлена метка: {self.marker_coords}")

            try:
                envelope = geo_object["boundedBy"]["Envelope"]
                lc_lon, lc_lat = map(float, envelope["lowerCorner"].split(" "))
                uc_lon, uc_lat = map(float, envelope["upperCorner"].split(" "))
                delta_lon = abs(uc_lon - lc_lon)
                delta_lat = abs(uc_lat - lc_lat)
                self.spn_lon = max(delta_lon * 1.2, MIN_SPN * 10)
                self.spn_lat = max(delta_lat * 1.2, MIN_SPN * 10)
            except (KeyError, IndexError, ValueError):
                print("Не удалось получить границы объекта, используется зум по умолчанию.")
                self.spn_lon = 0.01
                self.spn_lat = 0.005

            print(
                f"Объект найден. Центр: ({self.lon:.6f}, {self.lat:.6f}), spn: ({self.spn_lon:.6f}, {self.spn_lat:.6f})")
            self.load_map()

        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при запросе к Геокодеру: {e}")
            # self.reset_search_result() # Сброс уже сделан в search_object
            self.load_map()
        except Exception as e:
            print(f"Непредвиденная ошибка при геокодировании: {e}")
            # self.reset_search_result() # Сброс уже сделан в search_object
            self.load_map()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        map_updated = False

        if self.search_input.hasFocus():
            super().keyPressEvent(event)
            return

        if key == Qt.Key.Key_PageUp:
            new_spn_lon = self.spn_lon / ZOOM_FACTOR
            new_spn_lat = self.spn_lat / ZOOM_FACTOR
            if new_spn_lon >= MIN_SPN and new_spn_lat >= MIN_SPN:
                self.spn_lon = new_spn_lon
                self.spn_lat = new_spn_lat
                map_updated = True
            else:
                print("Достигнут минимальный масштаб")

        elif key == Qt.Key.Key_PageDown:
            new_spn_lon = self.spn_lon * ZOOM_FACTOR
            new_spn_lat = self.spn_lat * ZOOM_FACTOR
            if new_spn_lon <= MAX_SPN and new_spn_lat <= MAX_SPN:
                self.spn_lon = new_spn_lon
                self.spn_lat = new_spn_lat
                map_updated = True
            else:
                print("Достигнут максимальный масштаб")

        elif key == Qt.Key.Key_Up:
            new_lat = self.lat + self.spn_lat * MOVE_STEP_FACTOR
            if new_lat <= MAX_LAT:
                self.lat = new_lat
                map_updated = True
            else:
                print("Достигнута северная граница карты")

        elif key == Qt.Key.Key_Down:
            new_lat = self.lat - self.spn_lat * MOVE_STEP_FACTOR
            if new_lat >= MIN_LAT:
                self.lat = new_lat
                map_updated = True
            else:
                print("Достигнута южная граница карты")

        elif key == Qt.Key.Key_Left:
            new_lon = self.lon - self.spn_lon * MOVE_STEP_FACTOR
            if new_lon >= MIN_LON:
                self.lon = new_lon
                map_updated = True
            else:
                print("Достигнута западная граница карты")

        elif key == Qt.Key.Key_Right:
            new_lon = self.lon + self.spn_lon * MOVE_STEP_FACTOR
            if new_lon <= MAX_LON:
                self.lon = new_lon
                map_updated = True
            else:
                print("Достигнута восточная граница карты")

        if map_updated:
            self.load_map()
        else:
            super().keyPressEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MapViewerApp()
    sys.exit(app.exec())
