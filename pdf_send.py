import os
import constants as c

from pypdf import PdfReader, PdfWriter

import smtplib
from email.message import EmailMessage

from datetime import datetime


def create_pdf(values: dict, template_file: str, out_path: str):

    out_file_name = f"{values['%NAME%']} {values['%NUMBER%']} {values['%DATE%']}.pdf"
    out_file = f"{out_path}/{out_file_name}"

    try:
        reader = PdfReader(template_file)
        writer = PdfWriter()

        writer.append(reader)
        writer.update_page_form_field_values(writer.pages[0], values)

        with open(out_file, "wb") as output_stream:
            writer.write(output_stream)

    except Exception as exc:
        return False, None

    return True, out_file


def send_pdf(pdf_file: str, from_email: str, to_email: str, login: str, password: str):

    file_name = os.path.basename(pdf_file)

    try:
        msg = EmailMessage()
        msg['Subject'] = 'ЗАЯВКА НА ВРЕМЕННЫЙ ПРОПУСК'
        msg['From'] = from_email
        msg['To'] = to_email
        msg.preamble = 'NEOWELL\n'

        with open(pdf_file, 'rb') as f:
            data = f.read()

        msg.add_attachment(data, subtype='pdf', maintype='file', filename=file_name)

        server = smtplib.SMTP_SSL(c.SMTP_ADDRESS, c.SMTP_PORT)
        server.login(login, password)
        server.sendmail(from_email, to_email, msg.as_bytes())
        server.quit()

    except Exception as exc:
        return False

    return True


def procedure(out_path: str, template_file: str, values: dict):

    r, pdf_file = create_pdf(values, template_file, out_path)
    if not r:
        return

    from_email = c.FROM_EMAIL
    to_email = c.TO_EMAIL

    login = from_email
    password = c.EMAIL_PASS

    r = send_pdf(pdf_file, from_email, to_email, login, password)
    if not r:
        return


def run_procedure(template_file: str, values: dict):

    now = datetime.now().strftime("%d_%m_%Y_%H_%M_%S_%f")
    out_path = f"./tmp/{now}"
    os.makedirs(out_path)

    procedure(out_path, template_file, values)

    for file in os.listdir(out_path):
        os.remove(f"{out_path}/{file}")
    os.rmdir(out_path)


def send_mail(number: str, name: str, reason: str, date: str):

    template_file = './pdf/template.pdf'

    values = {'%NAME%': name,
              '%NUMBER%': number,
              '%REASON%': reason,
              '%DATE%': date}

    run_procedure(template_file, values)
