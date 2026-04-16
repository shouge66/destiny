import { apiFetch, guestLogin, login, register } from "./api.js";
import { clearAuth, setAssessmentDraft, state } from "./state.js";

const DIMENSION_META = {
  ni: { label: "内倾直觉 Ni" },
  ne: { label: "外倾直觉 Ne" },
  si: { label: "内倾感觉 Si" },
  se: { label: "外倾感觉 Se" },
  ti: { label: "内倾思维 Ti" },
  te: { label: "外倾思维 Te" },
  fi: { label: "内倾情感 Fi" },
  fe: { label: "外倾情感 Fe" },
};

const QUESTIONNAIRE = [
  { id: "q1", dim: "ni", text: "我会在复杂信息中先看到长期趋势和隐藏结构。" },
  { id: "q2", dim: "ni", text: "我对未来方向的判断常常比当下更早形成。" },
  { id: "q3", dim: "ne", text: "我能在一个问题上联想到多个跨领域方案。" },
  { id: "q4", dim: "ne", text: "我喜欢做概念实验，边做边发现新可能。" },
  { id: "q5", dim: "si", text: "我会依靠经验、案例和细节来建立稳定结果。" },
  { id: "q6", dim: "si", text: "我擅长发现流程中的偏差和可改进点。" },
  { id: "q7", dim: "se", text: "在现场变化中，我能快速做出务实反应。" },
  { id: "q8", dim: "se", text: "我通过行动和体验来获得真实判断。" },
  { id: "q9", dim: "ti", text: "我会主动拆解逻辑，追问定义边界。" },
  { id: "q10", dim: "ti", text: "我对概念严谨度有较高要求，不轻易妥协。" },
  { id: "q11", dim: "te", text: "我习惯用目标和结果来推动协作进程。" },
  { id: "q12", dim: "te", text: "我会把任务拆成可执行节点并追踪完成。" },
  { id: "q13", dim: "fi", text: "我重视内在价值一致性，不愿违背真实自我。" },
  { id: "q14", dim: "fi", text: "我对意义感和个人边界非常敏感。" },
  { id: "q15", dim: "fe", text: "我会主动理解他人状态并调整表达方式。" },
  { id: "q16", dim: "fe", text: "我擅长在群体中建立连接和合作氛围。" },
];

const DEEP_QUESTIONS = [
  {
    id: "dq1",
    label:
      "16岁之前（未被社会完全规训前），有哪些事情是没人逼也会废寝忘食去做的？或有哪些从小到大被批评的顽固缺点？",
  },
  {
    id: "dq2",
    label:
      "成年后的工作/生活中，哪件事让你觉得这还需要学吗？这不是显而易见的吗？但周围人却觉得很难？",
  },
  {
    id: "dq3",
    label: "哪件事做完后虽然身体累，但精神极度亢奋？",
  },
  {
    id: "dq4",
    label: "曾经对谁（或哪种生活状态）产生过羡慕或者嫉妒？",
  },
];

function esc(value) {
  return String(value ?? "").replaceAll("<", "&lt;");
}

function normalizeScore(raw) {
  return Math.max(0, Math.min(100, Number(raw) || 0));
}

function splitWords(text) {
  return (text || "")
    .toLowerCase()
    .replace(/[，。！？；：,.!?;:\n\r]/g, " ")
    .split(" ")
    .filter(Boolean);
}

function keywordBoost(text, map, base = 0) {
  const raw = String(text || "").toLowerCase();
  const words = splitWords(raw);
  let score = base;

  for (const [keyword, weight] of Object.entries(map)) {
    if (!keyword) continue;
    const lowerKeyword = keyword.toLowerCase();

    if (/^[a-z0-9_\-]+$/i.test(lowerKeyword)) {
      const count = words.filter((w) => w === lowerKeyword).length;
      score += count * weight;
      continue;
    }

    let idx = raw.indexOf(lowerKeyword);
    while (idx !== -1) {
      score += weight;
      idx = raw.indexOf(lowerKeyword, idx + lowerKeyword.length);
    }
  }
  return score;
}

function buildDimensionScores(answers) {
  const grouped = { ni: [], ne: [], si: [], se: [], ti: [], te: [], fi: [], fe: [] };
  QUESTIONNAIRE.forEach((item) => grouped[item.dim].push(Number(answers[item.id])));

  const result = {};
  Object.keys(grouped).forEach((key) => {
    const avg = grouped[key].reduce((a, b) => a + b, 0) / grouped[key].length;
    result[key] = normalizeScore(avg * 20);
  });
  return result;
}

function inferHiddenTalents(deepAnswers, dimensionScores) {
  const text = `${deepAnswers.dq1} ${deepAnswers.dq2} ${deepAnswers.dq3} ${deepAnswers.dq4}`;
  const creativeBoost = keywordBoost(text, {
    写作: 8, 画画: 8, 设计: 8, 音乐: 8, 创意: 6, 点子: 6, 构思: 6,
  });
  const analysisBoost = keywordBoost(text, {
    逻辑: 8, 研究: 8, 分析: 6, 结构: 6, 复盘: 6, 体系: 6, 模型: 8,
  });
  const empathyBoost = keywordBoost(text, {
    共情: 8, 倾听: 8, 陪伴: 6, 关系: 6, 沟通: 6, 帮助: 6,
  });
  const executionBoost = keywordBoost(text, {
    推进: 8, 落地: 8, 执行: 8, 项目: 6, 交付: 6, 节奏: 6,
  });

  const hidden = [];
  if (creativeBoost + dimensionScores.ne > 80) {
    hidden.push("创造性系统建模：把抽象想法转成可落地方案");
  }
  if (analysisBoost + dimensionScores.ti > 85) {
    hidden.push("深度洞察与结构诊断：快速定位问题根因");
  }
  if (empathyBoost + dimensionScores.fi + dimensionScores.fe > 150) {
    hidden.push("情绪与关系调频：在复杂关系中稳住协作氛围");
  }
  if (executionBoost + dimensionScores.te + dimensionScores.se > 145) {
    hidden.push("高压情境推进力：在不确定中维持执行节奏");
  }

  if (hidden.length === 0) {
    hidden.push("跨情境学习迁移：把经验迅速迁移到新场景");
  }

  return hidden;
}

function generateTalentReport(dimensionScores, deepAnswers, hiddenTalents) {
  const ranking = Object.entries(dimensionScores)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ key: k, score: v, label: DIMENSION_META[k]?.label || k }));

  const top = ranking.slice(0, 3).map((x) => x.label).join(" / ");
  const coreSignal = ranking[0]?.label || "核心优势";
  const supportSignal = ranking[1]?.label || "协同优势";
  const thirdSignal = ranking[2]?.label || "发展优势";
  const weakest = ranking.slice(-2);
  const weakestLabel = weakest.map((x) => x.label).join(" / ");
  const spread = (ranking[0]?.score || 0) - (ranking[ranking.length - 1]?.score || 0);
  const dominantPair = `${ranking[0]?.key || "ni"}-${ranking[1]?.key || "fi"}`;

  const pairNarrative = {
    "ni-ti": "你更像“洞察-建模型”选手，擅长先看见深层结构，再构建推演路径。",
    "ni-fi": "你更像“愿景-价值型”选手，重视长期方向与内在一致性。",
    "ne-ti": "你更像“发散-拆解型”选手，能快速提出多解并进行逻辑筛选。",
    "te-si": "你更像“执行-秩序型”选手，适合在明确目标中构建稳定产出系统。",
    "fe-ni": "你更像“关系-洞察型”选手，善于读懂人群动力并校准方向。",
    "se-te": "你更像“实战-推进型”选手，擅长在动态现场做快速决策。",
  };

  const weakAdviceMap = {
    ni: "先做结论树，再进入执行，避免在事务流中迷失主线。",
    ne: "每周固定一次方案发散练习，提升跨域联想弹性。",
    si: "建立复盘模板，把经验沉淀为可复用资产。",
    se: "增加真实场景验证，避免只在脑内推演。",
    ti: "在关键决策前做一次反证清单，提升逻辑闭环。",
    te: "把目标拆成周里程碑，减少“想得多做得少”。",
    fi: "把“我在乎什么”写成边界声明，降低内耗。",
    fe: "高强度协作后安排独处修复，避免关系透支。",
  };

  const deepText = `${deepAnswers.dq1 || ""} ${deepAnswers.dq2 || ""} ${deepAnswers.dq3 || ""} ${deepAnswers.dq4 || ""}`;
  const motifScores = {
    creative: keywordBoost(deepText, { 创作: 4, 写作: 4, 设计: 4, 产品: 3, 灵感: 3, 表达: 2 }),
    analytic: keywordBoost(deepText, { 分析: 4, 研究: 4, 模型: 4, 逻辑: 3, 数据: 3, 复盘: 2 }),
    social: keywordBoost(deepText, { 团队: 4, 沟通: 4, 协作: 3, 关系: 3, 影响: 2, 连接: 2 }),
    execution: keywordBoost(deepText, { 推进: 4, 落地: 4, 项目: 3, 交付: 3, 目标: 2, 节奏: 2 }),
  };
  const motif = Object.entries(motifScores).sort((a, b) => b[1] - a[1])[0]?.[0] || "analytic";

  const motifPlan = {
    creative: "建议采用“创意孵化-作品输出-市场验证”三段式节奏。",
    analytic: "建议采用“问题定义-结构拆解-验证迭代”三段式节奏。",
    social: "建议采用“关系建联-共识形成-协作放大”三段式节奏。",
    execution: "建议采用“目标拆分-周度推进-结果复盘”三段式节奏。",
  };

  const deepQ1 = (deepAnswers.dq1 || "").slice(0, 32) || "你的早期兴趣与长期坚持";
  const deepQ2 = (deepAnswers.dq2 || "").slice(0, 32) || "你在现实场景中的自然输出";
  const deepQ3 = (deepAnswers.dq3 || "").slice(0, 32) || "你能持续投入并感到充能的事项";
  const deepQ4 = (deepAnswers.dq4 || "").slice(0, 32) || "你内在真正向往的生活状态";

  const longForm = [
    `你的能力结构并非平均分布，而是围绕${coreSignal}、${supportSignal}与${thirdSignal}形成了清晰主轴。${pairNarrative[dominantPair] || "你在洞察、表达与推进之间具备可迁移的组合能力。"} 当前高低分差约 ${spread.toFixed(1)} 分，说明你的优势使用场景较集中，若把优势嵌入正确任务，产出会显著放大。`,
    `从叙事线索看，"${deepQ1}" 与 "${deepQ2}" 透露出你的天然工作偏好。你更容易在“认同感强 + 可持续沉淀”的场景进入深度投入，而不是在纯外部压力驱动下长期冲刺。`,
    `"${deepQ3}" 对你的能量系统有强提示：它不是短期兴奋，而是可复利的心流触发器。"${deepQ4}" 则揭示了你真正想靠近的生活方式与身份定位。把这两条线并入年度规划，能显著降低方向摇摆。`,
    `在显性优势之外，你还具备这些隐藏潜能：${hiddenTalents.join("；")}。这些潜能一旦与真实业务问题结合，会形成“洞察到结果”的跃迁效应。`,
    `你当前的薄弱位集中在 ${weakestLabel}。这不代表能力不足，而是提醒你要做结构补位：${weakest.map((item) => weakAdviceMap[item.key] || "保持稳定复盘与校准。").join("；")}`,
    `未来 6-12 个月建议围绕${top}做“主轴推进 + 弱项补位”双线策略。${motifPlan[motif]} 每月保留一次证据回看（作品、反馈、结果），让成长从感受判断转向事实判断。`,
  ].join("\n\n");

  const deepInsight = [
    `你的优势高点集中在${top}，主轴清晰，适合做长期复利型投入。`,
    `你在“${deepQ3}...”相关任务中具备更高的持续投入概率，应优先纳入主赛道。`,
    `当前薄弱位是${weakestLabel}，补位策略将直接决定你的稳定性上限。`,
    `你的叙事动机更偏${motif === "creative" ? "创造表达" : motif === "analytic" ? "结构分析" : motif === "social" ? "关系协同" : "执行落地"}，建议任务设计与动机匹配。`,
  ];

  return {
    summary:
      `你的能力画像显示：以${coreSignal}为核心引擎，${supportSignal}为协同支点，${thirdSignal}提供扩展弹性。当前最优路径不是平均用力，而是把优势放到高匹配场景并对${weakestLabel}做针对性补位。`,
    top_rankings: ranking,
    hidden_talents: hiddenTalents,
    deep_analysis: deepInsight,
    long_form: longForm,
    challenge_pattern:
      `你的常见卡点在于当任务与内在动机错位时，执行稳定性会下降，尤其在${weakestLabel}相关场景更明显。`,
    growth_principle:
      `先把${top}转化为可展示成果，再按“最弱两项最小补位”策略迭代，形成稳定的个性化成长回路。`,
  };
}

function heavenlyStemAndBranch(year) {
  const stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
  const branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
  return {
    stem: stems[(year - 4) % 10],
    branch: branches[(year - 4) % 12],
  };
}

function monthElement(month) {
  if ([1, 2].includes(month)) return "木";
  if ([3, 4].includes(month)) return "火";
  if ([5, 6].includes(month)) return "土";
  if ([7, 8].includes(month)) return "金";
  return "水";
}

function flyingStarNumber(year, month, day) {
  const digits = `${year}${month}${day}`.split("").map(Number);
  const sum = digits.reduce((a, b) => a + b, 0);
  const n = sum % 9;
  return n === 0 ? 9 : n;
}

function buildZiweiPalaces(topStrength) {

  return {
    命宫: `你的核心驱动力偏向${topStrength}，建议将其作为长期身份锚点。`,
    兄弟宫: "宜建立少量稳定同盟，重质量而非数量。",
    夫妻宫: "关系看重价值同频与成长节律一致。",
    子女宫: "创作表达有潜力，适合长期项目孵化。",
    财帛宫: "财务路径以能力复利与长期主义为主。",
    疾厄宫: "需管理作息与情绪负荷，避免连续透支。",
    迁移宫: "外部机会来自跨域协作与场景迁移。",
    仆役宫: "适合与高自驱伙伴共建，而非强控协作。",
    官禄宫: "事业位强调专业深度与可验证成果。",
    田宅宫: "环境宜安静克制，保留独处与复盘空间。",
    福德宫: "精神补给依赖意义感与内在一致性。",
    父母宫: "长辈或权威关系宜清边界、稳沟通。",
  };
}

function normalizeMysticReport(remote, formData, talentReport) {
  const fallback = buildMysticReport(formData, talentReport);
  if (!remote || typeof remote !== "object") {
    return fallback;
  }

  const source = remote.source || remote.provider || "professional";
  const chart = remote.chart || remote.professional_chart || {};
  const ziwei = remote.ziwei || chart.ziwei || {};
  const palaces = remote.ziwei_12_palaces || ziwei.palaces || fallback.ziwei_12_palaces || {};

  return {
    ...fallback,
    ...remote,
    bazi: remote.bazi || chart.bazi || fallback.bazi,
    yongshen: remote.yongshen || chart.yongshen || fallback.yongshen,
    flying_star: remote.flying_star || chart.flying_star || fallback.flying_star,
    flying_advice: remote.flying_advice || chart.flying_advice || fallback.flying_advice,
    ziwei_focus: remote.ziwei_focus || ziwei.focus || fallback.ziwei_focus,
    ziwei_12_palaces: palaces,
    best_cities: Array.isArray(remote.best_cities) ? remote.best_cities : fallback.best_cities,
    best_industries: Array.isArray(remote.best_industries) ? remote.best_industries : fallback.best_industries,
    source,
  };
}

function buildMysticReport(formData, talentReport) {
  const birthDate = formData.get("birth_date");
  if (!birthDate) return null;

  const [yearStr, monthStr, dayStr] = birthDate.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);
  const day = Number(dayStr);
  const hour = Number((formData.get("birth_time") || "12:00").split(":")[0]);

  const y = heavenlyStemAndBranch(year);
  const monthEle = monthElement(month);
  const flyingStar = flyingStarNumber(year, month, day);

  const elementMap = {
    甲: "木", 乙: "木", 丙: "火", 丁: "火", 戊: "土", 己: "土", 庚: "金", 辛: "金", 壬: "水", 癸: "水",
  };

  const natalElement = elementMap[y.stem];
  const yongshen = natalElement === monthEle ? "木火通明" : `${monthEle}${natalElement}调衡`;

  const directionMap = {
    木: "东、东南",
    火: "南",
    土: "中宫、西南、东北",
    金: "西、西北",
    水: "北",
  };
  const industryMap = {
    木: ["教育咨询", "健康管理", "文化内容"],
    火: ["品牌传播", "产品创新", "影像与表达"],
    土: ["运营管理", "项目统筹", "组织发展"],
    金: ["金融风控", "法务合规", "医疗器械"],
    水: ["数据智能", "科研医药", "心理服务"],
  };
  const cityMap = {
    木: ["上海", "杭州", "苏州"],
    火: ["深圳", "广州", "厦门"],
    土: ["成都", "重庆", "武汉"],
    金: ["北京", "青岛", "天津"],
    水: ["南京", "宁波", "大连"],
  };

  const flyingAdvice = {
    1: "一白贪狼，利学习进修与跨界探索。",
    2: "二黑坤星，重稳定与节律，避免过度透支。",
    3: "三碧震星，利突破与发声，需管理冲突成本。",
    4: "四绿文曲，利内容、品牌、表达与教学。",
    5: "五黄中宫，先守后攻，优先做风险减法。",
    6: "六白武曲，利管理与结构化决策。",
    7: "七赤破军，利市场与传播，注意信息噪声。",
    8: "八白左辅，利长期项目与资产积累。",
    9: "九紫右弼，利影响力升级与公开表达。",
  };

  const topStrength = talentReport.top_rankings[0]?.label || "综合能力";
  const ziwFocus = `紫微结构显示你适合以${topStrength}为主轴，优先打通“命宫-官禄宫-福德宫”三点联动：先稳内在节律，再做外部成果放大。`;

  const hourAdvice = hour >= 23 || hour < 5
    ? "夜时生人，适合深度创作与安静决策窗口。"
    : hour >= 5 && hour < 11
      ? "晨时生人，适合外部拓展与早段高能任务。"
      : "日时生人，适合协同推进与公开表达场景。";

  return {
    bazi: `${y.stem}${y.branch}年 / 月令${monthEle}`,
    yongshen,
    flying_star: `${flyingStar}白星`,
    flying_advice: flyingAdvice[flyingStar],
    ziwei_focus: ziwFocus,
    ziwei_12_palaces: buildZiweiPalaces(topStrength),
    best_directions: directionMap[natalElement],
    best_cities: cityMap[natalElement],
    best_industries: industryMap[natalElement],
    personalized_solution: `你的首位天赋为${topStrength}，建议采用“主优势主导 + 次优势协同”的双轮策略：先用${topStrength}建立可见成果，再通过每月复盘优化执行节奏。${hourAdvice}`,
    source: "local-fallback",
    note: "命理模块为辅助决策工具，建议与你的真实履历、资源条件共同评估。",
  };
}

async function resolveMysticReport(formData, talentReport) {
  try {
    const payload = {
      birth_date: formData.get("birth_date") || null,
      birth_time: formData.get("birth_time") || null,
      talent_summary: talentReport?.summary || "",
      top_strengths: (talentReport?.top_rankings || []).slice(0, 3).map((item) => item.label),
    };

    const remote = await apiFetch("/mystic-analysis/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return normalizeMysticReport(remote, formData, talentReport);
  } catch {
    return buildMysticReport(formData, talentReport);
  }
}

async function upsertMysticInput(formData) {
  const payload = {
    birth_date: formData.get("birth_date") || null,
    birth_time: formData.get("birth_time") || null,
    timezone_name: "Asia/Shanghai",
    consent_flag: true,
  };

  const existing = await apiFetch("/mystic-inputs/");
  if (existing.length > 0) {
    return apiFetch(`/mystic-inputs/${existing[0].id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  return apiFetch("/mystic-inputs/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

function getSortedRanking(scoresObj) {
  return Object.entries(scoresObj)
    .map(([key, score]) => [key, normalizeScore(score)])
    .sort((a, b) => b[1] - a[1]);
}

function rankingHtml(ranking) {
  return ranking
    .map(([key, score]) => `
      <div class="bar-row">
        <span>${DIMENSION_META[key]?.label || esc(key)}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${Number(score)}%"></div></div>
        <strong>${Number(score).toFixed(1)}</strong>
      </div>
    `)
    .join("");
}

const RADAR_DIMENSION_ORDER = ["ni", "ne", "si", "se", "ti", "te", "fi", "fe"];

function buildRadarSvg(ranking) {
  const size = 360;
  const center = size / 2;
  const maxR = 124;
  const levels = [20, 40, 60, 80, 100];
  const scoreMap = Object.fromEntries(ranking.map(([key, score]) => [key, Number(score) || 0]));

  const pointFor = (ratio, idx) => {
    const angle = ((Math.PI * 2) / RADAR_DIMENSION_ORDER.length) * idx - Math.PI / 2;
    const r = maxR * ratio;
    return {
      x: center + Math.cos(angle) * r,
      y: center + Math.sin(angle) * r,
    };
  };

  const rings = levels
    .map((lv) => {
      const points = RADAR_DIMENSION_ORDER.map((_, idx) => {
        const p = pointFor(lv / 100, idx);
        return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
      }).join(" ");
      return `<polygon points="${points}" class="radar-ring" />`;
    })
    .join("");

  const axes = RADAR_DIMENSION_ORDER.map((_, idx) => {
    const p = pointFor(1, idx);
    return `<line x1="${center}" y1="${center}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}" class="radar-axis" />`;
  }).join("");

  const dataPoints = RADAR_DIMENSION_ORDER.map((key, idx) => {
    const p = pointFor((scoreMap[key] || 0) / 100, idx);
    return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
  }).join(" ");

  const pointDots = RADAR_DIMENSION_ORDER.map((key, idx) => {
    const p = pointFor((scoreMap[key] || 0) / 100, idx);
    return `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.4" class="radar-dot" />`;
  }).join("");

  const labels = RADAR_DIMENSION_ORDER.map((key, idx) => {
    const p = pointFor(1.12, idx);
    const label = DIMENSION_META[key]?.label || key;
    return `<text x="${p.x.toFixed(1)}" y="${p.y.toFixed(1)}" class="radar-label" text-anchor="middle">${esc(label)}</text>`;
  }).join("");

  return `
    <svg viewBox="0 0 ${size} ${size}" class="radar-svg" role="img" aria-label="16题多维倾向性评分雷达图">
      ${rings}
      ${axes}
      <polygon points="${dataPoints}" class="radar-shape" />
      ${pointDots}
      ${labels}
    </svg>
  `;
}

function radarNoteHtml(ranking) {
  const top3 = ranking
    .slice(0, 3)
    .map(([key, score]) => `${DIMENSION_META[key]?.label || key}（${Number(score).toFixed(1)}）`)
    .join("、");
  const tail2 = ranking
    .slice(-2)
    .map(([key, score]) => `${DIMENSION_META[key]?.label || key}（${Number(score).toFixed(1)}）`)
    .join("、");

  return `
    <div class="radar-note">
      <p><strong>说明：</strong>该雷达图基于 16 道题计算，8 个维度各对应 2 道题，单维得分 = 两题平均分 × 20（范围 0-100）。</p>
      <p><strong>当前高倾向维度：</strong>${esc(top3)}</p>
      <p><strong>当前补位维度：</strong>${esc(tail2)}</p>
      <p class="tip">雷达图反映“倾向强度”，不是能力上限。高分代表更自然的认知偏好，低分代表当前较少启用，可通过训练补位。</p>
    </div>
  `;
}

function buildIntegratedReading(report, mysticReport, ranking) {
  const top3 = ranking.slice(0, 3).map(([key]) => DIMENSION_META[key]?.label || key);
  const weakest = ranking.slice(-2).map(([key]) => DIMENSION_META[key]?.label || key);
  const headline = mysticReport
    ? `你不是普通意义上的“平均型成长者”，而是带着${top3[0] || "核心优势"}主轴出生，并被${top3[1] || "协同优势"}与${top3[2] || "延展优势"}共同放大的人。`
    : `你的生命主轴已经非常清晰：${top3.join("、")}并不是零散优势，而是一条正在成形的命运推进线。`;

  const opening = mysticReport
    ? `问卷显示你的认知优势集中在${top3.join("、")}；命理结构则进一步说明，这种优势不是阶段性表现，而是更适合被长期经营的人生配置。你的路，不适合平均用力，更适合集中爆发。`
    : `从问卷结构看，你更适合把有限精力押注在高匹配场景中。只要主轴正确，你的成长速度会明显快于平均分布式投入。`;

  const mysticLines = mysticReport
    ? [
        `八字基准与喜用提示显示，你当前更适合顺势经营“${mysticReport.best_industries?.join(" / ") || "优势行业"}”这类能长期积累的方向，而不是反复横跳。`,
        `紫微提示你的外部成就，必须建立在内部节律稳定之上。${mysticReport.ziwei_focus}`,
        `从宫位联动看，事业、精神状态与关系质量彼此牵动：${mysticReport.ziwei_12_palaces?.官禄宫 || "事业位要求阶段成果"}${mysticReport.ziwei_12_palaces?.福德宫 || "精神位要求内在一致"}`,
      ]
    : [];

  const reportParagraphs = String(report.long_form || "")
    .split("\n\n")
    .filter(Boolean)
    .slice(0, 3);

  const narrative = [opening, ...reportParagraphs, ...mysticLines]
    .filter(Boolean)
    .map((text) => `<p>${esc(text)}</p>`)
    .join("");

  const highlights = [
    `你最该放大的不是短期效率，而是${top3[0] || "核心优势"}带来的长期复利。`,
    `你的人生突破口通常出现在“优势主轴 + 外部验证”同时发生的阶段。`,
    `当前真正决定上限的，不是天赋够不够，而是${weakest.join("、")}是否被稳定补位。`,
    mysticReport ? `方位与环境上，优先靠近${mysticReport.best_directions || "更稳的空间方向"}，有助于你把分散感收拢成行动力。` : "当你停止平均分配精力，改为围绕主轴做决策时，人生会明显开始提速。",
  ];

  return {
    headline,
    opening,
    narrative,
    highlights,
  };
}

const LIFE_DIMENSION_LIBRARY = {
  health: {
    name: "身心健康",
    objective: "建立稳定作息与基础体能，保证连续 90 天可持续输出。",
    baseline: "每晚保证 7 小时睡眠，每周至少 3 次 30 分钟低门槛运动。",
    progress: "每周 1 次力量训练 + 1 次有氧，晚间 23:30 前停止高刺激输入。",
    challenge: "连续 4 周完成固定训练节奏，并记录心率/睡眠趋势。",
    metric: "周睡眠达标天数 >= 5，周运动次数 >= 3。",
    warning: "连续 2 天熬夜、情绪易怒、白天注意力明显下滑。",
    correction: "启动 48 小时恢复：晚间减负 + 20 分钟快走 + 当天提前入睡。",
    fallback: "当日最低动作：10 分钟拉伸 + 提前 30 分钟睡觉。",
  },
  emotional: {
    name: "情绪与心理",
    objective: "从情绪反应转向情绪识别，提升稳定度与自我接纳。",
    baseline: "每天用 3 句话记录当日情绪触发点和身体感受。",
    progress: "每周完成 2 次 15 分钟情绪复盘（事实-解释-行动）。",
    challenge: "在高压情境中保持非对抗表达，并复盘 3 次成功案例。",
    metric: "每周情绪记录 >= 5 次，冲突后恢复时间缩短。",
    warning: "反复自责、长时间拖延、对小事过度反应。",
    correction: "先停 10 分钟呼吸与落地动作，再处理事件而非评价自我。",
    fallback: "当日最低动作：写下 1 条情绪触发 + 1 条可执行动作。",
  },
  relationship: {
    name: "关系与家庭",
    objective: "把重要关系从被动维护转为主动经营。",
    baseline: "每周至少 1 次高质量沟通（伴侣/家人/关键朋友）。",
    progress: "每周进行 1 次深聊，使用‘我感受’句式表达需求。",
    challenge: "连续 4 周完成关系仪式感行动（共餐/散步/探访）。",
    metric: "每周高质量沟通次数 >= 1，关键关系满意度主观提升。",
    warning: "长期回避沟通、误解累积、情绪化回应增多。",
    correction: "优先澄清事实和需求，约定 30 分钟低防御沟通窗口。",
    fallback: "当日最低动作：发送 1 条真诚问候并确认对方近况。",
  },
  career: {
    name: "事业与学业",
    objective: "围绕核心优势形成可见成果，避免忙碌但无积累。",
    baseline: "每周锁定 3 个高价值任务，先做主轴再做杂项。",
    progress: "每周产出 1 个可展示成果（文档/方案/演示/案例）。",
    challenge: "90 天内完成 1 次公开输出，并获得外部反馈。",
    metric: "周高价值任务完成率 >= 70%，成果产出 >= 1。",
    warning: "任务堆积、方向摇摆、高投入低回报。",
    correction: "回到季度主轴，砍掉非主轴事项 20%-30%。",
    fallback: "当日最低动作：完成主轴任务 20 分钟推进。",
  },
  finance: {
    name: "财务与资源",
    objective: "让现金流有秩序，降低长期焦虑与决策波动。",
    baseline: "每周更新一次收支，区分固定支出与弹性支出。",
    progress: "设置月度自动储蓄比例，建立 3-6 个月应急缓冲目标。",
    challenge: "90 天内完成 1 套个人资产配置学习与执行清单。",
    metric: "月储蓄率持续提升，应急金覆盖月数稳步增长。",
    warning: "冲动消费频繁、账目滞后、回避财务盘点。",
    correction: "执行 48 小时延迟购买规则，先记账再决策。",
    fallback: "当日最低动作：记录所有支出并标记必要/非必要。",
  },
  growth: {
    name: "个人成长",
    objective: "形成输入-思考-输出闭环，而不是只积累信息。",
    baseline: "每周固定 2 次深度学习时段（每次 45 分钟）。",
    progress: "每周输出 1 份学习笔记或观点卡片。",
    challenge: "90 天沉淀 1 套个人方法论草稿并迭代两轮。",
    metric: "周学习时长 >= 90 分钟，周输出 >= 1。",
    warning: "收藏很多但不复盘，学习焦虑替代真实进步。",
    correction: "每次学习结束必须输出 3 条可执行结论。",
    fallback: "当日最低动作：阅读 10 分钟并写 1 条洞察。",
  },
  experience: {
    name: "生活体验",
    objective: "通过兴趣与体验恢复能量，避免长期透支。",
    baseline: "每周安排 1 次无功利兴趣活动（音乐/运动/手作等）。",
    progress: "每月进行 1 次短途体验或文化输入（展览/自然/城市漫步）。",
    challenge: "90 天完成 1 个可持续爱好项目并公开记录过程。",
    metric: "每周兴趣时段 >= 1，主观精力评分提升。",
    warning: "长期只有工作任务，恢复活动几乎为零。",
    correction: "先恢复再冲刺，优先安排 2 小时低负担体验时段。",
    fallback: "当日最低动作：20 分钟纯兴趣时间，不做绩效化评估。",
  },
  environment: {
    name: "环境与秩序",
    objective: "通过空间与节律管理降低决策成本和分心损耗。",
    baseline: "每天结束前 10 分钟清理桌面与次日待办。",
    progress: "每周一次居住/数字空间整理，减少视觉与信息噪音。",
    challenge: "90 天内完成 1 套个人工作流与生活节律标准化。",
    metric: "每周整理次数 >= 1，计划执行偏差减少。",
    warning: "环境杂乱、待办失控、频繁临时救火。",
    correction: "先清场后开工，重建单日 3 件最重要事项清单。",
    fallback: "当日最低动作：整理 1 个小区域 + 删 10 条无效信息。",
  },
};

const COGNITIVE_TO_LIFE_DIMENSIONS = {
  ni: { growth: 2, emotional: 2, career: 1 },
  ne: { experience: 2, growth: 2, career: 1 },
  si: { environment: 2, health: 1, finance: 1 },
  se: { health: 2, experience: 2, career: 1 },
  ti: { growth: 2, finance: 1, career: 1 },
  te: { career: 2, finance: 2, environment: 1 },
  fi: { emotional: 2, relationship: 2, growth: 1 },
  fe: { relationship: 2, emotional: 1, career: 1 },
};

function selectLifeDimensionPriorities(report) {
  const scoreBoard = Object.keys(LIFE_DIMENSION_LIBRARY).reduce((acc, key) => {
    acc[key] = 0;
    return acc;
  }, {});

  const ranking = report?.top_rankings || [];
  ranking.slice(0, 4).forEach((item, idx) => {
    const dimKey = item?.key;
    const mappings = COGNITIVE_TO_LIFE_DIMENSIONS[dimKey] || {};
    const positionBoost = 4 - idx;
    Object.entries(mappings).forEach(([lifeKey, weight]) => {
      scoreBoard[lifeKey] += weight * positionBoost;
    });
  });

  return Object.entries(scoreBoard)
    .sort((a, b) => b[1] - a[1])
    .map(([key]) => key);
}

function buildDetailedPlan(report, mysticReport) {
  const top1 = report.top_rankings[0]?.label || "核心优势";
  const top2 = report.top_rankings[1]?.label || "次级优势";
  const orderedLifeKeys = selectLifeDimensionPriorities(report);
  const majorKeys = orderedLifeKeys.slice(0, 3);
  const supportKeys = orderedLifeKeys.slice(3, 5);
  const majorNames = majorKeys.map((k) => LIFE_DIMENSION_LIBRARY[k].name).join("、");
  const supportNames = supportKeys.map((k) => LIFE_DIMENSION_LIBRARY[k].name).join("、");
  const lifeDimensions = orderedLifeKeys.map((k) => LIFE_DIMENSION_LIBRARY[k]);

  return {
    annual_direction: `以${top1}为主轴、${top2}为协同，形成“事业推进 + 生活稳态 + 关系与成长并进”的 90 天行动系统。`,
    focus_summary: `本季度主攻：${majorNames}；托底维度：${supportNames}。其余维度保持最低可执行动作，确保整体平衡。`,
    phase_plan: [
      {
        phase: "Phase 1（1-4周）稳住节律",
        goals: [
          "主攻维度建立保底动作，先求稳定执行",
          "托底维度完成基础秩序搭建（作息、空间、关系触点）",
          "建立每周 1 次 30 分钟复盘窗口",
        ],
      },
      {
        phase: "Phase 2（5-8周）提升与外化",
        goals: [
          "主攻维度从保底升级到进阶动作",
          "每周至少完成 1 次外部反馈或可见成果记录",
          "把有效动作沉淀成个人模板",
        ],
      },
      {
        phase: "Phase 3（9-12周）整合与放大",
        goals: [
          "每个主攻维度完成 1 次挑战动作",
          "总结个人有效策略与失效触发点",
          "形成下一季度维度优先级与量化里程碑",
        ],
      },
    ],
    life_dimensions: lifeDimensions,
    weekly_actions: [
      `每周一：为主攻维度（${majorNames}）各设 1 个关键动作`,
      "每周三：15-30 分钟中检，识别偏离并及时减负",
      "每周五：记录本周证据（成果、关系反馈、能量状态）",
      "每周末：复盘 5 问，决定下周维度优先级",
    ],
    risk_controls: [
      "若出现过载：立刻削减非主轴任务，保留主攻维度保底动作",
      "若出现内耗：使用“事实-解释-行动”三栏复盘，避免自责循环",
      "若出现中断：启动 48 小时回归机制，先做迷你动作再恢复节奏",
    ],
    daily_actions: [
      "每天只保留 3 个重点动作：1 个主攻、1 个托底、1 个恢复。",
      "任一动作无法完成时，执行对应维度的最低动作，不做全盘放弃。",
      "晚间 5 分钟记录：今天最有能量时段 + 明日首要动作。",
    ],
    weekly_review_questions: [
      "本周哪个维度提升最明显？证据是什么？",
      "哪个触发点最容易让我偏离节奏？",
      "我在哪个场景最有心流，如何下周复用？",
      "是否有 1-2 个任务可以直接删除或延期？",
      "下周主攻 3 维和托底 2 维分别是什么？",
    ],
    mystic_alignment: mysticReport
      ? `方位建议：${mysticReport.best_directions}；行业建议：${mysticReport.best_industries.join(" / ")}；飞星提示：${mysticReport.flying_advice}；官禄宫提示：${mysticReport.ziwei_12_palaces?.官禄宫 || "以阶段成果稳步推进。"}`
      : "未开启命理补充模块，当前计划完全基于心理测评与叙事数据生成。",
  };
}

export function renderLogin(container) {
  container.innerHTML = `
    <section class="hero">
      <p class="meta-line">Inner Journey</p>
      <h2>看见自己</h2>
      <p>在安静处看见自己，在混沌里辨认方向。</p>
      <div class="hero-stats">
        <span>看见</span>
        <span>整合</span>
        <span>成为</span>
      </div>
    </section>

    <section class="panel">
      <p class="meta-line">Quiet Entry</p>
      <h2>登录后，开始你的内在旅程</h2>
      <form id="login-form" class="grid" style="max-width:480px;">
        <div>
          <label>用户名</label>
          <input name="username" required />
        </div>
        <div>
          <label>密码</label>
          <input name="password" type="password" required />
        </div>
        <div class="row">
          <button class="primary" type="submit">登录</button>
          <button class="secondary" type="button" id="guest-login">游客体验</button>
        </div>
      </form>
      <p id="login-error" class="tip warn" style="display:none;"></p>
    </section>

    <section class="panel panel-subtle">
      <p class="meta-line">First Visit</p>
      <h2>没有账号？直接注册</h2>
      <form id="register-form" class="grid" style="max-width:480px;">
        <div>
          <label>用户名</label>
          <input name="username" required />
        </div>
        <div>
          <label>邮箱（选填）</label>
          <input name="email" type="email" />
        </div>
        <div>
          <label>密码</label>
          <input name="password" type="password" required />
        </div>
        <div class="row">
          <button class="primary" type="submit">注册并进入</button>
        </div>
      </form>
      <p id="register-error" class="tip warn" style="display:none;"></p>
    </section>
  `;

  container.querySelector("#login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    try {
      await login(form.get("username"), form.get("password"));
      location.hash = "#/dashboard";
    } catch (error) {
      const target = container.querySelector("#login-error");
      target.style.display = "block";
      target.textContent = error.message;
    }
  });

  container.querySelector("#guest-login").addEventListener("click", async () => {
    const target = container.querySelector("#login-error");
    try {
      await guestLogin();
      location.hash = "#/dashboard";
    } catch (error) {
      target.style.display = "block";
      target.textContent = error.message;
    }
  });

  container.querySelector("#register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const target = container.querySelector("#register-error");
    try {
      await register(
        String(form.get("username") || "").trim(),
        String(form.get("password") || ""),
        String(form.get("email") || "").trim(),
      );
      location.hash = "#/dashboard";
    } catch (error) {
      target.style.display = "block";
      target.textContent = error.message;
    }
  });
}

export async function renderDashboard(container) {
  const [plans, actions, reviews] = await Promise.all([
    apiFetch("/annual-plans/"),
    apiFetch("/monthly-actions/"),
    apiFetch("/monthly-reviews/"),
  ]);

  container.innerHTML = `
    <section class="hero">
      <p class="meta-line">存在与虚无之间</p>
      <h2 class="quote-cn">即使心有混沌，也能孕育跳舞的星辰。</h2>
      <p class="quote-de">当你愿意缓慢凝视，答案会在沉默处浮现。</p>
    </section>

    <section class="panel">
      <p class="meta-line">旅程片段</p>
      <div class="grid three">
        <div class="kpi"><span>已留下的计划片段</span><strong>${plans.length}</strong></div>
        <div class="kpi"><span>已实践的行动片段</span><strong>${actions.length}</strong></div>
        <div class="kpi"><span>已完成的回望片段</span><strong>${reviews.length}</strong></div>
      </div>
      <div class="row" style="margin-top:16px;">
        <button class="primary" id="to-assessment">看见（5-7分钟）</button>
        <button class="secondary" id="logout">退出登录</button>
      </div>
    </section>
  `;

  container.querySelector("#to-assessment").addEventListener("click", () => {
    location.hash = "#/assessment";
  });

  container.querySelector("#logout").addEventListener("click", () => {
    clearAuth();
    location.hash = "#/login";
  });
}

export function renderAssessment(container) {
  const draft = state.assessmentDraft || {
    answers: {},
    deepAnswers: {},
    enableMystic: false,
    birth_date: "",
    birth_time: "",
  };

  const questionRows = QUESTIONNAIRE.map((q, index) => `
    <div class="question-item">
      <p>${index + 1}. ${q.text}</p>
      <select name="${q.id}" required>
        <option value="">请选择</option>
        <option value="1" ${String(draft.answers?.[q.id] || "") === "1" ? "selected" : ""}>1 - 非常不符合</option>
        <option value="2" ${String(draft.answers?.[q.id] || "") === "2" ? "selected" : ""}>2 - 不太符合</option>
        <option value="3" ${String(draft.answers?.[q.id] || "") === "3" ? "selected" : ""}>3 - 一般</option>
        <option value="4" ${String(draft.answers?.[q.id] || "") === "4" ? "selected" : ""}>4 - 比较符合</option>
        <option value="5" ${String(draft.answers?.[q.id] || "") === "5" ? "selected" : ""}>5 - 非常符合</option>
      </select>
    </div>
  `).join("");

  const deepRows = DEEP_QUESTIONS.map((q, idx) => `
    <div>
      <label>${idx + 1}. ${q.label}</label>
      <textarea name="${q.id}">${esc(draft.deepAnswers?.[q.id] || "")}</textarea>
    </div>
  `).join("");

  container.innerHTML = `
    <section class="panel">
      <h2>看见自己（5-7分钟）</h2>
      <div class="grid two">${questionRows}</div>
    </section>

    <section class="panel">
      <h2>内在叙事补充</h2>
      <form id="assessment-flow" class="grid">${deepRows}</form>
    </section>

    <section class="panel">
      <h2>出生信息（选填）</h2>
      <label><input type="checkbox" id="enable-mystic" ${draft.enableMystic ? "checked" : ""} /> 启用命理严选分析（八字 + 紫微星盘十二宫）</label>
      <div id="mystic-fields" class="grid two" style="display:${draft.enableMystic ? "grid" : "none"}; margin-top:10px;">
        <div>
          <label>出生日期</label>
          <input type="date" name="birth_date" form="assessment-flow" value="${esc(draft.birth_date || "")}" />
        </div>
        <div>
          <label>出生时间（24小时制）</label>
          <input type="time" name="birth_time" form="assessment-flow" step="60" value="${esc(draft.birth_time || "")}" />
        </div>
      </div>
      <p class="tip warn">命理模块将优先调用专业排盘服务，重点依据八字与紫微十二宫结构生成建议，仅用于辅助决策。</p>
      <div class="row">
        <button class="primary" id="generate-profile">生成天赋报告</button>
      </div>
      <p id="assessment-msg"></p>
    </section>
  `;

  const mysticSwitch = container.querySelector("#enable-mystic");
  const mysticFields = container.querySelector("#mystic-fields");
  const assessmentForm = container.querySelector("#assessment-flow");

  const saveDraftFromUi = () => {
    const answers = {};
    for (const q of QUESTIONNAIRE) {
      const field = container.querySelector(`select[name='${q.id}']`);
      answers[q.id] = field?.value || "";
    }

    const deepAnswers = {};
    for (const q of DEEP_QUESTIONS) {
      const field = container.querySelector(`textarea[name='${q.id}']`);
      deepAnswers[q.id] = (field?.value || "").trim();
    }

    setAssessmentDraft({
      answers,
      deepAnswers,
      enableMystic: mysticSwitch.checked,
      birth_date: container.querySelector("input[name='birth_date']")?.value || "",
      birth_time: container.querySelector("input[name='birth_time']")?.value || "",
    });
  };

  mysticSwitch.addEventListener("change", () => {
    mysticFields.style.display = mysticSwitch.checked ? "grid" : "none";
    saveDraftFromUi();
  });

  container.querySelectorAll("select[name^='q']").forEach((el) => {
    el.addEventListener("change", saveDraftFromUi);
  });
  assessmentForm.querySelectorAll("textarea, input[name='birth_date'], input[name='birth_time']").forEach((el) => {
    el.addEventListener("input", saveDraftFromUi);
    el.addEventListener("change", saveDraftFromUi);
  });

  saveDraftFromUi();

  container.querySelector("#generate-profile").addEventListener("click", async () => {
    saveDraftFromUi();
    const form = new FormData(assessmentForm);

    const answers = {};
    for (const q of QUESTIONNAIRE) {
      const field = document.querySelector(`select[name='${q.id}']`);
      const val = field?.value;
      if (!val) {
        container.querySelector("#assessment-msg").textContent = "请先完成所有量表题目。";
        return;
      }
      answers[q.id] = Number(val);
    }

    const deepAnswers = {};
    for (const q of DEEP_QUESTIONS) {
      const val = (form.get(q.id) || "").toString().trim();
      deepAnswers[q.id] = val;
    }

    const dimensionScores = buildDimensionScores(answers);
    const behaviorScores = {
      ...dimensionScores,
      te: normalizeScore(dimensionScores.te + keywordBoost(deepAnswers.dq2, { 组织: 6, 管理: 6, 目标: 6 })),
      fi: normalizeScore(dimensionScores.fi + keywordBoost(deepAnswers.dq1, { 敏感: 6, 坚持: 6, 价值: 6 })),
    };

    const hiddenTalents = inferHiddenTalents(deepAnswers, dimensionScores);
    const talentReport = generateTalentReport(dimensionScores, deepAnswers, hiddenTalents);

    let mysticReport = null;
    let externalScores = { ...dimensionScores };

    if (mysticSwitch.checked && form.get("birth_date")) {
      mysticReport = await resolveMysticReport(form, talentReport);
      externalScores = {
        ...externalScores,
        ni: normalizeScore(externalScores.ni + 5),
        ti: normalizeScore(externalScores.ti + 4),
      };
    }

    try {
      if (mysticReport) {
        await upsertMysticInput(form);
      }

      const assessment = await apiFetch("/assessments/", {
        method: "POST",
        body: JSON.stringify({
          version: "deep-talent-v2",
          questionnaire_data: dimensionScores,
          behavior_data: behaviorScores,
          external_import_data: externalScores,
        }),
      });

      const profile = await apiFetch(`/assessments/${assessment.id}/generate-profile/`, {
        method: "POST",
      });

      state.latestAssessmentId = assessment.id;
      state.activeProfile = {
        ...profile,
        report: talentReport,
      };
      state.correctedProfile = null;
      state.flowContext = {
        deepAnswers,
        dimensionScores,
        mysticReport,
      };

      container.querySelector("#assessment-msg").textContent = "深度天赋报告已生成，正在跳转...";
      setTimeout(() => {
        location.hash = "#/profile";
      }, 450);
    } catch (error) {
      container.querySelector("#assessment-msg").textContent = error.message;
    }
  });
}

function getCurrentRanking(profile) {
  if (profile?.report?.top_rankings) {
    return profile.report.top_rankings.map((x) => [x.key, x.score]);
  }
  if (!profile?.strengths_rank_data || profile.strengths_rank_data.length === 0) {
    return [];
  }
  return profile.strengths_rank_data
    .map(([key, score]) => [key, normalizeScore(score)])
    .sort((a, b) => b[1] - a[1]);
}

export async function renderProfile(container) {
  const profileList = await apiFetch("/talent-profiles/");
  const profile = state.correctedProfile || state.activeProfile || profileList[0];

  if (!profile) {
    container.innerHTML = `<section class="panel"><p>还没有报告，请先完成问卷。</p></section>`;
    return;
  }

  const ranking = getCurrentRanking(profile);
  const report = profile.report || {
    summary: "已生成画像。",
    hidden_talents: [],
    deep_analysis: [],
    long_form: "",
    challenge_pattern: "",
    growth_principle: "",
  };
  const mysticReport = state.flowContext.mysticReport;
  const integrated = buildIntegratedReading(report, mysticReport, ranking);

  container.innerHTML = `
    <section class="panel">
      <p class="meta-line">Destiny Reading</p>
      <h2 class="destiny-headline">${esc(integrated.headline)}</h2>
      <p class="destiny-opening">${esc(integrated.opening)}</p>

      <h3 style="margin-top:16px;">融合解读</h3>
      <div class="long-report">${integrated.narrative}</div>

      <div class="score-bars" id="ranking-bars" style="display:none;">${rankingHtml(ranking)}</div>

      <h3 style="margin-top:16px;">16题多维倾向性评分雷达图</h3>
      <div class="radar-wrap" id="radar-chart">${buildRadarSvg(ranking)}</div>

      <h3 style="margin-top:16px;">关键命运线索</h3>
      <ul>
        ${integrated.highlights.map((x) => `<li>${esc(x)}</li>`).join("")}
      </ul>

      <h3 style="margin-top:16px;">被隐藏的天赋</h3>
      <div>${(report.hidden_talents || []).map((x) => `<span class="chip">${esc(x)}</span>`).join("")}</div>

      <h3 style="margin-top:16px;">深度解读</h3>
      <ul>
        ${(report.deep_analysis || []).map((x) => `<li>${esc(x)}</li>`).join("")}
      </ul>

      <p><strong>典型卡点：</strong>${esc(report.challenge_pattern || "")}</p>
      <p><strong>成长原则：</strong>${esc(report.growth_principle || "")}</p>

      ${mysticReport ? `
      <div class="mystic-block" style="margin-top:16px;">
        <p><strong>命理坐标：</strong>${esc(mysticReport.bazi)}；${esc(mysticReport.yongshen)}；${esc(mysticReport.flying_star)} ${esc(mysticReport.flying_advice)}</p>
        <p><strong>适配方向：</strong>${esc(mysticReport.best_directions)}</p>
        <p><strong>适配城市：</strong>${mysticReport.best_cities.map((x) => `<span class="chip">${esc(x)}</span>`).join("")}</p>
        <p><strong>适配行业：</strong>${mysticReport.best_industries.map((x) => `<span class="chip">${esc(x)}</span>`).join("")}</p>
      </div>
      ` : ""}
    </section>

    <section class="panel panel-subtle">
      <h2>补充与重写</h2>
      <div style="margin-top:12px;">
        <label>补充叙事</label>
        <textarea id="edit-text"></textarea>
      </div>
      <div class="row" style="margin-top:12px;">
        <button class="primary" id="regenerate-now">重新整合</button>
        <button class="secondary" id="to-plan">成为</button>
      </div>
      <p id="profile-msg"></p>
    </section>
  `;

  container.querySelector("#to-plan").addEventListener("click", () => {
    location.hash = "#/plan";
  });

  container.querySelector("#regenerate-now").addEventListener("click", async () => {
    const editText = container.querySelector("#edit-text").value.trim();
    const deltas = {};

    const baseScores = Object.fromEntries(ranking);
    const revisedScores = {};
    Object.keys(baseScores).forEach((key) => {
      revisedScores[key] = normalizeScore(baseScores[key] + (deltas[key] || 0));
    });

    const revisedRanking = getSortedRanking(revisedScores);
    const rankingBars = container.querySelector("#ranking-bars");
    if (rankingBars) {
      rankingBars.innerHTML = rankingHtml(revisedRanking);
    }
    container.querySelector("#radar-chart").innerHTML = buildRadarSvg(revisedRanking);

    const regenerated = {
      ...profile,
      report: {
        ...(profile.report || {}),
        top_rankings: revisedRanking.map(([key, score]) => ({ key, score, label: DIMENSION_META[key]?.label || key })),
        summary: "已根据你的纠偏意见完成二次生成，新的优势结构已经更新。",
      },
    };
    state.correctedProfile = regenerated;

    try {
      if (profile.id) {
        await apiFetch("/profile-edits/", {
          method: "POST",
          body: JSON.stringify({
            profile: profile.id,
            edit_text: editText,
            edited_fields: Object.keys(deltas).filter((k) => deltas[k] !== 0),
            regenerated_profile_data: { ranking: revisedRanking, note: editText },
          }),
        });
      }
      container.querySelector("#profile-msg").textContent = "二次生成完成，已保存纠偏记录。";
    } catch (error) {
      container.querySelector("#profile-msg").textContent = `已本地生成，保存失败：${error.message}`;
    }
  });
}

export async function renderPlan(container) {
  const year = new Date().getFullYear();
  const profile = state.correctedProfile || state.activeProfile;
  const report = profile?.report || null;
  const mysticReport = state.flowContext.mysticReport;
  const planPack = report ? buildDetailedPlan(report, mysticReport) : null;

  container.innerHTML = `
    <section class="panel">
      <h2>详细计划方案</h2>
      ${planPack ? `
        <p><strong>年度主轴：</strong>${esc(planPack.annual_direction)}</p>
        <p><strong>维度策略：</strong>${esc(planPack.focus_summary)}</p>

        <h3 style="margin-top:16px;">全生活维度（90天）</h3>
        ${planPack.life_dimensions.map((dimension) => `
          <article class="step" style="margin-top:10px;">
            <h3>${esc(dimension.name)}</h3>
            <p><strong>90天目标：</strong>${esc(dimension.objective)}</p>
            <ul>
              <li><strong>保底层：</strong>${esc(dimension.baseline)}</li>
              <li><strong>进阶层：</strong>${esc(dimension.progress)}</li>
              <li><strong>挑战层：</strong>${esc(dimension.challenge)}</li>
            </ul>
            <p><strong>指标：</strong>${esc(dimension.metric)}</p>
            <p><strong>预警：</strong>${esc(dimension.warning)}</p>
            <p><strong>纠偏：</strong>${esc(dimension.correction)}</p>
            <p><strong>最低动作：</strong>${esc(dimension.fallback)}</p>
          </article>
        `).join("")}

        ${planPack.phase_plan.map((p) => `
          <article class="step" style="margin-top:10px;">
            <h3>${esc(p.phase)}</h3>
            <ul>${p.goals.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>
          </article>
        `).join("")}

        <h3 style="margin-top:16px;">每周执行节奏</h3>
        <ul>${planPack.weekly_actions.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>

        <h3 style="margin-top:16px;">风险预案</h3>
        <ul>${planPack.risk_controls.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>

        <h3 style="margin-top:16px;">每日执行规则</h3>
        <ul>${planPack.daily_actions.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>

        <h3 style="margin-top:16px;">周复盘 5 问</h3>
        <ul>${planPack.weekly_review_questions.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>

        <h3 style="margin-top:16px;">命理协同建议</h3>
        <p>${esc(planPack.mystic_alignment)}</p>
      ` : `<p>请先完成问卷与报告生成，再进入计划页。</p>`}

      <div class="row" style="margin-top:12px;">
        <button class="primary" id="save-plan">保存到年度计划</button>
      </div>
      <p id="plan-msg"></p>
    </section>
  `;

  container.querySelector("#save-plan").addEventListener("click", async () => {
    if (!planPack) {
      container.querySelector("#plan-msg").textContent = "请先生成天赋报告。";
      return;
    }

    try {
      const plans = await apiFetch(`/annual-plans/?year=${year}`);
      const directionText = planPack.annual_direction;
      if (plans.length > 0) {
        await apiFetch(`/annual-plans/${plans[0].id}/`, {
          method: "PATCH",
          body: JSON.stringify({ direction_text: directionText }),
        });
      } else {
        await apiFetch("/annual-plans/", {
          method: "POST",
          body: JSON.stringify({
            year,
            direction_text: directionText,
            evidence_chain_data: { phases: planPack.phase_plan },
            status: "draft",
          }),
        });
      }
      container.querySelector("#plan-msg").textContent = "详细计划方案已保存。";
    } catch (error) {
      container.querySelector("#plan-msg").textContent = error.message;
    }
  });
}

export function renderPrivacy(container) {
  container.innerHTML = `
    <section class="panel">
      <h2>隐私与数据控制</h2>
      <p>你可以随时执行一键删除，系统仅保留不可追溯聚合数据。</p>
      <div class="row">
        <button class="secondary" id="delete-data">一键删除个人数据</button>
      </div>
      <p id="privacy-msg"></p>
    </section>
  `;

  container.querySelector("#delete-data").addEventListener("click", async () => {
    if (!confirm("确认删除个人数据？该操作不可恢复。")) {
      return;
    }

    try {
      const result = await apiFetch("/delete-requests/execute/", { method: "POST" });
      container.querySelector("#privacy-msg").textContent = `删除完成，请求ID: ${result.delete_request_id}`;
    } catch (error) {
      container.querySelector("#privacy-msg").textContent = error.message;
    }
  });
}
