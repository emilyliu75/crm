import html
from imapclient import IMAPClient
import email
from email.header import decode_header
import os
import re
from markupsafe import Markup
import email.utils
import datetime
import smtplib
from email.mime.text import MIMEText
from models import db, EmailLog

def send_and_save_email(subject, html_body, recipient, bcc_recipient):
    sender = os.environ['EMAIL_USER']
    smtp_host = os.environ['EMAIL_HOST']
    smtp_port = int(os.environ.get('EMAIL_PORT', 587))
    smtp_pass = os.environ['IMAP_PASS']

    # Compose message
    msg = MIMEText(html_body, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg['Bcc'] = bcc_recipient

    # 1. Send via SMTP
    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, smtp_pass)
        smtp.sendmail(sender, [recipient, bcc_recipient], msg.as_string())

    # 2. Save to Sent folder via IMAP
    IMAP_HOST = os.environ['IMAP_HOST']
    IMAP_USER = sender  # Your info@ email
    IMAP_PASS = smtp_pass
    SENT_FOLDER = 'INBOX.Sent'  # Might also be 'Sent Mail', 'Sent Items', etc.

    with IMAPClient(IMAP_HOST, ssl=True) as server:
        server.login(IMAP_USER, IMAP_PASS)
        server.append(SENT_FOLDER, msg.as_bytes(), flags=['\\Seen'])
    now = datetime.datetime.utcnow()
    msgid = msg.get('Message-ID') or email.utils.make_msgid()
    try:
        new_log = EmailLog(
            client_email=recipient,
            subject=subject,
            body=html_body,
            from_addr=sender,
            to_addr=recipient,
            date=now,
            folder='INBOX.Sent',
            msgid=msgid
        )
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        print('Failed to save sent email to db:', e)

def safe_decode_header(header_value):
    """Decode an email header into a readable string."""
    if header_value is None:
        return ""
    if isinstance(header_value, bytes):
        try:
            header_value = header_value.decode('utf-8', errors='replace')
        except Exception:
            header_value = header_value.decode('latin1', errors='replace')
    decoded_parts = decode_header(header_value)
    decoded_str = ''
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            try:
                decoded_str += part.decode(encoding or 'utf-8', errors='replace')
            except Exception:
                decoded_str += part.decode('latin1', errors='replace')
        else:
            decoded_str += part
    return decoded_str

def extract_email_body(msg):
    # If multipart, find the best part
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_dispo = str(part.get('Content-Disposition'))
            if content_type == 'text/html' and 'attachment' not in content_dispo:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                try:
                    return payload.decode(charset, errors='replace')
                except Exception:
                    return payload.decode('utf-8', errors='replace')
            elif content_type == 'text/plain' and 'attachment' not in content_dispo:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                try:
                    return payload.decode(charset, errors='replace')
                except Exception:
                    return payload.decode('utf-8', errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or 'utf-8'
        try:
            return payload.decode(charset, errors='replace')
        except Exception:
            return payload.decode('utf-8', errors='replace')
    return ""

def strip_cid_images(body_html):
    clean_html = re.sub(r'<img[^>]+src="cid:[^"]+"[^>]*>', '[Inline image not shown]', body_html)
    return Markup(clean_html)

def fetch_emails_for_client(client_email, folders=None, max_count=50):
    from email.header import decode_header
    import datetime

    if folders is None:
        folders = ['INBOX', 'INBOX.Sent']
    IMAP_HOST = os.environ.get('IMAP_HOST')
    IMAP_USER = os.environ.get('IMAP_USER')  # your info@ email
    IMAP_PASS = os.environ.get('IMAP_PASS')
    IMAP_PORT = int(os.environ.get('IMAP_PORT', 993))
    emails = []

    with IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True) as server:
        server.login(IMAP_USER, IMAP_PASS)
        for folder in folders:
            try:
                server.select_folder(folder)
            except Exception:
                continue
            uids = server.search(['OR', ['TO', client_email], ['FROM', client_email]])
            for uid in reversed(uids[-max_count:]):
                data = server.fetch([uid], ['ENVELOPE', 'RFC822'])
                msg_bytes = data[uid][b'RFC822']
                msg = email.message_from_bytes(msg_bytes)
                envelope = data[uid][b'ENVELOPE']
                # Decode subject
                subject = envelope.subject
                if subject:
                    # If subject is bytes, decode to str first
                    if isinstance(subject, bytes):
                        try:
                            subject_str = subject.decode('utf-8', errors='replace')
                        except Exception:
                            subject_str = subject.decode('latin1', errors='replace')
                    else:
                        subject_str = str(subject)
                    dh = decode_header(subject_str)
                    subject = ''.join(
                        s.decode(enc or 'utf-8', errors='replace') if isinstance(s, bytes) else s
                        for s, enc in dh
                    )
                else:
                    subject = ''
                print(f"Folder: {folder}, found {len(uids)} emails")
                def decode_addr(addr):
                    return addr.mailbox.decode() + '@' + addr.host.decode() if addr else ''
                from_addr = decode_addr(envelope.from_[0]) if envelope.from_ else ''
                to_addr = decode_addr(envelope.to[0]) if envelope.to else ''
                msg_date = envelope.date
                if not msg_date:
                    raw_date = msg.get('Date')
                    if raw_date:
                        try:
                            msg_date = email.utils.parsedate_to_datetime(raw_date)
                        except Exception:
                            msg_date = None
                body = extract_email_body(msg)
                body = strip_cid_images(body)
                msgid = msg.get('Message-ID')
                emails.append({
                    'subject': subject,
                    'from': from_addr,
                    'to': to_addr,
                    'date': msg_date,
                    'body': body,
                    'folder': folder,
                    'msgid': msgid
                })
    # Filter out None dates, sort, and take 50
    since_date = datetime.datetime(2025, 5, 17)
    filtered = [e for e in emails if e['date'] is not None and e['date'] >= since_date ]
    print(f"Folder: {folder} | From: {from_addr} | To: {to_addr} | Subject: {subject} | Date: {msg_date}")


    return sorted(filtered, key=lambda e: e['date'], reverse=True)

def plaintext_to_html(text):
    safe_text = html.escape(text)
    safe_text = safe_text.replace('\n\n', '</p><p>')
    safe_text = safe_text.replace('\n', '<br>')
    return f'<p>{safe_text}</p>'

EMAIL_SIGNATURE = """
<div style="font-family: Arial, Helvetica, sans-serif; color: #000001;">
<table style="width: 281px;">
<tbody>
<tr style="height: 31px;">
<td style="width: 281px; height: 40px;">Kind Regards</td>
</tr>
</tbody>
</table>
</div>
<table border="0" width="500" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td style="padding: 0 9px 0 0; vertical-align: top;" valign="top" width="85"><a href="https://www.divi-design.co.uk" target="_blank" rel="noopener"><img style="width: 85px; moz-border-radius: 0%; khtml-border-radius: 0%; o-border-radius: 0%; webkit-border-radius: 0%; ms-border-radius: 0%; border-radius: 0%;" src="https://i.imgur.com/iDBdCrV.png" alt="Divi-Design" width="85" /></a></td>
<td style="border-left: 2px solid; vertical-align: top; border-color: #0F75BC; padding: 0 0 0 9px;" valign="top">
<table style="line-height: 1.4; font-family: Arial, Helvetica, sans-serif; font-size: 96%; color: #000001;" border="0" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td><span style="font: 1.2em Arial, Helvetica, sans-serif; color: #0f75bc;">Divi Design</span> <span style="font-family: Arial, Helvetica, sans-serif; color: #000001;">&nbsp;&nbsp;</span></td>
</tr>
<tr>
<td style="padding: 5px 0;">
<div style="font-family: Arial, Helvetica, sans-serif; color: #000001;">Architectural Services</div>
</td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">p:&nbsp;</span> <a style="text-decoration: none; font-family: Arial, Helvetica, sans-serif; color: #000001;" href="tel:0203 488 2828">0203 488 2828</a></td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">w:&nbsp;</span> <span style="font-family: Arial, Helvetica, sans-serif;"><a style="text-decoration: none; color: #000001;" href="http://www.divi-design.co.uk" target="_blank" rel="noopener">www.divi-design.co.uk</a></span></td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">e:&nbsp;</span> <a style="text-decoration: none; font-family: Arial, Helvetica, sans-serif; color: #000001;" href="mailto:info@divi-design.co.uk" target="_blank" rel="noopener">info@divi-design.co.uk</a></td>
</tr>
<tr>
<td><span style="font-family: Arial, Helvetica, sans-serif; color: #0f75bc;">a:&nbsp;</span> <span style="font-family: Arial, Helvetica, sans-serif; color: #000001;">124 City Road, EC1V 2NX&nbsp;</span></td>
</tr>
<tr>
<td style="color: #000001; padding: 8px 0 3px 0; display: block;">&nbsp;</td>
</tr>
<tr>
<td>
<table border="0" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td style="font-family: Arial; padding: 0 4px 0 0;"><a class="sc-hzDkRC kpsoyz" style="display: inline-block; padding: 0px; background-color: #0f75bc;" href="https://twitter.com/Divi_Design"><img class="sc-bRBYWo ccSRck" style="background-color: #0f75bc; max-width: 135px; display: block;" src="https://cdn2.hubspot.net/hubfs/53/tools/email-signature-generator/icons/twitter-icon-2x.png" alt="twitter" height="23" /></a></td>
<td style="font-family: Arial; padding: 0 4px 0 0;"><a class="sc-hzDkRC kpsoyz" style="display: inline-block; padding: 0px; background-color: #0f75bc;" href="https://www.instagram.com/divi_design_architecture/"><img class="sc-bRBYWo ccSRck" style="background-color: #0f75bc; max-width: 135px; display: block;" src="https://cdn2.hubspot.net/hubfs/53/tools/email-signature-generator/icons/instagram-icon-2x.png" alt="instagram" height="23" /></a></td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
</td>
</tr>
</tbody>
</table>
<table border="0" width="500" cellspacing="0" cellpadding="0">
<tbody>
<tr>
<td class="s_pixel" colspan="2">&nbsp;</td>
</tr>
<tr>
<td style="line-height: 1px;">&nbsp;</td>
</tr>
</tbody>
</table>
"""


