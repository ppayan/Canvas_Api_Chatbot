# main.py - Entry point for the Canvas API Chatbot (Hybrid Design Prototype)
from Canvas_api import CanvasAPI

def main():
    print("[Canvas] Welcome to the Canvas API Chatbot (Hybrid Design Prototype)!\n")

    base_url = input("Enter your Canvas URL (e.g. https://nmsu.instructure.com): ").strip()
    access_token = input("Enter your Canvas API Access Token: ").strip()

    api = CanvasAPI(base_url, access_token)

    user = api.get_current_user()
    if not user:
        print("\nAuthentication failed. Please check your token or URL.")
        return

    print(f"\nSuccessfully authenticated as: {user.get('name')} (ID: {user.get('id')})")

    # Fetch all courses once at login all is used for authentication and initial data tests
    courses = api.get_courses()
    if not courses:
        print("\n[!] No courses found or an error occurred.")
        return

    while True:
        print("\n[Books] Your Courses:")
        for idx, c in enumerate(courses, start=1):
            name = c.get("name") or f"(id {c.get('id')})"
            print(f"  {idx}. {name} (ID: {c.get('id')})")

        print("\nOptions:")
        print("  [number] - View assignments for that course")
        print("  r - Refresh course list")
        print("  q - Quit\n")

        choice = input("Enter a choice: ").strip().lower()
        if choice == "q":
            print("\n[Bye] Exiting Canvas API chatbot. Goodbye!")
            break
        elif choice == "r":
            print("[Refresh] Refreshing course list...")
            courses = api.get_courses()
            continue

        # If user selects a number
        if choice.isdigit() and 1 <= int(choice) <= len(courses):
            selected = courses[int(choice) - 1]
            course_name = selected.get("name", f"(id {selected.get('id')})")
            course_id = selected.get("id")
            print(f"\n Fetching assignments for: {course_name}...\n")

            assignments = api.get_assignments(course_id)
            if not assignments:
                print("   No assignments found or failed to fetch.\n")
                continue

            for a in assignments:
                name = a.get("name", "Untitled Assignment")
                due = a.get("due_at", "No due date")
                status = "Submitted" if a.get("has_submitted_submissions") else "Not submitted"
                print(f"  * {name}")
                print(f"    Due: {due}")
                print(f"    Status: {status}\n")

        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()