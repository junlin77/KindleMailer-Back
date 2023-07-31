from django.http import HttpResponse, JsonResponse
from django.conf import settings
from libgen_api import LibgenSearch
import os
from .helpers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import BookSerializer
import json

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

        if title is None or (title == None and author == None and extension == None): # initial page load
            results = []
        elif len(title) >= 3 and author == None and extension == None: # title search
            results = s.search_title(title)
        elif len(title) > 3 and (author != None or extension != None): # filtered title search 
            title_filters = {"Author": author, "Extension": extension}
            results = s.search_title_filtered(title, title_filters, exact_match=False)
        elif len(title) < 3 and author != None and extension == None: # author search
            results = s.search_author(author)
        elif len(title) < 3 and author != None and extension != None: # filtered author search
            author_filters = {"Extension": extension}
            results = s.search_author_filtered(author, author_filters, exact_match=False)

        # TODO: handle email address elsewhere
        # stored_kindle_email = request.session.get("kindle_email")

        # context = {
        #     "books": results,
        #     "stored_kindle_email": stored_kindle_email
        # }

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
        kindle_email = data.get("kindle_email")
        print(f"Kindle email: {kindle_email}")

        # Server-side email validation
        if len(kindle_email) == 0:
            print("No email address provided.")
            return HttpResponse("No email address provided.")
        elif not validate_email(kindle_email):
            print("Invalid email address.")
            return HttpResponse("Invalid email address.")

        # resolve_download_links()
        try:
            s = LibgenSearch() 
            url = s.resolve_download_links(item_to_download)
        except Exception as e:
            # Handle the exception or log the error message
            print(f"Failed to resolve download links: {str(e)}")
            return HttpResponse("Failed to resolve download links.")

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
            return HttpResponse("Failed to save the file.")

        # Send the file as an email attachment
        if send_email_with_attachment(kindle_email, file_path):
            success = True
        else:
            success = False

        delete_file(file_path)
        return JsonResponse({'success': success})



