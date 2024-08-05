# src/repoai/server/app.py

import streamlit as st
from repoai.server.components import (
    initialize_session_state,
    render_sidebar,
    render_project_creation,
    render_repository_content,
    render_docker_compose_section,
    render_settings,
)
from repoai.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    st.set_page_config(page_title="RepoAI", page_icon="🤖", layout="wide")
    
    initialize_session_state()
    
    render_sidebar()
    
    if st.session_state.creating_project:
        render_project_creation()
    elif st.session_state.project_path:
        render_repository_content()
        render_docker_compose_section()
    else:
        st.info("Please select or create a project to get started.")
    
    render_settings()

if __name__ == "__main__":
    main()