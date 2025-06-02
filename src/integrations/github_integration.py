import os
from typing import Dict, List
from github import Github
from pathlib import Path

class GitHubPRCreator:
    def __init__(self, repo_name: str):
        """Initialize with GitHub token and repository name"""
        self.github = Github(os.environ.get("GITHUB_TOKEN"))
        self.repo = self.github.get_repo(repo_name)
    
    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        description: str,
        file_changes: Dict[str, str]
    ) -> str:
        """
        Create a pull request with the specified changes
        
        Args:
            branch_name: Name for the new branch
            title: PR title
            description: PR description
            file_changes: Dict of file paths and their new content
            
        Returns:
            URL of the created pull request
        """
        try:
            # Get the default branch
            default_branch = self.repo.default_branch
            
            # Create a new branch
            source = self.repo.get_branch(default_branch)
            self.repo.create_git_ref(f"refs/heads/{branch_name}", source.commit.sha)
            
            # Create commits for each file
            for file_path, content in file_changes.items():
                try:
                    # Try to get the file first
                    file = self.repo.get_contents(file_path, ref=branch_name)
                    self.repo.update_file(
                        file_path,
                        f"Update {file_path}",
                        content,
                        file.sha,
                        branch=branch_name
                    )
                except Exception:
                    # File doesn't exist, create it
                    self.repo.create_file(
                        file_path,
                        f"Create {file_path}",
                        content,
                        branch=branch_name
                    )
            
            # Create the pull request
            pr = self.repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=default_branch
            )
            
            return pr.html_url
            
        except Exception as e:
            raise Exception(f"Error creating pull request: {str(e)}")
    
    def get_file_content(self, file_path: str, ref: str = None) -> str:
        """Get the content of a file from the repository"""
        try:
            file = self.repo.get_contents(file_path, ref=ref)
            return file.decoded_content.decode('utf-8')
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")
    
    def get_repository_files(self, path: str = "", ref: str = None) -> Dict[str, str]:
        """Recursively get all files from the repository"""
        files = {}
        contents = self.repo.get_contents(path, ref=ref)
        
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path, ref=ref))
            else:
                try:
                    files[file_content.path] = file_content.decoded_content.decode('utf-8')
                except Exception:
                    # Skip binary files
                    continue
        
        return files 