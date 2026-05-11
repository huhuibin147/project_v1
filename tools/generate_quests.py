#!/usr/bin/env python3
"""任务系统生成脚本 - 批量生成任务配置"""
import json
import random
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
OUTPUT_FILE = ROOT_DIR / "config" / "quests.json"

# ============================================================
# 数据源
# ============================================================

MONSTERS_DB = {}
monsters_file = ROOT_DIR / "config" / "monsters.json"
if monsters_file.exists():
    with open(monsters_file, "r", encoding="utf-8") as f:
        MONSTERS_DB = json.load(f)

ITEMS_DB = {}
items_file = ROOT_DIR / "config" / "items.json"
if items_file.exists():
    with open(items_file, "r", encoding="utf-8") as f:
        ITEMS_DB = json.load(f)

NPCS_DB = {}
npcs_file = ROOT_DIR / "config" / "npcs.json"
if npcs_file.exists():
    with open(npcs_file, "r", encoding="utf-8") as f:
        NPCS_DB = json.load(f)

# ============================================================
# NPC 人格模板
# ============================================================

NPC_PERSONALITIES = {
    "blacksmith": {
        "name": "铁匠老王",
        "tone": "粗犷豪爽",
        "dialogue_sets": {
            "collect": {
                "offer": [
                    "俺最近缺{item}，你能不能帮俺收集{count}个？",
                    "说起来，俺正愁{item}不够用呢。你去帮俺弄{count}个来咋样？",
                    "俺有个活儿，去搞{count}个{item}来。干不干？",
                ],
                "progress": [
                    "{item}还没凑齐呢？别急，慢慢来。",
                    "咋样了？{item}有着落没？",
                ],
                "complete": [
                    "太好了！{item}到手了！拿着，这是你的报酬！",
                    "干得漂亮！俺服了！来，重赏！",
                ],
                "reminder": [
                    "别忘了帮俺收集{item}啊，俺还等着用呢。",
                    "{item}的事别忘了，俺这边急用。",
                ],
            },
            "kill": {
                "offer": [
                    "最近{monster}越来越猖狂了，你能去清理{count}只吗？",
                    "说起来，俺正愁{monster}太多呢。你去干掉{count}只咋样？",
                    "俺有个活儿，去宰了{count}只{monster}。敢不敢？",
                ],
                "progress": [
                    "{monster}还没清理完？小心点，别受伤了。",
                    "咋样了？{monster}搞定没？",
                ],
                "complete": [
                    "干得漂亮！{monster}清理干净了！拿着，这是你的报酬！",
                    "好样的！这下俺能安心了。来，重赏！",
                ],
                "reminder": [
                    "别忘了清理{monster}啊，俺还等着呢。",
                    "{monster}的事别忘了，村里人还指望着呢。",
                ],
            },
            "talk": {
                "offer": [
                    "俺有个事，你去跟{target}说一声。干不干？",
                    "俺需要你帮俺跑个腿，去找{target}聊聊。",
                ],
                "progress": [
                    "跟{target}说过了没？别耽误了。",
                    "咋样了？{target}那边有消息没？",
                ],
                "complete": [
                    "好样的！{target}那边搞定了！拿着，这是你的报酬！",
                    "干得漂亮！来，重赏！",
                ],
                "reminder": [
                    "别忘了去找{target}啊，俺还等着回信呢。",
                    "{target}的事别忘了，别耽误了。",
                ],
            },
            "deliver": {
                "offer": [
                    "俺这里有{count}个{item}，你能帮俺送给{target}吗？",
                    "俺有个活儿，把{count}个{item}交给{target}。干不干？",
                ],
                "progress": [
                    "{item}送到{target}那没？别耽误了。",
                    "咋样了？{target}收到没？",
                ],
                "complete": [
                    "好样的！{target}收到{item}了！拿着，这是你的报酬！",
                    "干得漂亮！来，重赏！",
                ],
                "reminder": [
                    "别忘了把{item}送给{target}啊，俺还等着回信呢。",
                    "{target}的事别忘了，别耽误了。",
                ],
            },
            "explore": {
                "offer": [
                    "俺听说{map}那边有点不对劲，你能去探探路吗？",
                    "俺有个活儿，去{map}看看有啥情况。敢不敢？",
                ],
                "progress": [
                    "{map}那边探完了没？小心点。",
                    "咋样了？{map}有啥发现没？",
                ],
                "complete": [
                    "好样的！{map}探完了！拿着，这是你的报酬！",
                    "干得漂亮！来，重赏！",
                ],
                "reminder": [
                    "别忘了去{map}探路啊，俺还等着消息呢。",
                    "{map}的事别忘了，别耽误了。",
                ],
            },
        },
        "accept": ["好嘞！俺等着你的好消息！", "有种！俺就喜欢爽快人！", "行！别给俺丢脸啊！"],
        "decline": ["行吧，俺再找别人帮忙。", "也是，这活确实不轻松。", "那俺自己想办法吧。"],
    },
    "merchant": {
        "name": "杂货婆刘婶",
        "tone": "热情唠叨",
        "dialogue_sets": {
            "collect": {
                "offer": [
                    "哎呀，我铺子里缺{item}！你能不能帮我去收集{count}个？",
                    "说起来，我最近{item}快卖完了呢。你去帮我弄{count}个来咋样？",
                    "哎哟，有个事想拜托你，去帮我找{count}个{item}。",
                ],
                "progress": [
                    "{item}还没收齐？慢慢来，不着急。",
                    "咋样了？{item}找到没？",
                ],
                "complete": [
                    "太好了！{item}找来了！来，拿着这些，路上吃！",
                    "哎呀，太感谢了！这是给你的谢礼！",
                ],
                "reminder": [
                    "{item}的事别忘了啊，铺子里等着用呢。",
                    "别忘了帮我去收集{item}啊。",
                ],
            },
            "kill": {
                "offer": [
                    "哎呀，最近{monster}太多了！你能不能帮我去清理{count}只？",
                    "说起来，{monster}都快把路堵了。你去干掉{count}只咋样？",
                ],
                "progress": [
                    "{monster}还没清理？慢慢来，安全第一。",
                    "咋样了？{monster}搞定没？",
                ],
                "complete": [
                    "太好了！{monster}清理干净了！来，拿着这些谢礼！",
                    "哎呀，太感谢了！你真是个大好人！",
                ],
                "reminder": [
                    "{monster}的事别忘了啊，大家还指望着呢。",
                    "别忘了去清理{monster}啊。",
                ],
            },
            "talk": {
                "offer": [
                    "哎呀，有个事想拜托你，去跟{target}说一声。",
                    "哎哟，你能帮我去找{target}聊聊吗？",
                ],
                "progress": [
                    "跟{target}说过了没？慢慢来，不着急。",
                    "咋样了？{target}那边有消息没？",
                ],
                "complete": [
                    "太好了！{target}那边搞定了！来，拿着这些谢礼！",
                    "哎呀，太感谢了！你真是个大好人！",
                ],
                "reminder": [
                    "别忘了去找{target}啊，我还等着回信呢。",
                    "{target}的事别忘了啊。",
                ],
            },
            "deliver": {
                "offer": [
                    "哎呀，这里有{count}个{item}，你能帮我去送给{target}吗？",
                    "哎哟，有个事想拜托你，把{count}个{item}交给{target}。",
                ],
                "progress": [
                    "{item}送到{target}那没？慢慢来，不着急。",
                    "咋样了？{target}收到没？",
                ],
                "complete": [
                    "太好了！{target}收到{item}了！来，拿着这些谢礼！",
                    "哎呀，太感谢了！你真是个大好人！",
                ],
                "reminder": [
                    "别忘了把{item}送给{target}啊，我还等着回信呢。",
                    "{target}的事别忘了啊。",
                ],
            },
            "explore": {
                "offer": [
                    "哎呀，听说{map}那边有点不对劲，你能去探探路吗？",
                    "哎哟，你能帮我去{map}看看有啥情况吗？",
                ],
                "progress": [
                    "{map}那边探完了没？慢慢来，注意安全。",
                    "咋样了？{map}有啥发现没？",
                ],
                "complete": [
                    "太好了！{map}探完了！来，拿着这些谢礼！",
                    "哎呀，太感谢了！你真是个大好人！",
                ],
                "reminder": [
                    "别忘了去{map}探路啊，我还等着消息呢。",
                    "{map}的事别忘了啊。",
                ],
            },
        },
        "accept": ["太好了！你真是个勤快的孩子！", "哎呀，太感谢你了！", "好嘞！回来我给你做好吃的！"],
        "decline": ["哎，那我自己想办法吧。", "那算了，我换别的法子。", "好吧，我再找别人帮忙。"],
    },
    "herbalist": {
        "name": "采药人老林",
        "tone": "沉默寡言",
        "dialogue_sets": {
            "collect": {
                "offer": [
                    "……我需要{count}个{item}。你能帮忙吗？",
                    "……缺{item}。你去帮我找{count}个？",
                ],
                "progress": [
                    "……{item}还没凑齐？不急。",
                    "……慢慢来。",
                ],
                "complete": [
                    "……很好。这些{item}品质不错。这是你的报酬。",
                    "……多谢。这些对你有用。",
                ],
                "reminder": [
                    "……{item}的事，别忘了。",
                    "……别忘了那件事。",
                ],
            },
            "kill": {
                "offer": [
                    "……最近{monster}太多了。你能清理{count}只吗？",
                    "……{monster}挡路了。去干掉{count}只？",
                ],
                "progress": [
                    "……{monster}还没清理？注意安全。",
                    "……慢慢来。",
                ],
                "complete": [
                    "……干得好。{monster}清理干净了。这些给你。",
                    "……多谢。这些对你有用。",
                ],
                "reminder": [
                    "……{monster}的事，别忘了。",
                    "……别忘了那件事。",
                ],
            },
            "talk": {
                "offer": [
                    "……你去跟{target}说一声。",
                    "……找{target}聊聊。",
                ],
                "progress": [
                    "……跟{target}说过了？",
                    "……慢慢来。",
                ],
                "complete": [
                    "……好。{target}那边搞定了。这些给你。",
                    "……多谢。",
                ],
                "reminder": [
                    "……{target}的事，别忘了。",
                    "……别忘了那件事。",
                ],
            },
            "deliver": {
                "offer": [
                    "……这里有{count}个{item}，去送给{target}。",
                    "……把{count}个{item}交给{target}。",
                ],
                "progress": [
                    "……{item}送到{target}那了？",
                    "……慢慢来。",
                ],
                "complete": [
                    "……好。{target}收到{item}了。这些给你。",
                    "……多谢。",
                ],
                "reminder": [
                    "……把{item}送给{target}的事，别忘了。",
                    "……别忘了那件事。",
                ],
            },
            "explore": {
                "offer": [
                    "……去{map}看看。",
                    "……{map}那边有点不对劲。去探探。",
                ],
                "progress": [
                    "……{map}探完了？",
                    "……慢慢来。",
                ],
                "complete": [
                    "……好。{map}探完了。这些给你。",
                    "……多谢。",
                ],
                "reminder": [
                    "……去{map}的事，别忘了。",
                    "……别忘了那件事。",
                ],
            },
        },
        "accept": ["……好。我会等你的。", "……多谢。", "……小心。"],
        "decline": ["……也罢。", "……理解。", "……那我自己去。"],
    },
    "priest": {
        "name": "祭司阿雅",
        "tone": "温柔虔诚",
        "dialogue_sets": {
            "collect": {
                "offer": [
                    "我感应到需要{count}个{item}……冒险者，你能去收集吗？这对净化这片土地很重要。",
                    "愿光明指引你。我需要{count}个{item}。你愿意帮忙吗？",
                ],
                "progress": [
                    "还没有完成吗？继续努力吧，光明与你同在。",
                    "不要放弃，光明就在前方。",
                ],
                "complete": [
                    "感谢你！{item}收集完成了。这是神殿的谢礼。",
                    "愿光明永远照耀你。这是你的报酬。",
                ],
                "reminder": [
                    "别忘了收集{item}的使命。",
                    "{item}的事，别忘了。",
                ],
            },
            "kill": {
                "offer": [
                    "我感应到{monster}的邪恶气息……冒险者，你能去清除{count}只吗？这对净化这片土地很重要。",
                    "愿光明指引你。{monster}在危害这片土地，去清除{count}只吧。",
                ],
                "progress": [
                    "还没有完成吗？继续努力吧，光明与你同在。",
                    "不要放弃，光明就在前方。",
                ],
                "complete": [
                    "感谢你！{monster}清理干净了。这是神殿的谢礼。",
                    "愿光明永远照耀你。这是你的报酬。",
                ],
                "reminder": [
                    "别忘了清除{monster}的使命。",
                    "{monster}的事，别忘了。",
                ],
            },
            "talk": {
                "offer": [
                    "我感应到需要你去跟{target}说一声……冒险者，你愿意帮忙吗？这对维系这片土地的和谐很重要。",
                    "愿光明指引你。去和{target}聊聊吧。",
                ],
                "progress": [
                    "还没有完成吗？继续努力吧，光明与你同在。",
                    "不要放弃，光明就在前方。",
                ],
                "complete": [
                    "感谢你！{target}那边搞定了。这是神殿的谢礼。",
                    "愿光明永远照耀你。这是你的报酬。",
                ],
                "reminder": [
                    "别忘了去跟{target}说一声的使命。",
                    "{target}的事，别忘了。",
                ],
            },
            "deliver": {
                "offer": [
                    "我感应到需要把{count}个{item}送给{target}……冒险者，你愿意帮忙吗？这对维系这片土地的和谐很重要。",
                    "愿光明指引你。去把{count}个{item}交给{target}吧。",
                ],
                "progress": [
                    "还没有完成吗？继续努力吧，光明与你同在。",
                    "不要放弃，光明就在前方。",
                ],
                "complete": [
                    "感谢你！{target}收到{item}了。这是神殿的谢礼。",
                    "愿光明永远照耀你。这是你的报酬。",
                ],
                "reminder": [
                    "别忘了把{item}送给{target}的使命。",
                    "{target}的事，别忘了。",
                ],
            },
            "explore": {
                "offer": [
                    "我感应到{map}那边有黑暗气息……冒险者，你能去探索一下吗？这对净化这片土地很重要。",
                    "愿光明指引你。去{map}看看吧，那里需要你的帮助。",
                ],
                "progress": [
                    "还没有完成吗？继续努力吧，光明与你同在。",
                    "不要放弃，光明就在前方。",
                ],
                "complete": [
                    "感谢你！{map}探索完成了。这是神殿的谢礼。",
                    "愿光明永远照耀你。这是你的报酬。",
                ],
                "reminder": [
                    "别忘了去{map}探索的使命。",
                    "{map}的事，别忘了。",
                ],
            },
        },
        "accept": ["愿光明庇佑你。小心行事。", "感谢你。光明与你同在。", "太好了，愿神灵保佑你。"],
        "decline": ["我理解，这确实不是轻松的差事。", "没关系，光明会找到合适的人。", "我尊重你的选择。"],
    },
    "skill_master": {
        "name": "导师艾尔文",
        "tone": "严肃严厉",
        "dialogue_sets": {
            "collect": {
                "offer": [
                    "年轻人，去收集{count}个{item}，这是对你的考验。",
                    "老夫需要{count}个{item}。你敢去吗？",
                ],
                "progress": [
                    "还没完成？这可是最基本的考验。",
                    "加把劲，别让老夫等太久。",
                ],
                "complete": [
                    "不错，{item}收集齐了。拿着，这是你的奖励。",
                    "做得好！但还不够，继续努力。",
                ],
                "reminder": [
                    "考验还没完成，别让老夫等太久。",
                    "别忘了收集{item}，这是对你的考验。",
                ],
            },
            "kill": {
                "offer": [
                    "年轻人，去击杀{count}只{monster}，这是对你的考验。",
                    "老夫想看看你的实力。去干掉{count}只{monster}。",
                ],
                "progress": [
                    "还没完成？这可是最基本的考验。",
                    "加把劲，别让老夫等太久。",
                ],
                "complete": [
                    "不错，{monster}清理干净了。拿着，这是你的奖励。",
                    "做得好！但还不够，继续努力。",
                ],
                "reminder": [
                    "考验还没完成，别让老夫等太久。",
                    "别忘了击杀{monster}，这是对你的考验。",
                ],
            },
            "talk": {
                "offer": [
                    "年轻人，去跟{target}说一声，这是对你的考验。",
                    "老夫想看看你的沟通能力。去找{target}聊聊。",
                ],
                "progress": [
                    "还没完成？这可是最基本的考验。",
                    "加把劲，别让老夫等太久。",
                ],
                "complete": [
                    "不错，{target}那边搞定了。拿着，这是你的奖励。",
                    "做得好！但还不够，继续努力。",
                ],
                "reminder": [
                    "考验还没完成，别让老夫等太久。",
                    "别忘了去找{target}，这是对你的考验。",
                ],
            },
            "deliver": {
                "offer": [
                    "年轻人，去把{count}个{item}送给{target}，这是对你的考验。",
                    "老夫想看看你的责任心。去把{count}个{item}交给{target}。",
                ],
                "progress": [
                    "还没完成？这可是最基本的考验。",
                    "加把劲，别让老夫等太久。",
                ],
                "complete": [
                    "不错，{target}收到{item}了。拿着，这是你的奖励。",
                    "做得好！但还不够，继续努力。",
                ],
                "reminder": [
                    "考验还没完成，别让老夫等太久。",
                    "别忘了把{item}送给{target}，这是对你的考验。",
                ],
            },
            "explore": {
                "offer": [
                    "年轻人，去{map}探索一下，这是对你的考验。",
                    "老夫想看看你的勇气。去{map}看看。",
                ],
                "progress": [
                    "还没完成？这可是最基本的考验。",
                    "加把劲，别让老夫等太久。",
                ],
                "complete": [
                    "不错，{map}探索完成了。拿着，这是你的奖励。",
                    "做得好！但还不够，继续努力。",
                ],
                "reminder": [
                    "考验还没完成，别让老夫等太久。",
                    "别忘了去{map}探索，这是对你的考验。",
                ],
            },
        },
        "accept": ["很好，不要让老夫失望。", "有种！去吧。", "好！让老夫看看你的本事。"],
        "decline": ["哼，果然是缺乏勇气。", "也罢，等你准备好了再来。", "实力不够就先去练练。"],
    },
}

# ============================================================
# 物品分类
# ============================================================

ITEM_CATEGORIES = {
    "material": ["iron_ore", "herb", "mushroom", "beast_bone", "magic_crystal", "wolf_pelt", "spider_silk"],
    "consumable": ["health_potion", "mana_potion", "greater_health_potion", "bandage", "antidote", "bread", "dried_meat"],
    "special": ["strength_elixir", "purify_potion", "holy_water"],
}

# ============================================================
# 怪物标签映射
# ============================================================

MONSTER_TAGS = {}
for mid, mcfg in MONSTERS_DB.items():
    tags = mcfg.get("tags", [])
    MONSTER_TAGS[mid] = tags

# ============================================================
# 工具函数
# ============================================================

def get_item_name(item_id: str) -> str:
    return ITEMS_DB.get(item_id, {}).get("name", item_id)

def get_monster_name(monster_id: str) -> str:
    return MONSTERS_DB.get(monster_id, {}).get("name", monster_id)

def get_npc_name(npc_id: str) -> str:
    return NPCS_DB.get(npc_id, {}).get("name", npc_id)

def pick_random(lst: list) -> str:
    return random.choice(lst)

def calc_rewards(level: int, difficulty: int, objective_count: int = 1) -> dict:
    base_exp = 20 + level * 10 + difficulty * 15
    base_gold = 30 + level * 8 + difficulty * 12
    exp = int(base_exp * (0.8 + random.random() * 0.4))
    gold = int(base_gold * (0.8 + random.random() * 0.4))
    affinity = 5 + difficulty * 3 + random.randint(0, 3)
    return {"exp": exp, "gold": gold, "affinity": affinity}

def generate_dialogue(personality: dict, quest: dict) -> dict:
    objectives = quest["objectives"]
    obj = objectives[0]
    obj_type = obj["type"]

    # 获取对话模板集（按任务类型）
    dialogue_sets = personality.get("dialogue_sets", {})
    templates = dialogue_sets.get(obj_type, dialogue_sets.get("collect", {}))

    # 提取关键信息
    if obj_type == "collect":
        item_name = get_item_name(obj.get("item_id", ""))
        count = obj.get("count", 1)
        ctx = {"item": item_name, "count": count}
    elif obj_type == "kill":
        if obj.get("target"):
            monster_name = get_monster_name(obj["target"])
        elif obj.get("target_tags"):
            monster_name = f"{obj['target_tags'][0]}怪物"
        else:
            monster_name = "怪物"
        count = obj.get("count", 1)
        ctx = {"monster": monster_name, "count": count}
    elif obj_type == "talk":
        target_name = get_npc_name(obj.get("npc_id", ""))
        ctx = {"target": target_name}
    elif obj_type == "deliver":
        item_name = get_item_name(obj.get("item_id", ""))
        target_name = get_npc_name(obj.get("target_npc_id", ""))
        count = obj.get("count", 1)
        ctx = {"item": item_name, "target": target_name, "count": count}
    elif obj_type == "explore":
        map_id = obj.get("map_id", "")
        ctx = {"map": map_id}
    else:
        ctx = {}

    def fill(template_str: str) -> str:
        result = template_str
        for key, val in ctx.items():
            result = result.replace(f"{{{key}}}", str(val))
        return result

    offer = fill(pick_random(templates.get("offer", ["你能帮忙完成任务吗？"])))
    accept = pick_random(personality.get("accept", ["好的！"]))
    decline = pick_random(personality.get("decline", ["那算了。"]))
    progress = fill(pick_random(templates.get("progress", ["还没完成吗？"])))
    complete = fill(pick_random(templates.get("complete", ["任务完成了！这是你的报酬。"])))
    reminder = fill(pick_random(templates.get("reminder", ["别忘了完成任务。"])))

    return {
        "offer": offer,
        "accept": accept,
        "decline": decline,
        "progress": progress,
        "complete": complete,
        "reminder": reminder,
    }

# ============================================================
# 任务模板生成器
# ============================================================

def make_collect_quest(quest_id, name, description, npc_id, item_id, count, level, prerequisites=None, reward_items=None):
    personality = NPC_PERSONALITIES.get(npc_id, NPC_PERSONALITIES["merchant"])
    item_name = get_item_name(item_id)
    quest = {
        "id": quest_id,
        "name": name,
        "description": description,
        "type": "side",
        "npc_id": npc_id,
        "prerequisites": prerequisites or {"level": level, "quests_completed": [], "npc_affinity": 0},
        "objectives": [
            {"type": "collect", "item_id": item_id, "count": count, "description": f"收集{count}个{item_name}"}
        ],
        "rewards": {},
        "dialogue": {},
    }
    rewards = calc_rewards(level, len(prerequisites.get("quests_completed", []) if prerequisites else 0))
    reward_items_list = []
    if reward_items:
        for rid, rqty in reward_items:
            reward_items_list.append({"item_id": rid, "quantity": rqty})
    quest["rewards"] = {
        "exp": rewards["exp"],
        "gold": rewards["gold"],
        "items": reward_items_list,
        "affinity": {"npc_id": npc_id, "value": rewards["affinity"]},
    }
    quest["dialogue"] = generate_dialogue(personality, quest)
    return quest

def make_kill_quest(quest_id, name, description, npc_id, monster_id, count, level, prerequisites=None, reward_items=None, use_tags=False):
    personality = NPC_PERSONALITIES.get(npc_id, NPC_PERSONALITIES["blacksmith"])
    monster_name = get_monster_name(monster_id)
    tags = MONSTER_TAGS.get(monster_id, [])
    quest = {
        "id": quest_id,
        "name": name,
        "description": description,
        "type": "side",
        "npc_id": npc_id,
        "prerequisites": prerequisites or {"level": level, "quests_completed": [], "npc_affinity": 0},
        "objectives": [],
        "rewards": {},
        "dialogue": {},
    }
    if use_tags and tags:
        quest["objectives"] = [
            {"type": "kill", "target": "", "target_tags": tags, "count": count, "description": f"击杀{count}只{tags[0]}怪物"}
        ]
    else:
        quest["objectives"] = [
            {"type": "kill", "target": monster_id, "target_tags": [], "count": count, "description": f"击杀{count}只{monster_name}"}
        ]
    rewards = calc_rewards(level, len(prerequisites.get("quests_completed", []) if prerequisites else 0) + 1)
    reward_items_list = []
    if reward_items:
        for rid, rqty in reward_items:
            reward_items_list.append({"item_id": rid, "quantity": rqty})
    quest["rewards"] = {
        "exp": rewards["exp"],
        "gold": rewards["gold"],
        "items": reward_items_list,
        "affinity": {"npc_id": npc_id, "value": rewards["affinity"]},
    }
    quest["dialogue"] = generate_dialogue(personality, quest)
    return quest

def make_talk_quest(quest_id, name, description, npc_id, target_npc_id, level, prerequisites=None, reward_items=None):
    personality = NPC_PERSONALITIES.get(npc_id, NPC_PERSONALITIES["merchant"])
    target_name = get_npc_name(target_npc_id)
    quest = {
        "id": quest_id,
        "name": name,
        "description": description,
        "type": "side",
        "npc_id": npc_id,
        "prerequisites": prerequisites or {"level": level, "quests_completed": [], "npc_affinity": 0},
        "objectives": [
            {"type": "talk", "npc_id": target_npc_id, "description": f"与{target_name}对话"}
        ],
        "rewards": {},
        "dialogue": {},
    }
    rewards = calc_rewards(level, 0)
    reward_items_list = []
    if reward_items:
        for rid, rqty in reward_items:
            reward_items_list.append({"item_id": rid, "quantity": rqty})
    quest["rewards"] = {
        "exp": rewards["exp"],
        "gold": rewards["gold"],
        "items": reward_items_list,
        "affinity": {"npc_id": npc_id, "value": rewards["affinity"]},
    }
    quest["dialogue"] = generate_dialogue(personality, quest)
    return quest

def make_explore_quest(quest_id, name, description, npc_id, map_id, x, y, radius, level, prerequisites=None, reward_items=None):
    personality = NPC_PERSONALITIES.get(npc_id, NPC_PERSONALITIES["herbalist"])
    quest = {
        "id": quest_id,
        "name": name,
        "description": description,
        "type": "side",
        "npc_id": npc_id,
        "prerequisites": prerequisites or {"level": level, "quests_completed": [], "npc_affinity": 0},
        "objectives": [
            {"type": "explore", "map_id": map_id, "x": x, "y": y, "radius": radius, "description": f"探索{map_id}地图的({x},{y})附近区域"}
        ],
        "rewards": {},
        "dialogue": {},
    }
    rewards = calc_rewards(level, 2)
    reward_items_list = []
    if reward_items:
        for rid, rqty in reward_items:
            reward_items_list.append({"item_id": rid, "quantity": rqty})
    quest["rewards"] = {
        "exp": rewards["exp"],
        "gold": rewards["gold"],
        "items": reward_items_list,
        "affinity": {"npc_id": npc_id, "value": rewards["affinity"]},
    }
    quest["dialogue"] = generate_dialogue(personality, quest)
    return quest

def make_deliver_quest(quest_id, name, description, npc_id, item_id, count, target_npc_id, level, prerequisites=None, reward_items=None):
    personality = NPC_PERSONALITIES.get(npc_id, NPC_PERSONALITIES["merchant"])
    item_name = get_item_name(item_id)
    target_name = get_npc_name(target_npc_id)
    quest = {
        "id": quest_id,
        "name": name,
        "description": description,
        "type": "side",
        "npc_id": npc_id,
        "prerequisites": prerequisites or {"level": level, "quests_completed": [], "npc_affinity": 0},
        "objectives": [
            {"type": "deliver", "item_id": item_id, "count": count, "target_npc_id": target_npc_id, "description": f"将{count}个{item_name}交给{target_name}"}
        ],
        "rewards": {},
        "dialogue": {},
    }
    rewards = calc_rewards(level, 1)
    reward_items_list = []
    if reward_items:
        for rid, rqty in reward_items:
            reward_items_list.append({"item_id": rid, "quantity": rqty})
    quest["rewards"] = {
        "exp": rewards["exp"],
        "gold": rewards["gold"],
        "items": reward_items_list,
        "affinity": {"npc_id": npc_id, "value": rewards["affinity"]},
    }
    quest["dialogue"] = generate_dialogue(personality, quest)
    return quest

# ============================================================
# 任务链生成器
# ============================================================

def generate_npc_quest_chain(npc_id: str, chain_config: list) -> list:
    quests = []
    prev_quest_id = None
    for i, cfg in enumerate(chain_config):
        quest_id = cfg.get("quest_id", f"{npc_id}_quest_{i}")
        prerequisites = {
            "level": cfg.get("level", 1),
            "quests_completed": [prev_quest_id] if prev_quest_id and cfg.get("chain", True) else [],
            "npc_affinity": cfg.get("affinity_req", 0),
        }
        qtype = cfg.get("type", "collect")
        if qtype == "collect":
            q = make_collect_quest(
                quest_id=quest_id,
                name=cfg["name"],
                description=cfg["description"],
                npc_id=npc_id,
                item_id=cfg["item_id"],
                count=cfg.get("count", 1),
                level=cfg.get("level", 1),
                prerequisites=prerequisites,
                reward_items=cfg.get("reward_items"),
            )
        elif qtype == "kill":
            q = make_kill_quest(
                quest_id=quest_id,
                name=cfg["name"],
                description=cfg["description"],
                npc_id=npc_id,
                monster_id=cfg.get("monster_id", "slime"),
                count=cfg.get("count", 1),
                level=cfg.get("level", 1),
                prerequisites=prerequisites,
                reward_items=cfg.get("reward_items"),
                use_tags=cfg.get("use_tags", False),
            )
        elif qtype == "talk":
            q = make_talk_quest(
                quest_id=quest_id,
                name=cfg["name"],
                description=cfg["description"],
                npc_id=npc_id,
                target_npc_id=cfg["target_npc_id"],
                level=cfg.get("level", 1),
                prerequisites=prerequisites,
                reward_items=cfg.get("reward_items"),
            )
        elif qtype == "deliver":
            q = make_deliver_quest(
                quest_id=quest_id,
                name=cfg["name"],
                description=cfg["description"],
                npc_id=npc_id,
                item_id=cfg["item_id"],
                count=cfg.get("count", 1),
                target_npc_id=cfg["target_npc_id"],
                level=cfg.get("level", 1),
                prerequisites=prerequisites,
                reward_items=cfg.get("reward_items"),
            )
        elif qtype == "explore":
            q = make_explore_quest(
                quest_id=quest_id,
                name=cfg["name"],
                description=cfg["description"],
                npc_id=npc_id,
                map_id=cfg.get("map_id", "forest"),
                x=cfg.get("x", 40),
                y=cfg.get("y", 20),
                radius=cfg.get("radius", 5),
                level=cfg.get("level", 1),
                prerequisites=prerequisites,
                reward_items=cfg.get("reward_items"),
            )
        else:
            continue
        quests.append(q)
        prev_quest_id = quest_id
    return quests

# ============================================================
# 预设任务链
# ============================================================

def get_all_quest_chains() -> dict:
    return {
        "blacksmith": [
            {
                "quest_id": "blacksmith_ore",
                "name": "铁匠的委托",
                "description": "铁匠老王最近铁矿储备不足，需要冒险者帮忙收集铁矿来维持铁匠铺的运转。",
                "type": "collect", "item_id": "iron_ore", "count": 3, "level": 1, "chain": False,
                "reward_items": [],
            },
            {
                "quest_id": "blacksmith_wolf",
                "name": "狼患",
                "description": "森林里的野狼越来越猖狂，铁匠老王希望有人能清理一些，保护村民安全。",
                "type": "kill", "monster_id": "wild_wolf", "count": 2, "level": 2, "chain": True,
                "reward_items": [("bandage", 3)],
            },
            {
                "quest_id": "blacksmith_bear",
                "name": "暗熊之威胁",
                "description": "森林深处出现了一只凶暴的暗熊，铁匠老王希望有实力的冒险者能除掉它。",
                "type": "kill", "monster_id": "dark_bear", "count": 1, "level": 4, "chain": True, "affinity_req": 20,
                "reward_items": [("strength_elixir", 1)],
            },
        ],
        "merchant": [
            {
                "quest_id": "merchant_herb",
                "name": "草药收集",
                "description": "杂货婆刘婶的草药库存告急，需要冒险者帮忙收集草药。",
                "type": "collect", "item_id": "herb", "count": 5, "level": 1, "chain": False,
                "reward_items": [("bread", 3)],
            },
            {
                "quest_id": "merchant_deliver",
                "name": "跑腿送货",
                "description": "刘婶有一批货物需要送到神殿给祭司阿雅，但她走不开，需要冒险者帮忙跑腿。",
                "type": "talk", "target_npc_id": "priest", "level": 1, "chain": True,
                "reward_items": [],
            },
            {
                "quest_id": "merchant_mushroom",
                "name": "蘑菇美食",
                "description": "刘婶想尝试一道新菜，需要新鲜的蘑菇作为食材。",
                "type": "collect", "item_id": "mushroom", "count": 3, "level": 1, "chain": False,
                "reward_items": [("dried_meat", 2)],
            },
        ],
        "herbalist": [
            {
                "quest_id": "herbalist_herb",
                "name": "稀有草药",
                "description": "采药人老林需要一些草药和魔法水晶来炼制特殊药剂。",
                "type": "collect", "item_id": "herb", "count": 5, "level": 2, "chain": False,
                "reward_items": [("greater_health_potion", 2)],
            },
            {
                "quest_id": "herbalist_spider",
                "name": "毒蛛之患",
                "description": "森林中的毒蛛越来越多，威胁到采药人的安全，需要清理一些。",
                "type": "kill", "monster_id": "forest_spider", "count": 2, "level": 3, "chain": True, "affinity_req": 10,
                "reward_items": [("antidote", 3)],
            },
            {
                "quest_id": "herbalist_explore",
                "name": "森林深处",
                "description": "老林希望有人能探索森林深处的区域，那里可能隐藏着珍贵的药材。",
                "type": "explore", "map_id": "forest", "x": 42, "y": 38, "radius": 5, "level": 3, "chain": True, "affinity_req": 15,
                "reward_items": [("magic_crystal", 3)],
            },
        ],
        "priest": [
            {
                "quest_id": "priest_purify",
                "name": "神圣净化",
                "description": "祭司阿雅感应到森林中的邪恶气息，希望冒险者能清除一些森林怪物来净化这片土地。",
                "type": "kill", "monster_id": "slime", "count": 3, "level": 2, "chain": False, "use_tags": True,
                "reward_items": [("health_potion", 2)],
            },
            {
                "quest_id": "priest_deliver",
                "name": "圣水传递",
                "description": "祭司阿雅需要将一瓶圣水送到森林中的采药人老林手中，以保护他免受邪恶侵害。",
                "type": "talk", "target_npc_id": "herbalist", "level": 2, "chain": True, "affinity_req": 10,
                "reward_items": [("purify_potion", 1)],
            },
        ],
        "skill_master": [
            {
                "quest_id": "skillmaster_test",
                "name": "初级试炼",
                "description": "导师艾尔文要求你通过一个简单的试炼——击杀几只史莱姆来证明你的实力。",
                "type": "kill", "monster_id": "slime", "count": 3, "level": 1, "chain": False,
                "reward_items": [("bandage", 2)],
            },
            {
                "quest_id": "skillmaster_goblin",
                "name": "哥布林骚扰",
                "description": "哥布林不断骚扰过往的旅人，导师艾尔文希望你能处理这个问题。",
                "type": "kill", "monster_id": "goblin", "count": 2, "level": 3, "chain": True, "affinity_req": 10,
                "reward_items": [("mana_potion", 2)],
            },
            {
                "quest_id": "skillmaster_bone",
                "name": "骨材收集",
                "description": "导师艾尔文需要一些兽骨来研究古代战斗技艺，需要冒险者帮忙收集。",
                "type": "collect", "item_id": "beast_bone", "count": 2, "level": 2, "chain": True, "affinity_req": 5,
                "reward_items": [("strength_elixir", 1)],
            },
        ],
    }

# ============================================================
# 主函数
# ============================================================

def generate_quests(output_file: Path = None, seed: int = None, chains: dict = None):
    if seed is not None:
        random.seed(seed)
    if output_file is None:
        output_file = OUTPUT_FILE
    if chains is None:
        chains = get_all_quest_chains()

    all_quests = {}
    total = 0
    for npc_id, chain in chains.items():
        npc_quests = generate_npc_quest_chain(npc_id, chain)
        for q in npc_quests:
            all_quests[q["id"]] = q
            total += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_quests, f, ensure_ascii=False, indent=2)

    print(f"任务生成完成！共 {total} 个任务，输出到: {output_file}")
    for npc_id, chain in chains.items():
        npc_name = NPC_PERSONALITIES.get(npc_id, {}).get("name", npc_id)
        print(f"  {npc_name}: {len(chain)} 个任务")
        for q in chain:
            print(f"    - {q.get('quest_id')}: {q.get('name')} (Lv.{q.get('level', 1)})")

    return all_quests


def generate_single_quest(quest_id, quest_type, name, description, level=1,
                          npc_id=None, target_monster=None, target_item=None,
                          target_npc=None, target_map=None, count=1,
                          rewards=None):
    quest = {
        "id": quest_id,
        "name": name,
        "description": description,
        "type": quest_type,
        "level": level,
        "npc_id": npc_id or "quest_giver",
        "status": "available",
        "objectives": [],
        "rewards": rewards or {"exp": level * 10, "gold": level * 5, "items": []},
    }
    if quest_type == "kill":
        quest["objectives"].append({
            "type": "kill",
            "target": target_monster or "slime",
            "count": count,
            "current": 0,
        })
    elif quest_type == "collect":
        quest["objectives"].append({
            "type": "collect",
            "target": target_item or "herb",
            "count": count,
            "current": 0,
        })
    elif quest_type == "talk":
        quest["objectives"].append({
            "type": "talk",
            "target": target_npc or "merchant",
        })
    elif quest_type == "deliver":
        quest["objectives"].append({
            "type": "deliver",
            "target": target_npc or "merchant",
            "item": target_item or "letter",
            "count": count,
            "current": 0,
        })
    elif quest_type == "explore":
        quest["objectives"].append({
            "type": "explore",
            "target": target_map or "cave",
        })
    personality = NPC_PERSONALITIES.get(quest["npc_id"], NPC_PERSONALITIES.get("blacksmith"))
    dialogue_set = personality["dialogue_sets"].get(quest_type, personality["dialogue_sets"]["kill"])
    quest["dialogue"] = {
        "offer": random.choice(dialogue_set["offer"]),
        "progress": random.choice(dialogue_set["progress"]),
        "complete": random.choice(dialogue_set["complete"]),
        "reminder": random.choice(dialogue_set["reminder"]),
    }
    quest["dialogue"]["accept"] = random.choice(personality["accept"])
    quest["dialogue"]["decline"] = random.choice(personality["decline"])
    return quest


def validate_quests(quests_file=None):
    if quests_file is None:
        quests_file = OUTPUT_FILE
    if not quests_file.exists():
        print(f"错误：任务文件 '{quests_file}' 不存在")
        return 1
    with open(quests_file, "r", encoding="utf-8") as f:
        quests = json.load(f)
    issues = []
    for qid, quest in quests.items():
        if quest.get("id") != qid:
            issues.append(f"{qid}: id 不匹配（字段中为 {quest.get('id')}）")
        for field in ["name", "description", "type", "level", "npc_id", "objectives", "rewards"]:
            if field not in quest:
                issues.append(f"{qid}: 缺少必填字段 '{field}'")
        for i, obj in enumerate(quest.get("objectives", [])):
            if "type" not in obj:
                issues.append(f"{qid}: objectives[{i}] 缺少 type")
            if obj.get("type") in ("kill", "collect", "deliver") and "count" not in obj:
                issues.append(f"{qid}: objectives[{i}] 类型 {obj.get('type')} 需要 count")
            if "target" not in obj:
                issues.append(f"{qid}: objectives[{i}] 缺少 target")
        rewards = quest.get("rewards", {})
        if "exp" not in rewards:
            issues.append(f"{qid}: rewards 缺少 exp")
        if "gold" not in rewards:
            issues.append(f"{qid}: rewards 缺少 gold")
        if quest.get("type") == "kill":
            target = None
            for obj in quest.get("objectives", []):
                if obj.get("type") == "kill":
                    target = obj.get("target")
            if target and target not in MONSTERS_DB:
                issues.append(f"{qid}: 击杀目标 '{target}' 不在怪物数据库中")
        if quest.get("type") == "collect":
            target = None
            for obj in quest.get("objectives", []):
                if obj.get("type") == "collect":
                    target = obj.get("target")
            if target and target not in ITEMS_DB:
                issues.append(f"{qid}: 收集目标 '{target}' 不在物品数据库中")
    if issues:
        print(f"验证发现 {len(issues)} 个问题：")
        for issue in issues:
            print(f"  ⚠ {issue}")
    else:
        print(f"验证通过！共 {len(quests)} 个任务")
    return len(issues)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python generate_quests.py <命令> [参数]")
        print("\n命令:")
        print("  generate [seed]       生成所有任务（默认seed=42）")
        print("  single <id> <type> <name> <level>  生成单个任务")
        print("  validate              验证任务配置")
        print("  list                  列出所有任务")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "generate":
        seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
        generate_quests(seed=seed)
    elif cmd == "single":
        if len(sys.argv) < 6:
            print("用法: python generate_quests.py single <id> <type> <name> <level>")
            print("类型: kill, collect, talk, deliver, explore")
            sys.exit(1)
        quest = generate_single_quest(
            quest_id=sys.argv[2],
            quest_type=sys.argv[3],
            name=sys.argv[4],
            level=int(sys.argv[5]),
        )
        quests = {}
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                quests = json.load(f)
        quests[quest["id"]] = quest
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(quests, f, ensure_ascii=False, indent=2)
        print(f"已生成任务: {quest['id']} - {quest['name']}")
    elif cmd == "validate":
        validate_quests()
    elif cmd == "list":
        if not OUTPUT_FILE.exists():
            print("任务文件不存在，请先生成")
            sys.exit(1)
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            quests = json.load(f)
        print(f"\n共 {len(quests)} 个任务:\n")
        for qid, q in sorted(quests.items(), key=lambda x: x[1].get("level", 0)):
            print(f"  [{q.get('type','?'):8s}] Lv.{q.get('level',1):2d} {qid}: {q.get('name','?')}")
    else:
        print(f"未知命令: {cmd}")
