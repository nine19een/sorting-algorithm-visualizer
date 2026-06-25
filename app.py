# 开发说明：
# 1. 程序的功能目标、双页面结构、交互流程、统计内容和配色方案由本人设计。
# 2. Tkinter、Matplotlib 以及桌面程序相关的具体代码由 AI 辅助实现。
# 3. 本人完成了程序运行、功能验收、问题排查和后续调试。
#
# 标注规则：
# - “个人设计”表示该处体现的是本人提出的功能或视觉方案。
# - “AI 辅助实现”表示该处主要涉及本人尚未系统学习的 GUI、绘图或工程语法。

from __future__ import annotations

import random
import statistics
import os
import sys
import tempfile
import time
from typing import Any

# AI 辅助实现：处理部分 Python 环境中的 Tcl/Tk 路径，并设置 Matplotlib 缓存目录。
python_tcl_dir = os.path.join(sys.base_prefix, "tcl")
if os.path.isdir(python_tcl_dir):
    os.environ.setdefault("TCL_LIBRARY", os.path.join(python_tcl_dir, "tcl8.6"))
    os.environ.setdefault("TK_LIBRARY", os.path.join(python_tcl_dir, "tk8.6"))
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "sorting_visualizer_mpl"))

# AI 辅助实现：引入 Tkinter 与 Matplotlib，并把 Matplotlib 图表嵌入桌面窗口。
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import algorithms


# 个人设计：五种颜色分别表示普通、比较、写入、基准元素和已排序状态。
DEFAULT_COLOR = "#4c78a8"
COMPARE_COLOR = "#f58518"
WRITE_COLOR = "#e45756"
PIVOT_COLOR = "#b279a2"
SORTED_COLOR = "#54a24b"

# 个人设计：限制演示和性能测试规模，避免动画步骤或运行时间失控。
DEMO_MAX_LENGTH = 120
PERF_MAX_LENGTH = 5000
PERF_MAX_RUNS = 50


# AI 辅助实现：配置中文字体和负号显示。
def configure_matplotlib() -> None:
    matplotlib.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False


# 个人设计：耗时根据大小显示为微秒或毫秒；格式转换由 AI 辅助实现。
def format_elapsed(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.2f} 微秒"
    return f"{seconds * 1000:.2f} 毫秒"


# AI 辅助实现：统一处理输入框中的整数转换和错误信息。
def parse_int(value: str, label: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{label}必须是整数。") from exc


# AI 辅助实现：根据用户输入生成随机数组。
def make_random_array(length: int, min_value: int, max_value: int) -> list[int]:
    return [random.randint(min_value, max_value) for _ in range(length)]


# AI 辅助实现：使用一个主应用类管理窗口、状态、动画和图表。
class SortVisualizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("经典排序算法可视化演示系统")
        self.root.geometry("1200x760")
        self.root.minsize(980, 620)

        self.algorithm_names = list(algorithms.ALGORITHMS.keys())

        self.array: list[int] = []
        self.original_array: list[int] = []
        self.steps: list[algorithms.SortStep] = []
        self.step_index = 0
        self.animation_job: str | None = None
        self.is_sorting = False
        self.is_paused = False

        self.test_data: list[int] | None = None
        self.test_params: tuple[int, int, int] | None = None

        self._build_ui()
        self.generate_demo_array()

    # 个人设计：程序分为“排序演示”和“性能对比”两个页面。
    # AI 辅助实现：使用 Tkinter 标签页搭建具体界面。
    def _build_ui(self) -> None:
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.demo_frame = ttk.Frame(self.notebook, padding=8)
        self.perf_frame = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.demo_frame, text="排序演示")
        self.notebook.add(self.perf_frame, text="性能对比")

        self._build_demo_page()
        self._build_perf_page()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # 个人设计：演示页采用左侧控制与信息、右侧排序柱状图的布局。
    # AI 辅助实现：创建控件、绑定事件并嵌入 Matplotlib 图表。
    def _build_demo_page(self) -> None:
        self.demo_frame.columnconfigure(0, weight=0)
        self.demo_frame.columnconfigure(1, weight=1)
        self.demo_frame.rowconfigure(0, weight=1)

        left = self._scrollable_left_panel(self.demo_frame, width=390)

        right = ttk.Frame(self.demo_frame)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        params = ttk.LabelFrame(left, text="排序参数", padding=10)
        params.pack(fill=tk.X, pady=(0, 8))

        self.algorithm_var = tk.StringVar(value=self.algorithm_names[0])
        self.length_var = tk.StringVar(value="50")
        self.min_var = tk.StringVar(value="1")
        self.max_var = tk.StringVar(value="100")
        self.speed_var = tk.IntVar(value=60)

        self._labeled_widget(
            params,
            "排序算法",
            ttk.Combobox(
                params,
                textvariable=self.algorithm_var,
                values=self.algorithm_names,
                state="readonly",
            ),
        )
        self.algorithm_var.trace_add("write", lambda *_: self.update_algorithm_info())
        self._labeled_widget(params, "数组长度", ttk.Entry(params, textvariable=self.length_var))
        self._labeled_widget(params, "随机数最小值", ttk.Entry(params, textvariable=self.min_var))
        self._labeled_widget(params, "随机数最大值", ttk.Entry(params, textvariable=self.max_var))

        speed_row = ttk.Frame(params)
        speed_row.pack(fill=tk.X, pady=4)
        ttk.Label(speed_row, text="动画播放速度").pack(anchor=tk.W)
        speed_scale = ttk.Scale(
            speed_row,
            from_=1,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
        )
        speed_scale.pack(fill=tk.X)

        buttons = ttk.LabelFrame(left, text="操作", padding=10)
        buttons.pack(fill=tk.X, pady=(0, 8))
        self.generate_button = ttk.Button(buttons, text="生成随机数组", command=self.generate_demo_array)
        self.start_button = ttk.Button(buttons, text="开始排序", command=self.start_sorting)
        self.pause_button = ttk.Button(buttons, text="暂停 / 继续", command=self.toggle_pause)
        self.reset_button = ttk.Button(buttons, text="重置", command=self.reset_demo)
        for button in (self.generate_button, self.start_button, self.pause_button, self.reset_button):
            button.pack(fill=tk.X, pady=3)

        stats = ttk.LabelFrame(left, text="当前统计", padding=10)
        stats.pack(fill=tk.X, pady=(0, 8))
        self.stats_vars = {
            "comparisons": tk.StringVar(value="0"),
            "swaps": tk.StringVar(value="0"),
            "writes": tk.StringVar(value="0"),
            "elapsed": tk.StringVar(value="0.00 微秒"),
        }
        self._info_line(stats, "比较次数", self.stats_vars["comparisons"])
        self._info_line(stats, "交换次数", self.stats_vars["swaps"])
        self._info_line(stats, "写入/移动", self.stats_vars["writes"])
        self._info_line(stats, "执行耗时", self.stats_vars["elapsed"])

        self.step_text = tk.StringVar(value="已生成随机数组")
        ttk.Label(left, textvariable=self.step_text, wraplength=285, foreground="#333333").pack(
            fill=tk.X, pady=(0, 8)
        )

        legend = ttk.LabelFrame(left, text="颜色图例", padding=10)
        legend.pack(fill=tk.X, pady=(0, 8))
        for text, color in (
            ("普通元素", DEFAULT_COLOR),
            ("正在比较", COMPARE_COLOR),
            ("交换或写入", WRITE_COLOR),
            ("快速排序基准元素", PIVOT_COLOR),
            ("已经完成排序", SORTED_COLOR),
        ):
            self._legend_line(legend, text, color)

        info = ttk.LabelFrame(left, text="算法信息", padding=10)
        info.pack(fill=tk.BOTH, expand=True)
        self.info_vars = {
            "best": tk.StringVar(),
            "average": tk.StringVar(),
            "worst": tk.StringVar(),
            "space": tk.StringVar(),
            "stable": tk.StringVar(),
            "principle": tk.StringVar(),
        }
        self._info_line(info, "最好时间复杂度", self.info_vars["best"])
        self._info_line(info, "平均时间复杂度", self.info_vars["average"])
        self._info_line(info, "最坏时间复杂度", self.info_vars["worst"])
        self._info_line(info, "空间复杂度", self.info_vars["space"])
        self._info_line(info, "是否稳定", self.info_vars["stable"])
        ttk.Label(info, text="算法原理").pack(anchor=tk.W, pady=(8, 2))
        ttk.Label(info, textvariable=self.info_vars["principle"], wraplength=285).pack(fill=tk.X)

        self.demo_fig = Figure(figsize=(7, 5), dpi=100)
        self.demo_ax = self.demo_fig.add_subplot(111)
        self.demo_canvas = FigureCanvasTkAgg(self.demo_fig, master=right)
        self.demo_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.update_algorithm_info()

    # 个人设计：性能页显示参数、结果表格、耗时图和操作次数对比图。
    # AI 辅助实现：搭建表格与两张 Matplotlib 图表。
    def _build_perf_page(self) -> None:
        self.perf_frame.columnconfigure(0, weight=0)
        self.perf_frame.columnconfigure(1, weight=1)
        self.perf_frame.rowconfigure(0, weight=1)

        left = self._scrollable_left_panel(self.perf_frame, width=400)

        right = ttk.Frame(self.perf_frame)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        params = ttk.LabelFrame(left, text="性能测试参数", padding=10)
        params.pack(fill=tk.X, pady=(0, 8))

        self.perf_length_var = tk.StringVar(value="200")
        self.perf_min_var = tk.StringVar(value="1")
        self.perf_max_var = tk.StringVar(value="1000")
        self.perf_runs_var = tk.StringVar(value="3")

        self._labeled_widget(params, "测试数组长度", ttk.Entry(params, textvariable=self.perf_length_var))
        self._labeled_widget(params, "随机数最小值", ttk.Entry(params, textvariable=self.perf_min_var))
        self._labeled_widget(params, "随机数最大值", ttk.Entry(params, textvariable=self.perf_max_var))
        self._labeled_widget(params, "重复运行次数", ttk.Entry(params, textvariable=self.perf_runs_var))

        self.regen_perf_button = ttk.Button(params, text="重新生成测试数据", command=self.generate_perf_data)
        self.run_perf_button = ttk.Button(params, text="运行性能对比", command=self.run_performance_test)
        self.regen_perf_button.pack(fill=tk.X, pady=(8, 3))
        self.run_perf_button.pack(fill=tk.X, pady=3)

        table_frame = ttk.LabelFrame(left, text="测试结果", padding=8)
        table_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("algorithm", "elapsed", "comparisons", "swaps", "writes")
        self.result_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        headings = {
            "algorithm": "算法",
            "elapsed": "平均耗时",
            "comparisons": "比较次数",
            "swaps": "交换次数",
            "writes": "写入次数",
        }
        widths = {
            "algorithm": 74,
            "elapsed": 88,
            "comparisons": 72,
            "swaps": 68,
            "writes": 68,
        }
        for col in columns:
            self.result_table.heading(col, text=headings[col])
            self.result_table.column(col, width=widths[col], anchor=tk.CENTER, stretch=False)
        self.result_table.pack(fill=tk.BOTH, expand=True)

        self.perf_status = tk.StringVar(value="尚未运行性能测试")
        ttk.Label(left, textvariable=self.perf_status, wraplength=330).pack(fill=tk.X, pady=(8, 0))

        self.perf_fig = Figure(figsize=(8, 6), dpi=100)
        self.time_ax = self.perf_fig.add_subplot(211)
        self.ops_ax = self.perf_fig.add_subplot(212)
        self.perf_fig.tight_layout(pad=3.0)
        self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, master=right)
        self.perf_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.draw_empty_perf_charts()

    # AI 辅助实现：左侧内容过多时提供滚动区域和鼠标滚轮支持。
    def _scrollable_left_panel(self, parent: ttk.Frame, width: int) -> ttk.Frame:
        container = ttk.Frame(parent, width=width)
        container.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        container.grid_propagate(False)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, width=width - 18, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        content = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def update_scroll_region(_event: tk.Event) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def match_canvas_width(event: tk.Event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        def on_mousewheel(event: tk.Event) -> None:
            if event.delta:
                canvas.yview_scroll(int(-event.delta / 120), "units")

        content.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", match_canvas_width)
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))

        return content

    # AI 辅助实现：复用常见的“标签 + 输入控件”布局。
    def _labeled_widget(self, parent: ttk.Frame, label: str, widget: ttk.Widget) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=4)
        ttk.Label(row, text=label).pack(anchor=tk.W)
        widget.pack(fill=tk.X)

    # AI 辅助实现：复用统计信息和算法信息的行布局。
    def _info_line(self, parent: ttk.Frame, label: str, variable: tk.StringVar) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=f"{label}：", width=14).pack(side=tk.LEFT)
        ttk.Label(row, textvariable=variable).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 个人设计：左侧图例解释本人确定的五种状态颜色。
    # AI 辅助实现：创建颜色块和对应文字。
    def _legend_line(self, parent: ttk.Frame, label: str, color: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        swatch = tk.Frame(row, width=18, height=14, background=color)
        swatch.pack(side=tk.LEFT, padx=(0, 8))
        swatch.pack_propagate(False)
        ttk.Label(row, text=label).pack(side=tk.LEFT)

    # 个人设计：限制演示数组规模，并对输入错误给出中文提示。
    # AI 辅助实现：完成具体校验逻辑。
    def validate_demo_inputs(self) -> tuple[int, int, int]:
        length = parse_int(self.length_var.get(), "数组长度")
        min_value = parse_int(self.min_var.get(), "随机数最小值")
        max_value = parse_int(self.max_var.get(), "随机数最大值")
        if length <= 0:
            raise ValueError("数组长度必须是正整数。")
        if length > DEMO_MAX_LENGTH:
            raise ValueError(f"演示数组长度不能超过 {DEMO_MAX_LENGTH}，否则动画步骤过多。")
        if min_value > max_value:
            raise ValueError("随机数最小值不能大于最大值。")
        return length, min_value, max_value

    # 个人设计：性能测试允许更大规模，同时限制过大的重复次数。
    # AI 辅助实现：完成具体校验逻辑。
    def validate_perf_inputs(self) -> tuple[int, int, int, int]:
        length = parse_int(self.perf_length_var.get(), "测试数组长度")
        min_value = parse_int(self.perf_min_var.get(), "随机数最小值")
        max_value = parse_int(self.perf_max_var.get(), "随机数最大值")
        runs = parse_int(self.perf_runs_var.get(), "重复运行次数")
        if length <= 0:
            raise ValueError("测试数组长度必须是正整数。")
        if length > PERF_MAX_LENGTH:
            raise ValueError(f"测试数组长度不能超过 {PERF_MAX_LENGTH}。")
        if min_value > max_value:
            raise ValueError("随机数最小值不能大于最大值。")
        if runs <= 0:
            raise ValueError("重复运行次数必须是正整数。")
        if runs > PERF_MAX_RUNS:
            raise ValueError(f"重复运行次数不能超过 {PERF_MAX_RUNS}。")
        return length, min_value, max_value, runs

    def show_input_error(self, message: str) -> None:
        messagebox.showerror("输入错误", message)

    def cancel_animation(self) -> None:
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None

    # 个人设计：重新生成数组时同步清空动画与统计状态。
    # AI 辅助实现：完成状态重置和图表刷新。
    def generate_demo_array(self) -> None:
        try:
            length, min_value, max_value = self.validate_demo_inputs()
        except ValueError as exc:
            self.show_input_error(str(exc))
            return

        self.cancel_animation()
        self.array = make_random_array(length, min_value, max_value)
        self.original_array = self.array.copy()
        self.steps = []
        self.step_index = 0
        self.is_sorting = False
        self.is_paused = False
        self.start_button.config(state=tk.NORMAL)
        self.step_text.set("已生成随机数组")
        self.clear_stats()
        self.draw_demo_array(self.array)

    # 个人设计：直接复用 algorithms.py 的算法和 SortStep，不在界面中重复实现排序。
    # AI 辅助实现：收集动画步骤并启动播放。
    def start_sorting(self) -> None:
        if self.is_sorting:
            return
        if not self.array:
            self.generate_demo_array()
            if not self.array:
                return

        algorithm_name = self.algorithm_var.get()
        sort_func = algorithms.ALGORITHMS[algorithm_name]
        self.original_array = self.array.copy()
        self.steps = []
        working = self.array.copy()

        try:
            sort_func(working, self.steps.append)
        except Exception as exc:
            messagebox.showerror("排序错误", f"排序过程中发生错误：{exc}")
            return

        if not self.steps:
            self.array = working
            self.draw_demo_array(self.array)
            return

        self.step_index = 0
        self.is_sorting = True
        self.is_paused = False
        self.start_button.config(state=tk.DISABLED)
        self.play_next_step()

    # AI 辅助实现：使用 Tkinter 定时任务逐帧播放，避免阻塞桌面界面。
    def play_next_step(self) -> None:
        self.animation_job = None
        if not self.is_sorting or self.is_paused:
            return
        if self.step_index >= len(self.steps):
            self.finish_animation()
            return

        step = self.steps[self.step_index]
        self.apply_step(step)
        self.step_index += 1
        self.animation_job = self.root.after(self.animation_delay(), self.play_next_step)

    # 个人设计：速度滑块控制动画快慢；数值换算由 AI 辅助实现。
    def animation_delay(self) -> int:
        speed = max(1, min(100, int(self.speed_var.get())))
        return max(10, int(520 - speed * 5))

    # AI 辅助实现：把 SortStep 中的数组、颜色状态、文字和统计同步到界面。
    def apply_step(self, step: algorithms.SortStep) -> None:
        self.array = step.array.copy()
        self.draw_demo_array(
            step.array,
            compare_indices=step.compare_indices,
            write_indices=step.write_indices,
            sorted_indices=step.sorted_indices,
            pivot_index=step.pivot_index,
        )
        self.step_text.set(step.description or "排序进行中")
        if step.stats is not None:
            self.update_stats(step.stats)

    # AI 辅助实现：动画结束后恢复状态，并将全部元素显示为已排序。
    def finish_animation(self) -> None:
        self.is_sorting = False
        self.is_paused = False
        self.start_button.config(state=tk.NORMAL)
        self.animation_job = None
        if self.array:
            self.draw_demo_array(self.array, sorted_indices=tuple(range(len(self.array))))

    # 个人设计：动画支持暂停后从当前步骤继续。
    # AI 辅助实现：维护暂停状态和定时任务。
    def toggle_pause(self) -> None:
        if not self.is_sorting:
            return
        self.is_paused = not self.is_paused
        if not self.is_paused:
            self.play_next_step()

    # 个人设计：重置后恢复到本次排序开始前的数组。
    # AI 辅助实现：取消动画并恢复所有界面状态。
    def reset_demo(self) -> None:
        self.cancel_animation()
        self.array = self.original_array.copy()
        self.steps = []
        self.step_index = 0
        self.is_sorting = False
        self.is_paused = False
        self.start_button.config(state=tk.NORMAL)
        self.step_text.set("已重置为本次排序开始前的数组")
        self.clear_stats()
        self.draw_demo_array(self.array)

    def clear_stats(self) -> None:
        self.stats_vars["comparisons"].set("0")
        self.stats_vars["swaps"].set("0")
        self.stats_vars["writes"].set("0")
        self.stats_vars["elapsed"].set("0.00 微秒")

    def update_stats(self, stats: algorithms.SortStats) -> None:
        self.stats_vars["comparisons"].set(str(stats.comparisons))
        self.stats_vars["swaps"].set(str(stats.swaps))
        self.stats_vars["writes"].set(str(stats.writes))
        self.stats_vars["elapsed"].set(format_elapsed(stats.elapsed_time))

    # 个人设计：柱高表示数值，颜色表示当前排序状态。
    # AI 辅助实现：使用 Matplotlib 绘制并刷新柱状图。
    def draw_demo_array(
        self,
        data: list[int],
        *,
        compare_indices: tuple[int, ...] = (),
        write_indices: tuple[int, ...] = (),
        sorted_indices: tuple[int, ...] = (),
        pivot_index: int | None = None,
    ) -> None:
        self.demo_ax.clear()
        colors = self.colors_for_step(len(data), compare_indices, write_indices, sorted_indices, pivot_index)
        indices = list(range(len(data)))
        self.demo_ax.bar(indices, data, color=colors, width=0.82)
        self.demo_ax.set_title(f"{self.algorithm_var.get()}排序过程")
        self.demo_ax.set_xlabel("索引")
        self.demo_ax.set_ylabel("数值")
        self.demo_ax.grid(axis="y", linestyle="--", alpha=0.25)
        self.apply_axis_limits(self.demo_ax, data)
        self.demo_fig.tight_layout()
        self.demo_canvas.draw_idle()

    # 个人设计：颜色覆盖顺序为已排序、比较、写入、基准元素，基准元素优先级最高。
    # AI 辅助实现：根据 SortStep 的下标信息生成颜色列表。
    def colors_for_step(
        self,
        length: int,
        compare_indices: tuple[int, ...],
        write_indices: tuple[int, ...],
        sorted_indices: tuple[int, ...],
        pivot_index: int | None,
    ) -> list[str]:
        colors = [DEFAULT_COLOR] * length
        for index in sorted_indices:
            if 0 <= index < length:
                colors[index] = SORTED_COLOR
        for index in compare_indices:
            if 0 <= index < length:
                colors[index] = COMPARE_COLOR
        for index in write_indices:
            if 0 <= index < length:
                colors[index] = WRITE_COLOR
        if pivot_index is not None and 0 <= pivot_index < length:
            colors[pivot_index] = PIVOT_COLOR
        return colors

    # AI 辅助实现：自动调整坐标范围，兼容负数和所有元素相同的情况。
    def apply_axis_limits(self, axis: Any, data: list[int]) -> None:
        if not data:
            axis.set_xlim(-0.5, 0.5)
            axis.set_ylim(0, 1)
            return

        min_value = min(data)
        max_value = max(data)
        low = min(0, min_value)
        high = max(0, max_value)
        if low == high:
            margin = max(abs(low) * 0.2, 1)
            low -= margin
            high += margin
        else:
            margin = (high - low) * 0.12
            low -= margin
            high += margin
        axis.set_xlim(-0.6, len(data) - 0.4)
        axis.set_ylim(low, high)

    # 个人设计：算法复杂度和原理直接读取 algorithms.py，避免重复维护。
    # AI 辅助实现：把数据绑定到界面并刷新图表标题。
    def update_algorithm_info(self) -> None:
        name = self.algorithm_var.get()
        info = algorithms.ALGORITHM_INFO.get(name)
        if info is None:
            return
        self.info_vars["best"].set(info.best)
        self.info_vars["average"].set(info.average)
        self.info_vars["worst"].set(info.worst)
        self.info_vars["space"].set(info.space)
        self.info_vars["stable"].set(info.stable)
        self.info_vars["principle"].set(info.principle)
        if self.array:
            self.draw_demo_array(self.array)

    # 个人设计：用户可以单独重新生成性能测试数据。
    # AI 辅助实现：保存数据及其对应参数。
    def generate_perf_data(self) -> None:
        try:
            length, min_value, max_value, _runs = self.validate_perf_inputs()
        except ValueError as exc:
            self.show_input_error(str(exc))
            return
        self.test_data = make_random_array(length, min_value, max_value)
        self.test_params = (length, min_value, max_value)
        self.perf_status.set("已重新生成测试数据")

    # AI 辅助实现：参数变化时自动更新测试数据，并始终返回副本。
    def ensure_perf_data(self, length: int, min_value: int, max_value: int) -> list[int]:
        params = (length, min_value, max_value)
        if self.test_data is None or self.test_params != params:
            self.test_data = make_random_array(length, min_value, max_value)
            self.test_params = params
        return self.test_data.copy()

    # 个人设计：五种算法使用同一份原始数据的副本，并比较平均耗时和操作次数。
    # AI 辅助实现：完成重复运行、平均值计算和按钮状态管理。
    def run_performance_test(self) -> None:
        try:
            length, min_value, max_value, runs = self.validate_perf_inputs()
        except ValueError as exc:
            self.show_input_error(str(exc))
            return

        base_data = self.ensure_perf_data(length, min_value, max_value)
        self.run_perf_button.config(state=tk.DISABLED)
        self.regen_perf_button.config(state=tk.DISABLED)
        self.perf_status.set("性能测试运行中，请稍候...")
        self.root.update_idletasks()

        results = []
        try:
            for name, sort_func in algorithms.ALGORITHMS.items():
                elapsed_values: list[float] = []
                comparisons: list[int] = []
                swaps: list[int] = []
                writes: list[int] = []
                for _ in range(runs):
                    data = base_data.copy()
                    start = time.perf_counter()
                    stats = sort_func(data, None)
                    elapsed = stats.elapsed_time or (time.perf_counter() - start)
                    elapsed_values.append(elapsed)
                    comparisons.append(stats.comparisons)
                    swaps.append(stats.swaps)
                    writes.append(stats.writes)
                results.append(
                    {
                        "name": name,
                        "elapsed": statistics.fmean(elapsed_values),
                        "comparisons": statistics.fmean(comparisons),
                        "swaps": statistics.fmean(swaps),
                        "writes": statistics.fmean(writes),
                    }
                )
        finally:
            self.run_perf_button.config(state=tk.NORMAL)
            self.regen_perf_button.config(state=tk.NORMAL)

        self.populate_result_table(results)
        self.draw_perf_charts(results)
        self.perf_status.set(f"已完成：长度 {length}，重复 {runs} 次，所有算法使用同一份原始数据副本。")

    # AI 辅助实现：把性能结果写入 Tkinter 表格。
    def populate_result_table(self, results: list[dict[str, float | str]]) -> None:
        for row in self.result_table.get_children():
            self.result_table.delete(row)
        for item in results:
            self.result_table.insert(
                "",
                tk.END,
                values=(
                    item["name"],
                    format_elapsed(float(item["elapsed"])),
                    f"{float(item['comparisons']):.0f}",
                    f"{float(item['swaps']):.0f}",
                    f"{float(item['writes']):.0f}",
                ),
            )

    # AI 辅助实现：性能测试尚未运行时显示占位图。
    def draw_empty_perf_charts(self) -> None:
        self.time_ax.clear()
        self.ops_ax.clear()
        self.time_ax.set_title("平均执行耗时")
        self.ops_ax.set_title("操作次数对比")
        self.time_ax.text(0.5, 0.5, "运行性能对比后显示图表", ha="center", va="center")
        self.ops_ax.text(0.5, 0.5, "运行性能对比后显示图表", ha="center", va="center")
        self.perf_fig.tight_layout(pad=3.0)
        self.perf_canvas.draw_idle()

    # 个人设计：上图比较平均耗时，下图比较比较、交换和写入次数。
    # AI 辅助实现：使用 Matplotlib 绘制两组性能图。
    def draw_perf_charts(self, results: list[dict[str, float | str]]) -> None:
        names = [str(item["name"]) for item in results]
        elapsed_ms = [float(item["elapsed"]) * 1000 for item in results]
        comparisons = [float(item["comparisons"]) for item in results]
        swaps = [float(item["swaps"]) for item in results]
        writes = [float(item["writes"]) for item in results]
        positions = list(range(len(names)))

        self.time_ax.clear()
        self.ops_ax.clear()

        self.time_ax.bar(positions, elapsed_ms, color=DEFAULT_COLOR)
        self.time_ax.set_title("五种算法平均执行耗时")
        self.time_ax.set_ylabel("平均耗时（毫秒）")
        self.time_ax.set_xticks(positions, names)
        self.time_ax.grid(axis="y", linestyle="--", alpha=0.25)

        width = 0.25
        self.ops_ax.bar([x - width for x in positions], comparisons, width=width, label="比较次数", color=COMPARE_COLOR)
        self.ops_ax.bar(positions, swaps, width=width, label="交换次数", color=WRITE_COLOR)
        self.ops_ax.bar([x + width for x in positions], writes, width=width, label="写入次数", color=SORTED_COLOR)
        self.ops_ax.set_title("比较、交换、写入次数对比")
        self.ops_ax.set_ylabel("平均操作次数")
        self.ops_ax.set_xticks(positions, names)
        self.ops_ax.grid(axis="y", linestyle="--", alpha=0.25)
        self.ops_ax.legend()

        self.perf_fig.tight_layout(pad=3.0)
        self.perf_canvas.draw_idle()

    # AI 辅助实现：关闭窗口前取消动画并结束 Tkinter 主循环。
    def on_close(self) -> None:
        self.cancel_animation()
        self.root.quit()
        self.root.destroy()


# AI 辅助实现：创建窗口、初始化应用并进入 Tkinter 事件循环。
def main() -> None:
    configure_matplotlib()
    root = tk.Tk()
    SortVisualizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
