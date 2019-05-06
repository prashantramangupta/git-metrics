from datetime import datetime as dt, timedelta as td
import github
import pymysql
from warnings import filterwarnings
filterwarnings('ignore', category = pymysql.Warning)

def _collect(token, org, repo):
    gh = github.GitHub(access_token=token)
    repositries_data = gh.orgs(org).repos.get(per_page="1000")
    print("total no. of public repository: ", len(repositries_data))

    for rec in repositries_data:
        repo_nm = rec['name']
        forks = rec['forks']
        stargazers_count = rec['stargazers_count']
        watchers_count = rec['watchers_count']
        print("processing repo: ", repo_nm)
        commit_since = last_recorded_date(repo, repo_nm)
        if commit_since == None:
            commit_since = (dt.utcnow() - td(14)).date()
        page_no = 1
        commit_info = {}
        commit_count_dict = {}
        while len(commit_info) > 0 or page_no == 1:
            commit_info = gh.repos(org)(repo_nm).commits.get(since=str(commit_since), per_page="100", page=str(page_no))
            for rec in commit_info:
                date = dt.strptime(rec['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ').date()
                commit_count_dict[str(date)] = commit_count_dict.get(str(date), 0) + 1
            page_no = page_no + 1

        views_14_days = gh.repos(org, repo_nm).traffic.views.get()

        count = 0;
        for view_per_day in views_14_days['views']:
            view_dt = dt.strptime(view_per_day['timestamp'], '%Y-%m-%dT%H:%M:%SZ').date()
            if commit_since <= view_dt:
                commit_count = commit_count_dict.get(str(view_dt), 0)
                git_traffic_rec = [repo_nm, view_dt, view_per_day['count'], view_per_day['uniques'],
                                   commit_count, forks, stargazers_count, watchers_count, dt.utcnow(),
                                   dt.utcnow()]
                rows_inserted = write_to_db(repo, git_traffic_rec=git_traffic_rec)
                count = count + rows_inserted

        print("records recorded:", count)


def write_to_db(repo, git_traffic_rec):
    try:
        qry = "INSERT IGNORE INTO git_traffic (repo, date, views, uq_views, cmt_cnt, forks, stargazers_count, watchers_count," \
              " row_created, row_updated) " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        res = repo.execute(qry, git_traffic_rec)
        return res[0]
    except Exception as e:
        print(repr(e))

def last_recorded_date(repo, repo_nm):
    try:
        qry = "SELECT date FROM git_traffic WHERE repo =%s ORDER BY date DESC LIMIT 1"
        res = repo.execute(qry, repo_nm)
        if len(res) == 1:
            return res[0]['date'].date()
        return None
    except Exception as e:
        print(repr(e))

def update_github_traffic(repo):
    _collect(token="", org="singnet", repo=repo)
