from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from API.Poin.models import Poin
from API.Poin.serializers import getPoin
from API.Tema.models import Tema, TemaUser
from .models import User
from .serializers import UserSerializer
import jwt
import datetime

# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        try:
            user = User.objects.create_user(
                name = request.data["name"],
                email = request.data["email"],
                password = request.data["password"],
                phone = request.data["phone"],
            )
            Poin.objects.create(
                id_user = user.id,
                email = user.email,
                user = user.name,
                poin = 0,
            )
            for x in Tema.objects.all():
                TemaUser.objects.create(
                    id_tema = x.id,
                    tema = x.tema,
                    id_user = user.id,
                    user = user.name,
                    status = "Active" if x.id == 1 else "Not Purchased",
                    purchased = True if x.id == 1 else False,
                    primary1 = x.primary1,
                    primary2 = x.primary2,
                    accent1 = x.accent1,
                    accent2 = x.accent2,
                    mainPicture = x.mainPicture,
                    icon = x.icon,
                    poin = "Free" if x.id == 1 else x.poin
                )
            serializer = UserSerializer(data = user)
            if serializer.is_valid():
                serializer.save()
            return Response(serializer.data)
        except:
            return Response("User already exist")


class LoginView(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email__exact=email).first()

        if user is None:
            raise AuthenticationFailed('User not found!')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')

        payload = {
            'id': str(user.id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret',
                           algorithm='HS256').decode('utf-8')

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token
        }
        return response

class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response


@api_view(["GET"])
def getUser(request):
    token = ""
    jwt_cookie = request.headers.get('Cookie')
    if jwt_cookie:
        cookies = {c.split('=')[0]: c.split('=')[1] for c in jwt_cookie.split('; ')}
        token = cookies.get('jwt')
    else:
        pass
    if not token:
        raise AuthenticationFailed('Unauthenticated!')
    try:
        payload = jwt.decode(token, 'secret', algorithm=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Unauthenticated!')

    user = User.objects.get(id=payload['id'])
    poin = Poin.objects.get(id_user = str(user.id)).poin
    context = {
        "nama":user.name,
        "email":user.email,
        "password":user.password,
        "gambar":user.foto,
        "poin":poin,
    }
    return Response(context)

class ListUser(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer