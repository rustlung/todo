import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database import build_engine, get_session_factory, session_scope
from app.models import Base, Task

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def create_app(database_url: str | None = None) -> FastAPI:
    engine = build_engine(database_url)
    session_factory = get_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        logger.info("Database is ready")
        yield
        engine.dispose()

    app = FastAPI(title="To-Do List", lifespan=lifespan)
    app.state.session_factory = session_factory
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    def render_tasks(request: Request, session: Session, current_filter: str, error: str | None = None, form_title: str = ""):
        query: Select[tuple[Task]] = select(Task).order_by(Task.completed, Task.created_at.desc())
        if current_filter == "active":
            query = query.where(Task.completed.is_(False))
        elif current_filter == "completed":
            query = query.where(Task.completed.is_(True))
        tasks = session.scalars(query).all()
        active_count = session.scalar(select(func.count(Task.id)).where(Task.completed.is_(False))) or 0
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "tasks": tasks,
                "active_count": active_count,
                "current_filter": current_filter,
                "error": error,
                "form_title": form_title,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY if error else status.HTTP_200_OK,
        )

    def redirect_to_list(current_filter: str) -> RedirectResponse:
        return RedirectResponse(url=f"/?filter={current_filter}", status_code=status.HTTP_303_SEE_OTHER)

    def get_task_or_404(session: Session, task_id: int) -> Task:
        task = session.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task

    @app.get("/", name="task_list")
    def task_list(request: Request, filter: Literal["all", "active", "completed"] = "all"):
        with session_scope(request.app.state.session_factory) as session:
            return render_tasks(request, session, filter)

    @app.post("/tasks", name="create_task")
    def create_task(
        request: Request,
        title: str = Form(...),
        current_filter: Literal["all", "active", "completed"] = Form("all"),
    ):
        clean_title = title.strip()
        with session_scope(request.app.state.session_factory) as session:
            if not clean_title:
                return render_tasks(request, session, current_filter, "Введите текст задачи.", title)
            if len(clean_title) > 300:
                return render_tasks(request, session, current_filter, "Задача не должна быть длиннее 300 символов.", title)
            session.add(Task(title=clean_title))
            session.commit()
        logger.info("Task created")
        return redirect_to_list(current_filter)

    @app.post("/tasks/{task_id}/toggle", name="toggle_task")
    def toggle_task(request: Request, task_id: int, current_filter: Literal["all", "active", "completed"] = Form("all")):
        with session_scope(request.app.state.session_factory) as session:
            task = get_task_or_404(session, task_id)
            task.completed = not task.completed
            session.commit()
        logger.info("Task %s toggled", task_id)
        return redirect_to_list(current_filter)

    @app.post("/tasks/{task_id}/edit", name="edit_task")
    def edit_task(
        request: Request,
        task_id: int,
        title: str = Form(...),
        current_filter: Literal["all", "active", "completed"] = Form("all"),
    ):
        clean_title = title.strip()
        with session_scope(request.app.state.session_factory) as session:
            task = get_task_or_404(session, task_id)
            if not clean_title:
                return render_tasks(request, session, current_filter, "Введите текст задачи.")
            if len(clean_title) > 300:
                return render_tasks(request, session, current_filter, "Задача не должна быть длиннее 300 символов.")
            task.title = clean_title
            session.commit()
        logger.info("Task %s edited", task_id)
        return redirect_to_list(current_filter)

    @app.post("/tasks/{task_id}/delete", name="delete_task")
    def delete_task(request: Request, task_id: int, current_filter: Literal["all", "active", "completed"] = Form("all")):
        with session_scope(request.app.state.session_factory) as session:
            task = get_task_or_404(session, task_id)
            session.delete(task)
            session.commit()
        logger.info("Task %s deleted", task_id)
        return redirect_to_list(current_filter)

    return app


app = create_app()
