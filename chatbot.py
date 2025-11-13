#!/usr/bin/env python3
# chatbot.py - Intelligent chatbot for Canvas LMS queries
from datetime import datetime, timezone, timedelta


class CanvasChatBot:
    
    def __init__(self, api, courses, assignments_cache):
        self.api = api
        self.courses = courses
        self.assignments_cache = assignments_cache
    
    def process_query(self, query):
        query_lower = query.lower()
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        if intent == "assignments":
            return self._handle_assignment_query(query_lower)
        elif intent == "grades":
            return self._handle_grade_query(query_lower)
        elif intent == "courses":
            return self._handle_course_query(query_lower)
        elif intent == "help":
            return self._generate_help_response()
        else:
            return self._generate_fallback_response(query)
    
    def _detect_intent(self, query):
        # Define keyword sets for each intent
        assignment_keywords = ['assignment', 'homework', 'hw', 'due', 'deadline', 
                               'submit', 'turn in', 'work on']
        grade_keywords = ['grade', 'score', 'percent', 'graded', 'passing', 
                          'failing', 'gpa', 'doing']
        course_keywords = ['course', 'class', 'taking', 'enrolled']
        help_keywords = ['help', 'can you', 'what can', 'how do']
        
        # Count keyword matches
        assignment_count = sum(1 for kw in assignment_keywords if kw in query)
        grade_count = sum(1 for kw in grade_keywords if kw in query)
        course_count = sum(1 for kw in course_keywords if kw in query)
        help_count = sum(1 for kw in help_keywords if kw in query)
        
        # Determine primary intent
        if help_count > 0:
            return "help"
        elif grade_count > assignment_count and grade_count > course_count:
            return "grades"
        elif assignment_count > course_count:
            return "assignments"
        elif course_count > 0:
            return "courses"
        
        # Context-based guessing
        if any(word in query for word in ['next', 'upcoming', 'soon']):
            return "assignments"
        elif any(word in query for word in ['doing', 'performance']):
            return "grades"
        
        return "unknown"
    
    def _handle_assignment_query(self, query):
        now = datetime.now(timezone.utc)
        
        # Detect time frame
        timeframe, start_time, end_time = self._extract_timeframe(query, now)
        
        # Check for specific course
        specific_course = self._extract_course_name(query)
        
        # Collect matching assignments
        assignments = self._collect_assignments(
            specific_course, start_time, end_time, now
        )
        
        # Generate conversational response
        return self._format_assignment_response(
            assignments, timeframe, specific_course
        )
    
    def _extract_timeframe(self, query, now):
        if 'today' in query:
            return 'today', now, now + timedelta(days=1)
        elif 'tomorrow' in query:
            start = now + timedelta(days=1)
            return 'tomorrow', start, now + timedelta(days=2)
        elif 'this week' in query or 'week' in query:
            return 'this week', now, now + timedelta(days=7)
        else:
            return 'upcoming', now, now + timedelta(days=14)
    
    def _extract_course_name(self, query):
        for course in self.courses:
            course_name = course.get('name', '').lower()
            # Check if full course name is in query
            if course_name in query:
                return course
            # Check if individual words match
            course_words = course_name.split()
            if any(word in query for word in course_words if len(word) > 3):
                return course
        return None
    
    def _collect_assignments(self, specific_course, start_time, end_time, now):
        assignments = []
        
        for course in self.courses:
            # Skip if looking for specific course
            if specific_course and course.get('id') != specific_course.get('id'):
                continue
            
            course_name = course.get('name', '')
            course_id = course.get('id')
            
            for assignment in self.assignments_cache.get(course_id, []):
                due_at = assignment.get('due_at')
                if not due_at:
                    continue
                
                try:
                    due_date = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                except:
                    continue
                
                # Filter by timeframe
                if due_date > now and due_date <= end_time:
                    if start_time and due_date < start_time:
                        continue
                    
                    days_until = (due_date - now).days
                    assignments.append({
                        'name': assignment.get('name'),
                        'course': course_name,
                        'days_until': days_until,
                        'due_date': due_date
                    })
        
        # Sort by due date
        assignments.sort(key=lambda x: x['due_date'])
        return assignments
    
    def _format_assignment_response(self, assignments, timeframe, specific_course):
        if not assignments:
            if specific_course:
                return f"Great news! You don't have any assignments due in {specific_course.get('name')} {timeframe}. You're all caught up!"
            else:
                return f"You don't have any assignments due {timeframe}. Enjoy your free time!"
        
        # Build response
        if len(assignments) == 1:
            a = assignments[0]
            time_str = self._format_time_until(a['days_until'])
            return f"You have 1 assignment {timeframe}: {a['name']} in {a['course']}, due {time_str}."
        
        response = f"You have {len(assignments)} assignments {timeframe}:\n\n"
        for a in assignments[:5]:  # Limit to 5 for readability
            time_str = self._format_time_until(a['days_until'])
            response += f"- {a['name']} ({a['course']}) - due {time_str}\n"
        
        if len(assignments) > 5:
            response += f"\n...and {len(assignments) - 5} more. Check 'View Upcoming Assignments' for the full list!"
        
        return response
    
    def _format_time_until(self, days):
        if days == 0:
            return "today"
        elif days == 1:
            return "tomorrow"
        else:
            return f"in {days} days"
    
    def _handle_grade_query(self, query):
        # Check for specific course
        specific_course = self._extract_course_name(query)
        
        if specific_course:
            return self._get_course_grade(specific_course)
        
        # Check for comparative queries
        if 'lowest' in query or 'worst' in query:
            return self._get_lowest_grade()
        elif 'highest' in query or 'best' in query:
            return self._get_highest_grade()
        elif 'passing' in query or 'failing' in query:
            return self._check_passing_status()
        
        # Default: grade overview
        return self._get_grade_overview()
    
    def _get_course_grade(self, course):
        course_id = course.get('id')
        course_name = course.get('name')
        grade_info = self.api.get_course_grade(course_id)
        
        if grade_info and grade_info.get('current_score') is not None:
            score = grade_info.get('current_score')
            letter = grade_info.get('current_grade', '')
            return f"Your current grade in {course_name} is {score:.1f}% ({letter})."
        else:
            return f"I don't have grade information available for {course_name} yet."
    
    def _get_lowest_grade(self):
        grades = self._collect_all_grades()
        
        if not grades:
            return "I don't have enough grade information yet to determine your lowest grade."
        
        lowest = min(grades, key=lambda x: x['score'])
        return f"Your lowest grade is in {lowest['course']} with {lowest['score']:.1f}% ({lowest['letter']}). You might want to focus some extra effort there!"
    
    def _get_highest_grade(self):
        grades = self._collect_all_grades()
        
        if not grades:
            return "I don't have enough grade information yet to determine your highest grade."
        
        highest = max(grades, key=lambda x: x['score'])
        return f"Your highest grade is in {highest['course']} with {highest['score']:.1f}% ({highest['letter']}). Great work!"
    
    def _check_passing_status(self):
        grades = self._collect_all_grades()
        failing = [g for g in grades if g['score'] < 60]  # 60% is passing threshold
        
        if not grades:
            return "I don't have enough grade information yet to check your passing status."
        
        if not failing:
            return f"Good news! You're passing all {len(grades)} of your courses. Keep up the great work!"
        elif len(failing) == 1:
            f = failing[0]
            return f"You're currently not passing {f['course']} ({f['score']:.1f}%). Consider talking to your professor or getting some tutoring help."
        else:
            courses_list = ", ".join([f"{f['course']} ({f['score']:.1f}%)" for f in failing])
            return f"You're currently not passing {len(failing)} courses: {courses_list}. I recommend reaching out to your professors for help!"
    
    def _get_grade_overview(self):
        grades = self._collect_all_grades()
        
        if not grades:
            return "I don't have grade information available yet. Grades will appear here once your assignments are graded."
        
        avg_score = sum(g['score'] for g in grades) / len(grades)
        response = "Here's your grade overview:\n\n"
        
        for g in grades:
            response += f"- {g['course']}: {g['score']:.1f}% ({g['letter']})\n"
        
        response += f"\nYour average across all courses is {avg_score:.1f}%."
        
        return response
    
    def _collect_all_grades(self):
        grades = []
        for course in self.courses:
            grade_info = self.api.get_course_grade(course.get('id'))
            if grade_info and grade_info.get('current_score') is not None:
                grades.append({
                    'course': course.get('name'),
                    'score': grade_info.get('current_score'),
                    'letter': grade_info.get('current_grade', '')
                })
        return grades
    
    def _handle_course_query(self, query):
        if 'how many' in query or 'list' in query:
            response = f"You're enrolled in {len(self.courses)} courses:\n\n"
            for course in self.courses:
                response += f"- {course.get('name')}\n"
            return response
        else:
            return f"You're currently taking {len(self.courses)} courses. Ask me about specific courses or your grades to learn more!"
    
    def _generate_help_response(self):
        return """I can help you with:

- Assignments - "What's due this week?" or "Show assignments for Math"
- Grades - "What's my grade in Biology?" or "What's my lowest grade?"
- Courses - "What courses am I taking?"

Try asking me something!"""
    
    def _generate_fallback_response(self, query):
        return "I'm not sure what you're asking about. Try asking me about your assignments, grades, or courses. For example: 'What assignments are due this week?' or 'What's my grade in Math?'"
