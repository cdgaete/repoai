# src/repoai/server/components.py

import tkinter as tk
import time
import re
import json
import subprocess
from tkinter import filedialog
import streamlit as st
from pathlib import Path
from repoai.config import Config
from repoai.LLM.llm_client import LLMManager
from repoai.utils.git_operations import GitOperations
from repoai.utils.markdown_generator import MarkdownGenerator
from repoai.core.project_creator import ProjectCreator
from repoai.core.llm_expert_chat import LLMExpertChat
from repoai.utils.exceptions import OverloadedError, ConnectionError
from repoai.utils.context_managers import FeatureContext

from repoai.utils.logger import setup_logger

logger = setup_logger(__name__)

def sanitize_docker_tag(tag):
    # Convert to lowercase
    tag = tag.lower()
    # Replace spaces and other invalid characters with dashes
    tag = re.sub(r'[^a-z0-9._-]', '-', tag)
    # Ensure it starts with a letter or number
    if not tag[0].isalnum():
        tag = 'project-' + tag
    return tag

def initialize_session_state():
    if "messages_edition" not in st.session_state:
        st.session_state.messages_edition = []
    if "messages_create" not in st.session_state:
        st.session_state.messages_create = []
    if "project_root_path" not in st.session_state:
        st.session_state.project_root_path = None
    if "current_project_path" not in st.session_state:
        st.session_state.current_project_path = None
    if "ai_client" not in st.session_state:
        st.session_state.ai_client = None
    if "git_operations" not in st.session_state:
        st.session_state.git_operations = None
    if "markdown_generator" not in st.session_state:
        st.session_state.markdown_generator = MarkdownGenerator()
    if "project_creator" not in st.session_state:
        st.session_state.project_creator = None
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "show_repo_content" not in st.session_state:
        st.session_state.show_repo_content = False
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None
    if "project_creation_mode" not in st.session_state:
        st.session_state.project_creation_mode = None
    if "project_description_prompt" not in st.session_state:
        st.session_state.project_description_prompt = ""
    if "create_project_mode" not in st.session_state:
        st.session_state.create_project_mode = False
    if "llm_expert_chat" not in st.session_state:
        st.session_state.llm_expert_chat = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "file_suggestions" not in st.session_state:
        st.session_state.file_suggestions = []
    if "selected_operations" not in st.session_state:
        st.session_state.selected_operations = []

def render_project_selection():
    if st.session_state.project_root_path:
        projects = [d for d in st.session_state.project_root_path.iterdir() if d.is_dir()]
        selected_project = st.sidebar.selectbox("Select a project", ["None Selected"] + [p.name for p in projects])
        
        if selected_project != "None Selected" and not st.session_state.create_project_mode:
            # Check if the selected project is different from the current one
            if selected_project != st.session_state.get("current_project", None):
                # Clear all project-specific variables
                st.session_state.current_project = selected_project
                st.session_state.messages_edition = []
                st.session_state.messages_create = []
                st.session_state.current_project_path = None
                st.session_state.ai_client = None
                st.session_state.git_operations = None
                st.session_state.project_creator = None
                st.session_state.show_repo_content = False
                st.session_state.selected_file = None
                st.session_state.project_description_prompt = ""
                st.session_state.llm_expert_chat = None
                st.session_state.chat_messages = []
                st.session_state.file_suggestions = []
                st.session_state.selected_operations = []

                # Set the new project
                Config.set_current_project(selected_project)
                st.session_state.current_project_path = Config.get_current_project_path()
                
                # Reinitialize components for the new project
                initialize_components()
                
                st.sidebar.success(f"Project '{selected_project}' selected.")
                st.toast("All previous project data has been cleared.")
                time.sleep(.5)
                st.rerun()  # Add this line to force a rerun after project selection
            return True
        else:
            Config.CURRENT_PROJECT_PATH = None
            st.session_state.current_project_path = None
            st.session_state.current_project = None
    else:
        st.warning("Please set a project root path first.")
    return False

def render_project_creation():
    st.header("Create New Project")
    
    # Ensure project_creator is initialized
    if st.session_state.project_creator is None:
        initialize_components()
    
    project_name = st.text_input("Project Name")

    
    if st.session_state.project_creation_mode == "Create Empty Project":
        if st.button("Create Empty Project"):
            if project_name:
                try:
                    with st.spinner("Creating empty project... This may take a moment."):
                        new_project_path = st.session_state.project_creator.create_empty_project(project_name)
                    logger.info(f"New project path: {new_project_path}")  # Add this line
                    st.success(f"Empty project created successfully at: {new_project_path}")
                    st.session_state.current_project_path = new_project_path
                    Config.set_current_project(new_project_path.name)
                    initialize_components()
                    st.session_state.initialized = True
                    st.session_state.create_project_mode = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create empty project: {str(e)}")
            else:
                st.error("Please enter a valid project name.")

    elif st.session_state.project_creation_mode == "Describe Project":
        if "messages_create" not in st.session_state:
            st.session_state.messages_create = []
        
        user_input = st.text_area("Describe your project idea", height=150)
        
        if st.button("Submit Description"):
            if user_input:
                ai_response, messages = st.session_state.project_creator.chat_about_project(user_input, messages=st.session_state.messages_create)
                st.session_state.messages_create = messages
                st.session_state.project_description_prompt = st.session_state.project_creator.get_current_prompt()
            else:
                st.error("Please enter a valid description.")

        for message in st.session_state.messages_create:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("What would you like to do?"):
            ai_response, messages = st.session_state.project_creator.chat_about_project(prompt, messages=st.session_state.messages_create)
            st.session_state.project_description_prompt = st.session_state.project_creator.get_current_prompt()
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                if st.session_state.project_creator:
                    message_placeholder.markdown(ai_response)
                    st.session_state.messages_create = messages
                else:
                    error_message = "Project_creator is not initialized. Please select a project first."
                    message_placeholder.markdown(error_message)
                    st.session_state.messages_create.append({"role": "assistant", "content": error_message})

        st.subheader("Current Project Description Prompt")
        st.markdown(st.session_state.project_description_prompt)
        
        if st.button("Create Project from Description"):
            if project_name and st.session_state.project_description_prompt:
                try:
                    with st.spinner("Creating project based on description... This may take a moment."):
                        new_project_path = st.session_state.project_creator.create_project_from_description(project_name, st.session_state.project_description_prompt)
                    st.success(f"Project created successfully at: {new_project_path}")
                    st.session_state.current_project_path = new_project_path
                    Config.set_current_project(new_project_path.name)
                    initialize_components()
                    st.session_state.initialized = True
                    st.session_state.create_project_mode = False
                    st.session_state.project_description_prompt = None
                    st.session_state.messages_create = []
                    st.session_state.project_creator = ProjectCreator(st.session_state.ai_client)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create project: {str(e)}")
            else:
                st.error("Please enter a valid project name and ensure there's a project description prompt.")

    if st.button("Cancel Project Creation"):
        st.session_state.create_project_mode = False
        st.rerun()

def render_token_counts():
    token_counts = Config.get_token_counts()
    
    st.sidebar.subheader("Token Usage")
    
    if not any(counts for phase in token_counts.values() for counts in phase.values()):
        st.sidebar.write("No tokens used yet.")
    else:
        for phase in ["creation", "edition"]:
            if token_counts[phase]:
                st.sidebar.write(f"**:violet[{phase.capitalize()} Phase]**")
                for model, counts in token_counts[phase].items():
                    if counts["input"] == 0 and counts["output"] == 0:
                        continue
                    st.sidebar.write(f"Model: {model}")
                    st.sidebar.write(f"Input tokens: {counts['input']}")
                    st.sidebar.write(f"Output tokens: {counts['output']}")
    st.sidebar.write("---")

def render_repository_content():
    if st.session_state.current_project_path:
        st.session_state.show_repo_content = st.sidebar.checkbox("Show Repository Content", value=st.session_state.get("show_repo_content", False))
        st.session_state.include_line_numbers = st.sidebar.checkbox("Include Line Numbers", value=st.session_state.get("include_line_numbers", False))

        # Always show the chat interface
        st.subheader("Chat with LLM Expert")
        if st.session_state.llm_expert_chat is None:
            st.session_state.llm_expert_chat = LLMExpertChat(st.session_state.ai_client, st.session_state.markdown_generator)

        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about your project or type 'show content' to view repository content"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            if prompt.lower() == 'show content':
                st.session_state.show_repo_content = True
            else:
                with st.chat_message("assistant"):
                    try:
                        response = st.session_state.llm_expert_chat.chat(prompt, st.session_state.current_project_path.name)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                        st.markdown(response)

                        # Update file suggestions
                        st.session_state.file_suggestions = st.session_state.llm_expert_chat.get_file_suggestions()
                    except ConnectionError as e:
                        st.error(str(e))
                    except OverloadedError as e:
                        st.warning(str(e))
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

        # Display file operation suggestions
        if st.session_state.file_suggestions:
            st.subheader("File Operation Suggestions")
            selected_operations = st.multiselect(
                "Select operations to apply",
                options=[suggestion[0] for suggestion in st.session_state.file_suggestions],
                format_func=lambda x: next(suggestion[1] for suggestion in st.session_state.file_suggestions if suggestion[0] == x)
            )

            if st.button("Apply Selected Operations"):
                try:
                    st.session_state.llm_expert_chat.apply_file_operations(selected_operations)
                    st.toast("Selected operations applied successfully!")
                    time.sleep(1.0)
                    st.rerun()
                except ConnectionError as e:
                    st.error(str(e))
                except OverloadedError as e:
                    st.warning(str(e))
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

        if st.session_state.show_repo_content:
            st.subheader("Repository Content")
            repo_dict = st.session_state.markdown_generator.generate_repo_container(st.session_state.current_project_path, False)
            
            with st.expander("Repository Structure"):
                st.code(repo_dict["__tree__"]["content"], language="markdown")

            file_list = [key for key in repo_dict.keys() if key != "__tree__"]
            st.session_state.selected_file = st.selectbox("Select a file to view", ["None"] + file_list)

            if st.session_state.selected_file != "None":
                st.subheader(f"File: {st.session_state.selected_file}")
                file_content = repo_dict[st.session_state.selected_file]["content"]
                file_language = repo_dict[st.session_state.selected_file]["language"]
                
                if file_language == "markdown":
                    st.markdown(file_content, unsafe_allow_html=True)
                else:
                    st.code(file_content, language=file_language, line_numbers=st.session_state.include_line_numbers)

        # Add download button for repository content with a unique key
        repo_str = st.session_state.markdown_generator.generate_repo_content(st.session_state.current_project_path, st.session_state.include_line_numbers)
        st.sidebar.download_button(
            label="Download Repository Content",
            data=repo_str,
            file_name="repo_content.md",
            mime="text/markdown",
            key="download_repo_content_main"
        )
        render_token_counts()
    else:
        st.info("Please select a project to view its content and chat with the LLM expert.")

def render_settings():
    st.sidebar.header("Settings")

    with st.sidebar.expander("Expand"):
        for task, model in Config.TASK_MODEL_MAPPING.items():
            st.session_state[task] = st.selectbox(f"Select Model for {task}", [model] + [md for md in Config.MODELS_PROVIDER_MAPPING if md != model], index=0)
            Config.set_task_model(task, st.session_state[task])

    st.sidebar.markdown("---")
    st.sidebar.info("RepoAI - Powered by Anthropic's Claude")

def initialize_components():
    try:
        if st.session_state.project_root_path is None:
            st.error("Project root path is not set. Please select a project root path first.")
            return False

        Config.initialize_paths(st.session_state.project_root_path)
        
        st.session_state.git_operations = GitOperations()
        
        if st.session_state.ai_client is None:
            st.session_state.ai_client = LLMManager(Config.get_project_root_path())
        
        st.session_state.project_creator = ProjectCreator(st.session_state.ai_client)
        
        # Load token counts (this will create an empty structure if no project is selected)
        Config.load_token_counts()
        
        st.toast("All components initialized successfully")
        time.sleep(.5)
        return True
    except Exception as e:
        st.error(f"Failed to initialize components: {str(e)}")
        return False

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    root.destroy()
    return folder_path if folder_path else None

def render_sidebar():
    st.sidebar.title("RepoAI")
    
    project_root_path = st.sidebar.text_input("Project Root Path", value=st.session_state.get("project_root_path", ""))
    
    if st.sidebar.button("Select Project Root Path"):
        project_root_path = select_folder()
        if project_root_path:
            st.session_state.project_root_path = Path(project_root_path)
            if initialize_components():
                st.session_state.initialized = True
                st.rerun()
    
    if project_root_path:
        st.session_state.project_root_path = Path(project_root_path)
        if not st.session_state.initialized:
            if initialize_components():
                st.session_state.initialized = True
                st.rerun()

    st.sidebar.header("Project Creation")
    project_creation_options = ["Create Empty Project", "Describe Project"]
    st.session_state.project_creation_mode = st.sidebar.selectbox("Select Project Creation Mode", project_creation_options)

    if st.sidebar.button("Start Project Creation"):
        st.session_state.create_project_mode = True

def find_docker_compose_files(project_path):
    compose_files = list(project_path.glob('docker-compose*.yml'))
    compose_files.extend(project_path.glob('docker-compose*.yaml'))
    return [file.name for file in compose_files]

def render_docker_compose_section():
    st.sidebar.header("Docker Compose")
    if st.session_state.current_project_path:
        compose_files = find_docker_compose_files(st.session_state.current_project_path)
        if compose_files:
            selected_file = st.sidebar.selectbox("Select Docker Compose file", compose_files)
            col1, col2 = st.sidebar.columns(2)
            if col1.button("Run Docker Compose"):
                run_docker_compose(selected_file)
            if col2.button("Rebuild & Rerun"):
                rebuild_and_rerun_docker_compose(selected_file)
        else:
            st.sidebar.info("No Docker Compose files found in the project root.")
    else:
        st.sidebar.info("Please select a project first.")

def run_docker_compose(file_name):
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', file_name, 'up', '-d'],
            cwd=st.session_state.current_project_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            st.sidebar.success(f"Docker Compose file '{file_name}' executed successfully.")
        else:
            st.sidebar.error(f"Error executing Docker Compose file: {result.stderr}")
    except Exception as e:
        st.sidebar.error(f"An error occurred: {str(e)}")

def rebuild_and_rerun_docker_compose(file_name):
    try:
        # Run docker-compose down
        down_result = subprocess.run(
            ['docker', 'compose', '-f', file_name, 'down'],
            cwd=st.session_state.current_project_path,
            capture_output=True,
            text=True
        )
        if down_result.returncode != 0:
            st.sidebar.error(f"Error stopping Docker Compose: {down_result.stderr}")
            return

        # Run docker-compose up --build -d
        up_result = subprocess.run(
            ['docker', 'compose', '-f', file_name, 'up', '--build', '-d'],
            cwd=st.session_state.current_project_path,
            capture_output=True,
            text=True
        )
        if up_result.returncode == 0:
            st.sidebar.success(f"Docker Compose file '{file_name}' rebuilt and rerun successfully.")
        else:
            st.sidebar.error(f"Error rebuilding and rerunning Docker Compose: {up_result.stderr}")
    except Exception as e:
        st.sidebar.error(f"An error occurred: {str(e)}")