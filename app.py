import json
import uuid
import copy
from datetime import datetime, timezone
from threading import RLock, Thread, Event
from queue import Queue, Empty
from pathlib import Path

import litellm
import uvicorn
from fastapi import FastAPI, Cookie, Depends, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

from backend.assistant.tools import run_tool
from backend.assistant.research_tools import TOOLS, SHARED_NAMES, AssistantResearchTools
from backend.assistant.identity import player_catalog, resolve_name, validate_ids, identify, clarification_text
from backend.data.nba import NBAData
from backend.activity import ActivityLog
from backend.model_calls import completion_with_backoff, model_error_message
from backend.paths import PROJECT_ROOT
from backend.tool_errors import parse_tool_arguments, tool_error

# --- Config ---

SYSTEM_PROMPT = (
    "You are a neutral NBA research assistant. Always respond in English, even when the user writes in another language. "
    "Investigate the question without defending a selected player or manufacturing a counterargument. "
    "The server provides confirmed NBA player IDs as identity context. Use those for pronouns and selected players. "
    "For a newly named player call resolve_player before querying. Never expand a surname into a guessed full name. "
    "If identity is ambiguous, stop and ask the user to choose. Do not query candidate statistics first. "
    "Clarify undefined comparisons such as best or peak before choosing evaluation criteria. "
    "For historical numeric answers, finish with submit_answer and include the exact structured claims behind your answer. "
    "Use source URLs from retrieved evidence; acknowledge mixed evidence, limitations and unavailable data. "
    "Use the relevant NBA tools before reporting game facts; never invent data or event IDs. "
    "Use find_games to identify a game when needed. If multiple games or names match, "
    "ask the user to choose only for a single-game request; do not guess. Reuse the selected event_id across tools. "
    "For single-game or daily comparisons or rankings, compose basic tools: find_games to identify every game in scope, "
    "game_players for each game's candidate players, then player_advanced_stats for every eligible player "
    "using the same requested metric, event_id, full player_name and team_name. "
    "For a whole-day request, examine all returned games instead of asking the user to choose one. "
    "Batch independent tool calls in the same response where possible; continue across rounds until coverage is complete. "
    "Compare and sort the returned metric values yourself and report all ties; no ranking tool is needed. "
    "Skip explicit did-not-play entries and undefined metrics, never treating missing values as zero. "
    "Do not impose an unrequested attempt threshold; if requested, check FGA in metric inputs or player_game_stats. "
    "Ask for a metric when best is undefined. State scope, filters, provisional status and missing coverage. "
    "Only claim an overall maximum after checking all eligible candidates in scope; otherwise label results partial. "
    "Dates are YYYY-MM-DD; omitted dates default to today in America/New_York when no event_id is given. "
    "Game tools use team_name/player_name. Historical research tools use NBA player IDs, "
    "resolved using resolve_player; never substitute ESPN IDs or invent IDs. "
    "For season/career statistics use query_evidence; for player comparisons use compare_players. "
    "Use player_awards or compare_awards for honors, find_counterexamples for matching games, "
    "and find_comparative_edges for metric advantages and disadvantages. "
    "Use competitive/performance context tools for scoped teammate, role, ranking or opponent questions. "
    "Resolve ambiguous names with the user. Players can change freely in Assistant. "
    "Season values are starting years: 2023 means 2023-24. Preserve compatible scopes, sources and limitations. "
    "Separate measured statistical differences from subjective overall rankings. "
    "Keep answers focused on the requested information. Call separate tools for separate categories. "
    "Use game_score with quarter=0 for full-game scores, 1-4 for a quarter, and 5 or higher for overtime. "
    "Use player_game_stats for player statistics and team_game_leader for a single category leader. "
    "Use player_advanced_stats for player efficiency and team_advanced_stats for team advanced metrics. "
    "Report estimate labels, provisional results, and unavailable metrics accurately; never substitute zero for missing values. "
    "Data tools never display panels automatically. For photos/profiles, retrieve data with player_info. "
    "For a photo/profile request, call display_panel with identity and photo fields only; omit metrics. "
    "Only include statistics in a panel when the user asks for statistics, a box score, or a specific metric. "
    "When statistics are requested, retrieve them and call display_panel for the requested player/team with those statistics. "
    "Include only the requested metrics; a box-score request includes the available basic box score, not unrequested advanced metrics. "
    "For follow-ups such as 'Also show his box score', reuse the player and game from conversation context, "
    "and include their previously retrieved profile/photo together with the newly requested statistics in the follow-up panel. "
    "Never carry statistics into a photo/profile-only request or across different players or games. "
    "Use metric objects with label, numeric value and unit; for supplied shooting lines or minutes such as '9-16' or '37:12', "
    "use value=null and display_value set to the exact supplied string. Do not invent or calculate display values. "
    "Do not call display_panel for intermediate candidates or every player inspected. Plain answers need no panel. "
    "Pass only the metrics needed for the final answer, preserving formula, inputs, estimates, availability, "
    "provisional status and caveats. Never invent image URLs or statistics. Then write the final answer. "
    "There is no overall best-player selection tool; do not present a category leader as an official award winner. "
    "For plays and shots, use filters and pagination; follow next_offset if the user requests all events. "
    "Injury reports and standings may be current rather than historical; preserve their dates and season labels. "
    "When a tool returns an error, follow next_action: repair invalid arguments, use returned candidates, "
    "and respect retry limits. If data remains unavailable, explain that without fabricating a result."
)
MAX_TOOL_ROUNDS = 20

# --- The Harness ---


def run_agent(messages: list[dict], on_event=None, research=None) -> tuple[str, list[dict]]:
    """Complete until the model answers without asking for a tool.

    Returns the final text and a record of every tool call made along the way.
    """
    tool_calls = ActivityLog(on_event)
    research = research or AssistantResearchTools()
    submission_requests = 0

    for _ in range(MAX_TOOL_ROUNDS):
        tool_calls.phase('Preparing a reply')
        reply = completion_with_backoff(litellm.completion,
            model="vertex_ai/gemini-3.5-flash-lite",
            vertex_location="global",
            messages=messages,
            tools=TOOLS,
        ).choices[0].message

        # Append assistant's reply (text, tool calls, or both) to the context.
        # model_dump() keeps it a plain dict: the raw object carries provider-specific
        # fields that trip Pydantic when LiteLLM re-serializes it next round.
        messages += [reply.model_dump()]

        if not reply.tool_calls:
            if research.evidence and not research.submission:
                submission_requests += 1
                if submission_requests >= 3:
                    answer = "I retrieved evidence, but could not complete its numeric checks. Please narrow the question. Sources and coverage are shown below."
                    messages[-1] = {'role': 'assistant', 'content': answer}
                    return answer, tool_calls
                messages.append({'role': 'system', 'content': 'Historical evidence was retrieved. Submit your final answer through submit_answer with exact structured claims before publication. Do not publish an unchecked draft.'})
                continue
            return reply.content, tool_calls

        # The harness, not the model, runs each tool and appends the result
        for call in reply.tool_calls:
            args = {}
            try:
                args = parse_tool_arguments(call.function.arguments)
            except ValueError as exc:
                result = json.dumps(tool_error('invalid_arguments', str(exc),
                    'Resend this tool call with a valid JSON object matching its parameter schema.', status='revise'))
            else:
                tool_calls.start(call.function.name,args)
                if research.pending or research.submission:
                    result = json.dumps({'status': 'skipped', 'reason': 'Identity clarification or final submission ends this turn.'})
                else:
                    if call.function.name in SHARED_NAMES or call.function.name == 'submit_answer':
                        result = research.dispatch(call.function.name, args)
                    else:
                        identity_error = research.game_identity_error(args)
                        result = json.dumps(identity_error) if identity_error else run_tool(call.function.name, args)
                        research.observe_game_result(call.function.name, result)
            tool_calls.append({"name": call.function.name, "args": args, "result": result})

            messages += [{"role": "tool", "tool_call_id": call.id, "content": result}]
        if research.pending:
            answer = clarification_text(research.pending)
            messages.append({'role': 'assistant', 'content': answer})
            return answer, tool_calls
        if research.submission:
            answer = research.submission['answer']
            messages.append({'role': 'assistant', 'content': answer})
            return answer, tool_calls

    if research.used_evidence:
        answer = "The research limit was reached before an answer passed numeric checks. The retrieved sources and coverage remain available below."
        messages.append({'role': 'assistant', 'content': answer})
        return answer, tool_calls

    # One final model request with tools disabled, after all tool results are appended.
    summary_instruction = {"role": "system", "content": (
        "The tool-call round limit has been reached. Summarize only the collected evidence. "
        "Explicitly state any unfinished coverage; do not claim a definitive winner if candidates remain unchecked. "
        "Do not request further tools."
    )}
    reply = completion_with_backoff(litellm.completion,
        model="vertex_ai/gemini-3.5-flash-lite", vertex_location="global",
        messages=messages + [summary_instruction], tools=TOOLS, tool_choice="none",
    ).choices[0].message
    response = reply.content if not reply.tool_calls else None
    response = response or "I reached the tool-call limit. The collected results may be incomplete; please narrow the scope or continue."
    messages.append({"role": "assistant", "content": response})
    return response, tool_calls


# --- Session Store ---

HISTORY_DIR = PROJECT_ROOT / "chat_history"
store_lock = RLock()


def browser_owner(response: Response, nba_browser: str | None = Cookie(default=None)):
    try:
        owner = str(uuid.UUID(nba_browser or ""))
    except ValueError:
        owner = str(uuid.uuid4())
        response.set_cookie("nba_browser", owner, httponly=True, samesite="strict", max_age=31536000)
    return owner


def history_path(owner, session_id):
    try:
        session_id = str(uuid.UUID(session_id))
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid session ID")
    return HISTORY_DIR / owner / (session_id + ".json")


def read_history(owner, session_id):
    path = history_path(owner, session_id)
    if not path.exists():
        raise HTTPException(404, "Conversation not found")
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        raise HTTPException(500, "Unable to read saved conversation")


def save_history(owner, record):
    path = history_path(owner, record["session_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    temporary.replace(path)


# --- FastAPI App ---

app = FastAPI()
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets", check_dir=False), name="frontend-assets")


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(max_length=12000)
    session_id: str | None = None
    mode: Literal['assistant'] | None = None
    player_ids: list[int] | None = Field(default=None, max_length=8)
    identity_choices: dict[str, int] = Field(default_factory=dict)
    resume_pending: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list[dict]
    evidence_result: dict | None = None
    selected_players: list[dict] = Field(default_factory=list)
    player_clarifications: list[dict] = Field(default_factory=list)
    failed: bool = False


@app.get("/")
def index():
    if not (FRONTEND_DIST / "index.html").is_file():
        raise HTTPException(503, "Build the frontend first: cd frontend && npm ci && npm run build")
    return FileResponse(FRONTEND_DIST / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/favicon.svg")
def favicon():
    return FileResponse(PROJECT_ROOT / "frontend" / "public" / "favicon.svg")


@app.get("/sessions")
def list_sessions(owner: str = Depends(browser_owner)):
    with store_lock:
        records = []
        for path in (HISTORY_DIR / owner).glob("*.json"):
            try:
                record = json.loads(path.read_text())
                if record.get("mode", "assistant") != "assistant":
                    continue
                records.append({**{key: record[key] for key in ("session_id", "title", "updated_at")},
                                'mode': record.get('mode', 'assistant')})
            except (ValueError, OSError, KeyError):
                continue
        return sorted(records, key=lambda item: item["updated_at"], reverse=True)


@app.get("/sessions/{session_id}")
def get_session(session_id: str, owner: str = Depends(browser_owner)):
    with store_lock:
        record = read_history(owner, session_id)
        return {**{key: record[key] for key in ("session_id", "title", "turns")},
                'mode': 'assistant', 'selected_players': record.get('selected_players', []),
                'pending_identity': record.get('pending_identity')}



@app.get('/players')
def search_players(query: str = ''):
    if not 2 <= len(query.strip()) <= 100:
        return {'players': [], 'complete': True, 'resolved': False}
    return resolve_name(query.strip())


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, owner: str = Depends(browser_owner)):
    return _chat(request,owner)


@app.post('/chat/stream')
def chat_stream(request: ChatRequest, response: Response, owner: str = Depends(browser_owner)):
    queue = Queue()
    disconnected = Event()
    def emit(event):
        if not disconnected.is_set():
            queue.put(event)
    def work():
        try:
            result = _chat(request,owner,emit)
            emit({'type':'done','data':result.model_dump()})
        except HTTPException as exc:
            emit({'type':'error','message':str(exc.detail),'status':exc.status_code})
        except Exception:
            emit({'type':'error','message':'Unable to complete or save this conversation.'})
    def events():
        Thread(target=work,daemon=True).start()
        try:
            yield 'data: '+json.dumps({'type':'phase','label':'Preparing your request'})+'\n\n'
            while True:
                try:
                    event=queue.get(timeout=10)
                except Empty:
                    yield ': keepalive\n\n'
                    continue
                yield 'data: '+json.dumps(event,ensure_ascii=False)+'\n\n'
                if event['type'] in ('done','error'):
                    break
        finally:
            # A started turn may finish saving after disconnect; do not buffer events.
            disconnected.set()
    stream = StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})
    for key,value in response.raw_headers:
        if key.lower()==b'set-cookie':
            stream.raw_headers.append((key,value))
    return stream


def _chat(request: ChatRequest, owner: str, on_event=None):
    activity = []
    def emit(event):
        if event['type']=='tool_start':
            activity.append(dict(event['call']))
        elif event['type']=='tool_end':
            for index,call in enumerate(activity):
                if call['id']==event['call']['id']:
                    activity[index]=dict(event['call'])
                    break
        if on_event:
            on_event(event)
    if not request.message.strip():
        raise HTTPException(400, "Message must not be empty")
    with store_lock:
        if request.session_id:
            record = read_history(owner, request.session_id)
            if record.get('mode', 'assistant') != 'assistant':
                raise HTTPException(409, 'This is an archived debate conversation. Start a new research conversation.')
        else:
            record = {"session_id": str(uuid.uuid4()), "title": request.message.strip()[:80],
                      "messages": [{"role": "system", "content": SYSTEM_PROMPT}], "turns": [],
                      'mode': 'assistant', 'selected_players': [], 'evidence': {}}
        catalog = player_catalog()
        original = request.message
        pending_previous = record.get('pending_identity')
        replace_pending = False
        choices = dict(request.identity_choices)
        text_confirmation = False
        try:
            selected = validate_ids(request.player_ids, catalog) if request.player_ids is not None else record.get('selected_players', [])
            # A full-name-only reply also confirms a pending person. Preserve
            # the question instead of asking the user to type it again.
            if pending_previous and not request.resume_pending and not choices and len(pending_previous['groups']) == 1:
                explicit = resolve_name(request.message.strip(), catalog)
                group = pending_previous['groups'][0]
                if explicit['resolved'] and (not group['players'] or explicit['players'][0]['id'] in {p['id'] for p in group['players']}):
                    chosen = explicit['players'][0]
                    choices[group['query']] = chosen['id']
                    selected = [p for p in selected if p['id'] not in {c['id'] for c in group['players']}] + [chosen]
                    original = pending_previous['message']
                    text_confirmation = True
            if request.resume_pending:
                if not pending_previous:
                    raise ValueError('There is no pending player question to continue.')
                original = pending_previous['message']
                allowed = {g['query']: {p['id'] for p in g['players']} for g in pending_previous['groups']}
                if any(q not in allowed or ident not in allowed[q] for q, ident in choices.items()):
                    raise ValueError('Select a player from the pending candidates.')
                # Some ambiguity was detected by resolve_player rather than the
                # deterministic mention parser, so carry those choices as well.
                for query, ident in choices.items():
                    selected = [p for p in selected if p['id'] not in allowed[query]] + validate_ids([ident], catalog)
                replace_pending = bool(record['turns'] and record['turns'][-1].get('player_clarifications'))
            elif choices and not text_confirmation:
                raise ValueError('Player candidate choices require a pending question.')
            selected, pending = identify(original, selected, choices, catalog)
            if request.resume_pending:
                unresolved = [g for g in pending_previous['groups'] if g['query'] not in choices]
                pending = list({g['query']: g for g in pending + unresolved}.values())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        record['selected_players'] = selected
        emit({'type': 'session', 'session_id': record['session_id']})
        emit({'type': 'players', 'players': selected})
        evidence_result, failed, tool_calls = None, False, []
        if pending:
            response = clarification_text(pending)
        else:
            messages = copy.deepcopy(record['messages'])
            context = json.dumps([{'id': p['id'], 'name': p['name']} for p in selected], ensure_ascii=False)
            # Replace identity context each turn; removed players must not remain
            # in an old system message and silently override the new selection.
            messages = [m for m in messages if not (m.get('role') == 'system' and m.get('content', '').startswith('Confirmed NBA identities:'))]
            messages[0] = {'role': 'system', 'content': SYSTEM_PROMPT}
            aliases = json.dumps(choices, ensure_ascii=False)
            messages.insert(1, {'role': 'system', 'content': 'Confirmed NBA identities: ' + context + '. Confirmed name choices for this question: ' + aliases + '. This selection gives identity, not allegiance or a statistical scope. Explicit newly named players may be resolved. Do not infer who is better.'})
            messages.append({'role': 'user', 'content': original})
            research = AssistantResearchTools(evidence=record.get('evidence'), players=selected, catalog=catalog, question=original)
            try:
                response, tool_calls = run_agent(messages, on_event=emit, research=research)
                response = response or 'No response was returned. Please try again.'
                pending = research.pending
                # Do not keep a partial ambiguous tool exchange. Resume the
                # original question in a clean turn after candidate selection.
                if not pending:
                    record['messages'] = messages
                    record['evidence'] = research.evidence
                    evidence_result = research.summary() if research.used_evidence or research.submission else None
                if not pending:
                    by_id = {p['id']: p for p in catalog}
                    selected = list({p['id']: p for p in selected + [by_id[int(i)] for i in research.names if int(i) in by_id]}.values())[:8]
                    record['selected_players'] = selected
            except Exception as exc:
                response, tool_calls = model_error_message(exc), []
                for call in activity:
                    if call.get('status') == 'running':
                        call.update(status='failed', result='The request stopped before this tool completed.')
                    tool_calls.append(call)
                failed = True
        record['pending_identity'] = {'message': original, 'groups': pending} if pending else None
        turn = {'message': request.message if text_confirmation else original, 'response': response, 'tool_calls': tool_calls,
                'evidence_result': evidence_result, 'player_clarifications': pending,
                'selected_players': selected, 'failed': failed}
        if replace_pending:
            record['turns'][-1] = turn
        else:
            record['turns'].append(turn)
        record['updated_at'] = datetime.now(timezone.utc).isoformat()
        save_history(owner, record)
        return ChatResponse(response=response, session_id=record['session_id'], tool_calls=tool_calls,
                            evidence_result=evidence_result, selected_players=selected,
                            player_clarifications=pending, failed=failed)



@app.post("/clear")
def clear(session_id: str, owner: str = Depends(browser_owner)):
    with store_lock:
        history_path(owner, session_id).unlink(missing_ok=True)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
