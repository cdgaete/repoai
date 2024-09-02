import asyncio
from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.services.llm_service import LLMService

async def main():
    config = initialize()
    project_name = "llm_test"
    root_path = "/path/to/repoai_projects"
    project_path = Path(root_path) / project_name
    project_manager = ProjectManager(project_path, create_if_not_exists=True)
    llm_service = LLMService(project_manager.project_path, config)

    messages = [{"role": "user", "content": "Describe the process of photosynthesis."}]

    print("\nStreaming response:")
    async for chunk in llm_service.get_acompletion(messages):
        print(chunk, end='', flush=True)

if __name__ == "__main__":
    asyncio.run(main())