# git_operations.py
import git
import os

# Ensure gitpython knows where git.exe is (important if not in system PATH)
# This assumes you've set GIT_PYTHON_GIT_EXECUTABLE environment variable,
# or uncomment and set git_executable_path directly if needed.
# git_executable_path = r"C:\Program Files\Git\bin\git.exe"
# if os.path.exists(git_executable_path):
#     os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = git_executable_path
# else:
#     print(f"Warning: Git executable not explicitly set and not found at {git_executable_path}. Relying on system PATH or GIT_PYTHON_GIT_EXECUTABLE env var.")

def clone_repo(repo_url: str, target_path: str) -> tuple[bool, str]:
    """Clones a Git repository into the target path."""
    try:
        # Use a shallow clone to save time and space, especially for large repos
        git.Repo.clone_from(repo_url, target_path, depth=1)
        return True, "Repository cloned successfully."
    except git.GitCommandError as e:
        return False, f"Error cloning repository: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred during repository cloning: {e}"

if __name__ == '__main__':
    # Example usage for testing this module independently
    test_repo = "https://github.com/githu_user/test_repo" # Replace with a small public repo for testing
    test_dir = "./temp_test_repo_clone"
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir)
    success, message = clone_repo(test_repo, test_dir)
    print(f"Clone result: {message}")
    if success:
        print(f"Repo cloned to: {os.path.abspath(test_dir)}")
        import shutil
        shutil.rmtree(test_dir) # Clean up
        print("Cleaned up test repo.")