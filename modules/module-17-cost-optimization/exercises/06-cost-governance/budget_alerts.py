#!/usr/bin/env python3
"""
AWS Budgets and Cost Alerts
Create budgets with automated actions and multi-channel alerting
"""

import boto3
import json
from typing import List, Dict

class BudgetManager:
    """Manage AWS Budgets with alerts and actions"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize AWS clients"""
        self.budgets = boto3.client('budgets', region_name=region)
        self.sts = boto3.client('sts')
        self.sns = boto3.client('sns', region_name=region)
        self.iam = boto3.client('iam')
        self.account_id = self.sts.get_caller_identity()['Account']

    def create_monthly_budget(
        self,
        budget_amount: float,
        budget_name: str = None,
        alert_emails: List[str] = None,
        cost_filters: Dict = None
    ):
        """
        Create monthly cost budget with multiple alert thresholds

        Args:
            budget_amount: Monthly budget limit in USD
            budget_name: Budget name (auto-generated if None)
            alert_emails: List of email addresses for alerts
            cost_filters: Optional cost filters (tags, services, etc.)
        """
        if budget_name is None:
            budget_name = f'Monthly-Budget-{int(budget_amount)}'

        if alert_emails is None:
            alert_emails = ['devops@company.com']

        print("\n💰 Creating AWS Budget")
        print("=" * 60)
        print(f"   Name: {budget_name}")
        print(f"   Amount: ${budget_amount:,.2f}/month")
        print(f"   Alerts: {len(alert_emails)} subscribers")

        # Budget configuration
        budget = {
            'BudgetName': budget_name,
            'BudgetLimit': {
                'Amount': str(budget_amount),
                'Unit': 'USD'
            },
            'TimeUnit': 'MONTHLY',
            'BudgetType': 'COST',
            'CostFilters': cost_filters or {},
            'CostTypes': {
                'IncludeTax': True,
                'IncludeSubscription': True,
                'UseBlended': False,
                'IncludeRefund': False,
                'IncludeCredit': False,
                'IncludeUpfront': True,
                'IncludeRecurring': True,
                'IncludeOtherSubscription': True,
                'IncludeSupport': True,
                'IncludeDiscount': True,
                'UseAmortized': False
            }
        }

        try:
            # Create budget
            self.budgets.create_budget(
                AccountId=self.account_id,
                Budget=budget
            )

            print("\n✅ Budget created successfully!")

            # Create alert thresholds
            self._create_budget_alerts(budget_name, alert_emails, budget_amount)

        except self.budgets.exceptions.DuplicateRecordException:
            print(f"\n⚠️  Budget '{budget_name}' already exists")
            print("   Updating alerts...")
            self._create_budget_alerts(budget_name, alert_emails, budget_amount)
        except Exception as e:
            print(f"\n❌ Error creating budget: {e}")

    def _create_budget_alerts(
        self,
        budget_name: str,
        alert_emails: List[str],
        budget_amount: float
    ):
        """Create multiple alert thresholds for budget"""

        # Alert configurations
        alerts = [
            {
                'threshold': 80,
                'comparison': 'ACTUAL',
                'description': f'WARNING: 80% budget consumed (${budget_amount * 0.8:,.0f})'
            },
            {
                'threshold': 100,
                'comparison': 'ACTUAL',
                'description': f'ALERT: Budget exceeded (${budget_amount:,.0f})'
            },
            {
                'threshold': 120,
                'comparison': 'ACTUAL',
                'description': f'CRITICAL: 120% over budget (${budget_amount * 1.2:,.0f})'
            },
            {
                'threshold': 100,
                'comparison': 'FORECASTED',
                'description': 'FORECAST: Projected to exceed budget this month'
            }
        ]

        print("\n📧 Creating Alert Thresholds:")

        for alert in alerts:
            notification = {
                'NotificationType': alert['comparison'],
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': alert['threshold'],
                'ThresholdType': 'PERCENTAGE',
                'NotificationState': 'ALARM'
            }

            subscribers = [
                {'SubscriptionType': 'EMAIL', 'Address': email}
                for email in alert_emails
            ]

            try:
                self.budgets.create_notification(
                    AccountId=self.account_id,
                    BudgetName=budget_name,
                    Notification=notification,
                    Subscribers=subscribers
                )

                severity_icon = '⚠️' if alert['threshold'] <= 100 else '🚨'
                print(f"   {severity_icon} {alert['threshold']}% ({alert['comparison']})")

            except self.budgets.exceptions.DuplicateRecordException:
                print(f"   ⚠️  Alert {alert['threshold']}% already exists")
            except Exception as e:
                print(f"   ❌ Error creating alert: {e}")

    def create_budget_action(
        self,
        budget_name: str,
        action_threshold: float = 90,
        action_type: str = 'DENY_EC2_LAUNCH',
        approval_required: bool = True
    ):
        """
        Create automated budget action

        Args:
            budget_name: Existing budget name
            action_threshold: Percentage threshold to trigger action
            action_type: Type of action (DENY_EC2_LAUNCH, STOP_EC2_DEV, etc.)
            approval_required: Whether to require manual approval
        """
        print("\n⚡ Creating Budget Action")
        print("=" * 60)
        print(f"   Budget: {budget_name}")
        print(f"   Trigger: {action_threshold}% of budget")
        print(f"   Action: {action_type}")
        print(f"   Approval: {'Required' if approval_required else 'Automatic'}")

        # Create IAM role for budget actions
        role_name = 'BudgetActionRole'

        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "budgets.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }

        try:
            role_response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Role for AWS Budget automated actions'
            )
            role_arn = role_response['Role']['Arn']

            # Attach policy
            self.iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonEC2FullAccess'
            )

            print(f"\n   ✅ IAM role created: {role_name}")

        except self.iam.exceptions.EntityAlreadyExistsException:
            role_arn = f'arn:aws:iam::{self.account_id}:role/{role_name}'
            print(f"\n   ⚠️  IAM role already exists: {role_name}")

        # Define action based on type
        if action_type == 'DENY_EC2_LAUNCH':
            policy_arn = 'arn:aws:iam::aws:policy/AWSBudgetsActions_EC2DenyRunningInstances'
            action_definition = {
                'IamActionDefinition': {
                    'PolicyArn': policy_arn,
                    'Roles': [role_arn]
                }
            }
        else:
            print(f"   ❌ Unknown action type: {action_type}")
            return

        # Create SNS topic for action notifications
        topic_name = 'budget-action-alerts'
        try:
            topic_response = self.sns.create_topic(Name=topic_name)
            topic_arn = topic_response['TopicArn']
            print(f"   ✅ SNS topic: {topic_name}")
        except Exception:
            topic_arn = f'arn:aws:sns:us-east-1:{self.account_id}:{topic_name}'

        # Create budget action
        try:
            response = self.budgets.create_budget_action(
                AccountId=self.account_id,
                BudgetName=budget_name,
                NotificationType='ACTUAL',
                ActionType='APPLY_IAM_POLICY',
                ActionThreshold={
                    'ActionThresholdValue': action_threshold,
                    'ActionThresholdType': 'PERCENTAGE'
                },
                Definition=action_definition,
                ExecutionRoleArn=role_arn,
                ApprovalModel='MANUAL' if approval_required else 'AUTOMATIC',
                Subscribers=[
                    {
                        'SubscriptionType': 'SNS',
                        'Address': topic_arn
                    }
                ]
            )

            action_id = response['ActionId']

            print("\n✅ Budget Action Created!")
            print(f"   Action ID: {action_id}")
            print("\n   📋 Action Details:")
            print(f"      • Threshold: {action_threshold}% of budget")
            print("      • Policy: Deny new EC2 instance launches")
            print(f"      • Approval: {'Manual' if approval_required else 'Automatic'}")
            print(f"      • Notifications: SNS ({topic_name})")

            if approval_required:
                print("\n   ℹ️  Action requires manual approval in AWS Console")
                print("      Actions → Pending Approvals")
            else:
                print("\n   ⚠️  Action executes automatically!")
                print("      Monitor closely to avoid blocking legitimate work")

        except Exception as e:
            print(f"\n❌ Error creating budget action: {e}")

    def list_budgets(self):
        """List all budgets in the account"""
        print("\n📊 AWS Budgets")
        print("=" * 60)

        try:
            response = self.budgets.describe_budgets(AccountId=self.account_id)
            budgets = response.get('Budgets', [])

            if not budgets:
                print("   No budgets found")
                return []

            for budget in budgets:
                name = budget['BudgetName']
                limit = float(budget['BudgetLimit']['Amount'])
                budget_type = budget['BudgetType']
                time_unit = budget['TimeUnit']

                print(f"\n   Budget: {name}")
                print(f"      Type: {budget_type}")
                print(f"      Limit: ${limit:,.2f} ({time_unit})")

            return budgets

        except Exception as e:
            print(f"   ❌ Error listing budgets: {e}")
            return []

    def create_team_budgets(self, teams: Dict[str, float]):
        """
        Create separate budgets for each team

        Args:
            teams: Dict mapping team name to budget amount
        """
        print("\n👥 Creating Team Budgets")
        print("=" * 60)

        for team_name, amount in teams.items():
            budget_name = f'Team-{team_name}-Monthly'
            email = f'{team_name.lower()}@company.com'

            cost_filters = {
                'TagKeyValue': [f'Team${team_name}']
            }

            self.create_monthly_budget(
                budget_amount=amount,
                budget_name=budget_name,
                alert_emails=[email],
                cost_filters=cost_filters
            )

            print(f"\n   ✅ {team_name}: ${amount:,.2f}/month")

def create_sns_topic_with_email(topic_name: str, email_addresses: List[str]) -> str:
    """
    Create SNS topic and subscribe email addresses

    Args:
        topic_name: SNS topic name
        email_addresses: List of email addresses

    Returns:
        Topic ARN
    """
    sns = boto3.client('sns')

    print(f"\n📧 Creating SNS Topic: {topic_name}")

    try:
        # Create topic
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']

        print(f"   ✅ Topic ARN: {topic_arn}")

        # Subscribe emails
        for email in email_addresses:
            sub_response = sns.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )

            print(f"   ✅ Subscribed: {email}")
            print("      (Confirmation required - check email)")

        return topic_arn

    except sns.exceptions.TopicLimitExceededException:
        print("   ⚠️  Topic limit exceeded")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    """Main budget and alerts workflow"""
    print("=" * 70)
    print("AWS Budgets and Cost Alerts Configuration")
    print("=" * 70)

    manager = BudgetManager()

    # 1. Create account-level budget
    print("\n[Step 1/4] Account-Level Budget")
    manager.create_monthly_budget(
        budget_amount=5000,
        budget_name='Account-Monthly-Budget',
        alert_emails=['devops@company.com', 'finance@company.com']
    )

    # 2. Create team-level budgets
    print("\n\n[Step 2/4] Team-Level Budgets")
    teams = {
        'Backend': 1500,
        'Frontend': 800,
        'DataPlatform': 2000,
        'ML': 1200
    }
    manager.create_team_budgets(teams)

    # 3. Create budget action (with manual approval for safety)
    print("\n\n[Step 3/4] Budget Action (Prevent Cost Overruns)")
    manager.create_budget_action(
        budget_name='Account-Monthly-Budget',
        action_threshold=90,
        action_type='DENY_EC2_LAUNCH',
        approval_required=True  # Safer for production
    )

    # 4. List all budgets
    print("\n\n[Step 4/4] Budget Summary")
    budgets = manager.list_budgets()

    # Summary
    print("\n" + "=" * 70)
    print("✅ Budget Configuration Complete!")
    print("=" * 70)

    print("\n💡 Budget Alert Best Practices:")
    print("   1. Set alerts at 80%, 100%, 120% (ACTUAL) + 100% (FORECASTED)")
    print("   2. Use FORECASTED alerts → Prevents surprises 2-3 weeks early")
    print("   3. Start budget actions with MANUAL approval")
    print("   4. Create team/project-level budgets, not just account-level")
    print("   5. Filter by tags (Department, Team, Environment)")

    print("\n⚡ Budget Actions (Automated Responses):")
    print("   • 90% threshold → Deny new EC2 launches (dev/test only)")
    print("   • 100% threshold → Stop all dev/test instances")
    print("   • 110% threshold → Notify executive leadership")

    print("\n📊 Alert Channels:")
    print("   • Email (built-in)")
    print("   • SNS → Slack webhook (custom Lambda)")
    print("   • SNS → PagerDuty (for critical alerts)")
    print("   • SNS → Jira ticket creation (for investigations)")

    print("\n⚠️  Important Warnings:")
    print("   ❗ Budget actions can disrupt workloads")
    print("   ❗ Test in dev/test environments first")
    print("   ❗ Use tag-based conditions to limit scope")
    print("   ❗ Require approval for production actions")

    print("\n📈 Typical Budget Strategy:")
    print("   • Account Budget: $50K/month (total org)")
    print("   • Team Budgets: $5-15K each (10 teams)")
    print("   • Project Budgets: $1-5K (20 projects)")
    print("   • Environment: Dev $10K, Test $8K, Prod $32K")

if __name__ == '__main__':
    main()
