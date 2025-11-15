#!/usr/bin/env python3.11
# gui.py - makes the GUI for the Canvas API Chatbot and handles user interactions and display
import tkinter as tk
from tkinter import messagebox
import threading
from datetime import datetime, timezone, timedelta
from Canvas_api import CanvasAPI
from chatbot import CanvasChatBot
from tkinter import messagebox
import os, json, uuid
from datetime import datetime

# Try to import NLTK
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    # Download required data
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except:
        pass
except ImportError:
    NLTK_AVAILABLE = False


class CanvasChatbotGUI:
    # Initialize the GUI
    def __init__(self, root):
        self.root = root
        self.root.title("Canvas API Chatbot")
        self.root.geometry("1400x900")
        
        self.sidebar_color = "#6B1C1C"  
        self.button_color = "#D8C5D8"   
        self.main_bg = "#F5F5F0"        
        
        self.api = None
        self.user_name = "User"
        self.courses = []
        self.assignments_cache = {}
        self.last_sync_time = None
        self.chatbot = None  # Will be initialized after login
        
        self.show_login_screen()
    #creats the login screen
    def show_login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        login_frame = tk.Frame(self.root, bg=self.main_bg)
        login_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        tk.Label(login_frame, text="Canvas API Chatbot", 
                font=('Arial', 24, 'bold'), bg=self.main_bg, fg=self.sidebar_color).pack(pady=20)
        
        tk.Label(login_frame, text="Canvas URL:", 
                font=('Arial', 12), bg=self.main_bg, fg=self.sidebar_color).pack(anchor='w', padx=20)
        self.url_entry = tk.Entry(login_frame, width=40, font=('Arial', 11))
        self.url_entry.pack(padx=20, pady=(5, 15))
        self.url_entry.insert(0, "https://nmsu.instructure.com")
        
        tk.Label(login_frame, text="Access Token:", 
                font=('Arial', 12), bg=self.main_bg, fg= self.sidebar_color).pack(anchor='w', padx=20)
        self.token_entry = tk.Entry(login_frame, width=40, font=('Arial', 11), show="*")
        self.token_entry.pack(padx=20, pady=(5, 20))
        
        tk.Button(login_frame, text="Login", command=self.login,
                 bg=self.sidebar_color, fg='black',
                 font=('Arial', 12, 'bold'), padx=30, pady=10).pack(pady=10)
        
        tk.Button(login_frame, text="Show Tutorial", command=self.tutorial_popup,
                 bg=self.button_color, fg='black',
                 font=('Arial', 12), padx=20, pady=6).pack(pady=5)
        
        self.root.bind('<Return>', lambda e: self.login())
        
        self.status_label = tk.Label(login_frame, text="", font=('Arial', 10), bg=self.main_bg)
        self.status_label.pack(pady=10)
    #handles the login process and authentication
    def login(self):
        url = self.url_entry.get().strip()
        token = self.token_entry.get().strip()
        
        if not url or not token:
            messagebox.showerror("Error", "Please enter both URL and token")
            return
        
        self.status_label.config(text="Logging in...", fg="blue", font=('Arial', 22, 'italic'))
        self.root.update()
        
        threading.Thread(target=self._do_login, args=(url, token), daemon=True).start()
    
    # Perform login in background and fetch data
    def _do_login(self, url, token):
        try:
            self.api = CanvasAPI(url, token)
            user = self.api.get_current_user()
            
            if not user:
                self.root.after(0, lambda: messagebox.showerror("Error", "Authentication failed"))
                return
            
            self.user_name = user.get('name', 'User')
            all_courses = self.api.get_courses()
            
            # Filter out courses with None or empty names 
            self.courses = [c for c in all_courses if c.get('name') and c.get('name').strip().lower() != 'none']
            
            # Load all assignments and grades
            for course in self.courses:
                course_id = course.get('id')
                assignments = self.api.get_assignments(course_id)
                if assignments:
                    self.assignments_cache[course_id] = assignments
            
            # Initialize chatbot with loaded data
            self.chatbot = CanvasChatBot(self.api, self.courses, self.assignments_cache)
            
            self.last_sync_time = datetime.now()
            self.root.after(0, self.show_main_screen)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    #creates a tutorial popup for new users        
    def tutorial_popup(self):
        tutorial_text = (
            "Welcome to the Canvas API Chatbot!\n\n"
            "To get started:\n"
            "1. Obtain your Canvas API Access Token from your Canvas account settings.\n"
            "2. Enter your Canvas URL (e.g., https://nmsu.instructure.com) and the access token on the login screen.\n"
            "3. Click 'Login' to access your courses and assignments.\n\n"
            "Once logged in, you can view upcoming assignments, check grades, and set reminders.\n\n"
            "Enjoy using the Canvas API Chatbot!"
        )
        messagebox.showinfo("Tutorial", tutorial_text)
    
    #creates the main screen after login is successful
    def show_main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.unbind('<Return>')
        
        main_container = tk.Frame(self.root)
        main_container.pack(fill='both', expand=True)
        
        self.create_sidebar(main_container)
        self.create_main_content(main_container)
        self.show_dashboard()
    
    #creates the sidebar with all the buttons and search box 
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=self.sidebar_color, width=350)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        buttons = [
            ("View Upcoming Assignments", self.show_all_assignments),
            ("Check Grades", self.show_grades),
            ("Set Reminder", self.show_reminders),
        ]
        
        for text, command in buttons:
            tk.Button(sidebar, text=text, command=command,
                     bg=self.button_color, font=('Arial', 12),
                     relief='flat', pady=15, cursor='hand2').pack(fill='x', padx=20, pady=10)
        
        # Search box
        search_frame = tk.Frame(sidebar, bg=self.sidebar_color)
        search_frame.pack(fill='x', padx=20, pady=30)
        
        self.search_entry = tk.Entry(search_frame, font=('Arial', 11))
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.insert(0, "Chat with me!")
        self.search_entry.bind('<FocusIn>', lambda e: self.clear_placeholder())
        self.search_entry.bind('<Return>', lambda e: self.process_search())
        
        tk.Button(search_frame, text="Search", command=self.process_search,
                 bg='white', relief='flat', font=('Arial', 10)).pack(side='right', padx=(5, 0))
        
        # Settings at bottom
        tk.Button(sidebar, text="Settings", command=self.show_settings,
                 bg=self.button_color, font=('Arial', 12),
                 relief='flat', pady=15).pack(side='bottom', fill='x', padx=20, pady=20)
        
        tk.Button(sidebar, text="Home", command=self.show_dashboard,
                 bg=self.button_color, font=('Arial', 12),
                 relief='flat', pady=15).pack(side='bottom', fill='x', padx=20, pady=20)
    
    #creates the main content area with scrollable functionality
    def create_main_content(self, parent):
        main_frame = tk.Frame(parent, bg=self.main_bg)
        main_frame.pack(side='right', fill='both', expand=True)

        # ----- Header -----
        header = tk.Frame(main_frame, bg=self.sidebar_color, height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Canvas API Chatbot",
            font=('Arial', 28, 'bold'),
            bg=self.sidebar_color,
            fg='white'
        ).pack(pady=20)

        # ----- Scrollable content -----
        # Outer frame that holds both canvas and scrollbar
        content_container = tk.Frame(main_frame, bg=self.main_bg)
        content_container.pack(fill='both', expand=True)

        # Canvas + Scrollbar - Store canvas as instance variable
        self.canvas = tk.Canvas(content_container, bg=self.main_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(content_container, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True, padx=30, pady=20)

        # Inner frame where actual widgets go
        self.content_frame = tk.Frame(self.canvas, bg=self.main_bg)
        self.content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor='nw')

        # Update scroll region dynamically
        def on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.content_frame.bind("<Configure>", on_frame_configure)

        # Mouse wheel scrolling - works on Windows, Mac, and Linux
        def _on_mousewheel(event):
            # Windows and Mac
            if event.delta:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            # Linux
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
        
        # Bind mouse wheel for Windows/Mac
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Bind mouse wheel for Linux
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)

        # Resize inner frame when window resizes
        def resize_canvas(event):
            self.canvas.itemconfig(self.content_window, width=event.width)

        self.canvas.bind("<Configure>", resize_canvas)
    
    def update_scroll_region(self):
        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    #clears the main content area after a button is clicked
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    #creates the dashboard view for the main screen
    def show_dashboard(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text=f"Welcome back, {self.user_name}", 
                font=('Arial', 18, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))
        
        # Upcoming Assignments
        self.create_section("Upcoming Assignment", self.get_upcoming_assignments())
        
        # Grades
        self.create_section("Grades", self.get_grades_display())
        
        # Reminders
        self.create_section("Active Reminders", ["Lab Report Due tomorrow"])
        
        # Last sync
        if self.last_sync_time:
            mins = int((datetime.now() - self.last_sync_time).total_seconds() / 60)
            tk.Label(self.content_frame, text=f"Last synced to canvas, {mins} minutes ago",
                    font=('Arial', 10), bg=self.main_bg, fg='#6B6B6B').pack(pady=(20, 0))
        
        # Update scroll region
        self.update_scroll_region()
    
    #creates a section in the dashboard with a title and list of items
    def create_section(self, title, items):
        tk.Label(self.content_frame, text=title, 
                font=('Arial', 16, 'bold'), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=(20, 10))
        
        tk.Label(self.content_frame, text="-" * 40, 
                font=('Arial', 12), bg=self.main_bg, fg='#6B6B6B').pack(anchor='w')
        
        for item in items:
            tk.Label(self.content_frame, text=item, 
                    font=('Arial', 12), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=3)
    
    #computes the upcoming assignment for the dashboard that are due in 10 days or less 
    def get_upcoming_assignments(self):
        upcoming = []
        now = datetime.now(timezone.utc)
        ten_days_from_now = now + timedelta(days=10)

        for course in self.courses:
            course_name = course.get('name', '')
            course_id = course.get('id')

            for assignment in self.assignments_cache.get(course_id, []):
                due_at = assignment.get('due_at')
                if not due_at:
                    continue

                try:
                    due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                except Exception:
                    continue

                if due_date > now:
                    delta = due_date - now
                    days = delta.days
                    hours = delta.seconds // 3600
                    course_code = course_name[:20].strip()
                    if days == 0:
                        time_str = f"Due in {hours} hours"
                    else:
                        time_str = f"Due in {days} days"

                    upcoming.append((due_date, f"{course_code} - {assignment.get('name', 'Untitled')} ({time_str})"))

        upcoming.sort(key=lambda x: x[0])

        if not upcoming:
            return ["No upcoming assignments"]

        return [entry[1] for entry in upcoming[:3]]
    
    #gets the grades for display on the dashboard when clicked on the grades button
    def get_grades_display(self):
        grades_display = []
        for course in self.courses:  # Show all courses
            course_id = course.get('id')
            course_name = course.get('name', 'Unknown Course')
            
            # Get grade
            grade_info = self.api.get_course_grade(course_id)
            
            if grade_info and grade_info.get('current_score') is not None:
                score = grade_info.get('current_score')
                letter = grade_info.get('current_grade', '')
                grades_display.append(f"{course_name} - {score:.1f}% {letter}")
            else:
                grades_display.append(f"{course_name} - No grade yet")
        
        return grades_display if grades_display else ["No grades available"]
    
    from datetime import datetime, timezone

    #show all assignments that are upcoming and not yet submitted when view upcoming assignments is clicked
    def show_all_assignments(self):
        self.clear_content()
        
        tk.Label(
            self.content_frame, 
            text="Upcoming Assignments", 
            font=('Arial', 20, 'bold'), 
            bg=self.main_bg, 
            fg='#2C1810'
        ).pack(pady=(0, 20))
        
        tk.Label(
            self.content_frame, 
            text="(These are the assignments not yet submitted)", 
            font=('Arial', 12, 'italic'), 
            bg=self.main_bg, 
            fg='#6B6B6B'
        ).pack(pady=(0, 10))
        
        now = datetime.now(timezone.utc)
        found_any = False

        for course in self.courses:
            course_id = course.get('id')
            course_name = course.get('name', 'Unnamed Course')
            
            # Get submissions to check what's been submitted
            submissions = self.api.get_assignment_submissions(course_id)
            submitted_ids = set()

            if submissions:
                for sub in submissions:
                    # If submitted (has a submitted_at date or state is "submitted")
                    if sub.get('submitted_at') or sub.get('workflow_state') == 'submitted':
                        submitted_ids.add(sub.get('assignment_id'))
            
            # Filter upcoming or undated assignments
            upcoming_assignments = []
            for assignment in self.assignments_cache.get(course_id, []):
                assignment_id = assignment.get('id')
                due_at = assignment.get('due_at')

                # Skip if submitted
                if assignment_id in submitted_ids:
                    continue

                # Include if no due date or due date is in the future
                if not due_at:
                    upcoming_assignments.append(assignment)
                else:
                    try:
                        due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                        if due_date > now:
                            upcoming_assignments.append(assignment)
                    except Exception:
                        # If date parsing fails, still include (to avoid missing valid assignments)
                        upcoming_assignments.append(assignment)
            
            # Display course and its assignments if any
            if upcoming_assignments:
                found_any = True
                tk.Label(
                    self.content_frame, 
                    text=f"\n>> {course_name}", 
                    font=('Arial', 14, 'bold'), 
                    bg=self.main_bg, 
                    fg='#2C1810'
                ).pack(anchor='w')
                
                # Sort assignments by due date for readability
                upcoming_assignments.sort(
                    key=lambda a: a.get('due_at') or '9999-12-31'
                )

                for assignment in upcoming_assignments:
                    due_at = assignment.get('due_at')
                    if due_at:
                        try:
                            due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                            days_until = (due_date - now).days
                            if days_until >= 0:
                                due_text = f" (Due in {days_until} days)"
                            else:
                                due_text = f" (Overdue by {-days_until} days)"
                        except Exception:
                            due_text = " (Invalid date)"
                    else:
                        due_text = " (No due date)"
                    
                    tk.Label(
                        self.content_frame, 
                        text=f"  - {assignment.get('name', 'Untitled')}{due_text}", 
                        font=('Arial', 11), 
                        bg=self.main_bg, 
                        fg='#2C1810'
                    ).pack(anchor='w', pady=2)
        
        if not found_any:
            tk.Label(
                self.content_frame, 
                text="No upcoming assignments! Great job!", 
                font=('Arial', 12), 
                bg=self.main_bg, 
                fg='#2C1810'
            ).pack(anchor='w', pady=20)
        
        # Update scroll region
        self.update_scroll_region()

    #show grades when the grades button is clicked
    def show_grades(self):
        """Show grades"""
        self.clear_content()
        tk.Label(self.content_frame, text="Grades", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))
        
        tk.Label(self.content_frame, text="-" * 40, 
                font=('Arial', 12), bg=self.main_bg, fg='#6B6B6B').pack(anchor='w', pady=(0, 10))
        
        # Fetch and display grades for each course
        for course in self.courses:
            course_id = course.get('id')
            course_name = course.get('name', 'Unknown Course')
            
            # Get the overall grade for this course
            grade_info = self.api.get_course_grade(course_id)
            
            if grade_info and grade_info.get('current_score') is not None:
                score = grade_info.get('current_score')
                letter = grade_info.get('current_grade', '')
                grade_text = f"{course_name} - {score:.1f}% {letter}"
            else:
                grade_text = f"{course_name} - No grade available"
            
            # Create clickable label for each course grade
            grade_label = tk.Label(self.content_frame, text=grade_text, 
                                  font=('Arial', 12), bg=self.main_bg, fg='#2C1810',
                                  cursor='hand2')
            grade_label.pack(anchor='w', pady=5)
            
            # Make it clickable to show assignment details
            grade_label.bind('<Button-1>', 
                           lambda e, cid=course_id, cname=course_name: self.show_grade_details(cid, cname))
        
        # Update scroll region
        self.update_scroll_region()
    
    #showes the detailed grade information for a specific course when clicked on the grades view
    def show_grade_details(self, course_id, course_name):
        self.clear_content()

        tk.Label(self.content_frame, text=f"{course_name} - Assignments",
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 10), anchor='w')

        tk.Label(self.content_frame, text="Loading submission data...",
                font=('Arial', 11, 'italic'), bg=self.main_bg, fg='#6B6B6B').pack(anchor='w', pady=5)
        
        self.root.update()  # Update UI to show loading message

        assignments = self.assignments_cache.get(course_id, [])
        if not assignments:
            tk.Label(self.content_frame, text="No assignments found.",
                    font=('Arial', 12), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=10)
        else:
            # Try bulk fetch first
            submissions = self.api.get_assignment_submissions(course_id)
            
            # Create a mapping of assignment_id -> submission data
            submission_map = {}
            
            if submissions:
                for sub in submissions:
                    assignment_id = sub.get('assignment_id')
                    if assignment_id:
                        submission_map[assignment_id] = sub
            
            # Clear the loading message
            for widget in self.content_frame.winfo_children():
                if "Loading" in str(widget.cget('text')):
                    widget.destroy()
            
            now = datetime.now(timezone.utc)

            # Sort by due date if available
            assignments.sort(key=lambda a: a.get('due_at') or '9999-12-31T00:00:00Z')

            for a in assignments:
                name = a.get("name", "Untitled Assignment")
                due = a.get("due_at")
                assignment_id = a.get("id")
                possible = a.get("points_possible")
                
                # Get submission - try map first, then fetch individually if not found
                submission = submission_map.get(assignment_id)
                if not submission:
                    # Fallback: fetch individual submission
                    submission = self.api.get_single_assignment_submission(course_id, assignment_id)
                    if not submission:
                        submission = {}
                
                score = submission.get("score")
                submitted = submission.get("submitted_at") is not None or submission.get("workflow_state") == "submitted"
                
                if due:
                    try:
                        due_dt = datetime.fromisoformat(due.replace('Z', '+00:00'))
                        days_diff = (now - due_dt).days
                        if days_diff > 0:
                            due_text = f"Due {due_dt.strftime('%b %d, %Y')} ({days_diff} days ago)"
                        elif days_diff == 0:
                            due_text = f"Due {due_dt.strftime('%b %d, %Y')} (Today)"
                        else:
                            due_text = f"Due {due_dt.strftime('%b %d, %Y')} (in {-days_diff} days)"
                    except Exception:
                        due_text = "Due date invalid"
                else:
                    due_text = "No due date"

                status = "Submitted" if submitted else "Not submitted"

                # Make a small formatted block for each assignment
                frame = tk.Frame(self.content_frame, bg=self.main_bg)
                frame.pack(fill='x', anchor='w', pady=4)

                tk.Label(frame, text=f"- {name}",
                        font=('Arial', 12, 'bold'), bg=self.main_bg, fg='#2C1810').pack(anchor='w')
                tk.Label(frame, text=f"   {due_text}",
                        font=('Arial', 11), bg=self.main_bg, fg='#3C3C3C').pack(anchor='w')
                
                # Display score/possible points
                if score is not None and possible is not None:
                    percentage = (score / possible * 100) if possible > 0 else 0
                    score_text = f"   Score: {score}/{possible} ({percentage:.1f}%)"
                elif score is not None:
                    score_text = f"   Score: {score}"
                elif possible is not None:
                    score_text = f"   Points possible: {possible} (Not graded yet)"
                else:
                    score_text = "   Not graded yet"
                
                tk.Label(frame, text=score_text,
                        font=('Arial', 11), bg=self.main_bg, fg='#3C3C3C').pack(anchor='w')
                tk.Label(frame, text=f"   Status: {status}",
                        font=('Arial', 11), bg=self.main_bg,
                        fg='#007F00' if submitted else '#A00000').pack(anchor='w')

        # Add a back button
        tk.Button(self.content_frame, text="<- Back",
                command=self.show_grades, bg=self.sidebar_color, fg='black',
                font=('Arial', 11), padx=15, pady=6).pack(anchor='w', pady=20)
        
        # Update scroll region
        self.update_scroll_region()
    
    def show_reminders(self):
        import tkinter as tk
        from tkinter import messagebox, simpledialog

        self.clear_content()

        # In-memory list for this session only
        if not hasattr(self, "_reminders_tmp"):
            self._reminders_tmp = []

        # Title
        tk.Label(self.content_frame, text="Reminders",
        font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))

        # Buttons row
        btns = tk.Frame(self.content_frame, bg=self.main_bg)
        btns.pack(pady=10)

        # Dedicated area for the list (so we can re-render safely)
        list_frame = tk.Frame(self.content_frame, bg=self.main_bg)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)

        def render_list():
            # wipe previous contents
            for w in list_frame.winfo_children():
                w.destroy()
            items = sorted(self._reminders_tmp, key=lambda r: r.get("when", ""))
            if not items:
                tk.Label(list_frame, text="No reminders yet.", bg=self.main_bg).pack(anchor='w')
                return
            for r in items:
                row = tk.Frame(list_frame, bg=self.main_bg, highlightbackground='#DDD', highlightthickness=1, padx=8, pady=6)
                row.pack(fill='x', pady=6)
                tk.Label(row, text=r.get("title", "(untitled)"), bg=self.main_bg, font=('Arial', 12, 'bold')).pack(anchor='w')
                tk.Label(row, text=f"When: {r.get('when','')}", bg=self.main_bg).pack(anchor='w')
                if r.get("note"):
                    tk.Label(row, text=r["note"], bg=self.main_bg, fg="#3C3C3C").pack(anchor='w')

        def on_add():
            title = simpledialog.askstring("Add Reminder", "Title:", parent=self.root)
            if not title:
                return
            when = simpledialog.askstring("Add Reminder", "When (YYYY-MM-DDTHH:MM):", parent=self.root)
            if not when:
                return
            note = simpledialog.askstring("Add Reminder", "Note (optional):", parent=self.root) or ""
            self._reminders_tmp.append({"title": title.strip(), "when": when.strip(), "note": note.strip()})
            messagebox.showinfo("Reminders", "Saved.")
            render_list()  # show the new item

        def on_view():
            render_list()

        tk.Button(btns, text="Add Reminder", command=on_add,
            bg=self.sidebar_color, relief='flat', padx=20, pady=10).grid(row=0, column=0, padx=10, pady=10)

        tk.Button(btns, text="View Reminders", command=on_view,
        bg=self.sidebar_color, relief='flat', padx=20, pady=10).grid(row=0, column=1, padx=10, pady=10)

        # Back
        tk.Button(self.content_frame, text="<- Back", command=self.show_dashboard,
        bg=self.sidebar_color, relief='flat', padx=10, pady=6).pack(anchor='w', padx=10, pady=(20, 0))

        self.update_scroll_region()
    
        #show settings when the settings button is clicked
    def show_settings(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Settings", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))
        tk.Label(self.content_frame, text=f"Logged in as: {self.user_name}", 
                font=('Arial', 18), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=10)
        tk.Button(self.content_frame, text="Logout", command=self.logout,
                 bg=self.sidebar_color, fg='black', font=('Arial', 11), 
                 padx=20, pady=5).pack(anchor='center', pady=10)
        
        # Update scroll region
        self.update_scroll_region()
    
    #handles the logout process
    def logout(self):
        self.api = None
        self.show_login_screen()
    
    #clears the placeholder text in the search box when clicked
    def clear_placeholder(self):
        if self.search_entry.get() == "Chat with me!":
            self.search_entry.delete(0, 'end')
    
    #processes the search query with intelligent intent detection
    def process_search(self):
        query = self.search_entry.get().strip()
        if not query or query == "Chat with me!":
            return
        
        # Use chatbot to process query
        if self.chatbot:
            response = self.chatbot.process_query(query)
        else:
            response = "Chatbot not initialized. Please try logging in again."
        
        self.show_results(query, response)
    
    def show_results(self, query, response):
        self.clear_content()
        
        # Chat header
        tk.Label(self.content_frame, text="Chat Assistant", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 10))
        
        # User query in a speech bubble style
        query_frame = tk.Frame(self.content_frame, bg='#E8E8E8', relief='solid', borderwidth=1)
        query_frame.pack(fill='x', pady=(10, 5), padx=20)
        
        tk.Label(query_frame, text="You:", 
                font=('Arial', 10, 'bold'), bg='#E8E8E8', fg='#666666').pack(anchor='w', padx=10, pady=(5, 0))
        tk.Label(query_frame, text=query, 
                font=('Arial', 12), bg='#E8E8E8', fg='#2C1810', 
                wraplength=700, justify='left').pack(anchor='w', padx=10, pady=(0, 10))
        
        # Assistant response in a different speech bubble
        response_frame = tk.Frame(self.content_frame, bg='#F8F8FF', relief='solid', borderwidth=1)
        response_frame.pack(fill='x', pady=(5, 10), padx=20)
        
        tk.Label(response_frame, text="Assistant:", 
                font=('Arial', 10, 'bold'), bg='#F8F8FF', fg=self.sidebar_color).pack(anchor='w', padx=10, pady=(5, 0))
        tk.Label(response_frame, text=response, 
                font=('Arial', 12), bg='#F8F8FF', fg='#2C1810', 
                wraplength=700, justify='left').pack(anchor='w', padx=10, pady=(5, 10))
        
        # Buttons
        button_frame = tk.Frame(self.content_frame, bg=self.main_bg)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Ask Another Question", command=self.focus_search,
                 bg=self.sidebar_color, fg='black', font=('Arial', 11), 
                 padx=20, pady=8).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="Back to Dashboard", command=self.show_dashboard,
                 bg=self.button_color, fg='black', font=('Arial', 11), 
                 padx=20, pady=8).pack(side='left', padx=5)
        
        # Update scroll region
        self.update_scroll_region()
    
    def focus_search(self):
        self.show_dashboard()
        self.search_entry.focus()
        if self.search_entry.get() == "Chat with me!":
            self.search_entry.delete(0, 'end')

# the entry point for the application
def main():
    root = tk.Tk()
    app = CanvasChatbotGUI(root)
    root.mainloop()

# the main function is called when the script is executed
if __name__ == "__main__":
    main()