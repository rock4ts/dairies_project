# utility functions for post app tests
import math

from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post
from walkjn.settings import posts_per_page


def posts_number_on_page(page_number):
    """Function that calculates number of posts for a certain page.
    """
    posts_count = Post.objects.count()
    number_of_pages = math.ceil(posts_count / posts_per_page)
    remainder = posts_count % posts_per_page
    if page_number == number_of_pages and remainder != 0:
        return remainder
    return posts_per_page


def page_entry_equal_model_entry(self, Model, page_entry, model_enty):
    """Function that checks if page object instance is equal
    to model object instance by comparing every field data.
    """
    model_fields = [f.name for f in Model._meta.get_fields()]
    for field in model_fields:
        with self.subTest(field=field):
            self.assertEqual(
                getattr(page_entry, field),
                getattr(model_enty, field)
            )


def context_form_fields_are_instances(self, response, Form):
    """Function that iterates through context form of response and checks
    if each form field content represent the instance
    of a specified form corresponding field class.
    """
    form_instance = Form()
    form_fields = (
        {f: form_instance.fields[f].__class__ for f in form_instance.fields}
    )
    for field, value in form_fields.items():
        with self.subTest(field=field):
            context_field = response.context['form'].fields.get(field)
            self.assertIsInstance(context_field, value)


def create_test_image(image_name: str, format: str):
    """Function that uses bytestrings and
    emulates image as a SimpleUploadedFile class object.
    """
    small_image = (
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    )
    test_image = SimpleUploadedFile(
        name='.'.join([image_name, format]),
        content=small_image,
        content_type='image/' + format
    )
    return test_image
