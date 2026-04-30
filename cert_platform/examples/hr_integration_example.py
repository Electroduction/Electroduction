"""
Example: HR Integration with AI CertPro Platform
Demonstrates how to integrate the certification platform with HR systems
"""

import requests
import json
from typing import List, Dict

class CertProHRIntegration:
    """
    Example class showing how HR teams can integrate with the AI CertPro platform
    """

    def __init__(self, api_base_url: str = "http://localhost:5000/api"):
        self.api_base = api_base_url
        self.company_id = "acme_corp"  # Your company ID

    def analyze_workforce_gaps(self, current_skills: List[str], required_skills: List[str]) -> Dict:
        """
        Analyze skill gaps in your workforce

        Example:
            current = ["Python", "Excel", "SQL"]
            required = ["Machine Learning", "TensorFlow", "AWS", "Docker"]
            gaps = integration.analyze_workforce_gaps(current, required)
        """
        response = requests.post(
            f"{self.api_base}/hr/workforce-analysis",
            json={
                "company_id": self.company_id,
                "current_skills": current_skills,
                "required_skills": required_skills
            }
        )

        if response.status_code == 200:
            analysis = response.json()
            print(f"\n📊 Workforce Gap Analysis")
            print(f"   Identified Gaps: {', '.join(analysis['gaps'])}")
            print(f"   Recommended Programs: {len(analysis['recommended_programs'])}")

            for program in analysis['recommended_programs']:
                print(f"\n   ✓ {program['name']}")
                print(f"     Duration: {program['duration']}")
                print(f"     Key Skills: {', '.join(program['key_skills'][:3])}")

            return analysis
        else:
            print(f"❌ Error: {response.status_code}")
            return {}

    def deploy_training(self, program_ids: List[str], employee_ids: List[int],
                       deadline: str = None) -> Dict:
        """
        Deploy training programs to employees

        Example:
            result = integration.deploy_training(
                program_ids=["it_software", "cybersecurity"],
                employee_ids=[101, 102, 103, 104, 105],
                deadline="2026-06-30"
            )
        """
        response = requests.post(
            f"{self.api_base}/hr/deploy-training",
            json={
                "company_id": self.company_id,
                "program_ids": program_ids,
                "employee_ids": employee_ids,
                "deadline": deadline
            }
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Training Deployed Successfully")
            print(f"   Deployment ID: {result['deployment_id']}")
            print(f"   Employees Enrolled: {len(result['enrollments'])}")
            print(f"   Programs: {', '.join(program_ids)}")

            return result
        else:
            print(f"❌ Error: {response.status_code}")
            return {}

    def enroll_employee(self, name: str, email: str, program_id: str,
                       prior_knowledge: Dict = None) -> Dict:
        """
        Enroll a single employee in a program

        Example:
            employee = integration.enroll_employee(
                name="Jane Smith",
                email="jane.smith@acme.com",
                program_id="cybersecurity",
                prior_knowledge={
                    "years_experience": 3,
                    "education_level": "bachelors",
                    "related_skills": ["networking", "linux"]
                }
            )
        """
        if prior_knowledge is None:
            prior_knowledge = {}

        response = requests.post(
            f"{self.api_base}/enroll",
            json={
                "name": name,
                "email": email,
                "program_id": program_id,
                "company": self.company_id,
                "prior_knowledge": prior_knowledge
            }
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Employee Enrolled")
            print(f"   Student ID: {result['student_id']}")
            print(f"   Program: {program_id}")

            return result
        else:
            print(f"❌ Error: {response.status_code}")
            return {}

    def get_employee_progress(self, student_id: int) -> Dict:
        """
        Get an employee's training progress

        Example:
            progress = integration.get_employee_progress(student_id=123)
        """
        response = requests.get(f"{self.api_base}/progress/{student_id}")

        if response.status_code == 200:
            progress = response.json()
            print(f"\n📈 Employee Progress")
            print(f"   Student ID: {student_id}")
            print(f"   Overall Completion: {progress['completion_percentage']}%")

            for program in progress['programs']:
                print(f"\n   Program: {program['program_id']}")
                print(f"   Completed: {program['completed_lessons']}/{program['total_lessons']} lessons")
                print(f"   Progress: {program['completion_percentage']}%")

            return progress
        else:
            print(f"❌ Error: {response.status_code}")
            return {}

    def bulk_enroll_from_csv(self, csv_file_path: str, program_id: str):
        """
        Bulk enroll employees from a CSV file

        CSV Format:
        name,email,years_experience,education_level
        John Doe,john@acme.com,5,bachelors
        Jane Smith,jane@acme.com,3,masters
        """
        import csv

        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            enrolled = 0

            for row in reader:
                prior_knowledge = {
                    "years_experience": int(row.get('years_experience', 0)),
                    "education_level": row.get('education_level', 'none')
                }

                result = self.enroll_employee(
                    name=row['name'],
                    email=row['email'],
                    program_id=program_id,
                    prior_knowledge=prior_knowledge
                )

                if result:
                    enrolled += 1

            print(f"\n✅ Bulk Enrollment Complete")
            print(f"   Total Enrolled: {enrolled}")

    def get_all_programs(self) -> List[Dict]:
        """Get list of all available programs"""
        response = requests.get(f"{self.api_base}/programs")

        if response.status_code == 200:
            programs = response.json()
            print(f"\n📚 Available Programs: {len(programs)}")

            for program in programs:
                print(f"\n   {program['name']}")
                print(f"   ID: {program['id']}")
                print(f"   Duration: {program['duration']}")

            return programs
        else:
            print(f"❌ Error: {response.status_code}")
            return []


# Example Usage
if __name__ == "__main__":
    # Initialize integration
    integration = CertProHRIntegration()

    print("=" * 60)
    print("AI CertPro HR Integration Example")
    print("=" * 60)

    # Example 1: Analyze workforce gaps
    print("\n📊 Example 1: Workforce Gap Analysis")
    print("-" * 60)

    current_skills = ["Python", "Excel", "SQL", "PowerPoint"]
    required_skills = ["Machine Learning", "TensorFlow", "AWS", "Docker", "Kubernetes"]

    gaps = integration.analyze_workforce_gaps(current_skills, required_skills)

    # Example 2: Get all programs
    print("\n" + "=" * 60)
    print("📚 Example 2: Browse Available Programs")
    print("-" * 60)

    programs = integration.get_all_programs()

    # Example 3: Enroll single employee
    print("\n" + "=" * 60)
    print("👤 Example 3: Enroll Single Employee")
    print("-" * 60)

    employee = integration.enroll_employee(
        name="Jane Smith",
        email="jane.smith@acme.com",
        program_id="cybersecurity",
        prior_knowledge={
            "years_experience": 3,
            "education_level": "bachelors",
            "related_skills": ["networking", "linux", "security awareness"]
        }
    )

    # Example 4: Deploy training to multiple employees
    print("\n" + "=" * 60)
    print("🚀 Example 4: Deploy Training to Team")
    print("-" * 60)

    deployment = integration.deploy_training(
        program_ids=["it_software", "cybersecurity"],
        employee_ids=[101, 102, 103, 104, 105],
        deadline="2026-06-30"
    )

    # Example 5: Check employee progress
    if employee:
        print("\n" + "=" * 60)
        print("📈 Example 5: Check Employee Progress")
        print("-" * 60)

        progress = integration.get_employee_progress(employee['student_id'])

    print("\n" + "=" * 60)
    print("✅ Examples Complete!")
    print("=" * 60)
