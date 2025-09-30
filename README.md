# GUIUXConstrSpec-v2.0.4 Graphic-UI-UX-Constructor-Specification-For-LLM-AI  
Графический конструктор ИИ спецификаций прототипа интерфейса.

## Запуск и сборка .exe  
Файлы, которые вам нужны:  
📄 `main.py` (в нём класс 🧩 `MainWindow` и блок запуска)  
📄 `README.md` (инструкция по сборке .exe)

### 1. Быстрый запуск из исходников (рекомендуется)  
Откройте терминал в корне проекта (там, где лежит `main.py`).  
Создайте виртуальное окружение и установите зависимости (требуется `PyQt5`):  
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install --upgrade pip
pip install PyQt5
```  
Запустите приложение:  
```bash
python main.py
```  
Запускать нужно из корня проекта, чтобы пути к 📄 `help.html` и другим ресурсам работали корректно.

### 2. Сборка в один .exe (Windows)  
По инструкции в 📄 `README.md`:  
```bash
pyinstaller ^
  --name GUIUXConstrSpec ^
  --onefile ^
  --windowed ^
  --add-data "assets;assets" ^
  --add-data "translations;translations" ^
  main.py
```

### 3. Примечания  
- Требуется Python 3.6+ (рекомендуется 3.8+).  
- Если при запуске возникают ошибки про отсутствующие модули — установите их через `pip`.  
- Запуск/сборка должна выполняться из корня проекта (где находится `main.py`), чтобы ресурсы (`assets/`, `translations/`) находились по ожидаемым относительным путям.
