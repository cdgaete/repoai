# src/repoai/server/components.py

import tkinter as tk
import time
import subprocess
from tkinter import filedialog, simpledialog
import os
import json
import streamlit as st
from pathlib import Path
import shutil
from ..config import Config
from ..LLM.llm_client import LLMManager
from ..utils.markdown_generator import MarkdownGenerator
from ..core.project_creator import ProjectCreator
from ..core.llm_expert_chat import LLMExpertChat
from ..utils.exceptions import OverloadedError, ConnectionError
from ..utils.git_operations import GitOperations
from ..utils.config_manager import config_manager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    root.destroy()
    return folder_path if folder_path else None

def create_folder():
    root = tk.Tk()
    root.withdraw()
    selected_dir = filedialog.askdirectory(title="Select directory to host the new folder")
    if not selected_dir:
        return None
    
    folder_name = simpledialog.askstring("Folder name", "Enter the name for the new folder:")
    if not folder_name:
        return None

    new_folder_path = os.path.join(selected_dir, folder_name)
    try:
        os.makedirs(new_folder_path, exist_ok=False)
        return new_folder_path
    except OSError as e:
        st.error(f"Failed to create folder: {str(e)}")
        logger.error(f"Failed to create folder: {str(e)}")
        return None
    finally:
        root.destroy()

def initialize_session_state():
    if "messages_create" not in st.session_state:
        st.session_state.messages_create = []
    if "project_path" not in st.session_state:
        st.session_state.project_path = None
    if "ai_client" not in st.session_state:
        st.session_state.ai_client = LLMManager()
    if "markdown_generator" not in st.session_state:
        st.session_state.markdown_generator = MarkdownGenerator()
    if "project_creator" not in st.session_state:
        st.session_state.project_creator = None
    if "show_repo_content" not in st.session_state:
        st.session_state.show_repo_content = False
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None
    if "project_creation_mode" not in st.session_state:
        st.session_state.project_creation_mode = None
    if "project_description_prompt" not in st.session_state:
        st.session_state.project_description_prompt = ""
    if "creating_project" not in st.session_state:
        st.session_state.creating_project = False
    if "llm_expert_chat" not in st.session_state:
        st.session_state.llm_expert_chat = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "file_suggestions" not in st.session_state:
        st.session_state.file_suggestions = []
    if "selected_operations" not in st.session_state:
        st.session_state.selected_operations = []
    if "git_operations" not in st.session_state:
        st.session_state.git_operations = GitOperations()
    if "user_input" not in st.session_state:
        st.session_state.user_input = None

def render_project_creation():
    st.header("Create New Project")

    if st.session_state.project_creation_mode == "Create Empty Project":
        try:
            with st.spinner("Creating empty project... This may take a moment."):
                st.session_state.project_creator.create_empty_project(st.session_state.project_path)
            logger.info(f"New project created: {st.session_state.project_path.name}")
            st.success(f"Empty project created successfully at: {st.session_state.project_path.name}")
            st.session_state.creating_project = False
            st.session_state.project_creator = None
            st.session_state.project_creation_mode = None
        except Exception as e:
            cancel_or_fail()
            st.error(f"Failed to create empty project: {str(e)}")
        finally:
            st.rerun()

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
            if st.session_state.project_path and st.session_state.project_description_prompt:
                try:
                    with st.spinner("Creating project based on description... This may take a moment."):
                        st.session_state.project_creator.create_project_from_description(st.session_state.project_path, st.session_state.project_description_prompt)
                    st.success(f"Project created successfully at: {st.session_state.project_path.name}")
                    st.session_state.creating_project = False
                    st.session_state.project_description_prompt = None
                    st.session_state.messages_create = []
                    st.session_state.project_creator = None
                    st.session_state.project_creation_mode = None
                except Exception as e:
                    st.error(f"Failed to create project: {str(e)}")
                finally:
                    st.rerun()
            else:
                st.error("Please enter a valid project name and ensure there's a project description prompt.")

    if st.button("Cancel Project Creation"):
        cancel_or_fail()


def cancel_or_fail():
    st.session_state.creating_project = False
    shutil.rmtree(st.session_state.project_path)
    st.session_state.project_path = None
    st.session_state.project_creator = None
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
    if st.session_state.project_path:

        if "ignore_patterns" not in st.session_state:
            st.session_state.ignore_patterns = MarkdownGenerator._read_ignore_file(st.session_state.project_path)

        if st.sidebar.button("Restart Conversation"):
            st.session_state.chat_messages = []
            st.session_state.file_suggestions = []
            st.session_state.llm_expert_chat = None
            st.session_state.user_input = None
            st.toast("Conversation restarted and project summary reloaded.")
            time.sleep(1.5)
            st.rerun()

        st.session_state.show_repo_content = st.sidebar.checkbox("Show Repository Content", value=st.session_state.get("show_repo_content", False))
        st.session_state.include_line_numbers = st.sidebar.checkbox("Include Line Numbers", value=st.session_state.get("include_line_numbers", False))

        repo_str = st.session_state.markdown_generator.generate_repo_content(
            st.session_state.project_path,
            st.session_state.include_line_numbers,
            st.session_state.ignore_patterns,
        )
        st.sidebar.download_button(
            label="Download Repository Content",
            data=repo_str,
            file_name="repo_content.md",
            mime="text/markdown",
            key="download_repo_content_main"
        )

        st.sidebar.write("---")

        st.sidebar.subheader("Ignore Patterns")
        st.sidebar.write(":orange[Save the changes before the chat session starts.]")
        
        if st.session_state.ignore_patterns:
            st.sidebar.text_area("Current ignore patterns:", value="\n".join(st.session_state.ignore_patterns), disabled=True, height=150, help="It reads .repoai/.repoaiignore file. If not found, it loads the default ignore patterns. To customize, you can here add new ignore patterns or remove existing ones. To persist, save the changes and restart the chat session.")
        else:
            st.sidebar.info("No ignore patterns set.")
        
        new_pattern = st.sidebar.text_input("Add new ignore pattern")
        if st.sidebar.button("Add Pattern"):
            if new_pattern and new_pattern not in st.session_state.ignore_patterns:
                st.session_state.ignore_patterns.append(new_pattern)
                st.sidebar.success(f"Added: {new_pattern}")
            elif new_pattern in st.session_state.ignore_patterns:
                st.sidebar.warning(f"{new_pattern} is already in the ignore list.")
            else:
                st.sidebar.warning("Please enter a valid pattern.")
        
        if st.session_state.ignore_patterns:
            pattern_to_remove = st.sidebar.selectbox("Select pattern to remove", [""] + st.session_state.ignore_patterns)
            if st.sidebar.button("Remove Pattern"):
                if pattern_to_remove:
                    st.session_state.ignore_patterns.remove(pattern_to_remove)
                    st.sidebar.success(f"Removed: {pattern_to_remove}")
        
        if st.sidebar.button("Save Ignore Patterns"):
            ignore_file_path = Config.get_ignore_file_path(st.session_state.project_path)
            with open(ignore_file_path, "w") as f:
                for pattern in st.session_state.ignore_patterns:
                    f.write(f"{pattern}\n")
            st.sidebar.success(f"Ignore patterns saved to {ignore_file_path.name}")

        st.sidebar.write("---")

        render_token_counts()

        chat_edition_session()

        if st.session_state.show_repo_content:
            st.subheader("Repository Content")
            repo_dict = st.session_state.markdown_generator.generate_repo_container(
                st.session_state.project_path,
                False,
                st.session_state.ignore_patterns
            )
            
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
                    st.code(file_content,language=file_language, line_numbers=st.session_state.include_line_numbers)
    else:
        st.info("Please select a project to view its content and chat with the LLM expert.")

def render_settings():
    st.sidebar.header("Settings")

    # Add help section for task prompts
    st.sidebar.subheader("Task Prompts Help")

    with st.sidebar.expander("Global Configuration"):
        for provider in config_manager.get('providers', {}):
            st.subheader(f"{provider.capitalize()} Configuration")
            api_key = st.text_input(f"{provider.capitalize()} API Key", value=Config.get_provider_api_key(provider), type="password")
            api_host = st.text_input(f"{provider.capitalize()} API Host", value=Config.get_provider_api_host(provider))
            if st.button(f"Save {provider.capitalize()} Config"):
                config_manager.set(f'providers.{provider}.api_key', api_key)
                config_manager.set(f'providers.{provider}.api_host', api_host)
                st.success(f"{provider.capitalize()} configuration saved.")

    with st.sidebar.expander("System Prompts"):
        for prompt_key, prompt_value in config_manager.get('system_prompts', {}).items():
            new_prompt = st.text_area(f"Edit {prompt_key}", value=prompt_value, height=150)
            if new_prompt != prompt_value:
                config_manager.set(f'system_prompts.{prompt_key}', new_prompt)
                st.success(f"Updated {prompt_key}.")

    with st.sidebar.expander("Task-Model Mapping"):
        st.subheader("Creation Tasks")
        for task in ["PROJECT_DESCRIPTION_CHAT", "PROJECT_CREATOR", "FORMAT_DIRECTORY_STRUCTURE", "FORMAT_FILE_CONTENTS"]:
            current_model = config_manager.get(f'task_model_mapping.{task}')
            available_models = list(config_manager.get('MODELS_PROVIDER_MAPPING', {}).keys())
            
            if current_model not in available_models:
                current_model = available_models[0] if available_models else None
            
            new_model = st.selectbox(
                f"Model for {task}",
                options=available_models,
                index=available_models.index(current_model) if current_model in available_models else 0
            )
            if new_model != current_model:
                config_manager.set(f'task_model_mapping.{task}', new_model, project_specific=True)
                st.success(f"Updated model for {task}.")

        st.subheader("Edition Tasks", help="Set a model to global configuration if you want to use it for all projects.")
        for task in ["EXPERT_CHAT", "EDIT_FILE"]:
            current_model = config_manager.get(f'task_model_mapping.{task}')
            available_models = list(config_manager.get('MODELS_PROVIDER_MAPPING', {}).keys())
            
            if current_model not in available_models:
                current_model = available_models[0] if available_models else None
            
            new_model = st.selectbox(
                f"Model for {task}",
                options=available_models,
                index=available_models.index(current_model) if current_model in available_models else 0
            )
            if new_model != current_model:
                config_manager.set(f'task_model_mapping.{task}', new_model, project_specific=True)
                st.success(f"Updated model for {task}.")

    if st.session_state.project_path:
        with st.sidebar.expander("Project-Specific Configuration"):
            st.write("Override global settings for this project:")
            for task, model in config_manager.get('task_model_mapping', {}).items():
                new_model = st.text_input(f"Project Model for {task}", value=model)
                if new_model != model:
                    config_manager.set(f'task_model_mapping.{task}', new_model, project_specific=True)
                    st.success(f"Updated project-specific model for {task}.")

    if st.sidebar.button("Reset to Default Configuration"):
        config_manager.reset_to_default()
        st.sidebar.success("Configuration reset to default values.")

    st.sidebar.markdown("---")
    st.sidebar.info("RepoAI - A repository assistant.\nIt helps you create and edit your projects with ease.\n\nMade with ❤️ to the open source community by [Carlos Gaete](https://github.com/cdgaete)\n\nContribute to the project on [GitHub](https://github.com/cdgaete/repoai)")


def render_sidebar():
    st.sidebar.title("RepoAI")

    st.sidebar.text_input("Project Path", value=st.session_state.get("project_path", ""), disabled=True)
    
    st.sidebar.subheader("Create Project")
    project_creation_options = ["Create Empty Project", "Describe Project"]
    st.session_state.project_creation_mode = st.sidebar.selectbox("Select Project Creation Mode", project_creation_options)

    if st.sidebar.button("Start Project Creation"):
        st.session_state.creating_project = True
        if project_path:= create_folder():
            st.session_state.project_path = Path(project_path)
            st.session_state.project_creator = ProjectCreator(st.session_state.ai_client, st.session_state.git_operations)
            st.session_state.llm_expert_chat = None
            Config.load_token_counts()
            st.rerun()
        else:
            st.error("Project folder not created. Please finalize folder creation.")

    st.sidebar.write("---")

    st.sidebar.subheader("Select Project")
    
    if st.sidebar.button("Select Project"):
        if project_path := select_folder():
            st.session_state.project_path = Path(project_path)
            st.session_state.llm_expert_chat = None
            Config.load_token_counts()
            st.rerun()
        else:
            st.error("Project path not selected. Please finalize folder selection.")

    st.sidebar.write("---")

def find_docker_compose_files(project_path):
    compose_files = list(project_path.glob('docker-compose*.yml'))
    compose_files.extend(project_path.glob('docker-compose*.yaml'))
    return [file.name for file in compose_files]

def render_docker_compose_section():
    st.sidebar.header("Docker Compose")
    if st.session_state.project_path:
        if st.sidebar.button("Add Docker Prompt"):
            docker_prompt = Config.get_prompt("CREATE_DOCKERFILES_PROMPT")
            chat_update(docker_prompt, is_docker_prompt=True)
            st.rerun()

        compose_files = find_docker_compose_files(st.session_state.project_path)
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
            cwd=st.session_state.project_path,
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
        down_result = subprocess.run(
            ['docker', 'compose', '-f', file_name, 'down'],
            cwd=st.session_state.project_path,
            capture_output=True,
            text=True
        )
        if down_result.returncode != 0:
            st.sidebar.error(f"Error stopping Docker Compose: {down_result.stderr}")
            return

        up_result = subprocess.run(
            ['docker', 'compose', '-f', file_name, 'up', '--build', '-d'],
            cwd=st.session_state.project_path,
            capture_output=True,
            text=True
        )
        if up_result.returncode == 0:
            st.sidebar.success(f"Docker Compose file '{file_name}' rebuilt and rerun successfully.")
        else:
            st.sidebar.error(f"Error rebuilding and rerunning Docker Compose: {up_result.stderr}")
    except Exception as e:
        st.sidebar.error(f"An error occurred: {str(e)}")

def chat_edition_session():
    st.info("Avoid long conversations; sometimes it's best to restart the chat to provide a fresh view of the project's state. The chat has a history, but the AI can get confused with longer conversations.")
    st.subheader("Chat with the AI assistant")
    if st.session_state.llm_expert_chat is None:
        st.session_state.llm_expert_chat = LLMExpertChat(st.session_state.ai_client, st.session_state.markdown_generator, st.session_state.git_operations, st.session_state.project_path)

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.user_input:
        prompt = st.chat_input(f"Ask about the project content or request changes/suggestions/improvements.")
        if prompt:
            chat_update(prompt)
    
    if st.session_state.file_suggestions:
        st.subheader("File Operation Suggestions")
        selected_operations = st.multiselect(
            "Select operations to apply",
            options=[suggestion[0] for suggestion in st.session_state.file_suggestions],
            format_func=lambda x: next(suggestion[1] for suggestion in st.session_state.file_suggestions if suggestion[0] == x)
        )

        if st.button("Apply Selected Operations"):
            st.session_state.llm_expert_chat.apply_file_operations(selected_operations)
            st.toast("Selected operations applied successfully!")
            st.session_state.file_suggestions = []
            time.sleep(1.0)
            st.rerun()
    
    if st.session_state.user_input:
        prompt = st.text_area("Edit Docker Generation Prompt:", value=st.session_state.get("user_input", ""), height=150)
        if st.button("Send Prompt"):
            chat_update(prompt)
            st.session_state.user_input = None

def chat_update(prompt, is_docker_prompt=False):
    if is_docker_prompt:
        st.session_state.chat_messages.append({"role": "system", "content": prompt})
    else:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user" if not is_docker_prompt else "system"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.llm_expert_chat.chat(prompt)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.markdown(response)

        st.session_state.file_suggestions = st.session_state.llm_expert_chat.get_file_suggestions()

    if is_docker_prompt:
        st.session_state.user_input = None
