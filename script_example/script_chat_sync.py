from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.services.llm_service import LLMService

def main():
    config = initialize()
    project_name = "llm_test"
    root_path = "/path/to/repoai_projects"
    project_path = Path(root_path) / project_name
    project_manager = ProjectManager(project_path, create_if_not_exists=True)
    llm_service = LLMService(project_manager.project_path, config)

    messages = [{"role": "user", "content": "Describe the process of photosynthesis."}]

    response = llm_service.get_completion(messages)
    print("Synchronous response:", response.content)

if __name__ == "__main__":
    main()