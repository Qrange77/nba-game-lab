"""Public execution graph driven by actual lifecycle events, not model text."""
import copy
import time
from threading import RLock


class ResearchFlow:
    def __init__(self, emit, clock=time.monotonic):
        self.emit=emit
        self.clock=clock
        self.started=clock()
        self.lock=RLock()
        self.nodes=[]
        self.version=0
        self.status='running'
        self.peak_parallel=0

    def milliseconds(self):
        return round((self.clock()-self.started)*1000)

    def snapshot(self):
        with self.lock:
            return copy.deepcopy({'version':self.version,'status':self.status,
                'elapsed_ms':self.milliseconds(),'peak_parallel':self.peak_parallel,'nodes':self.nodes})

    def publish(self):
        self.version+=1
        self.emit({'type':'research_flow','flow':self.snapshot()})

    def add(self,ident,label,role,agent,parents=(),description='',round_number=0,queued=False):
        with self.lock:
            known={n['id'] for n in self.nodes}
            if ident in known or any(p not in known for p in parents):
                raise ValueError('Flow IDs must be unique and dependencies must already exist.')
            self.nodes.append({'id':ident,'label':label,'role':role,'agent':agent,
                'depends_on':list(parents),'description':description,'round':round_number,
                'status':'queued' if queued else 'running','started_ms':None if queued else self.milliseconds(),
                'ended_ms':None,'tool_ids':[],'summary':''})
            self.publish()

    def start(self,ident):
        with self.lock:
            node=next(n for n in self.nodes if n['id']==ident)
            node.update(status='running',started_ms=self.milliseconds())
            self.peak_parallel=max(self.peak_parallel,sum(n['role']=='researcher' and n['status']=='running' for n in self.nodes))
            self.publish()

    def finish(self,ident,status='completed',summary='',tool_ids=()):
        with self.lock:
            node=next(n for n in self.nodes if n['id']==ident)
            node.update(status=status,ended_ms=self.milliseconds(),summary=summary,tool_ids=list(tool_ids))
            self.publish()

    def close(self,status='completed'):
        with self.lock:
            self.status=status
            for node in self.nodes:
                if node['status'] in ('running','queued'):
                    node.update(status='failed' if node['status']=='running' else 'cancelled',ended_ms=self.milliseconds())
            self.publish()
