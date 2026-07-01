"""
🍅 Pomodoro Timer - 桌面番茄钟

一个基于 Python tkinter 的精美桌面番茄钟应用。
遵循番茄工作法：25分钟工作 → 5分钟短休息 → 25分钟工作 → ... → 15分钟长休息
"""

# ============================================================
# 模块导入
# ============================================================
import tkinter as tk              # Python 标准 GUI 库
from tkinter import ttk           # tkinter 的主题组件库（本项目中用于风格参考）
import winsound                   # Windows 系统声音播放库（用于计时结束时的提示音）
import math                       # 数学函数库（本项目用于角度计算，为扩展预留）


# ============================================================
# 配置区 —— 可自由调整的参数
# ============================================================
WORK_MINUTES = 25                  # 每轮工作时长（分钟）
SHORT_BREAK_MINUTES = 5            # 短休息时长（分钟）
LONG_BREAK_MINUTES = 15            # 长休息时长（分钟）
POMODOROS_BEFORE_LONG_BREAK = 4    # 多少个番茄后触发长休息

# ---- 配色方案（灵感来源于色环配色图） ----
# 从参考图片的纯色色环中提取并柔和化，形成一套
# 深色背景 + 高饱和点缀色的现代 UI 配色。
COLOR_BG = "#0b0d17"              # 主背景色 —— 近黑深蓝（色环图的深邃背景）
COLOR_BG_LIGHT = "#131626"        # 浅背景/面板色 —— 深蓝
COLOR_WORK = "#ff2d55"            # 工作模式色 —— 活力红（源自色环纯红 #fe0100 柔和化）
COLOR_BREAK = "#30d158"           # 短休息模式色 —— 清新绿（源自色环纯绿 #01fe00 柔和化）
COLOR_LONG_BREAK = "#00b8ff"      # 长休息模式色 —— 天空蓝（源自色环纯蓝/青）
COLOR_TEXT = "#f5f5f7"            # 主文字色 —— 暖白（接近纯白不刺眼）
COLOR_DIM = "#6b7280"             # 辅助文字色 —— 灰蓝
COLOR_BTN_BG = "#1d2032"          # 按钮背景色 —— 深靛蓝
COLOR_BTN_HOVER = "#2a3050"       # 按钮悬停色 —— 亮靛蓝
COLOR_CIRCLE_BG = "#1e2238"       # 圆环背景色 —— 暗靛蓝
COLOR_STATS_BG = "#131626"        # 统计栏背景色
COLOR_ACCENT = "#ffcc00"          # 强调色 —— 黄色（源自色环纯黄）


# ============================================================
# 核心类：番茄钟计时器
# ============================================================
class PomodoroTimer:
    """番茄钟计时器 —— 管理 UI 创建、计时逻辑、状态切换和通知提醒。"""

    # ==================== 初始化 ====================
    def __init__(self, root):
        """
        初始化番茄钟应用。

        参数:
            root (tk.Tk): tkinter 的主窗口对象
        """
        # ---- 窗口基本设置 ----
        self.root = root
        self.root.title("🍅 番茄钟")                # 窗口标题
        self.root.geometry("420x580")               # 窗口大小（宽 x 高）
        self.root.configure(bg=COLOR_BG)             # 设置背景色
        self.root.resizable(False, False)            # 禁止调整窗口大小
        self.center_window()                         # 将窗口居中显示

        # ---- 计时器状态变量 ----
        # 各模式的总时长（秒）
        self.work_time = WORK_MINUTES * 60                 # 工作时长（秒）
        self.short_break_time = SHORT_BREAK_MINUTES * 60   # 短休息时长（秒）
        self.long_break_time = LONG_BREAK_MINUTES * 60     # 长休息时长（秒）
        self.pomodoros_target = POMODOROS_BEFORE_LONG_BREAK  # 长休息触发阈值

        self.time_left = self.work_time          # 当前剩余时间（秒）
        self.total_time = self.work_time         # 当前模式的总时长（秒，用于计算进度百分比）
        self.mode = "work"                       # 当前模式：work | short_break | long_break
        self.running = False                     # 计时器是否正在运行
        self.pomodoros_completed = 0             # 累计完成的番茄数（生涯总计）
        self.timer_id = None                     # tkinter after() 的任务 ID，用于暂停/取消
        self.current_session_pomodoros = 0       # 本轮长休息周期内完成的番茄数（0~3 时休息都是短休息，到 4 触发长休息）

        # ---- 构建界面 ----
        self.setup_ui()                          # 创建所有 UI 组件
        self.update_display()                    # 刷新显示（时间、颜色、进度等）

    # ==================== 窗口居中 ====================
    def center_window(self):
        """将应用窗口居中显示在屏幕中央。"""
        self.root.update_idletasks()              # 刷新窗口信息，确保宽高已生效
        w, h = 420, 580                           # 窗口宽高
        sw = self.root.winfo_screenwidth()        # 获取屏幕宽度
        sh = self.root.winfo_screenheight()       # 获取屏幕高度
        x = (sw - w) // 2                         # 计算窗口左上角 X 坐标
        y = (sh - h) // 2                         # 计算窗口左上角 Y 坐标
        self.root.geometry(f"{w}x{h}+{x}+{y}")    # 设置窗口位置

    # ==================== UI 构建 ====================
    def setup_ui(self):
        """
        构建应用的用户界面。

        布局结构（从上到下）：
            1. 标题 "🍅 番茄钟"
            2. 模式指示器（工作时间/休息时间）
            3. Canvas 画布（圆形进度条 + 时间文字 + 状态提示）
            4. 阶段小圆点指示器（当前长休息周期的进度）
            5. 按钮区（开始/暂停、重置）
            6. 统计栏（已完成番茄数）
            7. 退出提示
        """
        # ---- 主容器 ----
        main_frame = tk.Frame(self.root, bg=COLOR_BG)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)
        # expand=True   → 当容器有额外空间时自动扩展
        # fill="both"   → 同时在水平和垂直方向填充
        # padx/pady     → 内边距

        # ---- 1. 标题 ----
        self.label_title = tk.Label(
            main_frame,
            text="🍅 番茄钟",                    # 标题文字
            font=("Microsoft YaHei", 22, "bold"), # 字体：微软雅黑，22号，加粗
            bg=COLOR_BG,                         # 背景色与主背景一致
            fg=COLOR_TEXT,                        # 文字颜色：白色
        )
        self.label_title.pack(pady=(0, 2))        # pack() 将组件放入布局；pady 设置上下间距

        # ---- 2. 模式指示器 ----
        self.label_mode = tk.Label(
            main_frame,
            text="⏰ 工作时间",                   # 默认文字
            font=("Microsoft YaHei", 12),
            bg=COLOR_BG,
            fg=COLOR_WORK,                        # 默认用红色（工作模式）
        )
        self.label_mode.pack(pady=(0, 15))

        # ---- 3. 计时器画布（Canvas） ----
        # Canvas 是 tkinter 的绘图画布，可以画圆、弧线、文字等
        self.canvas_size = 280                    # 画布尺寸（正方形）
        self.canvas = tk.Canvas(
            main_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg=COLOR_BG,                          # 背景与主背景融合
            highlightthickness=0,                  # 去掉默认的焦点高亮边框
        )
        self.canvas.pack()

        # 圆心坐标和半径
        cx = cy = self.canvas_size // 2            # 圆心在画布正中央 (140, 140)
        r = 120                                    # 圆的半径

        # ---- 背景圆环 ----
        # create_oval(x1,y1, x2,y2) 画椭圆/圆
        # (cx-r, cy-r) 左上角, (cx+r, cy+r) 右下角 → 刚好外切于半径为 r 的圆
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=COLOR_CIRCLE_BG,               # 边框色：暗紫（几乎不可见的背景环）
            width=8,                                # 边框宽度
        )

        # ---- 进度圆弧 ----
        # create_arc() 画弧形；start=90 表示从 90° 开始（相当于时钟的12点方向）
        # extent=0 表示弧长 0°，随后通过 itemconfig() 动态更新
        self.progress_arc = self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=90,                               # 从顶部开始（12点钟方向）
            extent=0,                                # 弧长（由 update_display() 动态设置）
            outline=COLOR_WORK,                      # 初始使用工作模式颜色
            width=8,
            style="arc",                             # 只画弧线，不画扇形
        )

        # ---- 中央计时文字 ----
        self.timer_text = self.canvas.create_text(
            cx, cy - 10,                            # 文字位置（比正中央略偏上，给状态文字留空间）
            text="25:00",                           # 初始时间
            fill=COLOR_TEXT,
            font=("Microsoft YaHei", 52, "bold"),
        )

        # ---- 状态提示文字 ----
        self.status_text = self.canvas.create_text(
            cx, cy + 45,                            # 位于计时文字下方
            text="点击「开始」启动计时",
            fill=COLOR_DIM,
            font=("Microsoft YaHei", 10),
        )

        # ---- 4. 阶段小圆点指示器 ----
        # 显示当前长休息周期的进度：每完成 1 个番茄点亮 1 个，4 个全亮后进入长休息
        self.session_frame = tk.Frame(main_frame, bg=COLOR_BG)
        self.session_frame.pack(pady=(12, 0))

        self.session_dots = []                      # 存储所有小圆点的 Canvas 对象
        for i in range(self.pomodoros_target):      # 创建 4 个小圆点
            dot = tk.Canvas(
                self.session_frame,
                width=16, height=16,
                bg=COLOR_BG, highlightthickness=0,
            )
            dot.pack(side="left", padx=4)           # 水平排列
            dot.create_oval(2, 2, 14, 14,           # 画圆形（留 2px 边距做描边效果）
                          outline=COLOR_DIM, width=2)
            self.session_dots.append(dot)

        # ---- 5. 按钮区域 ----
        btn_frame = tk.Frame(main_frame, bg=COLOR_BG)
        btn_frame.pack(pady=(18, 0))

        # 开始/暂停按钮（使用自定义方法 make_button 创建）
        self.btn_start = self.make_button(
            btn_frame, "▶  开始", COLOR_WORK,
            self.toggle_timer,                      # 点击事件：切换运行/暂停
            side="left", padx=6,
        )

        # 重置按钮
        self.btn_reset = self.make_button(
            btn_frame, "↻  重置", COLOR_BTN_BG,
            self.reset_timer,                       # 点击事件：重置
            side="left", padx=6,
        )

        # ---- 6. 统计栏 ----
        stats_frame = tk.Frame(main_frame, bg=COLOR_STATS_BG)
        stats_frame.pack(fill="x", pady=(18, 0), ipady=10)  # fill="x" 水平填充，ipady 内边距

        self.stats_label = tk.Label(
            stats_frame,
            text="🍅  已完成 0 个番茄",
            font=("Microsoft YaHei", 10),
            bg=COLOR_STATS_BG,
            fg="#8b8fa3",                            # 浅灰色
        )
        self.stats_label.pack()

        # ---- 7. 退出提示 ----
        tk.Label(
            main_frame,
            text="关闭窗口即可退出",
            font=("Microsoft YaHei", 8),
            bg=COLOR_BG,
            fg="#3d4055",
        ).pack(pady=(10, 0))

        # ---- 窗口关闭事件绑定 ----
        # 当用户点击右上角 X 时，调用 on_closing 方法做清理工作
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ==================== 创建样式按钮 ====================
    def make_button(self, parent, text, color, command, **pack_kw):
        """
        创建一个统一样式的按钮。

        参数:
            parent   — 父容器
            text     — 按钮文字
            color    — 背景色
            command  — 点击回调函数
            **pack_kw — 传递给 pack() 的布局参数
        """
        btn = tk.Button(
            parent,
            text=text,
            font=("Microsoft YaHei", 11, "bold"),
            bg=color,                                # 背景色
            fg=COLOR_TEXT,                            # 文字色
            activebackground=COLOR_BTN_HOVER,         # 鼠标悬停时的背景色
            activeforeground=COLOR_TEXT,               # 鼠标悬停时的文字色
            bd=0,                                      # 去掉边框（扁平风格）
            padx=22,                                   # 左右内边距（按钮宽度）
            pady=8,                                    # 上下内边距（按钮高度）
            cursor="hand2",                            # 鼠标悬停时显示手型
            command=command,                           # 点击回调
        )
        btn.pack(**pack_kw)                            # 按传入的布局参数放置
        return btn

    # ==================== 显示更新 ====================
    def update_display(self):
        """
        刷新所有显示内容，包括：
        - 计时文字（MM:SS 格式）
        - 进度圆弧（动态旋转）
        - 模式文字和配色
        - 番茄统计
        - 阶段小圆点
        - 底部状态提示
        """
        # ---- 格式化剩余时间 ----
        mins = self.time_left // 60                   # 取整得到分钟
        secs = self.time_left % 60                    # 取余得到秒钟
        self.canvas.itemconfig(
            self.timer_text,
            text=f"{mins:02d}:{secs:02d}"             # 格式化为 "25:00" 形式
        )

        # ---- 更新进度圆弧 ----
        # 计算已用时间的比例，转换成弧度
        # ratio = 剩余时间/总时间 → 用于计算圆弧还剩多少
        ratio = self.time_left / self.total_time if self.total_time > 0 else 0
        # 圆弧总长为 360°，减去已消耗的部分（1-ratio）* 360
        # 负号表示逆时针方向旋转（因为 canvas 默认顺时针为正）
        self.canvas.itemconfig(self.progress_arc, extent=-360 * (1 - ratio))

        # ---- 根据模式切换配色和文字 ----
        if self.mode == "work":
            color = COLOR_WORK                        # 工作模式：活力红
            accent_color = COLOR_WORK
            mode_text = "⏰ 工作时间"
        elif self.mode == "short_break":
            color = COLOR_BREAK                       # 短休息：清新绿
            accent_color = COLOR_BREAK
            mode_text = "☕ 休息时间"
        else:
            color = COLOR_LONG_BREAK                  # 长休息：天空蓝
            accent_color = COLOR_LONG_BREAK
            mode_text = "🎉 长休息"
        self.canvas.itemconfig(self.progress_arc, outline=accent_color)

        # 更新模式标签的颜色和文字
        self.label_mode.config(text=mode_text, fg=color)

        # ---- 更新番茄统计 ----
        self.stats_label.config(text=f"🍅  已完成 {self.pomodoros_completed} 个番茄")

        # ---- 更新阶段小圆点 ----
        # 色环配色：4 个小圆点依次为红 → 黄 → 绿 → 蓝
        dot_colors = [COLOR_WORK, COLOR_ACCENT, COLOR_BREAK, COLOR_LONG_BREAK]
        for i, dot in enumerate(self.session_dots):
            dot.delete("all")                          # 清除原有绘制
            if i < self.current_session_pomodoros:
                # 已完成的番茄 → 实心圆（使用对应色环颜色）
                dot.create_oval(2, 2, 14, 14,
                              fill=dot_colors[i], outline=dot_colors[i], width=2)
            else:
                # 未完成的 → 空心圆
                dot.create_oval(2, 2, 14, 14,
                              outline=COLOR_DIM, width=2)

        # ---- 更新底部状态提示文字 ----
        if not self.running and self.time_left > 0:
            # 计时器不在运行状态
            if self.time_left == self.total_time:
                # 时间没被动过 → 显示初始提示
                self.canvas.itemconfig(self.status_text, text="点击「开始」启动计时")
            else:
                # 暂停状态
                self.canvas.itemconfig(self.status_text, text="已暂停")
        elif self.running:
            # 正在运行 → 显示对应的鼓励文字
            status_map = {
                "work": "专注工作 💪",
                "short_break": "休息一下 ☕",
                "long_break": "休息一会儿 🎉",
            }
            self.canvas.itemconfig(self.status_text, text=status_map.get(self.mode, ""))

    # ==================== 计时控制 ====================

    def toggle_timer(self):
        """
        切换计时器的运行/暂停状态。
        如果正在运行则暂停，如果已暂停则继续。
        这是「开始/暂停」按钮的回调函数。
        """
        if self.running:
            self.pause_timer()                        # 运行中 → 暂停
        else:
            self.start_timer()                        # 暂停中 → 开始

    def start_timer(self):
        """启动倒计时。"""
        if self.time_left <= 0:                       # 防止时间已到 0 时误操作
            return
        self.running = True
        self.btn_start.config(text="⏸  暂停")        # 按钮文字切换为「暂停」
        self.tick()                                   # 开始每秒走表

    def pause_timer(self):
        """暂停倒计时。"""
        self.running = False
        if self.timer_id:
            # 取消之前通过 after() 注册的定时任务
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.btn_start.config(text="▶  继续")        # 按钮文字切换为「继续」
        self.update_display()                         # 刷新状态提示

    def reset_timer(self):
        """
        重置计时器。
        - 停止所有计时
        - 切换回工作模式
        - 时间重置为 25:00
        - 清空阶段小圆点
        """
        self.running = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        # 重置为工作模式
        self.mode = "work"
        self.time_left = self.work_time
        self.total_time = self.work_time
        self.current_session_pomodoros = 0             # 清空本轮进度
        self.btn_start.config(text="▶  开始")

        # 重置阶段小圆点（全部变空心）
        for dot in self.session_dots:
            dot.delete("all")
            dot.create_oval(2, 2, 14, 14, outline=COLOR_DIM, width=2)

        self.canvas.itemconfig(self.status_text, text="点击「开始」启动计时")
        self.update_display()

    # ==================== 核心计时逻辑 ====================
    def tick(self):
        """
        核心计时方法 —— 每秒执行一次。

        工作原理：
        tkinter 的 after(ms, callback) 方法可以在指定毫秒后
        执行一个回调函数。这里通过递归调用自身实现精准的每秒倒计时。

        这不是真正的多线程，而是利用 tkinter 事件循环的调度功能。
        """
        if not self.running:                           # 如果已暂停，停止递归
            return

        self.time_left -= 1                            # 减少一秒
        self.update_display()                          # 刷新显示

        if self.time_left <= 0:                        # 时间到！
            self.timer_finished()                      # 处理结束逻辑
            return

        # 在 1000 毫秒（1 秒）后再次调用 tick()
        # 返回的 timer_id 用于后续暂停/重置时取消这个调度
        self.timer_id = self.root.after(1000, self.tick)

    # ==================== 计时结束处理 ====================
    def timer_finished(self):
        """
        当计时器走到 0:00 时的处理逻辑。

        做的事：
        1. 停止运行状态
        2. 播放声音提示
        3. 窗口闪烁吸引注意
        4. 弹出通知
        5. 根据当前模式自动切换到下一阶段
           - 工作结束 → 短休息或长休息（视完成番茄数而定）
           - 休息结束 → 工作
        6. 3 秒后自动开始下一轮
        """
        self.running = False
        self.btn_start.config(text="▶  开始")

        # ---- 视觉反馈：窗口置顶（瞬间闪烁） ----
        self.root.attributes("-topmost", True)          # 窗口置顶
        self.root.after(100, lambda: self.root.attributes("-topmost", False))  # 100ms 后取消

        # ---- 声音和视觉提醒 ----
        self.play_alert()                               # 播放系统提示音
        self.flash_window()                             # 窗口透明度闪烁

        # ---- 根据当前模式切换下一阶段 ----
        if self.mode == "work":
            # 工作结束，记录一个番茄
            self.pomodoros_completed += 1
            self.current_session_pomodoros += 1
            self.show_popup("🎉 工作时间结束！", "该休息一下了～")

            # 判断进入短休息还是长休息
            if self.current_session_pomodoros >= self.pomodoros_target:
                # 已完成 4 个番茄 → 进入长休息
                self.mode = "long_break"
                self.time_left = self.long_break_time
                self.total_time = self.long_break_time
                self.current_session_pomodoros = 0       # 重置本轮计数
            else:
                # 还没到 4 个 → 进入短休息
                self.mode = "short_break"
                self.time_left = self.short_break_time
                self.total_time = self.short_break_time
        else:
            # 休息结束，回到工作模式
            self.show_popup("☕ 休息结束！", "开始下一个番茄吧 💪")
            self.mode = "work"
            self.time_left = self.work_time
            self.total_time = self.work_time

        self.update_display()                            # 立刻刷新显示

        # ---- 自动开始下一轮 ----
        # 3 秒后自动开始（给用户看到提示信息的时间）
        self.root.after(3000, self.auto_start_next)

    def auto_start_next(self):
        """
        计时结束后自动开始下一轮。
        - 仅在没有手动操作、且时间是满的时才启动
        - 防止用户手动暂停后再被自动启动
        """
        if not self.running and self.time_left == self.total_time:
            self.start_timer()

    # ==================== 提醒机制 ====================
    def play_alert(self):
        """
        播放系统提示音。

        使用 winsound.PlaySound() 调用 Windows 的系统声音。
        "SystemExclamation" 是 Windows 预设的系统感叹音。
        SND_ALIAS 表示第一个参数是系统声音的别名。

        用 try/except 包裹以防在无音频设备的环境下报错。
        """
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except Exception:
            pass                                         # 安静地失败，不影响程序运行

    def flash_window(self):
        """
        窗口闪烁效果 —— 通过快速改变窗口透明度实现。

        原理：在 0ms、200ms、400ms 时分别将透明度设为 0.6，
        然后在 100ms、300ms、500ms 时恢复为 1.0。
        总共闪烁 3 次，持续约 0.6 秒。
        """
        for i in range(3):                               # 闪烁 3 次
            delay = i * 200                              # 每次间隔 200ms
            # 变透明（60% 不透明度）
            self.root.after(delay, lambda: self.root.attributes("-alpha", 0.6))
            # 100ms 后恢复（100% 不透明度）
            self.root.after(delay + 100, lambda: self.root.attributes("-alpha", 1.0))

    def show_popup(self, title, message):
        """
        弹出通知窗口。

        优先使用 plyer 库发送系统桌面通知（Windows 右下角弹窗）。
        如果 plyer 不可用（未安装或导入失败），则回退到 tkinter
        的自定义弹窗。

        参数:
            title   — 通知标题
            message — 通知正文
        """
        try:
            # ---- 方案 A：使用 plyer 系统通知 ----
            from plyer import notification as plyer_notify

            plyer_notify.notify(
                title=title,
                message=message,
                app_name="🍅 番茄钟",
                timeout=5,                               # 5 秒后自动消失
            )
        except Exception:
            # ---- 方案 B：回退到 tkinter 弹窗 ----
            try:
                popup = tk.Toplevel(self.root)            # 创建顶级子窗口
                popup.title("🍅 番茄钟")
                popup.geometry("300x150")
                popup.configure(bg=COLOR_BG)
                popup.resizable(False, False)

                # 弹窗位置：相对于主窗口偏移，居中感觉
                px = self.root.winfo_x() + 60
                py = self.root.winfo_y() + 60
                popup.geometry(f"+{px}+{py}")             # 设置弹窗位置

                # 标题
                tk.Label(
                    popup,
                    text=title,
                    font=("Microsoft YaHei", 14, "bold"),
                    bg=COLOR_BG, fg=COLOR_TEXT,
                ).pack(pady=(20, 5))

                # 正文
                tk.Label(
                    popup,
                    text=message,
                    font=("Microsoft YaHei", 11),
                    bg=COLOR_BG, fg="#cccccc",
                ).pack(pady=(0, 15))

                # 确认按钮
                tk.Button(
                    popup,
                    text="知道了",
                    font=("Microsoft YaHei", 10),
                    bg=COLOR_BTN_BG, fg=COLOR_TEXT,
                    activebackground="#2a3050",
                    bd=0, padx=20, pady=5,
                    cursor="hand2",
                    command=popup.destroy,                 # 点击关闭弹窗
                ).pack()

                popup.grab_set()                           # 模态窗口（阻塞主窗口操作）
                # 5 秒后自动关闭弹窗
                self.root.after(5000,
                    lambda: popup.destroy() if popup.winfo_exists() else None)
            except Exception:
                pass                                       # 如果弹窗也失败，放弃提醒

    # ==================== 窗口关闭清理 ====================
    def on_closing(self):
        """
        窗口关闭时的清理方法。

        当用户点击窗口右上角的 X 按钮时调用。
        确保：
        1. 计时器停止运行
        2. 取消所有挂起的 after() 回调
        3. 正确销毁窗口
        """
        self.running = False                               # 停止计时
        if self.timer_id:
            self.root.after_cancel(self.timer_id)          # 取消定时任务
            self.timer_id = None
        self.root.destroy()                                # 销毁窗口，退出程序


# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    """
    Python 程序的入口点。

    __name__ 是 Python 的内置变量：
    - 当文件直接运行时，__name__ == "__main__"
    - 当文件被 import 时，__name__ == "pomodoro"

    这意味着只有直接运行 python pomodoro.py 时才会执行以下代码，
    导入该模块不会自动启动 GUI。
    """
    root = tk.Tk()                      # 创建 tkinter 主窗口
    app = PomodoroTimer(root)           # 创建番茄钟实例
    root.mainloop()                     # 进入 tkinter 事件循环（阻塞，直到窗口关闭）
    # mainloop() 会持续运行，处理用户的鼠标点击、键盘输入等事件，
    # 并驱动 after() 调用的定时任务。窗口关闭后 mainloop() 返回，程序结束。
