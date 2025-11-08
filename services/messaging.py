"""
Messaging Service
"""

def send_sms(phone_number, message):
    """
    Sends an SMS message to the specified phone number.
    NOTE: This is a placeholder and does not actually send SMS.
    """
    print(f"Sending SMS to {phone_number}: {message}")
    # In a real application, you would integrate with an SMS gateway like Twilio.
    return True

def send_whatsapp(phone_number, message):
    """
    Sends a WhatsApp message to the specified phone number.
    NOTE: This is a placeholder and does not actually send WhatsApp messages.
    """
    print(f"Sending WhatsApp message to {phone_number}: {message}")
    # In a real application, you would integrate with a WhatsApp Business API provider.
    return True
