import json

concept_categories = {
    "实相与创造": [
        {"zh": "你创造你自己的实相", "en": "You Create Your Own Reality"},
        {"zh": "信念系统", "en": "Belief Systems"},
        {"zh": "力量之点", "en": "Point of Power"},
        {"zh": "电磁能量单位(EE)", "en": "Electromagnetic Energy Units"},
        {"zh": "意识基本单元(CU)", "en": "Consciousness Units"},
        {"zh": "伪装系统", "en": "Camouflage System"},
        {"zh": "根假设", "en": "Root Assumptions"},
        {"zh": "强度法则", "en": "Law of Intensity"},
        {"zh": "思想物质化", "en": "Materialization of Thought"},
        {"zh": "内在风暴与外在风暴", "en": "Inner and Outer Storms"},
        {"zh": "自然恩典", "en": "Natural Grace"},
        {"zh": "创造性破坏", "en": "Creative Destruction"},
        {"zh": "自我实现的预言", "en": "Self-Fulfilling Prophecy"},
        {"zh": "期望效应", "en": "Expectation Effect"},
        {"zh": "情感作为能量", "en": "Emotion as Energy"},
        {"zh": "暗示的力量", "en": "Power of Suggestion"},
        {"zh": "心理环境", "en": "Psychological Environment"},
        {"zh": "价值气候", "en": "Value Climate"},
        {"zh": "肯定与声明", "en": "Affirmation"},
        {"zh": "心理/灵性交叠通道", "en": "Psychic Warp"}
    ],
    "意识与感知": [
        {"zh": "意识", "en": "Consciousness"},
        {"zh": "内在感官", "en": "Inner Senses"},
        {"zh": "外在自我", "en": "Outer Ego"},
        {"zh": "内在自我", "en": "Inner Ego"},
        {"zh": "自然催眠", "en": "Natural Hypnosis"},
        {"zh": "多重焦点", "en": "Multiple Focus"},
        {"zh": "意识专门化", "en": "Specialization of Consciousness"},
        {"zh": "内在感知器", "en": "Inner Perceptors"},
        {"zh": "心理现实", "en": "Psychological Reality"},
        {"zh": "主观现实", "en": "Subjective Reality"},
        {"zh": "客观现实", "en": "Objective Reality"},
        {"zh": "意识等级", "en": "Degrees of Consciousness"},
        {"zh": "意识焦点", "en": "Focus of Consciousness"},
        {"zh": "知觉过滤器", "en": "Perceptual Filters"},
        {"zh": "意识的侧池", "en": "Sidepools of Consciousness"},
        {"zh": "全意识", "en": "Whole Consciousness"},
        {"zh": "意识能量格式塔", "en": "Gestalt of Aware Energy"}
    ],
    "多维自我与身份": [
        {"zh": "多维人格", "en": "Multidimensional Personality"},
        {"zh": "实体/灵魂", "en": "Entity/Soul"},
        {"zh": "人格片段", "en": "Fragment Personality"},
        {"zh": "可能性的自我", "en": "Probable Selves"},
        {"zh": "轮回转世", "en": "Reincarnation"},
        {"zh": "同时性生命", "en": "Simultaneous Lives"},
        {"zh": "梦自我", "en": "Dreaming Self"},
        {"zh": "物理自我", "en": "Physical Self"},
        {"zh": "意识身份", "en": "Conscious Identity"},
        {"zh": "内在身份", "en": "Inner Identity"},
        {"zh": "多维存在", "en": "Multidimensional Existence"},
        {"zh": "意识流", "en": "Consciousness Stream"},
        {"zh": "种族心理库", "en": "Racial Psychic Bank"},
        {"zh": "集体意识", "en": "Collective Consciousness"},
        {"zh": "个体化意识", "en": "Individualized Consciousness"},
        {"zh": "存在层面", "en": "Planes of Existence"},
        {"zh": "角色自我", "en": "Ego/Role Self"},
        {"zh": "核心自我", "en": "Core Self"}
    ],
    "时间与空间": [
        {"zh": "同时性时间", "en": "Simultaneous Time"},
        {"zh": "时刻之点", "en": "Moment Point"},
        {"zh": "心理时间", "en": "Psychological Time"},
        {"zh": "线性时间幻觉", "en": "Illusion of Linear Time"},
        {"zh": "时间戏剧比喻", "en": "Drama in Time Metaphor"},
        {"zh": "交替的现在", "en": "Alternate Presents"},
        {"zh": "时间强度", "en": "Intensity of Time"},
        {"zh": "空间伪装", "en": "Space as Camouflage"},
        {"zh": "多维空间", "en": "Multidimensional Space"},
        {"zh": "心理空间", "en": "Psychological Space"},
        {"zh": "永恒的现在", "en": "Eternal Present"},
        {"zh": "时间的非连续性", "en": "Non-Continuity of Time"}
    ],
    "梦境与睡眠": [
        {"zh": "梦境意识", "en": "Dream Consciousness"},
        {"zh": "梦的工作", "en": "Dream Work"},
        {"zh": "梦境工作室", "en": "Dream Workshop"},
        {"zh": "梦境艺术科学家", "en": "Dream-Art Scientist"},
        {"zh": "睡眠状态", "en": "Sleep State"},
        {"zh": "清醒梦", "en": "Lucid Dreaming"},
        {"zh": "梦的记忆", "en": "Dream Memory"},
        {"zh": "梦境教学", "en": "Dream Teaching"},
        {"zh": "梦境疗愈", "en": "Dream Healing"},
        {"zh": "梦中多重焦点", "en": "Multiple Focus in Dreams"},
        {"zh": "梦境中的价值完成", "en": "Value Fulfillment in Dreams"}
    ],
    "身体与健康": [
        {"zh": "身体创造", "en": "Body Creation"},
        {"zh": "健康与疾病", "en": "Health and Illness"},
        {"zh": "细胞的意识", "en": "Consciousness of Cells"},
        {"zh": "身体作为信念的镜子", "en": "Body as Mirror of Beliefs"},
        {"zh": "疾病的信念根源", "en": "Belief Roots of Disease"},
        {"zh": "自然疗愈", "en": "Natural Healing"},
        {"zh": "完整的医师", "en": "The Complete Physician"},
        {"zh": "身体的持续创造", "en": "Constant Creation of Body"},
        {"zh": "身体细胞的选择性", "en": "Selectivity of Body Cells"},
        {"zh": "身体与情感的连接", "en": "Body-Emotion Connection"},
        {"zh": "健康信念", "en": "Health Beliefs"},
        {"zh": "死亡作为转换", "en": "Death as Transition"},
        {"zh": "死后过渡", "en": "After-Death Transition"},
        {"zh": "身体细胞的智慧", "en": "Wisdom of Body Cells"},
        {"zh": "走向健康之路", "en": "The Way Toward Health"}
    ],
    "情感与能量": [
        {"zh": "情感的本质", "en": "Nature of Emotions"},
        {"zh": "情感的纯真", "en": "Innocence of Feelings"},
        {"zh": "压抑的情感", "en": "Repressed Emotions"},
        {"zh": "情感作为创造燃料", "en": "Emotion as Creative Fuel"},
        {"zh": "爱作为基本现实", "en": "Love as Basic Reality"},
        {"zh": "恐惧的物质化", "en": "Materialization of Fear"},
        {"zh": "愤怒的创造性", "en": "Creativity of Anger"},
        {"zh": "自然情感流动", "en": "Natural Emotional Flow"},
        {"zh": "情感与信念的关系", "en": "Emotion-Belief Relationship"},
        {"zh": "情感的电磁本质", "en": "Electromagnetic Nature of Emotion"}
    ],
    "社会与群体": [
        {"zh": "群体事件", "en": "Mass Events"},
        {"zh": "个体与群体的关系", "en": "Individual and Mass Relationship"},
        {"zh": "集体信念", "en": "Collective Beliefs"},
        {"zh": "社会实相创造", "en": "Social Reality Creation"},
        {"zh": "文化信念系统", "en": "Cultural Belief Systems"},
        {"zh": "群体意识的形成", "en": "Formation of Group Consciousness"},
        {"zh": "社会价值气候", "en": "Social Value Climate"},
        {"zh": "历史作为集体梦境", "en": "History as Collective Dream"},
        {"zh": "文明的选择", "en": "Choices of Civilization"},
        {"zh": "群体信念交汇", "en": "Convergence of Mass Beliefs"},
        {"zh": "群体创伤与疗愈", "en": "Mass Trauma and Healing"}
    ],
    "进化与价值": [
        {"zh": "价值完成", "en": "Value Fulfillment"},
        {"zh": "进化作为创造性过程", "en": "Evolution as Creative Process"},
        {"zh": "意识的进化", "en": "Evolution of Consciousness"},
        {"zh": "生物进化", "en": "Biological Evolution"},
        {"zh": "进化的内在动力", "en": "Inner Drive of Evolution"},
        {"zh": "生命的内在价值", "en": "Inner Value of Life"},
        {"zh": "进化的目的性", "en": "Purposefulness of Evolution"},
        {"zh": "进化的自发性", "en": "Spontaneity of Evolution"},
        {"zh": "进化中的游戏品质", "en": "Play Quality in Evolution"}
    ],
    "创造与自发性": [
        {"zh": "自发性", "en": "Spontaneity"},
        {"zh": "游戏的创造力", "en": "Creativity of Play"},
        {"zh": "自然节奏", "en": "Natural Rhythm"},
        {"zh": "内在指引", "en": "Inner Guidance"},
        {"zh": "创造力的品质", "en": "Quality of Creativity"},
        {"zh": "创造与喜悦", "en": "Creation and Joy"},
        {"zh": "信任自发性", "en": "Trust in Spontaneity"},
        {"zh": "控制与自发的对比", "en": "Control vs Spontaneity"},
        {"zh": "魔法方法", "en": "The Magical Approach"},
        {"zh": "充满爱的技术", "en": "Loving Technology"}
    ],
    "宗教与神话": [
        {"zh": "万有", "en": "All That Is"},
        {"zh": "宗教作为外在戏剧", "en": "Religion as Outer Drama"},
        {"zh": "神的概念", "en": "God Concept"},
        {"zh": "内在精神现实", "en": "Inner Spiritual Reality"},
        {"zh": "宗教的心理学", "en": "Psychology of Religion"},
        {"zh": "神话与实相", "en": "Myth and Reality"},
        {"zh": "宗教投射", "en": "Religious Projection"},
        {"zh": "小写的神", "en": "God (lowercase)"},
        {"zh": "终极源头", "en": "Ultimate Source"},
        {"zh": "内在领悟", "en": "Inner Realization"},
        {"zh": "宗教的集体表达", "en": "Collective Expression of Religion"},
        {"zh": "精神追求", "en": "Spiritual Pursuit"}
    ],
    "科学与知识": [
        {"zh": "心理物理学", "en": "Mental Physics"},
        {"zh": "真正的心理物理学家", "en": "True Mental Physicist"},
        {"zh": "客观科学的局限", "en": "Limits of Objective Science"},
        {"zh": "科学范式转换", "en": "Scientific Paradigm Shift"},
        {"zh": "意识科学", "en": "Science of Consciousness"},
        {"zh": "动物与科学", "en": "Animals and Science"},
        {"zh": "主观科学", "en": "Subjective Science"},
        {"zh": "新的科学范式", "en": "New Scientific Paradigm"},
        {"zh": "亚原子粒子与意识", "en": "Subatomic Particles and Consciousness"},
        {"zh": "电子自旋的心理本质", "en": "Psychological Nature of Electron Spin"}
    ]
}

# Generate concept IDs and prepare for JSON
all_concepts = []
concept_id = 0

for category, concepts in concept_categories.items():
    for concept in concepts:
        concept_id += 1
        all_concepts.append({
            "id": f"concept-{concept_id:03d}",
            "name_zh": concept["zh"],
            "name_en": concept["en"],
            "category": category,
            "definition": "",
            "explanation": "",
            "quotes": [],
            "related_concepts": [],
            "sub_concepts": []
        })

print(f"Total concepts to create: {len(all_concepts)}")
print(f"\nConcepts per category:")
total = 0
for cat, cons in concept_categories.items():
    print(f"  {cat}: {len(cons)}")
    total += len(cons)
print(f"\nTotal: {total}")

# Save the concept list
with open('concept_list_complete.json', 'w', encoding='utf-8') as f:
    json.dump({
        "categories": {cat: [{"zh": c["zh"], "en": c["en"]} for c in cons] for cat, cons in concept_categories.items()},
        "concepts": all_concepts,
        "total": len(all_concepts)
    }, f, ensure_ascii=False, indent=2)

print("\nComplete concept list saved to concept_list_complete.json")
