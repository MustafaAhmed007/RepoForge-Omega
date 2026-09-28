from __future__ import annotations
import json,subprocess
from dataclasses import dataclass
from typing import Any
@dataclass(slots=True)
class MCPResponse:
    id:int;result:dict[str,Any]|None=None;error:dict[str,Any]|None=None
class StdioMCPClient:
    def __init__(self, command: list[str]) -> None:self.command=command;self._next_id=1
    def call(self, method: str, params: dict[str,Any] | None = None, timeout: int = 30) -> MCPResponse:
        i=self._next_id;self._next_id+=1
        payload=json.dumps({"jsonrpc":"2.0","id":i,"method":method,"params":params or {}})
        p=subprocess.run(self.command,input=payload+"\n",text=True,capture_output=True,timeout=timeout,shell=False)
        if p.returncode:return MCPResponse(i,error={"code":p.returncode,"message":p.stderr[-4000:]})
        try:d=json.loads(p.stdout.splitlines()[-1])
        except (json.JSONDecodeError,IndexError):return MCPResponse(i,error={"code":-1,"message":"Invalid JSON-RPC response."})
        return MCPResponse(i,d.get("result"),d.get("error"))
