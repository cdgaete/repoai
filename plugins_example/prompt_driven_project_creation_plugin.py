from pathlib import Path
from typing import Dict, Any, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from repoai.components.components_base import BaseInterface, BaseWorkflow, BaseTask
from repoai.core.project_manager import ProjectManager
from repoai.services.progress_service import ProgressService
from repoai.services.llm_service import LLMService
from repoai.utils.common_utils import extract_outer_code_block

class ProjectDescriptionandStructureTask(BaseTask):
    def __init__(self, llm_service: LLMService, progress_service: ProgressService, model_config: Dict[str, Any] = None):
        self.llm_service = llm_service
        self.progress_service = progress_service
        self.model_config = model_config or {}

    def execute(self, context: dict) -> None:
        self._process_chat(context)

    def _process_chat(self, context: dict):
        messages = context.get('messages', [])
        if not messages:
            system_message = """You are an AI assistant specialized in creating detailed project descriptions called 'project prompts'. Follow these guidelines:

Project Prompt Creation:
   - Write the project prompt in an instructive style.
   - Enclose the project prompt with triple backticks.
   - After each interaction, update the project prompt to reflect the latest information.
   - Aside from the project prompt, ask focused questions to gather specific information about the project.
   - Provide suggestions to enhance the project prompt.
   - Ensure the prompt comprehensively describes the project, including its purpose and main features.

Remember to tailor your responses to the specific project requirements and user feedback.
"""

            messages = [
                {"role": "system", "content": system_message},
            ]
            context['messages'] = messages

        user_input = context.get('user_input')
        file_contexts = context.get('file_contexts', [])
        stage = context.get('stage', 'description')
        
        if user_input:
            content = user_input
            if file_contexts:
                content += "\n\nAdditional Information for Contexts:\n"
            for file_context in file_contexts:
                content += f"\nFile: {file_context['file_path']}\nContent:\n```\n{file_context['content']}\n```"
            messages.append({"role": "user", "content": content})
        else:
            if messages[-1]['role'] == 'user':
                pass
            else:
                if stage == 'description':
                    raise Exception("No user input provided")
                elif stage == 'structure':
                    user_input = """Okay, now create the project structure based on the last updated project prompt. Consider the following guidelines:
1. Project Structure Development:
   - Format the structure as a tree-like representation of directories and files.
   - Enclose the structure with triple backticks.
   - Represent the root directory as a single forward slash (/).
   - Include only text-based files. Omit binary files, audio, video, images (except SVG), and PDF files.
   - From now on, update the structure after each relevant interaction with the user.

2. Structure Explanation:
   - Provide a clear explanation of the chosen structure and its components.
   - Update the explanation alongside the structure after relevant interactions.

Example of a tree-like project structure:

```markdown
/
├── src/
│   ├── components/
│   │   └── Header.js
│   ├── pages/
│   │   └── Home.js
│   └── utils/
│       └── helpers.js
├── tests/
│   └── unit/
│       └── helpers.test.js
├── docs/
│   └── API.md
├── README.md
└── package.json
```
                    
"""
                                
                    messages.append({"role": "user", "content": user_input})
            
        response = self.llm_service.get_completion(messages=messages, **self.model_config)

        lang, prompt = extract_outer_code_block(response.content)
        if response.content:
            if stage == 'description':
                if not prompt:
                    assistant_content = "\n\n**Description not found in triple backticks**"
                else:
                    assistant_content = prompt
            elif stage == 'structure':
                if not prompt:
                    assistant_content = "\n\n**Structure not found in triple backticks**"
                else:
                    assistant_content = prompt
        else:
            assistant_content = "No response from assistant"
        assistant_message = {"role": "assistant", "content": response.content if response.content else assistant_content}
        messages.append(assistant_message)

        context['messages'] = messages
        context['user_input'] = ""
        if stage == 'description':
            context['description'] = assistant_content
        elif stage == 'structure':
            context['structure'] = assistant_content
            context['structure_and_explanation'] = response.content

        self.progress_service.save_progress("project_description", context)

class PromptDrivenProjectCreationWorkflow(BaseWorkflow):
    def __init__(self, project_manager: ProjectManager, progress_service: ProgressService, model_config: Dict[str, Any] = None):
        self.project_manager = project_manager
        self.progress_service = progress_service
        self.llm_service = LLMService(project_manager.project_path, project_manager.config)
        
        self.model_config = model_config or {}
        
        self.description_task = ProjectDescriptionandStructureTask(
            self.llm_service, 
            self.progress_service,
            self.model_config.get("project_description_and_structure_task", {})
        )
        self.paths_task = project_manager.get_task("structure_to_paths_task")(
            self.llm_service,
            self.model_config.get("structure_to_paths_task", {})
        )
        self.content_generation_task = project_manager.get_task("file_content_generation_task")(
            self.llm_service, 
            self.progress_service, 
            self.model_config.get("file_content_generation_task", {})
        )

        self.path_generation_history = Path(self.project_manager.config.REPOAI_DIR) / "generation_history.yml"
        self.path_report = Path(self.project_manager.config.REPOAI_DIR) / "report.md"
        self.path_file_paths = Path(self.project_manager.config.REPOAI_DIR) / "file_paths.yml"

    def description_start(self, user_input: str, file_contexts: List[Dict[str, Any]], context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = self.reset_chat_context(context)
        context['user_input'] = user_input
        context['file_contexts'] = file_contexts
        return self.execute_description_task(context)
    
    def execute_description_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.description_task.execute(context)
        self.progress_service.save_progress("project_description", context)
        return context

    def finalize_project(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if "report" not in context:
            project_prompt = context["description"]
            structure_and_explanation = context["structure_and_explanation"]
            report = f"{project_prompt}\n\n{structure_and_explanation}"
            file_contexts = context.get('file_contexts', [])
            additional_context = ""
            for file_context in file_contexts:
                additional_context += f"\nFile: {file_context['file_path']}\nContent:\n```\n{file_context['content']}\n```"
            if additional_context:
                report += f"\n\nAdditional Information for Contexts:\n{additional_context}"
            context['report'] = context.get('report', report)
            self._save_report(context['report'])
        
        if 'file_paths' not in context:
            assert "structure" in context, "Structure not found in context"
            self.paths_task.execute(context)
            self.progress_service.save_progress("paths_generation", context)
            self._save_paths(context['file_paths'])
        self.content_generation_task.execute(context)
        self.progress_service.save_progress("file_content_generation", context)
        self._create_project_files(context['generated_files'])
        self._save_generation_history(context['generation_history'])
        self.progress_service.clear_progress()
        return context


    def _create_project_files(self, generated_files: Dict[str, Tuple[str, str, List[int]]], directories: List[str] = []):
        batch_operations = []
        for file_path, (language, code) in generated_files.items():
            batch_operations.append({'operation': 'create_file', 'file_path': file_path, 'content': code})
        for folder in directories:
            batch_operations.append({'operation': 'create_directory', 'file_path': folder})
        self.project_manager.batch_operations(batch_operations)

    def _save_generation_history(self, generation_history: List[Dict[str, Any]]):
        self.project_manager.file_manager.save_yaml(self.path_generation_history, generation_history)

    def _save_report(self, report: str):
        self.project_manager.file_manager.save_file(self.path_report, report)

    def _save_paths(self, file_paths: List[str]):
        self.project_manager.file_manager.save_yaml(self.path_file_paths, file_paths)

    @staticmethod
    def reset_chat_context(context: dict = None):
        if not context:
            return {
                "messages": [],
                "user_input": "",
                "stage": "description",
            }
        else:
            if context["stage"] == "description":
                context["messages"] = []
                context["user_input"] = ""
            elif context["stage"] == "structure":
                context["messages"] = context['saved_messages']
                context["user_input"] = ""
            return context

class PromptDrivenProjectCreationInterface(BaseInterface):
    def __init__(self, project_manager: ProjectManager, model_config: Dict[str, Any] = {}):
        super().__init__(project_manager, model_config)
        self.console = Console()
        self.progress_service = ProgressService(project_manager.project_path, project_manager.config)
        self.workflow = PromptDrivenProjectCreationWorkflow(project_manager, self.progress_service, model_config.get("prompt_driven_project_creation_workflow", {}))
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
        if self.project_manager.file_manager.file_exists(self.workflow.path_file_paths) and self.project_manager.file_manager.file_exists(self.workflow.path_report):
            self.console.print("[yellow]Report and file paths found. You can resume the process and start from there.[/yellow]")
            if Confirm.ask("Do you want to start the files generation?"):
                self.context = {}
                self.context["report"] = self.project_manager.file_manager.read_file(self.workflow.path_report)
                self.context["file_paths"] = self.project_manager.file_manager.read_yaml(self.workflow.path_file_paths)
                self.context = self.finalize_project()
                return
        self.context = {}

    def run_project_generation_workflow(self):
        self.context = self.project_description_chat()
        return  # This is the final step of the project generation


    def project_description_chat(self):
        self.console.print("\n[bold green]Starting project description chat...[/bold green]")
        if not self.context.get('description'):
            user_input = Prompt.ask("Please provide a brief description of your project")
            file_contexts = self.get_file_contexts()
            with self.console.status("[bold green]Starting project description chat..."):
                self.context = self.workflow.description_start(user_input, file_contexts, self.context)

        while True:
            self.display_output(self.context['messages'][-1]['content'])
            if self.context["stage"] == "description":
                self.display_output(self.context['description'])
            elif self.context["stage"] == "structure":
                self.display_output(f"```markdown\n{self.context['structure']}\n```")
            choice = self.handle_input(
                "Choice",
                choices=["continue", "apply", "reset", "exit"],
                default="continue"
            )
            if choice == "continue":
                user_input = self.handle_input("You")
                file_contexts = self.get_file_contexts()
                self.context['user_input'] = user_input
                self.context['file_contexts'] = file_contexts
                with self.console.status("[bold green]Thinking..."):
                    self.context = self.workflow.execute_description_task(self.context)
            elif choice == "apply":
                if self.context["stage"] == "description":
                    if "Description not found in triple backticks" in self.context['description']:
                        self.console.print("[yellow]No description captured. Please request a description in backticks.[/yellow]")
                        continue
                    self.context["saved_messages"] = self.context["messages"]
                    self.context['stage'] = "structure"
                    with self.console.status("[bold green]Thinking..."):
                        self.context = self.workflow.execute_description_task(self.context)
                elif self.context["stage"] == "structure":
                    if "Structure not found in triple backticks" in self.context['structure']:
                        self.console.print("[yellow]No structure captured. Please request a structure in backticks.[/yellow]")
                        continue
                    return self.finalize_project()
            elif choice == "reset":
                self.console.print("[yellow]Resetting context...[/yellow]\n")
                user_input = self.handle_input("You")
                file_contexts = self.get_file_contexts()
                with self.console.status("[bold green]Restarting chat..."):
                    self.context = self.workflow.description_start(user_input, file_contexts, self.context)
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
        elif last_step in ["paths_generation", "file_content_generation"]:
            return self.finalize_project()
        else:
            self.console.print("[yellow]Unknown last step. Starting from the beginning.[/yellow]")
            return self.run_project_generation_workflow()

    def display_output(self, output):
        self.console.print(Panel(Markdown(output), title="Assistant", border_style="blue"))

    def handle_input(self, prompt, **kwargs):
        return Prompt.ask(prompt, **kwargs)

    def get_file_contexts(self) -> List[Dict[str, str]]:
        file_contexts = []
        while True:
            file_path = self.handle_input("Enter a file path for context (or press Enter to finish)")
            if file_path.strip() == "":
                break
            content = self.project_manager.read_file(file_path)
            if content:
                file_contexts.append({
                    "file_path": file_path,
                    "content": content
                })
            else:
                self.console.print(f"[yellow]Warning: Could not read file {file_path}[/yellow]")
        return file_contexts

def register_plugin():
    return {
        "tasks": {
            "project_description_and_structure_task": ProjectDescriptionandStructureTask,
        },
        "workflows": {
            "prompt_driven_project_creation_workflow": PromptDrivenProjectCreationWorkflow
        },
        "interfaces": {
            "prompt_driven_project_creation_interface": PromptDrivenProjectCreationInterface
        }
    }            