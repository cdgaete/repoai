# src/repoai/server/app.py

import streamlit as st
from repoai.server.components import (
    initialize_session_state,
    render_sidebar,
    render_project_selection,
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
    
    if st.session_state.create_project_mode:
        render_project_creation()
    else:
        project_selected = render_project_selection()
        if project_selected:
            render_repository_content()
            render_docker_compose_section()
    
    render_settings()

if __name__ == "__main__":
    main()