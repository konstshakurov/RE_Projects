# Copyright (c) 2026 Anatoly Chaussky. AI-powered Platform AInalyst (AI Платформа AIналитик). Licensed under AGPL v3. Commercial licensing: chaussky@gmail.com
import os
import re
import sys
import logging
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

# Настройка логирования (stderr — не мешает протоколу JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("BABOK_Toolkit")

# Артефакты Компетенции 2 (BABOK v3) живут внутри проекта эпика RE_Projects,
# рядом с input/ — не в отдельном общем каталоге платформы (KON-12):
#   projects/<project_id>/output/data/     — JSON для MCP
#   projects/<project_id>/output/reports/  — Markdown для BA
#   projects/<project_id>/output/specs/    — спеки 7.1 и другие артефакты системного анализа
PROJECTS_DIR = "projects"
OUTPUT_SUBDIR = "output"

# Артефакты без project_id (например, confluence_pull) — не привязаны к проекту,
# складываются в общий плоский каталог на уровне эпика.
FALLBACK_REPORTS_DIR = "reports"


# ---------------------------------------------------------------------------
# Раскладка артефактов по подкаталогам проекта (issue #1)
# ---------------------------------------------------------------------------

_PID_DISALLOWED = re.compile(r"[^a-z0-9_-]+")


def normalize_project_id(project_id: str) -> str:
    """Безопасное имя проекта для использования как имя каталога.

    Защита от path traversal: убирает '/', '\\', '..', абсолютные пути;
    оставляет whitelist [a-z0-9_-]. Пустой результат → '_unknown'.
    """
    if not project_id:
        return "_unknown"
    s = str(project_id).strip().lower()
    s = s.replace("\\", "_").replace("/", "_").replace(" ", "_")
    s = _PID_DISALLOWED.sub("_", s)
    s = re.sub(r"_+", "_", s)
    s = s.strip("._-")
    return s or "_unknown"


def _project_output_dir(project_id: str) -> str:
    """projects/<safe_pid>/output/ — корень результатов проекта в эпике RE_Projects."""
    return os.path.join(PROJECTS_DIR, normalize_project_id(project_id), OUTPUT_SUBDIR)


def data_dir_for(project_id: str) -> str:
    """projects/<safe_pid>/output/data/ — каталог json-артефактов проекта."""
    return os.path.join(_project_output_dir(project_id), "data")


def report_dir_for(project_id: str) -> str:
    """projects/<safe_pid>/output/reports/ — каталог markdown-отчётов проекта."""
    return os.path.join(_project_output_dir(project_id), "reports")


def specs_dir(project_id: str) -> str:
    """projects/<safe_pid>/output/specs/ — каталог спеков 7.1 и других артефактов
    системного анализа проекта."""
    return os.path.join(_project_output_dir(project_id), "specs")


def data_path(project_id: str, filename: str) -> str:
    """Путь json-артефакта проекта: projects/<safe_pid>/output/data/<filename>.

    Каталог создаёт сторона записи: os.makedirs(os.path.dirname(path), ...).
    """
    return os.path.join(data_dir_for(project_id), filename)


class Stakeholder(BaseModel):
    """Модель стейкхолдера для матрицы вовлечения."""
    name: str = Field(..., description="Имя или роль стейкхолдера")
    influence: str = Field(..., pattern="^(Low|Medium|High)$", description="Уровень влияния")
    interest: str = Field(..., pattern="^(Low|Medium|High)$", description="Уровень интереса")
    attitude: Optional[str] = Field("Neutral", description="Отношение к проекту: Neutral / Champion / Blocker")


def save_artifact(content: str, prefix: str, project_id: Optional[str] = None) -> str:
    """Сохраняет Markdown-артефакт и возвращает путь.

    Если передан project_id — артефакт пишется в projects/<project_id>/output/reports/.
    Без project_id (артефакт не привязан к проекту) — в общий FALLBACK_REPORTS_DIR.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.md"
    out_dir = report_dir_for(project_id) if project_id else FALLBACK_REPORTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Артефакт сохранен: {filepath}")
    return f"\n\n✅ Артефакт сохранен: `{filepath}`"


# ---------------------------------------------------------------------------
# Shared matrices — используются в planning.py и planning_mcp.py
# Единственный источник истины (ADR-REVIEW-п5)
# ---------------------------------------------------------------------------

APPROACH_MATRIX: dict[tuple[str, str], tuple[str, list[str]]] = {
    ("Low",    "Low"):    ("Predictive (Waterfall)", ["Document Analysis", "Financial Analysis", "Business Rules Analysis"]),
    ("Low",    "Medium"): ("Predictive (Waterfall)", ["Document Analysis", "Interviews", "Prototyping"]),
    ("Low",    "High"):   ("Hybrid",                 ["Workshops", "Prototyping", "Risk Analysis"]),
    ("Medium", "Low"):    ("Hybrid",                 ["Workshops", "Prioritization", "Use Cases"]),
    ("Medium", "Medium"): ("Hybrid",                 ["Workshops", "User Stories", "Prioritization"]),
    ("Medium", "High"):   ("Adaptive (Agile)",        ["Backlog Management", "User Stories", "Retrospectives"]),
    ("High",   "Low"):    ("Adaptive (Agile)",        ["Backlog Management", "User Stories", "Kanban"]),
    ("High",   "Medium"): ("Adaptive (Agile)",        ["Backlog Management", "User Stories", "Retrospectives"]),
    ("High",   "High"):   ("Adaptive (Agile)",        ["Backlog Management", "Spike / PoC", "Retrospectives"]),
}

REGULATORY_OVERRIDE: dict[str, str] = {
    "Adaptive (Agile)": "Hybrid (Agile + compliance gates)",
    "Hybrid":           "Hybrid (с усиленным Governance)",
}

QUADRANT_STRATEGIES: dict[tuple[str, str], tuple[str, str, str]] = {
    ("High", "High"):     ("Key Players",     "Manage Closely — вовлекать в каждое решение",       "Еженедельно"),
    ("High", "Medium"):   ("Context Setters", "Keep Satisfied — информировать о ключевых вехах",   "При вехах"),
    ("High", "Low"):      ("Context Setters", "Keep Satisfied — информировать о ключевых вехах",   "При вехах"),
    ("Medium", "High"):   ("Subjects",        "Keep Informed — демонстрации, Sprint Review",        "Bi-weekly"),
    ("Low",  "High"):     ("Subjects",        "Keep Informed — демонстрации, Sprint Review",        "Bi-weekly"),
    ("Medium", "Medium"): ("Subjects",        "Keep Informed — регулярные обновления",              "Ежемесячно"),
    ("Medium", "Low"):    ("Crowd",           "Monitor — общая рассылка, низкий приоритет",         "Квартально"),
    ("Low",  "Medium"):   ("Crowd",           "Monitor — общая рассылка, низкий приоритет",         "Квартально"),
    ("Low",  "Low"):      ("Crowd",           "Monitor — общая рассылка, низкий приоритет",         "Квартально"),
}
