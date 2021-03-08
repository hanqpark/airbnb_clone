import os
import requests
from django.views.generic import FormView, DetailView, UpdateView
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login, logout
from django.core.files.base import ContentFile
from django.contrib import messages
from . import forms, models

# from django.views import View


class LoginView(FormView):

    template_name = "users/login.html"
    form_class = forms.LoginForm
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f"Welcome back {user.first_name}")
        return super().form_valid(form)

    """
    Function Based View에서 사용하는 방법

    def get(self, request):
        form = forms.LoginForm()
        return render(request, "users/login.html", {"form": form})

    def post(self, request):
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse("core:home"))
        return render(request, "users/login.html", {"form": form})
    """


# https://docs.github.com/en/developers/apps/authorizing-oauth-apps
def github_login(request):
    cid = os.environ.get("GH_ID")
    redirect_uri = "http://127.0.0.1:8000/users/login/github/callback"
    return redirect(
        f"https://github.com/login/oauth/authorize?client_id={cid}&redirect_uri={redirect_uri}&scope=read:user"
    )


class GithubException(Exception):
    pass


def github_callback(request):
    try:
        cid = os.environ.get("GH_ID")
        csecret = os.environ.get("GH_SECRET")
        code = request.GET.get("code", None)
        print(code)
        if code is not None:
            token_request = requests.post(
                f"https://github.com/login/oauth/access_token?client_id={cid}&client_secret={csecret}&code={code}",
                headers={"Accept": "application/json"},
            )
            token_json = token_request.json()
            error = token_json.get("error", None)
            if error is not None:
                raise GithubException("Can't get access token")
            else:
                # 이미 Github의 권한을 가지고 있을 때
                access_token = token_json.get("access_token")
                profile_request = requests.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/json",
                    },
                )
                profile_json = profile_request.json()
                username = profile_json.get("login", None)
                if username is not None:
                    # name, email, bio가 비어있을 때를 생각해줘서 문제를 해결해야 한다
                    name = profile_json.get("name")
                    name = username if name is None else name
                    email = profile_json.get("email")
                    email = name if email is None else email
                    bio = profile_json.get("bio")
                    bio = "" if bio is None else bio
                    try:
                        user = models.User.objects.get(email=email)
                        if user.login_method != models.User.LOGIN_GITHUB:
                            raise GithubException(f"Please log in with: {user.login_method}")
                    except models.User.DoesNotExist:
                        user = models.User.objects.create(
                            email=email,
                            first_name=name,
                            username=email,
                            bio=bio,
                            login_method=models.User.LOGIN_GITHUB,
                            email_verified=True,
                        )
                        user.set_unusable_password()
                        user.save()
                    login(request, user)
                    messages.success(request, f"Welcome back {user.first_name}")
                    return redirect(reverse("core:home"))

                else:
                    raise GithubException("Can't get your profile")

        else:
            raise GithubException("Can't get code")
    except GithubException as e:
        messages.error(request, e)
        return redirect(reverse("users:login"))


def kakao_login(request):
    api_key = os.environ.get("KK_KEY")
    redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback"
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={api_key}&redirect_uri={redirect_uri}&response_type=code"
    )


class KakaoException(Exception):
    pass


def kakao_callback(request):
    try:
        code = request.GET.get("code")
        api_key = os.environ.get("KK_KEY")
        redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback"
        token_request = requests.get(
            f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={api_key}&redirect_uri={redirect_uri}&code={code}"
        )
        token_json = token_request.json()
        error = token_json.get("error", None)
        if error is not None:
            raise KakaoException("Can't get authorization code.")
        access_token = token_json.get("access_token")
        profile_request = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_json = profile_request.json()
        kakao_account = profile_json.get("kakao_account", None)
        email = kakao_account.get("email", None)
        if email is None:
            raise KakaoException("Please also give me your email.")
        profile = kakao_account.get("profile", None)
        nickname = profile.get("nickname", None)
        thumbnail_image_url = profile.get("thumbnail_image_url", None)
        try:
            user = models.User.objects.get(email=email)
            if user.login_method != models.User.LOGIN_KAKAO:
                raise KakaoException(f"Please log in with: {user.login_method}")
        except models.User.DoesNotExist:
            user = models.User.objects.create(
                email=email,
                first_name=nickname,
                username=email,
                login_method=models.User.LOGIN_KAKAO,
                email_verified=True,
            )
            user.set_unusable_password()
            user.save()
            if thumbnail_image_url is not None:
                photo_request = requests.get(thumbnail_image_url)
                user.avatar.save(
                    f"{nickname}-avatar",
                    ContentFile(photo_request.content()),
                )
        login(request, user)
        messages.success(request, f"Welcome back {user.first_name}")
        return redirect(reverse("core:home"))
    except KakaoException as e:
        messages.error(request, e)
        return redirect(reverse("users:login"))


def log_out(request):
    logout(request)
    messages.info(request, "See you later")
    return redirect(reverse("core:home"))


class SignUpView(FormView):
    template_name = "users/signup.html"
    form_class = forms.SignUpForm
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        form.save()
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
        user.verify_email()
        return super().form_valid(form)


def complete_verification(request, key):
    try:
        user = models.User.objects.get(email_secret=key)
        user.email_verified = True
        user.save()
        # to do: add success messages.
    except models.User.DoesNotExist:
        # to do: add error messages.
        pass
    return redirect(reverse("core:home"))


class UserProfileView(DetailView):

    model = models.User
    context_object_name = "user_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class UpdateProfileView(UpdateView):

    model = models.User
    template_name = "users/update-profile.html"
    fields = (
        "first_name",
        "last_name",
        "gender",
        "bio",
        "birthdate",
        "language",
        "currency",
    )

    def get_object(self, queryset=None):
        return self.request.user

    # def form_valid(self, form):
    #     email = form.cleaned_data.get("email")
    #     self.object.username = email
    #     self.object.save()
    #     return super().form_valid(form)


class UpdatePasswordView(PasswordChangeView):

    template_name = "users/update-password.html"
