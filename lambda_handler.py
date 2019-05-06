import traceback

from common.constant import GITHUB_NET_ID
from common.repository import Repository
from common.utils import Utils
from github_traffic import update_github_traffic

obj_util = Utils()

db = Repository(net_id=GITHUB_NET_ID)


def request_handler(event, context):
    print(event)
    try:
        if db.connection is None:
            raise Exception('database connection is not initialized')
        update_github_traffic(repo=db)
        print("success")
    except Exception as e:
        print(repr(e))
        obj_util.report_slack(1, "Git Metrics|Err::" + repr(e))
        traceback.print_exc()
    return

request_handler(None,None)