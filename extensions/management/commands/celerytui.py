# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime

from celery import current_app
from django.core.management.base import BaseCommand
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Static

from izumi_infra.utils.date_utils import PYTHON_DATETIME_FORMAT


class CeleryTUI(App):
    """A Textual app to display Celery tasks."""

    BINDINGS = [("q", "quit", "Quit")]

    CSS = """
    .table-title {
        margin-bottom: 1;
        text-align: center;
        width: 100%;
    }
    DataTable {
        margin-bottom: 2;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the UI layout."""
        yield Header()

        yield Static("Active Tasks", classes="table-title")
        yield DataTable(id="active_tasks")

        yield Static("Scheduled Tasks", classes="table-title")
        yield DataTable(id="scheduled_tasks")

        yield Static("Reserved Tasks", classes="table-title")
        yield DataTable(id="reserved_tasks")


    async def on_mount(self) -> None:
        """Initialize the tables and start the refresh loop."""
        # Start the background task to refresh data
        self.set_interval(1.0, self.refresh_tables)

    async def refresh_tables(self) -> None:
        """Refresh the data in the tables."""
        # Fetch data asynchronously
        inspect = current_app.control.inspect()
        active_tasks = await self.get_celery_tasks(inspect.active)
        scheduled_tasks = await self.get_celery_tasks(inspect.scheduled)
        reserved_tasks = await self.get_celery_tasks(inspect.reserved)

        # Update tables
        self.update_table("active_tasks", active_tasks)
        self.update_table("scheduled_tasks", scheduled_tasks)
        self.update_table("reserved_tasks", reserved_tasks)

    async def get_celery_tasks(self, inspect_method):
        """Fetch Celery tasks asynchronously."""
        loop = asyncio.get_event_loop()
        tasks = await loop.run_in_executor(None, inspect_method)
        return tasks or {}

    def update_table(self, table_id: str, tasks: dict) -> None:
        """Update a specific table with task data."""
        table = self.query_one(f"#{table_id}", DataTable)

        # Save the current cursor position
        cursor_row = table.cursor_row
        cursor_column = table.cursor_column

        table.clear(columns=True)
        table.border_title = table_id
        table.add_columns("Worker", "Task Name", "Task ID", "Task Args", "Task Kwargs", "Time Start", "Task Priority")
        for worker, task_list in tasks.items():
            for task in task_list:
                time_start = "N/A"
                if task.get("time_start"):
                    start = datetime.fromtimestamp(task.get("time_start"))
                    time_start = datetime.strftime(start, PYTHON_DATETIME_FORMAT)
                table.add_row(
                    worker,
                    task.get("name", "N/A"),
                    task.get("id", "N/A"),
                    str(task.get("args", "N/A")),
                    str(task.get("kwargs", "N/A")),
                    time_start,
                    str(task.get("delivery_info", {}).get("priority", "N/A")),
                )

        # Restore the cursor position
        if cursor_row < len(table.rows):
            table.move_cursor(row=cursor_row, column=cursor_column)

class Command(BaseCommand):
    help = "Launch a TUI for managing Celery tasks."

    def handle(self, *args, **kwargs):
        """Run the Textual app."""
        app = CeleryTUI()
        app.run()
