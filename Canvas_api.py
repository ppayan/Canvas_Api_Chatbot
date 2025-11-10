# canvas_api.py
import requests

class CanvasAPI:
    def __init__(self, base_url, access_token):
        # Normalize URL
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        # If user passed the full API path, allow either:
        if base_url.endswith("/api/v1"):
            base_url = base_url[:-len("/api/v1")]
        self.base_url = base_url
        self.api_root = f"{self.base_url}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {access_token}"
        }
        # simple cache for last error
        self.last_error = None

    def _get(self, path, params=None):
        url = f"{self.api_root}{path}"
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            if resp.status_code >= 400:
                self.last_error = f"{resp.status_code} - {resp.text}"
                return None
            return resp.json()
        except requests.exceptions.RequestException as e:
            self.last_error = str(e)
            return None

    def get_current_user(self):
        """
        Returns user object for /users/self or None on error.
        """
        data = self._get("/users/self")
        return data

    def get_courses(self, per_page=100, include=None):
        """
        Returns a list of courses the user is enrolled in.
        Uses simple page loop pagination.
        `include` can be a list of include strings (e.g., ['term']).
        """
        courses = []
        page = 1
        params = {"per_page": per_page, "page": page}
        if include:
            # Canvas expects include[]=something for each include
            # requests will encode list correctly if we provide include[] keys
            for i, val in enumerate(include):
                params[f"include[{i}]"] = val

        while True:
            params["page"] = page
            chunk = self._get("/courses", params=params)
            # If error (None) occur, return what we have (or None if empty)
            if chunk is None:
                if not courses:
                    return None
                return courses

            if not isinstance(chunk, list):
                # Unexpected response shape
                break

            courses.extend(chunk)
            if len(chunk) < per_page:
                # Last page (no more results)
                break
            page += 1

        return courses

    def get_assignments(self, course_id, per_page=100):
        """
        Returns a list of assignments for a specific course ID.
        """
        assignments = []
        page = 1
        while True:
            params = {"per_page": per_page, "page": page}
            chunk = self._get(f"/courses/{course_id}/assignments", params=params)
            if chunk is None:
                return None
            if not isinstance(chunk, list) or len(chunk) == 0:
                break
            assignments.extend(chunk)
            if len(chunk) < per_page:
                break
            page += 1
        return assignments
    
    def get_course_grade(self, course_id):
        """
        Returns the current grade for a specific course.
        Gets user's enrollment which includes current_score and current_grade.
        """
        enrollments = self._get(f"/courses/{course_id}/enrollments", 
                               params={"user_id": "self"})
        if enrollments and len(enrollments) > 0:
            enrollment = enrollments[0]
            return {
                'current_score': enrollment.get('grades', {}).get('current_score'),
                'current_grade': enrollment.get('grades', {}).get('current_grade'),
                'final_score': enrollment.get('grades', {}).get('final_score'),
                'final_grade': enrollment.get('grades', {}).get('final_grade')
            }
        return None
    
    def get_assignment_submissions(self, course_id):
        """
        Returns all assignment submissions (with grades) for the current user in a course.
        """
        submissions = self._get(f"/courses/{course_id}/students/submissions", 
                               params={"student_ids": ["self"], "per_page": 100})
        return submissions if submissions else []