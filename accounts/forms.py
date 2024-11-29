from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField  
import bleach
from .models import Ticket
import magic 
import re
from education.models import Certificate, UserCertificate

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, validators=[EmailValidator()])
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    profile_photo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "profile_photo", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'topic', 'category', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter the title of your issue'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        return bleach.clean(title, tags=[], strip=True)

    def clean_topic(self):
        topic = self.cleaned_data.get('topic')
        return bleach.clean(topic, tags=[], strip=True)

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')

        if not attachment:
            return attachment

        # Check file size
        max_size_mb = 20
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        if attachment.size > max_size_bytes:
            raise ValidationError(f'File size exceeds the {max_size_mb}MB limit.')
        
        allowed_mime_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png'
        ]

        # Check MIME type using python-magic
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(attachment.read(1024))
        attachment.seek(0)

        if mime_type not in allowed_mime_types:
            raise ValidationError('Unsupported file type.')

        # Check for file signatures
        if mime_type == 'image/png':
            png_signature = b'\x89PNG\r\n\x1a\n'
            if attachment.read(8) != png_signature:
                raise ValidationError("Invalid PNG file.")

        elif mime_type == 'image/jpeg':
            jpeg_signature = b'\xff\xd8\xff'
            if not attachment.read(3).startswith(jpeg_signature):
                raise ValidationError("Invalid JPEG file.")

        elif mime_type == 'application/pdf':
            pdf_signature = b'%PDF-'
            if not attachment.read(5).startswith(pdf_signature):
                raise ValidationError("Invalid PDF file.")

        elif mime_type == 'application/msword':
            doc_signature = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
            if not attachment.read(8).startswith(doc_signature):
                raise ValidationError("Invalid DOC file.")

        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            docx_signature = b'PK\x03\x04'  # ZIP file signature
            # Seek to start of the file before checking the signature
            attachment.seek(0)
            if not attachment.read(4).startswith(docx_signature):
                raise ValidationError("Invalid DOCX file.")
            # Reset file pointer to the start for further processing or saving
            attachment.seek(0)

        # Reset file pointer to the start for further processing or saving
        attachment.seek(0)

        return attachment

    def contains_html_or_links(self, text):
        html_regex = re.compile(r'<[^>]+>')
        link_regex = re.compile(r'https?://[^\s]+')
        return bool(html_regex.search(text) or link_regex.search(text))
    captcha = ReCaptchaField()

    
class TicketResponseForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label='Your Response')
    #attachment = forms.FileField(required=False, label='Attach a file')        that part will be modified later, after providing multi file upload (up to 10)



class CertificateValidationForm(forms.Form):
    certificate_id = forms.UUIDField(label="Certificate ID")

class UserCertificateForm(forms.ModelForm):
    # Add a field to choose users
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="Select User")
    certificate = forms.ModelChoiceField(queryset=Certificate.objects.all(), label="Select Certificate")

    class Meta:
        model = UserCertificate
        fields = ['user', 'certificate',  'expiration_date', 'status']