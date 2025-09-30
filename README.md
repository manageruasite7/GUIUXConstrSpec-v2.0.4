# GUIUXConstrSpec-v2.0.4
Graphic-UI-UX-Constructor-Specification-For-LLM-AI

Графический конструктор ИИ спецификаций прототипа интерфейса.

Сборка финального .exe файла
1. Открой терминал (командную строку).
2. Перейди в папку с файлами проекта.
3. Выполни команду (ниже команды):
pyinstaller ^
    --name GUIUXConstrSpec ^
    --onefile ^
    --windowed ^
    --add-data "assets;assets" ^
    --add-data "translations;translations" ^
    main.py

    Результат: В папке dist появится единственный файл GUIUXConstrSpec.exe. Это и есть готовая программа.
