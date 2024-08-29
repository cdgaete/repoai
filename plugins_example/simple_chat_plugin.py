from typing import Dict, Any
from repoai import ProjectManager
from repoai.components.components_base import BaseTask, BaseWorkflow, BaseInterface
from repoai.services.llm_service import LLMService
from repoai.services.markdown_service import MarkdownService
from repoai.core.project_manager import ProjectManager

# 1. Custom Task
class SimpleChatTask(BaseTask):
    def __init__(self, llm_service: LLMService, model_config: Dict[str, Any] = None):
        self.llm_service = llm_service
        self.model_config = model_config or {}

    def execute(self, context: dict) -> None:
        messages = context.get('messages', [])
        user_input = context.get('user_input', '')
        if not messages:
            system_message = (f"You are an assistant expert in {self.llm_service.project_path}. "
                                "It is a project that you are working on. The project has the following context:"
                                f"\n\n{context['report']}\n\n")
            messages = [
                {"role": "system", "content": system_message},
            ]
            context['messages'] = messages
        if user_input:
            messages.append({"role": "user", "content": user_input})
        else:
            if messages[-1]['role'] == 'user':
                pass
            else:
                raise Exception("No user input provided")
        response = self.llm_service.get_completion(messages=messages, **self.model_config)
        assistant_message = {"role": "assistant", "content": response.content}
        messages.append(assistant_message)
        context['messages'] = messages
        context['last_response'] = response.content

# 2. Custom Workflow
class SimpleChatWorkflow(BaseWorkflow):
    def __init__(self, project_manager: ProjectManager, model_config: Dict[str, Any] = None):
        self.project_manager = project_manager
        self.llm_service = LLMService(project_manager.project_path, project_manager.config)
        self.markdown_service = MarkdownService(project_manager.project_path, project_manager.config.get('repoai_ignore_file'))
        self.model_config = model_config or {}
        self.chat_task = SimpleChatTask(self.llm_service, self.model_config.get('simple_chat_task', {}))

    def execute(self, context: dict) -> dict:
        self.chat_task.execute(context)
        return context

    def reset_chat(self):
        context = {}
        context['messages'] = []
        context['report'] = self.markdown_service.generate_markdown_compilation("")
        return context


# 3. Custom Application Interface
class SimpleChatInterface(BaseInterface):
    def __init__(self, project_manager: ProjectManager, model_config: Dict[str, Any] = {}):
        super().__init__(project_manager, model_config)
        self.workflow = SimpleChatWorkflow(project_manager, model_config.get('simple_chat_workflow', {}))
        self.context = {}

    def run(self):
        print("Welcome to Simple Chat Interface! You can chat with your project.")
        self.manage_context()
        self.main_loop()

    def main_loop(self):
        while True:
            self.handle_input()

    def handle_input(self, prompt="You: "):
        user_input = input(prompt)
        if user_input.lower() == 'exit':
            print("Goodbye!")
            exit(0)
        self.context['user_input'] = user_input
        result = self.workflow.execute(self.context)
        self.display_output(result)

    def handle_name(self, prompt="You: "):
        user_input = input(prompt)
        if user_input.lower() == 'exit':
            print("Goodbye!")
            exit(0)
        return user_input

    def display_output(self, output):
        print("AI:", output['last_response'])

    def manage_context(self):
        self.context = self.workflow.reset_chat()

# 4. Plugin Registration
def register_plugin():
    return {
        "tasks": {"simple_chat_task": SimpleChatTask},
        "workflows": {"simple_chat_workflow": SimpleChatWorkflow},
        "interfaces": {"simple_chat_interface": SimpleChatInterface}
    }