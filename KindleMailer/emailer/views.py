from django.http import JsonResponse, HttpResponseServerError
from django.conf import settings
from libgen_api import LibgenSearch
import os
from .helpers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .serializers import BookSerializer, DetailsSerializer
import json
from rest_framework import status
import requests
from .models import UserProfile

@api_view(["GET"])
def search_api(request):
    """
    Perform a search using the LibgenSearch class and return the results.
    """
    if request.method == "GET":
        search = request.GET.get("search")
        page = request.GET.get("page")
        print(page)
        if len(search) == 0:
            return HttpResponseServerError("Search query cannot be empty.")
        
        # Construct the URL for the external API
        api_url = "https://api.ylibrary.org/api/search/?"
        params = {
            "keyword": search,
            "page": page,
            "sensitive": "False",
        }

        response = requests.post(api_url, json=params)

        try:
            response_data = response.json()  # Try to parse the JSON response
        except requests.exceptions.JSONDecodeError:
            # If JSON parsing fails, handle the error appropriately
            print("Error parsing API response as JSON.")
            return Response("Error parsing API response as JSON.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Extract the "data" key from the response dictionary
        data_from_response = response_data.get("data", [])
        print(f"Data from response: {data_from_response}")
        results_serializer = BookSerializer(data=data_from_response, many=True)
        
        if results_serializer.is_valid():
            serialized_data = results_serializer.data
            return Response(serialized_data, status=status.HTTP_200_OK)
        else:
            print(results_serializer.errors)
            return Response(results_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def details_api(request):
    """
    Get details of selected books.
    """
    if request.method == "POST":
        id = request.data.get("id")
        source = request.data.get("source")

        if id is None or source is None:
            return HttpResponseServerError("ID and source must be provided in the request body.", status=status.HTTP_400_BAD_REQUEST)

        api_url = "https://api.ylibrary.org/api/detail/?"
        params = {
            "id": id,
            "source": source,  
        }
        response = requests.post(api_url, json=params)
        response_data = response.json()

        serializer = DetailsSerializer(data=response_data)
        if serializer.is_valid():
            serialized_data = serializer.data
            return Response(serialized_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def send_to_kindle_api(request):
    """
    Send the selected book to the Kindle email address.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        ipfs_cid = data.get("ipfs_cid")
        kindle_email = data.get("kindle_email").strip()
        title = data.get("title")
        extension = data.get("extension")

        print(f"IPFS CID: {ipfs_cid}")
        print(f"Kindle email: {kindle_email}")
        print(f"Title: {title}")
        print(f"Extension: {extension}")

        # Server-side email validation
        if len(kindle_email) == 0:
            print("No email address provided.")
            return JsonResponse({"error": "No email address provided."}, status=400)
        elif not validate_email(kindle_email):
            print("Invalid email address.")
            return JsonResponse({"error": "Invalid email address."}, status=400)

        # Fetch and save IPFS file
        try:
            ipfs_gateway_url = f"https://ipfs.io/ipfs/{ipfs_cid}"
            response = requests.get(ipfs_gateway_url)
            if response.status_code == 200:
                # Set the filename and destination directory
                filename = os.path.basename(title + "." + extension)  # Adjust extension if needed
                destination_directory = settings.MEDIA_ROOT
                file_path = os.path.join(destination_directory, filename)

                # Save the IPFS file in MEDIA_ROOT
                try:
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    print("IPFS file saved successfully.")
                except Exception as e:
                    print(f"Failed to save IPFS file: {str(e)}")
                    return HttpResponseServerError("Failed to save IPFS file.")
            else:
                print("Failed to fetch IPFS file from gateway.")
                return HttpResponseServerError("Failed to fetch IPFS file from gateway.")
        except Exception as e:
            print(f"Failed to process IPFS file: {str(e)}")
            return HttpResponseServerError("Failed to process IPFS file.")

        # Send the file as an email attachment
        if send_email_with_attachment(kindle_email, file_path):
            success = True
        else:
            success = False

        delete_file(file_path)
        return JsonResponse({'success': success})

@api_view(["POST"])
def login_api(request):
    """
    Login using Google OAuth2.
    """
    access_token = request.data.get('access_token')

    # Retrieve user profile picture URL using Google OAuth2 userinfo endpoint
    userinfo_api_url = f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
    userinfo_response = requests.get(userinfo_api_url)
    
    if userinfo_response.status_code == 200:
        userinfo_data = userinfo_response.json()
        print(f"Userinfo data: {userinfo_data}")

        profile_picture = userinfo_data.get('picture')
        google_user_id = userinfo_data.get('id')

        user_exists = UserProfile.objects.filter(google_user_id=google_user_id).exists()

        if not user_exists:
            # Create a new user profile
            new_user = UserProfile.objects.create(google_user_id=google_user_id)
            message = 'New user profile created'
            kindle_email = ''
            status_code = status.HTTP_201_CREATED
        else:
            message = 'User already exists'
            kindle_email = UserProfile.objects.get(google_user_id=google_user_id).kindle_email
            status_code = status.HTTP_200_OK
        return Response({'message': message, 'profile_picture': profile_picture, 'user_id': google_user_id, 'kindle_email': kindle_email}, status=status_code)
    else:
        return Response({'error': 'Failed to fetch user info from Google'}, status=userinfo_response.status_code)
    
class KindleEmailAPI(APIView):
    def get(self, request):
        """
        Get the Kindle email for the authenticated user.
        """
        user_id = request.GET.get("user_id")

        try:
            user_profile = UserProfile.objects.get(google_user_id=user_id)
            kindle_email = user_profile.kindle_email
            return Response({"kindle_email": kindle_email}, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
                            
    def post(self, request):
        """
        Set the Kindle email for the authenticated user.
        """
        user_id = request.data.get("user_id")

        if request.method == "POST":
            kindle_email = request.data.get("kindle_email").strip()

            if not kindle_email:
                return Response({"error": "Kindle email is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Update the user's Kindle email in the UserProfile model
            try:
                user_profile = UserProfile.objects.get(google_user_id=user_id)
                user_profile.kindle_email = kindle_email
                user_profile.save()
                return Response({"message": "Kindle email set successfully"}, status=status.HTTP_200_OK)
            except UserProfile.DoesNotExist:
                return Response({"error": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({"error": "Invalid request method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)