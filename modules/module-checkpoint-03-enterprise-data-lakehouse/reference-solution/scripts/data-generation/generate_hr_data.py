#!/usr/bin/env python3
"""
HR Data Generator for Enterprise Data Lakehouse
Generates synthetic HR domain data including employees, departments, payroll, and attendance.
Writes data to S3 as CSV with PII fields for testing data masking.
"""

import argparse
import csv
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import io

import boto3
from faker import Faker
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HRDataGenerator:
    """Generator for synthetic HR data with PII fields."""

    DEPARTMENTS = [
        'Engineering', 'Product', 'Sales', 'Marketing', 'Finance',
        'Human Resources', 'Operations', 'Customer Success', 'Legal',
        'IT', 'Data Analytics', 'Security', 'Quality Assurance'
    ]

    JOB_TITLES = {
        'Engineering': ['Software Engineer', 'Senior Engineer', 'Tech Lead', 'Engineering Manager', 'Architect'],
        'Product': ['Product Manager', 'Senior PM', 'Product Director', 'Product Owner'],
        'Sales': ['Sales Representative', 'Account Executive', 'Sales Manager', 'VP Sales'],
        'Marketing': ['Marketing Manager', 'Content Writer', 'Marketing Director', 'SEO Specialist'],
        'Finance': ['Financial Analyst', 'Accountant', 'Controller', 'CFO'],
        'Human Resources': ['HR Manager', 'Recruiter', 'HR Director', 'HR Specialist'],
        'Operations': ['Operations Manager', 'Operations Analyst', 'Director of Operations'],
        'Customer Success': ['Customer Success Manager', 'Support Engineer', 'CS Director'],
        'Legal': ['Legal Counsel', 'Paralegal', 'General Counsel'],
        'IT': ['IT Support', 'Systems Administrator', 'IT Manager', 'DevOps Engineer'],
        'Data Analytics': ['Data Analyst', 'Data Scientist', 'Analytics Manager', 'BI Developer'],
        'Security': ['Security Engineer', 'Security Analyst', 'CISO', 'Security Architect'],
        'Quality Assurance': ['QA Engineer', 'QA Lead', 'Test Automation Engineer']
    }

    EMPLOYMENT_TYPES = ['FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERN']

    PERFORMANCE_RATINGS = ['EXCEEDS', 'MEETS', 'NEEDS_IMPROVEMENT', 'UNSATISFACTORY']

    OFFICE_LOCATIONS = [
        'New York, NY', 'San Francisco, CA', 'Seattle, WA', 'Austin, TX',
        'Chicago, IL', 'Boston, MA', 'Denver, CO', 'Atlanta, GA',
        'Los Angeles, CA', 'Portland, OR', 'Remote'
    ]

    def __init__(self, seed: Optional[int] = 42):
        """Initialize the generator with optional seed for reproducibility."""
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

        self.departments_data = []
        self.employees = []
        self.payroll_records = []
        self.attendance_logs = []

    def generate_departments(self) -> List[Dict]:
        """Generate department data."""
        logger.info(f"Generating {len(self.DEPARTMENTS)} departments...")

        departments = []
        for i, dept_name in enumerate(self.DEPARTMENTS, start=1):
            department = {
                'department_id': f'DEPT{i:03d}',
                'department_name': dept_name,
                'budget': round(random.uniform(500000, 5000000), 2),
                'manager_name': self.fake.name(),
                'location': random.choice(self.OFFICE_LOCATIONS),
                'established_date': self.fake.date_between(start_date='-20y', end_date='-1y'),
                'headcount_target': random.randint(10, 200),
                'created_at': datetime.now().isoformat()
            }
            departments.append(department)

        self.departments_data = departments
        logger.info(f"Generated {len(departments)} departments")
        return departments

    def generate_employees(self, num_employees: int = 5000) -> List[Dict]:
        """Generate employee data with PII fields."""
        logger.info(f"Generating {num_employees} employees...")

        if not self.departments_data:
            self.generate_departments()

        employees = []

        for i in range(num_employees):
            # Personal information (PII)
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@company.com"

            # Employment details
            department = random.choice(self.departments_data)
            job_titles = self.JOB_TITLES.get(department['department_name'], ['Employee'])
            job_title = random.choice(job_titles)

            # Salary ranges based on seniority
            if 'Senior' in job_title or 'Lead' in job_title:
                salary = round(random.uniform(120000, 200000), 2)
            elif 'Manager' in job_title or 'Director' in job_title:
                salary = round(random.uniform(140000, 250000), 2)
            elif any(exec in job_title for exec in ['VP', 'Chief', 'CFO', 'CISO']):
                salary = round(random.uniform(200000, 400000), 2)
            elif 'Intern' in job_title:
                salary = round(random.uniform(40000, 60000), 2)
            else:
                salary = round(random.uniform(60000, 120000), 2)

            hire_date = self.fake.date_between(start_date='-15y', end_date='today')

            employee = {
                'employee_id': f'EMP{i+1:06d}',
                'ssn': self.fake.ssn(),  # PII
                'first_name': first_name,  # PII
                'last_name': last_name,  # PII
                'full_name': f"{first_name} {last_name}",  # PII
                'email': email,  # PII
                'phone_number': self.fake.phone_number(),  # PII
                'date_of_birth': self.fake.date_of_birth(minimum_age=22, maximum_age=65).isoformat(),  # PII
                'gender': random.choice(['Male', 'Female', 'Non-binary', 'Prefer not to say']),
                'address': self.fake.street_address(),  # PII
                'city': self.fake.city(),
                'state': self.fake.state_abbr(),
                'zip_code': self.fake.zipcode(),
                'country': 'USA',
                'department_id': department['department_id'],
                'department_name': department['department_name'],
                'job_title': job_title,
                'employment_type': random.choices(
                    self.EMPLOYMENT_TYPES,
                    weights=[0.70, 0.15, 0.10, 0.05]
                )[0],
                'salary': salary,
                'bonus_eligible': random.choices([True, False], weights=[0.60, 0.40])[0],
                'hire_date': hire_date.isoformat(),
                'termination_date': self.fake.date_between(
                    start_date=hire_date,
                    end_date='today'
                ).isoformat() if random.random() < 0.10 else None,
                'status': random.choices(
                    ['ACTIVE', 'ON_LEAVE', 'TERMINATED'],
                    weights=[0.85, 0.05, 0.10]
                )[0],
                'manager_id': f'EMP{random.randint(1, max(1, i//10)):06d}' if i > 0 else None,
                'office_location': random.choice(self.OFFICE_LOCATIONS),
                'emergency_contact_name': self.fake.name(),  # PII
                'emergency_contact_phone': self.fake.phone_number(),  # PII
                'performance_rating': random.choice(self.PERFORMANCE_RATINGS),
                'last_review_date': self.fake.date_between(start_date='-1y', end_date='today').isoformat(),
                'pto_balance': round(random.uniform(0, 30), 1),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            employees.append(employee)

        self.employees = employees
        logger.info(f"Generated {len(employees)} employees")
        return employees

    def generate_payroll_records(self, months_back: int = 24) -> List[Dict]:
        """Generate monthly payroll records for all employees."""
        logger.info(f"Generating payroll records for {months_back} months...")

        if not self.employees:
            logger.warning("No employees generated. Generating employees first.")
            self.generate_employees()

        payroll_records = []
        end_date = datetime.now()

        for month_offset in range(months_back):
            payroll_date = end_date - timedelta(days=30 * month_offset)
            payroll_period = payroll_date.strftime('%Y-%m')

            for emp in self.employees:
                hire_date = datetime.fromisoformat(emp['hire_date'])
                termination_date = datetime.fromisoformat(emp['termination_date']) if emp['termination_date'] else None

                # Skip if employee wasn't employed during this period
                if payroll_date < hire_date:
                    continue
                if termination_date and payroll_date > termination_date:
                    continue

                # Calculate gross pay
                monthly_salary = emp['salary'] / 12

                # Add bonus for some months
                bonus = round(random.uniform(0, emp['salary'] * 0.1), 2) if random.random() < 0.15 else 0.0

                # Calculate deductions
                federal_tax = round(monthly_salary * random.uniform(0.18, 0.24), 2)
                state_tax = round(monthly_salary * random.uniform(0.04, 0.08), 2)
                social_security = round(monthly_salary * 0.062, 2)
                medicare = round(monthly_salary * 0.0145, 2)
                health_insurance = round(random.uniform(200, 600), 2)
                retirement_401k = round(monthly_salary * random.uniform(0.03, 0.08), 2)

                gross_pay = monthly_salary + bonus
                total_deductions = federal_tax + state_tax + social_security + medicare + health_insurance + retirement_401k
                net_pay = gross_pay - total_deductions

                payroll_record = {
                    'payroll_id': f"PAY{emp['employee_id']}{payroll_date.strftime('%Y%m')}",
                    'employee_id': emp['employee_id'],
                    'pay_period': payroll_period,
                    'pay_date': payroll_date.date().isoformat(),
                    'gross_pay': round(gross_pay, 2),
                    'base_salary': round(monthly_salary, 2),
                    'bonus': bonus,
                    'overtime_pay': 0.0,  # Could be enhanced
                    'federal_tax': federal_tax,
                    'state_tax': state_tax,
                    'social_security': social_security,
                    'medicare': medicare,
                    'health_insurance': health_insurance,
                    'retirement_401k': retirement_401k,
                    'other_deductions': 0.0,
                    'total_deductions': round(total_deductions, 2),
                    'net_pay': round(net_pay, 2),
                    'payment_method': random.choice(['DIRECT_DEPOSIT', 'CHECK']),
                    'bank_account_last4': self.fake.numerify(text='####'),  # PII
                    'created_at': datetime.now().isoformat()
                }
                payroll_records.append(payroll_record)

        self.payroll_records = payroll_records
        logger.info(f"Generated {len(payroll_records)} payroll records")
        return payroll_records

    def generate_attendance_logs(self, days_back: int = 90) -> List[Dict]:
        """Generate attendance logs for employees."""
        logger.info(f"Generating attendance logs for {days_back} days...")

        if not self.employees:
            logger.warning("No employees generated. Generating employees first.")
            self.generate_employees()

        attendance_logs = []
        end_date = datetime.now()

        # Filter active employees
        active_employees = [emp for emp in self.employees if emp['status'] == 'ACTIVE']

        for day_offset in range(days_back):
            log_date = end_date - timedelta(days=day_offset)

            # Skip weekends
            if log_date.weekday() >= 5:
                continue

            for emp in active_employees:
                # 90% attendance rate
                if random.random() < 0.90:
                    # Generate clock in/out times
                    clock_in_hour = random.randint(7, 10)
                    clock_in_minute = random.randint(0, 59)
                    clock_in = log_date.replace(hour=clock_in_hour, minute=clock_in_minute, second=0)

                    # Work duration between 7-10 hours
                    work_hours = random.uniform(7, 10)
                    clock_out = clock_in + timedelta(hours=work_hours)

                    # Break time
                    break_minutes = random.randint(30, 60)

                    attendance = {
                        'attendance_id': f"ATT{emp['employee_id']}{log_date.strftime('%Y%m%d')}",
                        'employee_id': emp['employee_id'],
                        'date': log_date.date().isoformat(),
                        'clock_in': clock_in.isoformat(),
                        'clock_out': clock_out.isoformat(),
                        'total_hours': round(work_hours, 2),
                        'break_minutes': break_minutes,
                        'status': random.choices(
                            ['PRESENT', 'LATE', 'HALF_DAY'],
                            weights=[0.85, 0.10, 0.05]
                        )[0],
                        'work_location': random.choice(['OFFICE', 'REMOTE', 'CLIENT_SITE']),
                        'notes': self.fake.sentence(nb_words=5) if random.random() < 0.1 else '',
                        'created_at': datetime.now().isoformat()
                    }
                else:
                    # Absent
                    attendance = {
                        'attendance_id': f"ATT{emp['employee_id']}{log_date.strftime('%Y%m%d')}",
                        'employee_id': emp['employee_id'],
                        'date': log_date.date().isoformat(),
                        'clock_in': None,
                        'clock_out': None,
                        'total_hours': 0.0,
                        'break_minutes': 0,
                        'status': random.choice(['SICK', 'PTO', 'ABSENT']),
                        'work_location': None,
                        'notes': random.choice(['Sick leave', 'Vacation', 'Personal day', '']),
                        'created_at': datetime.now().isoformat()
                    }

                attendance_logs.append(attendance)

        self.attendance_logs = attendance_logs
        logger.info(f"Generated {len(attendance_logs)} attendance logs")
        return attendance_logs

    def write_to_csv_local(self, output_dir: str):
        """Write generated data to local CSV files."""
        logger.info(f"Writing HR data to local directory: {output_dir}")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write departments
        with open(output_path / 'departments.csv', 'w', newline='', encoding='utf-8') as f:
            if self.departments_data:
                writer = csv.DictWriter(f, fieldnames=self.departments_data[0].keys())
                writer.writeheader()
                writer.writerows(self.departments_data)
        logger.info(f"Wrote {len(self.departments_data)} departments")

        # Write employees
        with open(output_path / 'employees.csv', 'w', newline='', encoding='utf-8') as f:
            if self.employees:
                writer = csv.DictWriter(f, fieldnames=self.employees[0].keys())
                writer.writeheader()
                writer.writerows(self.employees)
        logger.info(f"Wrote {len(self.employees)} employees")

        # Write payroll records
        with open(output_path / 'payroll_records.csv', 'w', newline='', encoding='utf-8') as f:
            if self.payroll_records:
                writer = csv.DictWriter(f, fieldnames=self.payroll_records[0].keys())
                writer.writeheader()
                writer.writerows(self.payroll_records)
        logger.info(f"Wrote {len(self.payroll_records)} payroll records")

        # Write attendance logs
        with open(output_path / 'attendance_logs.csv', 'w', newline='', encoding='utf-8') as f:
            if self.attendance_logs:
                writer = csv.DictWriter(f, fieldnames=self.attendance_logs[0].keys())
                writer.writeheader()
                writer.writerows(self.attendance_logs)
        logger.info(f"Wrote {len(self.attendance_logs)} attendance logs")

    def write_to_s3(self, s3_bucket: str, s3_prefix: str = 'raw/hr'):
        """Write generated data to S3 as CSV."""
        logger.info(f"Writing HR data to S3: s3://{s3_bucket}/{s3_prefix}")

        try:
            s3_client = boto3.client('s3')

            # Helper function to write CSV to S3
            def write_csv_to_s3(data: List[Dict], key: str):
                if not data:
                    return

                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

                s3_client.put_object(
                    Bucket=s3_bucket,
                    Key=key,
                    Body=output.getvalue().encode('utf-8'),
                    ContentType='text/csv'
                )

            # Write each dataset
            write_csv_to_s3(self.departments_data, f"{s3_prefix}/departments/departments.csv")
            logger.info(f"Wrote {len(self.departments_data)} departments to S3")

            write_csv_to_s3(self.employees, f"{s3_prefix}/employees/employees.csv")
            logger.info(f"Wrote {len(self.employees)} employees to S3")

            write_csv_to_s3(self.payroll_records, f"{s3_prefix}/payroll/payroll_records.csv")
            logger.info(f"Wrote {len(self.payroll_records)} payroll records to S3")

            write_csv_to_s3(self.attendance_logs, f"{s3_prefix}/attendance/attendance_logs.csv")
            logger.info(f"Wrote {len(self.attendance_logs)} attendance logs to S3")

        except ClientError as e:
            logger.error(f"Error writing to S3: {e}")
            raise


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic HR data for Enterprise Data Lakehouse'
    )

    parser.add_argument(
        '--employees',
        type=int,
        default=5000,
        help='Number of employee records to generate (default: 5000)'
    )

    parser.add_argument(
        '--payroll-months',
        type=int,
        default=24,
        help='Number of months of payroll history (default: 24)'
    )

    parser.add_argument(
        '--attendance-days',
        type=int,
        default=90,
        help='Number of days of attendance logs (default: 90)'
    )

    parser.add_argument(
        '--output-path',
        type=str,
        default='./data/hr',
        help='Local output path for generated data'
    )

    parser.add_argument(
        '--s3-bucket',
        type=str,
        help='S3 bucket name for output (if not specified, writes to local only)'
    )

    parser.add_argument(
        '--s3-prefix',
        type=str,
        default='raw/hr',
        help='S3 key prefix (default: raw/hr)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()

    # Initialize generator
    logger.info("Initializing HR Data Generator...")
    generator = HRDataGenerator(seed=args.seed)

    # Generate data
    generator.generate_departments()
    generator.generate_employees(num_employees=args.employees)
    generator.generate_payroll_records(months_back=args.payroll_months)
    generator.generate_attendance_logs(days_back=args.attendance_days)

    # Write to local
    generator.write_to_csv_local(args.output_path)

    # Write to S3 if bucket specified
    if args.s3_bucket:
        generator.write_to_s3(args.s3_bucket, args.s3_prefix)

    logger.info("HR data generation completed successfully!")
    logger.info(f"Generated: {len(generator.departments_data)} departments, "
                f"{len(generator.employees)} employees, "
                f"{len(generator.payroll_records)} payroll records, "
                f"{len(generator.attendance_logs)} attendance logs")


if __name__ == '__main__':
    main()
