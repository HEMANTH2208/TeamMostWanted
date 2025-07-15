# app.py
import os
import shutil
import tempfile
import json
import subprocess

from flask import Flask, request, jsonify, render_template
from git_operations import clone_repo
from llm_analysis import analyze_code_with_llm
from docker_manager import generate_dockerfile, build_docker_image, run_docker_tests

# --- Git Executable Configuration ---
git_executable_path = r"C:\Program Files\Git\bin\git.exe"
if not os.path.exists(git_executable_path):
    raise RuntimeError(f"Error: Git executable not found at {git_executable_path}.")
else:
    os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = git_executable_path
    print(f"Git executable path set to: {git_executable_path}")

# --- Flask App Setup ---
app = Flask(__name__)

# --- Orchestration Function ---
def orchestrate_analysis(repo_url: str) -> str:
    report = []
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        report.append(f"Starting analysis for: {repo_url}\n")
        report.append(f"Temporary directory created at: {temp_dir}\n")

        success, msg = clone_repo(repo_url, temp_dir)
        report.append(f"Repository Cloning: {'SUCCESS' if success else 'FAILED'} - {msg}\n")
        if not success:
            return "\n".join(report)

        report.append("\n--- AI Code Analysis ---\n")
        llm_analysis_results = []
        exclude_dirs = ['.git', 'node_modules', '__pycache__', '.venv', 'build', 'dist', '.idea', '.vscode']

        for root, dirs, files in os.walk(temp_dir, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith((
                    '.js', '.py', '.java', '.ts', '.go', '.rb', '.cs', '.php', '.html', '.css',
                    '.json', '.xml', '.yml', '.yaml', '.md')) and os.path.getsize(os.path.join(root, file)) < 200 * 1024:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, temp_dir)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        llm_success, llm_msg = analyze_code_with_llm(content, relative_path)
                        if llm_success:
                            llm_analysis_results.append(f"File: {relative_path}\n{llm_msg}\n")
                        else:
                            llm_analysis_results.append(f"File: {relative_path}\nError analyzing: {llm_msg}\n")
                    except Exception as e:
                        llm_analysis_results.append(f"File: {relative_path}\nCould not read file or error during analysis: {e}\n")

        if llm_analysis_results:
            report.extend(llm_analysis_results)
        else:
            report.append("No suitable code files found for LLM analysis or all files skipped.\n")

        report.append("\n--- Dockerization ---\n")
        success, dockerfile_msg = generate_dockerfile(temp_dir)
        report.append(f"Dockerfile Generation: {'SUCCESS' if success else 'FAILED'} - {dockerfile_msg}\n")
        if not success:
            return "\n".join(report)

        image_name = f"audited-{os.path.basename(temp_dir).lower()}"
        success, image_tag, build_logs = build_docker_image(temp_dir, image_name)
        report.append(f"Docker Image Build: {'SUCCESS' if success else 'FAILED'}\n")
        report.append(f"Build Logs:\n{build_logs}\n")
        if not success:
            return "\n".join(report)
        report.append(f"Image Tag: {image_tag}\n")

        report.append("\n--- Automated Testing ---\n")
        success, test_results = run_docker_tests(image_name, temp_dir)
        report.append(f"Test Execution: {'SUCCESS' if success else 'FAILED'}\n")
        report.append(f"Test Results:\n{test_results}\n")

        report.append("\n--- Final AI Summary and Recommendations ---\n")
        final_summary_prompt = f"""
        Based on the following analysis report, synthesize a comprehensive summary for a human audience.
        Explain the overall findings, highlight key issues, successful steps, and provide actionable recommendations.
        Report:
        ```
        {"\n".join(report)}
        ```
        """
        llm_success, final_explanation = analyze_code_with_llm(final_summary_prompt, "Final Report Synthesis")
        if llm_success:
            report.append(final_explanation)
        else:
            report.append(f"Could not generate final AI explanation: {final_explanation}\n")

    except Exception as e:
        report.append(f"\nUnhandled error: {e}\n")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            report.append(f"\nCleaned up temporary directory: {temp_dir}\n")

    return "\n".join(report)

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_repo():
    data = request.get_json()
    repo_url = data.get('repo_url')
    if not repo_url:
        return jsonify({"error": "No repository URL provided"}), 400
    full_report = orchestrate_analysis(repo_url)
    return jsonify({"report": full_report})

# --- Entry Point ---
if __name__ == '__main__':
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    index_html_path = os.path.join(templates_dir, 'index.html')
    if not os.path.exists(index_html_path):
        with open(index_html_path, 'w') as f:
            f.write("""<html><body><h1>AI Code Auditor UI</h1></body></html>""")
    app.run(debug=True, host='0.0.0.0', port=5000)
