from github import Github

from tracker.common.config import TrackerInfraConfig


class GithubAgent:
    def __init__(self):
        self.agent = Github(self.github_access_token)
        self.repo = self.agent.get_repo("HumanCellAtlas/dcp")

    @property
    def github_access_token(self):
        return TrackerInfraConfig().github_access_token

    def create_issue(self, title, label, body):
        print(f"creating issue with title:{title} with body:{body}")
        issue = self.repo.create_issue(title=title, body=body, labels=[label])
        return issue

    def comment_on_issue(self, issue_number, body):
        print(f"commenting on issue:{issue_number} with comment:{body}")
        issue = self.repo.get_issue(number=int(issue_number))
        issue.create_comment(body=body)

    def edit_issue_state(self, issue_number, issue_state):
        print(f"editing issue:{issue_number} to state:{issue_state}")
        issue = self.repo.get_issue(number=int(issue_number))
        issue.edit(state=issue_state)

    def search(self, search_term):
        # Search issues in repo for title and return issue number number if exists
        pass
