class Course:
    """Course of a vessel"""

    def __init__(self, course=0):
        self.course = course
        self.prev_course = 0

    def __str__(self):
        return f"<Course: {self.course}>"
