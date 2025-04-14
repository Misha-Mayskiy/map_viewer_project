import sys
import requests
import math

from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QCheckBox, QLineEdit, QPushButton, QHBoxLayout)
from PyQt6.QtGui import QPixmap, QKeyEvent, QMouseEvent
from PyQt6.QtCore import Qt, QPoint

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
MIN_LAT, MAX_LAT = -85.05112878, 85.05112878
MIN_LON, MAX_LON = -180.0, 180.0


class MapViewerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.postal_code_checkbox = QCheckBox("Добавить индекс", self)
        self.address_label = QLabel("Полный адрес:", self)
        self.theme_checkbox = QCheckBox("Тёмная тема", self)
        self.address_display = QLabel("", self)
        self.reset_button = QPushButton("Сброс", self)
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
        self.current_full_address = ""
        self.current_postal_code = None
        self.include_postal_code = False

        self.initUI()
        self.load_map()

    def initUI(self):
        self.setWindowTitle('Карта v0.11')
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

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.theme_checkbox)
        controls_layout.addWidget(self.postal_code_checkbox)
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
            response = requests.get(STATIC_MAPS_API_SERVER, params=map_params)
            response.raise_for_status()
            pixmap = QPixmap()
            loaded = pixmap.loadFromData(response.content)
            if loaded:
                self.image_label.setPixmap(pixmap)
            else:
                print("Ошибка: Не удалось загрузить QPixmap.")
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
        self.current_theme = "dark" if state == Qt.CheckState.Checked.value else "light"
        print(f"Переключена тема: {self.current_theme}")
        self.load_map()

    def toggle_postal_code(self, state):
        self.include_postal_code = (state == Qt.CheckState.Checked.value)
        print(f"Отображение индекса: {'Включено' if self.include_postal_code else 'Выключено'}")
        self.update_address_display()

    def clear_search_state(self):
        self.marker_coords = None
        self.current_full_address = ""
        self.current_postal_code = None
        self.update_address_display()

    def reset_search_result(self):
        if self.marker_coords or self.current_full_address:
            print("Сброс результата поиска.")
            self.clear_search_state()
            self.search_input.clear()
            self.load_map()
        else:
            print("Нет активного результата поиска для сброса.")

    def update_address_display(self):
        if not self.current_full_address:
            self.address_display.clear()
            return
        display_text = self.current_full_address
        if self.include_postal_code and self.current_postal_code:
            display_text += f", {self.current_postal_code}"
        self.address_display.setText(display_text)

    def search_object(self):
        search_query = self.search_input.text().strip()
        if not search_query: return
        print(f"Выполняется поиск: '{search_query}'")
        self.clear_search_state()
        found_data = self.geocode(geocode_query=search_query)
        if found_data:
            self.update_map_view(found_data)
            self.set_search_result(found_data)
            self.load_map()

    def geocode(self, geocode_query=None, coords=None):
        if not geocode_query and not coords: return None
        geocoder_params = {"apikey": GEOCODER_API_KEY, "format": "json", "results": 1}
        if geocode_query:
            geocoder_params["geocode"] = geocode_query
        elif coords:
            geocoder_params["geocode"] = f"{coords[0]:.6f},{coords[1]:.6f}"
        try:
            response = requests.get(GEOCODER_API_SERVER, params=geocoder_params)
            response.raise_for_status()
            json_response = response.json()
            feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]
            if not feature_member:
                print(f"Ошибка геокодера: Объект не найден.")
                return None
            geo_object = feature_member[0]["GeoObject"]
            point_str = geo_object["Point"]["pos"]
            found_lon, found_lat = map(float, point_str.split(" "))
            found_coords = (found_lon, found_lat)
            address_meta = geo_object["metaDataProperty"]["GeocoderMetaData"]
            full_address = address_meta.get("text", "Адрес не найден")
            postal_code = address_meta.get("Address", {}).get("postal_code")
            print(f"Геокодер вернул: {full_address}" + (f", {postal_code}" if postal_code else ""))
            bounds = None
            try:
                envelope = geo_object["boundedBy"]["Envelope"]
                lc_lon, lc_lat = map(float, envelope["lowerCorner"].split(" "))
                uc_lon, uc_lat = map(float, envelope["upperCorner"].split(" "))
                bounds = ((lc_lon, lc_lat), (uc_lon, uc_lat))
            except (KeyError, IndexError, ValueError):
                pass
            return {"coords": found_coords, "address": full_address,
                    "postal_code": postal_code, "bounds": bounds}
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при запросе к Геокодеру: {e}")
            return None
        except Exception as e:
            print(f"Непредвиденная ошибка при геокодировании: {e}")
            return None

    def update_map_view(self, geo_data):
        if not geo_data: return
        self.lon, self.lat = geo_data["coords"]
        if geo_data["bounds"]:
            lc, uc = geo_data["bounds"]
            delta_lon, delta_lat = abs(uc[0] - lc[0]), abs(uc[1] - lc[1])
            self.spn_lon = max(delta_lon * 1.2, MIN_SPN * 10)
            self.spn_lat = max(delta_lat * 1.2, MIN_SPN * 10)
        else:
            print("Используется зум по умолчанию (нет границ).")
            self.spn_lon, self.spn_lat = 0.01, 0.005
        # print(f"Центр карты обновлен: ({self.lon:.6f}, {self.lat:.6f}), spn: ({self.spn_lon:.6f}, {self.spn_lat:.6f})")

    def set_search_result(self, geo_data):
        if not geo_data: return
        self.marker_coords = geo_data["coords"]
        self.current_full_address = geo_data["address"]
        self.current_postal_code = geo_data["postal_code"]
        self.update_address_display()
        print(f"Установлен результат поиска: Метка {self.marker_coords}, Адрес: {self.current_full_address}")

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        map_updated = False
        if self.search_input.hasFocus():
            super().keyPressEvent(event)
            return
        if key == Qt.Key.Key_PageUp:
            new_spn_lon, new_spn_lat = self.spn_lon / ZOOM_FACTOR, self.spn_lat / ZOOM_FACTOR
            if new_spn_lon >= MIN_SPN and new_spn_lat >= MIN_SPN:
                self.spn_lon, self.spn_lat = new_spn_lon, new_spn_lat
                map_updated = True
            else:
                print("Достигнут минимальный масштаб")
        elif key == Qt.Key.Key_PageDown:
            new_spn_lon, new_spn_lat = self.spn_lon * ZOOM_FACTOR, self.spn_lat * ZOOM_FACTOR
            if new_spn_lon <= MAX_SPN and new_spn_lat <= MAX_SPN:
                self.spn_lon, self.spn_lat = new_spn_lon, new_spn_lat
                map_updated = True
            else:
                print("Достигнут максимальный масштаб")
        elif key == Qt.Key.Key_Up:
            new_lat = self.lat + self.spn_lat * MOVE_STEP_FACTOR
            if new_lat <= MAX_LAT:
                self.lat, map_updated = new_lat, True
            else:
                print("Достигнута северная граница карты")
        elif key == Qt.Key.Key_Down:
            new_lat = self.lat - self.spn_lat * MOVE_STEP_FACTOR
            if new_lat >= MIN_LAT:
                self.lat, map_updated = new_lat, True
            else:
                print("Достигнута южная граница карты")
        elif key == Qt.Key.Key_Left:
            new_lon = self.lon - self.spn_lon * MOVE_STEP_FACTOR
            if new_lon >= MIN_LON:
                self.lon, map_updated = new_lon, True
            else:
                print("Достигнута западная граница карты")
        elif key == Qt.Key.Key_Right:
            new_lon = self.lon + self.spn_lon * MOVE_STEP_FACTOR
            if new_lon <= MAX_LON:
                self.lon, map_updated = new_lon, True
            else:
                print("Достигнута восточная граница карты")
        if map_updated:
            self.load_map()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if self.image_label.underMouse():
            if event.button() == Qt.MouseButton.LeftButton:
                print("Левый клик по карте.")
                map_pixel_pos = self.image_label.mapFromParent(event.pos())
                geo_coords = self.screen_to_geo(map_pixel_pos)
                if geo_coords:
                    print(f"Координаты клика: {geo_coords}")
                    self.clear_search_state()
                    found_data = self.geocode(coords=geo_coords)
                    if found_data:
                        self.set_search_result(found_data)
                        self.load_map()
                else:
                    print("Не удалось преобразовать координаты клика.")
        else:
            super().mousePressEvent(event)

    def screen_to_geo(self, screen_pos: QPoint):
        """
        Converts pixel coordinates (relative to map label) to geo coordinates
        using Mercator projection logic adapted for Static API's ll/spn. (More Accurate)
        """
        try:
            x_pix, y_pix = screen_pos.x(), screen_pos.y()
            center_lon, center_lat = self.lon, self.lat
            span_lon, span_lat = self.spn_lon, self.spn_lat
            map_width, map_height = MAP_WIDTH, MAP_HEIGHT

            lon_per_pixel = span_lon / map_width
            clicked_lon = center_lon + (x_pix - map_width / 2.0) * lon_per_pixel

            def lat_to_merc_y(lat_d):
                lat_r = math.radians(max(MIN_LAT, min(lat_d, MAX_LAT)))
                sin_lat = math.sin(lat_r)
                if abs(sin_lat) > 0.999999:
                    sin_lat = math.copysign(0.999999, sin_lat)
                y = 0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)
                return y

            def merc_y_to_lat(y_norm):
                g = math.pi * (1 - 2 * y_norm)
                lat_d = math.degrees(2 * math.atan(math.exp(g)) - math.pi / 2)
                return lat_d

            lat_top = center_lat + span_lat / 2.0
            lat_bottom = center_lat - span_lat / 2.0
            merc_y_top = lat_to_merc_y(lat_top)
            merc_y_bottom = lat_to_merc_y(lat_bottom)

            pixel_y_fraction = y_pix / map_height
            clicked_merc_y = merc_y_top + pixel_y_fraction * (merc_y_bottom - merc_y_top)

            clicked_lat = merc_y_to_lat(clicked_merc_y)

            clicked_lon = max(MIN_LON, min(clicked_lon, MAX_LON))
            clicked_lat = max(MIN_LAT, min(clicked_lat, MAX_LAT))

            return (clicked_lon, clicked_lat)
        except Exception as e:
            print(f"Ошибка при конвертации координат: {e}")
            return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MapViewerApp()
    sys.exit(app.exec())
