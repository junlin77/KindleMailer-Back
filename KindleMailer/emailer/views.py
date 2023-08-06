from django.http import JsonResponse, HttpResponseServerError
from django.conf import settings
from libgen_api import LibgenSearch
import os
from .helpers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .serializers import BookSerializer
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
        s = LibgenSearch()
        title = request.GET.get("title")
        author = request.GET.get("author")
        extension = request.GET.get("extension")
        publisher = request.GET.get("publisher")
        year = request.GET.get("year")
        language = request.GET.get("language")

        try: 
            if len(title) >= 3 and author == None and extension == None and publisher == None and year == None and language == None: # title search
                results = s.search_title(title)
            elif len(title) > 3 and (author != None or extension != None or publisher != None or year != None or language != None): # filtered title search 
                title_filters = {"Author": author, "Extension": extension, "Publisher": publisher, "Year": year, "Language": language}
                results = s.search_title_filtered(title, title_filters, exact_match=False)
            elif len(title) < 3 and author != None and extension == None and publisher == None and year == None and language == None: # author search
                results = s.search_author(author)
            elif len(title) < 3 and author != None and (extension != None or publisher != None or year != None or language != None): # filtered author search
                author_filters = {"Extension": extension, "Publisher": publisher, "Year": year, "Language": language}
                results = s.search_author_filtered(author, author_filters, exact_match=False)
        except Exception as e:
            if str(e) != "Query is too short":
                print("Caught a different Exception:", e)
            results = []

        serializer = BookSerializer(results, many=True)
        return Response(serializer.data)


@api_view(["POST"])
def send_to_kindle_api(request):
    """
    Send the selected book to the Kindle email address.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        item_to_download = data.get("book_to_download")
        kindle_email = data.get("kindle_email").strip()
        print(f"Kindle email: {kindle_email}")

        # Server-side email validation
        if len(kindle_email) == 0:
            print("No email address provided.")
            return JsonResponse({"error": "No email address provided."}, status=400)
        elif not validate_email(kindle_email):
            print("Invalid email address.")
            return JsonResponse({"error": "Invalid email address."}, status=400)

        # resolve_download_links()
        try:
            s = LibgenSearch() 
            url = s.resolve_download_links(item_to_download)
        except Exception as e:
            print(f"Failed to resolve download links: {str(e)}")
            return HttpResponseServerError("Failed to resolve download links.")

        # Iterate through the download links
        response = iterate_download_links(url)

        # Set the filename and destination directory
        filename = os.path.basename(item_to_download['Title'] + '.' + item_to_download['Extension'])
        destination_directory = settings.MEDIA_ROOT
        file_path = os.path.join(destination_directory, filename)
        print(f"File path: {file_path}")

        # Save the file in MEDIA_ROOT
        if save_file_in_media_root(response, file_path):
            print("File saved successfully in MEDIA_ROOT.")
        else:
            return HttpResponseServerError("Failed to save the file.")

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