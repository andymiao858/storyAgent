"""LangGraph node implementations for each Agent."""
import json
import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import StoryState
from app.utils.llm import get_llm
from app.rag.knowledge_base import search_knowledge

logger = logging.getLogger(__name__)


def user_profile_node(state: StoryState) -> dict:
    """User Profile Agent: Build a simplified child profile for story generation."""
    profile = state.get("child_profile", {})
    age = profile.get("age", 5)

    if age <= 5:
        age_group = "3-5"
        language_style = "简单短句，多用拟声词，语言活泼可爱"
    elif age <= 8:
        age_group = "5-8"
        language_style = "可以使用稍复杂句式，加入简单因果关系"
    else:
        age_group = "6-9"
        language_style = "可以有适度悬念和逻辑推理，鼓励思考"

    enriched_profile = {
        **profile,
        "age_group": age_group,
        "language_style": language_style,
    }
    return {"child_profile": enriched_profile}


def story_planning_node(state: StoryState) -> dict:
    """Story Planning Agent: LLM generates a concise story plan."""
    llm = get_llm(temperature=0.8)
    profile = state.get("child_profile", {})
    theme = state.get("story_theme", "探险")
    character = state.get("main_character", "小兔子")
    scene = state.get("scene", "森林")
    age_group = profile.get("age_group", "3-5")
    interests = profile.get("interests", [])
    blocked = state.get("blocked_topics", [])

    blocked_str = "、".join(blocked) if blocked else "无"
    interests_str = "、".join(interests) if interests else "无"

    prompt = f"""为{age_group}岁儿童策划一个5幕互动故事。
主题：{theme}，主角：{character}，场景：{scene}，兴趣：{interests_str}，禁止：{blocked_str}

直接输出JSON，不要其他文字：
{{"story_title":"标题","story_arc":"一句话概要","scenes":[{{"scene_index":0,"scene_title":"标题","scene_summary":"概要","education_point":"要点"}},{{"scene_index":1,"scene_title":"...","scene_summary":"...","education_point":"..."}},{{"scene_index":2,"scene_title":"...","scene_summary":"...","education_point":"..."}},{{"scene_index":3,"scene_title":"...","scene_summary":"...","education_point":"..."}},{{"scene_index":4,"scene_title":"...","scene_summary":"...","education_point":"..."}}]}}"""

    messages = [
        SystemMessage(content="你是儿童故事策划师。输出简洁JSON，每个scene_summary不超过15字。"),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    content = response.content.strip()

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        plan = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        plan = {
            "story_title": f"{character}的{theme}故事",
            "story_arc": f"{character}在{scene}经历了一段{theme}的冒险",
            "scenes": [
                {"scene_index": i, "scene_title": t, "scene_summary": s, "education_point": e}
                for i, (t, s, e) in enumerate([
                    ("冒险开始", f"{character}来到{scene}", "好奇"),
                    ("遇到挑战", "意外的难题出现", "勇敢"),
                    ("结识朋友", "新伙伴加入", "合作"),
                    ("关键抉择", "面对最大困难", "坚持"),
                    ("美好结局", "收获成长和友谊", "成长"),
                ])
            ],
        }

    return {"story_plan": plan}


def retrieval_node(state: StoryState) -> dict:
    """Retrieval Agent: Search RAG knowledge base for relevant context.
    Only depends on theme/character/scene/age_group — does NOT need story_plan,
    so it can run in parallel with planning.
    """
    theme = state.get("story_theme", "")
    character = state.get("main_character", "")
    scene = state.get("scene", "")
    profile = state.get("child_profile", {})
    age_group = profile.get("age_group", "")

    query = f"儿童故事 主题:{theme} 角色:{character} 场景:{scene} 年龄段:{age_group}"

    try:
        docs = search_knowledge(query, top_k=5)
        retrieved = [doc.page_content for doc in docs]
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        retrieved = []

    return {"retrieved_docs": retrieved}


def _build_history_context(history: list, is_last_scene: bool = False) -> tuple:
    """Build structured history context for generation prompts.

    Returns (history_text, last_choice_text):
      - history_text: formatted prior scenes
      - last_choice_text: the child's most recent choice (empty string for first scene)
    """
    if not history:
        return "", ""

    parts = []
    for i, h in enumerate(history):
        is_latest = i == len(history) - 1
        text = h.get("text", "")
        # Full text for the latest scene; summarised for older ones
        display = text if is_latest else (text[:200] + "…" if len(text) > 200 else text)
        parts.append(f"第{h.get('scene_index', 0) + 1}幕：{display}")
        if h.get("choice"):
            parts.append(f"  → 孩子选择了：「{h['choice']}」")

    last_choice = history[-1].get("choice", "") if history else ""
    return "\n".join(parts), last_choice


def _build_generation_messages(state: StoryState, *, plain_text: bool = False):
    """Build LLM messages for story scene generation.

    Args:
        state: current workflow state
        plain_text: if True, ask for plain text output (used by streaming path);
                    if False, ask for JSON output (used by non-streaming path).
    Returns:
        (messages, is_last, total_scenes)
    """
    profile = state.get("child_profile", {})
    plan = state.get("story_plan", {})
    scene_index = state.get("current_scene_index", 0)
    history = state.get("interaction_history", [])
    theme = state.get("story_theme", "探险")
    character = state.get("main_character", "小兔子")
    scene_setting = state.get("scene", "森林")
    language_style = profile.get("language_style", "简单短句")
    age_group = profile.get("age_group", "3-5")
    blocked = state.get("blocked_topics", [])

    scenes = plan.get("scenes", [])
    total_scenes = len(scenes) if scenes else 5
    is_last = scene_index >= total_scenes - 1

    current_plan = {}
    if scenes and scene_index < len(scenes):
        current_plan = scenes[scene_index]

    blocked_str = "、".join(blocked) if blocked else "无"
    history_text, last_choice = _build_history_context(history, is_last)

    plan_hint = ""
    if current_plan:
        plan_hint = f"本幕规划：{current_plan.get('scene_title', '')}——{current_plan.get('scene_summary', '')}\n"

    story_arc = plan.get("story_arc", "")
    arc_hint = f"故事主线：{story_arc}\n" if story_arc else ""

    # --- build prompt ----
    header = (
        f"你正在为{age_group}岁的孩子续写互动故事。\n"
        f"主角：{character}，主题：{theme}，场景：{scene_setting}\n"
        f"语言风格：{language_style}\n"
        f"禁止出现：{blocked_str}\n"
        f"{arc_hint}{plan_hint}"
        f"当前进度：第{scene_index + 1}幕（共{total_scenes}幕）\n"
    )

    if history_text:
        header += f"\n===前情回顾===\n{history_text}\n"

    if is_last:
        if last_choice:
            header += (
                f"\n===孩子的选择===\n"
                f"孩子刚才选择了「{last_choice}」。\n"
                f"\n===创作要求===\n"
                f"请基于孩子的选择「{last_choice}」，续写故事最终结局（150-300字）。\n"
                f"结局要温馨积极，自然收尾，肯定主角的成长，并呼应孩子一路以来的选择。\n"
            )
        else:
            header += (
                "\n===创作要求===\n"
                "创作温馨积极的结局（150-300字），自然收尾并肯定主角成长。\n"
            )
        if plain_text:
            header += "请直接输出故事文本，不要输出JSON或其他格式。\n"
        else:
            header += f'输出JSON：{{"scene_text": "结局文本", "is_ending": true}}\n'
    else:
        if last_choice:
            header += (
                f"\n===孩子的选择===\n"
                f"孩子刚才选择了「{last_choice}」。\n"
                f"\n===创作要求===\n"
                f"请基于孩子的选择「{last_choice}」，自然衔接上文，续写第{scene_index + 1}幕（150-300字）。\n"
                f"故事内容必须直接回应并延续孩子的选择，让孩子感受到自己的选择影响了故事走向。\n"
            )
        else:
            header += (
                "\n===创作要求===\n"
                f"创作第{scene_index + 1}幕故事场景（150-300字）。\n"
            )
        if plain_text:
            header += "请直接输出故事文本，不要输出JSON或其他格式。\n"
        else:
            header += (
                "同时给出2-3个互动选项供孩子选择，选项应有趣并能推动故事发展。\n"
                f'输出JSON：{{"scene_text": "文本", "options": [{{"key": "A", "text": "..."}}, {{"key": "B", "text": "..."}}, {{"key": "C", "text": "..."}}]}}\n'
            )

    sys_msg = (
        "你是一位深受孩子喜爱的儿童故事作家。"
        "你的故事充满想象力、语言生动有趣、积极向上。"
        "最重要的是：每一幕的内容必须紧密承接上一幕的结尾和孩子的选择，保持故事的连贯性。"
    )
    messages = [SystemMessage(content=sys_msg), HumanMessage(content=header)]
    return messages, is_last, total_scenes


def story_generation_node(state: StoryState) -> dict:
    """Story Generation Agent: Generate the current scene text and options (non-streaming)."""
    llm = get_llm(temperature=0.85)
    messages, is_last, _ = _build_generation_messages(state, plain_text=False)

    response = llm.invoke(messages)
    content = response.content.strip()

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        if is_last:
            result = {"scene_text": content, "is_ending": True}
        else:
            result = {
                "scene_text": content,
                "options": [
                    {"key": "A", "text": "继续探索"},
                    {"key": "B", "text": "换个方向"},
                    {"key": "C", "text": "找朋友帮忙"},
                ],
            }

    scene_text = result.get("scene_text", content)
    options = result.get("options", [])
    is_ending = result.get("is_ending", False) or is_last

    return {
        "current_scene_text": scene_text,
        "options": options,
        "story_finished": is_ending,
    }


async def generate_options(scene_text: str, state: StoryState) -> list:
    """Generate interactive options for a scene (used by streaming path)."""
    profile = state.get("child_profile", {})
    age_group = profile.get("age_group", "3-5")
    theme = state.get("story_theme", "")
    character = state.get("main_character", "")

    llm = get_llm(temperature=0.8)
    prompt = (
        f"根据以下故事场景，为{age_group}岁儿童生成2-3个简短有趣的互动选项。\n"
        f"主角：{character}，主题：{theme}\n\n"
        f"场景内容：\n{scene_text[-500:]}\n\n"
        f'直接输出JSON数组：[{{"key":"A","text":"选项1"}},{{"key":"B","text":"选项2"}},{{"key":"C","text":"选项3"}}]'
    )
    messages = [
        SystemMessage(content="你是儿童互动故事设计师，擅长设计有趣的选择分支。直接输出JSON。"),
        HumanMessage(content=prompt),
    ]
    response = await llm.ainvoke(messages)
    content = response.content.strip()
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        options = json.loads(content)
        if isinstance(options, list):
            return options
    except (json.JSONDecodeError, IndexError):
        pass
    return [
        {"key": "A", "text": "继续探索"},
        {"key": "B", "text": "换个方向"},
        {"key": "C", "text": "找朋友帮忙"},
    ]


def safety_audit_node(state: StoryState) -> dict:
    """Safety Audit Agent: Check generated text for safety issues."""
    text = state.get("current_scene_text", "")
    blocked = state.get("blocked_topics", [])

    # Layer 1: Rule-based filtering
    sensitive_words = [
        "死亡", "杀死", "血腥", "恐怖", "鬼", "魔鬼", "暴力", "打架",
        "武器", "枪", "刀", "毒", "赌博", "酒精", "吸烟",
    ]
    found_sensitive = []
    for word in sensitive_words:
        if word in text:
            found_sensitive.append(word)

    for topic in blocked:
        if topic in text:
            found_sensitive.append(f"屏蔽主题:{topic}")

    if not found_sensitive:
        return {
            "safety_result": {
                "status": "safe",
                "risk_type": "",
                "original_text": text,
                "revised_text": "",
            }
        }

    # Layer 2: LLM-based review and revision
    llm = get_llm(temperature=0.3)
    prompt = f"""你是一位儿童内容安全审核专家。以下故事文本中检测到了敏感内容：{', '.join(found_sensitive)}

原始文本：
{text}

请将文本修改为适合儿童阅读的安全版本，保持故事情节基本不变，但去除或替换所有不适宜的内容。
直接输出修改后的文本，不要有其他说明。"""

    messages = [
        SystemMessage(content="你是儿童内容安全审核专家，负责确保所有内容适合儿童阅读。"),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    revised = response.content.strip()

    return {
        "current_scene_text": revised,
        "safety_result": {
            "status": "revised",
            "risk_type": ", ".join(found_sensitive),
            "original_text": text,
            "revised_text": revised,
        },
    }


def interaction_control_node(state: StoryState) -> dict:
    """Interaction Control Agent: Process child's choice and update state."""
    selected = state.get("selected_option", "")
    history = state.get("interaction_history", [])
    scene_index = state.get("current_scene_index", 0)
    scene_text = state.get("current_scene_text", "")
    options = state.get("options", [])

    selected_text = selected
    for opt in options:
        if opt.get("key") == selected:
            selected_text = opt.get("text", selected)
            break

    history_entry = {
        "scene_index": scene_index,
        "text": scene_text,
        "choice": selected_text,
        "choice_key": selected,
    }
    new_history = history + [history_entry]

    return {
        "interaction_history": new_history,
        "current_scene_index": scene_index + 1,
        "selected_option": "",
    }


def summary_node(state: StoryState) -> dict:
    """Summary Agent: Generate story summary and encouragement after story ends."""
    llm = get_llm(temperature=0.7)
    history = state.get("interaction_history", [])
    theme = state.get("story_theme", "")
    character = state.get("main_character", "")
    profile = state.get("child_profile", {})
    nickname = profile.get("nickname", "小朋友")

    history_text = ""
    choices_text = ""
    for h in history:
        text = h.get("text", "")
        history_text += f"第{h.get('scene_index', 0) + 1}幕：{text[:120]}{'…' if len(text) > 120 else ''}\n"
        if h.get("choice"):
            choices_text += f"- {h['choice']}\n"

    prompt = f"""你是一位温暖的儿童教育专家。请为刚刚完成的故事生成总结。

故事主题：{theme}
主角：{character}
小读者昵称：{nickname}

故事经过：
{history_text}

孩子的选择：
{choices_text}

请生成JSON格式的总结，包含：
1. summary: 一段简短温暖的故事总结（50-100字）
2. encouragement: 对孩子的鼓励话语（30-50字）
3. parent_suggestion: 给家长的亲子互动建议（50-80字）
4. behavior_tags: 根据孩子的选择判断展现的品质标签（数组）

输出格式：
{{"summary": "...", "encouragement": "...", "parent_suggestion": "...", "behavior_tags": [...]}}"""

    messages = [
        SystemMessage(content="你是一位温暖亲切的儿童教育专家，善于发现孩子的闪光点并给予积极的反馈。"),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    content = response.content.strip()

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        result = {
            "summary": f"{nickname}完成了一个关于{theme}的精彩故事！",
            "encouragement": f"你真棒！{nickname}在故事中展现了很多好品质！",
            "parent_suggestion": "可以和孩子聊聊故事中最喜欢的部分，引导孩子思考故事中的道理。",
            "behavior_tags": ["勇敢", "好奇"],
        }

    return {
        "final_summary": result.get("summary", ""),
        "parent_suggestion": result.get("parent_suggestion", ""),
        "safety_result": state.get("safety_result", {}),
    }
