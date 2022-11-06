# utility functions for posts app

from django.core.paginator import Paginator

from walkjn.settings import posts_per_page


def create_page_obj(request, post_list):
    """Creates page_obj using page number from get-request and post_list
    """
    paginator = Paginator(post_list, posts_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
