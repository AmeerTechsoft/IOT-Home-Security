import RPi.GPIO as GPIO
import time
import picamera
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import datetime
from telegram import Bot
import asyncio
import socket
import requests

# Configure email settings
email_sender = 'IOT HOME Security Intruder Alert!'
email_receiver = 'raspberriespi2023@gmail.com'
email_subject = 'Intruder Alert - Video Capture'
email_body = 'A security alert has been triggered. Please check the attached video.'

# Configure Telegram settings
bot = Bot(token='6691527278:AAG8aVTKgrkrxhu3YhXvSE3pR7FkjSp-xhs')  # Replace with your Telegram bot token
chat_ids = ['1167573774', '5062032818']



# Configure camera settings
video_duration = 5  # Duration of the captured video in seconds

# Initialize the PIR sensor and camera
pir_pin = 17  # GPIO pin connected to the PIR sensor
camera = picamera.PiCamera()

def capture_video():
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f'security_video_{current_datetime}.h264'
    mp4_filename = f'security_video_{current_datetime}.mp4'
    
    # Set recording resolution to 720p (1280x720)
    camera.resolution = (1280, 720)
    
    camera.start_recording(filename)
    time.sleep(video_duration)
    camera.stop_recording()

    # Convert the captured video to MP4 format
    os.system(f'MP4Box -add {filename} {mp4_filename}')
    os.remove(filename)

    return mp4_filename

def send_email(filename):
    # def send_email(filename):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_receiver
    msg['Subject'] = email_subject

    # Add email body
    msg.attach(MIMEText(email_body, 'plain'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(filename, 'rb').read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(part)

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'osenioluwaseyidavid@gmail.com'
    smtp_password = 'bocfucbtqyzxrbaz'

    for retry in range(3):
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.sendmail(email_sender, email_receiver, msg.as_string())
                print("Email sent successfully.")
                break
            except smtplib.SMTPException as e:
                print(f"Failed to send email. Error: {e}")
                time.sleep(5)  # Wait for 5 seconds before retrying

async def send_telegram_alert(bot, chat_ids, video_filename):
    message = "URGENT: Security Alert - A Video clip has been sent here and to th eOwner Email."
    
    for retry in range(3):
        try:
            for chat_id in chat_ids:
                await bot.send_message(chat_id = chat_id, text=message)
                with open(video_filename, 'rb') as video_file:
                    await bot.send_video(chat_id=chat_id, video=video_file)
                print("Telegram alert sent successfully.")
            break
        except requests.RequestException as e:
            print(f"Failed to send Telegram alert. Error: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying
            
            
def check_internet_connection():
    try:
        # Use Google DNS (8.8.8.8) to check internet connectivity
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

# Main loop
def main_loop():
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pir_pin, GPIO.IN)

        while True:
            if GPIO.input(pir_pin):
                print("Motion detected!")
                video_filename = capture_video()

                if check_internet_connection():
                    asyncio.run(send_telegram_alert(bot, chat_ids, video_filename))
                    send_email(video_filename)
                else:
                    print("Network is unavailable. Saving data locally.")
                    # Save the video and alerts to a local directory for later delivery.

                storage_directory = '/home/ameer/Home_security/videos'  # Replace with your desired directory path
                os.rename(video_filename, os.path.join(storage_directory, video_filename))

                time.sleep(15)  # Delay to avoid repeated detections
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_loop())
