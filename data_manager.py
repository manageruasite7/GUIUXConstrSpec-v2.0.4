# --- v1.0: МОДУЛЬ ДЛЯ УПРАВЛЕНИЯ ДАННЫМИ ПРОЕКТА (СОХРАНЕНИЕ/ЗАГРУЗКА) ---
import json
import os

class DataManager:
    def save_project(self, project_data, file_path):
        """СОХРАНЯЕТ ДАННЫЕ ПРОЕКТА В JSON ФАЙЛ."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            pass
            return False

    def load_project(self, file_path):
        """ЗАГРУЖАЕТ ДАННЫЕ ПРОЕКТА ИЗ JSON ФАЙЛА."""
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            return project_data
        except Exception as e:
            pass
            return None