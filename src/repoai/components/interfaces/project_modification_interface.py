from typing import List, Dict, Any
from litellm import token_counter
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.markdown import Markdown
from ..components_base import BaseInterface
from ...core.project_manager import ProjectManager
from ...services.progress_service import ProgressService
from ...utils.logger import get_logger

logger = get_logger(__name__)



class ProjectModificationInterface(BaseInterface):
    def __init__(self, project_manager: ProjectManager, model_config: Dict[str, Any] = {}):
        super().__init__(project_manager, model_config)
        self.console = Console()
        self.progress_service = ProgressService(project_manager.project_path, project_manager.config)
        self.workflow = self.project_manager.get_workflow("project_modification_workflow")(self.progress_service, model_config.get("project_modification_workflow", {}))
        self.context = {}

    def run(self):
        self.console.print("[bold green]Starting project modification...[/bold green]")
        self.manage_context()
        self.run_project_modification_workflow()


    def manage_context(self):
        last_state = self.progress_service.get_last_state()
        if last_state:
            self.console.print("[yellow]Unfinished process found.[/yellow]")
            if Confirm.ask("Do you want to resume the unfinished process?"):
                self.resume_workflow()
                return
        self.context = self.workflow.reset_chat()

    def run_project_modification_workflow(self):

        self.display_output(self.context['project_report'])
        Initial_tokens = token_counter(model=self.model_config['project_modification_workflow']['project_modification_task']['model'], text=self.context['project_report'])
        self.console.print(f"[bold]Project report tokens:[/bold] {Initial_tokens}")
        while True:
            user_input = self.handle_input("Describe what you want to do (or 'exit' to quit or 'reset' to start over) press Enter twice to submit:")
            
            if user_input.strip().lower() == 'exit':
                break
            elif user_input.strip().lower() == 'reset':
                self.context = self.workflow.reset_chat()
                self.display_output(self.context['project_report'])
                continue

            file_contexts = self.get_file_contexts()
            image_contexts = self.get_image_contexts()

            with self.console.status("[bold green]Processing..."):
                self.context = self.workflow.execute(user_input, self.context, file_contexts, image_contexts)
            
            self.display_ai_response()
            self.display_proposed_modifications()

            action = self.handle_input(
                "What would you like to do?",
                choices=["apply", "continue", "reset", "exit"],
                default="continue"
            )

            if action == 'apply':
                self.apply_modifications()
            elif action == 'continue':
                self.console.print("Continuing the conversation without applying changes.", style="bold yellow")
            elif action == 'reset':
                self.context = self.workflow.reset_chat()
                self.display_output(self.context['project_report'])
                self.console.print("Chat reset. Starting a new conversation with updated project report.", style="bold yellow")
            elif action == 'exit':
                break

    def get_file_contexts(self) -> List[str]:
        file_contexts = []
        while True:
            file_path = self.handle_input("Enter a file path for context (or press Enter to finish)")
            if file_path.strip() == "":
                break
            file_contexts.append(file_path)
        return file_contexts

    def get_image_contexts(self) -> List[str]:
        image_contexts = []
        while True:
            image_path = self.handle_input("Enter an image path for context (or press Enter to finish)")
            if image_path.strip() == "":
                break
            image_contexts.append(image_path)
        return image_contexts

    def display_ai_response(self):
        ai_response = self.context['messages'][-1]['content']
        self.display_output(ai_response.strip())
        total_tokens = token_counter(model=self.model_config['project_modification_workflow']['project_modification_task']['model'], messages=self.context['messages'])
        user_tokens = token_counter(model=self.model_config['project_modification_workflow']['project_modification_task']['model'], text=self.context['messages'][-2]['content'])
        assistant_tokens = token_counter(model=self.model_config['project_modification_workflow']['project_modification_task']['model'], text=self.context['messages'][-1]['content'])
        self.console.print(f"[bold]Total tokens used:[/bold] {total_tokens} | [bold]User tokens:[/bold] {user_tokens} | [bold]Assistant tokens:[/bold] {assistant_tokens}")

    def display_proposed_modifications(self):
        if 'modifications' in self.context:
            self.console.print("Proposed modifications:")
            for mod in self.context['modifications']:
                operation = mod['operation'].capitalize()
                file_path = mod['file_path']
                self.console.print(f"- {operation} file: {file_path}")
                
                if operation in ['Edit', 'Create'] and 'content' in mod:
                    syntax = Syntax(mod['content'], "python", theme="monokai")
                    self.console.print(Panel(syntax, title=f"Content for {file_path}", border_style="green"))
                elif operation == 'Move' and 'content' in mod:
                    self.console.print(f"  Destination path: {mod['content']}")

    def apply_modifications(self):
        with self.console.status("[bold green]Applying changes..."):
            diffs = self.workflow.apply_modifications(self.context)
        self.console.print("Changes applied successfully!", style="bold green")
        self.display_diffs(diffs)

    def display_diffs(self, diffs: List[Dict[str, Any]]) -> None:
        self.console.print("\n[bold]Detailed changes:[/bold]")

        for diff in diffs:
            operation = diff['operation']
            file_path = diff['file_path']

            if operation == 'edit':
                self.console.print(f"\n[bold yellow]Edited file:[/bold yellow] {file_path}")
                self.console.print("\n[italic]Diff between current and new content:[/italic]")
                self.print_diff(diff['diff']['current_vs_new'])

    def print_diff(self, diff_lines: List[str]) -> None:
        diff_text = '\n'.join(diff_lines)
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def display_output(self, output):
        self.console.print(Panel(Markdown(output), title="Current Project State", border_style="blue"))

    def handle_input(self, prompt, **kwargs):
        if 'choices' in kwargs:
            return Prompt.ask(prompt, **kwargs)
        else:
            self.console.print(prompt)
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            return "\n".join(lines)

    def resume_workflow(self):
        with self.console.status("[bold green]Resuming workflow..."):
            last_step = self.progress_service.get_last_step()
            self.context = self.progress_service.resume_from_last_step()
            if 'project_report' not in self.context:
                self.context['project_report'] = self.workflow.generate_project_report()

        self.console.print(f"[yellow]Resuming from step: {last_step}[/yellow]")
        self.run_project_modification_workflow()