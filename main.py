from github import Github
import json
from datetime import datetime

from github import Auth

auth = Auth.Token("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")

g = Github(auth=auth)


def clean_company_name(name):
    if not name:
        return None
    
    cleaned = name.strip()
    cleaned = name.replace('@','')
    cleaned = cleaned.upper()
    cleaned = ' '.join(cleaned.split())
    return cleaned


def scrape_users():
    query = "location:Singapore followers:>100"

    users = g.search_users(query)
    print(f"Found {users.totalCount} matching users.")

    users_data = []
    repos_data = []

    for user in users:

        user_data = {
            "login": user.login,
            "name": user.name,
            "company": clean_company_name(user.company),
            "location": user.location,
            "email": user.email,
            "hireable": user.hireable,
            "bio": user.bio,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

        repos = user.get_repos(type='all', sort='pushed', direction='desc')

        repo_count = 0
        for repo in repos:
            if repo_count >= 500:
                break

            repo_data = {
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
            repo_count += 1
            repos_data.append(repo_data)
            print(f"Processed repo {repo_data['full_name']}, Count: {repo_count}")

        users_data.append(user_data)
        print(f"Processed user {user.name}. Company {user_data['company']}")


    with open("users.json", 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)
    
    with open("repository_data.json", 'w', encoding='utf-8') as f:
        json.dump(repos_data, f, indent=2, ensure_ascii=False)


scrape_users()
g.close()
