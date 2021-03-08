import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls.base import reverse
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string

# Create your models here.
class User(AbstractUser):

    """ Custom User Model """

    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_OTHER = "other"
    GENDER_CHOICES = ((GENDER_MALE, "Male"), (GENDER_FEMALE, "Female"), (GENDER_OTHER, "Other"))

    LANGUAGE_ENGLISH = "en"
    LANGUAGE_KOREAN = "kr"
    LANGUAGE_JAPANESE = "jp"
    LANGUAGE_CHOICES = (
        (LANGUAGE_ENGLISH, "English"),
        (LANGUAGE_KOREAN, "Korean"),
        (LANGUAGE_JAPANESE, "Japanese"),
    )

    CURRENCY_USD = "usd"
    CURRUNCY_KRW = "krw"
    CURRENCY_JPY = "jpy"
    CURRENCY_CHOICES = (
        (CURRENCY_USD, "USD"),
        (CURRUNCY_KRW, "KRW"),
        (CURRENCY_JPY, "JPY"),
    )

    LOGIN_EMAIL = "email"
    LOGIN_GITHUB = "github"
    LOGIN_KAKAO = "kakao"
    LOGIN_CHOICES = (
        (LOGIN_EMAIL, "Email"),
        (LOGIN_GITHUB, "Github"),
        (LOGIN_KAKAO, "Kakao"),
    )

    # default 대신 null=True를 넣어주어도 됨. SQL 특성상 비어있으면 안되기 때문에 default를 설정해주거나 null값을 줌
    # null과 함계 blank도 허용해줘야 빈 칸으로 둘 수 있다.
    avatar = models.ImageField(upload_to="avatars", blank=True)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=10, blank=True)
    bio = models.TextField(blank=True)
    birthdate = models.DateField(blank=True, null=True)
    language = models.CharField(
        choices=LANGUAGE_CHOICES, max_length=10, blank=True, default=LANGUAGE_KOREAN
    )
    currency = models.CharField(
        choices=CURRENCY_CHOICES, max_length=10, blank=True, default=CURRUNCY_KRW
    )
    superhost = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_secret = models.CharField(max_length=120, default="", blank=True)
    login_method = models.CharField(max_length=50, choices=LOGIN_CHOICES, default=LOGIN_EMAIL)

    def verify_email(self):
        if self.email_verified is False:
            secret = uuid.uuid4().hex[:20]
            self.email_secret = secret
            html_message = render_to_string(
                "emails/verify_email.html",
                {"secret": secret},
            )
            send_mail(
                "Verify Airbnb Account",
                strip_tags(html_message),  # TEXT를 HTML로 바꿔주기 위해서 사용한다.
                settings.EMAIL_FROM,
                [self.email],
                fail_silently=False,
                html_message=html_message,  # 링크를 보내주기 위해 넣어줘야하는 필수 옵션
            )
            self.save()
        return

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("users:profile", kwargs={"pk": self.pk})
