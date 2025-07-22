from models import EmailLog, db
from utils import fetch_emails_for_client
from models import Client

def poll_and_store_incoming():
    all_clients = Client.query.all()
    for client in all_clients:
        emails = fetch_emails_for_client(client.email, folders=['INBOX', 'INBOX.Sent'], max_count=50)
        for email in emails:
            if not EmailLog.query.filter_by(msgid=email['msgid']).first():
                log = EmailLog(
                    client_email=client.email,
                    subject=email.get('subject', ''),
                    body=email.get('body', ''),
                    from_addr=email.get('from', ''),
                    to_addr=email.get('to', ''),
                    folder=email.get('folder', ''),
                    msgid=email['msgid']
                )
                db.session.add(log)
    db.session.commit()

if __name__ == "__main__":
    poll_and_store_incoming()
    print("Polling and storing incoming emails completed.")