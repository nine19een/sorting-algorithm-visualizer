from __future__ import annotations

from dataclasses import dataclass, replace
from time import perf_counter
from typing import Callable


@dataclass
class SortStats:
    algorithm_name: str
    comparisons: int = 0
    swaps: int = 0
    writes: int = 0
    elapsed_time: float = 0.0

    @property
    def data_operations(self) -> int:
        return self.swaps + self.writes


@dataclass
class SortStep:
    array: list[int]
    compare_indices: tuple[int, ...] = ()
    write_indices: tuple[int, ...] = ()
    sorted_indices: tuple[int, ...] = ()
    pivot_index: int | None = None
    description: str = ""
    stats: SortStats | None = None


@dataclass(frozen=True)
class AlgorithmInfo:
    name: str
    best: str
    average: str
    worst: str
    space: str
    stable: str
    principle: str


StepEmitter = Callable[[SortStep], None]
SortFunction = Callable[[list[int], StepEmitter | None], SortStats]


ALGORITHM_INFO: dict[str, AlgorithmInfo] = {
    "冒泡排序": AlgorithmInfo(
        name="冒泡排序",
        best="O(n)",
        average="O(n²)",
        worst="O(n²)",
        space="O(1)",
        stable="是",
        principle="相邻元素两两比较并交换，每一轮把当前最大值移动到右侧。",
    ),
    "选择排序": AlgorithmInfo(
        name="选择排序",
        best="O(n²)",
        average="O(n²)",
        worst="O(n²)",
        space="O(1)",
        stable="否",
        principle="每轮从未排序区间选择最小值，放到当前起始位置。",
    ),
    "插入排序": AlgorithmInfo(
        name="插入排序",
        best="O(n)",
        average="O(n²)",
        worst="O(n²)",
        space="O(1)",
        stable="是",
        principle="维护有序前缀，将当前元素插入到合适位置。",
    ),
    "快速排序": AlgorithmInfo(
        name="快速排序",
        best="O(n log n)",
        average="O(n log n)",
        worst="O(n²)",
        space="平均 O(log n)",
        stable="否",
        principle="选择 pivot，将数组划分为左右区间，再递归排序。",
    ),
    "归并排序": AlgorithmInfo(
        name="归并排序",
        best="O(n log n)",
        average="O(n log n)",
        worst="O(n log n)",
        space="O(n)",
        stable="是",
        principle="递归二分数组，再合并两个有序子数组。",
    ),
}


def _copy_stats(stats: SortStats, start: float) -> SortStats:
    return replace(stats, elapsed_time=perf_counter() - start)


def _finish(stats: SortStats, start: float) -> SortStats:
    stats.elapsed_time = perf_counter() - start
    return stats


def _emit(
    emit: StepEmitter | None,
    a: list[int],
    stats: SortStats,
    start: float,
    *,
    cmp: tuple[int, ...] = (),
    wr: tuple[int, ...] = (),
    done: tuple[int, ...] = (),
    pivot: int | None = None,
    text: str = "",
) -> None:
    if emit is None:
        return
    # 动画帧必须复制数组，否则后续原地修改会覆盖旧快照。
    emit(
        SortStep(
            array=a.copy(),
            compare_indices=cmp,
            write_indices=wr,
            sorted_indices=done,
            pivot_index=pivot,
            description=text,
            stats=_copy_stats(stats, start),
        )
    )


def bubble_sort(data: list[int], emit_step: StepEmitter | None = None) -> SortStats:
    stats = SortStats("冒泡排序")
    start = perf_counter()
    n = len(data)
    _emit(emit_step, data, stats, start, text="开始冒泡排序")

    for r in range(n - 1, 0, -1):
        swapped = False
        for i in range(r):
            stats.comparisons += 1
            _emit(
                emit_step,
                data,
                stats,
                start,
                cmp=(i, i + 1),
                done=tuple(range(r + 1, n)),
                text=f"比较 a[{i}]={data[i]} 和 a[{i + 1}]={data[i + 1]}",
            )
            if data[i] > data[i + 1]:
                x, y = data[i], data[i + 1]
                data[i], data[i + 1] = data[i + 1], data[i]
                stats.swaps += 1
                stats.writes += 2
                swapped = True
                _emit(
                    emit_step,
                    data,
                    stats,
                    start,
                    wr=(i, i + 1),
                    done=tuple(range(r + 1, n)),
                    text=f"交换 {x} 和 {y}",
                )
        _emit(
            emit_step,
            data,
            stats,
            start,
            done=tuple(range(r, n)),
            text=f"a[{r}]={data[r]} 已就位",
        )
        if not swapped:
            _emit(emit_step, data, stats, start, done=tuple(range(n)), text="本轮无交换，提前结束")
            break

    _emit(emit_step, data, stats, start, done=tuple(range(n)), text="排序完成")
    return _finish(stats, start)


def selection_sort(data: list[int], emit_step: StepEmitter | None = None) -> SortStats:
    stats = SortStats("选择排序")
    start = perf_counter()
    n = len(data)
    _emit(emit_step, data, stats, start, text="开始选择排序")

    for i in range(n):
        mn = i
        for j in range(i + 1, n):
            stats.comparisons += 1
            _emit(
                emit_step,
                data,
                stats,
                start,
                cmp=(mn, j),
                done=tuple(range(i)),
                text=f"比较 a[{mn}]={data[mn]} 和 a[{j}]={data[j]}",
            )
            if data[j] < data[mn]:
                mn = j
                _emit(
                    emit_step,
                    data,
                    stats,
                    start,
                    cmp=(mn,),
                    done=tuple(range(i)),
                    text=f"当前最小值 a[{mn}]={data[mn]}",
                )
        if mn != i:
            x, y = data[i], data[mn]
            data[i], data[mn] = data[mn], data[i]
            stats.swaps += 1
            stats.writes += 2
            _emit(
                emit_step,
                data,
                stats,
                start,
                wr=(i, mn),
                done=tuple(range(i + 1)),
                text=f"把最小值 {y} 放到 a[{i}]",
            )
        else:
            _emit(
                emit_step,
                data,
                stats,
                start,
                done=tuple(range(i + 1)),
                text=f"a[{i}]={data[i]} 已是最小值",
            )

    _emit(emit_step, data, stats, start, done=tuple(range(n)), text="排序完成")
    return _finish(stats, start)


def insertion_sort(data: list[int], emit_step: StepEmitter | None = None) -> SortStats:
    stats = SortStats("插入排序")
    start = perf_counter()
    n = len(data)
    _emit(emit_step, data, stats, start, text="开始插入排序")

    for i in range(1, n):
        key = data[i]
        j = i - 1
        _emit(
            emit_step,
            data,
            stats,
            start,
            cmp=(i,),
            done=tuple(range(i)),
            text=f"取出 a[{i}]={key}",
        )
        while j >= 0:
            stats.comparisons += 1
            _emit(
                emit_step,
                data,
                stats,
                start,
                cmp=(j,),
                done=tuple(range(i)),
                text=f"比较 a[{j}]={data[j]} 和待插入值 {key}",
            )
            if data[j] <= key:
                break
            data[j + 1] = data[j]
            stats.writes += 1
            _emit(
                emit_step,
                data,
                stats,
                start,
                wr=(j + 1,),
                done=tuple(range(i)),
                text=f"{data[j]} 右移到 a[{j + 1}]",
            )
            j -= 1
        data[j + 1] = key
        stats.writes += 1
        _emit(
            emit_step,
            data,
            stats,
            start,
            wr=(j + 1,),
            done=tuple(range(i + 1)),
            text=f"{key} 插入到 a[{j + 1}]",
        )

    _emit(emit_step, data, stats, start, done=tuple(range(n)), text="排序完成")
    return _finish(stats, start)


def quick_sort(data: list[int], emit_step: StepEmitter | None = None) -> SortStats:
    stats = SortStats("快速排序")
    start = perf_counter()
    n = len(data)
    _emit(emit_step, data, stats, start, text="开始快速排序")

    def swap(i: int, j: int, p: int | None, text: str) -> None:
        if i == j:
            return
        x, y = data[i], data[j]
        data[i], data[j] = data[j], data[i]
        stats.swaps += 1
        stats.writes += 2
        _emit(emit_step, data, stats, start, wr=(i, j), pivot=p, text=f"{text}：{x} <-> {y}")

    def partition(l: int, r: int) -> int:
        # Lomuto partition：data[l..i] 放不大于 pivot 的元素。
        p = data[r]
        i = l - 1
        _emit(
            emit_step,
            data,
            stats,
            start,
            pivot=r,
            text=f"选择 a[{r}]={p} 作为基准元素（pivot）",
        )
        for j in range(l, r):
            stats.comparisons += 1
            _emit(
                emit_step,
                data,
                stats,
                start,
                cmp=(j, r),
                pivot=r,
                text=f"比较 a[{j}]={data[j]} 和基准元素（pivot）{p}",
            )
            if data[j] <= p:
                i += 1
                swap(i, j, r, f"放入左侧 a[{i}]")
        swap(i + 1, r, r, f"基准元素（pivot）归位 a[{i + 1}]")
        _emit(
            emit_step,
            data,
            stats,
            start,
            done=(i + 1,),
            pivot=i + 1,
            text=f"基准元素（pivot）在 a[{i + 1}]",
        )
        return i + 1

    def solve(l: int, r: int) -> None:
        if l >= r:
            if 0 <= l < n:
                _emit(emit_step, data, stats, start, done=(l,), text=f"a[{l}]={data[l]} 已就位")
            return
        p = partition(l, r)
        solve(l, p - 1)
        solve(p + 1, r)

    solve(0, n - 1)
    _emit(emit_step, data, stats, start, done=tuple(range(n)), text="排序完成")
    return _finish(stats, start)


def merge_sort(data: list[int], emit_step: StepEmitter | None = None) -> SortStats:
    stats = SortStats("归并排序")
    start = perf_counter()
    n = len(data)
    _emit(emit_step, data, stats, start, text="开始归并排序")

    def merge(l: int, mid: int, r: int) -> None:
        left = data[l : mid + 1]
        right = data[mid + 1 : r + 1]
        i = j = 0
        k = l
        _emit(emit_step, data, stats, start, cmp=tuple(range(l, r + 1)), text=f"合并 [{l}, {r}]")

        while i < len(left) and j < len(right):
            stats.comparisons += 1
            _emit(
                emit_step,
                data,
                stats,
                start,
                cmp=(l + i, mid + 1 + j),
                text=f"比较左侧值 {left[i]} 和右侧值 {right[j]}",
            )
            if left[i] <= right[j]:
                data[k] = left[i]
                i += 1
            else:
                data[k] = right[j]
                j += 1
            stats.writes += 1
            _emit(emit_step, data, stats, start, wr=(k,), text=f"写入 a[{k}]={data[k]}")
            k += 1

        while i < len(left):
            data[k] = left[i]
            i += 1
            stats.writes += 1
            _emit(emit_step, data, stats, start, wr=(k,), text=f"写入 a[{k}]={data[k]}")
            k += 1

        while j < len(right):
            data[k] = right[j]
            j += 1
            stats.writes += 1
            _emit(emit_step, data, stats, start, wr=(k,), text=f"写入 a[{k}]={data[k]}")
            k += 1

    def solve(l: int, r: int) -> None:
        if l >= r:
            return
        mid = (l + r) // 2
        _emit(emit_step, data, stats, start, cmp=tuple(range(l, r + 1)), text=f"拆分 [{l}, {r}]")
        solve(l, mid)
        solve(mid + 1, r)
        merge(l, mid, r)

    solve(0, n - 1)
    _emit(emit_step, data, stats, start, done=tuple(range(n)), text="排序完成")
    return _finish(stats, start)


ALGORITHMS: dict[str, SortFunction] = {
    "冒泡排序": bubble_sort,
    "选择排序": selection_sort,
    "插入排序": insertion_sort,
    "快速排序": quick_sort,
    "归并排序": merge_sort,
}
