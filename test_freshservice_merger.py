import unittest
from unittest.mock import patch, Mock
import freshservice_merger

class TestFreshserviceMerger(unittest.TestCase):

    def test_parse_ticket_description(self):
        description = "action: test_action\\nwho: test_user"
        action, who = freshservice_merger.parse_ticket_description(description)
        self.assertEqual(action, "test_action")
        self.assertEqual(who, "test_user")

    def test_group_tickets(self):
        tickets = [
            {"subject": "Test Ticket 1", "description_text": "action: action1\\nwho: user1", "created_at": "2023-01-01T00:00:00Z"},
            {"subject": "Test Ticket 1", "description_text": "action: action1\\nwho: user1", "created_at": "2023-01-02T00:00:00Z"},
            {"subject": "Test Ticket 2", "description_text": "action: action2\\nwho: user2", "created_at": "2023-01-01T00:00:00Z"},
        ]
        grouped_tickets = freshservice_merger.group_tickets(tickets)
        self.assertEqual(len(grouped_tickets), 2)
        self.assertIn(("Test Ticket 1", "action1", "user1"), grouped_tickets)
        self.assertEqual(len(grouped_tickets[("Test Ticket 1", "action1", "user1")]), 2)

    @patch('freshservice_merger.find_and_merge_tickets')
    def test_webhook(self, mock_find_and_merge):
        app = freshservice_merger.app.test_client()
        data = {
            "freshservice_webhook": {
                "ticket": {
                    "id": 1,
                    "subject": "Test Ticket",
                    "description_text": "action: test_action\\nwho: test_user"
                }
            }
        }
        response = app.post('/webhook', json=data)
        self.assertEqual(response.status_code, 200)
        mock_find_and_merge.assert_called_once()

    @patch('freshservice_merger.requests.get')
    @patch('freshservice_merger.merge_tickets')
    def test_find_and_merge_tickets(self, mock_merge_tickets, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tickets": [
                {"id": 2, "subject": "Test Ticket", "description_text": "action: test_action\\nwho: test_user", "created_at": "2023-01-01T00:00:00Z"},
            ]
        }
        mock_get.return_value = mock_response

        new_ticket = {"id": 1, "subject": "Test Ticket", "description_text": "action: test_action\\nwho: test_user", "created_at": "2023-01-02T00:00:00Z"}
        freshservice_merger.find_and_merge_tickets(new_ticket)
        mock_merge_tickets.assert_called_once()

if __name__ == '__main__':
    unittest.main()
