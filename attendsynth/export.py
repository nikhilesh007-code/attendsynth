"""Data exporter supporting CSV, JSON-LD, and Ed-Fi Alliance Standard schemas."""

import csv
import io
import json
from typing import Any, Dict, List


class DataExporter:
    """Exports generated synthetic cohorts to diverse industry-standard data formats."""

    @staticmethod
    def to_csv_students(students: List[Dict[str, Any]]) -> str:
        """Converts student summaries to CSV string."""
        if not students:
            return ""
        output = io.StringIO()
        fieldnames = [
            "student_id",
            "display_name",
            "school_name",
            "grade_level",
            "archetype",
            "attendance_rate",
            "absence_rate",
            "chronic_absenteeism_flag",
            "total_lms_minutes",
            "avg_daily_lms_minutes",
            "assignment_submission_rate",
            "average_quiz_score",
            "composite_risk_score",
            "risk_level",
            "early_warning_trigger_week",
            "recommended_intervention",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for s in students:
            writer.writerow(s)
        return output.getvalue()

    @staticmethod
    def to_csv_daily_records(daily_records: List[Dict[str, Any]]) -> str:
        """Converts daily attendance & engagement logs to CSV string."""
        if not daily_records:
            return ""
        output = io.StringIO()
        fieldnames = [
            "student_id",
            "date",
            "week_number",
            "weekday",
            "attendance_status",
            "lms_active_minutes",
            "lms_logins",
            "assignment_due",
            "submission_status",
            "quiz_given",
            "quiz_score",
            "daily_engagement_score",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in daily_records:
            writer.writerow(r)
        return output.getvalue()

    @staticmethod
    def to_ed_fi_json(cohort_data: Dict[str, Any]) -> str:
        """Transforms synthetic student cohort into an Ed-Fi Alliance 3.x schema compatible structure.
        
        Ed-Fi is the leading data standard in K-12 education, standardizing entities such as:
        - Student
        - StudentSchoolAssociation
        - StudentAttendanceEvent
        - StudentAcademicRecord
        """
        students = cohort_data.get("students", [])
        daily_records = cohort_data.get("daily_records", [])

        ed_fi_students = []
        for s in students:
            ed_fi_students.append({
                "studentUniqueId": s["student_id"],
                "firstName": s.get("first_name", "Synthetic"),
                "lastSurname": s.get("last_name", "Student"),
                "studentSchoolAssociations": [
                    {
                        "schoolReference": {"schoolId": hash(s["school_name"]) % 100000},
                        "entryGradeLevelDescriptor": f"uri://ed-fi.org/GradeLevelDescriptor#{s['grade_level']}th Grade",
                    }
                ],
                "academicIndicators": {
                    "cumulativeGpa": s.get("baseline_gpa"),
                    "chronicAbsenteeismRisk": s.get("chronic_absenteeism_flag"),
                    "riskTier": s.get("risk_level"),
                },
            })

        ed_fi_attendance_events = []
        # Sample or include all attendance events
        for r in daily_records[:1000]:  # Cap sample for payload efficiency if necessary
            status_map = {
                "PRESENT": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#In Attendance",
                "TARDY": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#Tardy",
                "EXCUSED_ABSENCE": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#Excused Absence",
                "UNEXCUSED_ABSENCE": "uri://ed-fi.org/AttendanceEventCategoryDescriptor#Unexcused Absence",
            }
            ed_fi_attendance_events.append({
                "studentReference": {"studentUniqueId": r["student_id"]},
                "eventDate": r["date"],
                "attendanceEventCategoryDescriptor": status_map.get(
                    r["attendance_status"], "uri://ed-fi.org/AttendanceEventCategoryDescriptor#In Attendance"
                ),
                "attendanceEventReason": (
                    "Synthetic System Absence" if "ABSENCE" in r["attendance_status"] else None
                ),
            })

        payload = {
            "schemaVersion": "Ed-Fi-Data-Standard-3.3",
            "sourceSystem": "AttendSynth-AI-Synthetic-Generator",
            "cohortId": cohort_data.get("cohort_id"),
            "district": cohort_data.get("config", {}).get("district_name", "Horizon Metro Public Schools"),
            "students": ed_fi_students,
            "sampleAttendanceEvents": ed_fi_attendance_events,
        }
        return json.dumps(payload, indent=2)

