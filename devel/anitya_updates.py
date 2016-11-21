"""
This fetches a selection of update message ids from datagrepper to use for
development in the-new-hotness.
"""

import requests


UPDATE_URL = ('https://apps.fedoraproject.org/datagrepper/raw?topic=org.'
              'release-monitoring.prod.anitya.project.version.update&'
              'delta=604800&rows_per_page=75')
response = requests.get(UPDATE_URL, timeout=30)
updates = response.json()

template = """
Message ID: {msg_id}
Update for {name} to {new_v}
"""
for message in updates['raw_messages']:
    name = message['msg']['project']['name']
    new_v = message['msg']['project']['version']
    print(template.format(msg_id=message['msg_id'], name=name, new_v=new_v))
