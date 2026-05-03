"""
Command Handler for CQRS

This module handles write operations (commands) and appends events to event store.
Commands are validated before execution (business rules, inventory checks).

Key Features:
1. Command validation (business rules)
2. Event emission (append to event store)
3. Idempotency (duplicate command prevention)
4. Compensating transactions (Saga pattern)
5. Command routing (different handlers per command type)

Author: Training Module 18
"""

import os
import sys
import json
import logging
import argparse
import uuid
from datetime import datetime
from typing import Dict, Optional, Any


# Import event store
sys.path.append(os.path.dirname(__file__))
from event_store import EventStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Handles commands (write operations) for CQRS architecture.

    Validates commands and emits events to event store.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        use_localstack: bool = False
    ):
        """
        Initialize Command Handler.

        Args:
            region: AWS region
            use_localstack: If True, use LocalStack
        """
        self.region = region
        self.event_store = EventStore(use_localstack=use_localstack)

        # Command handlers registry
        self.handlers = {
            'PlaceOrder': self._handle_place_order,
            'ProcessPayment': self._handle_process_payment,
            'ShipOrder': self._handle_ship_order,
            'DeliverOrder': self._handle_deliver_order,
            'CancelOrder': self._handle_cancel_order
        }

        logger.info("CommandHandler initialized")

    def execute_command(
        self,
        command_type: str,
        aggregate_id: str,
        data: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute command.

        Args:
            command_type: Command type (PlaceOrder, CancelOrder, etc.)
            aggregate_id: Aggregate identifier
            data: Command payload
            idempotency_key: Optional key for duplicate detection

        Returns:
            Dict with result
        """
        logger.info(f"⚙️  Executing command: {command_type}")
        logger.info(f"   Aggregate: {aggregate_id}")

        # Check idempotency
        if idempotency_key:
            if self._is_duplicate_command(idempotency_key):
                logger.info("✅ Duplicate command detected (idempotent)")
                return {'status': 'duplicate', 'aggregate_id': aggregate_id}

        # Get command handler
        handler = self.handlers.get(command_type)

        if not handler:
            raise ValueError(f"Unknown command type: {command_type}")

        # Execute handler
        try:
            result = handler(aggregate_id, data)

            # Store idempotency key
            if idempotency_key:
                self._store_idempotency_key(idempotency_key, aggregate_id)

            logger.info(f"✅ Command executed: {command_type}")

            return result

        except Exception as e:
            logger.error(f"❌ Command failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _handle_place_order(
        self,
        order_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle PlaceOrder command.

        Validation:
        - Customer exists and active
        - Items have valid product IDs
        - Amount > 0
        """
        logger.info(f"📝 PlaceOrder: {order_id}")

        # Validate
        if not data.get('customer_id'):
            raise ValueError("customer_id required")

        items = data.get('items', [])
        if not items:
            raise ValueError("items cannot be empty")

        amount = data.get('amount', 0.0)
        if amount <= 0:
            raise ValueError("amount must be positive")

        # Check inventory (simulated)
        for item in items:
            product_id = item['product_id']
            quantity = item.get('quantity', 1)

            if not self._check_inventory(product_id, quantity):
                raise ValueError(f"Insufficient inventory: {product_id}")

        # Emit event
        event_data = {
            'customer_id': data['customer_id'],
            'items': items,
            'amount': amount,
            'order_date': datetime.now().isoformat()
        }

        self.event_store.append_event(
            aggregate_id=order_id,
            event_type='OrderPlaced',
            data=event_data
        )

        return {
            'status': 'success',
            'order_id': order_id,
            'event_type': 'OrderPlaced',
            'amount': amount
        }

    def _handle_process_payment(
        self,
        order_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle ProcessPayment command."""
        logger.info(f"💳 ProcessPayment: {order_id}")

        # Get current state
        state = self.event_store.get_current_state(order_id)

        if state['status'] != 'pending':
            raise ValueError(f"Cannot process payment: order is {state['status']}")

        if state['payment_status'] == 'paid':
            raise ValueError("Payment already processed")

        # Validate payment
        payment_method = data.get('payment_method')
        if payment_method not in ['credit_card', 'debit_card', 'paypal']:
            raise ValueError(f"Invalid payment method: {payment_method}")

        # Emit event
        event_data = {
            'payment_method': payment_method,
            'transaction_id': f"TXN_{uuid.uuid4().hex[:8]}",
            'amount': state['amount']
        }

        self.event_store.append_event(
            aggregate_id=order_id,
            event_type='PaymentProcessed',
            data=event_data
        )

        return {
            'status': 'success',
            'order_id': order_id,
            'event_type': 'PaymentProcessed',
            'transaction_id': event_data['transaction_id']
        }

    def _handle_ship_order(
        self,
        order_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle ShipOrder command."""
        logger.info(f"📦 ShipOrder: {order_id}")

        # Get current state
        state = self.event_store.get_current_state(order_id)

        if state['status'] != 'pending':
            raise ValueError(f"Cannot ship: order is {state['status']}")

        if state['payment_status'] != 'paid':
            raise ValueError("Cannot ship: payment not processed")

        # Emit event
        event_data = {
            'tracking_number': data.get('tracking_number', f"1Z999AA{uuid.uuid4().hex[:12]}"),
            'carrier': data.get('carrier', 'UPS'),
            'shipped_at': datetime.now().isoformat()
        }

        self.event_store.append_event(
            aggregate_id=order_id,
            event_type='OrderShipped',
            data=event_data
        )

        return {
            'status': 'success',
            'order_id': order_id,
            'event_type': 'OrderShipped',
            'tracking_number': event_data['tracking_number']
        }

    def _handle_deliver_order(
        self,
        order_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle DeliverOrder command."""
        logger.info(f"📬 DeliverOrder: {order_id}")

        state = self.event_store.get_current_state(order_id)

        if state['status'] != 'shipped':
            raise ValueError(f"Cannot deliver: order is {state['status']}")

        event_data = {
            'delivered_at': datetime.now().isoformat(),
            'signature': data.get('signature', 'N/A')
        }

        self.event_store.append_event(
            aggregate_id=order_id,
            event_type='OrderDelivered',
            data=event_data
        )

        return {
            'status': 'success',
            'order_id': order_id,
            'event_type': 'OrderDelivered'
        }

    def _handle_cancel_order(
        self,
        order_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle CancelOrder command (compensating transaction)."""
        logger.info(f"❌ CancelOrder: {order_id}")

        state = self.event_store.get_current_state(order_id)

        if state['status'] in ['shipped', 'delivered']:
            raise ValueError(f"Cannot cancel: order already {state['status']}")

        # Emit cancellation event
        event_data = {
            'reason': data.get('reason', 'customer_request'),
            'cancelled_at': datetime.now().isoformat()
        }

        self.event_store.append_event(
            aggregate_id=order_id,
            event_type='OrderCancelled',
            data=event_data
        )

        # If payment was processed, emit refund event
        if state['payment_status'] == 'paid':
            self.event_store.append_event(
                aggregate_id=order_id,
                event_type='RefundIssued',
                data={'amount': state['amount']}
            )

        return {
            'status': 'success',
            'order_id': order_id,
            'event_type': 'OrderCancelled',
            'refund_issued': state['payment_status'] == 'paid'
        }

    def _check_inventory(self, product_id: str, quantity: int) -> bool:
        """Check inventory availability (simulated)."""
        # In production: query inventory service
        return True

    def _is_duplicate_command(self, idempotency_key: str) -> bool:
        """Check if command already executed."""
        # In production: check DynamoDB idempotency table
        return False

    def _store_idempotency_key(self, idempotency_key: str, aggregate_id: str) -> None:
        """Store idempotency key."""
        # In production: write to DynamoDB with TTL (24 hours)
        pass


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='CQRS - Command Handler')

    parser.add_argument(
        '--mode',
        choices=['execute', 'saga-demo'],
        default='execute',
        help='Operation mode'
    )

    parser.add_argument(
        '--env',
        choices=['localstack', 'aws'],
        default='localstack',
        help='Environment'
    )

    parser.add_argument(
        '--command',
        type=str,
        help='Command type'
    )

    parser.add_argument(
        '--aggregate',
        type=str,
        help='Aggregate ID'
    )

    parser.add_argument(
        '--data',
        type=str,
        help='Command data (JSON)'
    )

    args = parser.parse_args()

    # Initialize handler
    handler = CommandHandler(use_localstack=(args.env == 'localstack'))

    if args.mode == 'execute':
        if not (args.command and args.aggregate and args.data):
            logger.error("❌ --command, --aggregate, and --data required")
            sys.exit(1)

        data = json.loads(args.data)

        result = handler.execute_command(
            command_type=args.command,
            aggregate_id=args.aggregate,
            data=data
        )

        print(json.dumps(result, indent=2))

    elif args.mode == 'saga-demo':
        # Demonstrate Saga pattern
        order_id = f"ORD_{uuid.uuid4().hex[:8]}"

        logger.info("=== Saga Pattern Demo ===")
        logger.info(f"   Order: {order_id}")
        logger.info("")

        try:
            # Step 1: Place order
            logger.info("Step 1: PlaceOrder")
            handler.execute_command(
                'PlaceOrder',
                order_id,
                {
                    'customer_id': 'CUST_123',
                    'items': [{'product_id': 'PROD_456', 'quantity': 2}],
                    'amount': 150.00
                }
            )

            # Step 2: Process payment
            logger.info("\nStep 2: ProcessPayment")
            handler.execute_command(
                'ProcessPayment',
                order_id,
                {'payment_method': 'credit_card'}
            )

            # Step 3: Ship order
            logger.info("\nStep 3: ShipOrder")
            handler.execute_command(
                'ShipOrder',
                order_id,
                {'carrier': 'UPS'}
            )

            logger.info("\n✅ Saga completed successfully")

        except Exception as e:
            logger.error(f"\n❌ Saga failed: {e}")
            logger.info("   Executing compensating transactions...")

            # Compensating transaction: Cancel order
            handler.execute_command(
                'CancelOrder',
                order_id,
                {'reason': 'saga_failure'}
            )

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
