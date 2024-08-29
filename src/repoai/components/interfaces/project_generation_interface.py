from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from ..components_base import BaseInterface
from ...core.project_manager import ProjectManager
from ...services.progress_service import ProgressService
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ProjectGenerationInterface(BaseInterface):
    def __init__(self, project_manager: ProjectManager, model_config: Dict[str, Any] = {}):
        super().__init__(project_manager, model_config)
        self.console = Console()
        self.progress_service = ProgressService(project_manager.project_path, project_manager.config)
        self.workflow = self.project_manager.get_workflow("project_generation_workflow")(self.progress_service, model_config.get("project_generation_workflow", {}))
        self.context = {}


    def run(self):
        self.console.print("[bold green]Starting project generation...[/bold green]")
        self.manage_context()
        self.run_project_generation_workflow()


    def manage_context(self):
        last_state = self.progress_service.get_last_state()
        if last_state:
            self.console.print("[yellow]Unfinished process found.[/yellow]")
            if Confirm.ask("Do you want to resume the unfinished process?"):
                self.resume_workflow()
                return
        self.context = {}


    def run_project_generation_workflow(self):
        self.context = self.project_description_chat()
        return



    def project_description_chat(self):
        self.console.print("\n[bold green]Starting project description chat...[/bold green]")
        if not self.context.get('description'):
            user_input = Prompt.ask("Please provide a brief description of your project")
            with self.console.status("[bold green]Starting project description chat..."):
                self.context = self.workflow.description_start(user_input, self.context)

        while True:
            self.display_output(self.context['messages'][-1]['content'])
            choice = self.handle_input(
                "Choice",
                choices=["continue", "apply", "reset", "exit"],
                default="continue"
            )
            if choice == "continue":
                user_input = self.handle_input("You")
                self.context['user_input'] = user_input
                with self.console.status("[bold Thinking..."):
                    self.context = self.workflow.execute_description_task(self.context)
            elif choice == "apply":
                user_input = self.context["description"]
                self.context = self.workflow.reset_chat_context(self.context)
                self.context["user_input"] = user_input  # Passing the prompt to the next task
                return self.project_structure_chat()
            elif choice == "reset":
                self.console.print("[yellow]Resetting context...[/yellow]\n")
                user_input = self.handle_input("Please provide a brief description of your project")
                with self.console.status("[bold green]Restarting chat..."):
                    self.context = self.workflow.description_start(user_input)
            elif choice == "exit":
                self.console.print("[yellow]Exiting project...[/yellow]")
                return None


    def project_structure_chat(self):
        self.console.print("\n[bold green]Starting project structure chat...[/bold green]")
        while True:
            with self.console.status("[bold green]Thinking..."):
                self.context = self.workflow.execute_structure_task(self.context)
            self.display_output(self.context['messages'][-1]['content'])
            choice = self.handle_input(
                "Choice",
                choices=["continue", "apply", "reset", "exit"],
                default="continue"
            )
            if choice == "continue":
                user_input = self.handle_input("You")
                self.context['user_input'] = user_input
            elif choice == "apply":
                return self.finalize_project()
            elif choice == "reset":
                self.console.print("[yellow]Resetting context...[/yellow]\n")
                self.context = self.workflow.reset_chat_context(self.context)
                self.context["user_input"] = self.context["description"]
            elif choice == "exit":
                self.console.print("[yellow]Exiting project...[/yellow]")
                return None


    def finalize_project(self):
        self.console.print("\n[bold green]Finalizing project...[/bold green]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Finalizing project...", total=None)
            self.context = self.workflow.finalize_project(self.context)
            progress.update(task, completed=True)

        self.display_output(
            f"**Project generation completed successfully for {self.project_manager.project_path}**\n\nGenerated files:"
        )
        for file_path in self.context.get('generated_files', {}).keys():
            self.console.print(f"  - [cyan]{file_path}[/cyan]")

        self.progress_service.clear_progress()
        return self.context


    def resume_workflow(self):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Resuming workflow...", total=None)
            last_step = self.progress_service.get_last_step()
            self.context = self.progress_service.resume_from_last_step()
            progress.update(task, completed=True)

        self.console.print(f"[yellow]Resuming from step: {last_step}[/yellow]")

        if last_step == "project_description":
            return self.project_description_chat()
        elif last_step == "project_structure":
            return self.project_structure_chat()
        elif last_step in ["paths_generation", "file_content_generation"]:
            return self.finalize_project()
        else:
            self.console.print("[yellow]Unknown last step. Starting from the beginning.[/yellow]")
            return self.run_project_generation_workflow()


    def display_output(self, output):
        self.console.print(Panel(Markdown(output), title="Assistant", border_style="blue"))


    def handle_input(self, prompt, **kwargs):
        return Prompt.ask(prompt, **kwargs)