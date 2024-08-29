import argparse
import json
from pathlib import Path
from repoai import initialize, ProjectManager
from repoai.core.plugin_manager import PluginManager
from repoai.services.markdown_service import MarkdownService
from repoai.components.interfaces.project_generation_interface import ProjectGenerationInterface
from repoai.components.interfaces.project_modification_interface import ProjectModificationInterface
from repoai.utils.logger import get_logger

config = initialize()

logger = get_logger(__name__)



def main():
    parser = argparse.ArgumentParser(description="RepoAI - AI-assisted repository content creation")
    parser.add_argument('action', choices=['init', 'report', 'plugin', 'create', 'edit'], help="Action to perform")
    parser.add_argument('--project_path', '-p', type=Path, help="Path to the project directory (for all actions except 'plugin')")
    parser.add_argument('--output', help="Output directory for the report (for 'report' action) default: current directory")
    parser.add_argument('--interface', help="Name of the interface to run (for 'plugin' action)")
    parser.add_argument('--model_config', help="Path to model config JSON file to use (for 'plugin', 'create', and 'edit' actions)")
    args = parser.parse_args()

    if args.action in ['create', 'edit']:
        handle_project_actions(args)
    elif args.action == 'init':
        handle_init_action(args)
    elif args.action == 'report':
        handle_report_action(args)
    elif args.action == 'plugin':
        handle_plugin_action(args)

def load_model_config(model_config_path):
    model_config_path = Path(model_config_path)
    if not model_config_path.exists():
        raise FileNotFoundError(f"Model config file not found: {model_config_path}")
    with open(model_config_path, 'r') as f:
        model_config = json.load(f)
    return model_config

def handle_project_actions(args):
    assert args.project_path is not None, "Project path must be specified\nUsage: repoai <action> --project_path <path_to_project>"

    if args.model_config:
        model_config = load_model_config(args.model_config)
    else:
        model_config = {}
    if args.action == 'create':
        project_manager = ProjectManager(args.project_path, create_if_not_exists=True, error_if_exists=False)
        generation_interface = ProjectGenerationInterface(project_manager, model_config)
        generation_interface.run()
        # Transition to modification interface
        logger.info("\nProject created successfully. Transitioning to modification mode...\n")
        modification_interface = ProjectModificationInterface(project_manager, model_config)
        modification_interface.run()
    
    elif args.action == 'edit':        
        project_manager = ProjectManager(args.project_path, create_if_not_exists=False, error_if_exists=False)
        modification_interface = ProjectModificationInterface(project_manager, model_config)
        modification_interface.run()


def handle_init_action(args):
    assert args.project_path is not None, "Project path must be specified\nUsage: repoai <action> --project_path <path_to_project>"

    project_manager = ProjectManager(args.project_path, create_if_not_exists=True, error_if_exists=True)
    logger.info(f"Project '{project_manager.project_name}' initialized successfully.")
    logger.info("The following files were created:")
    logger.info("  .gitignore")
    logger.info("  .repoai/.repoaiignore")
    logger.info("An initial Git commit was made.")


def handle_report_action(args):
    assert args.project_path is not None, "Project path must be specified\nUsage: repoai <action> --project_path <path_to_project>"

    project_manager = ProjectManager(args.project_path, create_if_not_exists=False, error_if_exists=False)
    markdown_service = MarkdownService(project_manager.project_path, project_manager.config.get('repoai_ignore_file'))
    # Generate the report
    report_content = markdown_service.generate_markdown_compilation("")
    # Determine the output location
    output_dir = Path(args.output) if args.output else Path.cwd()
    output_file = output_dir / f"{project_manager.project_name}_report.md"
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    # Write the report to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"Project report for '{project_manager.project_name}' generated successfully.")
    logger.info(f"Report saved to: {output_file}")


def handle_plugin_action(args):
    if args.model_config:
        model_config = load_model_config(args.model_config)
    else:
        model_config = {}
    
    plugin_manager = PluginManager(config.get('plugin_dir'))
    plugin_manager.discover_plugins()

    if not args.interface:
        logger.info("Available plugin interfaces:")
        for name in plugin_manager.get_interfaces().keys():
            logger.info(f"  - {name}")
        logger.info("\nUsage:\nrepoai plugin --project_path <path_to_project> --interface <interface_name>")
    else:
        assert args.project_path is not None, "Project path must be specified\nUsage: repoai <action> --project_path <path_to_project>"
        project_manager = ProjectManager(args.project_path, create_if_not_exists=True, error_if_exists=False)
        interface_class = plugin_manager.get_interfaces().get(args.interface)
        if interface_class:
            interface = interface_class(project_manager, model_config)
            interface.run()
        else:
            logger.info(f"Interface '{args.interface}' not found.")

if __name__ == "__main__":
    main()