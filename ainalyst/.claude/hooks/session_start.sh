#!/bin/bash
# SessionStart hook — загружает контекст проекта AInalyst для BA
# Вывод в stdout добавляется как контекст который Claude видит в начале сессии

PROJECTS_DIR="$CLAUDE_PROJECT_DIR/projects"

echo "=== AInalyst — Контекст проекта ==="
echo ""

# Показываем какие проекты уже есть (по подпапкам projects/<id>/output/)
if [ -d "$PROJECTS_DIR" ] && [ "$(find "$PROJECTS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null)" ]; then
    echo "📁 Активные проекты:"
    find "$PROJECTS_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | \
        sed 's/.*\///' | \
        sort -u | \
        while read proj; do echo "   • $proj"; done
    echo ""
else
    echo "📁 Проектов пока нет. Начните с нового проекта."
    echo "   Пример: «Начинаю новый проект — автоматизация HR в банке»"
    echo ""
fi

# Показываем последние сохранённые отчёты (во всех projects/<id>/output/reports/)
if [ -d "$PROJECTS_DIR" ] && [ "$(find "$PROJECTS_DIR" -path '*/output/reports/*.md' 2>/dev/null)" ]; then
    echo "📄 Последние артефакты:"
    find "$PROJECTS_DIR" -path '*/output/reports/*.md' 2>/dev/null | xargs -r ls -t 2>/dev/null | head -5 | \
        while read f; do
            echo "   • $(basename $f)  (${f#$PROJECTS_DIR/})"
        done
    echo ""
fi

echo "💡 Просто опишите задачу на русском — я подберу нужный скилл и инструмент."
echo "   Голосовой режим: /voice (держи пробел — говори, отпусти — отправь)"
echo "   Плановый режим: Shift+Tab дважды (обсудить подход перед действием)"
echo "   Экспорт в PDF:  python export_pdf.py [файл.md | --all] [--force]"
echo "   Канал проекта:  https://t.me/platform_ainalyst"
echo ""

# Показываем файлы готовые к обработке — inputs/ (standalone AInalyst) или
# projects/<project_id>/input/ (внутри эпика RE_Projects, Компетенция 2)
INPUTS_DIR="$CLAUDE_PROJECT_DIR/inputs"
INPUT_FILES=$(find "$INPUTS_DIR" -maxdepth 1 \( -name "*.txt" -o -name "*.md" -o -name "*.pdf" -o -name "*.docx" \) ! -name "README*" 2>/dev/null)
if [ -d "$INPUTS_DIR" ] && [ -n "$INPUT_FILES" ]; then
    echo "📂 Файлы готовые к обработке (inputs/):"
    echo "$INPUT_FILES" | while read f; do echo "   • $(basename $f)"; done
    echo "   Скажите: «Обработай материал: inputs/ИМЯ_ФАЙЛА»"
    echo ""
fi

PROJECT_INPUT_FILES=$(find "$PROJECTS_DIR" -path '*/input/*' \( -name "*.txt" -o -name "*.md" -o -name "*.pdf" -o -name "*.docx" \) 2>/dev/null)
if [ -d "$PROJECTS_DIR" ] && [ -n "$PROJECT_INPUT_FILES" ]; then
    echo "📂 Файлы готовые к обработке (projects/<project_id>/input/):"
    echo "$PROJECT_INPUT_FILES" | while read f; do echo "   • ${f#$PROJECTS_DIR/}"; done
    echo "   Скажите: «Обработай материал: projects/ПРОЕКТ/input/ИМЯ_ФАЙЛА»"
    echo ""
fi
