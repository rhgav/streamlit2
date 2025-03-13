# Home.py
import sqlite3
import streamlit as st
import pandas as pd
import subprocess
import os


# ----------------- 数据库初始化（用户认证部分） -----------------
def init_db():
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        role TEXT,
                        message TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(chat_id) REFERENCES chats(id)
                    )''')
    cursor.execute('SELECT id FROM users WHERE username = "admin"')
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', 'admin'))
    conn.commit()
    conn.close()


# ----------------- 用户认证功能 -----------------
def register_user(username, password):
    if username.strip().lower() == 'admin':
        st.error("不能注册管理员账号")
        return
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        st.success("注册成功！")
    except sqlite3.IntegrityError:
        st.error("用户名已存在，请选择其他用户名。")
    except Exception as e:
        st.error(f"注册时发生错误: {str(e)}")
    finally:
        conn.close()


def login_user(username, password):
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user:
            if user[2] == password:  # 假设密码在第三列
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]  # 保存用户名
                return user[0]
            else:
                st.error("密码错误，请重试。")
        else:
            st.error("用户名不存在，请检查或注册新用户。")
        return None
    except Exception as e:
        st.error(f"登录时发生错误: {str(e)}")
    finally:
        conn.close()


# ----------------- 游戏展示部分配置 -----------------
# 网页配置信息
PAGE_CONFIG = [
    {
        "thumbnail": "images/Group1.png",
        "exe_path": "Debug/Group4.exe",  # 替换为实际的.exe文件路径
        "description": "Group 1 - 初期调查",
        "author": "解振昊、夏希慈、娄颖卓",
        "intro": "在贵州瓮安，一场悲剧拉开序幕。初二女生李树芬溺水身亡，警察打捞未果，家属质疑死因，要求尸检。第一次尸检认定溺亡，但真相扑朔迷离……"
    },
    {
        "thumbnail": "images/Group2.png",
        "exe_path": "Debug/Group4.exe",  # 替换为实际的.exe文件路径
        "description": "Group 2 - 矛盾激化",
        "author": "李沛然、贾欣雨、胡思睿、陈廷萱",
        "intro": "家属要求二次尸检，警方不予立案。次日警察与家属冲突升级，第二次尸检展开。案件转向民事纠纷，但谣言四起，公安定论后家属拒绝处理尸体，调解彻底失败，局势愈发紧张……"
    },
    {
        "thumbnail": "images/Group3.png",
        "exe_path": "Debug/Group4.exe",  # 替换为实际的.exe文件路径
        "description": "Group 3 - 游行与冲突",
        "author": "宋翊加、王墨涵、冉莫凡、胡诗宇",
        "intro": "民众游行请愿，情绪激化，学生、移民、帮派、家属纷纷加入。公安局遭冲击，冲突升级，大楼被焚烧，局势失控，政府紧急请求支援，现场一片混乱……"
    },
    {
        "thumbnail": "images/Group4.png",
        "exe_path": "Debug/Group4.exe",  # 替换为实际的.exe文件路径
        "description": "Group 4 - 爆发与后果",
        "author": "仇睿铭、廖蔓萁、杜欣宇、李光铖",
        "intro": "局势进一步失控，县委、县政府大楼被焚烧，事态震惊省与中央。上级紧急介入，下达八点批示，要求查明真相、依法处理，全力平息事态，恢复秩序。"
    }
]

# 评分帮助信息
HELP_TEXTS = {
    "游戏性": {
        1: "很不有趣，几乎没有吸引力",
        2: "一般有趣，有一些吸引力",
        3: "比较有趣，有一定吸引力",
        4: "非常有趣，很有吸引力",
        5: "极度有趣，极具吸引力"
    },
    "故事性": {
        1: "故事情节非常不连贯，几乎没有吸引力",
        2: "故事情节有些不连贯，吸引力有限",
        3: "故事情节比较连贯，有一定吸引力",
        4: "故事情节很连贯，很有吸引力",
        5: "故事情节极其连贯，极具吸引力"
    },
    "音效": {
        1: "音效质量非常差，与游戏内容完全不符",
        2: "音效质量较差，与游戏内容有些不符",
        3: "音效质量一般，与游戏内容基本相符",
        4: "音效质量较好，与游戏内容很契合",
        5: "音效质量非常好，与游戏内容完美契合"
    },
    "用户体验": {
        1: "界面极不友好，操作非常复杂",
        2: "界面不够友好，操作比较复杂",
        3: "界面一般，操作比较便捷",
        4: "界面比较友好，操作很便捷",
        5: "界面非常友好，操作极其便捷"
    },
    "学习目标": {
        1: "游戏目标非常不清晰，与学习内容毫无关联",
        2: "游戏目标有些不清晰，与学习内容关联性较弱",
        3: "游戏目标比较清晰，与学习内容有一定关联",
        4: "游戏目标很清晰，与学习内容关联性很强",
        5: "游戏目标极其清晰，与学习内容完美关联"
    },
    "游戏反馈": {
        1: "反馈非常不及时，准确性极低",
        2: "反馈有些不及时，准确性较低",
        3: "反馈比较及时，准确性一般",
        4: "反馈很及时，准确性较高",
        5: "反馈极其及时，准确性非常高"
    },
    "视觉效果": {
        1: "画面非常丑陋，完全没有视觉冲击力",
        2: "画面比较丑陋，视觉冲击力较弱",
        3: "画面一般，视觉冲击力一般",
        4: "画面比较美观，视觉冲击力较强",
        5: "画面非常美观，视觉冲击力极高"
    },
    "交互性": {
        1: "交互性极差，响应非常迟钝",
        2: "交互性较差，响应比较迟钝",
        3: "交互性一般，响应比较及时",
        4: "交互性较好，响应很及时",
        5: "交互性非常好，响应极其及时"
    },
    "背景音乐": {
        1: "音乐氛围非常不适宜，让人不舒服",
        2: "音乐氛围有些不适宜，让人不太舒服",
        3: "音乐氛围一般，比较适宜",
        4: "音乐氛围很好，非常适宜",
        5: "音乐氛围极佳，完美适宜"
    },
    "学习材料": {
        1: "学习材料非常不清晰，与游戏内容毫无相关性",
        2: "学习材料有些不清晰，与游戏内容相关性较弱",
        3: "学习材料比较清晰，与游戏内容有一定相关性",
        4: "学习材料很清晰，与游戏内容相关性很强",
        5: "学习材料极其清晰，与游戏内容完美相关"
    },
    "学习成果": {
        1: "完全没有对学习成果产生任何影响",
        2: "对学习成果的影响非常有限",
        3: "对学习成果有一定影响",
        4: "对学习成果有明显影响",
        5: "对学习成果有极大影响"
    },
    "动机激励": {
        1: "完全不能激发和维持学习动机",
        2: "对学习动机的激发和维持非常有限",
        3: "对学习动机的激发和维持有一定作用",
        4: "对学习动机的激发和维持有明显作用",
        5: "对学习动机的激发和维持有极大作用"
    },
    "目标明确": {
        1: "游戏目标非常不明确，完全没有达成感",
        2: "游戏目标有些不明确，达成感较弱",
        3: "游戏目标比较明确，有一定达成感",
        4: "游戏目标很明确，有很强的达成感",
        5: "游戏目标极其明确，有极强的达成感"
    },
    "玩家参与": {
        1: "玩家几乎不参与，完全没有投入",
        2: "玩家参与度较低，投入感较弱",
        3: "玩家参与度一般，有一定投入",
        4: "玩家参与度较高，有很强的投入",
        5: "玩家参与度极高，有极强的投入"
    },
    "游戏平衡": {
        1: "游戏难度完全没有平衡，非常无趣",
        2: "游戏难度平衡性较差，趣味性较弱",
        3: "游戏难度平衡性一般，趣味性一般",
        4: "游戏难度平衡性较好，趣味性较强",
        5: "游戏难度平衡性非常好，趣味性极高"
    },
    "个人关联": {
        1: "完全不相关，没有任何个人兴趣和知识",
        2: "相关性很低，个人兴趣和知识很少",
        3: "相关性一般，个人兴趣和知识有一些",
        4: "相关性很高，个人兴趣和知识很多",
        5: "完全相关，个人兴趣和知识非常多"
    }
}



# ----------------- 游戏展示数据库 -----------------
def create_db():
    conn = sqlite3.connect("evaluation_data.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_description TEXT,
                    name TEXT,
                    game_play INTEGER,
                    story INTEGER,
                    sound INTEGER,
                    user_experience INTEGER,
                    learning_goal INTEGER,
                    game_feedback INTEGER,
                    visual_effect INTEGER,
                    interactivity INTEGER,
                    background_music INTEGER,
                    learning_material INTEGER,
                    learning_outcome INTEGER,
                    motivation INTEGER,
                    goal_clarity INTEGER,
                    player_participation INTEGER,
                    game_balance INTEGER,
                    personal_relevance INTEGER,
                    free_feedback TEXT)''')  # 新增字段
    conn.commit()
    conn.close()


# ----------------- 游戏展示页面组件 -----------------
def show_main_page():
    """显示缩略图主页面"""
    st.title("游戏展示板")
    for row in range(0, len(PAGE_CONFIG), 2):
        cols = st.columns(2)
        for col in range(2):
            idx = row + col
            if idx < len(PAGE_CONFIG):
                with cols[col]:
                    page = PAGE_CONFIG[idx]
                    st.image(page["thumbnail"], use_container_width=True, caption=page["description"])

                    # 游戏介绍悬浮框（去掉内部图片，初始状态为关闭）
                    with st.expander("游戏介绍", expanded=False):
                        #st.write(f"**作者**：{page['author']}")
                        st.write(f"**描述**：{page['intro']}")

                    # 按钮布局
                    btn_col1, btn_col2 = st.columns([1, 0.4])
                    with btn_col1:
                        if st.button("进入游戏", key=f"enter_{idx}"):
                            st.session_state.current_page = page["exe_path"]
                            st.rerun()
                    with btn_col2:
                        if st.button("填写评价", key=f"eval_{idx}"):
                            st.session_state.evaluation_group = idx
                            st.rerun()


def show_evaluation_page():
    """显示评价页面"""
    st.title("项目评价")
    group_idx = st.session_state.evaluation_group
    group_info = PAGE_CONFIG[group_idx]

    st.header(f"正在评价: {group_info['description']}")

    # 输入姓名
    name = st.text_input("请输入您的姓名", key="name")

    # 评分项目
    categories = [
        ("游戏性", "游戏玩法的趣味性和吸引力"),
        ("故事性", "游戏故事情节的连贯性和吸引力"),
        ("音效", "游戏音效的质量与情境匹配度"),
        ("用户体验", "游戏界面与操作的友好性"),
        ("学习目标", "游戏是否具有明确的学习目标"),
        ("游戏反馈", "游戏反馈的及时性与准确性"),
        ("视觉效果", "游戏画面的美观程度与视觉冲击力"),
        ("交互性", "游戏的交互方式是否流畅"),
        ("背景音乐", "背景音乐与游戏情境的契合度"),
        ("学习材料", "游戏中的学习材料是否清晰明了"),
        ("学习成果", "通过游戏能够达到的学习成果"),
        ("动机激励", "游戏是否能激发学习动机"),
        ("目标明确", "游戏目标是否明确，是否易于达成"),
        ("玩家参与", "玩家在游戏中的参与度"),
        ("游戏平衡", "游戏的难度是否平衡"),
        ("个人关联", "游戏内容与个人知识和兴趣的关联度")
    ]

    ratings = {}
    for category, description in categories:
        help_text = "\n".join([f"{k}: {v}" for k, v in HELP_TEXTS[category].items()])
        rating = st.slider(
            f"{category} - {description}",
            min_value=1, max_value=5, value=3,
            help=help_text,
            key=f"rating_{category}_{group_idx}"
        )
        ratings[category] = rating

        # 新增自由评价输入框
    free_feedback = st.text_area("请输入您的自由评价（选填）",
                                 height=150,
                                 key=f"free_feedback_{group_idx}")

    # 修改后的提交逻辑
    if name and all(ratings.values()) and not st.session_state.submitted:
        submit_button = st.button("提交评价")
        if submit_button:
            conn = sqlite3.connect("evaluation_data.db")
            c = conn.cursor()
            # 修改后的插入语句（添加free_feedback字段）
            c.execute('''INSERT INTO evaluations (
                               project_description, name, game_play, story, sound, user_experience,
                               learning_goal, game_feedback, visual_effect, interactivity, background_music,
                               learning_material, learning_outcome, motivation, goal_clarity, player_participation,
                               game_balance, personal_relevance, free_feedback) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (group_info['description'], name,
                       ratings["游戏性"], ratings["故事性"], ratings["音效"],
                       ratings["用户体验"], ratings["学习目标"], ratings["游戏反馈"], ratings["视觉效果"],
                       ratings["交互性"], ratings["背景音乐"], ratings["学习材料"], ratings["学习成果"],
                       ratings["动机激励"], ratings["目标明确"], ratings["玩家参与"], ratings["游戏平衡"],
                       ratings["个人关联"], free_feedback))  # 新增自由评价参数
            conn.commit()
            conn.close()

            st.session_state.submitted = True
            st.success("评价提交成功！")
    else:
        if st.session_state.submitted:
            st.warning("评价已经提交，无法再次提交。")
        else:
            if not name:
                st.warning("请填写姓名！")
            elif not all(ratings.values()):
                st.warning("请确保所有评分项都已填写！")
            else:
                submit_button = st.button("提交评价", disabled=True)

    # 返回按钮
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("返回主界面"):
            st.session_state.evaluation_group = None
            st.session_state.submitted = False
            st.rerun()


def show_subpage():
    """显示子页面内容"""
    exe_path = st.session_state.current_page
    if exe_path:
        try:
            # 使用绝对路径
            exe_path = os.path.abspath(exe_path)
            subprocess.Popen([exe_path], shell=True)
            st.write("游戏已启动，请查看弹出的窗口。")
        except Exception as e:
            st.error(f"启动游戏时发生错误: {str(e)}")
    if st.button("返回主界面"):
        st.session_state.current_page = None
        st.rerun()


def get_all_users():
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users')
    users = cursor.fetchall()
    conn.close()
    return users


def get_all_evaluations():
    conn = sqlite3.connect('evaluation_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluations')
    evaluations = cursor.fetchall()
    conn.close()
    return evaluations


def show_admin_interface():
    st.title("管理员界面")

    users = get_all_users()
    evaluations = get_all_evaluations()

    tab1, tab2 = st.tabs(["用户信息", "评价信息"])

    with tab1:
        st.subheader("用户列表")
        if users:
            df_users = pd.DataFrame(users, columns=["ID", "用户名"])
            st.dataframe(df_users)
        else:
            st.write("暂无用户数据")

    with tab2:
        st.subheader("评价信息")
        if evaluations:
            columns = ["ID", "项目描述", "姓名", "游戏性", "故事性", "音效", "用户体验",
                       "学习目标", "游戏反馈", "视觉效果", "交互性", "背景音乐", "学习材料",
                       "学习成果", "动机激励", "目标明确", "玩家参与", "游戏平衡", "个人关联", "自由反馈"]
            df_eval = pd.DataFrame(evaluations, columns=columns)
            st.dataframe(df_eval)
        else:
            st.write("暂无评价数据")
# ----------------- 主程序逻辑 -----------------
if __name__ == "__main__":
    # 页面配置
    st.set_page_config(page_title="综合学习平台", layout="wide")
    # 初始化所有数据库
    init_db()
    create_db()
    # 用户认证状态管理
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
        st.session_state.current_page = None
        st.session_state.evaluation_group = None
        st.session_state.submitted = False

    # 用户未登录时显示认证界面
    if not st.session_state.user_id:
        st.title("用户认证")
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        action_type = st.radio("操作类型", ["登录", "注册"])

        if st.button("提交"):
            if action_type == "注册":
                register_user(username, password)
            else:
                user_id = login_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.rerun()
    else:
        # 管理员界面逻辑
        if st.session_state.username == 'admin':
            show_admin_interface()
            if st.button("退出登录"):
                st.session_state.clear()
                st.rerun()
        else:
            # 顶部导航栏
            with st.container():
                # 退出登录按钮
                cols1 = st.columns([1, 1, 1, 1, 1, 1])
                with cols1[5]:
                    if st.button("🚪 退出登陆"):
                        st.session_state.clear()
                        st.rerun()

            # 显示游戏内容
            if st.session_state.current_page:
                show_subpage()
            elif st.session_state.evaluation_group is not None:
                show_evaluation_page()
            else:
                show_main_page()