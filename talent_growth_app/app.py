import datetime
import hashlib
import json
import math
import sqlite3
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd
import streamlit as st

try:
    from timezonefinder import TimezoneFinder

    TIMEZONE_FINDER = TimezoneFinder()
except Exception:
    TIMEZONE_FINDER = None

try:
    from lunar_python import Solar

    HAS_LUNAR_PYTHON = True
except Exception:
    HAS_LUNAR_PYTHON = False

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "talent_growth.db"

DIMENSIONS = {
    "analytical": "分析思维",
    "creative": "创造力",
    "communication": "沟通表达",
    "leadership": "领导协作",
    "empathy": "同理心",
    "execution": "执行力",
    "learning": "学习敏捷",
    "resilience": "抗压韧性",
}

QUESTIONS = [
    ("面对复杂问题，我会先拆解再行动。", "analytical"),
    ("我喜欢通过数据验证想法。", "analytical"),
    ("我经常冒出新点子并愿意尝试。", "creative"),
    ("我会主动优化已有流程或方案。", "creative"),
    ("我能把复杂内容讲清楚。", "communication"),
    ("我在表达观点时会注意对方感受。", "communication"),
    ("团队讨论时我常能推动达成共识。", "leadership"),
    ("我愿意承担责任并带动他人行动。", "leadership"),
    ("我能敏感察觉他人的情绪变化。", "empathy"),
    ("我善于从他人视角理解问题。", "empathy"),
    ("我能持续推进任务直到完成。", "execution"),
    ("我会为目标制定清晰的执行步骤。", "execution"),
    ("遇到新领域，我能快速上手。", "learning"),
    ("我会主动复盘并总结经验。", "learning"),
    ("面对压力，我能保持稳定输出。", "resilience"),
    ("遭遇挫折后，我通常能较快恢复。", "resilience"),
]

GROWTH_LIBRARY = {
    "analytical": {
        "strength": "擅长结构化分析、逻辑判断和决策支持。",
        "careers": ["数据分析", "商业分析", "产品策略", "医学信息分析"],
        "actions": ["每周完成 1 次数据复盘", "学习一个统计或分析模型", "做 1 次问题树拆解练习"],
    },
    "creative": {
        "strength": "擅长发散思考、提出创新方案和改进路径。",
        "careers": ["创新项目", "内容策划", "用户体验", "品牌传播"],
        "actions": ["每周输出 10 个创意", "练习 SCAMPER 创新法", "做 1 次跨领域灵感采样"],
    },
    "communication": {
        "strength": "擅长表达复杂信息、影响他人理解与行动。",
        "careers": ["培训讲师", "项目沟通", "客户成功", "医学教育"],
        "actions": ["每周做 1 次 5 分钟演讲", "练习金字塔表达", "记录并优化一次关键沟通"],
    },
    "leadership": {
        "strength": "擅长组织协作、设定目标并推动落地。",
        "careers": ["项目管理", "团队管理", "运营管理", "跨部门协调"],
        "actions": ["主持 1 次高质量会议", "建立任务看板并跟进", "进行 1 次反馈对话"],
    },
    "empathy": {
        "strength": "擅长理解他人需求，建立信任和合作关系。",
        "careers": ["人力发展", "咨询顾问", "用户研究", "患者支持"],
        "actions": ["每周进行 2 次深度倾听", "练习非暴力沟通", "记录并复盘冲突场景"],
    },
    "execution": {
        "strength": "擅长把目标拆解成行动并高效推进结果。",
        "careers": ["运营执行", "PMO", "交付管理", "项目推进"],
        "actions": ["每天列 3 个最重要任务", "使用番茄法 4 轮", "周末做执行复盘"],
    },
    "learning": {
        "strength": "擅长快速学习、迁移经验并持续提升。",
        "careers": ["专家发展路径", "新业务探索", "知识管理", "培训发展"],
        "actions": ["每周学习 3 小时", "输出一页知识卡片", "做一次教会别人练习"],
    },
    "resilience": {
        "strength": "擅长在不确定和高压情境下稳定表现。",
        "careers": ["关键岗位", "应急协同", "复杂项目", "高压沟通场景"],
        "actions": ["建立压力日志", "每周 3 次运动", "进行 10 分钟冥想练习"],
    },
}

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
CHINESE_ZODIAC = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

STEM_ELEMENT = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

BRANCH_ELEMENT = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

ELEMENT_DIRECTION = {
    "木": "东方、东南方",
    "火": "南方",
    "土": "中部、西南、东北",
    "金": "西方、西北方",
    "水": "北方",
}

ELEMENT_INDUSTRY = {
    "木": ["教育培训", "文化出版", "生物健康", "组织发展"],
    "火": ["品牌传播", "互联网产品", "能源科技", "内容创作"],
    "土": ["运营管理", "地产与供应链", "咨询服务", "项目管理"],
    "金": ["金融风控", "法律合规", "精密制造", "医疗器械"],
    "水": ["数据分析", "物流航运", "医药研发", "心理咨询"],
}

ELEMENT_ADVICE = {
    "木": "强调成长与拓展，适合通过学习和协作打开机会。",
    "火": "强调影响力与表达，适合主动站到台前。",
    "土": "强调稳定与承载，适合做长期主义和体系建设。",
    "金": "强调规则与决断，适合在高标准场景建立专业壁垒。",
    "水": "强调洞察与流动，适合在变化中做策略调整。",
}

ZIWEI_AXIS = [
    "命宫主轴：自我驱动与人生定位",
    "兄弟宫主轴：同伴资源与横向协作",
    "夫妻宫主轴：关系经营与亲密边界",
    "子女宫主轴：创造表达与成果孵化",
    "财帛宫主轴：价值变现与资源管理",
    "疾厄宫主轴：身心能量与压力调节",
    "迁移宫主轴：外部机会与环境适应",
    "交友宫主轴：社群网络与影响半径",
    "官禄宫主轴：职业路径与成就模式",
    "田宅宫主轴：生活基盘与长期配置",
    "福德宫主轴：精神内核与幸福感来源",
    "父母宫主轴：传承支持与权威互动",
]


def table_has_column(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]
    return column_name in columns


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_text TEXT NOT NULL,
                dimension TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                checkin_date TEXT NOT NULL,
                energy_score INTEGER NOT NULL,
                note TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                scores_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS coach_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS birth_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                birth_date TEXT NOT NULL,
                birth_hour INTEGER NOT NULL,
                birth_minute INTEGER NOT NULL DEFAULT 0,
                latitude REAL NOT NULL DEFAULT 31.2304,
                longitude REAL NOT NULL DEFAULT 121.4737,
                timezone_name TEXT NOT NULL DEFAULT 'Asia/Shanghai',
                gender TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        # Migration for older databases created before multi-user support.
        if not table_has_column(conn, "goals", "user_id"):
            cur.execute("ALTER TABLE goals ADD COLUMN user_id INTEGER")
        if not table_has_column(conn, "checkins", "user_id"):
            cur.execute("ALTER TABLE checkins ADD COLUMN user_id INTEGER")
        if not table_has_column(conn, "birth_profiles", "birth_minute"):
            cur.execute("ALTER TABLE birth_profiles ADD COLUMN birth_minute INTEGER NOT NULL DEFAULT 0")
        if not table_has_column(conn, "birth_profiles", "latitude"):
            cur.execute("ALTER TABLE birth_profiles ADD COLUMN latitude REAL NOT NULL DEFAULT 31.2304")
        if not table_has_column(conn, "birth_profiles", "longitude"):
            cur.execute("ALTER TABLE birth_profiles ADD COLUMN longitude REAL NOT NULL DEFAULT 121.4737")
        if not table_has_column(conn, "birth_profiles", "timezone_name"):
            cur.execute("ALTER TABLE birth_profiles ADD COLUMN timezone_name TEXT NOT NULL DEFAULT 'Asia/Shanghai'")

        conn.commit()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    if len(username) < 3:
        return False, "用户名至少需要 3 个字符。"
    if len(password) < 6:
        return False, "密码至少需要 6 个字符。"

    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, hash_password(password), datetime.datetime.now().isoformat()),
            )
            conn.commit()
            return True, "注册成功，请登录。"
        except sqlite3.IntegrityError:
            return False, "用户名已存在，请更换。"


def authenticate_user(username: str, password: str) -> tuple[int | None, str]:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

    if not row:
        return None, "用户不存在。"

    user_id, password_hash = row
    if hash_password(password) != password_hash:
        return None, "密码错误。"

    return int(user_id), "登录成功。"


def get_username(user_id: int) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    return row[0] if row else "Unknown"


def save_assessment(user_id: int, scores: dict[str, float]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO assessments (user_id, scores_json, created_at) VALUES (?, ?, ?)",
            (user_id, json.dumps(scores, ensure_ascii=False), datetime.datetime.now().isoformat()),
        )
        conn.commit()


def get_latest_assessment(user_id: int) -> dict[str, float] | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT scores_json FROM assessments WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    if not row:
        return None
    return json.loads(row[0])


def add_goal(user_id: int, goal_text: str, dimension: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO goals (user_id, goal_text, dimension, created_at, completed) VALUES (?, ?, ?, ?, 0)",
            (user_id, goal_text, dimension, datetime.datetime.now().isoformat()),
        )
        conn.commit()


def set_goal_status(user_id: int, goal_id: int, completed: bool) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE goals SET completed = ? WHERE id = ? AND user_id = ?",
            (1 if completed else 0, goal_id, user_id),
        )
        conn.commit()


def get_goals(user_id: int) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT id, goal_text, dimension, created_at, completed FROM goals WHERE user_id = ? ORDER BY id DESC",
            conn,
            params=(user_id,),
        )


def add_checkin(user_id: int, checkin_date: str, energy_score: int, note: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO checkins (user_id, checkin_date, energy_score, note) VALUES (?, ?, ?, ?)",
            (user_id, checkin_date, energy_score, note),
        )
        conn.commit()


def get_checkins(user_id: int) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT id, checkin_date, energy_score, note FROM checkins WHERE user_id = ? ORDER BY checkin_date DESC, id DESC",
            conn,
            params=(user_id,),
        )


def add_coach_message(user_id: int, role: str, content: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO coach_messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, datetime.datetime.now().isoformat()),
        )
        conn.commit()


def get_coach_messages(user_id: int) -> list[dict[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role, content FROM coach_messages WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ).fetchall()
    return [{"role": row[0], "content": row[1]} for row in rows]


def upsert_birth_profile(
    user_id: int,
    birth_date: datetime.date,
    birth_hour: int,
    birth_minute: int,
    latitude: float,
    longitude: float,
    timezone_name: str,
    gender: str,
) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO birth_profiles
            (user_id, birth_date, birth_hour, birth_minute, latitude, longitude, timezone_name, gender, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                birth_date = excluded.birth_date,
                birth_hour = excluded.birth_hour,
                birth_minute = excluded.birth_minute,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                timezone_name = excluded.timezone_name,
                gender = excluded.gender,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                str(birth_date),
                birth_hour,
                birth_minute,
                latitude,
                longitude,
                timezone_name,
                gender,
                datetime.datetime.now().isoformat(),
            ),
        )
        conn.commit()


def get_birth_profile(user_id: int) -> dict[str, str | int] | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT birth_date, birth_hour, birth_minute, latitude, longitude, timezone_name, gender "
            "FROM birth_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "birth_date": row[0],
        "birth_hour": int(row[1]),
        "birth_minute": int(row[2]),
        "latitude": float(row[3]),
        "longitude": float(row[4]),
        "timezone_name": str(row[5] or "Asia/Shanghai"),
        "gender": row[6] or "未设置",
    }


def resolve_timezone_name(latitude: float, longitude: float) -> str:
    if TIMEZONE_FINDER is None:
        return "Asia/Shanghai"
    timezone_name = TIMEZONE_FINDER.timezone_at(lat=latitude, lng=longitude)
    return timezone_name or "Asia/Shanghai"


def get_western_zodiac(birth_date: datetime.date) -> str:
    md = birth_date.month * 100 + birth_date.day
    if 321 <= md <= 419:
        return "白羊座"
    if 420 <= md <= 520:
        return "金牛座"
    if 521 <= md <= 621:
        return "双子座"
    if 622 <= md <= 722:
        return "巨蟹座"
    if 723 <= md <= 822:
        return "狮子座"
    if 823 <= md <= 922:
        return "处女座"
    if 923 <= md <= 1023:
        return "天秤座"
    if 1024 <= md <= 1122:
        return "天蝎座"
    if 1123 <= md <= 1221:
        return "射手座"
    if 1222 <= md <= 1231 or 101 <= md <= 119:
        return "摩羯座"
    if 120 <= md <= 218:
        return "水瓶座"
    return "双鱼座"


def get_hour_branch(hour: int, minute: int = 0) -> str:
    total_minutes = hour * 60 + minute
    index = ((total_minutes + 60) // 120) % 12
    return EARTHLY_BRANCHES[index]


def equation_of_time_minutes(day_of_year: int) -> float:
    b = 2 * math.pi * (day_of_year - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def calc_true_solar_datetime(
    birth_date: datetime.date,
    birth_hour: int,
    birth_minute: int,
    longitude: float,
    timezone_name: str,
) -> tuple[datetime.datetime, float, float, float, float, str]:
    local_dt = datetime.datetime.combine(birth_date, datetime.time(hour=birth_hour, minute=birth_minute))
    try:
        tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("Asia/Shanghai")
        timezone_name = "Asia/Shanghai"

    aware_local = local_dt.replace(tzinfo=tz)
    utc_offset = aware_local.utcoffset() or datetime.timedelta()
    timezone_offset_hours = utc_offset.total_seconds() / 3600
    std_meridian = timezone_offset_hours * 15.0
    longitude_correction = 4.0 * (longitude - std_meridian)
    eot = equation_of_time_minutes(birth_date.timetuple().tm_yday)
    total_correction = longitude_correction + eot
    true_solar_dt = local_dt + datetime.timedelta(minutes=total_correction)
    return true_solar_dt, longitude_correction, eot, total_correction, timezone_offset_hours, timezone_name


def calc_destiny_profile(
    birth_date: datetime.date,
    birth_hour: int,
    birth_minute: int,
    latitude: float,
    longitude: float,
    timezone_name: str,
    gender: str,
) -> dict[str, object]:
    western_zodiac = get_western_zodiac(birth_date)

    true_solar_dt, longitude_corr, eot_corr, total_corr, timezone_offset_hours, timezone_name = calc_true_solar_datetime(
        birth_date,
        birth_hour,
        birth_minute,
        longitude,
        timezone_name,
    )

    if HAS_LUNAR_PYTHON:
        solar = Solar.fromYmdHms(
            true_solar_dt.year,
            true_solar_dt.month,
            true_solar_dt.day,
            true_solar_dt.hour,
            true_solar_dt.minute,
            true_solar_dt.second,
        )
        eight_char = solar.getLunar().getEightChar()
        ganzhi_year = eight_char.getYear()
        ganzhi_month = eight_char.getMonth()
        year_stem = ganzhi_year[0]
        year_branch = ganzhi_year[1]
        month_stem = ganzhi_month[0]
        month_branch = ganzhi_month[1]
    else:
        # Fallback if lunar_python is unavailable.
        year_index = (birth_date.year - 1984) % 60
        year_stem = HEAVENLY_STEMS[year_index % 10]
        year_branch = EARTHLY_BRANCHES[year_index % 12]
        month_branch = EARTHLY_BRANCHES[(birth_date.month + 1) % 12]
        month_stem = HEAVENLY_STEMS[(birth_date.month + 1) % 10]
        ganzhi_year = f"{year_stem}{year_branch}"
        ganzhi_month = f"{month_stem}{month_branch}"

    zodiac = CHINESE_ZODIAC[EARTHLY_BRANCHES.index(year_branch)]

    month_element = STEM_ELEMENT.get(month_stem, "木")

    hour_branch = get_hour_branch(true_solar_dt.hour, true_solar_dt.minute)
    elements = {
        "木": 0,
        "火": 0,
        "土": 0,
        "金": 0,
        "水": 0,
    }

    elements[STEM_ELEMENT[year_stem]] += 2
    elements[BRANCH_ELEMENT[year_branch]] += 1
    elements[month_element] += 1
    elements[BRANCH_ELEMENT[month_branch]] += 1
    elements[BRANCH_ELEMENT[hour_branch]] += 1
    day_element = ["木", "火", "土", "金", "水"][birth_date.toordinal() % 5]
    elements[day_element] += 1

    dominant = max(elements, key=elements.get)
    weakest = min(elements, key=elements.get)

    latitude_zone = int(abs(latitude) // 10)
    palace_index = (birth_date.month + EARTHLY_BRANCHES.index(hour_branch) + latitude_zone) % len(ZIWEI_AXIS)
    ziwei_focus = ZIWEI_AXIS[palace_index]

    cycle = ["木", "火", "土", "金", "水"]
    start_idx = cycle.index(dominant)
    age = datetime.date.today().year - birth_date.year
    luck_rows = []
    for i, start_age in enumerate([10, 20, 30, 40, 50, 60, 70]):
        elem = cycle[(start_idx + i) % len(cycle)]
        luck_rows.append(
            {
                "年龄段": f"{start_age}-{start_age + 9}",
                "大运五行": elem,
                "阶段建议": ELEMENT_ADVICE[elem],
            }
        )

    return {
        "gender": gender,
        "western_zodiac": western_zodiac,
        "chinese_zodiac": zodiac,
        "ganzhi_year": ganzhi_year,
        "ganzhi_month": ganzhi_month,
        "hour_branch": hour_branch,
        "true_solar_time": true_solar_dt.strftime("%Y-%m-%d %H:%M"),
        "longitude_correction_min": round(longitude_corr, 2),
        "equation_of_time_min": round(eot_corr, 2),
        "total_correction_min": round(total_corr, 2),
        "latitude": latitude,
        "longitude": longitude,
        "timezone_name": timezone_name,
        "timezone_offset": round(timezone_offset_hours, 2),
        "elements": elements,
        "dominant_element": dominant,
        "weakest_element": weakest,
        "direction": ELEMENT_DIRECTION[dominant],
        "industries": ELEMENT_INDUSTRY[dominant],
        "ziwei_focus": ziwei_focus,
        "luck_rows": luck_rows,
        "current_age": age,
        "disclaimer": "本模块为简化模型（含 IANA 时区/夏令时 + 真太阳时修正 + 节气年柱月柱），用于成长参考，不替代专业命理排盘。",
    }


def evaluate(answers: dict[str, int]) -> dict[str, float]:
    grouped = {k: [] for k in DIMENSIONS}
    for idx, (_, dim) in enumerate(QUESTIONS):
        grouped[dim].append(answers.get(f"q_{idx}", 3))

    scores = {}
    for dim, values in grouped.items():
        avg = sum(values) / len(values)
        scores[dim] = round((avg / 5) * 100, 1)
    return scores


def generate_plan(scores: dict[str, float]) -> list[dict[str, str]]:
    top_dims = sorted(scores, key=scores.get, reverse=True)[:3]
    plan = []
    for i, dim in enumerate(top_dims, start=1):
        item = GROWTH_LIBRARY[dim]
        plan.append(
            {
                "阶段": f"第 {i * 4 - 3} - {i * 4} 周",
                "核心天赋": DIMENSIONS[dim],
                "目标": item["strength"],
                "行动建议": "；".join(item["actions"]),
            }
        )
    return plan


def generate_coach_reply(
    user_input: str,
    supplement: str,
    scores: dict[str, float] | None,
    goals_df: pd.DataFrame,
    checkins_df: pd.DataFrame,
    destiny_profile: dict[str, object] | None,
) -> str:
    combined = f"{supplement} {user_input}".lower()
    focus_dim = None
    keyword_map = {
        "execution": ["拖延", "执行", "效率", "完成", "deadline", "procrast"],
        "communication": ["沟通", "表达", "汇报", "演讲", "冲突", "反馈"],
        "resilience": ["压力", "焦虑", "疲惫", "倦怠", "stress", "burnout"],
        "learning": ["学习", "技能", "上手", "知识", "课程"],
        "leadership": ["带团队", "管理", "协作", "推进", "团队"],
        "creative": ["创意", "创新", "点子", "方案"],
        "analytical": ["分析", "决策", "数据", "逻辑"],
        "empathy": ["共情", "理解", "关系", "倾听", "情绪"],
    }
    for dim, words in keyword_map.items():
        if any(word in combined for word in words):
            focus_dim = dim
            break

    if focus_dim is None and scores:
        focus_dim = sorted(scores, key=scores.get, reverse=True)[0]
    if focus_dim is None:
        focus_dim = "execution"

    profile = GROWTH_LIBRARY[focus_dim]
    top_hint = ""
    if scores:
        top_dims = sorted(scores, key=scores.get, reverse=True)[:2]
        top_hint = f"你的优势倾向是：{DIMENSIONS[top_dims[0]]}、{DIMENSIONS[top_dims[1]]}。"

    goal_hint = "目前还没有设定成长目标。建议先建立一个 7 天可完成的小目标。"
    if not goals_df.empty:
        done_count = int(goals_df["completed"].sum())
        goal_hint = f"你当前有 {len(goals_df)} 个目标，其中已完成 {done_count} 个。"

    energy_hint = "暂无打卡数据。"
    if not checkins_df.empty:
        avg_energy = round(float(checkins_df["energy_score"].mean()), 1)
        energy_hint = f"你最近的平均状态分是 {avg_energy}/10。"

    actions = "；".join(profile["actions"])
    destiny_hint = ""
    if destiny_profile:
        destiny_hint = (
            f"命理侧参考：你当前更顺势的发力方向是{destiny_profile['direction']}，"
            f"可优先关注{ '、'.join(destiny_profile['industries']) }。\n"
        )
    reply = (
        f"我建议你把本周重点放在【{DIMENSIONS[focus_dim]}】。\n\n"
        f"观察：{top_hint}{goal_hint}{energy_hint}\n"
        f"{destiny_hint}"
        f"行动建议：{actions}\n"
        "请从以上行动里选 1 条，告诉我你准备在什么时间执行，我会帮你拆到日计划。"
    )
    return reply


def ensure_auth_state() -> None:
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("username", "")


def show_auth_panel() -> int | None:
    ensure_auth_state()
    with st.sidebar:
        st.header("账号")

        if st.session_state["user_id"]:
            st.success(f"已登录：{st.session_state['username']}")
            if st.button("退出登录"):
                st.session_state["user_id"] = None
                st.session_state["username"] = ""
                st.session_state.pop("scores", None)
                st.rerun()
            return int(st.session_state["user_id"])

        login_tab, signup_tab = st.tabs(["登录", "注册"])

        with login_tab:
            with st.form("login_form"):
                username = st.text_input("用户名", key="login_username")
                password = st.text_input("密码", type="password", key="login_password")
                submit_login = st.form_submit_button("登录")
                if submit_login:
                    user_id, message = authenticate_user(username, password)
                    if user_id:
                        st.session_state["user_id"] = user_id
                        st.session_state["username"] = get_username(user_id)
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        with signup_tab:
            with st.form("signup_form"):
                new_username = st.text_input("新用户名", key="signup_username")
                new_password = st.text_input("新密码", type="password", key="signup_password")
                submit_signup = st.form_submit_button("注册")
                if submit_signup:
                    ok, message = create_user(new_username, new_password)
                    if ok:
                        st.success(message)
                    else:
                        st.error(message)

    return None


def show_home(username: str) -> None:
    st.title("个人天赋挖掘与成长软件")
    st.caption("Talent Discovery & Growth Studio")
    st.write(f"欢迎你，{username}")

    st.markdown(
        """
        这个工具帮助你完成三件事：
        1. 识别你的核心天赋优势
        2. 生成 12 周成长计划
        3. 用目标与打卡持续追踪改变
        """
    )


def show_assessment(user_id: int) -> None:
    st.subheader("1) 天赋测评")
    st.write("请根据最近 1-3 个月的真实表现评分：1=非常不符合，5=非常符合")

    if "scores" not in st.session_state:
        latest = get_latest_assessment(user_id)
        if latest:
            st.session_state["scores"] = latest

    answers = {}
    cols = st.columns(2)
    for idx, (question, _) in enumerate(QUESTIONS):
        with cols[idx % 2]:
            answers[f"q_{idx}"] = st.slider(question, min_value=1, max_value=5, value=3, key=f"q_{idx}")

    if st.button("生成天赋报告", type="primary"):
        scores = evaluate(answers)
        st.session_state["scores"] = scores
        save_assessment(user_id, scores)

    scores = st.session_state.get("scores")
    if not scores:
        return

    st.success("报告已生成")

    df = pd.DataFrame(
        {
            "维度": [DIMENSIONS[d] for d in scores.keys()],
            "得分": list(scores.values()),
        }
    )

    st.dataframe(df, hide_index=True, use_container_width=True)
    st.bar_chart(df.set_index("维度"))

    top_dims = sorted(scores, key=scores.get, reverse=True)[:3]
    st.markdown("### 你的 Top 3 天赋")
    for dim in top_dims:
        profile = GROWTH_LIBRARY[dim]
        st.markdown(f"**{DIMENSIONS[dim]}（{scores[dim]} 分）**")
        st.write(profile["strength"])
        st.write("适配方向：" + "、".join(profile["careers"]))

    st.markdown("### 出生信息综合测算（星座 / 八字 / 紫微）")
    st.caption("输入出生信息与经纬度后，使用真太阳时修正，再生成方位、行业和大运建议。")

    saved_profile = get_birth_profile(user_id)
    default_birth_date = datetime.date(1995, 1, 1)
    default_birth_hour = 9
    default_birth_minute = 0
    default_latitude = 31.2304
    default_longitude = 121.4737
    default_timezone_name = "Asia/Shanghai"
    default_gender = "未设置"
    if saved_profile:
        default_birth_date = datetime.date.fromisoformat(str(saved_profile["birth_date"]))
        default_birth_hour = int(saved_profile["birth_hour"])
        default_birth_minute = int(saved_profile["birth_minute"])
        default_latitude = float(saved_profile["latitude"])
        default_longitude = float(saved_profile["longitude"])
        default_timezone_name = str(saved_profile["timezone_name"])
        default_gender = str(saved_profile["gender"])

    gender_options = ["未设置", "女", "男", "其他"]
    default_gender_idx = gender_options.index(default_gender) if default_gender in gender_options else 0

    with st.form("birth_destiny_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            birth_date = st.date_input("出生日期", value=default_birth_date)
        with c2:
            birth_hour = st.selectbox("出生小时（0-23）", options=list(range(24)), index=default_birth_hour)
            birth_minute = st.selectbox("出生分钟（0-59）", options=list(range(60)), index=default_birth_minute)
        with c3:
            latitude = st.number_input("出生地纬度", min_value=-90.0, max_value=90.0, value=default_latitude, step=0.0001)
            longitude = st.number_input("出生地经度", min_value=-180.0, max_value=180.0, value=default_longitude, step=0.0001)
        with c4:
            auto_timezone = resolve_timezone_name(float(latitude), float(longitude))
            st.text_input("自动识别时区（IANA）", value=auto_timezone, disabled=True)
            if auto_timezone != default_timezone_name:
                st.caption(f"上次保存时区：{default_timezone_name}")
            gender = st.selectbox("性别（可选）", options=gender_options, index=default_gender_idx)

        submit_birth = st.form_submit_button("保存并测算")
        if submit_birth:
            upsert_birth_profile(
                user_id,
                birth_date,
                int(birth_hour),
                int(birth_minute),
                float(latitude),
                float(longitude),
                auto_timezone,
                gender,
            )
            st.session_state["destiny_profile"] = calc_destiny_profile(
                birth_date,
                int(birth_hour),
                int(birth_minute),
                float(latitude),
                float(longitude),
                auto_timezone,
                gender,
            )
            st.success("出生信息已保存，命理测算已更新。")

    if "destiny_profile" not in st.session_state and saved_profile:
        st.session_state["destiny_profile"] = calc_destiny_profile(
            datetime.date.fromisoformat(str(saved_profile["birth_date"])),
            int(saved_profile["birth_hour"]),
            int(saved_profile["birth_minute"]),
            float(saved_profile["latitude"]),
            float(saved_profile["longitude"]),
            str(saved_profile["timezone_name"]),
            str(saved_profile["gender"]),
        )

    destiny_profile = st.session_state.get("destiny_profile")
    if not destiny_profile:
        return

    st.info(str(destiny_profile["disclaimer"]))
    st.write(
        f"星座：{destiny_profile['western_zodiac']}  |  生肖：{destiny_profile['chinese_zodiac']}  |  年柱：{destiny_profile['ganzhi_year']}  |  月柱：{destiny_profile['ganzhi_month']}"
    )
    st.write(
        f"出生地：纬度 {destiny_profile['latitude']:.4f} / 经度 {destiny_profile['longitude']:.4f} / 时区 {destiny_profile['timezone_name']} (UTC{destiny_profile['timezone_offset']:+g})"
    )
    st.write(
        f"真太阳时：{destiny_profile['true_solar_time']}（经度修正 {destiny_profile['longitude_correction_min']} 分钟，均时差 {destiny_profile['equation_of_time_min']} 分钟，总修正 {destiny_profile['total_correction_min']} 分钟）"
    )
    st.write(
        f"五行主势：{destiny_profile['dominant_element']}  |  待补元素：{destiny_profile['weakest_element']}  |  时辰地支：{destiny_profile['hour_branch']}"
    )
    st.write(f"更适合方位：{destiny_profile['direction']}")
    st.write("更适合行业：" + "、".join(destiny_profile["industries"]))
    st.write(f"紫微主轴提示：{destiny_profile['ziwei_focus']}")

    element_df = pd.DataFrame(
        {
            "五行": list(destiny_profile["elements"].keys()),
            "强度": list(destiny_profile["elements"].values()),
        }
    )
    st.bar_chart(element_df.set_index("五行"))

    st.markdown("#### 大运节奏（十年参考）")
    st.dataframe(pd.DataFrame(destiny_profile["luck_rows"]), hide_index=True, use_container_width=True)


def show_growth_plan() -> None:
    st.subheader("2) 12 周成长计划")
    scores = st.session_state.get("scores")
    if not scores:
        st.info("请先在天赋测评中生成报告。")
        return

    plan = generate_plan(scores)
    st.dataframe(pd.DataFrame(plan), hide_index=True, use_container_width=True)


def show_goal_tracker(user_id: int) -> None:
    st.subheader("3) 目标管理")

    with st.form("add_goal_form", clear_on_submit=True):
        goal_text = st.text_input("新增成长目标", placeholder="例如：本周完成 1 次项目复盘分享")
        dim_label = st.selectbox("关联天赋维度", list(DIMENSIONS.values()))
        submitted = st.form_submit_button("添加目标")

        if submitted and goal_text.strip():
            dim_key = next(key for key, value in DIMENSIONS.items() if value == dim_label)
            add_goal(user_id, goal_text.strip(), dim_key)
            st.success("目标已添加")

    goals_df = get_goals(user_id)
    if goals_df.empty:
        st.caption("还没有目标，先添加一个吧。")
        return

    for _, row in goals_df.iterrows():
        c1, c2 = st.columns([0.85, 0.15])
        with c1:
            st.write(f"[{DIMENSIONS[row['dimension']]}] {row['goal_text']}")
        with c2:
            checked = st.checkbox(
                "完成",
                value=bool(row["completed"]),
                key=f"goal_{int(row['id'])}",
                label_visibility="collapsed",
            )
            if checked != bool(row["completed"]):
                set_goal_status(user_id, int(row["id"]), checked)
                st.rerun()


def show_checkins(user_id: int) -> None:
    st.subheader("4) 每日打卡")

    with st.form("checkin_form", clear_on_submit=True):
        checkin_date = st.date_input("日期", value=datetime.date.today())
        energy_score = st.slider("今日状态分（1-10）", 1, 10, 7)
        note = st.text_area("今日复盘", placeholder="今天做得好的事、遇到的问题、下一步动作")
        submitted = st.form_submit_button("保存打卡")
        if submitted:
            add_checkin(user_id, str(checkin_date), energy_score, note.strip())
            st.success("打卡已保存")

    checkins_df = get_checkins(user_id)
    if checkins_df.empty:
        st.caption("暂无打卡记录。")
        return

    st.dataframe(checkins_df[["checkin_date", "energy_score", "note"]], hide_index=True, use_container_width=True)
    trend_df = checkins_df.sort_values("checkin_date").set_index("checkin_date")[["energy_score"]]
    st.line_chart(trend_df)


def show_coach_chat(user_id: int) -> None:
    st.subheader("5) 教练建议与互动")
    st.caption("先输入补充信息，再和成长教练进行连续对话。")

    supplement = st.text_area(
        "补充信息（可选）",
        placeholder="例如：我在做跨部门项目，最近每周只能投入 4 小时，希望提升表达与推进能力。",
        key=f"supplement_{user_id}",
    )

    messages = get_coach_messages(user_id)
    if not messages:
        opening = "你好，我是你的成长教练。你可以告诉我当前卡点、目标和可投入时间，我会给你可执行建议。"
        add_coach_message(user_id, "assistant", opening)
        messages = get_coach_messages(user_id)

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("输入你当前的问题，例如：我总是拖延，怎么做一周改进？")
    if not user_input:
        return

    add_coach_message(user_id, "user", user_input)
    scores = st.session_state.get("scores") or get_latest_assessment(user_id)
    saved_profile = get_birth_profile(user_id)
    destiny_profile = None
    if saved_profile:
        destiny_profile = calc_destiny_profile(
            datetime.date.fromisoformat(str(saved_profile["birth_date"])),
            int(saved_profile["birth_hour"]),
            int(saved_profile["birth_minute"]),
            float(saved_profile["latitude"]),
            float(saved_profile["longitude"]),
            str(saved_profile["timezone_name"]),
            str(saved_profile["gender"]),
        )
    goals_df = get_goals(user_id)
    checkins_df = get_checkins(user_id)
    reply = generate_coach_reply(user_input, supplement, scores, goals_df, checkins_df, destiny_profile)
    add_coach_message(user_id, "assistant", reply)
    st.rerun()


def main() -> None:
    st.set_page_config(page_title="个人天赋挖掘与成长软件", page_icon="🌱", layout="wide")
    init_db()

    user_id = show_auth_panel()
    if not user_id:
        st.title("个人天赋挖掘与成长软件")
        st.info("请先在左侧登录或注册，再使用测评、计划和教练功能。")
        return

    show_home(st.session_state.get("username", "用户"))
    tabs = st.tabs(["天赋测评", "成长计划", "目标管理", "每日打卡", "教练互动"])

    with tabs[0]:
        show_assessment(user_id)
    with tabs[1]:
        show_growth_plan()
    with tabs[2]:
        show_goal_tracker(user_id)
    with tabs[3]:
        show_checkins(user_id)
    with tabs[4]:
        show_coach_chat(user_id)


if __name__ == "__main__":
    main()
