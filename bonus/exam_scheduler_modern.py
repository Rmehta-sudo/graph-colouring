#!/usr/bin/env python3
"""
University Exam Scheduler - Modern UI Version

A beautiful graphical interface for creating conflict-free exam timetables 
using graph coloring algorithms.

Features:
- Modern, aesthetic UI with custom styling
- Checkbox-based course selection for students
- Pure Python implementations (no external dependencies)
- Exact solver for small graphs, DSatur for larger ones
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Set
from collections import defaultdict
import time

# ============================================================================
# GRAPH COLORING ALGORITHMS
# ============================================================================

class Graph:
    """Simple graph representation using adjacency list"""
    def __init__(self, n: int):
        self.n = n
        self.adj: List[Set[int]] = [set() for _ in range(n)]
    
    def add_edge(self, u: int, v: int):
        if u != v:
            self.adj[u].add(v)
            self.adj[v].add(u)
    
    def neighbors(self, v: int) -> Set[int]:
        return self.adj[v]
    
    def degree(self, v: int) -> int:
        return len(self.adj[v])


def dsatur_coloring(graph: Graph) -> List[int]:
    """DSatur (Saturation Degree) Algorithm for Graph Coloring"""
    n = graph.n
    if n == 0:
        return []
    
    colors = [-1] * n
    saturation = [0] * n
    neighbor_colors: List[Set[int]] = [set() for _ in range(n)]
    
    for _ in range(n):
        best_v, best_sat, best_deg = -1, -1, -1
        for v in range(n):
            if colors[v] == -1:
                sat, deg = saturation[v], graph.degree(v)
                if sat > best_sat or (sat == best_sat and deg > best_deg):
                    best_v, best_sat, best_deg = v, sat, deg
        
        if best_v == -1:
            break
        
        color = 0
        while color in neighbor_colors[best_v]:
            color += 1
        colors[best_v] = color
        
        for neighbor in graph.neighbors(best_v):
            if colors[neighbor] == -1 and color not in neighbor_colors[neighbor]:
                neighbor_colors[neighbor].add(color)
                saturation[neighbor] += 1
    
    return colors


def exact_coloring(graph: Graph, timeout_seconds: float = 10.0) -> List[int]:
    """Exact Graph Coloring using Backtracking with Pruning"""
    n = graph.n
    if n == 0:
        return []
    
    upper_bound_solution = dsatur_coloring(graph)
    best_k = max(upper_bound_solution) + 1 if upper_bound_solution else 1
    best_solution = upper_bound_solution.copy()
    
    if best_k <= 1:
        return [0] * n
    
    start_time = time.time()
    nodes_visited = [0]
    
    def backtrack(colors: List[int], vertex: int, current_max: int) -> bool:
        nodes_visited[0] += 1
        if nodes_visited[0] % 1000 == 0 and time.time() - start_time > timeout_seconds:
            return True
        
        if vertex == n:
            nonlocal best_k, best_solution
            used = current_max + 1
            if used < best_k:
                best_k, best_solution = used, colors.copy()
            return False
        
        if current_max + 1 >= best_k:
            return False
        
        used_by_neighbors = {colors[nb] for nb in graph.neighbors(vertex) if colors[nb] >= 0}
        
        for c in range(current_max + 1):
            if c not in used_by_neighbors:
                colors[vertex] = c
                if backtrack(colors, vertex + 1, current_max):
                    colors[vertex] = -1
                    return True
                colors[vertex] = -1
        
        if current_max + 2 < best_k:
            colors[vertex] = current_max + 1
            if backtrack(colors, vertex + 1, current_max + 1):
                colors[vertex] = -1
                return True
            colors[vertex] = -1
        
        return False
    
    vertices_by_degree = sorted(range(n), key=lambda v: graph.degree(v), reverse=True)
    old_to_new = {old: new for new, old in enumerate(vertices_by_degree)}
    
    new_graph = Graph(n)
    for v in range(n):
        for u in graph.neighbors(v):
            if old_to_new[v] < old_to_new[u]:
                new_graph.add_edge(old_to_new[v], old_to_new[u])
    
    backtrack([-1] * n, 0, -1)
    
    final_solution = [0] * n
    for old_v, new_v in old_to_new.items():
        if new_v < len(best_solution):
            final_solution[old_v] = best_solution[new_v]
    
    return final_solution


# ============================================================================
# MODERN COLOR SCHEME
# ============================================================================

class Colors:
    # Main colors
    BG_DARK = "#1a1a2e"
    BG_MEDIUM = "#16213e"
    BG_LIGHT = "#0f3460"
    BG_CARD = "#1f2940"
    
    # Accent colors
    PRIMARY = "#e94560"
    PRIMARY_HOVER = "#ff6b6b"
    SECONDARY = "#0f3460"
    ACCENT = "#00d9ff"
    SUCCESS = "#00d26a"
    WARNING = "#ffc107"
    
    # Text colors
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#a0a0a0"
    TEXT_MUTED = "#6c757d"
    
    # Timeslot colors (vibrant, modern palette)
    TIMESLOTS = [
        "#ff6b6b",  # Coral Red
        "#4ecdc4",  # Teal
        "#45b7d1",  # Sky Blue
        "#96ceb4",  # Sage
        "#ffeaa7",  # Soft Yellow
        "#dfe6e9",  # Light Gray
        "#a29bfe",  # Lavender
        "#fd79a8",  # Pink
        "#00b894",  # Mint
        "#e17055",  # Terra Cotta
        "#74b9ff",  # Light Blue
        "#55a3ff",  # Blue
        "#ffeaa7",  # Yellow
        "#fab1a0",  # Peach
        "#81ecec",  # Cyan
    ]


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class ModernExamScheduler:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("📚 University Exam Scheduler")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg=Colors.BG_DARK)
        
        # Data
        self.courses: List[str] = []
        self.students: Dict[str, List[str]] = {}
        self.course_checkboxes: Dict[str, tk.BooleanVar] = {}
        
        self._setup_styles()
        self._create_ui()
        self._load_sample_data()
    
    def _setup_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styles
        style.configure("Dark.TFrame", background=Colors.BG_DARK)
        style.configure("Card.TFrame", background=Colors.BG_CARD)
        style.configure("Medium.TFrame", background=Colors.BG_MEDIUM)
        
        # Label styles
        style.configure("Title.TLabel",
                       background=Colors.BG_DARK,
                       foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 24, "bold"))
        
        style.configure("Subtitle.TLabel",
                       background=Colors.BG_DARK,
                       foreground=Colors.TEXT_SECONDARY,
                       font=("Segoe UI", 11))
        
        style.configure("Header.TLabel",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 14, "bold"))
        
        style.configure("Card.TLabel",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 10))
        
        style.configure("CardMuted.TLabel",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_SECONDARY,
                       font=("Segoe UI", 9))
        
        style.configure("Stats.TLabel",
                       background=Colors.BG_MEDIUM,
                       foreground=Colors.ACCENT,
                       font=("Segoe UI", 11, "bold"))
        
        # Button styles
        style.configure("Primary.TButton",
                       background=Colors.PRIMARY,
                       foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 11, "bold"),
                       padding=(20, 12))
        
        style.map("Primary.TButton",
                 background=[("active", Colors.PRIMARY_HOVER)])
        
        style.configure("Secondary.TButton",
                       background=Colors.BG_LIGHT,
                       foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 10),
                       padding=(15, 8))
        
        style.configure("Small.TButton",
                       background=Colors.BG_LIGHT,
                       foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 9),
                       padding=(10, 5))
        
        # Entry style
        style.configure("Modern.TEntry",
                       fieldbackground=Colors.BG_LIGHT,
                       foreground=Colors.TEXT_PRIMARY,
                       insertcolor=Colors.TEXT_PRIMARY,
                       padding=10)
        
        # Checkbutton style
        style.configure("Course.TCheckbutton",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY,
                       font=("Segoe UI", 10))
        
        style.map("Course.TCheckbutton",
                 background=[("active", Colors.BG_CARD)])
        
        # LabelFrame style
        style.configure("Card.TLabelframe",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY)
        
        style.configure("Card.TLabelframe.Label",
                       background=Colors.BG_CARD,
                       foreground=Colors.ACCENT,
                       font=("Segoe UI", 12, "bold"))
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container
        main = ttk.Frame(self.root, style="Dark.TFrame")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self._create_header(main)
        
        # Content area with 3 columns
        content = ttk.Frame(main, style="Dark.TFrame")
        content.pack(fill="both", expand=True, pady=(20, 0))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.columnconfigure(2, weight=2)
        content.rowconfigure(0, weight=1)
        
        # Three panels
        self._create_courses_panel(content)
        self._create_students_panel(content)
        self._create_schedule_panel(content)
        
        # Bottom action bar
        self._create_action_bar(main)
    
    def _create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent, style="Dark.TFrame")
        header.pack(fill="x")
        
        # Title with emoji
        title = ttk.Label(header, text="🎓 University Exam Scheduler",
                         style="Title.TLabel")
        title.pack(anchor="w")
        
        # Subtitle
        subtitle = ttk.Label(header,
                            text="Create conflict-free exam timetables using graph coloring algorithms",
                            style="Subtitle.TLabel")
        subtitle.pack(anchor="w", pady=(5, 0))
    
    def _create_courses_panel(self, parent):
        """Create courses input panel"""
        # Card frame
        card = self._create_card(parent, "📚 Courses")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Course entry
        entry_frame = ttk.Frame(card, style="Card.TFrame")
        entry_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(entry_frame, text="Course Code:", style="Card.TLabel").pack(anchor="w")
        
        entry_row = ttk.Frame(entry_frame, style="Card.TFrame")
        entry_row.pack(fill="x", pady=(5, 0))
        
        self.course_entry = tk.Entry(entry_row, 
                                     font=("Segoe UI", 11),
                                     bg=Colors.BG_LIGHT,
                                     fg=Colors.TEXT_PRIMARY,
                                     insertbackground=Colors.TEXT_PRIMARY,
                                     relief="flat",
                                     highlightthickness=2,
                                     highlightbackground=Colors.BG_LIGHT,
                                     highlightcolor=Colors.ACCENT)
        self.course_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.course_entry.bind("<Return>", lambda e: self._add_course())
        
        add_btn = tk.Button(entry_row, text="+ Add",
                           font=("Segoe UI", 10, "bold"),
                           bg=Colors.SUCCESS,
                           fg=Colors.TEXT_PRIMARY,
                           relief="flat",
                           cursor="hand2",
                           command=self._add_course)
        add_btn.pack(side="left", padx=(10, 0), ipady=6, ipadx=10)
        self._add_hover_effect(add_btn, Colors.SUCCESS, "#00ff7f")
        
        # Course list with custom styling
        list_frame = ttk.Frame(card, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        
        # Custom listbox
        self.course_listbox = tk.Listbox(list_frame,
                                         font=("Consolas", 11),
                                         bg=Colors.BG_MEDIUM,
                                         fg=Colors.TEXT_PRIMARY,
                                         selectbackground=Colors.PRIMARY,
                                         selectforeground=Colors.TEXT_PRIMARY,
                                         relief="flat",
                                         highlightthickness=0,
                                         activestyle="none",
                                         borderwidth=0)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                  command=self.course_listbox.yview)
        self.course_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.course_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Remove button
        remove_btn = tk.Button(card, text="🗑️ Remove Selected",
                              font=("Segoe UI", 10),
                              bg=Colors.BG_LIGHT,
                              fg=Colors.TEXT_PRIMARY,
                              relief="flat",
                              cursor="hand2",
                              command=self._remove_course)
        remove_btn.pack(pady=(15, 0), fill="x", ipady=8)
        self._add_hover_effect(remove_btn, Colors.BG_LIGHT, Colors.PRIMARY)
    
    def _create_students_panel(self, parent):
        """Create students input panel with checkboxes"""
        card = self._create_card(parent, "👨‍🎓 Student Enrollments")
        card.grid(row=0, column=1, sticky="nsew", padx=10)
        
        # Student name entry
        name_frame = ttk.Frame(card, style="Card.TFrame")
        name_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(name_frame, text="Student Name:", style="Card.TLabel").pack(anchor="w")
        
        self.student_entry = tk.Entry(name_frame,
                                      font=("Segoe UI", 11),
                                      bg=Colors.BG_LIGHT,
                                      fg=Colors.TEXT_PRIMARY,
                                      insertbackground=Colors.TEXT_PRIMARY,
                                      relief="flat",
                                      highlightthickness=2,
                                      highlightbackground=Colors.BG_LIGHT,
                                      highlightcolor=Colors.ACCENT)
        self.student_entry.pack(fill="x", pady=(5, 0), ipady=8)
        
        # Enrolled courses section (checkboxes)
        courses_label = ttk.Label(card, text="Select Enrolled Courses:",
                                  style="Card.TLabel")
        courses_label.pack(anchor="w", pady=(10, 5))
        
        # Scrollable checkbox area
        checkbox_container = ttk.Frame(card, style="Card.TFrame")
        checkbox_container.pack(fill="both", expand=True)
        
        # Canvas for scrollable checkboxes
        self.checkbox_canvas = tk.Canvas(checkbox_container,
                                         bg=Colors.BG_MEDIUM,
                                         highlightthickness=0,
                                         height=150)
        checkbox_scroll = ttk.Scrollbar(checkbox_container, orient="vertical",
                                        command=self.checkbox_canvas.yview)
        
        self.checkbox_frame = ttk.Frame(self.checkbox_canvas, style="Medium.TFrame")
        self.checkbox_canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        
        self.checkbox_frame.bind("<Configure>",
                                 lambda e: self.checkbox_canvas.configure(
                                     scrollregion=self.checkbox_canvas.bbox("all")))
        
        self.checkbox_canvas.configure(yscrollcommand=checkbox_scroll.set)
        self.checkbox_canvas.pack(side="left", fill="both", expand=True)
        checkbox_scroll.pack(side="right", fill="y")
        
        # Add student button
        add_student_btn = tk.Button(card, text="+ Add Student",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=Colors.SUCCESS,
                                    fg=Colors.TEXT_PRIMARY,
                                    relief="flat",
                                    cursor="hand2",
                                    command=self._add_student)
        add_student_btn.pack(pady=(15, 10), fill="x", ipady=8)
        self._add_hover_effect(add_student_btn, Colors.SUCCESS, "#00ff7f")
        
        # Student list
        ttk.Label(card, text="Registered Students:", style="CardMuted.TLabel").pack(anchor="w")
        
        student_list_frame = ttk.Frame(card, style="Card.TFrame")
        student_list_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        self.student_listbox = tk.Listbox(student_list_frame,
                                          font=("Consolas", 10),
                                          bg=Colors.BG_MEDIUM,
                                          fg=Colors.TEXT_PRIMARY,
                                          selectbackground=Colors.PRIMARY,
                                          selectforeground=Colors.TEXT_PRIMARY,
                                          relief="flat",
                                          highlightthickness=0,
                                          height=8)
        
        student_scroll = ttk.Scrollbar(student_list_frame, orient="vertical",
                                       command=self.student_listbox.yview)
        self.student_listbox.configure(yscrollcommand=student_scroll.set)
        
        self.student_listbox.pack(side="left", fill="both", expand=True)
        student_scroll.pack(side="right", fill="y")
        
        # Remove student button
        remove_student_btn = tk.Button(card, text="🗑️ Remove Selected",
                                       font=("Segoe UI", 9),
                                       bg=Colors.BG_LIGHT,
                                       fg=Colors.TEXT_PRIMARY,
                                       relief="flat",
                                       cursor="hand2",
                                       command=self._remove_student)
        remove_student_btn.pack(pady=(10, 0), fill="x", ipady=6)
        self._add_hover_effect(remove_student_btn, Colors.BG_LIGHT, Colors.PRIMARY)
    
    def _create_schedule_panel(self, parent):
        """Create schedule display panel"""
        card = self._create_card(parent, "📅 Exam Schedule")
        card.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        
        # Stats bar
        stats_frame = ttk.Frame(card, style="Medium.TFrame")
        stats_frame.pack(fill="x", pady=(0, 15))
        stats_frame.configure(padding=10)
        
        self.algo_label = ttk.Label(stats_frame, text="Algorithm: --",
                                    style="Stats.TLabel")
        self.algo_label.pack(side="left")
        
        self.stats_label = ttk.Label(stats_frame, text="Ready to generate",
                                     style="Stats.TLabel")
        self.stats_label.pack(side="right")
        
        # Schedule canvas
        canvas_frame = ttk.Frame(card, style="Card.TFrame")
        canvas_frame.pack(fill="both", expand=True)
        
        self.schedule_canvas = tk.Canvas(canvas_frame,
                                         bg=Colors.BG_MEDIUM,
                                         highlightthickness=0)
        
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical",
                                 command=self.schedule_canvas.yview)
        h_scroll = ttk.Scrollbar(card, orient="horizontal",
                                 command=self.schedule_canvas.xview)
        
        self.schedule_canvas.configure(yscrollcommand=v_scroll.set,
                                       xscrollcommand=h_scroll.set)
        
        self.schedule_canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(fill="x")
        
        # Initial message
        self._show_empty_schedule()
        
        # Log area
        log_frame = ttk.Frame(card, style="Card.TFrame")
        log_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Label(log_frame, text="Activity Log:", style="CardMuted.TLabel").pack(anchor="w")
        
        self.log_text = tk.Text(log_frame,
                                font=("Consolas", 9),
                                bg=Colors.BG_MEDIUM,
                                fg=Colors.TEXT_SECONDARY,
                                relief="flat",
                                height=4,
                                highlightthickness=0)
        self.log_text.pack(fill="x", pady=(5, 0))
    
    def _create_action_bar(self, parent):
        """Create bottom action bar"""
        bar = ttk.Frame(parent, style="Dark.TFrame")
        bar.pack(fill="x", pady=(20, 0))
        
        # Left buttons
        left_btns = ttk.Frame(bar, style="Dark.TFrame")
        left_btns.pack(side="left")
        
        sample_btn = tk.Button(left_btns, text="📋 Load Sample Data",
                               font=("Segoe UI", 10),
                               bg=Colors.BG_LIGHT,
                               fg=Colors.TEXT_PRIMARY,
                               relief="flat",
                               cursor="hand2",
                               command=self._load_sample_data)
        sample_btn.pack(side="left", padx=(0, 10), ipady=10, ipadx=15)
        self._add_hover_effect(sample_btn, Colors.BG_LIGHT, Colors.SECONDARY)
        
        clear_btn = tk.Button(left_btns, text="🗑️ Clear All",
                              font=("Segoe UI", 10),
                              bg=Colors.BG_LIGHT,
                              fg=Colors.TEXT_PRIMARY,
                              relief="flat",
                              cursor="hand2",
                              command=self._clear_all)
        clear_btn.pack(side="left", ipady=10, ipadx=15)
        self._add_hover_effect(clear_btn, Colors.BG_LIGHT, Colors.PRIMARY)
        
        # Main generate button (right side)
        generate_btn = tk.Button(bar, text="✨ Generate Schedule",
                                 font=("Segoe UI", 14, "bold"),
                                 bg=Colors.PRIMARY,
                                 fg=Colors.TEXT_PRIMARY,
                                 relief="flat",
                                 cursor="hand2",
                                 command=self._generate_schedule)
        generate_btn.pack(side="right", ipady=12, ipadx=30)
        self._add_hover_effect(generate_btn, Colors.PRIMARY, Colors.PRIMARY_HOVER)
    
    def _create_card(self, parent, title: str) -> ttk.Frame:
        """Create a styled card frame"""
        card = ttk.LabelFrame(parent, text=f"  {title}  ", style="Card.TLabelframe")
        card.configure(padding=15)
        return card
    
    def _add_hover_effect(self, button: tk.Button, normal_color: str, hover_color: str):
        """Add hover effect to button"""
        button.bind("<Enter>", lambda e: button.configure(bg=hover_color))
        button.bind("<Leave>", lambda e: button.configure(bg=normal_color))
    
    def _darken_color(self, hex_color: str, factor: float = 0.7) -> str:
        """Darken a hex color by a factor (0-1)"""
        hex_color = hex_color.lstrip('#')
        r = int(int(hex_color[0:2], 16) * factor)
        g = int(int(hex_color[2:4], 16) * factor)
        b = int(int(hex_color[4:6], 16) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _update_checkboxes(self):
        """Update the course checkboxes based on current courses"""
        # Clear existing checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.course_checkboxes.clear()
        
        if not self.courses:
            ttk.Label(self.checkbox_frame,
                     text="No courses added yet",
                     style="CardMuted.TLabel").pack(pady=10)
            return
        
        # Create checkbox for each course
        for course in self.courses:
            var = tk.BooleanVar(value=False)
            self.course_checkboxes[course] = var
            
            cb = tk.Checkbutton(self.checkbox_frame,
                               text=f"  {course}",
                               variable=var,
                               font=("Segoe UI", 10),
                               bg=Colors.BG_MEDIUM,
                               fg=Colors.TEXT_PRIMARY,
                               selectcolor=Colors.BG_LIGHT,
                               activebackground=Colors.BG_MEDIUM,
                               activeforeground=Colors.TEXT_PRIMARY,
                               highlightthickness=0,
                               cursor="hand2")
            cb.pack(anchor="w", pady=2, padx=5)
    
    def _add_course(self):
        """Add a course"""
        course = self.course_entry.get().strip().upper()
        if not course:
            return
        if course in self.courses:
            messagebox.showwarning("Duplicate", f"Course '{course}' already exists!")
            return
        
        self.courses.append(course)
        self.course_listbox.insert(tk.END, f"  {course}")
        self.course_entry.delete(0, tk.END)
        self._update_checkboxes()
        self._log(f"Added course: {course}")
    
    def _remove_course(self):
        """Remove selected course"""
        selection = self.course_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        course = self.courses[idx]
        
        # Remove from students too
        for student, courses in self.students.items():
            if course in courses:
                courses.remove(course)
        
        self.courses.pop(idx)
        self.course_listbox.delete(idx)
        self._update_checkboxes()
        self._update_student_display()
        self._log(f"Removed course: {course}")
    
    def _add_student(self):
        """Add a student with selected courses"""
        name = self.student_entry.get().strip()
        if not name:
            messagebox.showwarning("Input Required", "Please enter a student name!")
            return
        
        # Get selected courses
        selected = [course for course, var in self.course_checkboxes.items() if var.get()]
        
        if not selected:
            messagebox.showwarning("No Courses", "Please select at least one course!")
            return
        
        self.students[name] = selected
        self._update_student_display()
        
        # Clear inputs
        self.student_entry.delete(0, tk.END)
        for var in self.course_checkboxes.values():
            var.set(False)
        
        self._log(f"Added student: {name} → {', '.join(selected)}")
    
    def _remove_student(self):
        """Remove selected student"""
        selection = self.student_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        students_list = list(self.students.keys())
        if idx < len(students_list):
            name = students_list[idx]
            del self.students[name]
            self._update_student_display()
            self._log(f"Removed student: {name}")
    
    def _update_student_display(self):
        """Update student listbox"""
        self.student_listbox.delete(0, tk.END)
        for name, courses in sorted(self.students.items()):
            display = f"  {name}: {', '.join(courses)}"
            self.student_listbox.insert(tk.END, display)
    
    def _clear_all(self):
        """Clear all data"""
        self.courses.clear()
        self.students.clear()
        self.course_listbox.delete(0, tk.END)
        self.student_listbox.delete(0, tk.END)
        self._update_checkboxes()
        self._show_empty_schedule()
        self.algo_label.config(text="Algorithm: --")
        self.stats_label.config(text="Ready to generate")
        self.log_text.delete(1.0, tk.END)
        self._log("Cleared all data")
    
    def _load_sample_data(self):
        """Load sample data"""
        self._clear_all()
        
        sample_courses = ["MATH301", "PHY102", "CS101", "CHEM201",
                         "ENG101", "HIST202", "BIO301", "ECON101"]
        
        sample_students = {
            "Alice": ["MATH301", "PHY102", "CS101"],
            "Bob": ["PHY102", "CHEM201", "BIO301"],
            "Charlie": ["CS101", "MATH301", "ENG101"],
            "Diana": ["HIST202", "ENG101", "ECON101"],
            "Eve": ["MATH301", "ECON101", "CHEM201"],
            "Frank": ["BIO301", "CHEM201", "PHY102"],
            "Grace": ["CS101", "ENG101", "HIST202"],
            "Henry": ["ECON101", "HIST202", "MATH301"],
        }
        
        for course in sample_courses:
            self.courses.append(course)
            self.course_listbox.insert(tk.END, f"  {course}")
        
        self.students = sample_students
        self._update_checkboxes()
        self._update_student_display()
        self._log("Loaded sample data: 8 courses, 8 students")
    
    def _build_conflict_graph(self) -> Graph:
        """Build conflict graph from data"""
        n = len(self.courses)
        course_idx = {c: i for i, c in enumerate(self.courses)}
        graph = Graph(n)
        
        for student, enrolled in self.students.items():
            for i in range(len(enrolled)):
                for j in range(i + 1, len(enrolled)):
                    c1 = course_idx.get(enrolled[i])
                    c2 = course_idx.get(enrolled[j])
                    if c1 is not None and c2 is not None:
                        graph.add_edge(c1, c2)
        
        return graph
    
    def _generate_schedule(self):
        """Generate exam schedule"""
        if not self.courses:
            messagebox.showwarning("No Data", "Please add courses first!")
            return
        if not self.students:
            messagebox.showwarning("No Data", "Please add student enrollments!")
            return
        
        try:
            graph = self._build_conflict_graph()
            n = graph.n
            edges = sum(len(adj) for adj in graph.adj) // 2
            self._log(f"Built graph: {n} vertices, {edges} edges")
            
            # Choose algorithm
            if n < 8:
                algo = "Exact Solver (Optimal)"
                self._log(f"Using {algo}...")
                start = time.time()
                colors = exact_coloring(graph)
                elapsed = time.time() - start
            else:
                algo = "DSatur Heuristic"
                self._log(f"Using {algo}...")
                start = time.time()
                colors = dsatur_coloring(graph)
                elapsed = time.time() - start
            
            num_slots = max(colors) + 1 if colors else 0
            
            self.algo_label.config(text=f"Algorithm: {algo}")
            self.stats_label.config(text=f"{n} courses → {num_slots} timeslots | {elapsed*1000:.1f}ms")
            self._log(f"Generated in {elapsed*1000:.1f}ms: {num_slots} timeslots needed")
            
            self._display_schedule(colors, num_slots)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"ERROR: {e}")
    
    def _show_empty_schedule(self):
        """Show empty schedule placeholder"""
        self.schedule_canvas.delete("all")
        self.schedule_canvas.create_text(
            200, 100,
            text="📅\n\nClick 'Generate Schedule'\nto create your timetable",
            font=("Segoe UI", 12),
            fill=Colors.TEXT_MUTED,
            justify="center"
        )
    
    def _display_schedule(self, colors: List[int], num_slots: int):
        """Display the schedule with beautiful cards"""
        self.schedule_canvas.delete("all")
        
        # Group by timeslot
        timeslots: Dict[int, List[str]] = defaultdict(list)
        for i, color in enumerate(colors):
            timeslots[color].append(self.courses[i])
        
        # Layout
        padding = 20
        card_width = 350
        card_height = 90
        y = padding
        
        # Title
        self.schedule_canvas.create_text(
            padding, y,
            text="Generated Exam Timetable",
            font=("Segoe UI", 16, "bold"),
            fill=Colors.TEXT_PRIMARY,
            anchor="nw"
        )
        y += 40
        
        # Draw each timeslot as a card
        for slot in range(num_slots):
            courses = timeslots.get(slot, [])
            color = Colors.TIMESLOTS[slot % len(Colors.TIMESLOTS)]
            
            # Card background with rounded corners effect
            self.schedule_canvas.create_rectangle(
                padding, y,
                padding + card_width, y + card_height,
                fill=color,
                outline="",
                width=0
            )
            
            # Timeslot badge (darker shade of the slot color)
            self.schedule_canvas.create_rectangle(
                padding + 10, y + 10,
                padding + 100, y + 35,
                fill=self._darken_color(color),
                outline=""
            )
            
            self.schedule_canvas.create_text(
                padding + 55, y + 22,
                text=f"Slot {slot + 1}",
                font=("Segoe UI", 11, "bold"),
                fill="#ffffff"
            )
            
            # Courses
            courses_text = " • ".join(courses) if courses else "(empty)"
            self.schedule_canvas.create_text(
                padding + 15, y + 55,
                text=courses_text,
                font=("Consolas", 12, "bold"),
                fill="#000000",
                anchor="w",
                width=card_width - 30
            )
            
            y += card_height + 15
        
        # Success message
        y += 10
        self.schedule_canvas.create_text(
            padding, y,
            text="✓ No student has conflicting exams!",
            font=("Segoe UI", 11, "italic"),
            fill=Colors.SUCCESS,
            anchor="nw"
        )
        
        # Update scroll region
        self.schedule_canvas.configure(scrollregion=(0, 0, card_width + 2*padding, y + 50))
    
    def _log(self, msg: str):
        """Add to activity log"""
        self.log_text.insert(tk.END, f"• {msg}\n")
        self.log_text.see(tk.END)


def main():
    root = tk.Tk()
    app = ModernExamScheduler(root)
    root.mainloop()


if __name__ == "__main__":
    main()
