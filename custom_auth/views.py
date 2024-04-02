from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
import random
import requests
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import SMSSerializer, VerifySMSSerializer, CreateSerializer
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model

User = get_user_model()

SMS_KEY = settings.SMS_KEY


class SMSLoginViewSet(viewsets.ViewSet):
    @swagger_auto_schema(request_body=SMSSerializer)
    def send_sms(self, request):
        serializer = SMSSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']

            # Generate a random 6-digit verification code
            verification_code = str(random.randint(100000, 999999))
            print(verification_code)

            # Send SMS via Infobip
            url = 'https://1vnm9n.api.infobip.com/sms/2/text/advanced'
            headers = {
                'Authorization': SMS_KEY,
                'Content-Type': 'application/json',
                'Accept': 'application/json'

            }

            payload = {
                'messages': [
                    {
                        'from': '5511.uz',
                        'destinations': [
                            {
                                'to': phone_number
                            }
                        ],
                        'text': f'Your verification code is {verification_code}'
                    }
                ]
            }
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                # Store the verification code and phone number in cache for 5 minutes
                cache.set(phone_number, verification_code, 300)

                return Response({"message": "SMS yuborildi "}, status=status.HTTP_200_OK)

            return Response({"message": "SMS yuborib bulmadi"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=VerifySMSSerializer)
    def verify_sms(self, request):
        serializer = VerifySMSSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            verification_code = serializer.validated_data['verification_code']
            cached_code = cache.get(phone_number)

            if verification_code == cached_code:
                return Response({"message": "raqam tasdiqlandi"})
                # user, created = User.objects.get_or_create(phone_number=phone_number)
                # if created:
                #     # Set other fields like username, email, etc. if needed
                #     user.save()
                #
                # # Generate JWT token for the user
                # refresh = RefreshToken.for_user(user)
                # return Response({
                #     'refresh': str(refresh),
                #     'access': str(refresh.access_token),
                # })

            return Response({"message": "Tasdiqlash kodi yaroqsiz"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=CreateSerializer)
    def create_user(self, request):
        serializer = SMSSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            cached_code = cache.get(phone_number)
            user, created = User.objects.get_or_create(phone_number=phone_number)
            if created:
                user.set_password(serializer.validated_data['phone_number'])
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),

                })
        return Response({"message": "bunday  raqam ruyhatdan utmagan "})
