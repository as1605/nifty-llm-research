"""
Email notification module using Amazon SES.
"""
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError

from config.settings import settings

class EmailSender:
    """Class for sending emails using Amazon SES."""
    
    def __init__(self):
        """Initialize the email sender."""
        self.ses = boto3.client(
            'ses',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
    
    def send_portfolio_update(
        self,
        selected_stocks: List[str],
        expected_return: float,
        summary: str,
        subject: Optional[str] = None
    ) -> bool:
        """Send portfolio update email.
        
        Args:
            selected_stocks: List of selected stock symbols
            expected_return: Expected portfolio return
            summary: Analysis summary
            subject: Optional email subject
            
        Returns:
            Boolean indicating success
        """
        if subject is None:
            subject = "Weekly Stock Portfolio Update"
        
        # Create the email body
        body_html = f"""
        <html>
        <head></head>
        <body>
            <h2>Weekly Portfolio Recommendation</h2>
            
            <h3>Selected Stocks:</h3>
            <ul>
                {"".join(f"<li>{stock}</li>" for stock in selected_stocks)}
            </ul>
            
            <h3>Expected Monthly Return:</h3>
            <p>{expected_return:.2%}</p>
            
            <h3>Analysis Summary:</h3>
            <p>{summary}</p>
            
            <hr>
            <p><em>This is an automated message from the Nifty Stock Research System.</em></p>
        </body>
        </html>
        """
        
        body_text = f"""
        Weekly Portfolio Recommendation
        
        Selected Stocks:
        {", ".join(selected_stocks)}
        
        Expected Monthly Return:
        {expected_return:.2%}
        
        Analysis Summary:
        {summary}
        
        ---
        This is an automated message from the Nifty Stock Research System.
        """
        
        try:
            response = self.ses.send_email(
                Source=settings.sender_email,
                Destination={
                    'ToAddresses': [settings.recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body_text,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': body_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            return True
            
        except ClientError as e:
            print(f"Error sending email: {e.response['Error']['Message']}")
            return False 