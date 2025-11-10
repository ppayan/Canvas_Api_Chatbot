#!/usr/bin/env python3.11
# gui.py - Canvas API Chatbot with Dashboard
import tkinter as tk
from tkinter import messagebox
import threading
from datetime import datetime
from Canvas_api import CanvasAPI

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
    def __init__(self, root):
        self.root = root
        self.root.title("Canvas API Chatbot")
        self.root.geometry("1200x700")
        
        # Colors from screenshot
        self.sidebar_color = "#6B1C1C"  # Maroon
        self.button_color = "#D8C5D8"   # Light purple
        self.main_bg = "#F5F5F0"        # Cream
        
        self.api = None
        self.user_name = "User"
        self.courses = []
        self.assignments_cache = {}
        self.last_sync_time = None
        
        self.show_login_screen()
    
    def show_login_screen(self):
        """Show login screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        login_frame = tk.Frame(self.root, bg=self.main_bg)
        login_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        tk.Label(login_frame, text="Canvas API Chatbot", 
                font=('Arial', 24, 'bold'), bg=self.main_bg, fg=self.sidebar_color).pack(pady=20)
        
        tk.Label(login_frame, text="Canvas URL:", 
                font=('Arial', 12), bg=self.main_bg).pack(anchor='w', padx=20)
        self.url_entry = tk.Entry(login_frame, width=40, font=('Arial', 11))
        self.url_entry.pack(padx=20, pady=(5, 15))
        self.url_entry.insert(0, "https://nmsu.instructure.com")
        
        tk.Label(login_frame, text="Access Token:", 
                font=('Arial', 12), bg=self.main_bg).pack(anchor='w', padx=20)
        self.token_entry = tk.Entry(login_frame, width=40, font=('Arial', 11), show="*")
        self.token_entry.pack(padx=20, pady=(5, 20))
        
        tk.Button(login_frame, text="Login", command=self.login,
                 bg=self.sidebar_color, fg='white',
                 font=('Arial', 12, 'bold'), padx=30, pady=10).pack(pady=10)
        
        self.root.bind('<Return>', lambda e: self.login())
        
        self.status_label = tk.Label(login_frame, text="", font=('Arial', 10), bg=self.main_bg)
        self.status_label.pack(pady=10)
    
    def login(self):
        """Handle login"""
        url = self.url_entry.get().strip()
        token = self.token_entry.get().strip()
        
        if not url or not token:
            messagebox.showerror("Error", "Please enter both URL and token")
            return
        
        self.status_label.config(text="Logging in...", fg="blue")
        self.root.update()
        
        threading.Thread(target=self._do_login, args=(url, token), daemon=True).start()
    
    def _do_login(self, url, token):
        """Perform login in background"""
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
            
            self.last_sync_time = datetime.now()
            self.root.after(0, self.show_main_screen)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def show_main_screen(self):
        """Show main dashboard"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.unbind('<Return>')
        
        main_container = tk.Frame(self.root)
        main_container.pack(fill='both', expand=True)
        
        self.create_sidebar(main_container)
        self.create_main_content(main_container)
        self.show_dashboard()
    
    def create_sidebar(self, parent):
        """Create sidebar with buttons"""
        sidebar = tk.Frame(parent, bg=self.sidebar_color, width=350)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        buttons = [
            ("View All Assignments", self.show_all_assignments),
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
        self.search_entry.insert(0, "Hinted search text")
        self.search_entry.bind('<FocusIn>', lambda e: self.clear_placeholder())
        self.search_entry.bind('<Return>', lambda e: self.process_search())
        
        tk.Button(search_frame, text="Search", command=self.process_search,
                 bg='white', relief='flat', font=('Arial', 10)).pack(side='right', padx=(5, 0))
        
        # Settings at bottom
        tk.Button(sidebar, text="Settings", command=self.show_settings,
                 bg=self.button_color, font=('Arial', 12),
                 relief='flat', pady=15).pack(side='bottom', fill='x', padx=20, pady=20)
    
    def create_main_content(self, parent):
        """Create main content area"""
        main_frame = tk.Frame(parent, bg=self.main_bg)
        main_frame.pack(side='right', fill='both', expand=True)
        
        # Header
        header = tk.Frame(main_frame, bg=self.sidebar_color, height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="Canvas API Chatbot", 
                font=('Arial', 28, 'bold'), bg=self.sidebar_color, fg='white').pack(pady=20)
        
        # Scrollable content
        canvas = tk.Canvas(main_frame, bg=self.main_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        
        self.content_frame = tk.Frame(canvas, bg=self.main_bg)
        
        canvas.pack(side='left', fill='both', expand=True, padx=30, pady=20)
        scrollbar.pack(side='right', fill='y')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=self.content_frame, anchor='nw')
        
        self.content_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    
    def clear_content(self):
        """Clear content"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Show dashboard"""
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
    
    def create_section(self, title, items):
        """Create section"""
        tk.Label(self.content_frame, text=title, 
                font=('Arial', 16, 'bold'), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=(20, 10))
        
        tk.Label(self.content_frame, text="-" * 40, 
                font=('Arial', 12), bg=self.main_bg, fg='#6B6B6B').pack(anchor='w')
        
        for item in items:
            tk.Label(self.content_frame, text=item, 
                    font=('Arial', 12), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=3)
    
    def get_upcoming_assignments(self):
        """Get upcoming assignments"""
        upcoming = []
        now = datetime.now()
        
        for course in self.courses:
            course_name = course.get('name', '')
            course_id = course.get('id')
            
            for assignment in self.assignments_cache.get(course_id, []):
                due_at = assignment.get('due_at')
                if due_at:
                    try:
                        due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                        if due_date > now:
                            days = (due_date - now).days
                            course_code = course_name.split('-')[0].strip() if '-' in course_name else course_name[:15]
                            upcoming.append((due_date, f"{course_code} - {assignment.get('name', 'Untitled')}", days))
                    except:
                        pass
        
        upcoming.sort(key=lambda x: x[0])
        result = []
        for _, text, days in upcoming[:3]:
            result.append(text)
            result.append(f"(Due in {days} days)")
            result.append("")
        
        return result if result else ["No upcoming assignments"]
    
    def get_grades_display(self):
        """Get grades for display on dashboard"""
        grades_display = []
        for course in self.courses:  # Show top 3 courses
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
    
    def show_all_assignments(self):
        """Show all assignments"""
        self.clear_content()
        
        tk.Label(self.content_frame, text="All Assignments", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))
        
        for course in self.courses:
            tk.Label(self.content_frame, text=f"\n>> {course.get('name')}", 
                    font=('Arial', 14, 'bold'), bg=self.main_bg, fg='#2C1810').pack(anchor='w')
            
            for assignment in self.assignments_cache.get(course.get('id'), [])[:-5]:
                tk.Label(self.content_frame, text=f"  * {assignment.get('name')}", 
                        font=('Arial', 11), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=2)
    
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
    
    def show_grade_details(self, course_id, course_name):
        """Show detailed grades for a specific course"""
        self.clear_content()
        
        tk.Label(self.content_frame, text=f"Grades - {course_name}", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))
        
        # Get assignment submissions with grades
        submissions = self.api.get_assignment_submissions(course_id)
        
        if not submissions:
            tk.Label(self.content_frame, text="No graded assignments found.", 
                    font=('Arial', 12), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=10)
        else:
            # Get assignment names from cache
            assignments_dict = {}
            if course_id in self.assignments_cache:
                for assignment in self.assignments_cache[course_id]:
                    assignments_dict[assignment.get('id')] = assignment.get('name', 'Untitled')
            
            # Display each graded assignment
            for submission in submissions:
                assignment_id = submission.get('assignment_id')
                assignment_name = assignments_dict.get(assignment_id, f"Assignment {assignment_id}")
                
                score = submission.get('score')
                possible = submission.get('assignment', {}).get('points_possible')
                grade = submission.get('grade')
                
                if score is not None and possible:
                    percentage = (score / possible * 100) if possible > 0 else 0
                    grade_text = f"  * {assignment_name}: {score}/{possible} ({percentage:.1f}%)"
                elif grade:
                    grade_text = f"  * {assignment_name}: {grade}"
                else:
                    grade_text = f"  * {assignment_name}: Not graded yet"
                
                tk.Label(self.content_frame, text=grade_text, 
                        font=('Arial', 11), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=3)
        
        # Back button
        tk.Button(self.content_frame, text="<- Back to Grades", command=self.show_grades,
                 bg=self.sidebar_color, fg='white', font=('Arial', 11), 
                 padx=15, pady=5).pack(anchor='w', pady=20)
    
    def show_reminders(self):
        """Show reminders"""
        self.clear_content()
        tk.Label(self.content_frame, text="Reminders", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))
        tk.Label(self.content_frame, text="Reminder feature coming soon!", 
                font=('Arial', 12), bg=self.main_bg, fg='#2C1810').pack(pady=10)
    
    def show_settings(self):
        """Show settings"""
        self.clear_content()
        tk.Label(self.content_frame, text="Settings", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 20))
        tk.Label(self.content_frame, text=f"Logged in as: {self.user_name}", 
                font=('Arial', 12), bg=self.main_bg, fg='#2C1810').pack(anchor='w', pady=10)
        tk.Button(self.content_frame, text="Logout", command=self.logout,
                 bg=self.sidebar_color, fg='white', font=('Arial', 11), 
                 padx=20, pady=5).pack(anchor='w', pady=10)
    
    def logout(self):
        """Logout"""
        self.api = None
        self.show_login_screen()
    
    def clear_placeholder(self):
        """Clear placeholder"""
        if self.search_entry.get() == "Hinted search text":
            self.search_entry.delete(0, 'end')
    
    def process_search(self):
        """Process search with NLTK"""
        query = self.search_entry.get().strip()
        if not query or query == "Hinted search text":
            return
        
        if NLTK_AVAILABLE:
            response = self.process_nltk(query)
        else:
            response = self.process_simple(query)
        
        self.show_results(query, response)
    
    def process_nltk(self, query):
        """Process with NLTK"""
        try:
            tokens = word_tokenize(query.lower())
            stop_words = set(stopwords.words('english'))
            keywords = [w for w in tokens if w.isalnum() and w not in stop_words]
            
            if any(w in keywords for w in ['assignment', 'homework', 'hw']):
                return self.search_assignments(keywords)
            elif any(w in keywords for w in ['due', 'deadline']):
                return "\n".join(self.get_upcoming_assignments())
            elif any(w in keywords for w in ['course', 'class']):
                return "\n".join([f"* {c.get('name')}" for c in self.courses])
            else:
                return "Try asking about: assignments, due dates, or courses"
        except:
            return self.process_simple(query)
    
    def process_simple(self, query):
        """Simple keyword search"""
        query_lower = query.lower()
        if 'assignment' in query_lower:
            return self.search_assignments([])
        elif 'due' in query_lower:
            return "\n".join(self.get_upcoming_assignments())
        elif 'course' in query_lower:
            return "\n".join([f"* {c.get('name')}" for c in self.courses])
        return "Try asking about: assignments, due dates, or courses"
    
    def search_assignments(self, keywords):
        """Search assignments"""
        results = []
        for course in self.courses:
            for assignment in self.assignments_cache.get(course.get('id'), []):
                name = assignment.get('name', '').lower()
                if not keywords or any(k in name for k in keywords):
                    results.append(f"* {assignment.get('name')} ({course.get('name')})")
                    if len(results) >= 10:
                        break
        return "\n".join(results) if results else "No assignments found"
    
    def show_results(self, query, response):
        """Show search results"""
        self.clear_content()
        
        tk.Label(self.content_frame, text="Search Results", 
                font=('Arial', 20, 'bold'), bg=self.main_bg, fg='#2C1810').pack(pady=(0, 10))
        tk.Label(self.content_frame, text=f"Query: {query}", 
                font=('Arial', 12, 'italic'), bg=self.main_bg, fg='#6B6B6B').pack(anchor='w', pady=(0, 20))
        tk.Label(self.content_frame, text=response, 
                font=('Arial', 12), bg=self.main_bg, fg='#2C1810', justify='left').pack(anchor='w', pady=10)
        tk.Button(self.content_frame, text="<- Back", command=self.show_dashboard,
                 bg=self.sidebar_color, fg='white', font=('Arial', 11), 
                 padx=15, pady=5).pack(anchor='w', pady=20)


def main():
    root = tk.Tk()
    app = CanvasChatbotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()      