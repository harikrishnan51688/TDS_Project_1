#!/usr/bin/env python3
"""
GitHub User and Repository Scraper

This script scrapes information about GitHub users in Singapore and their repositories.
It uses the GitHub API through PyGithub library to collect data about users with more
than 100 followers and their most recently pushed repositories.

The data is saved in two JSON files:
- users.json: Contains user profile information
- repository_data.json: Contains repository information for each user
"""

from github import Github, Auth
from github.GithubException import GithubException, RateLimitExceededException
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GitHubScraper:
    """A class to handle GitHub data scraping operations."""
    
    def __init__(self, token: str, max_repos_per_user: int = 500):
        """
        Initialize the GitHub scraper.
        
        Args:
            token (str): GitHub API token
            max_repos_per_user (int): Maximum number of repositories to fetch per user
        """
        self.auth = Auth.Token(token)
        self.github = Github(auth=self.auth)
        self.max_repos_per_user = max_repos_per_user

    @staticmethod
    def clean_company_name(name: Optional[str]) -> Optional[str]:
        """
        Clean and standardize company names.
        
        Args:
            name (Optional[str]): Raw company name
            
        Returns:
            Optional[str]: Cleaned company name or None if input is empty
        """
        if not name:
            return None
        
        cleaned = name.strip()
        cleaned = cleaned.replace('@', '')
        cleaned = cleaned.upper()
        cleaned = ' '.join(cleaned.split())
        return cleaned

    def get_user_data(self, user) -> Dict:
        """
        Extract relevant data from a user object.
        
        Args:
            user: PyGithub user object
            
        Returns:
            Dict: Dictionary containing user information
        """
        return {
            "login": user.login,
            "name": user.name,
            "company": self.clean_company_name(user.company),
            "location": user.location,
            "email": user.email,
            "hireable": user.hireable,
            "bio": user.bio,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

    def get_repo_data(self, user, repo) -> Dict:
        """
        Extract relevant data from a repository object.
        
        Args:
            user: PyGithub user object
            repo: PyGithub repository object
            
        Returns:
            Dict: Dictionary containing repository information
        """
        return {
            "login": user.login,
            "full_name": repo.full_name,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "stargazers_count": repo.stargazers_count,
            "watchers_count": repo.watchers_count,
            "language": repo.language,
            "has_projects": repo.has_projects,
            "has_wiki": repo.has_wiki,
            "license_name": repo.license.key if repo.license and repo.license.key else None
        }

    def save_to_json(self, data: List[Dict], filename: str) -> None:
        """
        Save data to a JSON file.
        
        Args:
            data (List[Dict]): Data to save
            filename (str): Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved data to {filename}")
        except IOError as e:
            logger.error(f"Error saving to {filename}: {str(e)}")
            raise

    def scrape_users(self, location: str = "Singapore", min_followers: int = 100) -> None:
        """
        Scrape GitHub users and their repositories based on location and minimum followers.
        
        Args:
            location (str): Location to search for users
            min_followers (int): Minimum number of followers required
        """
        query = f"location:{location} followers:>{min_followers}"
        users_data = []
        repos_data = []

        try:
            users = self.github.search_users(query)
            logger.info(f"Found {users.totalCount} matching users")

            for user in users:
                try:
                    user_data = self.get_user_data(user)
                    users_data.append(user_data)
                    
                    # Fetch repositories for the user
                    repos = user.get_repos(type='all', sort='pushed', direction='desc')
                    repo_count = 0
                    
                    for repo in repos:
                        if repo_count >= self.max_repos_per_user:
                            break
                            
                        try:
                            repo_data = self.get_repo_data(user, repo)
                            repos_data.append(repo_data)
                            repo_count += 1
                            logger.debug(f"Processed repo {repo_data['full_name']}, Count: {repo_count}")
                        except GithubException as e:
                            logger.warning(f"Error processing repo {repo.full_name}: {str(e)}")
                            continue
                            
                    logger.info(f"Processed user {user.name or user.login}. Company: {user_data['company']}")
                    
                except RateLimitExceededException:
                    logger.error("GitHub API rate limit exceeded")
                    break
                except GithubException as e:
                    logger.warning(f"Error processing user {user.login}: {str(e)}")
                    continue

            # Save the collected data
            self.save_to_json(users_data, "users.json")
            self.save_to_json(repos_data, "repository_data.json")

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
        finally:
            self.github.close()

def main():
    """Main entry point of the script."""
    # Replace with your GitHub token
    token = "ghp_******************"
    
    try:
        scraper = GitHubScraper(token)
        scraper.scrape_users()
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()