# managers.py

import os
import json
import uuid
import copy
from PyQt5.QtCore import Qt

# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ШАБЛОНАМИ (v13.0) ---
class TemplatesManager:
    def __init__(self, filename="templates/templates.json"):
        self.filepath = filename
        self.templates = self.load_templates()

    def load_templates(self):
        """ЗАГРУЖАЕТ ШАБЛОНЫ ИЗ JSON-ФАЙЛА."""
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_templates(self):
        """СОХРАНЯЕТ ТЕКУЩИЕ ШАБЛОНЫ В JSON-ФАЙЛ."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            pass
            return False

    def add_template(self, name, description, data):
        """ДОБАВЛЯЕТ НОВЫЙ ШАБЛОН."""
        template_id = str(uuid.uuid4())
        self.templates[template_id] = {
            "name": name,
            "description": description,
            "data": data
        }
        return self.save_templates()

    def get_templates_list(self):
        """ВОЗВРАЩАЕТ СПИСОК ШАБЛОНОВ ДЛЯ ОТОБРАЖЕНИЯ (ID, ИМЯ, ОПИСАНИЕ)."""
        return [{"id": tid, "name": t.get("name"), "description": t.get("description", "")}
                for tid, t in self.templates.items()]
    
    def get_template_data(self, template_id):
        """ВОЗВРАЩАЕТ ДАННЫЕ КОНКРЕТНОГО ШАБЛОНА ПО ЕГО ID."""
        #import copy
        # ВОЗВРАЩАЕМ ГЛУБОКУЮ КОПИЮ, ЧТОБЫ ИЗМЕНЕНИЯ В ПРОЕКТЕ НЕ ЗАТРОНУЛИ ШАБЛОН
        return copy.deepcopy(self.templates.get(template_id, {}).get("data"))

# --- НАЧАЛО: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---
    def rename_template(self, template_id, new_name, new_description):
        """ПЕРЕИМЕНОВЫВАЕТ ШАБЛОН И ОБНОВЛЯЕТ ЕГО ОПИСАНИЕ."""
        if template_id in self.templates:
            self.templates[template_id]['name'] = new_name
            self.templates[template_id]['description'] = new_description
            return self.save_templates()
        return False

    def delete_template(self, template_id):
        """УДАЛЯЕТ ШАБЛОН ПО ЕГО ID."""
        if template_id in self.templates:
            del self.templates[template_id]
            return self.save_templates()
        return False
    # --- КОНЕЦ: ДОБАВЛЕНЫ МЕТОДЫ ДЛЯ УПРАВЛЕНИЯ ШАБЛОНАМИ (v15.7) ---

# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ШАБЛОНАМИ (v13.0) ---


# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ НАСТРОЙКАМИ СТИЛЕЙ (v9.7) ---
class StyleSettingsManager:
    def __init__(self, filename="settings/settings.json"):
        self.filepath = filename
        self.settings = self.load_settings()

    def get_default_settings(self):
        """ВОЗВРАЩАЕТ НАСТРОЙКИ ПО УМОЛЧАНИЮ."""
        return {
            "active": {
                "line_width": 2, "line_color": "#ff0000", "line_style": Qt.SolidLine,
                "fill_color": "#ff0000", "fill_opacity": 20
            },
            "inactive": {
                "line_width": 1, "line_color": "#808080", "line_style": Qt.DashLine,
                "fill_color": "#808080", "fill_opacity": 0
            },
            # --- НАЧАЛО: ДОБАВЬ ЭТОТ БЛОК (v2.0.5-fix) ---
            "relations": {
                "display_mode": "Подсветка", 
                "highlight_color_primary": "#0078D4",
                "highlight_color_secondary": "#50E6FF",
            },
            # --- КОНЕЦ: ДОБАВЬ ЭТОТ БЛОК (v2.0.5-fix) ---
             # --- НАЧАЛО: ДОБАВЛЕН КЛЮЧ ДЛЯ ПУТИ К РАБОЧЕЙ ОБЛАСТИ (v3.4-fix3) ---
            "workspace_path": ""
            # --- КОНЕЦ: ДОБАВЛЕН КЛЮЧ ДЛЯ ПУТИ К РАБОЧЕЙ ОБЛАСТИ (v3.4-fix3) ---
        }

    def load_settings(self):
        defaults = self.get_default_settings()
        if not os.path.exists(self.filepath):
            return defaults
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # --- ПОЛНОСТЬЮ ЗАМЕНЯЕМ СЛИЯНИЕ НА БОЛЕЕ НАДЕЖНОЕ (v3.6) ---
                for key in defaults:
                    if key in loaded_settings:
                        if isinstance(defaults[key], dict):
                            defaults[key].update(loaded_settings[key])
                        else:
                            defaults[key] = loaded_settings[key]
                return defaults
        except (json.JSONDecodeError, IOError):
            return self.get_default_settings()

    def save_settings(self):
        """СОХРАНЯЕТ ТЕКУЩИЕ НАСТРОЙКИ В JSON-ФАЙЛ."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            pass

    def get_style(self, style_type):
        """ПОЛУЧАЕТ СЛОВАРЬ С НАСТРОЙКАМИ ДЛЯ 'active' ИЛИ 'inactive'."""
        return self.settings.get(style_type, self.get_default_settings()[style_type])

    def set_style(self, style_type, new_values):
        """ОБНОВЛЯЕТ НАСТРОЙКИ ДЛЯ 'active' ИЛИ 'inactive'."""
        self.settings[style_type].update(new_values)
# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ НАСТРОЙКАМИ СТИЛЕЙ (v9.7) ---

# --- НАЧАЛО: НОВЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ СЦЕНАРИЯМИ (v3.3) ---
class ScenariosManager:
    def __init__(self, filename="scenarios.json"):
        self.filepath = filename
        self.scenarios = self.load_scenarios()

    def load_scenarios(self):
        """ЗАГРУЖАЕТ СЦЕНАРИИ ИЗ JSON-ФАЙЛА."""
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_scenarios(self):
        """СОХРАНЯЕТ ТЕКУЩИЕ СЦЕНАРИИ В JSON-ФАЙЛ."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.scenarios, f, indent=4, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get_scenarios_list(self):
        """ВОЗВРАЩАЕТ СПИСОК СЦЕНАРИЕВ ДЛЯ ОТОБРАЖЕНИЯ."""
        # Сортируем по имени для удобства
        sorted_scenarios = sorted(self.scenarios.values(), key=lambda x: x.get('name', ''))
        return sorted_scenarios

    def add_scenario(self, name):
        """ДОБАВЛЯЕТ НОВЫЙ ПУСТОЙ СЦЕНАРИЙ."""
        scenario_id = str(uuid.uuid4())
        self.scenarios[scenario_id] = {
            "id": scenario_id,
            "name": name,
            "description": ""
        }
        return scenario_id, self.save_scenarios()

    def update_scenario(self, scenario_id, name, description):
        """ОБНОВЛЯЕТ ИМЯ И ОПИСАНИЕ СЦЕНАРИЯ."""
        if scenario_id in self.scenarios:
            self.scenarios[scenario_id]['name'] = name
            self.scenarios[scenario_id]['description'] = description
            return self.save_scenarios()
        return False
        
    def delete_scenario(self, scenario_id):
        """УДАЛЯЕТ СЦЕНАРИЙ."""
        if scenario_id in self.scenarios:
            del self.scenarios[scenario_id]
            return self.save_scenarios()
        return False
# --- КОНЕЦ: НОВЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ СЦЕНАРИЯМИ (v3.3) ---