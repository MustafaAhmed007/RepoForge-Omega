from __future__ import annotations
import shlex

BLOCKED = ('rm -rf /','rm -rf ~','format c:','shutdown','reboot','git push','git reset --hard')
NETWORK = ('curl ','wget ','invoke-webrequest','powershell -command','pip install','npm install')

def command_policy(command:list[str], allow_side_effects:bool=False)->tuple[bool,str|None]:
    text=' '+shlex.join(command).lower()+' '
    if any(x in text for x in BLOCKED):
        return False,'destructive or state-changing command blocked by default'
    if not allow_side_effects and any(x in text for x in NETWORK):
        return False,'network/package mutation requires explicit approval'
    return True,None
